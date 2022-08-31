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
gameMode = True #Control if camera is moved with WASD or through direct commands

print(clear)

cam = Controller()

imap = {
    #Keyboard shortcuts
    "w" : lambda x : cam.steer("up"),
    "s" : lambda x : cam.steer("down"),
    "a" : lambda x : cam.steer("left"),
    "d" : lambda x : cam.steer("right"),
    "c" : lambda x : cam.reset(),
    "q" : lambda x : cam.zoomFocus("zoom", "in"),
    "e" : lambda x : cam.zoomFocus("zoom", "out"),
    "z" : lambda x : cam.zoomFocus("focus", "near"),
    "x" : lambda x : cam.zoomFocus("zoom", "far"),
    "f" : lambda x : cam.flip("toggle"),
    "m" : lambda x : cam.mirror("toggle"),
    "b" : lambda x : cam.backlight("toggle"),
    #Direct commands
    "vid_format" : lambda x : cam.vid_format(x),
    "wb_auto" : lambda x : cam.wb_auto(x),
    "ae_auto" : lambda x : cam.ae_auto(x),
    "gamma_auto" : lambda x : cam.gamma_auto(x),
    "mm_detect" : lambda x : cam.mm_detect(x),
    "zf" : lambda x : cam.zoomFocus_direct(x),
    "focus_auto" : lambda x : cam.focus_auto(x),
    "pt" : lambda x : cam.pt_direct(x),
    "ptzf" : lambda x : cam.ptzf(x),
    #Queries
    "q_camid" : lambda x : cam.Q_camID(),
    "q_z" : lambda x : cam.Q_zoomPos(),
    "q_fPos" : lambda x : cam.Q_focusPos(),
    "q_fMode" : lambda x : cam.Q_focusMode(),
    "q_pt" : lambda x : cam.Q_ptPos(),
}

port = input("Enter port to connect:")
if(cam.connect(port)):
    run = False #Exit since connect failed
    print("Connection to port: FAILED")

while run:
    print(clear)
    print("Enter mode: Game(+) / Type(-)\nPress 0 to Quit")

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
            inp = [0,0]
            cmd = keyboard.read_key()
        else:
            inp = input(">>").split(' ')
            cmd = inp[0]

        #Process input
        if cmd in imap:
            imap[cmd](inp[1:])

        #Escape to mode choice / quit
        if(cmd == "Esc" or cmd == 'esc'):
            break
        elif(inp == "0"):
            cam.disconnect()
            exit()
        
        sleep(0.1)  #To ensure keyboard presses are not excessive
print("Exiting...")
