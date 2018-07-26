import serial
import time
import glob
import random


def connectToArduino():
    """
    This function will automatically connect to the first arduino
    connected to your Mac and will return the serial object which
    you can then operate on
    """
    arduino_port = '/dev/tty.usbmodem1411'
    # print out all serial devices connected to computer
    ports = glob.glob('/dev/tty.*')
    for port in ports:
        if "usbmodem" in port:
            print("arduino port : " + port)
            arduino_port = port
        else:
            print("port : " + port)

    # and use that variable to connect to the arduino via serial
    arduino = serial.Serial(arduino_port, 9600)
    return arduino

def sendToArduino(msg):
    msg = str(msg).encode()
    print("msg is : ", type(msg), " ", msg)
    for m in msg:
        arduino.write(m)
    arduino.write('\n')

arduino = connectToArduino()
# take note that each string ends with \n this is needed for the protocol to work
# also note how there is a "b" before the start of each string this is also needed

while True:
    test_color = random.randint(0, 255)
    print("test color is : ", test_color)
    # print (arduino.readline()) # print out the arduinos response (should be message)
    sendToArduino(test_color)
    time.sleep(0.5)
