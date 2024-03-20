'''
Test sending message over from flask
'''
import requests
from io import BytesIO
from settings import PC, FLASK_PORT
import time

def compute_on_PC(obst_message):
    data = {'message': obst_message}
    response = requests.post(f'http://192.168.22.31:8081/map', json=data)

    if response.status_code == 200:
        computed_path = response.text
        print(computed_path)
        time.sleep(1)
        return computed_path
    else:
        print("Server Down or message sending failed!")
        return None

def receive_message():
    url = 'http://192.168.22.31:8081/path'
    response = requests.get(url)
    print(response.text)
 
        
if __name__ == '__main__':
    send_message()
