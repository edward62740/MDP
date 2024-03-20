'''
[WIP] supposed to update android on current position when moving 
'''


from Connection.RPI_comms import RPI_connection

STEP = 10

class MovementUpdate:
    def __init__(self, rpi: RPI_connection = None):
        self.x = 2
        self.y = 2
        self.d = 'N'
        self.rpi  = rpi
        self.update_movement()
    
    def update_movement(self):
        self.rpi.android_send(f"UPDATE,{self.x},{self.y},{self.d}") if self.rpi is not None else print(f"UPDATE,{self.x},{self.y},{self.d}")
        
    def F(self, dist: int):
        '''
        call this function when robot is gonna move forward
        '''
        if(dist == 0):
            return

        for i in range(dist, 0, -STEP):
            if  ('N' == self.d):
                self.x += 1
            elif('S' == self.d):
                self.x -= 1
            elif('E' == self.d):
                self.y += 1
            elif('W' == self.d):
                self.y -= 1
        self.update_movement()
        
    def B(self, dist: int):
        '''
        call this function when robot is gonna move backwards
        '''
        if(dist == 0):
            return

        for i in range(dist, 0, -STEP):
            if  ('N' == self.d):
                self.x -= 1
            elif('S' == self.d):
                self.x += 1
            elif('E' == self.d):
                self.y -= 1
            elif('W' == self.d):
                self.y += 1
        self.update_movement()
            
    def L(self, direction: bool):
        '''
        call this function when robot is gonna move left. direction indicates turn forwards (True) or turn backwards (False)
        '''
        if  ('N' == self.d):
            if direction:
                self.d = 'W' 
                self.x -= 2
                self.y += 2
            else:
                self.d = 'E'
                self.x -= 2
                self.y -= 2
        elif('S' == self.d):
            if direction:
                self.d = 'E' 
                self.x += 2
                self.y -= 2
            else:
                self.d = 'W'
                self.x += 2
                self.y += 2
        elif('E' == self.d):
            if direction:
                self.d = 'N' 
                self.x += 2
                self.y += 2
            else:
                self.d = 'S'
                self.x -= 2
                self.y += 2
        elif('W' == self.d):
            if direction:
                self.d = 'S' 
                self.x -= 2
                self.y -= 2
            else:
                self.d = 'N'
                self.x += 2
                self.y -= 2
        self.update_movement()
                
    def R(self, direction: bool):
        '''
        call this function when robot is gonna move right. direction indicates turn forwards (True) or turn backwards (False)
        '''
        if  ('N' == self.d):
            if direction:
                self.d = 'E' 
                self.x += 2
                self.y += 2
            else:
                self.d = 'W'
                self.x += 2
                self.y -= 2
        elif('S' == self.d):
            if direction:
                self.d = 'W'
                self.x -= 2
                self.y -= 2
            else:
                self.d = 'E'
                self.x -= 2
                self.y += 2
        elif('E' == self.d):
            if direction:
                self.d = 'S' 
                self.x += 2
                self.y -= 2
            else:
                self.d = 'N'
                self.x -= 2
                self.y -= 2
        elif('W' == self.d):
            if direction:
                self.d = 'N' 
                self.x -= 2
                self.y += 2
            else:
                self.d = 'S'
                self.x += 2
                self.y += 2
        self.update_movement()
                
if __name__ == '__main__':
    m = MovementUpdate()
    m.F(180)
    m.R(True)
    m.R(False)
    m.L(True)
    m.B(40)
