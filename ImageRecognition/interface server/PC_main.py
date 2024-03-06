'''
[WIP] To host flask server and act as socket client atst 
'''
from multiprocessing import Process
import flask_server
from PC_comms import Communication

def PC_communications(IP, PORT):
    pc = Communication(IP, PORT)
    pc.connect()
    x = input()
    pc.send_message("BEGIN")
    
if __name__ == '__main__':
    p1 = Process(target=flask_server.start_server, args=('0.0.0.0',8080,False))
    p2 = Process(target=PC_communications, args=('192.168.22.22', 5000))
    p1.start()
    p2.start()
    
    