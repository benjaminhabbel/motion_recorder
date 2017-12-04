import os
import recordlib
import datetime

if __name__ == "__main__":
    if os.path.ismount('/media/usb-video'):
        date = datetime.datetime.strftime(
            datetime.datetime.today(),
            "%Y%m%d_%H%M%S"
        )
        recordlib.initialize()
        recordlib.stop_recording(0)
        recordlib.start_recording(0, date)