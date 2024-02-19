import math
import sys
import time

from PathFinder import FastestPath
from Task2 import Task2
from map import *
from Astar import *
from setup_logger import logger
import Configs
from comms import Communication
from Constants import *
from Car import Car

from stm32_api.robot_controller import RobotController

class Contigency:
    def __init__(self):
        self.robot = Car(self)
        

    def Nav():
          """
        if(imagepos = Right Edge):
            Turn Right.
            RobotController.turn_right(90,True)
        else if image on left edge:
            Turn Left
            RobotController.turn_left(90,True)
        else if Image centered:
            Move forward until 20 cm from obstacle:
            RobotController.move_forward(20)
        else Approach()
        """
    def Approach(): #TODO FineTune
        RobotController.move_forward(30)

    def Circle(self):
        RobotController.move_backward(30)
        RobotController.turn_left(90,True)
        RobotController.turn_right(180,True)

    def NoImage():

        RobotController.move_backward(20)
        #GetImage, if Image: Navi
        sides = 1
        RobotController.turn_right(90,True)
        #Get Image
        RobotController.turn_right(90,True) #If still no Image

    def CrashAlert(curr_pos,goal_pos):
        RobotController.move_backward(20)
        RobotController.turn_left(90,True)
        RobotController.turn_Right(180,True)
        return curr_pos


#If no image:
        Contigency.NoImage()
#else if Image Present:
        Contigency.Nav()
        #get Image
        Image = 0 #Replace with get fn for imageID
        while(Image == 99):
            Contigency.Circle()