'''
To be run on PC. PC hosts flask server for image recognition works
'''

import os
import ast
import torch
from io import BytesIO
from flask import Flask, request, jsonify
from PIL import Image
from ultralytics import YOLO
import random

from Algorithms.simulator import AlgoMinimal
from Algorithms.Map import Obstacle, Direction
from typing import List
# import cv2
# import numpy as np
# import uuid
# import math


app = Flask(__name__)
model = YOLO('./models/no_deadend.pt') # replace model here
id_to_class = { 
    0: 99, # convert detected image ID to their correct (MDP) class ID
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
    27: 38,
    28: 39,
    29: 40,
    99: 99,
}

output_class = {}

def choose_best_class(detected_items):
    YOLO_CONF_THRESH = 0.1

    if len(detected_items) == 0:
        print('No items detected')
        return -1, -1  # Return -1 to indicate no detections

    elif len(detected_items) == 1:
        # Only one item detected, return it
        detected_item = list(detected_items.keys())[0]
        _, confidence = detected_items[detected_item]
        return detected_item, confidence
        # if confidence > YOLO_CONF_THRESH:
        #    return detected_item
        #else:
        #    return -1  # Return -1 to indicate no detections
    else:
        # Handle multiple detections -> choose the best based on criteria
        best_actual_id = None
        biggest_area = 0
        conf_threshold = YOLO_CONF_THRESH  # to finalize threshold

        for actual_id, values in detected_items.items():
            size, confidence = values
            if size > biggest_area and confidence > conf_threshold:
                best_actual_id = actual_id
                biggest_area = size

    return best_actual_id, confidence

def detect_image(image_path):
    output_folder_path = './photos_taken'

    if not os.path.exists(output_folder_path):
        os.makedirs(output_folder_path)
        
    detected_items = {}

    try:
        # results = model(image_path, device="0") only with gpu
        results = model(image_path) # CPU
        result = results[0]
        detection_count = result.boxes.shape[0]
        print(f'Number of detections: {detection_count}')

        if detection_count == 0:
            return -1,-1  # Return -1 to indicate no detections
        
        boxes = result.boxes
        im_array = result.plot()
        im = Image.fromarray(im_array[..., ::-1])

        for i in range(detection_count):
            obj_detected_startfrom0 = int(result.boxes.cls[i])
            confidence = result.boxes.conf[i]
            bounding_box = result.boxes.xyxy[i]
            x_min, y_min, x_max, y_max = bounding_box
            box_width = x_max - x_min
            box_height = y_max - y_min
            box_size = box_width * box_height
            
            real_id = id_to_class[obj_detected_startfrom0]
            print(str(real_id)+' area: '+str(box_size))
            detected_items[real_id] = [box_size, confidence]

        chosen_class = choose_best_class(detected_items)
        #print('chosen_class ',chosen_class)
        if not output_class.get(chosen_class[0]) and detection_count >= 1:
            output_class[chosen_class[0]] = chosen_class[1]
            print('saving image')
            saved_filename = f'found_{chosen_class[0]}.jpg'
            im.save(os.path.join("./photos_taken", saved_filename))
        elif output_class[chosen_class[0]] < chosen_class[1] and detection_count >= 1:
            output_class[chosen_class[0]] = chosen_class[1]
            print('saving image')
            saved_filename = f'found_{chosen_class[0]}.jpg'
            im.save(os.path.join("./photos_taken", saved_filename))
        else:
            print('saving image by else')
            number = str(random.randint(0,9999999))
            saved_filename = f'found_{number}.jpg'
            im.save(os.path.join("./photos_taken", saved_filename))

        #if detection_count >= 1:
        #    print('saving image')
        #    saved_filename = f'found_{chosen_class[0]}.jpg'
        #    im.save(os.path.join("./output", saved_filename))

        if chosen_class is not None:
            return chosen_class
        if chosen_class is None:
            return -1,-1  # Return -1 to indicate no detections

    except Exception as e:
        print(f"[IMG-DET ERROR] Error processing {image_path}: {e}")
        return -1,-1 # No detection

'''
def img_rec(image_file):
    results = model(image_file, device="0")
    mdp_id = id_to_class[int(results[0].boxes.cls)] # take the detected ID and convert to MDP ID
    results[0].save(filename=f'found_{chosen_class}.jpg')  # save to disk

    return mdp_id
'''

@app.route('/upload', methods=['POST'])
def upload_image():
    if 'image' not in request.files:
        return jsonify({'message': 'No image part'}), 400  # Return an error response 
    image = request.files['image']
    img = Image.open(BytesIO(image.read()))
    # mdp_id = img_rec(img)
    mdp_id = detect_image(img)
    if mdp_id[0] == -1:
        img.save(f'./photos_taken/not_found_{str(random.randint(0,9999999))}.jpeg', 'JPEG')
        result = {'message': 'TARGET,Obstacle_num,-1,-1'}
    else:
        result = {'message': f'TARGET,Obstacle_num,{mdp_id[0]},{mdp_id[1]}'}
    return jsonify(result), 200  # Return a success response with the result

# To receive map data from RPI for computation of hamiltonian path on PC
@app.route('/map', methods=['POST'])
def upload_map():
    map = request.json
    map = map['message']

    obstacles = parse_obstacle_data_cur(map)
    app = AlgoMinimal(obstacles)
    path = app.plan_path_only()
    path = list(path) 
    return jsonify(str(path)), 200 

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
    
def start_server(host, port, debug):
    app.run(host=host,port=port,debug=debug)    

if __name__ == '__main__':
    app.run(host='0.0.0.0',port=8081,debug=False)