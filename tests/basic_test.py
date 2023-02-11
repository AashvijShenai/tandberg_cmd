import os
import sys

sys.path.append("../tandberg/")
from tandberg import tandberg as td
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

cam = td.Controller()

imap = {
    #Keyboard shortcuts
    "w" : lambda x : cam.steer(["up"]),
    "s" : lambda x : cam.steer(["down"]),
    "a" : lambda x : cam.steer(["left"]),
    "d" : lambda x : cam.steer(["right"]),
    "c" : lambda x : cam.clear(),
    "r" : lambda x : cam.reset(),
    "q" : lambda x : cam.zoomFocus(["zoom", "in"]),
    "e" : lambda x : cam.zoomFocus(["zoom", "out"]),
    "z" : lambda x : cam.zoomFocus(["focus", "near"]),
    "x" : lambda x : cam.zoomFocus(["focus", "far"]),
    "f" : lambda x : cam.flip(["toggle"]),
    "m" : lambda x : cam.mirror(["toggle"]),
    "b" : lambda x : cam.backlight(["toggle"]),
    #Direct commands
    "stop"          : lambda x : cam.steer(["stop"]),
    "clear"         : lambda x : cam.clear(),
    "address_set"   : lambda x : cam.address_set(),
    "power"         : lambda x : cam.power(x),
    "vid_format"    : lambda x : cam.vid_format(x),
    "wb_auto"       : lambda x : cam.wb_auto(x),
    "ae_auto"       : lambda x : cam.ae_auto(x),
    "backlight"     : lambda x : cam.backlight(x),
    "mirror"        : lambda x : cam.mirror(x),
    "flip"          : lambda x : cam.flip(x),
    "gamma_auto"    : lambda x : cam.gamma_auto(x),
    "mm_detect"     : lambda x : cam.mm_detect(x),
    "call_led"      : lambda x : cam.call_led(x),
    "pwr_led"       : lambda x : cam.pwr_led(x),
    "bestView"      : lambda x : cam.bestView(x),
    "zoomSpeed"     : lambda x : cam.setZoomSpeed(x),
    "focusSpeed"    : lambda x : cam.setFocusSpeed(x),
    "zf"            : lambda x : cam.zoomFocus_direct(x),
    "focus_auto"    : lambda x : cam.focus_auto(x),
    "reset"         : lambda x : cam.reset(),
    "reboot"        : lambda x : cam.reboot(),
    "pt"            : lambda x : cam.pt_direct(x),
    "ptzf"          : lambda x : cam.ptzf(x),
    #Queries
    "query"         : lambda x : cam.qCmd(x),
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
        if(gameMode):
            inp = [0,0]
            cmd = keyboard.read_key()
        else:
            inp = input(">>").split(' ')
            cmd = inp[0]

        #Process input
        if cmd in imap:
            imap[cmd](inp[1:])
        elif cmd == '+':
            gameMode = True
        elif cmd == '-':
            gameMode = False
        #Escape to mode choice / quit
        if(cmd == "Esc" or cmd == 'esc'):
            break
        elif cmd == "0":
            cam.disconnect()
            exit()
        
        sleep(0.1)  #To ensure keyboard presses are not excessive
print("Exiting...")
