import gphoto2 as gp
import cv2
import os
import time
import datetime
import sys
from PIL import Image, ImageDraw, ImageFont
import cups
from tempfile import mktemp
import logging
from pathlib import Path
import uuid
import serial
from serial.tools import list_ports
import json
from io import BytesIO
import argparse
import traceback
import base64
import requests
import usb.core
import db
import webuiapi
import random
import threading
import RPi.GPIO as GPIO
from luma.led_matrix.device import max7219
from luma.core.interface.serial import spi, noop
from luma.core.render import canvas
from luma.core.virtual import viewport
from luma.core.legacy import text, show_message
from luma.core.legacy.font import proportional, CP437_FONT, TINY_FONT, SINCLAIR_FONT, LCD_FONT, ATARI_FONT
import tm1637

# Pins def
COIN_PIN = 16
START_PIN = 20
AUX_PIN = 23
CB_PIN = 14


# constants
PRICE = 400
COINS_MULTI = 50
COINS = PRICE
WAITFORSTART = False
START = False

#Globals
CAMERA = None
MAX7219 = None
global CURRENT_PATH,USB_STICK, BKPIMG, BKP_PATH, PHOTO_COUNT,PHOTO_PAUSE,VERTICAL, PROCESS_ASSETS_FOLDER
global CAPTURE_FOLDER, PROCESS_FILE_BACKGROUND, PROCESS_FILE_MASK, ADD_LOGO,PROCESS_FILE_LOGO1, PROCESS_FILE_LOGO2
global LOGO1_POS, LOGO2_POS, PROCESS_FILE_MARGIN, PRINT, MARGIN, IA, api

CURRENT_PATH = os.path.dirname(os.path.abspath(__file__))
LOG_FILENAME = Path(CURRENT_PATH, "log.txt")
logging.basicConfig(
    format="%(asctime)s %(levelname)s %(message)s",
    filename=LOG_FILENAME,
    level=logging.DEBUG,
    datefmt="%Y-%m-%d %H:%M:%S",
)
#output sur console
console = logging.StreamHandler()
console.setLevel(logging.DEBUG)
format=logging.Formatter("%(asctime)s %(levelname)s %(message)s")
console.setFormatter(format)
logging.getLogger("").addHandler(console)
#deactivate Pillow logging
logging.getLogger('PIL').setLevel(logging.WARNING)

# init apn
def init_camera():
    logging.info("Camera init - Wait loop for camera")
    
    global CAMERA
    error, CAMERA = gp.gp_camera_new()

    while True:
        error = gp.gp_camera_init(CAMERA)

        if error >= gp.GP_OK:
            # operation completed successfully so exit loop
            break
        if error != gp.GP_ERROR_MODEL_NOT_FOUND:
            # some other error we can't handle here
            raise gp.GPhoto2Error(error)
        # no camera, try again in 2 seconds
        time.sleep(2)

    # capture pour enclencher le process sinon ÃÂÃÂÃÂÃÂ§a le fait pas
    logging.info("Camera init - first capture")
    CAMERA.capture(gp.GP_CAPTURE_IMAGE)

    # continue with rest of program
    logging.info("Camera init - continue")

    return CAMERA


def capture(camera):
    global MAX7219
    
    #capture_uuid = uuid.uuid4()
    capture_uuid = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
    CAPTURE_PATH = Path(CAPTURE_FOLDER, str(capture_uuid))

    if not CAPTURE_PATH.exists():
        os.makedirs(CAPTURE_PATH)

    logging.info("Capture - Start shooting - " + str(capture_uuid))
    nextShot = time.time()
    current = nextShot
    for image_index in range(PHOTO_COUNT):
        logging.info("Shot " + str(image_index))
        filename = str(image_index) + ".jpg"
        target = os.path.join(CAPTURE_PATH, filename)
        
        #countdown
        MAX7219.clear()
        for second in reversed(range(1,PHOTO_PAUSE + 1)):
            MAX7219.clear()
            with canvas(MAX7219) as draw:
                text(draw, (1, 1), str(second), fill="white", font=proportional(CP437_FONT))
            time.sleep(1)
        showSmiley()

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

        logging.info("process image")
        if not VERTICAL:
            im1 = processImage(capture_uuid, str(image_index) + ".jpg")
        else:
            im1 = processImageVertical(capture_uuid, str(image_index) + ".jpg")
            
        if IA:
            logging.info("process ia")
            task = threading.Thread( target = threadIA, name=str(image_index), args   = ( capture_uuid, image_index ) )
            task.start()

    logging.info("fin capture")
    return capture_uuid

    
