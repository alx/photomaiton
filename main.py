import gphoto2 as gp
import cv2
import os
import time
import sys
from PIL import Image
import cups
from tempfile import mktemp
import logging
from pathlib import Path
import uuid

CURRENT_PATH = os.path.dirname(os.path.abspath(__file__))
LOG_FILENAME = Path(CURRENT_PATH, 'log.txt')
logging.basicConfig(filename=LOG_FILENAME,level=logging.DEBUG)

PHOTO_LENGTH = 4 # number of photos to take
PHOTO_PAUSE = 5 # in seconds

# Folder containing background
PROCESS_ASSETS_FOLDER = Path(CURRENT_PATH, 'assets/')
if not PROCESS_ASSETS_FOLDER.exists():
        os.makedirs(PROCESS_ASSETS_FOLDER)

# Root folder for `capture_uuid` captures
CAPTURE_FOLDER = Path(CURRENT_PATH, 'captures/')
if not CAPTURE_FOLDER.exists():
        os.makedirs(CAPTURE_FOLDER)

# Create background image if it doesn't exist
try:
        PROCESS_FILE_BACKGROUND = Image.open(Path(PROCESS_ASSETS_FOLDER, 'background.png'))
except FileNotFoundError:
        PROCESS_FILE_BACKGROUND = Image.new('RGB', (6000, 4000), color='black')
        PROCESS_FILE_BACKGROUND.save(Path(PROCESS_ASSETS_FOLDER, 'background.png'))

# Create mask image if it doesn't exist
try:
        PROCESS_FILE_MASK = Image.open(Path(PROCESS_ASSETS_FOLDER, 'mask.png'))
except FileNotFoundError:
        PROCESS_FILE_MASK = Image.new('RGB', (6000, 4000), color='black')
        PROCESS_FILE_MASK.save(Path(PROCESS_ASSETS_FOLDER, 'mask.png'))

# Raspberry Pi
ON_RASP = False # will be set to True if running on Raspberry Pi
GPIO_INPUT = 15 # GPIO pin to use for input

