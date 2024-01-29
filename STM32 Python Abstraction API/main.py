from time import sleep

from robot_controller import RobotController


def main():
    robot = RobotController('COM16', 115200)
    while 1:
        print(x := robot.get_quaternion())
        assert x is not None
        sleep(0.2)
        print(x := robot.get_yaw())
        assert x is not None
        sleep(0.2)
        print(x := robot.get_gyro_Z())
        assert x is not None
        sleep(0.2)
        print(x := robot.get_ir_L())
        assert x is not None
        sleep(0.2)
        print(x := robot.get_ir_R())
        assert x is not None
        sleep(0.2)
        print(x := robot.move_forward(10))
        assert x
        sleep(0.2)
        print(x := robot.move_backward(10))
        assert x
        sleep(0.2)




if __name__ == '__main__':
    main()
