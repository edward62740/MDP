from typing import List
from Algorithms.Map import Obstacle, Direction
from Algorithms.simulator import AlgoMinimal
from collections import deque
import ast 

def compute(map):
    obstacles = parse_obstacle_data_cur(map)
    app = AlgoMinimal(obstacles)
    path = app.plan_path_only()
    serialized_data = list(path)
    return serialized_data


def parse_obstacle_data_cur(obst_message: str) -> List[Obstacle]:
    '''
    converts obstacle data from android to list format. a bit weird here since im trying to fit it to the format that was previously written
    - input example argument: 1,18,S,16,10,N,12,3,N,18,18,S,2,8,N,5,12,S
    - output example return value: [Obstacle(Position(15, 185,  angle=Direction.BOTTOM)), Obstacle(Position(165, 105,  angle=Direction.TOP)), Obstacle(Position(125, 35,  angle=Direction.TOP)), Obstacle(Position(185, 185,  angle=Direction.BOTTOM)), Obstacle(Position(25, 85,  angle=Direction.TOP)), Obstacle(Position(55, 125,  angle=Direction.BOTTOM))]
    '''
    obst_message = obst_message.replace(' ', '')
    if obst_message[-1] == ',':
        obst_message = obst_message[:-1]
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
    d = compute('16,15,N,16,6,W,8,10,S,1,15,E,6,20,S')
    d = ast.literal_eval(str(d))
    print(d)
    print(type(d))
    for i in d:
        print(i)
        print(type(i))