def save_ia_image(capture_path, index, prompt):
    try:
        source_image_path = Path(capture_path, f"{index}.jpg")
        with Image.open(source_image_path) as source:
            
            start = time.time()

            unit0 = webuiapi.ControlNetUnit(input_image=source, 
                                            module='canny', 
                                            model='sdxl_canny [a2e6a438]', 
                                            weight=1, 
                                            control_mode = 2,
                                            guidance_end = 1,
                                            guidance_start = 0,
                                            threshold_a = 100,
                                            threshold_b = 200)

            reactor = webuiapi.ReActor(
                img=source,
                enable=True,
                source_faces_index = "0,1,2,3", #2 Comma separated face number(s) from swap-source image
                faces_index = "0,1,2,3", #3 Comma separated face number(s) for target image (result)
                model = 'inswapper_128.onnx', # None, #4 model path
                face_restorer_name = "CodeFormer", #4 Restore Face: None; CodeFormer; GFPGAN
                face_restorer_visibility = 1, #5 Restore visibility value
                restore_first = True,  #7 Restore face -> Upscale
                upscaler_name =  "None",# None, # "R-ESRGAN 4x+", #8 Upscaler (type 'None' if doesn't need), see full list here: http://127.0.0.1:7860/sdapi/v1/script-info -> reactor -> sec.8
                upscaler_scale = 2,#9 Upscaler scale value
                upscaler_visibility = 1,
                swap_in_source = True,
                swap_in_generated = True,
                console_logging_level = 2, #13 Console Log Level (0 - min, 1 - med or 2 - max)
                gender_source = 0, #14 Gender Detection (Source) (0 - No, 1 - Female Only, 2 - Male Only)
                gender_target = 0, #14 Gender Detection (Target) (0 - No, 1 - Female Only, 2 - Male Only)
                save_original = False,
                codeFormer_weight = 1,
                source_hash_check = True,
                target_hash_check = True,
                device = "CUDA", #or CPU
                mask_face = False,
                select_source = 0, #IMPORTANT. MUST BE 0 or faceswap won't work
                face_model = None,
            )

            
            result1 = api.txt2img(prompt=prompt["positive"],
                                negative_prompt=prompt["negative"],
                                seed=-1,
                                cfg_scale=1,
                                steps=9,
                                width=1150,
                                height=875,
                                controlnet_units=[unit0],
                                restore_faces=False,
                                reactor=reactor)
            #capture_uuid = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
            filepath = Path(capture_path, f"{index}.ia.jpg")
            filepathSD = Path(capture_path, f"{index}.iabkp.jpg")
            result1.image.save(filepath)
            #Resize sinon image en 872 x 1144
            imageIA = Image.open(filepath)
            (width, height) = (1150, 875)
            imageIA = imageIA.resize((width, height))
            imageIA.save(filepath)
            
            end = time.time()
            logging.info(str(index) + ": %s seconds ---" % (end - start))

            # Ouverture de l'image reÃÂÃÂÃÂÃÂ§ue pour traitement
            with Image.open(filepath) as img:
                
                # Save the final image after cropping, resizing, and adding the label
                font_size = 64
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", font_size)
                draw = ImageDraw.Draw(img) 
                if VERTICAL:
                    draw.text((20, 20), prompt["name"],(255, 255, 255), font=font)
                else:
                    draw.text((20, 20), prompt["name"],(255, 255, 255), font=font)
                img.save(filepath)
            
            logging.info(f"Image resized and saved successfully: {filepath}")
    
    except Exception as e:
        logging.error("An exception occurred while processing the image:")
        logging.error(traceback.format_exc())

