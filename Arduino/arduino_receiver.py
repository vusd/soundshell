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
    arduino = serial.Serial(arduino_port, 57600,timeout=0.1)
    return arduino

def sendToArduino(color, brightness):
    msg = str(color) + "," + str(brightness) + '\n'
    msg = msg.encode()
    # print("msg is : ", type(msg), " ", msg)
    arduino.write(msg)

arduino = connectToArduino()
# take note that each string ends with \n this is needed for the protocol to work
# also note how there is a "b" before the start of each string this is also needed

while True:
    test_color = random.randint(0, 255)
    test_brightness = random.randint(1, 255)
    print("test color is : ", test_color, " - ", test_brightness)

    # read the arduino
    amsg = arduino.readline()[:-2]
    if b"TRIG" in amsg:
        print("Someone is detected") # print out the arduinos response (should be message)
    elif amsg:
        print(amsg)
        pass
    sendToArduino(test_color, test_brightness)
    time.sleep(1);
