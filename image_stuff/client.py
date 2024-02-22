import requests
import time
from io import BytesIO
from picamera import Picamera

class ImageRec:
    def __init__(self):
        # Camera object
        self.url = 'http://127.0.0.1:8080/upload'

    def take_photo(self):
        camera = Picamera()
        camera.resolution = (640,640)
        try:
            image_stream = BytesIO()
            camera.capture(image_stream, format='jpeg') # take photo and save as given name
            image_stream.seek(0)
            files = {'image': ('camera_photo.jpg',image_stream,'image/jpeg')}
            response = requests.post(self.url, files=files)

            if response.status_code == 200:
                mdp_id = response.text
                print(mdp_id)
            # time.sleep(2)
            else:
                print("Server Down or Image Rec failed!")
        except KeyboardInterrupt:
            pass
        finally:
            # Clean up resource
            camera.close()