def threadIA(capture_uuid, id):
    CAPTURE_PATH = Path(CAPTURE_FOLDER, str(capture_uuid))
    
    # mode alÃ©atoire
    lettres = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K']

    save_ia_image(CAPTURE_PATH, id, config["prompts"][str(id+1)+ str(random.choice(lettres))])


def capture_to_ia(capture_uuid):

    CAPTURE_PATH = Path(CAPTURE_FOLDER, str(capture_uuid))
    # mode alÃ©atoire
    lettres = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K']

    save_ia_image(CAPTURE_PATH, 0, config["prompts"]["1"+ str(random.choice(lettres))])
    save_ia_image(CAPTURE_PATH, 1, config["prompts"]["2"+ str(random.choice(lettres))])
    save_ia_image(CAPTURE_PATH, 2, config["prompts"]["3"+ str(random.choice(lettres))])
    save_ia_image(CAPTURE_PATH, 3, config["prompts"]["4"+ str(random.choice(lettres))])

def processImage(capture_uuid, imgName):
    CAPTURE_PATH = Path(CAPTURE_FOLDER, str(capture_uuid))
    img = Image.open(Path(CAPTURE_PATH, imgName))
    crop = (832, 0, 2144, 1728) # RÃ©solution 2592x1728 
    img = img.crop(crop)
    (width, height) = (875, 1150)
    img = img.resize((width, height))
    img.save(Path(CAPTURE_PATH,imgName))
    return img

def processImageVertical(capture_uuid, imgName):
    CAPTURE_PATH = Path(CAPTURE_FOLDER, str(capture_uuid))
    img = Image.open(Path(CAPTURE_PATH, imgName))
    #crop = (164, 0, 2428, 1728) # RÃ©solution 2592x1728 
    crop = (233, 0, 3223, 2304) # RÃ©solution 3456x2304
    img = img.crop(crop)
    (width, height) = (1150, 875)
    img = img.resize((width, height))
    img.save(Path(CAPTURE_PATH,imgName))
    return img

def processImages(capture_uuid):
    if not VERTICAL:
        im1 = processImage(capture_uuid, "0.jpg")
        im2 = processImage(capture_uuid, "1.jpg")
        im3 = processImage(capture_uuid, "2.jpg")
        im4 = processImage(capture_uuid, "3.jpg")
    else:
        im1 = processImageVertical(capture_uuid, "0.jpg")
        im2 = processImageVertical(capture_uuid, "1.jpg")
        im3 = processImageVertical(capture_uuid, "2.jpg")
        im4 = processImageVertical(capture_uuid, "3.jpg")


