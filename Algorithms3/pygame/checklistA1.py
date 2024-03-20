'''
This is used to test the connections between the PC, Android, and STM32. Essentially for checklist A1
Usage:
    1. Ensure that the robot is fully connected to the STM32 and relevant sensors
    1. Run 'python3 checklistA1.py' in RPI terminal to run the connection test
    2. Connect RPI to android tablet via bluetooth (can use the S2 Terminal app)
    3. Run 'python3 PC_comms.py' in PC terminal 
    4. Connection all done. Begin testing now
'''

from Connection.RPI_comms import RPI_connection
from stm32_api.robot_controller import RobotController
from settings import PORT, BAUD

if __name__ == '__main__':
    
    rpi = RPI_connection()
    robot = RobotController(PORT, BAUD)
    DIST = 100 # cm
    ANGLE = 90 # degrees

    rpi.bluetooth_connect()
    rpi.PC_connect()

    try:
        while True:
            print("-----------------------------------------------------------------------")
            print("You are currently in the connection test function. This function allows")
            print("you to test the connection between the RPI, STM, Android, or PC")
            print("-----------------------------------------------------------------------")
            print("Enter your choice of test:")
            print("1 -- Android to PC")
            print("2 -- PC to Android")
            print("3 -- Android to STM")
            print("4 -- PC to STM")
            print("Q -- exit")
            choice = input()
            if choice == '1':
                print("Testing Android to PC communication. Type something on the tablet and the PC should show")
                rpi.PC_send("A-PC")
                while True:
                    message = rpi.android_receive()
                    print(f"Received {message}. Passing over to PC now")
                    rpi.PC_send(message)
                    if message.lower() == 'bye': 
                        message = ''
                        break
                
            elif choice == '2':
                print("Testing PC to Android communication. Type something on the PC and the tablet should show")
                rpi.PC_send("PC-A")
                while True:
                    message = rpi.PC_receive()
                    print(f"Received {message}. Passing over to android now")
                    rpi.android_send(message)
                    if message.lower() == 'bye': 
                        message = ''
                        break
                    
            elif choice == '3':
                print("Testing Android to STM communication. Type W/A/S/D on the tablet and the robot should move")
                while True:
                    move = rpi.android_receive()
                    if move == 'w' or move == 'W':
                        robot.move_forward(DIST)
                    elif move == 'a' or move == 'A':
                        robot.turn_left(ANGLE, True)
                    elif move == 's' or move == 'S':
                        robot.move_backward(DIST)
                    elif move == 'd' or move == 'D':
                        robot.turn_right(ANGLE, True)
                    elif move.lower() == 'bye':
                        move = ''
                        break
                    else:
                        break
                    
            elif choice == '4':
                print("Testing PC to STM communication. Type W/A/S/D on the PC and the robot should move")
                rpi.PC_send("PC-A")
                while True:
                    move = rpi.PC_receive()
                    if move == 'w' or move == 'W':
                        robot.move_forward(DIST)
                    elif move == 'a' or move == 'A':
                        robot.turn_left(ANGLE, True)
                    elif move == 's' or move == 'S':
                        robot.move_backward(DIST)
                    elif move == 'd' or move == 'D':
                        robot.turn_right(ANGLE, True)
                    elif move.lower() == 'bye':
                        move = ''
                        rpi.PC_send('bye')
                        break
                    else:
                        break
                
            elif choice.lower() == 'q' or choice.lower() == 'quit' or choice.lower() == 'exit':
                rpi.PC_send("exit")
                break
            else:
                print("Invalid choice")
    except:    
        rpi.bluetooth_disconnect()
        rpi.PC_disconnect()
        
    finally:
        rpi.bluetooth_disconnect()
        rpi.PC_disconnect()