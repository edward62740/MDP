import logging
from time import sleep
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


class Translator:
    GRID_UNIT_CM = 10
    TURN_ARC_RADIUS_CM = 20

    def __init__(self, robot_port: str, robot_baudrate: int):
        self.path: List[Any] = []
        self.robot = RobotController(robot_port, robot_baudrate)
        self.logger = logging.getLogger(__name__)
        self.moving = False

    def add_path(self, path: List[Command]):
        self.logger.debug("adding path %s", path)
        for movement in path:
            if not isinstance(movement, Command):
                raise ValueError("Invalid movement encountered: {}".format(movement))
            self.path.append(movement)

    def translate(self): ### TODO Remove Compress and change to STM commands
        self.logger.debug("translating path")
        if len(self.path) < 2:
            return []
        cmd_path: List[Tuple[Callable, List[Any]]] = []

        summarized_path: List[List[Any]] = []

        """
        # shorten the path by combining consecutive straight movements
        for i in range(0, len(self.path)):
            if i == 0:
                summarized_path.append([self.path[i], self.GRID_UNIT_CM])
            elif self.path[i] == self.path[i - 1] and len(summarized_path) > 0:
                summarized_path[-1][1] += self.GRID_UNIT_CM

            else:
                summarized_path.append([self.path[i], self.GRID_UNIT_CM])

        self.logger.debug(summarized_path)
        self.logger.debug("summarized path!")
        
        # compensate for turning arc
        for i in range(1, len(summarized_path)):
            if summarized_path[i][0] == Movement.RIGHT or summarized_path[i][0] == Movement.LEFT:
                if summarized_path[i - 1][0] == Movement.FORWARD:
                    summarized_path[i - 1][1] -= self.TURN_ARC_RADIUS_CM
                    self.logger.debug("reduced length to %s", summarized_path[i - 1][1])
                elif summarized_path[i - 1][0] == Movement.REVERSE:
                    summarized_path[i - 1][1] += self.TURN_ARC_RADIUS_CM

                if i >= len(summarized_path) - 1:
                    continue
                if summarized_path[i + 1][0] == Movement.FORWARD:
                    summarized_path[i + 1][1] -= self.TURN_ARC_RADIUS_CM
                elif summarized_path[i + 1][0] == Movement.REVERSE:
                    summarized_path[i + 1][1] += self.TURN_ARC_RADIUS_CM
        """
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

    def dispatch(self, cmd_path):
        self.logger.debug("Start Dispatch")
        self.logger.debug("dispatching path")
        for cmd in cmd_path:
            while self.moving:
                sleep(1)
            # print(cmd[0])
            # print(*cmd[1])
            # if cmd[0] != 'F':
            #     print(" | ")
            #     print(" V ")
            self.logger.debug(*cmd[1])
            if isinstance(cmd[0],str):
                sleep(0.5)#Take Image and send to rpi/pc
            else: 
                self.moving = True
                cmd[0](self.robot, *cmd[1])
                #if(self.robot.poll_is_moving):# If robot not moving
                if(1):
                    self.moving = False
        self.logger.debug("dispatched path")
        return None
