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
dispatcher = BlockingDispatcher(robot, 5, 2, u_if=_IO_Attr_Type.PHYSICAL)
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



def obst_cb(*args):
    print("OBSTACLE")
    pass

# wait for "interrupt". technically, not an interrupt. but it makes sense to think of it as such from application level
async def _WFI():
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
navigate to the side of obstacle 1 corresponding to dir and start scanning
"""          
async def nav1_pos(dir: DIR):
    await dispatcher.dispatchB(RobotController.turn_left if dir is DIR.LEFT else RobotController.turn_right, [45, 1, True], obst_cb)
    await _WFI()
    await dispatcher.dispatchB(RobotController.move_forward, [15,  True], obst_cb)
    await _WFI()
    await dispatcher.dispatchB(RobotController.turn_right if dir is DIR.LEFT else RobotController.turn_left, [45, 1,  True], obst_cb)
    await _WFI()

"""
find the next point at the side of obstacle 2, move there, then move behind the obstacle to the opposite side facing the carpark
"""
async def scan_len2(dir: DIR, cond: COND) -> float:
    await _WFI()
    if cond is COND.OPP:
        await dispatcher.dispatchB(RobotController.move_forward, [CONST_OPP_FWD_OFFSET], obst_cb)
        await _WFI()
        

    d0 = 0
    for i in range(11):
        d0 += await get_distance()
    d0 /= 10

    d0 *= math.cos(math.radians(CONST_CAMERA_TURN_ANGLE))

    await dispatcher.dispatchB(RobotController.move_forward, [math.floor(d0 // 2)], obst_cb)
    await _WFI()
    d0 = 0
    for i in range(11):
        d0 += await get_distance()
    d0 /= 10

    d0 *= math.cos(math.radians(CONST_CAMERA_TURN_ANGLE))
    LOG_I("Setpoint: " + str(d0))

    if cond is not COND.OPP:
        await dispatcher.dispatchB(RobotController.turn_right if dir is DIR.LEFT else RobotController.turn_left, [CONST_CAMERA_TURN_ANGLE, 0], obst_cb)
        await _WFI()

    if cond is COND.OPP:
        phi_offset = max(15, math.atan2(3*CONST_STEP_SIZE_OBST, d0))
        LOG_I("phi offset" + str(phi_offset))
        await dispatcher.dispatchB(RobotController.turn_left if dir is DIR.LEFT else RobotController.turn_right, [phi_offset, 1], obst_cb)
        await _WFI()
        
    phi = math.floor(math.degrees(math.atan2(math.radians(CONST_STEP_SIZE_OBST), math.radians(d0))) // 2) 
    dn = d0
    global y_p2
    y_p2 += d0

    for i in range(0, CONST_MAX_STEPS_OBST):
        await dispatcher.dispatchB(RobotController.turn_left if dir is DIR.LEFT else RobotController.turn_right, [phi if i>0 else 0, 1], obst_cb)
        await _WFI()
        LOG_I(i*phi)
        
        LOG_I(d0)
        LOG_I((d0 // math.cos(math.radians(phi*i))) + CONST_SENSOR_MAX_ERROR)
        dn = await get_distance()

        LOG_I(dn)
        opp_offset = 15 if cond is COND.OPP else 0
        if dn is None or dn > (d0 // math.cos(math.radians(phi*i+ opp_offset))) + CONST_SENSOR_MAX_ERROR:
            await dispatcher.dispatchB(RobotController.turn_left if dir is DIR.LEFT else RobotController.turn_right, [phi//2, 1], obst_cb)
            LOG_I("moving out")

            await dispatcher.dispatchB(RobotController.move_forward, [abs(math.floor((d0 // math.cos(math.radians(phi*i))))) + 2* CONST_STEP_SIZE_OBST] , obst_cb)
            await _WFI()
            offset_opp = math.floor(phi_offset) + CONST_CAMERA_TURN_ANGLE if cond is COND.OPP else 0
            await dispatcher.dispatchB(RobotController.turn_right if dir is DIR.LEFT else RobotController.turn_left, [math.ceil(90 + phi*i + offset_opp), 1] , obst_cb)
            await _WFI()
            opp = i*phi
            opp += 15 if cond is COND.OPP else 0
            dist_h_blk = abs(math.floor(math.tan(math.radians(opp)) * d0))
            dist_h_blk -= 20 if cond is COND.OPP else 0
            #dist_h_blk += 1.5*CONST_MAX_STEPS_OBST if cond is COND.OPP else 0
            print(dist_h_blk)
            return math.floor(dist_h_blk)
        
    LOG_I("moving out with error")
    await dispatcher.dispatchB(RobotController.move_forward, [math.floor(d0 + 2* CONST_STEP_SIZE_OBST)] , obst_cb)
    await _WFI()
    offset_opp = math.floor(phi_offset) if cond is COND.OPP else 0
    await dispatcher.dispatchB(RobotController.turn_right if dir is DIR.LEFT else RobotController.turn_left, [math.ceil(90 + phi*CONST_MAX_STEPS_OBST-1 + offset_opp), 1] , obst_cb)
    await _WFI()
    return abs(math.floor(math.tan(math.radians(CONST_MAX_STEPS_OBST-1*phi)) * d0))

    








async def main():
    robot.set_threshold_disable_obstacle_detection()
    
    await dispatcher.dispatchB(RobotController.crawl_forward, [150], obst_cb)
    x = await get_distance()
    global y_p1, y_p2
    
    y_p1 += x
    y_p2 += x
    while x is None or x > CONST_TH_DIST_OBST:                                      #range distance min(60,150)
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
    

    # placeholder for img detection

    
    #snap_pic_process = Process(target=take_photo)
    #snap_pic_process.start()
    img = str(take_photo())
    img = (json.loads(img)["message"]).split(",")[2]
    print(img)
  
    ret = DIR.RIGHT if int(img) == 38 else DIR.LEFT
    await nav1_pos(ret)
    

    # turn to face the arrow
    await dispatcher.dispatchB(RobotController.turn_right if ret is DIR.LEFT else RobotController.turn_left, [CONST_CAMERA_TURN_ANGLE, 1], obst_cb)
    await _WFI()


    img = str(take_photo())
    img = (json.loads(img)["message"]).split(",")[2]
    ret = DIR.RIGHT if int(img) == 38 else DIR.LEFT
    ret_pre = ret
    # placeholder for img detectionn
    #snap_pic_process = Process(target=take_photo)
    #snap_pic_process.start()
    cond = COND.OPP if ret != ret_pre else COND.CUR
    #cond = COND.OPP # REMOVE

    
    
    len2 = await scan_len2(ret, cond)
    global x_p
    x_p += (len2 + CONST_STEP_SIZE_OBST)
    len2 *= 2

    #len2 -= CONST_TURN_RAD_CM*2
    await dispatcher.dispatchB(RobotController.move_forward, [len2 + 2* CONST_STEP_SIZE_OBST], obst_cb)
    await _WFI()
    await dispatcher.dispatchB(RobotController.turn_right if ret is DIR.LEFT else RobotController.turn_left, [90, 1], obst_cb)
    await _WFI()
    #await dispatcher.dispatchB(RobotController.move_forward, [CONST_STEP_SIZE_OBST], obst_cb)
    #await _WFI()


    '''
    home_angle = math.floor(math.degrees(math.atan2(math.radians(x_p-10), math.radians(y_p2))))
    home_dist = (y_p2) // math.cos(math.radians(home_angle)) + CONST_STEP_SIZE_OBST
    await dispatcher.dispatchB(RobotController.turn_right if ret is DIR.LEFT else RobotController.turn_left, [home_angle, 1], obst_cb)
    await _WFI()
    await dispatcher.dispatchB(RobotController.move_forward, [math.ceil(home_dist+CONST_STEP_SIZE_OBST)], obst_cb)
    await _WFI()
    '''
    await dispatcher.dispatchB(RobotController.move_forward, [math.floor(y_p2 - 10)], obst_cb)
    await _WFI()
    await dispatcher.dispatchB(RobotController.turn_right if ret is DIR.LEFT else RobotController.turn_left, [90, 1], obst_cb)
    await _WFI()
    await dispatcher.dispatchB(RobotController.move_forward, [math.floor(x_p - CONST_TURN_RAD_CM)], obst_cb)
    await dispatcher.dispatchB(RobotController.turn_right if ret is DIR.RIGHT else RobotController.turn_left, [90, 1], obst_cb)
    await _WFI()





    






if __name__ == '__main__':
    asyncio.run(main())
    
