import logging
from time import sleep

import asyncio
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
from Connection.RPI_comms import RPI_connection

def obst_cb():
    pass

class Translator:
    GRID_UNIT_CM = 10
    TURN_ARC_RADIUS_CM = 20

    def __init__(self, robot_port: str, robot_baudrate: int, rpi: RPI_connection = None):
        self.path: List[Any] = []
        self.robot = RobotController(robot_port, robot_baudrate)
        self.robot.set_threshold_stop_distance_right(1)
        self.robot.set_threshold_stop_distance_left(1) # remove in real run
        self.dispatcher = BlockingDispatcher(self.robot, 5, 2, u_if=_IO_Attr_Type.PHYSICAL)
        self.logger = logging.getLogger(__name__)
        self.rpi = rpi
        self.moving = False
        self.camera = None

    def add_path(self, path: List[Command]):
        #self.logger.debug("adding path %s", path)
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
                cmd_path.append(f'Scan,{tempCmd.obj_index}')

        cmd_path.append("Fin")
        self.logger.debug(cmd_path)
        return cmd_path

    def obstacle_callback(self, *args):
        print("Obstacle detected!")

    async def dispatch(self, cmd_path):
        self.logger.debug("Start Dispatch")
        self.logger.debug("dispatching path")
        phi = await self.dispatcher.dispatchB(RobotController.get_yaw, [], obst_cb)
        cur_offset = 0
        ctr = 0
        for cmd in cmd_path:
            if isinstance(cmd[0],str):
                if ('Scan' in cmd):
                    obj_index = cmd.split(',')[1]
                    
                    if self.camera is None:
                        self.camera = photographer.start_camera()
                    photographer.fire_and_forget(self.camera, self.rpi, obj_index)

            else: 
                self.moving = True
                await self.dispatcher.dispatchB(cmd[0], cmd[1], self.obstacle_callback)
                await asyncio.sleep(0.45)
                    
                while(self.robot.poll_is_moving()):# If robot not moving
                    await asyncio.sleep(0.01)
                    
                ctr += 1
                if id(cmd[0]) == id(RobotController.turn_left):
                    cur_offset += 90
                    if cur_offset > 180:
                        cur_offset = -180 + (cur_offset % 180)
                elif id(cmd[0]) == id(RobotController.turn_right):
                    cur_offset -= 90
                    if cur_offset < -180:
                        cur_offset %= 180

                if id(cmd[0]) == id(RobotController.move_forward):
                    phi_cur = await self.dispatcher.dispatchB(RobotController.get_yaw, [], obst_cb)
                    e, sgn = await turn_error_minimization(phi, True, phi_cur, cur_offset)
                    print(e)
                    if e < 25:
                        await self.dispatcher.dispatchB(RobotController.turn_left if sgn else RobotController.turn_right, [math.floor(e), 1], self.obstacle_callback)
                        while(self.robot.poll_is_moving()):# If robot not moving
                            await asyncio.sleep(0.01)
                            
        self.logger.debug("dispatched path")
        photographer.combine_images()
        return None

async def turn_error_minimization(phi: float, offset_known: bool, phi_cur: float,  sgn_offset: float = 0) :
    
    if offset_known:

        if (phi + sgn_offset) >= 180:
            phi_opt = -180 + ((phi + sgn_offset) % 180)
        elif (phi + sgn_offset) < -180:
            phi_opt = (phi + sgn_offset) % 180
        else:
            phi_opt = (phi + sgn_offset)


        epsl = phi_opt - phi_cur
        if abs(epsl) <= 180:
            return abs(epsl), 1 if epsl > 0 else 0
        else:
            return 360-epsl, 1 if epsl <= 0 else 0

    else:
        epsl_vars = []
        # basically repeat the above for all k in -2..2
        _CONST_ROT_MAG = 90
        for k in (-2, 3):
            if (phi + _CONST_ROT_MAG * k) >= 180:
                phi_opt = -180 + ((phi + _CONST_ROT_MAG * k) % 180)
            elif (phi + _CONST_ROT_MAG * k) < -180:
                phi_opt = (phi + _CONST_ROT_MAG * k) % 180
            else:
                phi_opt = (phi + _CONST_ROT_MAG * k)


            epsl = phi_opt - phi_cur
            if abs(epsl) <= 180:
                epsl_vars.append([abs(epsl), 1 if epsl > 0 else 0])
            else:
                epsl_vars.append([360-epsl, 1 if epsl <= 0 else 0])
        n = 0
        for k, _ in enumerate(epsl_vars):
            if epsl_vars[k][0] < epsl_vars[n][0]:
                n = k
        return epsl_vars[n]