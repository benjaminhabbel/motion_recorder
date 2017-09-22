#!/usr/bin/python
import RPi.GPIO as gpio
import time

pin = 29
gpio.setmode(gpio.BOARD)
gpio.setup(pin, gpio.IN, pull_up_down = gpio.PUD_UP)

def my_callback(channel):
#    if channel == pin:
      if gpio.input(pin):
        print "Der Taster wurde geoeffnet."
      else:
        print "Der Taster wurde geschlossen."
gpio.add_event_detect(pin, gpio.BOTH, my_callback)
#time.sleep(5)
#try:
#  raw_input("Mit Eingabetste beenden")
#finally:
#  gpio.cleanup()
