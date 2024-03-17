import asyncio
import SRF05
from Robot.commands import *
from stm32_api.dispatcher import *
from time import *
from Connection.RPI_comms import RPI_connection
from stm32_api.dispatcher import BlockingDispatcher, _IO_Attr_Type
import math
from photographer import take_photo
from multiprocessing import Process
import json

robot = RobotController(PORT, BAUD)
robot.set_threshold_stop_distance_left(1)
robot.set_threshold_stop_distance_right(1)
dispatcher = BlockingDispatcher(robot, 5, 2, u_if=_IO_Attr_Type.SIMULATED)
sensor = SRF05.SRF05(trigger_pin=17, echo_pin=27)

DEBUG = True
LOG_I = lambda z: print("[APP-I] " + str(z)) if DEBUG else None
LOG_W = lambda z: print("[APP-W] " + str(z)) if DEBUG else None
LOG_E = lambda z: print("[APP-E] " + str(z)) if DEBUG else None

# typedefs
class DIR(Enum):
    LEFT = 0,
    RIGHT = 1

class COND(Enum):
    CUR = 0,
    OPP = 1

# defines
CONST_TH_DIST_OBST = 20
CONST_STEP_SIZE_OBST = 10
CONST_MAX_STEPS_OBST = 10
CONST_SENSOR_MAX_ERROR = 5
CONST_OPP_FWD_OFFSET = 15
CONST_TURN_RAD_CM = 20
CONST_CAMERA_TURN_ANGLE = 7

# globals
x_p = 0
y_p1 = 0
y_p2 = 0
phi = 0



def obst_cb(*args):
    print("OBSTACLE")
    pass

# wait for "interrupt". technically, not an interrupt. but it makes sense to think of it as such from application level
async def _WFI():
     
     await asyncio.sleep(0.45)
     while(robot.poll_is_moving()):
        await asyncio.sleep(0.05)

# get some x for which x is not None with patience
async def get_distance():
    x = sensor.measure()
    for i in range(10):
        x = sensor.measure()
        LOG_I("distance: " + str(x))
        await asyncio.sleep(0.05)
        if x is not None:
            break
    return x

"""
This function finds mag(epsilon) and sgn(epsilon) for which mag(expected_phi -cur_phi) is minimized,
given expected_phi = prev_phi + sgn_offset
subject to the wrapping of values at 180 <-> -180.
Otherwise, solves the optimization problem to minimize epsilon for any integer k*90 angular offset
from phi.

"""
async def turn_error_minimization(phi: float, offset_known: bool, sgn_offset: float = 0) :
    phi_cur = await dispatcher.dispatchB(RobotController.get_yaw, [], obst_cb)
    if offset_known:

        if (phi + sgn_offset) >= 180:
            phi_opt = -180 + ((phi + sgn_offset) % 180)
        elif (phi + sgn_offset) < -180:
            phi_opt = (phi + sgn_offset) % 180
        else:
            phi_opt = (phi + sgn_offset)


        epsl = phi_opt - phi_cur
        if abs(epsl) <= 180:
            return abs(epsl), DIR.LEFT if epsl > 0 else DIR.RIGHT
        else:
            return 360-epsl, DIR.LEFT if epsl <= 0 else DIR.RIGHT

    else:
        epsl_vars = []
        # basically repeat the above for all k in -2..2
        _CONST_ROT_MAG = 90
        for k in (-2, 3):
            if (phi + _CONST_ROT_MAG * k) >= 180:
                phi_opt = -180 + ((phi + _CONST_ROT_MAG * k) % 180)
            elif (phi + _CONST_ROT_MAG * k) < -180:
                phi_opt = (phi + _CONST_ROT_MAG * k) % 180
            else:
                phi_opt = (phi + _CONST_ROT_MAG * k)


            epsl = phi_opt - phi_cur
            if abs(epsl) <= 180:
                epsl_vars.append([abs(epsl), DIR.LEFT if epsl > 0 else DIR.RIGHT])
            else:
                epsl_vars.append([360-epsl, DIR.LEFT if epsl <= 0 else DIR.RIGHT])
        n = 0
        for k, _ in enumerate(epsl_vars):
            if epsl_vars[k][0] < epsl_vars[n][0]:
                n = k
        return epsl_vars[n]

            
    



