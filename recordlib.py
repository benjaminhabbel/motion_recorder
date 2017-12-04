import os
import RPi.GPIO as GPIO
import time
import subprocess
import logging
import shutil
import sys
import datetime

# GPIO pins
TASTER_1 = 12
TASTER_2 = 16
RED_PIN = 11
GREEN_PIN = 13
BLUE_PIN = 15

# define state
status = "idle"

# debug logging
logSrc = '/home/pi/motion_recorder/test-pig_recorder.log'
logDst = '/media/usb-video/pig_recorder.log'

def initialize():
    # use GPIO board numbers
    GPIO.setmode(GPIO.BOARD)
    GPIO.setwarnings(False)

    # button = input
    GPIO.setup(TASTER_1, GPIO.IN)
    GPIO.setup(TASTER_2, GPIO.IN)

    # LED = output
    GPIO.setup(RED_PIN, GPIO.OUT)
    GPIO.setup(GREEN_PIN, GPIO.OUT)
    GPIO.setup(BLUE_PIN, GPIO.OUT)

    GPIO.output(BLUE_PIN, GPIO.HIGH)

    logging.basicConfig(
    filename=logSrc,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
    datefmt='%Y/%m/%d - %H:%M:%S',
    level=logging.DEBUG
)

    stdout_logger = logging.getLogger('STDOUT')
    sl = StreamToLogger(stdout_logger, logging.INFO)
    sys.stdout = sl

    stderr_logger = logging.getLogger('STDERR')
    sl = StreamToLogger(stderr_logger, logging.ERROR)
    sys.stderr = sl


class StreamToLogger(object):
   """
   Fake file-like stream object that redirects writes to a logger instance.
   """
    def __init__(self, logger, log_level=logging.INFO):
        self.logger = logger
        self.log_level = log_level
        self.linebuf = ''

    def write(self, buf):
        for line in buf.rstrip().splitlines():
            self.logger.log(self.log_level, line.rstrip())

    def flush(self, flush):
        pass


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
        logging.info("Button 1 -> mount usb, start ffmpeg")
        if not os.path.exists('/media/usb-video'):
            os.mkdir('/media/usb-video')
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
        #cmd="ffmpeg -i /dev/video0 -vf drawtext=x=8: y=8: box=1: fontcolor=white: boxcolor=black: expansion=strftime: text='%T' -r 3 -hide_banner -f segment -segment_time 3600 -strftime 1 camera1-%Y%m%d-%H%M%S.avi"
        #rec = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, bufsize=10**8)
        #for line in rec.stdout:
        #    logging.info(line)
        date = datetime.datetime.strftime(
            datetime.datetime.today(),
            "%Y%m%d_%H%M%S"
        )
        subprocess.Popen([
            "ffmpeg", "-i", "/dev/video0",
            "-vf", "drawtext=x=8: y=8: box=1: fontcolor=white: boxcolor=black: expansion=strftime: text='%T'",
            "-r", "3",
            "camera1-{0}.avi".format(date)
        ])
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
        logging.info("Button 2 -> stop ffmpeg, unmount usb")
        shutil.copyfile(logSrc, logDst)
        subprocess.call(["sudo", "killall", "ffmpeg"])
        subprocess.call(["sudo", "sync"])
        try:
            os.chdir("/home/pi")
            subprocess.check_call(["sudo", "umount", "/media/usb-video"])
        except:
            print('could not unmount drive')
            logging.error("could not unmount drive")
            status = "recording"
            return
        subprocess.call(["sudo", "rm", "-r", "/media/usb-video"])
        led_off()
        GPIO.output(BLUE_PIN, GPIO.HIGH)
        status = "idle"