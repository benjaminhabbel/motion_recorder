#!/usr/bin/python
import os
import RPi.GPIO as GPIO
import time
import subprocess

#+-----+-----+---------+------+---+---Pi 3---+---+------+---------+-----+-----+
#| BCM | wPi |   Name  | Mode | V | Physical | V | Mode | Name    | wPi | BCM |
#+-----+-----+---------+------+---+----++----+---+------+---------+-----+-----+
#|     |     |    3.3v |      |   |  1 || 2  |   |      | 5v      |     |     |
#|   2 |   8 |   SDA.1 |   IN | 1 |  3 || 4  |   |      | 5v      |     |     |
#|   3 |   9 |   SCL.1 |   IN | 1 |  5 || 6  |   |      | 0v      |     |     |
#|   4 |   7 | GPIO. 7 |   IN | 1 |  7 || 8  | 0 | IN   | TxD     | 15  | 14  |
#|     |     |      0v |      |   |  9 || 10 | 1 | IN   | RxD     | 16  | 15  |
#|  *R |   0 | GPIO. 0 |  OUT | 0 + 11 || 12 + 0 | IN   | GPIO. 1 | 1   |*T1  |
#|  *G |   2 | GPIO. 2 |  OUT | 0 + 13 || 14 +   |      | 0v      |     |*GND |
#|  *B |   3 | GPIO. 3 |  OUT | 0 + 15 || 16 + 0 | IN   | GPIO. 4 | 4   |*T2  |
#|*3,3V|     |    3.3v |      |   + 17 || 18 | 0 | IN   | GPIO. 5 | 5   | 24  |
#|  10 |  12 |    MOSI |   IN | 0 | 19 || 20 |   |      | 0v      |     |     |
#|   9 |  13 |    MISO |   IN | 0 | 21 || 22 | 0 | IN   | GPIO. 6 | 6   | 25  |
#|  11 |  14 |    SCLK |   IN | 0 | 23 || 24 | 1 | IN   | CE0     | 10  | 8   |
#|     |     |      0v |      |   | 25 || 26 | 1 | IN   | CE1     | 11  | 7   |
#|   0 |  30 |   SDA.0 |   IN | 1 | 27 || 28 | 1 | IN   | SCL.0   | 31  | 1   |
#|   5 |  21 | GPIO.21 |  OUT | 1 | 29 || 30 |   |      | 0v      |     |     |
#|   6 |  22 | GPIO.22 |  OUT | 0 | 31 || 32 | 0 | IN   | GPIO.26 | 26  | 12  |
#|  13 |  23 | GPIO.23 |  OUT | 0 | 33 || 34 |   |      | 0v      |     |     |
#|  19 |  24 | GPIO.24 |   IN | 1 | 35 || 36 | 0 | IN   | GPIO.27 | 27  | 16  |
#|  26 |  25 | GPIO.25 |   IN | 1 | 37 || 38 | 0 | IN   | GPIO.28 | 28  | 20  |
#|     |     |      0v |      |   | 39 || 40 | 0 | IN   | GPIO.29 | 29  | 21  |
#+-----+-----+---------+------+---+----++----+---+------+---------+-----+-----+
#| BCM | wPi |   Name  | Mode | V | Physical | V | Mode | Name    | wPi | BCM |
#+-----+-----+---------+------+---+---Pi 3---+---+------+---------+-----+-----+

# GPIO pins
TASTER_1 = 12
TASTER_2 = 16
RED_PIN = 11
GREEN_PIN = 13
BLUE_PIN = 15

# use GPIO board numbers
GPIO.setmode(GPIO.BOARD)

# button = input
GPIO.setup(TASTER_1, GPIO.IN)
GPIO.setup(TASTER_2, GPIO.IN)

# LED = output
GPIO.setup(RED_PIN, GPIO.OUT)
GPIO.setup(GREEN_PIN, GPIO.OUT)
GPIO.setup(BLUE_PIN, GPIO.OUT)

# define state
status = "idle"
GPIO.output(BLUE_PIN, GPIO.HIGH)

# USB-Sticks by UUID
# stick[("54D3-D098", "E9B7-83A1", "F054-0EB3", "C087-0BFB")]


# LED off
def led_off():
    GPIO.output(BLUE_PIN, GPIO.LOW)
    GPIO.output(RED_PIN, GPIO.LOW)
    GPIO.output(GREEN_PIN, GPIO.LOW)


# error LED
def error():
    i = 0
    led_off()
    for i in range(10):
        GPIO.output(RED_PIN, GPIO.HIGH)
        time.sleep(0.05)
        GPIO.output(RED_PIN, GPIO.LOW)
        time.sleep(0.05)


# start record
def start_recording(pin):
    global status
    if status == "idle":
        status = "switching"
        led_off()
        GPIO.output(RED_PIN, GPIO.HIGH)
        print("mount usb, start motion")
        subprocess.call(["sudo", "mkdir", "/media/usb-video"])
        subprocess.call([
            "sudo",
            "mount",
            "/dev/sda1",
            "/media/usb-video"
        ])
        if not os.path.ismount('/media/usb-video'):
            error()
            GPIO.output(BLUE_PIN, GPIO.HIGH)
            status = "idle"
            return

        subprocess.check_call(["sudo", "motion"])
        led_off()
        GPIO.output(GREEN_PIN, GPIO.HIGH)
        status = "recording"


# stop record
def stop_recording(pin):
    global status
    if status == "recording":
        status = "switching"
        led_off()
        GPIO.output(RED_PIN, GPIO.HIGH)
        print("stop motion, unmount usb")
        subprocess.call(["sudo", "killall", "-9", "motion"])
        subprocess.call(["sudo", "sync"])
        subprocess.call(["sudo", "umount", "/media/usb-video"])
        subprocess.call(["sudo", "rm", "-r", "/media/usb-video"])
        led_off()
        GPIO.output(BLUE_PIN, GPIO.HIGH)
        status = "idle"


if __name__ == "__main__":
    print("waiting for input")
    try:
        # define interrupt, get rising signal, debounce pin
        GPIO.add_event_detect(
            TASTER_1,
            GPIO.RISING,
            callback=start_recording,
            bouncetime=1000
        )
        GPIO.add_event_detect(
            TASTER_2,
            GPIO.RISING,
            callback=stop_recording,
            bouncetime=1000
        )
        # keep script running
        while True:
            time.sleep(0.5)

    finally:
        GPIO.cleanup()
        print("\nQuit\n")