def capture_to_montage(capture_uuid, bIA):
    logging.info("capture_to_montage")
    CAPTURE_PATH = Path(CAPTURE_FOLDER, str(capture_uuid))
    im1 = Image.open(Path(CAPTURE_PATH, "0.jpg"))
    im2 = Image.open(Path(CAPTURE_PATH, "1.jpg"))
    im3 = Image.open(Path(CAPTURE_PATH, "2.jpg"))
    im4 = Image.open(Path(CAPTURE_PATH, "3.jpg"))
    
    try:
        imia1 = Image.open(Path(CAPTURE_PATH, "0.ia.jpg"))
    except FileNotFoundError:
        imia1 = im1.convert("L")
    try:
        imia2 = Image.open(Path(CAPTURE_PATH, "1.ia.jpg"))
    except FileNotFoundError:
        imia2 = im2.convert("L")
    try:
        imia3 = Image.open(Path(CAPTURE_PATH, "2.ia.jpg"))
    except FileNotFoundError:
        imia3 = im3.convert("L")
    try:
        imia4 = Image.open(Path(CAPTURE_PATH, "3.ia.jpg"))
    except FileNotFoundError:
        imia4 = im4.convert("L")

    if BKPIMG:
        im1.save(Path(BKP_PATH, str(capture_uuid) + "_1.jpg"), quality=95)
        im2.save(Path(BKP_PATH, str(capture_uuid) + "_2.jpg"), quality=95)
        im3.save(Path(BKP_PATH, str(capture_uuid) + "_3.jpg"), quality=95)
        im4.save(Path(BKP_PATH, str(capture_uuid) + "_4.jpg"), quality=95)
        imia1.save(Path(BKP_PATH, str(capture_uuid) + "_1_NB.jpg"), quality=95)
        imia2.save(Path(BKP_PATH, str(capture_uuid) + "_2_NB.jpg"), quality=95)
        imia3.save(Path(BKP_PATH, str(capture_uuid) + "_3_NB.jpg"), quality=95)
        imia4.save(Path(BKP_PATH, str(capture_uuid) + "_4_NB.jpg"), quality=95)

    #rotate si mode horizontal
    if VERTICAL:
        im1 = im1.rotate(90, expand=True)
        im2 = im2.rotate(90, expand=True)
        im3 = im3.rotate(90, expand=True)
        im4 = im4.rotate(90, expand=True)
        imia1 = imia1.rotate(90, expand=True)
        imia2 = imia2.rotate(90, expand=True)
        imia3 = imia3.rotate(90, expand=True)
        imia4 = imia4.rotate(90, expand=True)
    
    mask = PROCESS_FILE_MASK.resize(im1.size)
    mask = mask.convert("L")

    # Couleur
    PROCESS_FILE_BACKGROUND.paste(im1, (20, 20), mask)
    PROCESS_FILE_BACKGROUND.paste(im2, (915, 20), mask)
    PROCESS_FILE_BACKGROUND.paste(im3, (1810, 20), mask)
    PROCESS_FILE_BACKGROUND.paste(im4, (2705, 20), mask)
    
    # noir et blanc ou IA
    PROCESS_FILE_BACKGROUND.paste(imia1, (20, 1225), mask)
    PROCESS_FILE_BACKGROUND.paste(imia2, (915, 1225), mask)
    PROCESS_FILE_BACKGROUND.paste(imia3, (1810, 1225), mask)
    PROCESS_FILE_BACKGROUND.paste(imia4, (2705, 1225), mask)  

    # logos
    if ADD_LOGO:
        PROCESS_FILE_BACKGROUND.paste(PROCESS_FILE_LOGO1, (LOGO1_POS['x'], LOGO1_POS['y']), PROCESS_FILE_LOGO1)
        PROCESS_FILE_BACKGROUND.paste(PROCESS_FILE_LOGO2, (LOGO2_POS['x'], LOGO2_POS['y']), PROCESS_FILE_LOGO2)

    # Add margins
    PROCESS_FILE_MARGIN.paste(PROCESS_FILE_BACKGROUND, (MARGIN['x'], MARGIN['y']))
    PROCESS_FILE_MARGIN.save(Path(CAPTURE_PATH, "print.jpg"), quality=95)

    #BACKUP
    if BKPIMG:
        PROCESS_FILE_MARGIN.save(Path(BKP_PATH, str(capture_uuid) + "_print.jpg"), quality=95)

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

def showArrow():
    global MAX7219,PROCESS_ASSETS_FOLDER
    arrowImg = Image.open(Path(PROCESS_ASSETS_FOLDER, "arrow.png"))
    arrowImg = arrowImg.convert('1')
    MAX7219.display(arrowImg)

def showSmiley():
    global MAX7219, PROCESS_ASSETS_FOLDER
    smileyImg = Image.open(Path(PROCESS_ASSETS_FOLDER, "smiley.png"))
    smileyImg = smileyImg.convert('1')
    MAX7219.display(smileyImg)

