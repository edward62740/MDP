'''
To be run on PC. PC hosts flask server for image recognition works
'''

import os
import torch
from io import BytesIO
from flask import Flask, request, jsonify
from PIL import Image
from ultralytics import YOLO
import random
import requests
from simulator import AlgoMinimal
from Map import Obstacle, Direction
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
    
    if 'obj_index' in request.files:
        obj_index = request.files['obj_index'].read().decode('utf-8')
        print("obj_index", obj_index)
        url = 'http://192.168.22.22:2222/class_detected' # pi server
        data = f'{mdp_id[0]},{int(obj_index)}' # detection class
        headers = { # filler
            'Content-Type':'plain'
        }
        requests.post(url,data=data,headers=headers)
        
        return 't', 202
    
    elif 'task2' in request.files:
        if mdp_id[0] == -1:
            img.save(f'./photos_taken/not_found_{str(random.randint(0,9999999))}.jpeg', 'JPEG')
            result = {'message': 'No image found'}
        else:
            result = {'message': f'{mdp_id[0]},{mdp_id[1]}'}
        return jsonify(result), 200  # Return a success response with the result
        

@app.route('/combine_images', methods=['POST'])
def combine_images_two_columns():
    folder_path = './photos_taken'  # Change to your folder path
    output_path = 'combined_result.jpg'  # Output image path
    # Load all the images in the folder that end with .jpg
    images = [Image.open(os.path.join(folder_path, f)) for f in os.listdir(folder_path) if f.endswith('.jpg')]
    
    # Split the images into two columns
    left_column_images = images[::2]  # Images at even indices
    right_column_images = images[1::2]  # Images at odd indices

    # Calculate total height for each column
    left_column_height = sum(image.height for image in left_column_images)
    right_column_height = sum(image.height for image in right_column_images)

    # Calculate the maximum width for both columns to align them properly
    max_width_left = max(image.width for image in left_column_images)
    max_width_right = max(image.width for image in right_column_images)

    # Create a new image with the appropriate size
    total_height = max(left_column_height, right_column_height)
    combined_image = Image.new('RGB', (max_width_left + max_width_right, total_height))

    # Paste the images in the left column
    y_offset_left = 0
    for image in left_column_images:
        combined_image.paste(image, (0, y_offset_left))
        y_offset_left += image.height

    # Paste the images in the right column
    y_offset_right = 0
    for image in right_column_images:
        combined_image.paste(image, (max_width_left, y_offset_right))
        y_offset_right += image.height

    # Save the combined image
    combined_image.save(output_path)
    
    return jsonify({"message": "Images combined successfully"})
    
def start_server(host, port, debug):
    app.run(host=host,port=port,debug=debug)    

if __name__ == '__main__':
    app.run(host='0.0.0.0',port=8080,debug=False)