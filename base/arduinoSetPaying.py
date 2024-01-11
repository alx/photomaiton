#
# Send json command to arduino to start photo sequence
#

import serial
import json
import os
import logging
from pathlib import Path
from arduino import connect_to_arduino

CURRENT_PATH = os.path.dirname(os.path.abspath(__file__))

LOG_FILENAME = Path(CURRENT_PATH, "arduino.log")
logging.basicConfig(
    format="%(asctime)s %(levelname)s %(message)s",
    filename=LOG_FILENAME,
    level=logging.DEBUG,
    datefmt="%Y-%m-%d %H:%M:%S",
)

serial = connect_to_arduino()

def main():
    # convert into JSON:
    jason = "6".encode('utf-8')
    serial.write(jason)
    return 1


if __name__ == "__main__":
    main()