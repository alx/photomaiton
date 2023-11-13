import gphoto2 as gp
import cv2
import os
import time
import datetime
import sys
from PIL import Image
import cups
from tempfile import mktemp
import logging
from pathlib import Path
import uuid
#from mastodon import Mastodon
import serial
import json

args = sys.argv
if len(args) >= 2:
    CURRENT_PATH = os.path.abspath(args[1])
else:
    CURRENT_PATH = os.path.dirname(os.path.abspath(__file__))
    
with open(Path(CURRENT_PATH, "config.json"), "r") as f:
    config = json.load(f)

USB_STICK = config["usb_stick"]  # use of usb storage
if USB_STICK:
    CURRENT_PATH = os.path.abspath(config["usb_stick_adr"])

LOG_FILENAME = Path(CURRENT_PATH, config["log_filename"])
logging.basicConfig(
    format="%(asctime)s %(levelname)s %(message)s",
    filename=LOG_FILENAME,
    level=logging.DEBUG,
    datefmt="%Y-%m-%d %H:%M:%S",
)

PHOTO_COUNT = config["photo_count"]  # number of photos to take
PHOTO_PAUSE = config["photo_pause"]  # in seconds
ARDUINO_JSON = config["arduino_json"]  # communicate with serial & json (unless with gpio)

# mastodon
MASTODON_ENABLE = config["mastodon_enable"]

if MASTODON_ENABLE:
    mastodon = Mastodon(
        api_base_url=config["mastodon_base_url"],
        access_token=config["mastodon_access_token"],
    )

# Folder containing background
PROCESS_ASSETS_FOLDER = Path(CURRENT_PATH, "assets/")
if not PROCESS_ASSETS_FOLDER.exists():
    os.makedirs(PROCESS_ASSETS_FOLDER)

# Root folder for `capture_uuid` captures
CAPTURE_FOLDER = Path(CURRENT_PATH, "captures/")
if not CAPTURE_FOLDER.exists():
    os.makedirs(CAPTURE_FOLDER)

# Create background image if it doesn't exist
try:
    PROCESS_FILE_BACKGROUND = Image.open(Path(PROCESS_ASSETS_FOLDER, "background.jpg"))
except FileNotFoundError:
    PROCESS_FILE_BACKGROUND = Image.new("RGB", (3600, 2400), color="white")
    PROCESS_FILE_BACKGROUND.save(Path(PROCESS_ASSETS_FOLDER, "background.jpg"))

# Create mask image if it doesn't exist
try:
    PROCESS_FILE_MASK = Image.open(Path(PROCESS_ASSETS_FOLDER, "mask.jpg"))
except FileNotFoundError:
    PROCESS_FILE_MASK = Image.new("RGB", (875, 1150), color="white")
    PROCESS_FILE_MASK.save(Path(PROCESS_ASSETS_FOLDER, "mask.jpg"))

# Create logo image if it doesn't exist
ADD_LOGO = config["add_logo"]
if ADD_LOGO:
    LOGO1_POS = config["logo1_pos"]
    LOGO2_POS = config["logo2_pos"]
    try:
        PROCESS_FILE_LOGO = Image.open(Path(PROCESS_ASSETS_FOLDER, "logo.png"))
    except FileNotFoundError:
        PROCESS_FILE_LOGO = Image.new("RGB", (1, 1), color="white")
        PROCESS_FILE_LOGO.save(Path(PROCESS_ASSETS_FOLDER, "logo.png"))

# Final image for print (dnp ds 40 eat the borders / fond perdu)
try:
    PROCESS_FILE_MARGIN = Image.open(Path(PROCESS_ASSETS_FOLDER, "margin.jpg"))
except FileNotFoundError:
    PROCESS_FILE_MARGIN = Image.new("RGB", (3700, 2500), color="white")
    PROCESS_FILE_MARGIN.save(Path(PROCESS_ASSETS_FOLDER, "margin.png"))

PRINT = config["print"]
MARGIN = config["margin"]
print(MARGIN)
# Raspberry Pi
ON_RASP = False  # will be set to True if running on Raspberry Pi
GPIO_INPUT = 15  # GPIO pin to use for input

