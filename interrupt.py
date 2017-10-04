#!/usr/bin/python
import RPi.GPIO as GPIO
import time
import subprocess
import os

# +-----+-----+---------+------+---+---Pi 3---+---+------+---------+-----+-----+
# | BCM | wPi |   Name  | Mode | V | Physical | V | Mode | Name    | wPi | BCM |
# +-----+-----+---------+------+---+----++----+---+------+---------+-----+-----+
# |     |     |    3.3v |      |   |  1 || 2  |   |      | 5v      |     |     |
# |   2 |   8 |   SDA.1 |   IN | 1 |  3 || 4  |   |      | 5v      |     |     |
# |   3 |   9 |   SCL.1 |   IN | 1 |  5 || 6  |   |      | 0v      |     |     |
# |   4 |   7 | GPIO. 7 |   IN | 1 |  7 || 8  | 0 | IN   | TxD     | 15  | 14  |
# |     |     |      0v |      |   |  9 || 10 | 1 | IN   | RxD     | 16  | 15  |
# |  *R |   0 | GPIO. 0 |  OUT | 0 + 11 || 12 + 0 | IN   | GPIO. 1 | 1   |*T1  |
# |  *G |   2 | GPIO. 2 |  OUT | 0 + 13 || 14 +   |      | 0v      |     |*GND |
# |  *B |   3 | GPIO. 3 |  OUT | 0 + 15 || 16 + 0 | IN   | GPIO. 4 | 4   |*T2  |
# |*3,3V|     |    3.3v |      |   + 17 || 18 | 0 | IN   | GPIO. 5 | 5   | 24  |
# |  10 |  12 |    MOSI |   IN | 0 | 19 || 20 |   |      | 0v      |     |     |
# |   9 |  13 |    MISO |   IN | 0 | 21 || 22 | 0 | IN   | GPIO. 6 | 6   | 25  |
# |  11 |  14 |    SCLK |   IN | 0 | 23 || 24 | 1 | IN   | CE0     | 10  | 8   |
# |     |     |      0v |      |   | 25 || 26 | 1 | IN   | CE1     | 11  | 7   |
# |   0 |  30 |   SDA.0 |   IN | 1 | 27 || 28 | 1 | IN   | SCL.0   | 31  | 1   |
# |   5 |  21 | GPIO.21 |  OUT | 1 | 29 || 30 |   |      | 0v      |     |     |
# |   6 |  22 | GPIO.22 |  OUT | 0 | 31 || 32 | 0 | IN   | GPIO.26 | 26  | 12  |
# |  13 |  23 | GPIO.23 |  OUT | 0 | 33 || 34 |   |      | 0v      |     |     |
# |  19 |  24 | GPIO.24 |   IN | 1 | 35 || 36 | 0 | IN   | GPIO.27 | 27  | 16  |
# |  26 |  25 | GPIO.25 |   IN | 1 | 37 || 38 | 0 | IN   | GPIO.28 | 28  | 20  |
# |     |     |      0v |      |   | 39 || 40 | 0 | IN   | GPIO.29 | 29  | 21  |
# +-----+-----+---------+------+---+----++----+---+------+---------+-----+-----+
# | BCM | wPi |   Name  | Mode | V | Physical | V | Mode | Name    | wPi | BCM |
# +-----+-----+---------+------+---+---Pi 3---+---+------+---------+-----+-----+


class MotionRecorder():

    def __init__(self):
        '''
        initialize pin constants and GPIO set-up
        '''
        # GPIO pins
        self.TASTER_1 = 12
        self.TASTER_2 = 16
        self.RED_PIN = 11
        self.GREEN_PIN = 13
        self.BLUE_PIN = 15

        # use GPIO board numbers
        GPIO.setmode(GPIO.BOARD)

        # button = input
        GPIO.setup(self.TASTER_1, GPIO.IN)
        GPIO.setup(self.TASTER_2, GPIO.IN)

        # LED = output
        GPIO.setup(self.RED_PIN, GPIO.OUT)
        GPIO.setup(self.GREEN_PIN, GPIO.OUT)
        GPIO.setup(self.BLUE_PIN, GPIO.OUT)

        # define state
        self.status = "idle"
        GPIO.output(self.BLUE_PIN, GPIO.HIGH)

        # define interrupt, get rising signal, debounce pin
        GPIO.add_event_detect(
            self.TASTER_1,
            GPIO.RISING,
            callback=self.start_recording,
            bouncetime=10000
        )
        GPIO.add_event_detect(
            self.TASTER_2,
            GPIO.RISING,
            callback=self.stop_recording,
            bouncetime=10000
        )
        # USB-Sticks by UUID
        # stick[("54D3-D098", "E9B7-83A1", "F054-0EB3", "C087-0BFB")]

    def led_off(self):
        '''
        switches off the LED, RGB channels have to be switched off
        separately
        '''
        GPIO.output(self.BLUE_PIN, GPIO.LOW)
        GPIO.output(self.RED_PIN, GPIO.LOW)
        GPIO.output(self.GREEN_PIN, GPIO.LOW)

    def error(self):
        '''
        send a blinking red led signal to visualize an error
        '''
        i = 0
        self.led_off()
        for i in range(10):
            GPIO.output(self.RED_PIN, GPIO.HIGH)
            time.sleep(0.1)
            GPIO.output(self.RED_PIN, GPIO.LOW)
            time.sleep(0.1)

    def start_recording(self):
        '''
        mount flash drive and start motion
        '''
        if self.status == "idle":
            self.status = "switching"
            self.led_off()
            GPIO.output(self.RED_PIN, GPIO.HIGH)
            print("mount usb, start motion")
            subprocess.run(["sudo", "mount", "/dev/sda1", "/media/usb-video"])
            time.sleep(5)
            if not os.path.ismount("/media/usb-video"):
                self.error()
                GPIO.output(self.BLUE_PIN, GPIO.HIGH)
                self.status = "idle"
            else:
                subprocess.run(["sudo", "motion"])
                self.led_off()
                GPIO.output(self.GREEN_PIN, GPIO.HIGH)
                self.status = "recording"

    def stop_recording(self):
        '''
        stop motion and un-mount flash drives
        '''
        global status
        if self.status == "recording":
            self.status = "switching"
            self.led_off()
            GPIO.output(self.RED_PIN, GPIO.HIGH)
            print("stop motion, unmount usb")
            subprocess.run(["sudo", "killall", "-9", "motion"])
            subprocess.run(["sudo", "umount", "/media/usb-video"])
            time.sleep(5)
            self.led_off()
            GPIO.output(self.BLUE_PIN, GPIO.HIGH)
            status = "idle"


if __name__ == "__main__":
    recorder = MotionRecorder()
    print("waiting for input")
    try:
        # keep script running
        while True:
            time.sleep(0.5)

    finally:
        GPIO.cleanup()
        print("\nQuit\n")
