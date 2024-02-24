import asyncio
from io import BytesIO
from time import sleep
import picamera
import requests
from robot_controller import RobotController

import SRF05


def cb_fn(*args):
    print("Obstacle detected!")
    print(args)


id_to_class = {
    0: 11,
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


def take_photo():
    with picamera.PiCamera() as camera:
        camera.resolution = (640, 640)
        image_stream = BytesIO()
        camera.capture(image_stream, format='jpeg')  # take photo and save as given name
        image_stream.seek(0)
        files = {'image': ('camera_photo.jpg', image_stream, 'image/jpeg')}
        response = requests.post('http://127.0.0.1:8080/upload', files=files)

        if response.status_code == 200:
            mdp_id = response.text
            print(mdp_id)
            return mdp_id
        # time.sleep(2)
        else:
            print("Server Down or Image Rec failed!")
            return None

async def main():
    robot = RobotController('/dev/ttyUSB0', 115200)
    robot.set_threshold_disable_obstacle_detection()
    sensor = SRF05.SRF05(trigger_pin=17, echo_pin=27)
    robot.move_forward(500)
    x = sensor.measure()
    while x is None or x > 40:
        x = sensor.measure()
        sleep(0.05)

    x = robot.halt()
    sleep(0.05)
    x = robot.halt()
    sleep(0.05)
    x = robot.halt()
    robot.move_backward(50)
    # take picture
    while robot.poll_is_moving():
        sleep(1)
    robot.turn_left(90, True)
    while robot.poll_is_moving():
        sleep(1)
    robot.move_forward(35)
    while robot.poll_is_moving():
        sleep(1)

    for i in range(4):
        robot.turn_right(90, True)
        while robot.poll_is_moving():
            sleep(1)
        robot.move_forward(30)
        while robot.poll_is_moving():
            sleep(1)
        robot.turn_right(90, True)
        while robot.poll_is_moving():
            sleep(1)
        #take picture
        mdp_id = None

        if mdp_id is not None and i==2:
            print("found mdp_id: ", mdp_id)
            exit(1)

        robot.turn_right(90, False)
        print("exit turn right")
        while robot.poll_is_moving():
            sleep(1)

        robot.move_forward(75)
        while robot.poll_is_moving():
            sleep(1)


if __name__ == '__main__':
    asyncio.run(main())
