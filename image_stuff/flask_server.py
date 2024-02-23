# import cv2
# import os
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
}

def img_rec(image_file):
    results = model(image_file, device="0")
    mdp_id = id_to_class[int(results[0].boxes.cls)] # take the detected ID and convert to MDP ID
    results[0].save(filename=f'found_{mdp_id}.jpg')  # save to disk
    return mdp_id


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
