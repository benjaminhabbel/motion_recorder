#!/usr/bin/python
from __future__ import print_function
import RPi.GPIO as GPIO
import time
import queue # https://pymotw.com/2/Queue/
import subprocess

#GPIO Pins
Taster1 = 37
Taster2 = 35
redPin = 33
greenPin = 31
bluePin = 29

# GPIO-Nummer als Pinreferenz waehlen
GPIO.setmode(GPIO.BOARD)  

# Taster als Input deklarieren
GPIO.setup(Taster1, GPIO.IN)
GPIO.setup(Taster2, GPIO.IN)

# LED als Output deklarieren
GPIO.setup(redPin, GPIO.OUT)
GPIO.setup(greenPin, GPIO.OUT)
GPIO.setup(bluePin, GPIO.OUT)

# Dictionary definieren. http://www.tutorialspoint.com/python/python_dictionary.htm
dictionary = {}
dictionary['pause'] = False

queue = queue.Queue()

# Script pausieren/blockieren/beschaeftigen
def Pause():
   while dictionary['pause'] == True:
       time.sleep(1)

# RGB-LED konfigurieren
def turnOn(pin):
    GPIO.output(pin, GPIO.HIGH)

def turnOff(pin):
    GPIO.output(pin, GPIO.LOW)

def redOn():
    turnOff(redPin)

def redOff():
    turnOff(redPin)

#def greenOn():
#    turnOff(greenPin)

#def greenOff():
#    turnOff(greenPin)

def blueOn():
    turnOff(bluePin)

#def blueOff():
#    turnOff(bluePin)

def yellowOn():
    turnOff(redPin)
    turnOff(greenPin)

#def yellowOff():
#    turnOff(redPin)
#    turnOff(greenPin)

#def cyanOn():
#    turnOff(greenPin)
#    turnOff(bluePin)

#def cyanOff():
#    turnOff(greenPin)
#    turnOff(bluePin)

#def magentaOn():
#    turnOff(redPin)
#    turnOff(bluePin)

#def magentaOff():
#    turnOff(redPin)
#    turnOff(bluePin)

#def whiteOn():
#    turnOff(redPin)
#    turnOff(greenPin)
#    turnOff(bluePin)

def whiteOff():
    turnOff(redPin)
    turnOff(greenPin)
    turnOff(bluePin)

# ISR
def InterruptIn(pin):
    if pin == Taster1:
        if dictionary['pause'] == True:
            whiteOff()
            redOn()
            print("mount usb, start motion")
            subprocess.run(["sudo", "mount", "/media/usb-video"])
            subprocess.run(["sudo", "service", "motion", "start"])
            dictionary['pause'] = False
            redOff()
            blueOn()
        else:
            queue.put(pin)

def InterruptOut(pin):
    if pin == Taster2:
        if dictionary['pause'] == True:
            whiteOff()
            redOn()
            print("stop motion, unmount usb")
            subprocess.run(["sudo", "service", "motion", "stop"])
            subprocess.run(["sudo", "umount", "/media/usb-video"])
            dictionary['pause'] = False
            redOff()
            yellowOn()
        else:
            queue.put(pin)

try:
    # Interrupt Event hinzufuegen. Auf steigende Flanke reagieren und ISR "Interrupt" deklarieren sowie Pin entprellen
    GPIO.add_event_detect(Taster1, GPIO.RISING, callback=InterruptIn, bouncetime=200)
    GPIO.add_event_detect(Taster2, GPIO.RISING, callback=InterruptOut, bouncetime=200)
    # keep script running
    while True:
        time.sleep(0.5)
        if not queue.empty():
            job = queue.get()
            if job == Taster1:
                print("RECORD!")
                dictionary['pause'] = True
                Pause()
            if job == Taster2:
                print("PAUSE!")
                dictionary['pause'] = True
                Pause()
except (KeyboardInterrupt, SystemExit):
   GPIO.cleanup()
   print("\nQuit\n")

