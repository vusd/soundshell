# this script is for testing the HC-SR501 Proximity sensor
# it is a binary sensor which returns 1 when there is someone present
# and 0 when there is no one around.
import RPi.GPIO as GPIO
from time import sleep
# from aiy.audio import say


if __name__ == "__main__":
    IR_port = 26
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(IR_port, GPIO.IN)
    # say("initalizing system")
    while True:
        val = GPIO.input(IR_port)
        print(val)
        sleep(0.25)