def CB_interrupt(channel):
    global COINS, WAITFORSTART
    #Calc signal duration
    startMillis = time.monotonic()
    endMillis = startMillis
    while GPIO.input(CB_PIN):
        endMillis = time.monotonic()
    startMillis = startMillis * 1000
    endMillis = endMillis * 1000
    logging.debug("CB duration=")
    logging.debug(endMillis - startMillis)
    if endMillis - startMillis > 85 and endMillis - startMillis < 115:
        WAITFORSTART = True
        COINS = 0
        showArrow()

def coin_interrupt(channel):
    global COINS, COINS_MULTI, START, WAITFORSTART, TM1637
    
    COINS = COINS - COINS_MULTI
    
    if COINS <= 0:
        WAITFORSTART = True
        COINS = 0
        showArrow()
    
        
def start_interrupt(channel):
    global START, WAITFORSTART
    if WAITFORSTART :
        START = True
        
    
def initPhotobooth():
    logging.info("initPhotobooth")
    global CAMERA, MAX7219, TM1637
    
    logging.info("initGPIO")
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(COIN_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(START_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.setup(CB_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.setup(AUX_PIN, GPIO.OUT)
    GPIO.output(AUX_PIN, False)
    GPIO.add_event_detect(COIN_PIN, GPIO.FALLING, callback=coin_interrupt)
    GPIO.add_event_detect(START_PIN, GPIO.RISING, callback=start_interrupt)
    GPIO.add_event_detect(CB_PIN, GPIO.RISING, callback=CB_interrupt)
    
    #7 segment
    logging.info("initSegment")
    TM1637 = tm1637.TM1637(clk=15, dio=18)
    TM1637.brightness(1)
    TM1637.show(str("    "), colon=True)
    TM1637.show(" " + str(PRICE), colon=True)
    
    #led matrix
    logging.info("initLedMatrix")
    serial = spi(port=0, device=0, gpio=noop())
    MAX7219 = max7219(serial)

    # init camera
    CAMERA = init_camera()
    
    #init config
    initConfig()
    
def initConfig():
    logging.info("initConfig")
    global START, WAITFORSTART, PRICE
    global config, CURRENT_PATH, USB_STICK, BKPIMG, BKP_PATH, PHOTO_COUNT,PHOTO_PAUSE,VERTICAL, PROCESS_ASSETS_FOLDER
    global CAPTURE_FOLDER, PROCESS_FILE_BACKGROUND, PROCESS_FILE_MASK, ADD_LOGO,PROCESS_FILE_LOGO1, PROCESS_FILE_LOGO2
    global LOGO1_POS, LOGO2_POS, PROCESS_FILE_MARGIN, PRINT, MARGIN, IA, api
    
    #config json
    parser = argparse.ArgumentParser(description="Read config file path")
    parser.add_argument(
        "--config",
        type=str,
        default=Path(CURRENT_PATH, "config.json"),
        help="Path to the configuration file"
    )
    args = parser.parse_args()

    with open(args.config, "r") as f:
        config = json.load(f)

    USB_STICK = config["usb_stick"]  # use of usb storage
    if USB_STICK:
        CURRENT_PATH = os.path.abspath(config["usb_stick_adr"])
        
    BKPIMG = config["bkpimg"]  # store img in a folder.
    if BKPIMG:
        BKP_PATH = os.path.abspath(config["bkp_path"])


    PHOTO_COUNT = config["photo_count"]  # number of photos to take
    PHOTO_PAUSE = config["photo_pause"]  # in seconds
    VERTICAL = config["vertical"]  # strip ÃÂÃÂ  la verticale

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
        PROCESS_FILE_MASK = Image.open(Path(PROCESS_ASSETS_FOLDER, "maskVertical.jpg"))
    except FileNotFoundError:
        PROCESS_FILE_MASK = Image.new("RGB", (875, 1150), color="white")
        PROCESS_FILE_MASK.save(Path(PROCESS_ASSETS_FOLDER, "mask.jpg"))

    # Create logo image if it doesn't exist
    ADD_LOGO = config["add_logo"]
    if ADD_LOGO:
        LOGO1_NAME = config["logo1_name"]
        LOGO2_NAME = config["logo2_name"]
        LOGO1_POS = config["logo1_pos"]
        LOGO2_POS = config["logo2_pos"]
        try:
            PROCESS_FILE_LOGO1 = Image.open(Path(PROCESS_ASSETS_FOLDER, LOGO1_NAME))
            PROCESS_FILE_LOGO2 = Image.open(Path(PROCESS_ASSETS_FOLDER, LOGO2_NAME))
            if VERTICAL:
                PROCESS_FILE_LOGO1 = PROCESS_FILE_LOGO1.rotate(90, expand=True)
                PROCESS_FILE_LOGO2 = PROCESS_FILE_LOGO2.rotate(90, expand=True)
        except FileNotFoundError:
            PROCESS_FILE_LOGO1 = Image.new("RGB", (1, 1), color="white")
            PROCESS_FILE_LOGO1.save(Path(PROCESS_ASSETS_FOLDER, "logo1.png"))
            PROCESS_FILE_LOGO2 = Image.new("RGB", (1, 1), color="white")
            PROCESS_FILE_LOGO2.save(Path(PROCESS_ASSETS_FOLDER, "logo2.png"))

    # Final image for print (dnp ds 40 eat the borders / fond perdu)
    try:
        PROCESS_FILE_MARGIN = Image.open(Path(PROCESS_ASSETS_FOLDER, "margin.jpg"))
    except FileNotFoundError:
        PROCESS_FILE_MARGIN = Image.new("RGB", (3700, 2500), color="white")
        PROCESS_FILE_MARGIN.save(Path(PROCESS_ASSETS_FOLDER, "margin.png"))

    PRINT = config["print"]
    MARGIN = config["margin"]

    #Api serveur IA
    IA = config["ia"]
    if IA:
        logging.info("connexion serveur IA")
        time.sleep(10)
        api = webuiapi.WebUIApi()

        # create API client with custom host, port
        api = webuiapi.WebUIApi(host='uncanny.taile7da6.ts.net', port=7860, sampler = "Euler a")
        logging.info("Serveur IA OK")

    WAITFORSTART = PRICE == 0

    if WAITFORSTART:
        showArrow()
    else:
        showSmiley()
        
    
def main():

    global START, WAITFORSTART, COINS, CAMERA, MAX7219, TM1637, IA
    
    lastRefresh = time.time()
    
    # Boucle de la mort
    while True:
        
        #refresh Segment
        currTime = time.time()
        if currTime - lastRefresh >= 0.5:
            TM1637.show(" " + str(COINS), colon=True)
            lastRefresh = currTime
        
        if START:
            logging.info("Start sequence")
            GPIO.output(AUX_PIN, True)
            TM1637.show("BUSY", colon=False)
            capture_uuid = capture(CAMERA)
            
            startIA = time.time()
            
            if IA:
                logging.info("Process:" + str(threading.active_count()))
                logging.info("wait for IA")
                while threading.active_count() > 1:
                    time.sleep(1) 

            output = capture_to_montage(capture_uuid, IA)
            
            if PRINT:
                print_image(capture_uuid)
            logging.info("Done: %s seconds ---" % (time.time() - startIA))

            GPIO.output(AUX_PIN, False)

            #Re init
            START = False
            WAITFORSTART = PRICE == 0
            COINS = PRICE
            if WAITFORSTART:
                showArrow()
            else:
                showSmiley()
            
    return 0


if __name__ == "__main__":
    print("START")
    initPhotobooth()
    main()
    GPIO.cleanup()
    logging.info("Stop")



