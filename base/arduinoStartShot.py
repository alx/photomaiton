#
# Send json command to arduino to start photo sequence
#

import serial
import json
import os
import logging
from pathlib import Path

CURRENT_PATH = os.path.dirname(os.path.abspath(__file__))

LOG_FILENAME = Path(CURRENT_PATH, "arduino.log")
logging.basicConfig(
    format="%(asctime)s %(levelname)s %(message)s",
    filename=LOG_FILENAME,
    level=logging.DEBUG,
    datefmt="%Y-%m-%d %H:%M:%S",
)

# Serial arduino
try:
    ser = serial.Serial("/dev/ttyUSB0", 9600, timeout=1)
    ser.reset_input_buffer()
except:
    logging.debug("Error serial arduino usb0")
    try:
        ser = serial.Serial("/dev/ttyUSB1", 9600, timeout=1)
        ser.reset_input_buffer()
    except:
        logging.debug("Error serial arduino usb1")

def main():
    # convert into JSON:
    jason = "1".encode('utf-8')
    ser.write(jason)
    return 1


if __name__ == "__main__":
    main()