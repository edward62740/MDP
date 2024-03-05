'''
[WIP] This is a replacement of mainalgo, where all the pygame shit is disabled cause I cant fucking get the dependancies to work on the RPI
- TODO: integrate the photo taking portion
- TODO: multi-process where needed
- TODO: add some control feature to trigger start only when asked
'''

from RPI_comms import RPI_connection
from time import sleep
from simulator import AlgoMinimal
from typing import List
from Map import *
import asyncio

rpi = RPI_connection()

def main():
    #rpi.bluetooth_connect() #TODO: test this on the android

    print("===========================Receive Obstacles Data===========================")
    print("Waiting to receive obstacle data from ANDROID...")

    #obst_message = rpi.android_receive()
    obst_message = '1,18,s,16,10,n,12,3,n,18,18,s,2,8,n,5,12,s'
    obstacles = parse_obstacle_data_cur(obst_message)
    print(obstacles) #debugging
    
    app = AlgoMinimal(obstacles)
    asyncio.run(app.execute())

def parse_obstacle_data_cur(obst_message: str) -> List[Obstacle]:
    '''
    converts obstacle data from android to list format. a bit weird here since im trying to fit it to the format that was previously written
    - input example argument: 1,3,N,19,10,S,12,13,S,11,0,W
    - output example return value:
    '''
    obst_split = obst_message.split(',')
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
        i["x"] += 5
        i["y"] *= 10
        i["y"] += 5
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

if __name__ == '__main__':
    main()