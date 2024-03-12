import asyncio
import SRF05

from Robot.commands import *
from stm32_api.dispatcher import *
import photographer
from time import *


from Connection.RPI_comms import RPI_connection
from stm32_api.dispatcher import BlockingDispatcher, _IO_Attr_Type
Robot = RobotController(PORT, BAUD)
x_travelled = 0 #Right is positive, Left is Negative
y_travelled = 0 #Forward is positive, Backwards is Negative
FWD_TURN_45_Delta_Y = 15    #approx, Dependent of Bearing
FWD_TURN_90_Delta_Y = 20    #approx, Dependent of Bearing
FWD_TURN_45_Delta_X = 15    #approx, Dependent of Bearing
FWD_TURN_45_Delta_X = 15    #approx, Dependent of Bearing

def cb_fn(*args):
        print("Obstacle detected!")
        print(args)


id_to_class = {
    0: 11,
    1: 12,
    2: 13,
    3: 14,
    4: 15,
    5: 16,
    6: 17,
    7: 18,
    8: 19,
    9: 20,
    10: 21,
    11: 22,
    12: 23,
    13: 24,
    14: 25,
    15: 26,
    16: 27,
    17: 28,
    18: 29,
    19: 30,
    20: 31,
    21: 32,
    22: 33,
    23: 34,
    24: 35,
    25: 36,
    26: 37,
    27: 38, #right
    28: 39, #left
    29: 40,
}

def cb_fn(*args):
    pass



async def FwdTillObst(dispatcher,sensor):
    prev_y = y_travelled
    await dispatcher.dispatchB(Robot.move_forward,[40],cb_fn)
    y_travelled += 40

    #sensor
    x = sensor.measure()
    while x is None or x > 60:                                      #range distance min(60,150)
        x = sensor.measure()
        await asyncio.sleep(0.05)
        if Robot.poll_is_moving()==False:
            await dispatcher.dispatchB(Robot.move_forward,[40],cb_fn)
            y_travelled += 40
    # x = Robot.halt()   ##What is this for?
    # await asyncio.sleep(0.05)
    # x = Robot.halt()
    # await asyncio.sleep(0.05)
        return prev_y

async def Obst1Right(dispatcher):
    """
    Travel to Right of obstacle 1 if Arrow is to Right
    """
    cmd_list = [(Robot.turn_right,[45,True] ), #turn forward 45 to right arnd 1st obstacle
                (Robot.move_forward,[30]    ),    #Gain leeway for turn to behind Obst1 
                (Robot.turn_left,[90,True]  ),  #turn forward left to move behind Obst1
                (Robot.move_forward,[30]    ), #Return for straightening 
                (Robot.turn_right,[45,True] )] #Straighten to face obst2

    for cmd in cmd_list:
        while(Robot.poll_is_moving):
            await asyncio.sleep(0.05)
        else:
            #robot.turn_right(ANGLE, True)
            await dispatcher.dispatchB(cmd[0],cmd[1],None) 
            

    y_travelled += 15+15+20
    
    # print("Turn Right forward around obs1")
            
    # await dispatcher.dispatchB(robot.move_forward,[30],None)    #Gain leeway for turn to behind Obst1 
    # print("Gain leeway for turn to behind Obst1")

    # #robot.turn_left(ANGLE, True)                                
    # await dispatcher.dispatchB(robot.turn_left,[90,True],None)  #turn forward left to move behind Obst1
    # print("Turn forward left to move behind Obst1")        

    # await dispatcher.dispatchB(robot.move_forward,[30],None)    #Return for straightening 
    # print("Return for straightening")

    # await dispatcher.dispatchB(robot.turn_right,[45,True],None) #Straighten to face obst2
    # print("Straighten to face obst2")

async def Obst1Left(dispatcher):
    """
    Travel to left of obstacle 1 if Arrow is to Left
    """
    cmd_list = [(Robot.turn_left,[45,True]  ), #turn forward 45 to left arnd 1st obstacle
                (Robot.move_forward,[30]    ),    #Gain leeway for turn to behind Obst1 
                (Robot.turn_right,[90,True] ),  #turn forward right to move behind Obst1
                (Robot.move_forward,[30]    ), #Return for straightening 
                (Robot.turn_left,[45,True]  )] #Straighten to face obst2

    for cmd in cmd_list:
        while(Robot.poll_is_moving):
            await asyncio.sleep(0.05)
        else:
            #robot.turn_right(ANGLE, True)
            await dispatcher.dispatchB(cmd[0],cmd[1],None) 
    
    y_travelled += 15+15+20

