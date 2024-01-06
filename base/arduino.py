import serial
from serial.tools import list_ports
import logging
import os
from pathlib import Path

CURRENT_PATH = os.path.dirname(os.path.abspath(__file__))

LOG_FILENAME = Path(CURRENT_PATH, "arduino.log")
logging.basicConfig(
    format="%(asctime)s %(levelname)s %(message)s",
    filename=LOG_FILENAME,
    level=logging.DEBUG,
    datefmt="%Y-%m-%d %H:%M:%S",
)

def connect_to_arduino():
    def find_arduino_port():
        # Obtient la liste des ports série disponibles
        available_ports = list_ports.comports()

        # Itère sur la liste des ports
        for port in available_ports:
            try:
                # Teste la liaison série pour le port actuel
                SERIAL = serial.Serial(port.device, 9600, timeout=1)
                SERIAL.reset_input_buffer()
                # Si la liaison série est réussie, retourne le port
                return port.device
            except:
                logging.debug("Error serial arduino {0}".format(port.device))

        # Retourne None si aucun port n'a été trouvé
        return None

    # Utilise la fonction pour trouver le port série
    arduino_port = find_arduino_port()

    if arduino_port:
        try:
            SERIAL = serial.Serial(arduino_port, 9600, timeout=1)
            SERIAL.reset_input_buffer()
            # Effectue d'autres opérations avec la liaison série établie
            return SERIAL
        except:
            logging.debug("Error connecting to Arduino")
            return None
    else:
        logging.debug("No Arduino port found")
        return None