try:
    import RPi.GPIO as GPIO

    GPIO.setmode(GPIO.BCM)
    GPIO.setup(GPIO_INPUT, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    ON_RASP = True
except:
    logging.debug("Error importing RPi.GPIO")

# Serial arduino
if ARDUINO_JSON:
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
    


def capture_webcam(
    nb_photos=1,
    photo_pause=0,
    filename="capture.jpg",
    capture_id=0,
    width=640,
    height=480,
):
    cap = cv2.VideoCapture(capture_id)
    cap.set(3, width)
    cap.set(4, height)

    capture_uuid = uuid.uuid4()
    CAPTURE_PATH = Path(CAPTURE_FOLDER, str(capture_uuid))
    if not CAPTURE_PATH.exists():
        os.makedirs(CAPTURE_PATH)

    if cap.isOpened():
        for i in range(nb_photos):
            if nb_photos > 1:
                photo_filename = str(i) + ".jpg"
            else:
                photo_filename = "capture.jpg"

            _, frame = cap.read()
            cap.release()  # releasing camera immediately after capturing picture
            if _ and frame is not None:
                cv2.imwrite(str(Path(CAPTURE_PATH, photo_filename)), frame)

            time.sleep(photo_pause)

    return capture_uuid


# Only run if on Raspberry Pi
def init_camera():
    logging.info("Camera init - Wait loop for camera")
    error, camera = gp.gp_camera_new()

    while True:
        error = gp.gp_camera_init(camera)

        if error >= gp.GP_OK:
            # operation completed successfully so exit loop
            break
        if error != gp.GP_ERROR_MODEL_NOT_FOUND:
            # some other error we can't handle here
            raise gp.GPhoto2Error(error)
        # no camera, try again in 2 seconds
        time.sleep(2)

    # capture pour enclencher le process sinon ça le fait pas
    logging.info("Camera init - first capture")
    camera.capture(gp.GP_CAPTURE_IMAGE)

    # continue with rest of program
    logging.info("Camera init - continue")

    return camera


def capture(camera):
    #capture_uuid = uuid.uuid4()
    capture_uuid = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    CAPTURE_PATH = Path(CAPTURE_FOLDER, str(capture_uuid))

    if not CAPTURE_PATH.exists():
        os.makedirs(CAPTURE_PATH)

    logging.info("Capture - Start shooting - " + str(capture_uuid))

    for image_index in range(PHOTO_COUNT):
        time.sleep(PHOTO_PAUSE)

        filename = str(image_index) + ".jpg"
        target = os.path.join(CAPTURE_PATH, filename)
        logging.info("Capture - Copying image to" + str(target))

        # capture
        file_path = camera.capture(gp.GP_CAPTURE_IMAGE)
        logging.info(
            "Capture - Camera file path: {0}/{1}".format(
                file_path.folder, file_path.name
            )
        )

        # download
        camera_file = camera.file_get(
            file_path.folder, file_path.name, gp.GP_FILE_TYPE_NORMAL
        )
        camera_file.save(target)

    return capture_uuid


def capture_files(capture_uuid):
    CAPTURE_PATH = Path(CAPTURE_FOLDER, str(capture_uuid))
    return [str(x) for x in CAPTURE_PATH.iterdir() if x.is_file()]


def capture_to_toot(image_filepath):
    media_ids = mastodon.media_post(image_filepath)

    mastodon.status_post(
        status="@alx prompt: test image | negative_prompt: cartoon | other_param: 0.2",
        media_ids=media_ids,
        visibility="direct",
    )


def capture_to_montage(capture_uuid):
    CAPTURE_PATH = Path(CAPTURE_FOLDER, str(capture_uuid))
    im1 = Image.open(Path(CAPTURE_PATH, "0.jpg"))
    im2 = Image.open(Path(CAPTURE_PATH, "1.jpg"))
    im3 = Image.open(Path(CAPTURE_PATH, "2.jpg"))
    im4 = Image.open(Path(CAPTURE_PATH, "3.jpg"))

    crop = (744, 0, 2232, 1984)
    im1 = im1.crop(crop)
    im2 = im2.crop(crop)
    im3 = im3.crop(crop)
    im4 = im4.crop(crop)

    # resize
    (width, height) = (875, 1150)
    im1 = im1.resize((width, height))
    im2 = im2.resize((width, height))
    im3 = im3.resize((width, height))
    im4 = im4.resize((width, height))

    im1.save(Path(CAPTURE_PATH,"0.jpg"))
    im2.save(Path(CAPTURE_PATH,"1.jpg"))
    im3.save(Path(CAPTURE_PATH,"2.jpg"))
    im4.save(Path(CAPTURE_PATH,"3.jpg"))

    mask = PROCESS_FILE_MASK.resize(im1.size)
    mask = mask.convert("L")

    # im1.save('/tmp/0.jpg', quality=95)
    PROCESS_FILE_BACKGROUND.paste(im1, (20, 20), mask)
    PROCESS_FILE_BACKGROUND.paste(im2, (915, 20), mask)
    PROCESS_FILE_BACKGROUND.paste(im3, (1810, 20), mask)
    PROCESS_FILE_BACKGROUND.paste(im4, (2705, 20), mask)
    # noir et blanc
    PROCESS_FILE_BACKGROUND.paste(im1.convert("L"), (20, 1225), mask)
    PROCESS_FILE_BACKGROUND.paste(im2.convert("L"), (915, 1225), mask)
    PROCESS_FILE_BACKGROUND.paste(im3.convert("L"), (1810, 1225), mask)
    PROCESS_FILE_BACKGROUND.paste(im4.convert("L"), (2705, 1225), mask)

    # logos
    if ADD_LOGO:
        PROCESS_FILE_BACKGROUND.paste(PROCESS_FILE_LOGO, (LOGO1_POS['x'], LOGO1_POS['y']), PROCESS_FILE_LOGO)
        PROCESS_FILE_BACKGROUND.paste(PROCESS_FILE_LOGO, (LOGO2_POS['x'], LOGO2_POS['y']), PROCESS_FILE_LOGO)

    # Add margins
    PROCESS_FILE_MARGIN.paste(PROCESS_FILE_BACKGROUND, (MARGIN['x'], MARGIN['y']))
    PROCESS_FILE_MARGIN.save(Path(CAPTURE_PATH, "print.jpg"), quality=95)


def print_image(capture_uuid):
    # impression
    logging.info("Print Image - start")

    # Set up CUPS
    conn = cups.Connection()
    printers = conn.getPrinters()
    printer_name = list(printers.keys())[0]
    cups.setUser("pi")

    # Save data to a temporary file
    CAPTURE_PATH = Path(CAPTURE_FOLDER, str(capture_uuid))
    imgPrint = Image.open(os.path.join(CAPTURE_PATH, "print.jpg"))

    output = mktemp(prefix="jpg")
    imgPrint.save(output, format="jpeg")

    # Send the picture to the printer
    print_id = conn.printFile(printer_name, output, "nofilterbooth", {})
    logging.info("Print Image - print id: " + str(print_id))
    # Wait until the job finishes
    # from time import sleep
    # while conn.getJobs().get(print_id, None):
    # sleep(1)


def main():
    if ON_RASP:
        # init camera
        camera = init_camera()

        # Boucle de la mort
        while True:
            bStart = False
            if ARDUINO_JSON:
                # Commande" via serial de l'arduino
                jason = {}

                if ser.in_waiting > 0:
                    line = ser.readline().decode("utf-8").rstrip()

                    try:
                        jason = json.loads(line)
                    except json.decoder.JSONDecodeError:
                        logging.info("Not json:" + str(line))

                    logging.info("json:" + str(jason))

                    if "cmd" in jason and jason["cmd"] == 1:
                        bStart = True
            else:
                if GPIO.input(15):
                    bStart = True

            if bStart:
                capture_uuid = capture(camera)
                for capture_filepath in capture_files(capture_uuid):
                    print(capture_filepath)
                    if MASTODON_ENABLE:
                        output = capture_to_toot(capture_filepath)
                output = capture_to_montage(capture_uuid)
                if PRINT:
                    print_image(capture_uuid)      

        return 0
    else:
        logging.debug("Not running on Raspberry Pi")
        capture_uuid = capture_webcam()
        for capture_filepath in capture_files(capture_uuid):
            print(capture_filepath)
            if MASTODON_ENABLE:
                output = capture_to_toot(capture_filepath)
        return 1


if __name__ == "__main__":
    main()