async def Obst2Right(dispatcher):
    """
    Travel to Right of obstacle 2 if Arrow is to Right
    """

    cmd_list = [(Robot.turn_right,[90,True] ), #turn forward 90 to Right , parallel to Obst2  TODO Can consider 45 degree turns here?
                (Robot.move_forward,[30]    ),    #Move to edge of Obst2 (60 considering Largest size of 120cm) 
                (Robot.turn_left,[180,True] ),  #turn forward right to move behind Obst1   TODO Can consider 45 degree turns here?
                (Robot.move_forward,[120]   ), #Move to opposite end of Obst 2
                (Robot.turn_left,[90,True]  )] #Move perpendicular to Obst 2 Facing Back/Carpark

    for cmd in cmd_list:
        while(Robot.poll_is_moving):
            await asyncio.sleep(0.05)
        else:
            #robot.turn_right(ANGLE, True)
            await dispatcher.dispatchB(cmd[0],cmd[1],None) 

    x_travelled -= 90
    y_travelled += 40

async def Obst2Left(dispatcher):
    """
    Travel to Left of obstacle 2 if Arrow is to Left
    """

    cmd_list = [(Robot.turn_left,[90,True]  ), #turn forward 90 to left , parallel to Obst2  TODO Can consider 45 degree turns here?
                (Robot.move_forward,[30]    ),    #Move to edge of Obst2 (60 considering Largest size of 120cm) 
                (Robot.turn_right,[180,True]),  #turn forward right to move behind Obst1   TODO Can consider 45 degree turns here?
                (Robot.move_forward,[120]   ), #Move to opposite end of Obst 2
                (Robot.turn_right,[90,True] )] #Move perpendicular to Obst 2 Facing Back/Carpark

    for cmd in cmd_list:
        while(Robot.poll_is_moving):
            await asyncio.sleep(0.05)
        else:
            #robot.turn_right(ANGLE, True)
            await dispatcher.dispatchB(cmd[0],cmd[1],None) 

    x_travelled += 90
    y_travelled += 40

    
    # #robot.turn_left(ANGLE, True)
    # await dispatcher.dispatchB(robot.turn_left,[ANGLE,True],None)
    # print("Turn Left forward around obs2")

    # sleep(2)
    # #robot.move_forward(20)      
    # await dispatcher.dispatchB(robot.move_forward,[20],None) 
    # print("Straight forward around obs2")

    # sleep(2)

    # await dispatcher.dispatchB(robot.turn_right,[135,True],None)

    # #robot.turn_right(ANGLE, True)
    # await dispatcher.dispatchB(robot.move_forward,[120],None) 
    # print("Turn Right forward around obs2")

    # #robot.move_forward(65) #length 30-60
    # await dispatcher.dispatchB(robot.move_forward,[65],None) 
    # print("Straight forward at top of obs2")

    # #robot.turn_right(ANGLE, True)
    # await dispatcher.dispatchB(robot.move_forward,[120],None) 
    # print("Turn Right forward around obs2")

async def ReturnFromLeft(dispatcher,dist_y):
    """
    Return back to carpark after Obst2 is Right Arrow
    """
    y_travelled -= dist_y
    d = math.sqrt((-40 - x_travelled)**2 + (y_travelled)**2)
    a = math.sqrt((-20 - x_travelled)**2 + (y_travelled)**2)
    angle = math.degrees(math.acos(40/d))
    # cosA=(b2+c2-a2)/2bc
    b = 20
    turnAngle = math.degrees(math.acos((pow(b,2)+pow(d,2)-pow(a,2))/2*b*d)) - angle
    lineDist = math.sqrt((-40 - x_travelled)**2 + (y_travelled)**2 - ((2*20)**2))
    
    cmd_list = [(Robot.move_forward,[dist_y]), #turn forward 90 to left , parallel to Obst2  TODO Can consider 45 degree turns here?
                (Robot.turn_left,[turnAngle,True]  ),    #Move to edge of Obst2 (60 considering Largest size of 120cm) 
                (Robot.move_forward,[lineDist]),  #turn forward right to move behind Obst1   TODO Can consider 45 degree turns here?
                (Robot.turn_right,[turnAngle,True] )] #Move perpendicular to Obst 2 Facing Back/Carpark

    for cmd in cmd_list:
        while(Robot.poll_is_moving):
            await asyncio.sleep(0.05)
        else:
            #robot.turn_right(ANGLE, True)
            await dispatcher.dispatchB(cmd[0],cmd[1],None) 

