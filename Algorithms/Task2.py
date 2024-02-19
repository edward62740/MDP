import math
import sys
import time

from Constants import *
from Astar import *
from setup_logger import logger

class Task2:
    ###########################################################################################
    def fastestCar(self):
        self.simulator.robot_movement = []
        horiz_distance = 0
        wasd_str = []
        amount = 2  # vertical distance for the first obstacle

        for rounds in range(0, 2):
            #  start = [6, 2, 11]
            if rounds > 0:
                amount = 5  # since second obstacle is bigger we move it vertically by a higher distance

            if rounds == 0:
                # first sensor reading
                # TODO: get initial sensor reading
                sensor_reading = 3
            else:
                # second sensor reading
                sensor_reading = 5
            #  self.simulator.robot_movement.append(Movement.RIGHT)

            while sensor_reading > 2:  # while distance is greater than 20 cm
                # get sensor reading
                self.simulator.robot_movement.append(Movement.FORWARD)
                self.robot_rpi_temp_movement.append(Movement.FORWARD)
                wasd_str.append("w")
                horiz_distance += 1
                sensor_reading -= 1  # measure sensor reading

            wasd_str.append("x")
            # take picture and start image recog

            if rounds > 0:
                obs = "RIGHT"  # determined by image recognition, second round
            else:
                obs = "RIGHT"

            if obs == "LEFT":
                self.simulator.robot_movement.append(Movement.LEFT)
                self.robot_rpi_temp_movement.append(Movement.LEFT)
                wasd_str.append("a")
                # move forward by vert amount
                for j in range(0, amount):
                    self.simulator.robot_movement.append(Movement.FORWARD)
                    self.robot_rpi_temp_movement.append(Movement.FORWARD)
                    wasd_str.append("w")
                # turn opposite direction
                self.simulator.robot_movement.append(Movement.RIGHT)
                self.robot_rpi_temp_movement.append(Movement.RIGHT)
                wasd_str.append("d")
            elif obs == "RIGHT":
                self.simulator.robot_movement.append(Movement.RIGHT)
                self.robot_rpi_temp_movement.append(Movement.RIGHT)
                wasd_str.append("d")
                # move forward by amount
                for Goals in range(0, amount):
                    self.simulator.robot_movement.append(Movement.FORWARD)
                    self.robot_rpi_temp_movement.append(Movement.FORWARD)
                    wasd_str.append("w")
                # turn opposite direction ##
                self.simulator.robot_movement.append(Movement.LEFT)
                self.robot_rpi_temp_movement.append(Movement.LEFT)
                wasd_str.append("a")
            ### it has now gone up above the obstacle and turned in the direction of travel ###

            # move forward by horiz amount
            for i in range(0, 5):
                self.simulator.robot_movement.append(Movement.FORWARD)
                self.robot_rpi_temp_movement.append(Movement.FORWARD)
                wasd_str.append("w")
                horiz_distance += 1
            # turn opposite direction to obs
            if obs == "LEFT":
                self.simulator.robot_movement.append(Movement.RIGHT)
                self.robot_rpi_temp_movement.append(Movement.RIGHT)
                wasd_str.append("w")
            else:
                self.simulator.robot_movement.append(Movement.LEFT)
                self.robot_rpi_temp_movement.append(Movement.LEFT)
                wasd_str.append("a")
            # move forward by amount
            # problematic
            for i in range(0, amount):
                self.simulator.robot_movement.append(Movement.FORWARD)
                self.robot_rpi_temp_movement.append(Movement.FORWARD)
                wasd_str.append("w")
            # turn same direction as obs
            # straightening
            if obs == "LEFT":
                # if rounds == 0:
                self.simulator.robot_movement.append(Movement.LEFT)
                self.robot_rpi_temp_movement.append(Movement.LEFT)
                wasd_str.append("a")
            else:
                # if rounds == 0:
                self.simulator.robot_movement.append(Movement.RIGHT)
                self.robot_rpi_temp_movement.append(Movement.RIGHT)
                wasd_str.append("d")

            ## 1 iteration finished

        # come back to carpark
        horiz_distance //= 2

        if obs == "LEFT":
            self.simulator.robot_movement.append(Movement.RIGHT)
            self.robot_rpi_temp_movement.append(Movement.RIGHT)
            wasd_str.append("d")
            for i in range(0, amount):
                self.simulator.robot_movement.append(Movement.FORWARD)
                self.robot_rpi_temp_movement.append(Movement.FORWARD)
                wasd_str.append("w")
            self.simulator.robot_movement.append(Movement.RIGHT)
            self.robot_rpi_temp_movement.append(Movement.RIGHT)
            wasd_str.append("d")
            # move back the horizontal distance
            for i in range(0, horiz_distance):
                self.simulator.robot_movement.append(Movement.FORWARD)
                self.robot_rpi_temp_movement.append(Movement.FORWARD)
                wasd_str.append("w")
        else:
            self.simulator.robot_movement.append(Movement.RIGHT)
            self.robot_rpi_temp_movement.append(Movement.RIGHT)
            wasd_str.append("d")
            for i in range(0, amount):
                self.simulator.robot_movement.append(Movement.FORWARD)
                self.robot_rpi_temp_movement.append(Movement.FORWARD)
                wasd_str.append("w")
            self.simulator.robot_movement.append(Movement.RIGHT)
            self.robot_rpi_temp_movement.append(Movement.RIGHT)
            wasd_str.append("d")
            # move back the horizontal distance
            for i in range(0, horiz_distance):
                self.simulator.robot_movement.append(Movement.FORWARD)
                self.robot_rpi_temp_movement.append(Movement.FORWARD)
                wasd_str.append("w")

        # final bring back
        # it crashes with the wall so need to subtract

        self.simulator.robot_movement.append(Movement.RIGHT)
        self.robot_rpi_temp_movement.append(Movement.RIGHT)
        wasd_str.append("d")
        for i in range(0, 3):
            self.simulator.robot_movement.append(Movement.FORWARD)
            self.robot_rpi_temp_movement.append(Movement.FORWARD)
            wasd_str.append("w")
        # final final mov
        self.simulator.robot_movement.append(Movement.LEFT)
        self.robot_rpi_temp_movement.append(Movement.LEFT)
        wasd_str.append("a")
        for i in range(0, horiz_distance):
            self.simulator.robot_movement.append(Movement.FORWARD)
            self.robot_rpi_temp_movement.append(Movement.FORWARD)
            wasd_str.append("w")

        self.displayMovement()
        print(wasd_str)  # wasd str to send to rpi

    ########################################################################################