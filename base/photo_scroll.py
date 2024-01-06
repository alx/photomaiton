# SensÃ© afficher la derniÃ©re image d'un rÃ©pertoire et supprimer les autres.
# Merci Chatgpt.

import os
import time
import pi3d
from PIL import Image

# RÃ©pertoire d'images et taille de l'Ã©cran
image_directory = '/home/minutepapillons/BkpImg/Dada'
screen_width = 800 #1920
screen_height = 600 #1080

def get_image_list(directory):
    image_list = sorted(os.listdir(directory), key=lambda x: os.path.getmtime(os.path.join(directory, x)), reverse=True)
    return [os.path.join(directory, image) for image in image_list]

def remove_old_images(directory):
    image_list = get_image_list(directory)
    
    # Conserver seulement la derniÃ¨re image
    for i in range(1, len(image_list)):
        os.remove(image_list[i])

# Initialisation de l'affichage
display = pi3d.Display.create(w=screen_width, h=screen_height, background=(0, 0, 0, 255))

# CrÃ©ation de l'image sprite avec dimensions adaptÃ©es
def create_image_sprite(image_path, screen_width, screen_height):
    image = Image.open(image_path)
    #image.thumbnail((screen_width, screen_height))
    w, h = image.size
    print(w)
    print(h)
    x_pos = (screen_width - w) / 2
    y_pos = (screen_height - h) / 2
    image_texture = pi3d.Texture(image_path)
    shader = pi3d.Shader("uv_flat")
    return pi3d.ImageSprite(image_texture, w=w, h=h, x=0, y=0, z=5, shader=shader)


# Boucle principale
keyboard = pi3d.Keyboard()
while display.loop_running():

    if keyboard.read() == ord('q'):  # Vérifie si la touche pressée est 'q'
        display.destroy()  # Quitte le mode plein écran et détruit la fenêtre
        break
    
    # Suppression des anciennes images Ã  chaque boucle principale
    remove_old_images(image_directory)
    
    # RÃ©cupÃ©ration de la liste des images
    image_list = get_image_list(image_directory)

    # Chargement de l'image la plus rÃ©cente
    image_path = image_list[0]
    print(image_path)
    image_sprite = create_image_sprite(image_path, screen_width, screen_height)

    display.clear()

    # Affichage de l'image
    image_sprite.draw()

    # Attente de 5 secondes avant de passer Ã  la prochaine boucle
    time.sleep(5)

keyboard.close()

