import asyncio
import SRF05

from Robot.commands import *
import photographer
from time import *
from Connection.RPI_comms import RPI_connection
from stm32_api.dispatcher import BlockingDispatcher, _IO_Attr_Type

robot = RobotController(PORT, BAUD)

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


async def obs1(id1, dispatcher):
    if(id1 == 38):  #turn Right; RS LS R
        await dispatcher.dispatchB(robot.turn_right,[45,True],None)
        await dispatcher.dispatchB(robot.move_forward,[35],None) 
        await dispatcher.dispatchB(robot.turn_left,[90,True],None)
        await dispatcher.dispatchB(robot.move_forward,[30],None)        
        await dispatcher.dispatchB(robot.turn_right,[45,True],None)

    else:  #turn Left; LS RS L
        await dispatcher.dispatchB(robot.turn_left,[45,True],None)
        await dispatcher.dispatchB(robot.move_forward,[35],None) 
        await dispatcher.dispatchB(robot.turn_right,[90,True],None)
        await dispatcher.dispatchB(robot.move_forward,[30],None)        
        await dispatcher.dispatchB(robot.turn_left,[45,True],None)
        
 

async def obs2(id2, dispatcher):
    if(id2 == 38): #turn Right; RS LS L
        await dispatcher.dispatchB(robot.turn_right,[60,True],None)
        await dispatcher.dispatchB(robot.move_forward,[50],None) 
        await dispatcher.dispatchB(robot.turn_left,[135,True],None)
        await dispatcher.dispatchB(robot.move_forward,[60],None) #30-120 length of ob2
        await dispatcher.dispatchB(robot.turn_left,[80,True],None)
        returnOrigin(id2,dispatcher)

    else: #turn Left; LS RS R
        await dispatcher.dispatchB(robot.turn_left,[60,True],None)
        await dispatcher.dispatchB(robot.move_forward,[50],None) 
        await dispatcher.dispatchB(robot.turn_right,[135,True],None)
        await dispatcher.dispatchB(robot.move_forward,[70],None) #30-120 length of ob2
        await dispatcher.dispatchB(robot.turn_right,[80,True],None)
        returnOrigin(id2,dispatcher)


        
async def returnOrigin(id2,dispatcher):
    if(id2 == 38): #S R or SLRS
        await dispatcher.dispatchB(robot.move_forward,[140],None) #min 140 - max 320
        await dispatcher.dispatchB(robot.turn_left,[35],None) 
        await dispatcher.dispatchB(robot.move_forward,[30],None) #carpark 60x50 deep; carpark 20 + carpark to obs1 30 =  50
        

    else: #S L or SRLS
        await dispatcher.dispatchB(robot.move_forward,[140],None) #min 140 - max 320
        await dispatcher.dispatchB(robot.turn_right,[35],None) 
        await dispatcher.dispatchB(robot.move_forward,[30],None) #carpark 60x50 deep; carpark 20 + carpark to obs1 30 =  50
        
async def moveStraight(dispatcher,sensor):
    await dispatcher.dispatchB(robot.move_forward,[50],cb_fn) #move forward to 1st obstacle; distance between 60-150cm
    #sensor
    x = sensor.measure()
    while x is None or x > 40:                                      #range distance min(60,150)
        x = sensor.measure()
        sleep(0.05)
        if robot.poll_is_moving()==False:
            await dispatcher.dispatchB(robot.move_forward,[50],cb_fn)
    x = robot.halt()
    await asyncio.sleep(0.05)
    x = robot.halt()
    sleep(0.05)
    
    id = photographer.take_photo()                                           #scan 1st obstacle; return id
    while (id != 38 or id != 39):
        print("----------not right/left direction----------")
        id = photographer.take_photo() 
    print("obstacle direction ID: ", obs1)
    return id
    
async def main():
    #_wrapper = WrapperInstance()
    #stm sensor
    #robot = _wrapper.robot
    #dispatcher = _wrapper.dispatcher

    robot.set_threshold_disable_obstacle_detection()
    sensor = SRF05.SRF05(trigger_pin=17, echo_pin=27)
    dispatcher = BlockingDispatcher(robot, 5, 2, u_if=_IO_Attr_Type.PHYSICAL)
    
    print("START TASK 2")
    start_time = time()
    id1 = moveStraight(dispatcher,sensor)   #scan 1st obstacle; return id
    print("-" * 70)
    obs1(id1,dispatcher) #1st obstacle 10x10
   
    print("-" * 70)
    id2 = moveStraight(dispatcher,sensor)   #scan 1st obstacle; return id
    obs2(id2,dispatcher) #2nd obstacle 30-120 x 10

    print("Parked.")
    end_time = time()
    execution_time = end_time - start_time
    print(f"Total execution time: {execution_time} seconds")



if __name__ == '__main__':
    asyncio.run(main())
    

