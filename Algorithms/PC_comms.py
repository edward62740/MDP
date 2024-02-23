import socket
import time
from typing import List, Optional

from Constants import Direction, Obstacle
from setup_logger import logger

RETRY_LIMIT = 10

class Communication:
    def __init__(self):
        self.ipv4 = "192.168.22.22" 
        self.port: int = 5000  
        
        self.socket: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # the socket object used for 2-way TCP communication with the RPi
        self.msg: str = None  # message received from the Rpi
        self.msg_format: str = "utf-8"  # message format for sending (encoding to a UTF-8 byte sequence) and receiving (decoding a UTF-8 byte sequence) data from the Rpi
        self.read_limit_bytes: int = 2048  # number of bytes to read from the socket in a single blocking socket.recv command

    def connect(self):
        TRIES = 0
        RETRY = True
        while RETRY and TRIES < RETRY_LIMIT:
            try:
                if self.socket:
                    self.socket.close()
                logger.debug(f"Connecting to the server at {self.ipv4}:{self.port}...")
                self.socket: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.socket.connect((self.ipv4, self.port))
                logger.debug(f"Successfully connected to the server at {self.ipv4}:{self.port}")
                RETRY = False
            except socket.error as e:
                logger.debug("Connection with RPI failed: " + str(e))
                if self.socket:
                    self.socket.close()
                TRIES += 1
                logger.debug(f"Retrying for the {TRIES} time...")
                time.sleep(1)
                
    def disconnect(self):
        if not (self.socket and not self.socket._closed):
            logger.warning(
                "There is no active connection with a server currently. Unable to disconnect."
            )
            return

        logger.debug(f"Disconnecting from the server at {self.ipv4}:{self.port}...")
        self.socket.shutdown(socket.SHUT_RDWR)
        self.socket.close()
        logger.debug(f"Algo client socket has been closed")

    def listen_to_rpi(self):
        logger.debug("[BLOCKING] Client listening for data from server...")

        while True:
            msg = self.socket.recv(self.read_limit_bytes).strip()

            if msg:
                self.msg = msg.decode(self.msg_format)
                logger.debug(
                    f"[ALGO RCV] Client received data from server: '{self.msg}'"
                )
                return

            logger.debug(
                f"[ALGO RCV] Client is waiting for data from server but received: '{self.msg}'. Sleeping for 1 second..."
            )
            time.sleep(1)
            if not self.socket:
                break
            
    def send_message(self, message: str) -> None:
        # NOT WRITTEN BY YEE LONG
        """Sends string data to the RPi

        Args:
            message (str): the unencoded raw string to send to the RPi
        """
        server_ipv4, server_port = self.socket.getpeername()
        logger.debug(
            f"[ALGO SEND] Client is sending '{message}' to server at {server_ipv4}:{server_port}"
        )
        self.socket.send(str(message).encode(self.msg_format))

    def get_obstacles(self) -> List[Obstacle]:
        # NOT WRITTEN BY YEE LONG
        """
        Returns the list of obstacles sent via Android.

        Sample input `data` from RPi:
        "0,1,3,N,19,10,S,1,12,13,E,11,0,W" - each obstacle is represented by a comma-separated string of index,x,y,direction

        Returns:
            List[Tuple[int, int, int, str]]: A list of obstacles, where each obstacle is in the format (index, x, y, direction)
        """
        logger.debug("Client is waiting for the server to send the obstacles list")

        while True:
            logger.debug("[BLOCKING] Client listening for data from server...")
            data = self.socket.recv(self.read_limit_bytes).strip()

            if len(data) > 0:
                data = data.decode(self.msg_format)
                logger.debug(f"Client received obstacles from server: '{data}'")
                obstacles = data.split(",")

                new_obstacles = []
                for i in range(0, len(obstacles), 4):
                    obstacle_data = obstacles[i : i + 4]
                    obstacle = self.parse_obstacle(obstacle_data)
                    if obstacle is not None:
                        new_obstacles.append(obstacle)

                logger.debug(
                    f"Client parsed obstacles from server: {new_obstacles}. Obstacle coordinates treat TOP-LEFT as (0, 0)"
                )
                return new_obstacles

            logger.warn(
                f"Server received empty data from client: '{data}'. Sleeping for 1 second..."
            )
            time.sleep(1)

    def parse_obstacle(self, obstacle_data: List[str]) -> Optional[Obstacle]:
        # NOT WRITTEN BY YEE LONG
        """
        Parses an obstacle string into an Obstacle object.

        Args:
            obstacle_data (List[str]): A list of strings representing the obstacle data.

        Returns:
            Optional[Obstacle]: The parsed Obstacle object, or None if the obstacle is invalid.
        """
        index, x, y, direction = obstacle_data

        try:
            index = int(index.strip())
            x = int(x.strip())
            y = 19 - int(y.strip())
        except ValueError:
            logger.error(
                f"Invalid obstacle '{obstacle_data}'. Index, x, or y is not a valid integer. Resend the obstacle list"
            )
            return None

        direction = direction.strip()
        direction_mapping = {
            Direction.NORTH.value: 10,
            Direction.SOUTH.value: 12,
            Direction.EAST.value: 11,
            Direction.WEST.value: 13,
        }
        direction = direction_mapping.get(direction)
        if direction is None:
            logger.error(
                f"Invalid obstacle '{obstacle_data}'. Direction is invalid. Resend the obstacle list"
            )
            return None

        if not (0 <= x <= 19 and 0 <= y <= 19):
            logger.error(
                f"Invalid obstacle '{obstacle_data}'. Coordinates are out of bounds [0, 19]. Resend the obstacle list"
            )
            return None

        return Obstacle(index, x, y, direction)


    # def communicate(self, data: str, listen=True, write=True):
    #     if write and data:
    #         self.send_message(data)
    #     if listen:
    #         self.listen_to_rpi()

'''
Below is used to test the connections written in this .py file
Usage: See RPI_comms for use
'''

if __name__ == '__main__':
    c = Communication()
    try:
        c.connect()
        
        while True:
            c.listen_to_rpi()
            if c.msg == "A-PC":
                print("Listening to RPI...")
                while not c.msg == "bye":
                    c.listen_to_rpi()
            elif c.msg == "PC-A":
                print("Type something to send to RPI")
                while not c.msg == "bye":
                    c.send_message(input())
            elif c.msg == "exit":
                break
    except:
        c.disconnect()
    c.disconnect()