async def ReturnFromRight(dispatcher,dist_y):
    """
    Return back to carpark after Obst2 is Left Arrow
    """
    y_travelled -= dist_y
    d = math.sqrt((40 - x_travelled)**2 + (y_travelled)**2)
    a = math.sqrt((20 - x_travelled)**2 + (y_travelled)**2)
    angle = math.degrees(math.acos(40/d))
    # cosA=(b2+c2-a2)/2bc
    b = 20
    turnAngle = math.degrees(math.acos((pow(b,2)+pow(d,2)-pow(a,2))/2*b*d)) - angle
    lineDist = math.sqrt((40 - x_travelled)**2 + (y_travelled)**2 - ((2*20)**2))
    
    cmd_list = [(Robot.move_forward,[dist_y]), #turn forward 90 to left , parallel to Obst2  TODO Can consider 45 degree turns here?
                (Robot.turn_right,[turnAngle,True]  ),    #Move to edge of Obst2 (60 considering Largest size of 120cm) 
                (Robot.move_forward,[lineDist]),  #turn forward right to move behind Obst1   TODO Can consider 45 degree turns here?
                (Robot.turn_left,[turnAngle,True] )] #Move perpendicular to Obst 2 Facing Back/Carpark

    for cmd in cmd_list:
        while(Robot.poll_is_moving):
            await asyncio.sleep(0.05)
        else:
            #robot.turn_right(ANGLE, True)
            await dispatcher.dispatchB(cmd[0],cmd[1],None) 

        
async def main():
    #_wrapper = WrapperInstance()
    #stm sensor
    #robot = _wrapper.robot
    #dispatcher = _wrapper.dispatcher
    Robot.set_threshold_disable_obstacle_detection()
    sensor = SRF05.SRF05(trigger_pin=17, echo_pin=27)
    dispatcher = BlockingDispatcher(Robot, 5, 2, u_if=_IO_Attr_Type.PHYSICAL)
    print("START TASK 2")
    start_time = time()
    print("Straight FORWARD TO DETECT OBS1 from origin")
    #robot.move_forward(30)                            
    tmp = [30]              #move forward to 1st obstacle; distance between 60-150cm

    FwdTillObst(dispatcher, sensor)
    
    obs1 = photographer.take_photo()                                           #scan 1st obstacle; return id
    #obs1 = 38
    print("1st obstacle direction: ", obs1)
    print("-" * 70)

    #1st obstacle 10x10
    #Right arrow id:38; left arrow id:39
    if obs1 == 38:
        Obst1Right(dispatcher)
    else:
        Obst1Left(dispatcher)

    y2 = FwdTillObst(dispatcher,sensor) + 60                             # Move forward till in front of Obstacle 2 with distance of 40, y2 used to avoid Obst1 on return motion

    obs2 = photographer.take_photo()                                     #scan 2nd obstacle
    #obs2 = 38
    print("2nd obstacle direction: ", obs2)
    print("-" * 70)

    #2nd obstacle 30 to 60 x 10
    if(obs2 == 38):
        Obst2Right(dispatcher)
        ReturnFromLeft(dispatcher=dispatcher, dist_y= y2)

    else:
        Obst2Left(dispatcher)
        ReturnFromRight(dispatcher=dispatcher, dist_y= y2)


       

    # #Return to start
        

    # #robot.move_forward(120) #fastest speed when going back origin
    # await dispatcher.dispatchB(robot.move_forward,[120],None) 
    # print("Straight forward towards origin after ob2")

    # #robot.turn_right(ANGLE, True)
    # await dispatcher.dispatchB(robot.move_forward,[120],None) 
    # print("Turn Right forward after obs 1 towards origin ")

    # #carpark 60x50 deep; carpark 20 + carpark to obs1 30 =  50
    # #robot.move_forward(50)
    # await dispatcher.dispatchB(robot.move_forward,[50],None) 
    print("Straight forward into origin")
    print("Parked.")

    end_time = time()
    execution_time = end_time - start_time
    print(f"Total execution time: {execution_time} seconds")
    print("Fin.")



if __name__ == '__main__':
    asyncio.run(main())
    

