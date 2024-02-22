import requests
from io import BytesIO

url = 'http://127.0.0.1:8080/upload'
# Take a photo

with open('zzz.jpg', 'rb') as file:
    byte_stream = BytesIO(file.read())

byte_stream.seek(0)

# files = {'image': open('1_far.jpg', 'rb')}
files = {'image': ('5_close.jpg',byte_stream,'image/jpeg')}
response = requests.post(url, files=files)

if response.status_code == 200:
    mdp_id = response.text
    print(mdp_id)
else:
    print('fail')
