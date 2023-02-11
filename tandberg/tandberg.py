import serial
import logging
import time
from serial.tools import list_ports

stat_OK = 0
stat_FAIL = 1

# Tandberg PrecisionHD 1080p supports:
# Pan : -90 to +90 deg : 0-816 values   # value = deg*4.533 + 408
# Tilt : -25 to +15 deg : 7-212 values  # value = deg*5.125 + 135.125
# Zoom : 0-2850 values ?

# Important note: The response to commands depends on the camera's mood.
# It can decide that it doesnt want to move away from a particular spot. 
# Reboot in this case.

class Controller(object):
    def __init__(self):
        # Might want to be able to change this in the future to support
        # multiple cameras. 0x81 means "from 0 to 1" due to some weird
        # fixed bits in the VISCA spec. Assumption is that controller (us)
        # is 0 and camera is 1, which is the case at camera bootup until it's
        # told otherwise.
        self.address        = b'\x81'

        #Speeds
        self.panSpeed       = b'\x0f' #Range 0x01-0x0f
        self.tiltSpeed      = b'\x0f'
        self.panSpeedMax    = b'\x0f'
        self.tiltSpeedMax   = b'\x0f'
        self.zoomSpeed      = 10    #10 = low , 11 = high
        self.focusSpeed     = 11    #11 = low, 11 = high

        #The communication port
        self.port           = None
        self.ser            = None

        self.flipState       = False
        self.mirrorState     = False
        self.backlightState  = False

    def connect(self, inp):
        #9600 baud, 8N1, no flow control.
        interface   = inp
        status      = 0
        try:
            self.ser = serial.Serial(interface, timeout=20)
            self.interface = interface
        except Exception as error:
            print("Exception when connecting to device.")
            self.interface = None
            status = 1
        return status

    def disconnect(self):
        status = 0
        try:
            if(self.ser != None):
                self.ser.close()
                self.interface = None

        except Exception as error:
            print("Exception when disconnecting to device.")
            status = 1
        return status

    def clear(self):
        #TODO: FIX
        """Stops any current operation"""
        msg     = b'\x01\x00\x01'
        status  = self.send(msg)

        if(status != stat_OK):
            print("Clear : FAILED")
        return status

    def address_set(self, inp):
        """Sets address of camera """
        address = int(inp[0])
        #If broadcast i.e \x81, increase address with 1 before sending to chain
        #Assuming address 0-9. ?Is A-F allowed
        msg = b'\x30'
        msg += address.to_bytes(1,'big')
        status = self.send(msg)

        if(status != stat_OK):
            print("SetAddress : FAILED")
        return status

    def power(self, inp):
        #The command doesnt power on/off the camera. Only reset motors
        cmd = inp[0]
        lookup = {
            'on' : b'\x01\x04\x00\x02',
            'off': b'\x01\x04\x00\x03',
        }
        status = self.send(lookup[cmd])

        if(status != stat_OK):
            print("Power status : FAILED")
        return status

    def vid_format(self, inp):
        """Sets the video format"""
        cmd = inp[0]
        #Only functions if the video mode DIP is set to SW
        #If DIP is changed during runtime, camera must be rebooted
        lookup = {
            "1080p25"   : b'\x00',
            "1080p30"   : b'\x01',
            "1080p50"   : b'\x02',
            "1080p60"   : b'\x03',
            "720p25"    : b'\x04',
            "720p30"    : b'\x05',
            "720p50"    : b'\x06',
            "720p60"    : b'\x07'
        }

        msg = b'\x01\x35\x00'
        msg += lookup[cmd]
        msg += b'\x00'  #Used in PrecisionHD 720p camera

        status = self.send(msg)

        if(status != stat_OK):
            print("Video format status : FAILED")
        return status

    def wb_auto(self, inp):
        """Sets White balance to auto/manual and to value if manual"""
        cmd = inp[0]
        lookup = {
            'on' : b'\x01\x04\x35\x00',
            'off': b'\x01\x04\x35\x06',
        }

        if(cmd == 'off'):
            #Update table index before switching to manual mode
            msg = b'\x01\x04\x75' + self.__toVisca2b(int(inp[1]))
            status = self.send(msg)

            if(status != stat_OK):
                print("Update WB Table status : FAILED")

        status = self.send(lookup[cmd])

        if(status != stat_OK):
            print("WB status : FAILED")
        return status

    def ae_auto(self, inp):
        """Sets Auto Exposure to auto/manual and to value if manual"""
        cmd = inp[0]

        lookup = {
            'on' : b'\x01\x04\x39\x00',
            'off': b'\x01\x04\x39\x03',
        }

        if(cmd == 'off'):
            #Update iris position before switching to manual mode, range = 0..50
            msg = b'\x01\x04\x4B' + self.__toVisca2b(int(inp[1]))
            status = self.send(msg)

            if(status != stat_OK):
                print("Update iris status : FAILED")

            #Update gain position before switching to manual mode, range = 12-21 dB
            msg = b'\x01\x04\x4C' + self.__toVisca2b(int(inp[2]))
            status = self.send(msg)

            if(status != stat_OK):
                print("Update gain status : FAILED")

        status = self.send(lookup[cmd])

        if(status != stat_OK):
            print("AE status : FAILED")
        return status

    def backlight(self, inp):
        """Turns backlight compensation on or off"""
        cmd = inp[0]
        lookup = {
            'on' : b'\x01\x04\x33\x02',
            'off': b'\x01\x04\x33\x03',
        }

        if(cmd == "toggle"):
            if(self.backlightState == False):
                self.backlightState = True
                cmd = "on"
            else:
                self.backlightState = False
                cmd = "off"

        status = self.send(lookup[cmd])

        if(status != stat_OK):
            print("Backlight status : FAILED")
        return status

    def mirror(self, inp):
        """Turns mirror on or off"""
        cmd = inp[0]
        lookup = {
            'on' : b'\x01\x04\x61\x02',
            'off': b'\x01\x04\x61\x03',
        }

        if(cmd == "toggle"):
            if(self.mirrorState == False):
                self.mirrorState = True
                cmd = "on"
            else:
                self.mirrorState = False
                cmd = "off"

        status = self.send(lookup[cmd])

        if(status != stat_OK):
            print("Mirror status : FAILED")
        return status

    def flip(self, inp):
        """Turns flip on or off"""
        cmd = inp[0]
        lookup = {
            'on' : b'\x01\x04\x66\x02',
            'off': b'\x01\x04\x66\x03',
        }

        if(cmd == "toggle"):
            if(self.flipState == False):
                self.flipState = True
                cmd = "on"
            else:
                self.flipState = False
                cmd = "off"

        status = self.send(lookup[cmd])

        if(status != stat_OK):
            print("Flip status : FAILED")
        return status

    def gamma_auto(self, inp):
        """Sets Gamma to auto/manual and to value if manual"""
        cmd = inp[0]
        # Default - table 4
        lookup = {
            'on' : b'\x01\x04\x51\x02',
            'off': b'\x01\x04\x51\x03',
        }

        if(cmd == 'off'):
            #Update table before switching to manual mode range = 0..7
            msg = b'\x01\x04\x52' + self.__toVisca2b(int(inp[1]))
            status = self.send(msg)

            if(status != stat_OK):
                print("Update Gamma Table status : FAILED")

        status = self.send(lookup[cmd])

        if(status != stat_OK):
            print("Gamma status : FAILED")
        return status

    def mm_detect(self, inp):
        # Works irregularly
        """Turns Motor moved detection on or off"""
        cmd = inp[0]
        #Camera recalibrates if MMD is on and is touched
        lookup = {
            'on' : b'\x01\x50\x30\x01',
            'off': b'\x01\x50\x30\x00',
        }

        status = self.send(lookup[cmd])

        if(status != stat_OK):
            print("MM status : FAILED")
        return status

    def call_led(self, inp):
        """Turns call LED on or off"""
        cmd = inp[0]
        lookup = {
            'on' : b'\x01\x33\x01\x01',
            'off': b'\x01\x33\x01\x00',
            'blink': b'\x01\x33\x01\x02',
        }

        status = self.send(lookup[cmd])

        if(status != stat_OK):
            print("Call LED status : FAILED")
        return status

    def pwr_led(self, inp):
        cmd = inp[0]
        """Turns power LED on or off"""
        lookup = {
            'on' : b'\x01\x33\x02\x01',
            'off': b'\x01\x33\x02\x00',
        }

        status = self.send(lookup[cmd])

        if(status != stat_OK):
            print("Power LED status : FAILED")
        return status

    def bestView(self, inp):
        # Untested
        """Turns Best View on or off"""
        cmd     = inp[0]
        time    = int(inp[1])
        #time < 100s
        #time = 0 stops operation
        msg = b'\x01\x50\x60'
        temp = int(time/10)
        msg += temp.to_bytes(1,"big")
        temp = time%10
        msg += temp.to_bytes(1,"big")

        status = self.send(msg)

        if(status != stat_OK):
            print("Best view status : FAILED")
        return status

    def setZoomSpeed(self, inp):
        cmd = inp[0]
        if(cmd == "high"):
            self.zoomSpeed = 11
        else:
            self.zoomSpeed = 10

    def setFocusSpeed(self, inp):
        cmd = inp[0]
        if(cmd == "high"):
            self.focusSpeed = 11
        else:
            self.focusSpeed = 10

    def zoomFocus(self, inp):
        """Sets the Zoom/Focus"""
        fn  = inp[0]
        cmd = inp[1]
        msg = b'\x01\x04'

        speed = self.zoomSpeed
        if(fn == "zoom"):
            msg+= b'\x07'
        elif(fn == "focus"):
            msg += b'\x08'
            speed = self.focusSpeed

        if(cmd == "stop"):
            temp = 0
        elif(cmd == "in" or cmd == "far"):
            temp = 32 + speed   #32 - 0x20
        elif(cmd == "out" or cmd == "near"):
            temp = 48 + speed   #48 - 0x30
        msg += temp.to_bytes(1,"big")

        status = self.send(msg)

        if(status != stat_OK):
            print("Zoom/Focus status : FAILED")
        return status

    def zoomFocus_direct(self, inp):
        # Fails but ptzf works so use that directly
        zoom    = int(inp[0])
        focus   = int(inp[1])
        print(zoom, focus)
        """Sets Zoom/Focus to specified position directly"""
        #Set zoom/focus arguments to -1 if functions are not used
        #Zoom/Focus = PQRS, not sure what these stand for

        msg = b'\x01\x04'
        if(zoom == -1 and focus != -1):
            msg += b'\x48'
            msg += self.__toVisca2b(focus)

        elif(zoom != -1):
            msg += b'\x47'
            msg += self.__toVisca2b(zoom)
            if(focus != -1):
                msg += self.__toVisca2b(focus)

        status = self.send(msg)

        if(status != stat_OK):
            print("Zoom/Focus direct status : FAILED")
        return status

    def focus_auto(self, inp):
        cmd = inp[0]
        """Turns autofocus on or off"""
        lookup = {
            'on': b'\x01\x04\x38\x02',
            'off': b'\x01\x04\x38\x03',
        }

        status = self.send(lookup[cmd])

        if(status != stat_OK):
            print("Auto focus status : FAILED")
        return status

    def steer(self, inp):
        """Steer in a direction"""
        cmd = inp[0]
        #Stop is not added
        lookup = {
            'up'        : b'\x03\x01',
            'down'      : b'\x03\x02',
            'left'      : b'\x01\x03',
            'right'     : b'\x02\x03',
            'upleft'    : b'\x01\x01',
            'upright'   : b'\x02\x01',
            'downleft'  : b'\x01\x02',
            'downright' : b'\x02\x02',
            'stop'      : b'\x03\x03',
        }
        msg = b'\x01\x06\x01'
        if(cmd != 'stop'):
            msg += self.panSpeed
            msg += self.tiltSpeed
        else:
            msg += b'\x03\x03'
        msg += lookup[cmd]

        status = self.send(msg)

        if(status != stat_OK):
            print("Operation status : FAILED")
        return status

    def reset(self):
        """Resets the motors only"""
        msg = b'\x01\x06\x05'
        status = self.send(msg)

        if(status != stat_OK):
            print("Reset motor status : FAILED")
        return status

    def reboot(self):
        """Reboots the camera"""
        #Resets serial to 9600 baud
        msg = b'\x01\x42'
        status = self.send(msg)

        if(status != stat_OK):
            print("Reboot status : FAILED")
        return status

    def pt_direct(self, inp):
        """Sets Pan/Tilt directly to positions"""
        pan     = int(inp[0])
        tilt    = int(inp[1])

        msg = b'\x01\x06\x02'
        msg += self.panSpeed
        msg += self.tiltSpeed
        msg += self.__toVisca2b(pan)
        msg += self.__toVisca2b(tilt)

        status = self.send(msg)

        if(status != stat_OK):
            print("PT direct status : FAILED")

    def ptzf(self, inp):
        # Focus cannot be controlled if auto focus is disabled
        # But focus cannot be controlled if auto focus is enabled
        """Sets all motors directly to positions in one operation"""
        pan     = int(inp[0])
        tilt    = int(inp[1])
        zoom    = int(inp[2])
        focus   = int(inp[3])

        msg = b'\x01\x06\x20'
        msg += self.__toVisca2b(pan)
        msg += self.__toVisca2b(tilt)
        msg += self.__toVisca2b(zoom)
        msg += self.__toVisca2b(focus)

        status = self.send(msg)

        if(status != stat_OK):
            print("PTZF direct status : FAILED")
        return status

    def serialSpeed(self, inp):
        """Update serial communication speed"""
        speed = inp[0]
        #Requires a delay of 20s before next command
        #9600 baud/115200 baud
        lookup = {
            9600 : b'\x01\x34\x00',
            115200 : b'\x01\x34\x01'
        }
        status = self.send(lookup[speed])

        if(status != stat_OK):
            print("Update serial speed status : FAILED")
        else:
            time.sleep(20)
        return status

    #Inquiry commands:
    def qCmd(self, inp):
        query = inp[0]
        print(query)
        qDict = {
            "q_camid"       : b'\x09\x04\x22',
            "q_zoompos"     : b'\x09\x04\x47',
            "q_fPos"        : b'\x09\x04\x48',
            "q_fMode"       : b'\x09\x04\x38',
            "q_pt"          : b'\x09\x06\x12',
            "q_pwr"         : b'\x09\x04\x00',
            "q_wbMode"      : b'\x09\x04\x35',
            "q_wbTable"     : b'\x09\x04\x75',
            "q_aeMode"      : b'\x09\x04\x39',
            "q_blacklight"  : b'\x09\x04\x33',
            "q_mirror"      : b'\x09\x04\x61',
            "q_flip"        : b'\x09\x04\x66',
            "q_gMode"       : b'\x09\x04\x51',
            "q_gTable"      : b'\x09\x04\x52',
            "q_callLed"     : b'\x09\x01\x33\x01',
            "q_pwrLed"      : b'\x09\x01\x33\x02',
            "q_vidSW"       : b'\x09\x06\x24',
            "q_alsRGain"    : b'\x09\x50\x50',
            "q_alsBGain"    : b'\x09\x50\x51',
            "q_alsGGain"    : b'\x09\x50\x52',
            "q_alsGGain"    : b'\x09\x50\x53',
            "q_bestView"    : b'\x09\x50\x60',
            "q_invert"      : b'\x09\x50\x70',
        }

        msg     = qDict[query]
        status  = self.send(msg)

        if(status != stat_OK):
            print("Query status : FAILED")
        return status

    def receive(self, query_stat):
        # TODO: Parse data nicely
        resp        = b''
        rcvd_byte   = None
        hex_str     = []
        while rcvd_byte != b'\xff':
            rcvd_byte = self.ser.read()
            resp += rcvd_byte
            hex_str.append(rcvd_byte.hex())

        # Strip off first byte (address) and last (terminator)
        # We leave the reponse as bytes instead of hex
        resp = resp[1:-1]

        if(query_stat == True):
            print(hex_str)

        error_stat = {
            1 : "Message length error (>14bytes)",
            2 : "Syntax error",
            3 : "Command buffer full",
            4 : "Command cancelled",
            5 : "No socket",
            65 : "Command not executable",
        }

        if(resp[0] != 80):  #\x50=80 decimal
            if(resp[0] != 96):  #\x60=96d
                print("Incorrect socket")
            else:
                print(error_stat[resp[1]])
            return 1
        return 0


    def send(self, cmd):
        """Sends a command to the camera and returns the success code"""
        if self.ser == None:
            return 1

        #Is command an inquiry?
        inq = False
        if(cmd[0] == 9):
            inq = True

        msg = self.address
        msg += cmd
        msg += b'\xff'

        #Write to camera
        self.ser.write(msg)

        status = self.receive(inq)
        return status


    @staticmethod
    def getPorts():
        """Gets a list of available serial ports"""
        ports = list_ports.comports()
        return [x.device for x in ports]

    @staticmethod
    def __toVisca2b(value):
        """Converts an integer to the weird VISCA 2-byte number representation, in hex for convenience."""
        # The VISCA format in question looks like 0i:0j:0k:0l where ijkl are
        # nibbles of the two-byte number.
        b = value.to_bytes(2, 'big')
        nib_1 = b[0] >> 4
        nib_2 = b[0] & 0x0f
        nib_3 = b[1] >> 4
        nib_4 = b[1] & 0x0f
        return bytes((nib_1, nib_2, nib_3, nib_4))