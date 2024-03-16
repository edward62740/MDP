import logging
from time import sleep
from multiprocessing import Process

from stm32_api.dispatcher import BlockingDispatcher, _IO_Attr_Type

"""
This class acts as the mid-level abstraction that "translates" the ideal simulation commands to the set of commands for
the robot. It also gets the robot sensor data to act as heuristic for the algorithm.

Only 90 degree turns are supported (i.e. the set of commands that the algorithm uses).
Given some path in the form: straight1-rotate-straight2, where straight1 is x cm, rotate is k degrees, and straight2 is y cm,
turning radius of r cm, it's trivial to see that the ideal commands to compensate for turning arc is
straight(x - r), rotate(k), straight(y - r) and the min. inner clearance at the turning axis is sqrt(2) * r - r.

"""
from typing import List, Tuple, Any, Callable
from stm32_api.robot_controller import RobotController
from Robot.commands import *
import photographer


class Translator:
    GRID_UNIT_CM = 10
    TURN_ARC_RADIUS_CM = 20

    def __init__(self, robot_port: str, robot_baudrate: int):
        self.path: List[Any] = []
        self.robot = RobotController(robot_port, robot_baudrate)
        self.robot.set_threshold_stop_distance_right(1)
        self.robot.set_threshold_stop_distance_left(1) # remove in real run
        self.dispatcher = BlockingDispatcher(self.robot, 5, 2, u_if=_IO_Attr_Type.PHYSICAL)
        self.logger = logging.getLogger(__name__)
        self.moving = False

    def add_path(self, path: List[Command]):
        self.logger.debug("adding path %s", path)
        for movement in path:
            if not isinstance(movement, Command):
                raise ValueError("Invalid movement encountered: {}".format(movement))
            self.path.append(movement)
        return self.path

    def translate(self, path = ''): ### TODO Remove Compress and change to STM commands
        if path != '':
            self.path = path
        self.logger.debug("translating path")
        if len(self.path) < 2:
            return []
        cmd_path: List[Tuple[Callable, List[Any]]] = []

        for i in range(len(self.path)):
            tempCmd = self.path[i]
            #Straight Line movements
            if isinstance(tempCmd,StraightCommand):
                if tempCmd.dist > 0: # +ve Distance so move forward
                    cmd_path.append((RobotController.move_forward, [int(tempCmd.dist//SCALING_FACTOR)]))
                elif tempCmd.dist < 0: # Reverse for -ve Distance 
                    cmd_path.append((RobotController.move_backward, [abs(int(tempCmd.dist//SCALING_FACTOR))]))
            
            #Turning Motions TODO Confirm the turn angle +ve angle = turn left or right
            elif isinstance(tempCmd,TurnCommand):
                if tempCmd.angle > 0 and not tempCmd.rev:# Forward Left
                    cmd_path.append((RobotController.turn_left, [90,True]))
                elif tempCmd.angle > 0 and tempCmd.rev: # Reverse Wheel to Right; (Rear of car moving to right)
                    cmd_path.append((RobotController.turn_right, [90,False]))
                elif tempCmd.angle < 0 and not tempCmd.rev: #Forward to Right
                    cmd_path.append((RobotController.turn_right, [90, True]))
                elif tempCmd.angle < 0 and tempCmd.rev: # Reverse Wheel to Left; (Rear of car moving to left)
                    cmd_path.append((RobotController.turn_left, [90, False]))
            
            
            elif isinstance(tempCmd,ScanCommand):
                #SendRequest to take image
                cmd_path.append('Scan')

        cmd_path.append("Fin")
        self.logger.debug(cmd_path)
        return cmd_path

    def obstacle_callback(self, *args):
        print("Obstacle detected!")

    async def dispatch(self, cmd_path):
        self.logger.debug("Start Dispatch")
        self.logger.debug("dispatching path")
        for cmd in cmd_path:
            while self.moving:
                print("in while loopp", self.moving)
                self.moving = False # temporary 
                sleep(1)
            # print(cmd[0])
            # print(*cmd[1])
            # if cmd[0] != 'F':
            #     print(" | ")
            #     print(" V ")
            print(*cmd[1])
            if isinstance(cmd[0],str):
                snap_pic_process = Process(target=photographer.take_photo)
                snap_pic_process.start()
                # print('snap! took a photo')
                # photographer.take_photo()
                # sleep(0.5)#Take Image and send to rpi/pc
            else: 
                self.moving = True
                #cmd[0](self.robot, *cmd[1])
                print(cmd[1])
                await self.dispatcher.dispatchB(cmd[0], cmd[1], self.obstacle_callback)
                while(self.robot.poll_is_moving()):# If robot not moving
                # if(1):
                    self.moving = False
        self.logger.debug("dispatched path")
        return None
    
    async def dispatch_2(self, cmd_path): # TODO: a bit wonky here. fix.
        self.logger.debug("Start Dispatch")
        self.logger.debug("dispatching path")
        for cmd in cmd_path:
            while self.moving:
                print("in while loopp", self.moving)
                self.moving = False # temporary 
                sleep(1)

            print(cmd)
            if isinstance(cmd,str):
                snap_pic_process = Process(target=photographer.take_photo)
                snap_pic_process.start()
                # print('snap! took a photo')
                # photographer.take_photo()
                # sleep(0.5)#Take Image and send to rpi/pc
            else: 
                self.moving = True
                if len(cmd == 2):
                    print('robot supposed to move in a straight line, dist:', cmd[1])
                else:
                    print('robot moving curved, angle:', cmd[1], 'reverse:', cmd[2])
                # await self.dispatcher.dispatchB(cmd[0], cmd[1], self.obstacle_callback)
                # while(self.robot.poll_is_moving()):# If robot not moving
                # # if(1):
                #     self.moving = False
        self.logger.debug("dispatched path")
        return None