"""
navigate to the side of obstacle 1 corresponding to dir and start scanning
"""          
async def nav1_pos(dir: DIR):
    await dispatcher.dispatchB(RobotController.turn_left if dir is DIR.LEFT else RobotController.turn_right, [55, 1, 1], obst_cb)
    await _WFI()

    await dispatcher.dispatchB(RobotController.turn_right if dir is DIR.LEFT else RobotController.turn_left, [110, 1, 1], obst_cb)
    await _WFI()
    await dispatcher.dispatchB(RobotController.turn_right if dir is DIR.RIGHT else RobotController.turn_left, [55, 1, 1], obst_cb)
    await _WFI()

    #cur_phi = await dispatcher.dispatchB(RobotController.get_yaw, [], obst_cb)

    global phi
    mag, direction = await turn_error_minimization(phi, True, 0)
    print(mag)
    print(direction)

    if mag < 15:
        await dispatcher.dispatchB(RobotController.turn_left if direction is DIR.LEFT else RobotController.turn_right, [math.floor(mag), 1], obst_cb)
        await _WFI()



"""
find the next point at the side of obstacle 2, move there, then move behind the obstacle to the opposite side facing the carpark
"""
async def scan_len2(dir: DIR) -> float:


    sensor = None
    
    await dispatcher.dispatchB(RobotController.turn_left if dir is DIR.LEFT else RobotController.turn_right, [90, 1], obst_cb)
    await _WFI()
    sensor = DIR.RIGHT if dir is DIR.LEFT else DIR.LEFT
    await dispatcher.dispatchB(RobotController.set_threshold_stop_distance_left if sensor is DIR.LEFT else RobotController.set_threshold_stop_distance_right, [25], obst_cb)
    
    
    await dispatcher.dispatchB(RobotController.crawl_forward, [CONST_STEP_SIZE_OBST*6], obst_cb)
    
    await asyncio.sleep(0.25)
    while 1:
        #x = await dispatcher.dispatchB(RobotController.get_ir_R if sensor is DIR.LEFT else RobotController.get_ir_L, [], obst_cb)
        if not robot.poll_obstruction():
            print("FALSE")
            break
        await asyncio.sleep(0.01)

    
    await dispatcher.dispatchB(RobotController.halt, [], obst_cb)
    await _WFI()

    x = await dispatcher.dispatchB(RobotController.get_last_successful_arg, [], obst_cb)
    if x is False:
        x = 0

    global x_p
    x_p += x + CONST_TURN_RAD_CM + CONST_STEP_SIZE_OBST

    print("Last distance: " + str(x))
    

    print(sensor)

    await dispatcher.dispatchB(RobotController.move_forward, [5, 1], obst_cb)
    await _WFI()
    await dispatcher.dispatchB(RobotController.turn_left if sensor is DIR.LEFT else RobotController.turn_right, [90, 1, 1], obst_cb)

    await _WFI()

    global phi


    await dispatcher.dispatchB(RobotController.crawl_forward, [math.floor(CONST_STEP_SIZE_OBST//2)], obst_cb)
    await _WFI()


  

    await dispatcher.dispatchB(RobotController.turn_left if sensor is DIR.LEFT else RobotController.turn_right, [90, 1, 1], obst_cb)

    await _WFI()


    mag, direction = await turn_error_minimization(phi, True, 90 if dir is DIR.RIGHT else -90)
    print(mag)
    print(direction)

    if mag < 15:
        await dispatcher.dispatchB(RobotController.turn_left if direction is DIR.LEFT else RobotController.turn_right, [math.floor(mag), 1], obst_cb)
        await _WFI()
    #await dispatcher.dispatchB(RobotController.move_forward, [math.floor(2*(x+ CONST_TURN_RAD_CM) + CONST_STEP_SIZE_OBST), 1], obst_cb)
    #await _WFI()
    await dispatcher.dispatchB(RobotController.crawl_forward, [math.floor(2*(x+ CONST_TURN_RAD_CM) + 4*CONST_STEP_SIZE_OBST)], obst_cb)
    
    await asyncio.sleep(0.25)
    while 1:
        #x = await dispatcher.dispatchB(RobotController.get_ir_R if sensor is DIR.LEFT else RobotController.get_ir_L, [], obst_cb)
        if not robot.poll_obstruction():
            print("FALSE")
            break
        await asyncio.sleep(0.01)

    
    await dispatcher.dispatchB(RobotController.halt, [], obst_cb)
    await _WFI()
    await dispatcher.dispatchB(RobotController.move_forward, [5, 1], obst_cb)
    await _WFI()

    await dispatcher.dispatchB(RobotController.turn_left if sensor is DIR.LEFT else RobotController.turn_right, [90, 1, 1], obst_cb)
    await _WFI()
    await _WFI()


    mag, direction = await turn_error_minimization(phi, True, 180)
    print(mag)
    print(direction)
    if mag < 15:
        await dispatcher.dispatchB(RobotController.turn_left if direction is DIR.LEFT else RobotController.turn_right, [math.floor(mag), 1], obst_cb)
        await _WFI()




    await dispatcher.dispatchB(RobotController.move_forward, [math.floor(y_p2 - 10)], obst_cb)
    await _WFI()
    await dispatcher.dispatchB(RobotController.turn_right if dir is DIR.LEFT else RobotController.turn_left, [90, 1, 1], obst_cb)
    await _WFI()
    
    if x_p - 2*CONST_TURN_RAD_CM> 0:
        await dispatcher.dispatchB(RobotController.move_forward, [math.floor(x_p-2*CONST_TURN_RAD_CM), 1], obst_cb)
  
    await dispatcher.dispatchB(RobotController.turn_right if dir is DIR.RIGHT else RobotController.turn_left, [90, 1, 1], obst_cb)
    await _WFI()

    await dispatcher.dispatchB(RobotController.set_threshold_disable_obstacle_detection_left if sensor is DIR.LEFT else RobotController.set_threshold_disable_obstacle_detection_right, [], obst_cb)
    



async def main():
    await dispatcher.dispatchB(RobotController.set_threshold_disable_obstacle_detection_left, [], obst_cb)
    await dispatcher.dispatchB(RobotController.set_threshold_disable_obstacle_detection_right, [], obst_cb)

    global phi
    
    phi = await dispatcher.dispatchB(RobotController.get_yaw, [], obst_cb)
    print("YAW")
    print(phi)




    x = await get_distance()
    await dispatcher.dispatchB(RobotController.crawl_forward, [150], obst_cb)
    
    global y_p1, y_p2
    
    y_p1 += min(x, 150)
    y_p2 += min(x, 150)
    while x is None or x > CONST_TH_DIST_OBST + 10:                                      #range distance min(60,150)
        x = await get_distance()
        LOG_I(x)

        await asyncio.sleep(0.05)
    await dispatcher.dispatchB(RobotController.halt, [], obst_cb)
    x = await get_distance()
    LOG_I(x)
    await _WFI()
    

 

    if x < CONST_TH_DIST_OBST:
        await dispatcher.dispatchB(RobotController.move_backward, [CONST_TH_DIST_OBST - x], obst_cb)
    else:
        await dispatcher.dispatchB(RobotController.move_forward, [x - CONST_TH_DIST_OBST], obst_cb)
    await _WFI()
    x = await get_distance()
    LOG_I(x)
    
    img = str(take_photo())
    
    img = (json.loads(img)["message"]).split(",")[2]
    print(img)
    
    

    # placeholder for img detection

    
    #snap_pic_process = Process(target=take_photo)
    #snap_pic_process.start()
    
    
    
    # tony wants to send a HTTP signal here

    # ^
    ret = DIR.RIGHT if int(img)-1 == 38 else DIR.LEFT
    
  
    await nav1_pos(ret)
    d0 = await get_distance()
    if d0 is None:
        await dispatcher.dispatchB(RobotController.crawl_backward, [10], obst_cb)
        await _WFI()
        d0 = await get_distance()

    y_p2 += min((d0 + 30), 150)
    if not d0 < CONST_TH_DIST_OBST :
        await dispatcher.dispatchB(RobotController.crawl_forward, [150], obst_cb)
        d0 = await get_distance()
        while d0 is None or d0 > CONST_TH_DIST_OBST + 10:                                      #range distance min(60,150)
            d0 = await get_distance()
            LOG_I(d0)

            await asyncio.sleep(0.05)
        await dispatcher.dispatchB(RobotController.halt, [], obst_cb)
        await _WFI()
        d0 = await get_distance()


    if d0 < CONST_TH_DIST_OBST  :
        await dispatcher.dispatchB(RobotController.move_backward, [CONST_TH_DIST_OBST - d0], obst_cb)
    else:
        await dispatcher.dispatchB(RobotController.move_forward, [d0 - CONST_TH_DIST_OBST ], obst_cb)
    await _WFI()
    d0 = await get_distance()
    print(d0)

    d0 = d0 if d0 is not None else await dispatcher.dispatchB(RobotController.get_last_successful_arg, [], obst_cb)
    LOG_I(x)
    await _WFI()

    
    img = str(take_photo())
    
    img = (json.loads(img)["message"]).split(",")[2]

    ret = DIR.RIGHT if int(img)-1 == 38 else DIR.LEFT
    
 
    len2 = await scan_len2(ret)
    

    await _WFI()

    mag, direction = await turn_error_minimization(phi, True, 180)
    print(mag)
    print(direction)

    if mag < 15:
        await dispatcher.dispatchB(RobotController.turn_left if direction is DIR.LEFT else RobotController.turn_right, [math.floor(mag), 1], obst_cb)
        await _WFI()







    






if __name__ == '__main__':
    asyncio.run(main())
    
