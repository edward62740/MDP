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
from RPI_flask import RPIFlaskServer
from multiprocessing import Process
#import pdb; pdb.set_trace()


def main():
    rpi = RPI_connection()
    while True:
        print("Select choice of execution:")
        print("1. send map via android")
        print("2. send map via hardcoded map")
        choice = input()
        try:
            choice = int(choice)
        except:
            rpi.bluetooth_disconnect()
            break
        
        if choice == 1:
            rpi.bluetooth_connect() 
            print("===========================Receive Obstacles Data===========================")
            print("Waiting to receive obstacle data from ANDROID...")
            obst_message = rpi.android_receive()
            rpi_flask = RPIFlaskServer(rpi)
            rpi_flask_process = Process(target=rpi_flask.run_server)
            rpi_flask_process.start()
            try:
                obstacles = parse_obstacle_data_cur(obst_message)
                app = AlgoMinimal(obstacles, rpi)
                asyncio.run(app.execute())
            except Exception as e:
                print(e)
                
        elif choice == 2:
            obst_message = 'OBS|16,15,N,1|16,6,W,2|8,10,S,3|3,18,S,4|18,18,W,5|'
            rpi_flask = RPIFlaskServer(None)
            rpi_flask_process = Process(target=rpi_flask.run_server)
            rpi_flask_process.start()
            try:
                obstacles = parse_obstacle_data_cur(obst_message)
                app = AlgoMinimal(obstacles, None)
                asyncio.run(app.execute())
                print("finished Task 1")
            except Exception as e:
                print(e)
                
        elif choice == 3: # for testing only
            rpi.bluetooth_connect()
            rpi_flask = RPIFlaskServer(rpi)
            rpi_flask_process = Process(target=rpi_flask.run_server)
            rpi_flask_process.start()
        else:
            print("invalid choice")

def parse_obstacle_data_cur(obst_message: str) -> List[Obstacle]:
    '''
    converts obstacle data from android to list format. a bit weird here since im trying to fit it to the format that was previously written
    - input example argument: OBS|16,15,N,1|16,6,W,2|8,10,S,3|3,18,S,4|18,18,W,5|
    - output example return value: [Obstacle(Position(15, 185,  angle=Direction.BOTTOM)), Obstacle(Position(165, 105,  angle=Direction.TOP)), Obstacle(Position(125, 35,  angle=Direction.TOP)), Obstacle(Position(185, 185,  angle=Direction.BOTTOM)), Obstacle(Position(25, 85,  angle=Direction.TOP)), Obstacle(Position(55, 125,  angle=Direction.BOTTOM))]
    '''
    obst_split = obst_message.split('|')
    data = []
    for obs in obst_split:
        if obs == 'OBS' or obs == '':
            0
        else:
            obs_a = obs.split(',')
            if(obs_a[2].upper() == 'N'):
                direction = 90
            elif(obs_a[2].upper() == 'S'):
                direction = -90
            elif(obs_a[2].upper() == 'E'):
                direction = 0
            elif(obs_a[2].upper() == 'W'):
                direction = 180
            data.append({'x': int(obs_a[0]), 'y': int(obs_a[1]), 'direction': direction, 'obs_id': int(obs_a[3])})
    
    
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
