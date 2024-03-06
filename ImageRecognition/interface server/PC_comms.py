'''
To be run on PC. PC will act as socket client to RPI for communications
'''

import socket
import time
from setup_logger import logger

RETRY_LIMIT = 10

class Communication:
    def __init__(self, IP, PORT):
        self.ipv4: str = IP 
        self.port: int = PORT  
        
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
                return self.msg

            logger.debug(
                f"[ALGO RCV] Client is waiting for data from server but received: '{self.msg}'. Sleeping for 1 second..."
            )
            time.sleep(1)
            if not self.socket:
                break
            
    def send_message(self, message: str) -> None:
        """Sends string data to the RPi

        Args:
            message (str): the unencoded raw string to send to the RPi
        """
        server_ipv4, server_port = self.socket.getpeername()
        logger.debug(
            f"[ALGO SEND] Client is sending '{message}' to server at {server_ipv4}:{server_port}"
        )
        self.socket.send(str(message).encode(self.msg_format))

'''
Below is used to test the connections written in this .py file
Usage: See RPI_comms for use
'''

if __name__ == '__main__':
    c = Communication('192.168.22.22', 5000)
    message = ''
    try:
        c.connect()
        
        while True:
            direction = c.listen_to_rpi()
            time.sleep(1)
            if direction == "A-PC":
                direction = ''
                print("Listening to RPI...")
                while not message.lower() == "bye":
                    message = c.listen_to_rpi()
                message = ''
            elif direction == "PC-A":
                direction = ''
                print("Type something to send to RPI")
                while not message.lower() == "bye":
                    message = input()
                    c.send_message(message)
                message = ''
            elif direction == "exit":
                break
    except:
        c.disconnect()
    c.disconnect()