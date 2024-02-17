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
from Constants import Movement


class Translator:
    GRID_UNIT_CM = 10
    TURN_ARC_RADIUS_CM = 19
    path: List[Any] = []
    robot = RobotController("COM30", 115200)

    def __init__(self):
        pass

    def add_path(self, path: List[Movement]):
        print("adding path", path)
        for movement in path:
            if movement in [Movement.FORWARD, Movement.REVERSE, Movement.LEFT, Movement.RIGHT]:
                self.path.append(movement)

    def translate(self):
        print("translating path")
        if len(self.path) < 2:
            return []
        cmd_path: List[Tuple[Callable, List[Any]]] = []

        summarized_path: List[List[Any]] = []

        # shorten the path by combining consecutive straight movements
        for i in range(0, len(self.path)):
            if i == 0:
                summarized_path.append([self.path[i], self.GRID_UNIT_CM])
            elif self.path[i] == self.path[i - 1] and len(summarized_path) > 0:
                summarized_path[-1][1] += self.GRID_UNIT_CM

            else:
                summarized_path.append([self.path[i], self.GRID_UNIT_CM])

        print(summarized_path)
        print("summarized path!")

        # compensate for turning arc
        for i in range(1, len(summarized_path)):
            if summarized_path[i][0] == Movement.RIGHT or summarized_path[i][0] == Movement.LEFT:
                if summarized_path[i - 1][0] == Movement.FORWARD:
                    summarized_path[i - 1][1] -= self.TURN_ARC_RADIUS_CM
                    print("reduced length to ", summarized_path[i - 1][1])
                elif summarized_path[i - 1][0] == Movement.REVERSE:
                    summarized_path[i - 1][1] += self.TURN_ARC_RADIUS_CM

                if i >= len(summarized_path) - 1:
                    continue
                if summarized_path[i + 1][0] == Movement.FORWARD:
                    summarized_path[i + 1][1] -= self.TURN_ARC_RADIUS_CM
                elif summarized_path[i + 1][0] == Movement.REVERSE:
                    summarized_path[i + 1][1] += self.TURN_ARC_RADIUS_CM



        for i in range(len(summarized_path)):
            if summarized_path[i][0] == Movement.FORWARD:
                if summarized_path[i][1] > 0:
                    cmd_path.append((RobotController.move_forward, [summarized_path[i][1]]))
                elif summarized_path[i][1] < 0:
                    cmd_path.append((RobotController.move_backward, [abs(summarized_path[i][1])]))
            elif summarized_path[i][0] == Movement.REVERSE:
                if summarized_path[i][1] > 0:
                    cmd_path.append((RobotController.move_backward, [summarized_path[i][1]]))
                elif summarized_path[i][1] < 0:
                    cmd_path.append((RobotController.move_forward, [abs(summarized_path[i][1])]))
            elif summarized_path[i][0] == Movement.LEFT:
                cmd_path.append((RobotController.turn_left, [90, 1]))
            elif summarized_path[i][0] == Movement.RIGHT:
                cmd_path.append((RobotController.turn_right, [90, 1]))

        print(cmd_path)
        return cmd_path

    def dispatch(self, cmd_path):

        print("dispatching path")
        for cmd in cmd_path:
            print(*cmd[1])
            cmd[0](self.robot, *cmd[1])
        print("dispatched path")
        return True
