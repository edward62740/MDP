from Connection.RPI_comms import RPI_connection

rpi = RPI_connection()

rpi.bluetooth_connect()
for i in range(10):
    mes = input()
    rpi.android_send(mes)

rpi.bluetooth_disconnect()
    