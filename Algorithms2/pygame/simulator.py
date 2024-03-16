#import pygame
import time
from Map import Grid,Obstacle
from abc import ABC, abstractmethod
#from button import Button
from typing import List
from enum import Enum
from Robot.robot import Robot
#from settings import *

# start_img = pygame.image.load("Algorithms-testing/assets/Start.png").convert_alpha()
# exit_img = pygame.image.load("Algorithms-testing/assets/Exit.png").convert_alpha()
# reset_img = pygame.image.load("Algorithms-testing/assets/Reset.png").convert_alpha()


class AlgoApp(ABC):
    def __init__(self, obstacles: List[Obstacle]):
        self.grid = Grid(obstacles)
        self.robot = Robot(self.grid)
        
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
    
    def __init__(self, obstacles):
        super().__init__(obstacles)

    def init(self):
        pass

    async def execute(self):
        print("Calculating path...")
        #index_list = self.robot.brain.plan_path()
        planned_path = self.robot.brain.plan_path()
        ret = self.robot.brain.translator.translate()
        print("Planned path: ", planned_path)
        print("Translated path...  Dispatching..")
        await self.robot.brain.translator.dispatch(ret)
        
    async def execute_PC(self, path):
        print("Dispatching path computed by the PC")
        await self.robot.brain.translator.dispatch_2(self.robot.brain.translator.translate(path))
        return
   