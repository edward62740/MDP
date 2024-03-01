import asyncio
from time import sleep

from robot_controller import RobotController
from dispatcher import _Dispatcher, BlockingDispatcher, ConcurrentDispatcher, _IO_Attr_Type


def cb_fn(*args):
    print("Obstacle detected!")
    print(args)


def cb_fn2(*args):
    print("COMPLETED CALLBACK FROM DISPATCHER2 WITH: ")
    print(args)


def cb_fn3(*args):
    print("OBSTACLE DETECTED WITH TOTAL DISTANCE SUCCESSFULLY MOVED AS: ")
    print(args)


async def main():
    robot = RobotController('COM3', 115200, cb_fn3)
    dispatcher = BlockingDispatcher(robot, 15, 2, _IO_Attr_Type.SIMULATED)
    dispatcher2 = ConcurrentDispatcher(robot, 5, 2, _IO_Attr_Type.SIMULATED)
    print(robot.set_threshold_stop_distance_right(10))

    dispatcher2.listen_for_obstruction(cb_fn3)

    dispatcher2.dispatch(robot.get_quaternion, [], cb_fn, cb_fn2)  # async example
    dispatcher.dispatch(robot.move_forward, [10], cb_fn)  # async using the blocking dispatcher also works
    await dispatcher.dispatchB(robot.move_forward, [10], cb_fn)  # blocking example


if __name__ == '__main__':
    asyncio.run(main())
