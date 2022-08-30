import os
from controller import *
import keyboard
from time import sleep

class clear(object):
    def __repr__(self):
        os.system('cls' if os.name == 'nt' else 'clear')
        return ''

clear = clear() #Printing 'clear' clears the screen

#########MAIN############
run = True
gameMode = True #Control if camera is moved with WASD or through typed commands

print(clear)

cam = Controller()


port = input("Enter port to connect:")
if(cam.connect(port)):
    run = False #Exit since connect dailed
    print("Connection to port: FAILED")

while run:
    print(clear)
    
    print("Enter mode: Game(+) / Type(-)")
    print("Press 0 to Quit")

    while True:
        if(keyboard.is_pressed("+")):
            gameMode = True
            break
        elif(keyboard.is_pressed("-")):
            gameMode = False
            break
        elif(keyboard.is_pressed("0")):
            cam.disconnect()
            exit()

    while True:
        print(clear)

        if(gameMode):
            inp = keyboard.read_key()

            #Escape to mode choice / quit
            if(inp == "Esc" or inp == 'esc'):
                break
            elif(inp == "0"):
                cam.disconnect()
                exit()
    
            #Steer
            elif(inp == "w"):         #Up
                cam.steer("up")
            elif(inp == "s"):       #Down
                cam.steer("down")
            elif(inp == "a"):       #Left
                cam.steer("left")
            elif(inp == "d"):       #Right
                cam.steer("right")
            elif(inp == "c"):       #Center
                cam.reset()
    
            #Zoom
            elif(inp == "q"):       #Zoom in
                cam.zoomFocus("zoom", "in")
            elif(inp == "e"):       #Zoom out
                cam.zoomFocus("zoom", "out")
    
            #Focus
            elif(inp == "z"):       #Focus near
                cam.zoomFocus("focus", "near")
            elif(inp == "x"):       #Focus far
                cam.zoomFocus("zoom", "far")
    
            elif(inp == "f"):       #Flip
                cam.flip("toggle")
            elif(inp == "m"):       #Mirror
                cam.mirror("toggle")
            elif(inp == "b"):       #Backlight compensation
                cam.mirror("toggle")
    
            sleep(0.1)  #To ensure keyboard presses are not excessive
    
    
        else:
            inp = input(">>").split(' ')

            #Escape to mode choice / quit
            if(inp[0] == "Esc"):
                break
            elif(inp[0] == "0"):
                cam.disconnect()
                exit()

            elif(inp[0] == "vid_format"):
                cam.vid_format(inp[1])

            elif(inp[0] == "wb_auto"):
                if(len(inp) == 2):
                    cam.wb_auto(inp[1])
                else:
                    cam.wb_auto(inp[1], int(inp[2]))

            elif(inp[0] == "ae_auto"):
                if(len(inp) == 2):
                    cam.ae_auto(inp[1])
                else:
                    cam.ae_auto(inp[1], int(inp[2]), int(inp[3]))

            elif(inp[0] == "gamma_auto"):
                if(len(inp) == 2):
                    cam.gamma_auto(inp[1])
                else:
                    cam.gamma_auto(inp[1], int(inp[2]))

            elif(inp[0] == "mm_detect"):
                cam.mm_detect(inp[1])

            elif(inp[0] == "zf"):
                cam.zoomFocus_direct(int(inp[1]), int(inp[2]))

            elif(inp[0] == "focus_auto"):
                cam.focus_auto(inp[1])

            elif(inp[0] == "pt"):
                cam.pt_direct(int(inp[1]), int(inp[2]))

            elif(inp[0] == "ptzf"):
                cam.ptzf(int(inp[1]), int(inp[2]), int(inp[3]), int(inp[4]))
