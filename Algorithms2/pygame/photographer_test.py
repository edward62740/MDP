import photographer
from time import sleep

cam = photographer.start_camera()
n = 3
print("taking pics now")
for i in range(8):
    photographer.fire_and_forget(cam)
    sleep(n)

sleep(1)
photographer.combine_images()
