import asyncio
import SRF05

from Robot.commands import *
from stm32_api.dispatcher import *
import photographer
from time import *


from Connection.RPI_comms import RPI_connection
from stm32_api.dispatcher import BlockingDispatcher, _IO_Attr_Type


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
   
async def main():
    robot = RobotController(PORT, BAUD)
    DIST = 100 # cm
    ANGLE = 45 # degrees

    #stm sensor
    robot.set_threshold_disable_obstacle_detection()
    sensor = SRF05.SRF05(trigger_pin=17, echo_pin=27)
    dispatcher = BlockingDispatcher(robot, 5, 2, u_if=_IO_Attr_Type.PHYSICAL)
    print("START TASK 2")
    start_time = time()

    print("Straight FORWARD TO DETECT OBS1 from origin")
    robot.move_forward(50)                                          #move forward to 1st obstacle; distance between 60-150cm
    #await dispatcher.dispatchB(robot.move_forward,[30],None)


    #sensor
    x = sensor.measure()
    while x is None or x > 45:                                      #range distance min(60,150)
        x = sensor.measure()
        sleep(0.05)
        if robot.poll_is_moving()==False:
            robot.move_forward(50)

    x = robot.halt()
    sleep(0.05)
    x = robot.halt()
    sleep(0.05)
    #x = sensor.measure()
    #while x is None:                                      #range distance min(60,150)
    #    x = sensor.measure()
    #    sleep(0.05)
    #print(x)
    #robot.move_backward(30 -int(x))
    obs1 = photographer.take_photo()                                           #scan 1st obstacle; return id
    #obs1 = 38
    print("1st obstacle direction: ", obs1)
    print("-" * 70)

    #1st obstacle 10x10
    #Right arrow id:38; left arrow id:39
    if obs1 == 38:
        
        robot.turn_right(ANGLE, True)                               #turn forward right arnd 1st obstacle
        #await dispatcher.dispatchB(robot.turn_right,[ANGLE,True],None)
        print("Turn Right forward around obs1")

        robot.turn_left(ANGLE, True)                                #turn forward left
        #await dispatcher.dispatchB(robot.turn_left,[ANGLE,True],None)
        print("Turn Left forward around obs1")        

        robot.move_forward(20)                                      #move forward; facing East
        #await dispatcher.dispatchB(robot.move_forward,[20],None)
        print("Straight forward arnd obs1")

        robot.turn_left(ANGLE, True)                                #turn forward left
        #await dispatcher.dispatchB(robot.turn_left,[ANGLE,True],None)
        print("Turn Left forward towards obs2")

        robot.turn_right(ANGLE, True)                               #turn forward right arnd 1st obstacle
        #await dispatcher.dispatchB(robot.turn_right,[ANGLE,True],None)
        print("Turn Right forward towards obs2")

        robot.move_forward(40)                                      #move forward; facing North
        #await dispatcher.dispatchB(robot.move_forward,[40],None) 
        print("Straight forward TO DETECT OBS2")
        
        #sensor
        y = sensor.measure()
        while y is None or y > 40:                                   #range distance min(60,150)
            y = sensor.measure()
            sleep(0.05)
        y = robot.halt()
        sleep(0.05)
        y = robot.halt()
        sleep(0.05)

        obs2 = photographer.take_photo()                                     #scan 2nd obstacle
        #obs2 = 38
        print("2nd obstacle direction: ", obs2)
        print("-" * 70)

        #2nd obstacle 30 to 60 x 10
        if(obs2 == 38):

            robot.turn_right(ANGLE, True)
            #await dispatcher.dispatchB(robot.turn_right,[ANGLE,True],None)
            print("Turn Right forward around obs2")

            robot.move_forward(20)
            #await dispatcher.dispatchB(robot.move_forward,[20],None) 
            print("Straight forward arnd obs2")

            robot.turn_left(ANGLE, True)
            #await dispatcher.dispatchB(robot.turn_left,[ANGLE,True],None)
            print("Turn Left forward arnd obs2")

            robot.move_forward(65)                                  #length of obstacle2
            #await dispatcher.dispatchB(robot.move_forward,[65],None)   
            print("Straight forward at top of obs2")

            robot.turn_left(ANGLE, True)
            #await dispatcher.dispatchB(robot.turn_left,[ANGLE,True],None)
            print("Turn Left forward around obs2")
            
            print("-" * 70)
            
            #to origin turn Right
            robot.move_forward(120)
            #await dispatcher.dispatchB(robot.move_forward,[120],None) 
            print("Straight forward towards origin after ob2")

            robot.turn_left(ANGLE, True)
            #await dispatcher.dispatchB(robot.turn_left,[ANGLE,True],None)
            print("Turn Left forward after obs 1 towards origin ")

            robot.move_forward(50)
            #await dispatcher.dispatchB(robot.move_forward,[50],None) 
            print("Straight forward into origin")
            print("Parked.")

        else:
            
            robot.turn_left(ANGLE, True)
            #await dispatcher.dispatchB(robot.turn_left,[ANGLE,True],None)
            print("Turn Left forward around obs2")

            robot.move_forward(20)      
            #await dispatcher.dispatchB(robot.move_forward,[20],None) 
            print("Straight forward around obs2")

            robot.turn_right(ANGLE, True)
            #await dispatcher.dispatchB(robot.move_forward,[120],None) 
            print("Turn Right forward around obs2")

            robot.move_forward(65) #length 30-60
            #await dispatcher.dispatchB(robot.move_forward,[65],None) 
            print("Straight forward at top of obs2")

            robot.turn_right(ANGLE, True)
            #await dispatcher.dispatchB(robot.move_forward,[120],None) 
            print("Turn Right forward around obs2")

            print("-" * 70)

            #to origin turn left
            robot.move_forward(120) #fastest speed when going back origin
            #await dispatcher.dispatchB(robot.move_forward,[120],None) 
            print("Straight forward towards origin after ob2")

            robot.turn_right(ANGLE, True)
            #await dispatcher.dispatchB(robot.move_forward,[120],None) 
            print("Turn Right forward after obs 1 towards origin ")

            #carpark 60x50 deep; carpark 20 + carpark to obs1 30 =  50
            robot.move_forward(50)
            #await dispatcher.dispatchB(robot.move_forward,[50],None) 
            print("Straight forward into origin")
            print("Parked.")

        


    else:

        #robot.turn_left(ANGLE, True)                                #turn forward right arnd 1st obstacle
        await dispatcher.dispatchB(robot.turn_left,[ANGLE,True],None)
        print("Turn Left forward around obs1")

        #robot.move_forward(40)                                      #move forward; facing East
        await dispatcher.dispatchB(robot.move_forward,[30],None) 
        print("Straight forward arnd obs1")
        
        #robot.turn_right(90, True)                               #turn forward left
        await dispatcher.dispatchB(robot.turn_right,[90,True],None)
        print("Turn Right forward towards obs2")
        
        #robot.move_forward(40)
        await dispatcher.dispatchB(robot.move_forward,[30],None)

        #robot.turn_left(ANGLE, True)                                #turn forward right arnd 1st obstacle
        await dispatcher.dispatchB(robot.turn_left,[ANGLE,True],None)
        print("Turn Left forward around obs1")


        #robot.move_forward(20)                                      #move forward; facing North
        await dispatcher.dispatchB(robot.move_forward,[150],None) 
        print("Straight forward TO DETECT OBS2")

        #sensor
        y = sensor.measure()
        while y is None or y > 40:                                   #range distance min(60,150)
            y = sensor.measure()
            sleep(0.05)
        y = robot.halt()
        sleep(0.05)
        y = robot.halt()
        sleep(0.05)

        obs2 = photographer.take_photo()                                          #scan 2nd obstacle
        print("2nd obstacle direction: ", obs2)
        print("-" * 70)

        #2nd obstacle 30 to 60 x 10
        if(obs2 == 38):

            robot.turn_right(ANGLE, True)
            #await dispatcher.dispatchB(robot.turn_right,[ANGLE,True],None)
            print("Turn Right forward around obs2")

            robot.move_forward(20)
            #await dispatcher.dispatchB(robot.move_forward,[20],None) 
            print("Straight forward arnd obs2")

            robot.turn_left(ANGLE, True)
            #await dispatcher.dispatchB(robot.turn_left,[ANGLE,True],None)
            print("Turn Left forward arnd obs2")

            robot.move_forward(65)                                  #length of obstacle2
            #await dispatcher.dispatchB(robot.move_forward,[65],None)   
            print("Straight forward at top of obs2")

            robot.turn_left(ANGLE, True)
            #await dispatcher.dispatchB(robot.turn_left,[ANGLE,True],None)
            print("Turn Left forward around obs2")
            
            print("-" * 70)
            
            #to origin turn Right
            robot.move_forward(120)
            #await dispatcher.dispatchB(robot.move_forward,[120],None) 
            print("Straight forward towards origin after ob2")

            robot.turn_left(ANGLE, True)
            #await dispatcher.dispatchB(robot.turn_left,[ANGLE,True],None)
            print("Turn Left forward after obs 1 towards origin ")

            robot.move_forward(50)
            #await dispatcher.dispatchB(robot.move_forward,[50],None) 
            print("Straight forward into origin")
            print("Parked.")

        else:
            
            #robot.turn_left(ANGLE, True)
            await dispatcher.dispatchB(robot.turn_left,[ANGLE,True],None)
            print("Turn Left forward around obs2")

            #robot.move_forward(20)      
            await dispatcher.dispatchB(robot.move_forward,[30],None) 
            print("Straight forward around obs2")

            #robot.turn_right(135,True)
            await dispatcher.dispatchB(robot.turn_right,[135,True],None)
            print("Go behind obs 2")

            #robot.turn_right(ANGLE, True)
            await dispatcher.dispatchB(robot.move_forward,[120],None) 
            print("Turn Right forward around obs2")

            #robot.move_forward(65) #length 30-60
            await dispatcher.dispatchB(robot.move_forward,[65],None) 
            print("Straight forward at top of obs2")

            #robot.turn_right(ANGLE, True)
            await dispatcher.dispatchB(robot.move_forward,[120],None) 
            print("Turn Right forward around obs2")

            print("-" * 70)

            #to origin turn left
            robot.move_forward(120) #fastest speed when going back origin
            #await dispatcher.dispatchB(robot.move_forward,[120],None) 
            print("Straight forward towards origin after ob2")

            robot.turn_right(ANGLE, True)
            #await dispatcher.dispatchB(robot.move_forward,[120],None) 
            print("Turn Right forward after obs 1 towards origin ")

            #carpark 60x50 deep; carpark 20 + carpark to obs1 30 =  50
            robot.move_forward(50)
            #await dispatcher.dispatchB(robot.move_forward,[50],None) 
            print("Straight forward into origin")
            print("Parked.")
    


    end_time = time.time()
    execution_time = end_time - start_time
    print(f"Total execution time: {execution_time} seconds")
    print("Fin.")



if __name__ == '__main__':
    asyncio.run(main())
    

