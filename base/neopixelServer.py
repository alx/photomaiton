import board
import neopixel
from multiprocessing.connection import Listener

strip = neopixel.NeoPixel(board.D12, 169, pixel_order=neopixel.RGB)
strip.auto_write = False
strip.fill((0, 0, 0))
strip.show()

listener = Listener(('localhost', 6000), authkey=b'neopixel')
running = True
print("Neopixel server running")

while running:
    conn = listener.accept()
    print('connection accepted from', listener.last_accepted)
    while True:
        msg = conn.recv()
        
        #clear strip
        strip.fill((0, 0, 0))

        # Blue or red pill
        bClassic = msg[0]
        for i in range(40):
            strip[i] = (0, 255 if not bClassic else 0, 255 if bClassic else 0)

        for i in range(65,102):
            strip[i] = (0, 255 if not bClassic else 0, 255 if bClassic else 0)
        
        for i in range(51,54):
            strip[i] = (0, 255 if not bClassic else 0, 255 if bClassic else 0)
        
        for i in range(113, 116):
            strip[i] = (0, 255 if not bClassic else 0, 255 if bClassic else 0)
        
        for i in range(127, 169):
            strip[i] = (0, 255 if not bClassic else 0, 255 if bClassic else 0)

        # Refresh infos panel
        pose1 = msg[1]
        pose2 = msg[2]
        pose3 = msg[3]
        pose4 = msg[4]
        #print("bClassic",bClassic,"1: ", pose1, "2: ", pose2,"3:",pose3,"4:",pose4)
        
        if not bClassic:
            #print("iamode")
            # Pose 4
            strip[40 + pose4] = (0, 255, 0)

            # Pose 2
            strip[54 + pose3] = (0, 255, 0)

            # Pose 1
            strip[112 - pose1] = (0, 255, 0)

            # Pose 3
            strip[126 - pose2] = (0, 255, 0)

        strip.show()

listener.close()
