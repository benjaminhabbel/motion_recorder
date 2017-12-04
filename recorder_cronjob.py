import os
import recordlib

if __name__ == "__main__":
    if os.path.ismount('/media/usb-video'):
        recordlib.initialize()
        recordlib.stop_recording(0)
        recordlib.start_recording(0)