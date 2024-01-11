# SensÃ© afficher la derniÃ©re image d'un rÃ©pertoire et supprimer les autres.
# Merci Chatgpt.

import os
import time
import cv2
import numpy as np
from PIL import Image

# Répertoire d'images et taille de l'écran
image_directory = '/home/minutepapillons/BkpImg/Dada'
screen_width = 1280
screen_height = 720


def get_image_list(directory):
    image_list = sorted(os.listdir(directory), key=lambda x: os.path.getmtime(os.path.join(directory, x)), reverse=True)
    return [os.path.join(directory, image) for image in image_list]

def remove_old_images(directory):
    image_list = get_image_list(directory)
    
    # Supprimer toutes les images sauf la plus récente
    for i in range(1, len(image_list)):
        os.remove(image_list[i])

# Création de la fenêtre d'affichage
cv2.namedWindow("La Voix de son Maître", cv2.WND_PROP_FULLSCREEN)
#cv2.resizeWindow("La Voix de son Maître", screen_width, screen_height)
cv2.setWindowProperty("La Voix de son Maître", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)


# Boucle principale
while True:
    # Suppression des anciennes images à chaque boucle principale
    #remove_old_images(image_directory)
    
    # Récupération de la liste des images
    image_list = get_image_list(image_directory)

    # Charger la nouvelle image la plus récente
    if len(image_list) > 0:
        image_path = image_list[0]

        # Création d'une image noire pour le fond
        image = Image.open(image_path)
        #image = image.rotate(-90)
        background = Image.new("RGB", (screen_width, screen_height), color="black")
        background.paste(image, (50, 0))
        background.save(image_path, quality=95)

        image = cv2.imread(image_path)
        cv2.imshow("La Voix de son Maître", image)

        key = cv2.waitKey(5000)
        if key == ord('q'):
            break
    

        
    # Attente de 5 secondes avant de passer à la prochaine image
    #cv2.waitKey(5000)
    if len(image_list) > 1:
       os.remove(image_list[0])

cv2.destroyAllWindows() 
