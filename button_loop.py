import time
from . import recordlib

if __name__ == "__main__":
    print("waiting for input")
    recordlib.logging.info("waiting for input")
    try:
        # define interrupt, get rising signal, debounce pin
        recordlib.GPIO.add_event_detect(
            recordlib.TASTER_1,
            recordlib.GPIO.RISING,
            callback=recordlib.start_recording,
            bouncetime=1000
        )
        recordlib.GPIO.add_event_detect(
            recordlib.TASTER_2,
            recordlib.GPIO.RISING,
            callback=recordlib.stop_recording,
            bouncetime=1000
        )
        # keep script running
        while True:
            time.sleep(0.5)

    finally:
        recordlib.GPIO.cleanup()
        print("\nQuit\n")
