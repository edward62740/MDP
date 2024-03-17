'''
[WIP] This is a replacement of mainalgo
- TODO: robot movement currently seems incorrect. to check with team on expected robot movement
'''

import asyncio
from time import sleep
import requests
from typing import List
from Map import *
from settings import PC, FLASK_PORT
from Connection.RPI_comms import RPI_connection
from simulator import AlgoMinimal
#import pdb; pdb.set_trace()

rpi = RPI_connection()

def main():
    while True:
        print("Select choice of execution:")
        print("1. send map via android")
        print("2. send map via hardcoded map")
        choice = input()
        choice = int(choice)
        
        if choice == 1:
            rpi.bluetooth_connect() #TODO: test this on the android
            print("===========================Receive Obstacles Data===========================")
            print("Waiting to receive obstacle data from ANDROID...")
            obst_message = rpi.android_receive()
            try:
                obstacles = parse_obstacle_data_cur(obst_message)
                app = AlgoMinimal(obstacles)
                asyncio.run(app.execute())
            except Exception as e:
                print(e)
        elif choice == 2:
            #obst_message = '16,15,N,16,6,W,8,10,S,1,15,E,6,20,S'
            obst_message = '16,15,N,16,6,W,8,10,S,3,18,S,18,18,w'
            #obst_message = '18,18,s,3,18,s, 18,3,w'
            try:
                obstacles = parse_obstacle_data_cur(obst_message)
                app = AlgoMinimal(obstacles)
                asyncio.run(app.execute())
                print("finished Task 1")
            except Exception as e:
                print(e)
        else:
            print("invalid choice")

def parse_obstacle_data_cur(obst_message: str) -> List[Obstacle]:
    '''
    converts obstacle data from android to list format. a bit weird here since im trying to fit it to the format that was previously written
    - input example argument: 1,18,S,16,10,N,12,3,N,18,18,S,2,8,N,5,12,S
    - output example return value: [Obstacle(Position(15, 185,  angle=Direction.BOTTOM)), Obstacle(Position(165, 105,  angle=Direction.TOP)), Obstacle(Position(125, 35,  angle=Direction.TOP)), Obstacle(Position(185, 185,  angle=Direction.BOTTOM)), Obstacle(Position(25, 85,  angle=Direction.TOP)), Obstacle(Position(55, 125,  angle=Direction.BOTTOM))]
    '''
    obst_split = obst_message.split(',')
    print(obst_split)
    data = []
    for i in range(0,len(obst_split), 3):
        x = int(obst_split[i])
        y = int(obst_split[i+1])
        if(obst_split[i+2].upper() == 'N'):
            direction = 90
        elif(obst_split[i+2].upper() == 'S'):
            direction = -90
        elif(obst_split[i+2].upper() == 'E'):
            direction = 0
        elif(obst_split[i+2].upper() == 'W'):
            direction = 180
        obs_id = i // 3
        print({"x":x,"y":y,"direction":direction,"obs_id":obs_id})
        data.append({"x":x,"y":y,"direction":direction,"obs_id":obs_id})
    
    # this part onwards was the previously written parsing thing
    obs = []
    lst3 = []
    lst = []
    i = 0

    for obj in data:
        lst.append(obj)

    for i in lst:
        i["x"] *= 10
        i["x"] -= 5
        i["y"] *= 10
        i["y"] -= 5
        #i["obs_id"] -= 1

    a = [list(row) for row in zip(*[m.values() for m in lst])]

    for i in range(len(a[0])):
        lst2 = [item[i] for item in a]
        lst3.append(lst2)
        i+=1
        
    for obstacle_params in lst3:
        obs.append(Obstacle(obstacle_params[0],
                            obstacle_params[1],
                            Direction(obstacle_params[2]),
                            obstacle_params[3]))

    # [[x, y, orient, index], [x, y, orient, index]]
    return obs 

# def compute_on_PC(obst_message):
#     data = {'message': str(obst_message)}
#     response = requests.post(f'http://{PC}:{FLASK_PORT}/map', json=data)
#     if response.status_code == 200:
#         computed_path = response.text
#         print("COMPUTED PATH:", computed_path)
#         sleep(1)
#         return computed_path
#     else:
#         print("Server Down or message sending failed!")
#         return None
    

if __name__ == '__main__':
    main()
