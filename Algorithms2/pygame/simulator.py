#import pygame
import time
from Map import Grid,Obstacle
from abc import ABC, abstractmethod
#from button import Button
from typing import List
from enum import Enum
from Robot.robot import Robot
#from settings import *
from Connection.RPI_comms import RPI_connection

# start_img = pygame.image.load("Algorithms-testing/assets/Start.png").convert_alpha()
# exit_img = pygame.image.load("Algorithms-testing/assets/Exit.png").convert_alpha()
# reset_img = pygame.image.load("Algorithms-testing/assets/Reset.png").convert_alpha()


class AlgoApp(ABC):
    def __init__(self, obstacles: List[Obstacle], rpi: RPI_connection = None):
        self.grid = Grid(obstacles)
        self.robot = Robot(self.grid, rpi)
        self.rpi = rpi
        
        # self.start_button = Button(620, 250, start_img, 0.15)
        # self.reset_button = Button(640, 350, reset_img, 0.08)
        # self.exit_button = Button(650, 480, exit_img, 0.15)

    @abstractmethod
    def init(self):
        pass

    @abstractmethod
    def execute(self):
        pass
        
class AlgoMinimal(AlgoApp):
    
    #Minimal app to just calculate a path and then send the commands over.
    
    def __init__(self, obstacles, rpi: RPI_connection = None):
        super().__init__(obstacles, rpi)

    def init(self):
        pass

    async def execute(self):
        print("Calculating path...")
        planned_path = self.robot.brain.plan_path()
        ret = self.robot.brain.translator.translate()
        #print("Planned path: ", planned_path)
        print("Path has been planned. Press start on the tablet when ready...")
        if self.rpi is not None:
            while True:
                if "start" == self.rpi.android_receive():
                    break
        print("Translated path...  Dispatching..")
        await self.robot.brain.translator.dispatch(ret)
   