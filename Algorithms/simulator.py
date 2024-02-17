import time
import tkinter.ttk as ttk
from bz2 import compress
from math import sqrt
from tkinter import *
from tkinter import scrolledtext
from typing import Tuple

import Configs
from comms import Communication
from Constants import *
from map import *
from Car import Car
from setup_logger import logger
from stm32_api.robot_controller import RobotController
from translator import Translator


class Simulator:
    real_x = 15
    real_y = 185
    real_dir = 0
    last_str = Movement.STOP

    def __init__(self):
        self.simulated_robot = True
        self.root = Tk()
        self.root.title("MDP Simulation")
        self.root.resizable(True, True)
        self.job = None
        self.map = Map()
        self.robot = Car(self)
        self.robot_n = []
        self.robot_e = []
        self.robot_s = []
        self.robot_w = []
        self.robot_temp_movement = []
        self.robot_movement = []
        self.movement_to_rpi = (
            []
        )  # movement_to_rpi[i] = list of "wasd" actions to take to move the i'th obstacle
        self.goal_pairs = []
        self.temp_pairs = []
        self.obstacles = []
        self.communicate = Communication()
        for i in range(3):
            self.robot_n.append([])
            self.robot_e.append([])
            self.robot_s.append([])
            self.robot_w.append([])
            for j in range(3):
                self.robot_n[i].append(config.robot_grid[Direction.NORTH][i][j])
                self.robot_e[i].append(config.robot_grid[Direction.EAST][i][j])
                self.robot_s[i].append(config.robot_grid[Direction.SOUTH][i][j])
                self.robot_w[i].append(config.robot_grid[Direction.WEST][i][j])
        t = Toplevel(self.root)
        t.title("Control Panel")
        t.geometry("+610+0")
        t.resizable(False, False)

        self.canvas = Canvas(
            self.root,
            width=40 * config.map_size["width"],
            height=40 * config.map_size["height"],
        )
        self.canvas.pack()

        self.control_panel = ttk.Frame(t, padding=(10, 10))
        self.control_panel.grid(row=0, column=1, sticky="snew")
        control_pane_window = ttk.Panedwindow(self.control_panel, orient=VERTICAL)
        control_pane_window.grid(column=0, row=0, sticky=(N, S, E, W))
        parameter_pane = ttk.Frame(control_pane_window)
        action_pane = ttk.Frame(control_pane_window)
        parameter_pane.grid(column=0, row=0, sticky=(N, S, E, W))
        action_pane.grid(column=0, row=1, pady=(10, 0), sticky=(N, S, E, W))

        self.text_area = scrolledtext.ScrolledText(
            control_pane_window, wrap=WORD, width=35, height=10
        )
        self.text_area.grid(row=2, column=0, pady=(20, 10))

        hamiltonian_path_button = ttk.Button(
            action_pane,
            text="Hamiltonian Path Computation",
            command=self.hamiltonian_path,
            width=30,
        )
        hamiltonian_path_button.grid(column=0, row=0, sticky="ew")

        fastest_path_button = ttk.Button(
            action_pane, text="Fastest Path", command=self.findFP
        )
        fastest_path_button.grid(column=0, row=1, sticky="ew")

        fastest_car_button = ttk.Button(
            action_pane, text="Fastest Car", command=self.findFC
        )
        fastest_car_button.grid(column=0, row=2, sticky="ew")

        reset_button = ttk.Button(action_pane, text="Reset", command=self.reset)
        reset_button.grid(column=0, row=3, sticky="ew")
        create_map_button = ttk.Button(
            action_pane, text="Create Map", command=self.android_map_formation
        )

        create_map_button.grid(column=0, row=4, sticky="ew")
        connect_button = ttk.Button(
            action_pane,
            text="Connect to RPI",
            command=self.communicate.connect,
            width=30,
        )
        connect_button.grid(column=0, row=5, sticky="ew")
        disconnect_button = ttk.Button(
            action_pane,
            text="Disconnect to RPI",
            command=self.communicate.disconnect,
            width=30,
        )
        disconnect_button.grid(column=0, row=6, sticky="ew")
        self.control_panel.columnconfigure(0, weight=1)
        self.control_panel.rowconfigure(0, weight=1)
        self.update_map(full=True)
        self.root.mainloop()

    def android_map_formation(self):
        self.obstacles = self.communicate.get_obstacles()
        self.map.create_map(self.obstacles)
        self.reset()
        self.robot.fastestPath(map_sim)

        movement_command = {
            Movement.FORWARD: self.robot.move,
            Movement.REVERSE: self.robot.reverse,
            Movement.LEFT: self.robot.left,
            Movement.RIGHT: self.robot.right,
        }

        # Reset the robot position first
        self.robot.reset()

        # Send the movements back to the client
        for i, movement_to_obstacle in enumerate(self.movement_to_rpi):  ### TODO Edit Movement Code for to fit
            logger.debug(
                f"Sending movement (one by one) towards obstacle {i} - {[movement.value for movement in movement_to_obstacle]}"
            )

            movement_to_obstacle = self.compress_movements(movement_to_obstacle)

            for movement, count in movement_to_obstacle:

                if movement in [Movement.FORWARD, Movement.REVERSE]:
                    _direction, _count = movement.value[0], str(count * 10).zfill(3)
                    self.send_movement_to_stm(
                        f"{_direction}{_count}", True
                    )  # ACK required

                    for _ in range(count):
                        movement_command[movement]()  # Move in Stim

                if movement in [Movement.LEFT, Movement.RIGHT]:
                    for _ in range(count):
                        self.send_movement_to_stm(movement, True)  # ACK required
                        movement_command[movement]()

                # Send STOP (x), followed by image ID (IMG,<id>)
                if movement in [Movement.STOP]:
                    self.send_movement_to_stm(movement, False)  # ACK NOT required
                    self.send_image_id_to_rpi(i)  # ACK NOT required

                # Update Android with robot's current coordinates ONLY if it moved
                if movement != Movement.STOP:
                    self.send_live_location_to_android()  # ACK NOT required

        # Reset the robot so it moves corrctly in the ALgo UI
        # Check the obstacle list before displaying movement
        self.robot.reset()

        # Somehow the FIRST movement of the robot gets "eaten up" - compensate for it
        movement_command[self.movement_to_rpi[0][0]]()

    def compress_movements(self, movements: List[str]) -> List[Tuple[Movement, int]]:
        """Compress the movements into a list of (Movement, count)

        Input  - [Movement.FORWARD, Movement.FORWARD, Movement.LEFT]
        Output - [(Movement.FORWARD, 2), (Movement.LEFT, 1)]

        Args:
            movements (List[str]): The movements to be sent to the STM

        Returns:
            List[Tuple[Movement, int]]: The compressed movements
        """
        if not movements:
            return []

        current, count = movements[0], 1
        compressed_movements = []

        for movement in movements[1:]:
            if movement == current:
                count += 1
            else:
                compressed_movements.append((current, count))
                current, count = movement, 1

        compressed_movements += [(current, count)]
        logger.debug(f"Before compression: {movements}")
        logger.debug(f"After compression: {compressed_movements}")
        return compressed_movements

    def send_movement_to_stm(self, movement: Movement, require_ack: bool) -> bool:
        while True:
            if isinstance(movement, Movement):
                movement = movement.value

            logger.debug(
                f"[ALGO --> STM] Sending movement='{movement}' - require_ack = {require_ack}"
            )
            self.communicate.communicate(movement, listen=require_ack)

            if not require_ack:
                break

            # stop sending the same movement if STM acknowledges
            if self.communicate.msg == Message.ACK.value:
                logger.debug(f"[STM --> ALGO] Received ACK for movement='{movement}'")
                self.communicate.msg = ""
                break
            else:
                logger.debug(
                    f"[STM --> ALGO] Missing ACK for movement='{movement}'. Sleeping and retrying in 1 second..."
                )
                time.sleep(1)

        return True

    def send_live_location_to_android(self) -> bool:
        bearing_direction = {
            Bearing.NORTH: Direction.NORTH,
            Bearing.EAST: Direction.EAST,
            Bearing.SOUTH: Direction.SOUTH,
            Bearing.WEST: Direction.WEST,
        }

        # (19 - y) to convert from arena's representation which treats bottom-left as (0,0)
        # to our representation which treats top-left as (0, 0)
        x, y = self.robot.x, 19 - self.robot.y
        direction = bearing_direction[self.robot.bearing].value
        live_location = f"ROBOT,{x},{y},{direction}"
        logger.debug(
            f"[ALGO --> AND] Sending live_location='{live_location}' - require_ack=False"
        )
        self.communicate.communicate(live_location, listen=False)
        return True

    def send_image_id_to_rpi(self, i: int) -> bool:
        x, y = self.temp_pairs[i]

        for obstacle in self.obstacles:
            if obstacle.x == x and obstacle.y == y:
                image_id = f"IMG,{obstacle.id}"
                logger.debug(
                    f"[ALGO --> AND] Sending image_id='{image_id}' - require_ack=False"
                )
                self.communicate.communicate(image_id, listen=False)
                return True

        logger.error(f"No image ID was found for i={i}")
        return False

    def findFP(self):
        self.robot.fastestPath(map_sim)

    def findFC(self):
        self.robot.FastCar()

    def hamiltonian_path(self):
        self.robot.hamiltonian_path_search(map_sim, self.goal_pairs)

    def put_robot(self, x, y, bearing):
        if bearing == Bearing.NORTH:
            front_coor = (x * 40 + 15, y * 40 - 10, x * 40 + 25, y * 40)
        elif bearing == Bearing.NORTH_EAST:
            front_coor = (x * 40 + 35, y * 40 - 5, x * 40 + 45, y * 40 + 5)
        elif bearing == Bearing.EAST:
            front_coor = (x * 40 + 40, y * 40 + 10, x * 40 + 50, y * 40 + 20)
        elif bearing == Bearing.SOUTH_EAST:
            front_coor = (x * 40 + 35, y * 40 + 35, x * 40 + 45, y * 40 + 45)
        elif bearing == Bearing.SOUTH:
            front_coor = (x * 40 + 15, y * 40 + 40, x * 40 + 25, y * 40 + 50)
        elif bearing == Bearing.SOUTH_WEST:
            front_coor = (x * 40 - 5, y * 40 + 35, x * 40 + 5, y * 40 + 45)
        elif bearing == Bearing.WEST:
            front_coor = (x * 40 - 10, y * 40 + 10, x * 40, y * 40 + 20)
        else:
            front_coor = (x * 40 - 5, y * 40 - 5, x * 40 + 5, y * 40 + 5)

        try:
            self.canvas.delete(self.robot_body)
            self.canvas.delete(self.robot_header)
        except:
            pass

        self.robot_body = self.canvas.create_rectangle(
            x * 40 - 20,
            y * 40 - 20,
            x * 40 + 60,
            y * 40 + 60,
            fill="maroon",
            outline="",
        )
        self.robot_header = self.canvas.create_rectangle(
            front_coor[0],
            front_coor[1],
            front_coor[2],
            front_coor[3],
            fill="white",
            outline="",
        )

    def update_cell(self, x, y):
        def wall_radius(wall, wall_c):
            for i in range(3):
                for j in range(3):
                    if not (
                            x - 1 + j < 0
                            or x + j > config.map_size["width"]
                            or y - 1 + i < 0
                            or y - 1 + i >= config.map_size["height"]
                    ):
                        self.canvas.itemconfig(
                            config.map_cells_1[y - 1 + i][x - 1 + j], fill=wall_c
                        )
                        if not map_sim[y - 1 + i][x - 1 + j] in [
                            10,
                            11,
                            12,
                            13,
                        ]:  # Skip the obstacle itself to prevent changes
                            # Update surrounding wall near the obstacle (3x3)
                            map_sim[y - 1 + i][x - 1 + j] = wall

        if map_sim[y][x] in [10, 11, 12, 13]:
            if [x, y] not in self.temp_pairs:
                self.temp_pairs.append([x, y])
        elif map_sim[y][x] == 2:
            if [x, y] in self.temp_pairs:
                self.temp_pairs.remove([x, y])

        direction = ""
        # Start box
        if (17 <= y <= 19) and (0 <= x <= 2):
            color = "lightblue"
        elif map_sim[y][x] in [0, 2]:
            color = "gray88"
            self.canvas.itemconfig(config.map_cells_2[y][x], text="")
        elif map_sim[y][x] == 10:
            direction = "^"
            color = "palevioletred"
        elif map_sim[y][x] == 11:
            direction = ">"
            color = "wheat"
        elif map_sim[y][x] == 12:
            direction = "v"
            color = "darkseagreen"
        elif map_sim[y][x] == 13:
            direction = "<"
            color = "lightsteelblue"
        else:
            color = "thistle"

        if not config.map_cells_1[y][x]:
            config.map_cells_1[y][x] = self.canvas.create_rectangle(
                x * 40, y * 40, x * 40 + 40, y * 40 + 40, fill=color
            )
            config.map_cells_2[y][x] = self.canvas.create_text(
                x * 40 + 20, y * 40 + 20, text=direction, fill="black", font="bold"
            )
            self.canvas.bind("<ButtonPress-1>", self.on_click)
        else:
            if direction in ["^", "v", ">", "<"]:
                wall_radius(1, "thistle")
                self.canvas.itemconfig(
                    config.map_cells_2[y][x], text=direction, fill="black", font="bold"
                )
            elif map_sim[y][x] == 2:
                wall_radius(0, "gray88")
            self.text_area.delete("0.0", END)
            self.text_area.insert("end", "Goals:\n" + str(self.temp_pairs), "\n")
            self.canvas.itemconfig(config.map_cells_1[y][x], fill=color)

    def update_goal_pairs(self):
        for i in self.temp_pairs:
            if map_sim[i[1]][i[0]] == 10:
                self.goal_pairs.append([i[0], i[1] - Distance.IMAGE_CAPTURE.value, 12])
            elif map_sim[i[1]][i[0]] == 11:
                self.goal_pairs.append([i[0] + Distance.IMAGE_CAPTURE.value, i[1], 13])
            elif map_sim[i[1]][i[0]] == 12:
                self.goal_pairs.append([i[0], i[1] + Distance.IMAGE_CAPTURE.value, 10])
            else:
                self.goal_pairs.append([i[0] - Distance.IMAGE_CAPTURE.value, i[1], 11])

        # TODO - let's ignore goal pairs that are OOB
        valid_goal_pairs = []
        valid_bearings = [10, 11, 12, 13]

        for x, y, bearing in self.goal_pairs:
            x, y, bearing = int(x), int(y), int(bearing)

            if 0 <= x <= 19 and 0 <= y <= 19 and bearing in valid_bearings:
                valid_goal_pairs.append([x, y, bearing])
            else:
                if not (0 <= x <= 19):
                    logger.error(f"Goal pair {(x, y, bearing)} has invalid x={x}")
                if not (0 <= y <= 19):
                    logger.error(f"Goal pair {(x, y, bearing)} has invalid y={y}")
                if bearing not in valid_bearings:
                    logger.error(
                        f"Goal pair {(x, y, bearing)} has invalid bearing={bearing}"
                    )

                logger.error(f"Goal pair {(x, y, bearing)} will be IGNORED\n")

        self.goal_pairs = valid_goal_pairs

    def on_click(self, event):
        x = event.x // 40
        y = event.y // 40

        if map_sim[y][x] == 0:
            map_sim[y][x] = 10  # North
        elif map_sim[y][x] == 10:
            map_sim[y][x] = 11  # East
        elif map_sim[y][x] == 11:
            map_sim[y][x] = 12  # South
        elif map_sim[y][x] == 12:
            map_sim[y][x] = 13  # West
        else:
            map_sim[y][x] = 2  # Reset to 0 later

        self.update_cell(x, y)
        self.goal_pairs = []
        self.update_goal_pairs()

    def update_map(self, radius: int = 2, full: bool = False) -> None:
        """Updates the map either completely, or in the vicinity of the robot

        Args:
            radius (int, optional): All squares in the bounding box with top-left corner as (x - radius, y - radius) and bottom-right corner
            as (x + radius, y + radius) will be updated, where (x, y) is the current coordinate of the robot. Defaults to 2.
            full (bool, optional): If provided and set to True, the entire map will be updated, regardless of whether or not radius is provided. Defaults to False.
        """
        if full:
            y_range = range(config.map_size["height"])
            x_range = range(config.map_size["width"])
        else:
            y_range = range(
                max(0, self.robot.y - radius),
                min(self.robot.y + radius, config.map_size["height"] - 1) + 1,
            )
            x_range = range(
                max(0, self.robot.x - radius),
                min(self.robot.x + radius, config.map_size["width"] - 1) + 1,
            )

        for y in y_range:
            for x in x_range:
                try:
                    self.update_cell(x, y)
                except IndexError:
                    pass

        self.update_goal_pairs()
        self.text_area.delete("0.0", END)
        self.text_area.insert("end", "Goals:\n" + str(self.temp_pairs), "\n")
        self.put_robot(self.robot.x, self.robot.y, self.robot.bearing)

    def reset(self):
        if self.job:
            self.root.after_cancel(self.job)
        self.robot_movement = []
        self.goal_pairs = []
        self.temp_pairs = []
        self.movement_to_rpi = []
        self.robot.reset()
        self.map.reset()
        self.update_map(full=True)

    def get_obstacle_id(self, x: int, y: int, direction: int) -> int:
        """Returns the obstacle ID of the obstacle at the given coordinate and bearing

        Args:
            x (int): The x coordinate of the obstacle
            y (int): The y coordinate of the obstacle
            direction (int): The direction of the obstacle

        Returns:
            int: The obstacle ID of the obstacle
        """
        for obstacle in self.obstacles:
            if obstacle.x == x and obstacle.y == y and obstacle.direction == direction:
                return obstacle.id

        raise ValueError(
            f"No obstacle found at the given coordinate and direction of ({x}, {y}, {direction})"
        )

    def draw_cmd_path(self, cmd_path):

        for command, args in cmd_path:
            print("exe cmd: ", command, args)

            if command == RobotController.move_forward:
                distance = args[0]
                self.last_str = Movement.FORWARD

                new_x, new_y = self.calculate_new_position(self.real_x, self.real_y, self.real_dir, distance)
                canvas_x, canvas_y = self.robot_to_canvas(self.real_x, self.real_y)
                canvas_new_x, canvas_new_y = self.robot_to_canvas(new_x, new_y)

                self.canvas.create_line(canvas_x, canvas_y, canvas_new_x, canvas_new_y, fill="green", width=5)

                self.update_map(full=True)
                self.real_x, self.real_y = new_x, new_y

            elif command == RobotController.move_backward:
                distance = args[0]
                self.last_str = Movement.REVERSE
                new_x, new_y = self.calculate_new_position(self.real_x, self.real_y, self.real_dir, -distance)
                canvas_x, canvas_y = self.robot_to_canvas(self.real_x, self.real_y)
                canvas_new_x, canvas_new_y = self.robot_to_canvas(new_x, new_y)
                self.canvas.create_line(canvas_x, canvas_y, canvas_new_x, canvas_new_y, fill="red", dash=(2, 4),
                                        width=5)

                self.update_map(full=True)
                self.real_x, self.real_y = new_x, new_y
            elif command == RobotController.turn_left:

                # Calculate start and end points for the arc
                tmp_x, tmp_y = self.real_x, self.real_y
                tmp_dir = self.real_dir
                self.real_x, self.real_y = self.calculate_new_position(self.real_x, self.real_y, self.real_dir, 19)
                canvas_mid_x, canvas_mid_y = self.robot_to_canvas(
                    *self.calculate_turn_mid_pos(self.real_x, self.real_y, tmp_dir, 19, False))
                self.real_dir = (self.real_dir - 90) % 360  # 90 degrees to the right
                self.real_x, self.real_y = self.calculate_new_position(self.real_x, self.real_y, self.real_dir, 19)
                canvas_x, canvas_y = self.robot_to_canvas(self.real_x, self.real_y)
                canvas_new_x, canvas_new_y = self.robot_to_canvas(tmp_x, tmp_y)

                # self.canvas.create_arc(canvas_x, canvas_y, canvas_new_x, canvas_new_y, start=(self.real_dir + 90) % 360, extent=90, style='arc', outline='blue', width=5)
                self.canvas.create_line([canvas_x, canvas_y, canvas_mid_x, canvas_mid_y, canvas_new_x, canvas_new_y],
                                        fill="yellow", width=5, smooth=True)



            elif command == RobotController.turn_right:
                tmp_x, tmp_y = self.real_x, self.real_y
                tmp_dir = self.real_dir
                self.real_x, self.real_y = self.calculate_new_position(self.real_x, self.real_y, self.real_dir, 19)
                canvas_mid_x, canvas_mid_y = self.robot_to_canvas(
                    *self.calculate_turn_mid_pos(self.real_x, self.real_y, tmp_dir, 19, False))
                self.real_dir = (self.real_dir + 90) % 360  # 90 degrees to the right
                self.real_x, self.real_y = self.calculate_new_position(self.real_x, self.real_y, self.real_dir, 19)
                canvas_x, canvas_y = self.robot_to_canvas(self.real_x, self.real_y)
                canvas_new_x, canvas_new_y = self.robot_to_canvas(tmp_x, tmp_y)


                self.canvas.create_line([canvas_x, canvas_y, canvas_mid_x, canvas_mid_y, canvas_new_x, canvas_new_y],
                                        fill="blue", width=5, smooth=True)
                # Update real direction

    def calculate_new_position(self, x, y, direction, distance):
        # Adjust the direction based on the robot's coordinate system
        if direction == 0:  # Moving up in the canvas
            return x, y - distance
        elif direction == 90:  # Moving right
            return x + distance, y
        elif direction == 180:  # Moving down
            return x, y + distance
        elif direction == 270:  # Moving left
            return x - distance, y
        else:
            return x, y

    def robot_to_canvas(self, x, y):
        # convert 200cm to the height of the canvas
        canvas_height = self.canvas.winfo_height()
        return x * canvas_height / 200, y * canvas_height / 200

    def calculate_turn_mid_pos(self, x, y, direction, distance, is_left):
        # given x, y and direction, where direction 0 is top and 0,0 is top left, calculate the mid point of the turn
        distance = 3
        if not is_left:
            if direction == 0:
                return x + distance, y - distance
            elif direction == 90:
                return x + distance, y + distance
            elif direction == 180:
                return x - distance, y + distance
            elif direction == 270:
                return x - distance, y - distance
        else:
            if direction == 0:
                return x - distance, y - distance
            elif direction == 90:
                return x + distance, y - distance
            elif direction == 180:
                return x + distance, y + distance
            elif direction == 270:
                return x - distance, y + distance
