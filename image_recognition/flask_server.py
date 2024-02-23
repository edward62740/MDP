# import cv2
import os
# import numpy as np
# import uuid
# import math
import torch
from io import BytesIO
from flask import Flask, request, jsonify
from PIL import Image
from ultralytics import YOLO


app = Flask(__name__)
model = YOLO('best_bull.pt') # replace model here
id_to_class = { 
    0: 11, # convert detected image ID to their correct (MDP) class ID
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

def choose_best_class(detected_items):
    YOLO_CONF_THRESH = 0.5

    if len(detected_items) == 0:
        print('No items detected')
        return -1  # Return -1 to indicate no detections

    elif len(detected_items) == 1:
        # Only one item detected, return it
        detected_item = list(detected_items.keys())[0]
        _, confidence = detected_items[detected_item]
        if confidence > YOLO_CONF_THRESH:
            return detected_item
        else:
            return -1  # Return -1 to indicate no detections
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

    return best_actual_id

def detect_image(image_path):
    output_folder_path = './output'

    if not os.path.exists(output_folder_path):
        os.makedirs(output_folder_path)
        
    detected_items = {}

    try:
        results = model(image_path, device="0")
        result = results[0]
        detection_count = result.boxes.shape[0]
        print(f'Number of detections: {detection_count}')

        if detection_count == 0:
            return -1  # Return -1 to indicate no detections
        
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

        if detection_count >= 1:
            print('saving image')
            saved_filename = f'found_{chosen_class}.jpg'
            im.save(os.path.join("./output", saved_filename))

        if chosen_class is not None:
            return chosen_class
        if chosen_class is None:
            return -1  # Return -1 to indicate no detections

    except Exception as e:
        print(f"[IMG-DET ERROR] Error processing {image_path}: {e}")

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
    mdp_id = img_rec(img)
    result = {'message': f'TARGET,Obstacle_num,{mdp_id}'}
    return jsonify(result), 200  # Return a success response with the result
    
if __name__ == '__main__':
    app.run(host='0.0.0.0',port=8080,debug=False)
