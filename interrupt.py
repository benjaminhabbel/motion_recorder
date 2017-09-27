#!/usr/bin/python
import RPi.GPIO as GPIO
import time
import subprocess
import os

#GPIO Pins
TASTER_1 = 37
TASTER_2 = 35
RED_PIN = 33
GREEN_PIN = 31
BLUE_PIN = 29

# GPIO-Nummer als Pinreferenz waehlen
GPIO.setmode(GPIO.BOARD)  

# Taster als Input deklarieren
GPIO.setup(TASTER_1, GPIO.IN)
GPIO.setup(TASTER_2, GPIO.IN)

# LED als Output deklarieren
GPIO.setup(RED_PIN, GPIO.OUT)
GPIO.setup(GREEN_PIN, GPIO.OUT)
GPIO.setup(BLUE_PIN, GPIO.OUT)

# Status definieren
status = "idle"
GPIO.output(BLUE_PIN, GPIO.HIGH)

# USB-Sticks by UUID
#stick[("54D3-D098", "E9B7-83A1", "F054-0EB3", "C087-0BFB")]

print("waiting for input")

def white_off():
    GPIO.output(BLUE_PIN, GPIO.LOW)
    GPIO.output(RED_PIN, GPIO.LOW)
    GPIO.output(GREEN_PIN, GPIO.LOW)

# Start record
def start_recording(pin):
    global status
    if status == "idle":
        status = "switching"
        white_off()
        GPIO.output(RED_PIN, GPIO.HIGH)
        print("mount usb, start motion")
        #try:
        subprocess.run(["sudo", "mount", "-a"])
        #except Exception as e:
        #    print("Error on mounting device:")
        #    print(str(e))
        subprocess.run(["sudo", "motion"])
        white_off()
        GPIO.output(GREEN_PIN, GPIO.HIGH)
        status = "recording"

# Stop record
def stop_recording(pin):
    global status
    if status == "recording":
        status = "switching"
        white_off()
        GPIO.output(RED_PIN, GPIO.HIGH)
        print("stop motion, unmount usb")
        subprocess.run(["sudo", "killall", "-9", "motion"])
        subprocess.run(["sudo", "umount", "/media/usb-video"])
        white_off()
        GPIO.output(BLUE_PIN, GPIO.HIGH)
        status = "idle"


try:
    # Interrupt Event hinzufuegen. Auf steigende Flanke reagieren und ISR "Interrupt" deklarieren sowie Pin entprellen
    GPIO.add_event_detect(TASTER_1, GPIO.RISING, callback=start_recording, bouncetime=200)
    GPIO.add_event_detect(TASTER_2, GPIO.RISING, callback=stop_recording, bouncetime=200)
    # keep script running
    while True:
        time.sleep(0.5)
        
except (KeyboardInterrupt, SystemExit):
   GPIO.cleanup()
   print("\nQuit\n")

