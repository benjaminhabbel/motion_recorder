#!/usr/bin/python
import os
import RPi.GPIO as GPIO
import time
import subprocess
import logging
import shutil
import sys
from datetime import datetime


class PigRecorder():

    # USB-Sticks by UUID
    # LABEL="mp-video-1a" UUID="699c84be-41e2-423c-819a-02c0dbdf9664"
    # LABEL="mp-video-1b" UUID="a4724cb0-f5d6-424d-a34a-f28b3ece39a8"
    # LABEL="mp-video-2a" UUID="a5025313-3cef-407a-b320-531c64f49083"
    # LABEL="mp-video-2b" UUID="176d600d-646b-40d7-83ec-bb13641fb03e"

    # GPIO pins
    TASTER_1 = 12
    TASTER_2 = 16
    RED_PIN = 11
    GREEN_PIN = 13
    BLUE_PIN = 15

    states = {
        'idle': BLUE_PIN,
        'recording': GREEN_PIN,
        'switching': RED_PIN,
    }

    # debug logging
    log_src = '/home/pi/motion_recorder/pig_recorder.log'
    log_dst = '/media/usb-video/pig_recorder.log'
    video_path = '/media/usb-video'

    def __init__(self):
        # use GPIO board numbers
        GPIO.setmode(GPIO.BOARD)
        GPIO.setwarnings(False)

        # button = input
        GPIO.setup(self.TASTER_1, GPIO.IN)
        GPIO.setup(self.TASTER_2, GPIO.IN)

        # LED = output
        GPIO.setup(self.RED_PIN, GPIO.OUT)
        GPIO.setup(self.GREEN_PIN, GPIO.OUT)
        GPIO.setup(self.BLUE_PIN, GPIO.OUT)

        # define state
        self.set_status("idle")

        GPIO.add_event_detect(
            self.TASTER_1,
            GPIO.RISING,
            callback=self.start_recording,
            bouncetime=1000
        )
        GPIO.add_event_detect(
            self.TASTER_2,
            GPIO.RISING,
            callback=self.stop_recording,
            bouncetime=1000
        )

        logging.basicConfig(
           filename=self.log_src,
           format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
           datefmt='%Y/%m/%d-%H:%M:%S',
           level=logging.DEBUG
        )

        stdout_logger = logging.getLogger('STDOUT')
        sys.stdout = StreamToLogger(
            stdout_logger,
            logging.INFO
        )

        stderr_logger = logging.getLogger('STDERR')
        sys.stderr = StreamToLogger(
            stderr_logger,
            logging.ERROR
        )

    def led_off(self):
        '''
        LED off
        '''
        GPIO.output(self.BLUE_PIN, GPIO.LOW)
        GPIO.output(self.RED_PIN, GPIO.LOW)
        GPIO.output(self.GREEN_PIN, GPIO.LOW)

    def set_status(self, state):
        self.status = state
        self.led_off()
        GPIO.output(
            self.states[state],
            GPIO.HIGH
        )

    def error(self):
        '''
        error LED
        '''
        self.led_off()
        for i in range(10):
            GPIO.output(self.RED_PIN, GPIO.HIGH)
            time.sleep(0.05)
            GPIO.output(self.RED_PIN, GPIO.LOW)
            time.sleep(0.05)

    def mount_drive(self):
        if os.path.ismount(self.video_path):
            return True

        self.set_status('switching')
        logging.info("mounting usb")

        if not os.path.exists(self.video_path):
            try:
                os.mkdir(self.video_path)
                subprocess.check_call([
                    "sudo",
                    "mount",
                    "/dev/sda1",
                    self.video_path
                ])
            except Exception as e:
                logging.error(e)
                self.error()
                os.rmdir(self.video_path)
                self.set_status('idle')
                return False

        return os.path.ismount(self.video_path)

    def unmount_drive(self):
        if not os.path.ismount(self.video_path):
            return True

        self.set_status("switching")
        logging.info("unmounting usb")

        shutil.copyfile(self.log_src, self.log_dst)
        subprocess.call(["sudo", "sync"])
        os.chdir("/home/pi")
        try:
            subprocess.check_call([
                "sudo",
                "umount",
                self.video_path
            ])
        except Exception as e:
            logging.error("could not unmount drive")
            logging.error(e)
            self.set_status('idle')
            return False

        try:
            subprocess.call(["sudo", "rm", "-r", self.video_path])
        except Exception as e:
            logging.error("could not remove usb-video directory")
            logging.error(e)
            self.set_status('idle')
            return False

        logging.info('unmounting complete')
        self.set_status('idle')
        return True

    def start_recording(self, pin):
        '''
        start record
        '''
        if self.status == "idle" and self.mount_drive():
            rec_time = datetime.today()
            os.chdir(self.video_path)
            subprocess.Popen([
                "sudo", "ffmpeg", "-i", "/dev/video0",
                "-vf", "drawtext=x=8: y=8: box=1: fontcolor=white: boxcolor=black: expansion=strftime: text='%T'",
                "-r", "3",
                "camera1-{}.avi".format(
                    datetime.strftime(
                        rec_time,
                        "%Y%m%d-%H%M%S"
                    )
                )
            ])
            self.set_status('recording')

    def stop_recording(self, pin):
        '''
        stop recording
        '''
        if self.status == "recording":
            self.set_status('idle')
            logging.info('killing ffmpeg')
            subprocess.call(["sudo", "killall", "ffmpeg"])
            self.unmount_drive()

    def restart_recording(self):
        if self.status == "recording":
            logging.info('killing ffmpeg')
            subprocess.call(["sudo", "killall", "ffmpeg"])
            self.set_status('idle')
            self.start_recording(0)


class StreamToLogger(object):
    """
    Fake file-like stream object that redirects
    writes to a logger instance.
    """
    def __init__(self, logger, log_level=logging.INFO):
        self.logger = logger
        self.log_level = log_level
        self.linebuf = ''

    def write(self, buf):
        for line in buf.rstrip().splitlines():
            self.logger.log(self.log_level, line.rstrip())

    def flush(self):
        pass


if __name__ == "__main__":

    recorder = PigRecorder()
    start_time = datetime.now()

    logging.info("waiting for input")
    try:
        while True:
            time_span = datetime.now() - start_time
            if time_span.total_seconds() >= 3600:
                start_time = datetime.now()
                recorder.restart_recording()
            time.sleep(0.5)

    finally:
        recorder.stop_recording(0)
        GPIO.cleanup()
        print("\nQuit\n")