try:
        import RPi.GPIO as GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(GPIO_INPUT, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        ON_RASP = True
except RuntimeError:
        logging.debug("Error importing RPi.GPIO")

def capture_webcam():

        logging.debug('Not running on Raspberry Pi')
        cap = cv2.VideoCapture(0)
        cap.set(3,640) #width=640
        cap.set(4,480) #height=480

        capture_uuid = uuid.uuid4()
        CAPTURE_PATH = Path(CAPTURE_FOLDER, str(capture_uuid))
        if not CAPTURE_PATH.exists():
                os.makedirs(CAPTURE_PATH)

        if cap.isOpened():
                _,frame = cap.read()
                cap.release() #releasing camera immediately after capturing picture
                if _ and frame is not None:
                        cv2.imwrite(str(Path(CAPTURE_PATH, '0.jpg')), frame)
                        cv2.imwrite(str(Path(CAPTURE_PATH, '1.jpg')), frame)
                        cv2.imwrite(str(Path(CAPTURE_PATH, '2.jpg')), frame)
                        cv2.imwrite(str(Path(CAPTURE_PATH, '3.jpg')), frame)
        return capture_uuid

# Only run if on Raspberry Pi
def init_camera():

        logging.info('Camera init - Wait loop for camera')
        error, camera = gp.gp_camera_new()

        while True:

                error = gp.gp_camera_init(camera)

                if error >= gp.GP_OK:
                        # operation completed successfully so exit loop
                        bprinireak
                if error != gp.GP_ERROR_MODEL_NOT_FOUND:
                        # some other error we can't handle here
                        raise gp.GPhoto2Error(error)
                # no camera, try again in 2 seconds
                time.sleep(2)

        #capture pour enclencher le process sinon ça le fait pas
        logging.info('Camera init - first capture')
        camera.capture(gp.GP_CAPTURE_IMAGE)

        # continue with rest of program
        logging.info('Camera init - continue')

        return camera

def capture(camera):

        capture_uuid = uuid.uuid4()
        CAPTURE_PATH = Path(CAPTURE_FOLDER, str(capture_uuid))
        if not CAPTURE_PATH.exists():
                os.makedirs(CAPTURE_PATH)

        logging.info('Capture - Start shooting - ' + str(capture_uuid))

        for image_index in range(PHOTO_LENGTH):

                time.sleep(PHOTO_PAUSE)
                start = time.time()

                filename = str(image_index) + '.jpg'
                target = Path(CAPTURE_PATH, filename)
                logging.info('Capture - Copying image to' + str(target))

                #capture
                file_path = camera.capture(gp.GP_CAPTURE_IMAGE)
                logging.info('Capture - Camera file path: {0}/{1}'.format(file_path.folder, file_path.name))

                #download
                camera_file = camera.file_get(
                        file_path.folder,
                        file_path.name,
                        gp.GP_FILE_TYPE_NORMAL
                )
                camera_file.save(target)

                end = time.time() - start
                logging.info(end)

        return capture_uuid

def process(capture_uuid):

        CAPTURE_PATH = Path(CAPTURE_FOLDER, str(capture_uuid))
        im1 = Image.open(Path(CAPTURE_PATH, '0.jpg'))
        im2 = Image.open(Path(CAPTURE_PATH, '1.jpg'))
        im3 = Image.open(Path(CAPTURE_PATH, '2.jpg'))
        im4 = Image.open(Path(CAPTURE_PATH, '3.jpg'))

        #resize
        #crop = (200,0,1784,1984)
        #crop = (220,10,1774,1964)
        crop = (948,10,2508,1964)
        #crop = (848,50,2608,1963)
        im1 = im1.crop(crop)
        im1.save(Path(CAPTURE_PATH, '0resize.jpg'), quality=95)
        im2 = im2.crop(crop)
        im3 = im3.crop(crop)
        im4 = im4.crop(crop)

        mask = PROCESS_FILE_MASK.resize(im1.size)
        mask = mask.convert('L')

        #im1.save('/tmp/0.jpg', quality=95)
        start = time.time()
        PROCESS_FILE_BACKGROUND.paste(im1, (200, 250), mask)
        PROCESS_FILE_BACKGROUND.paste(im2, (1804, 250), mask)
        PROCESS_FILE_BACKGROUND.paste(im3, (3408, 250), mask)
        PROCESS_FILE_BACKGROUND.paste(im4, (5012, 250), mask)
        #noir et blanc
        PROCESS_FILE_BACKGROUND.paste(im1.convert('L'), (200, 2525), mask)
        PROCESS_FILE_BACKGROUND.paste(im2.convert('L'), (1804, 2525), mask)
        PROCESS_FILE_BACKGROUND.paste(im3.convert('L'), (3408, 2525), mask)
        PROCESS_FILE_BACKGROUND.paste(im4.convert('L'), (5012, 2525), mask)

        PROCESS_FILE_BACKGROUND.save(Path(CAPTURE_PATH, 'print.jpg'), quality=95)

        end = time.time() - start
        logging.info(end)

def print_image(capture_uuid):

        #impression
        logging.info('Print Image - start')

        # Set up CUPS
        conn = cups.Connection()
        printers = conn.getPrinters()
        printer_name = list(printers.keys())[0]
        cups.setUser('pi')

        # Save data to a temporary file
        CAPTURE_PATH = Path(CAPTURE_FOLDER, str(capture_uuid))
        imgPrint = Image.open(Path(CAPTURE_PATH, 'print.jpg'))

        output = mktemp(prefix='jpg')
        imgPrint.save(output, format='jpeg')

        # Send the picture to the printer
        print_id = conn.printFile(printer_name, output, "nofilterbooth", {})
        logging.info('Print Image - print id: ' + str(print_id))
        # Wait until the job finishes
        #from time import sleep
        #while conn.getJobs().get(print_id, None):
        #sleep(1)

def main():

        if ON_RASP:
                #init camera
                camera = init_camera()

                #Boucle de la mort
                while True:

                        #Impulsion de 100ms de l'arduino
                        if GPIO.input(GPUIO_INPUT):

                                capture_uuid = capture(camera)
                                output = process(capture_uuid)
                                print_image(output)

                return 0
        else:
                capture_uuid = capture_webcam()
                output = process(capture_uuid)
                return 1

if __name__ == "__main__":
        main()
