'''
Takes a photo and uploads to flask server for image recognition works
'''

import picamera
import requests
from io import BytesIO
from settings import PC, FLASK_PORT
import time

def take_photo():
    print("snap! picture taken")
    with picamera.PiCamera() as camera:
        camera.resolution = (1980, 1980)
        image_stream = BytesIO()
        camera.capture(image_stream, format='jpeg')  # take photo and save as given name
        image_stream.seek(0)
        files = {'image': ('camera_photo.jpg', image_stream, 'image/jpeg')}
        response = requests.post(f'http://{PC}:{FLASK_PORT}/upload', files=files)

        if response.status_code == 200:
            mdp_id = response.text
            print(mdp_id)
            time.sleep(1)
            return mdp_id
        else:
            print("Server Down or Image Rec failed!")
            return None
        
if __name__ == '__main__':
    take_photo()
