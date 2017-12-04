#!/usr/bin/python
import os
import RPi.GPIO as GPIO
import time
import subprocess

#sudo chown -R pi:pi /media/

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
# LABEL="mp-video-1a" UUID="699c84be-41e2-423c-819a-02c0dbdf9664"
# LABEL="mp-video-1b" UUID="a4724cb0-f5d6-424d-a34a-f28b3ece39a8"
# LABEL="mp-video-2a" UUID="a5025313-3cef-407a-b320-531c64f49083"
# LABEL="mp-video-2b" UUID="176d600d-646b-40d7-83ec-bb13641fb03e"

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
        print("mount usb, start ffmpeg")
        if not os.path.exists('/media/usb-video'):
            os.mkdirs('/media/usb-video')
            return
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
        os.chdir('/media/usb-video')
        cmd = "ffmpeg -i /dev/video0 -r 3 -f segment -segment_time 3600 -strftime 1 camera1-%Y%m%d-%H%M.avi &"
        #-vf drawtext (x=8 y=8 box=1 fontcolor=white boxcolor=black expansion=strftime text='$newline %Y-%m-%d %H\\:%M\\:%S')
        subprocess.call(cmd, shell=False)
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
        print("stop ffmpeg, unmount usb")
        subprocess.call(["sudo", "killall", "ffmpeg"])
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