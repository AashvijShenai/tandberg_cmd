import serial
import logging
import time

stat_OK = 0
stat_FAIL = 1

class Controller(object):

    flipState = False
    mirrorState = False
    backlightState = False

    def __init__(self):
        # Might want to be able to change this in the future to support
        # multiple cameras. 0x81 means "from 0 to 1" due to some weird
        # fixed bits in the VISCA spec. Assumption is that controller (us)
        # is 0 and camera is 1, which is the case at camera bootup until it's
        # told otherwise.
        self.address = b'\x81'

        #Speeds
        self.panSpeed = b'\x01' #Range 1-9?
        self.tiltSpeed = b'\x01'
        self.panSpeedMax = b'\x01'
        self.tiltSpeedMax = b'\x01'

        self.zoomSpeed = 10 #10 = low , 11 = high
        self.focusSpeed = 11 #11 = low, 11 = high

        #The communication port
        self.port = None
        self.ser = None

    def connect(self, interface):
        #9600 baud, 8N1, no flow control.
        status = 0
        try:
            self.ser = serial.Serial(interface, timeout=5)
            self.interface = interface
        except Exception as error:
            log.exception("Exception when connecting to device.")
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
            log.exception("Exception when disconnecting to device.")
            status = 1
        return status

    def clear(self):
        """Stops any current operation"""
        msg = b'\x01\x00\x01'
        status = self.send(msg)

        if(status != stat_OK):
            print("Clear : FAILED")
        return status

    def address_set(self, address):
        """Sets address of camera """
        #If broadcast i.e \x81, increase address with 1 before sending to chain
        #Assuming address 0-9. ?Is A-F allowed
        msg = b'\x30'
        msg += address.to_bytes(1,'big')
        status = self.send(msg)

        if(status != stat_OK):
            print("SetAddress : FAILED")
        return status

    def power(self, cmd):
        #The command dont power on/off the camera. Only reset motors
        lookup = {
            'on' : b'\x01\x04\x00\x02',
            'off': b'\x01\x04\x00\x03',
        }
        status = self.send(lookup[cmd])

        if(status != stat_OK):
            print("Power status : FAILED")
        return status

    def vid_format(self, value):
        """Sets the video format"""
        #Only functions if the video mode DIP is set to SW
        #If DIP is changed during runtime, camera must be rebooted
        lookup = {
            "1080p25" : b'\x00',
            "1080p30" : b'\x01',
            "1080p50" : b'\x02',
            "1080p60" : b'\x03',
            "720p25" : b'\x04',
            "720p30" : b'\x05',
            "720p50" : b'\x06',
            "720p60" : b'\x07'
        }

        msg = b'\x01\x35\x00'
        msg += lookup[cmd]
        msg += b'\x00'  #Used in PrecisionHD 720p camera

        status = self.send(msg)

        if(status != stat_OK):
            print("Video format status : FAILED")
        return status

    def wb_auto(self, cmd, value=0):
        """Sets White balance to auto/manual and to value if manual"""
        lookup = {
            'on' : b'\x01\x04\x35\x00',
            'off': b'\x01\x04\x35\x06',
        }

        if(cmd == 'off'):
            #Update table index before switching to manual mode
            msg = b'\x01\x04\x75' + self.__toVisca2b(value)
            status = self.send(msg)

            if(status != stat_OK):
                print("Update WB Table status : FAILED")

        status = self.send(lookup[cmd])

        if(status != stat_OK):
            print("WB status : FAILED")
        return status

    def ae_auto(self, cmd, iris=0, gain=0):
        """Sets Auto Exposure to auto/manual and to value if manual"""
        lookup = {
            'on' : b'\x01\x04\x39\x00',
            'off': b'\x01\x04\x39\x03',
        }

        if(cmd == 'off'):
            #Update iris_position before switching to manual mode, range = 0..50
            msg = b'\x01\x04\x4B' + self.__toVisca2b(iris)
            status = self.send(msg)

            if(status != stat_OK):
                print("Update iris status : FAILED")

            #Update gain position before switching to manual mode, range = 12-21 dB
            msg = b'\x01\x04\x4C' + self.__toVisca2b(gain)
            status = self.send(msg)

            if(status != stat_OK):
                print("Update gain status : FAILED")

        status = self.send(lookup[cmd])

        if(status != stat_OK):
            print("AE status : FAILED")
        return status

    def backlight(self, cmd):
        """Turns backlight compensation on or off"""

        lookup = {
            'on' : b'\x01\x04\x33\x02',
            'off': b'\x01\x04\x33\x03',
        }

        if(cmd == "toggle"):
            if(backlightState == False):
                backlightState == True
                cmd = "on"
            else:
                backlightState = False
                cmd = "off"

        status = self.send(lookup[cmd])

        if(status != stat_OK):
            print("Backlight status : FAILED")
        return status

    def mirror(self, cmd):
        """Turns mirror on or off"""
        lookup = {
            'on' : b'\x01\x04\x61\x02',
            'off': b'\x01\x04\x61\x03',
        }

        if(cmd == "toggle"):
            if(mirrorState == False):
                mirrorState == True
                cmd = "on"
            else:
                mirrorState = False
                cmd = "off"

        status = self.send(lookup[cmd])

        if(status != stat_OK):
            print("Mirror status : FAILED")
        return status

    def flip(self, cmd):
        """Turns flip on or off"""
        lookup = {
            'on' : b'\x01\x04\x66\x02',
            'off': b'\x01\x04\x66\x03',
        }

        if(cmd == "toggle"):
            if(flipState == False):
                flipState == True
                cmd = "on"
            else:
                flipState = False
                cmd = "off"

        status = self.send(lookup[cmd])

        if(status != stat_OK):
            print("Flip status : FAILED")
        return status

    def gamma_auto(self, cmd, value=0):
        """Sets Gamma to auto/manual and to value if manual"""
        # Default - table 4
        lookup = {
            'on' : b'\x01\x04\x51\x02',
            'off': b'\x01\x04\x51\x03',
        }

        if(cmd == 'off'):
            #Update table before switching to manual mode range = 0..7
            msg = b'\x01\x04\x52' + self.__toVisca2b(value)
            status = self.send(msg)

            if(status != stat_OK):
                print("Update Gamma Table status : FAILED")

        status = self.send(lookup[cmd])

        if(status != stat_OK):
            print("Gamma status : FAILED")
        return status

    def mm_detect(self, cmd):
        """Turns Motor moved detection on or off"""
        #Camera recalibrates if MMD is on and is touched
        lookup = {
            'on' : b'\x01\x50\x30\x01',
            'off': b'\x01\x50\x30\x00',
        }

        status = self.send(lookup[cmd])

        if(status != stat_OK):
            print("MM status : FAILED")
        return status

    def call_led(self, cmd):
        """Turns call LED on or off"""
        lookup = {
            'on' : b'\x01\x33\x01\x01',
            'off': b'\x01\x33\x01\x00',
            'blink': b'\x01\x33\x01\x02',
        }

        status = self.send(lookup[cmd])

        if(status != stat_OK):
            print("Call LED status : FAILED")
        return status

    def pwr_led(self, cmd):
        """Turns power LED on or off"""
        lookup = {
            'on' : b'\x01\x33\x02\x01',
            'off': b'\x01\x33\x02\x00',
        }

        status = self.send(lookup[cmd])

        if(status != stat_OK):
            print("Power LED status : FAILED")
        return status

    def bestView(self, cmd, time):
        """Turns Best View on or off"""
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

    def setZoomSpeed(self, cmd):
        if(cmd == "high"):
            self.zoomSpeed = 11
        else:
            self.zoomSpeed = 10

    def setFocusSpeed(self, cmd):
        if(cmd == "high"):
            self.focusSpeed = 11
        else:
            self.focusSpeed = 10

    def zoomFocus(self, fn,cmd):
        """Sets the Zoom/Focus"""
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
            temp = 32 + speed
        elif(cmd == "out" or cmd == "near"):
            temp = 48 + speed
        msg += temp.to_bytes(1,"big")

        status = self.send(msg)

        if(status != stat_OK):
            print("Zoom/Focus status : FAILED")
        return status

    def zoomFocus_direct(self, zoom=0, focus=0):
        """Sets Zoom/Focus to specified position directly"""
        #Set zoom/focus arguments to -1 if both functions are not used
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

    def focus_auto(self, cmd):
        """Turns autofocus on or off"""
        lookup = {
            'on': b'\x01\x04\x38\x02',
            'off': b'\x01\x04\x38\x03',
        }

        status = self.send(lookup[cmd])

        if(status != stat_OK):
            print("Auto focus status : FAILED")
        return status

    def steer(self, cmd):
        """Steer in a direction"""
        #Stop is not added
        lookup = {
            'up': b'\x03\x01',
            'down': b'\x03\x02',
            'left': b'\x01\x03',
            'right': b'\x02\x03',
            'upleft': b'\x01\x01',
            'upright': b'\x02\x01',
            'downleft': b'\x01\x02',
            'downright': b'\x02\x02'
        }
        msg = b'\x01\x06\x01'
        msg += self.panSpeed
        msg += self.tiltSpeed
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
        msg = b'\x01\42'
        status = self.send(msg)

        if(status != stat_OK):
            print("Reboot status : FAILED")
        return status

    def pt_direct(self, pan, tilt):
        """Sets Pan/Tilt directly to positions"""
        msg = b'\x01\x06\x02'
        msg += self.panSpeedMax
        msg += self.tiltSpeedMax
        msg += self.__toVisca2b(pan)
        msg += self.__toVisca2b(tilt)

        status = self.send(msg)

        if(status != stat_OK):
            print("PT direct status : FAILED")

    def ptzf(self, pan, tilt, zoom, focus):
        """Sets all motors directly to positions in one operation"""
        msg = b'\x01\x06\x20'
        msg += self.__toVisca2b(pan)
        msg += self.__toVisca2b(tilt)
        msg += self.__toVisca2b(zoom)
        msg += self.__toVisca2b(focus)

        status = self.send(msg)

        if(status != stat_OK):
            print("PTZF direct status : FAILED")
        return status

    def serialSpeed(self, speed):
        """Update serial communication speed"""
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
    def Q_camID(self):
        msg = b'\x09\x04\x22'
        status = self.send(msg)

        if(status != stat_OK):
            print("CAM ID query status : FAILED")
        return status

    def Q_zoomPos(self):
        msg = b'\x09\x04\x47'
        status = self.send(msg)

        if(status != stat_OK):
            print("Zoom query status : FAILED")
        return status

    def Q_focusPos(self):
        msg = b'\x09\x04\x48'
        status = self.send(msg)

        if(status != stat_OK):
            print("Focus_pos query status : FAILED")
        return status

    def Q_focusMode(self):
        msg = b'\x09\x04\x38'
        status = self.send(msg)

        if(status != stat_OK):
            print("Focus_mode query status : FAILED")
        return status

    def Q_ptPos(self):
        msg = b'\x09\x06\x12'
        status = self.send(msg)

        if(status != stat_OK):
            print("PT query status : FAILED")
        return status

    def Q_pwr(self):
        msg = b'\x09\x04\x00'
        status = self.send(msg)

        if(status != stat_OK):
            print("Query status : FAILED")
        return status

    def Q_wbMode(self):
        msg = b'\x09\x04\x35'
        status = self.send(msg)

        if(status != stat_OK):
            print("Query status : FAILED")
        return status

    def Q_wbTable(self):
        msg = b'\x09\x04\x75'
        status = self.send(msg)

        if(status != stat_OK):
            print("Query status : FAILED")
        return status

    def Q_aeMode(self):
        msg = b'\x09\x04\x39'
        status = self.send(msg)

        if(status != stat_OK):
            print("Query status : FAILED")
        return status

    def Q_backlight(self):
        msg = b'\x09\x04\x33'
        status = self.send(msg)

        if(status != stat_OK):
            print("Query status : FAILED")
        return status

    def Q_mirror(self):
        msg = b'\x09\x04\x61'
        status = self.send(msg)

        if(status != stat_OK):
            print("Query status : FAILED")
        return status

    def Q_flip(self):
        msg = b'\x09\x04\x66'
        status = self.send(msg)

        if(status != stat_OK):
            print("Query status : FAILED")
        return status

    def Q_gammaMode(self):
        msg = b'\x09\x04\x51'
        status = self.send(msg)

        if(status != stat_OK):
            print("Query status : FAILED")
        return status

    def Q_gammaTable(self):
        msg = b'\x09\x04\x52'
        status = self.send(msg)

        if(status != stat_OK):
            print("Query status : FAILED")
        return status

    def Q_callLed(self):
        msg = b'\x09\x01\x33\x01'
        status = self.send(msg)

        if(status != stat_OK):
            print("Query status : FAILED")
        return status

    def Q_pwrLed(self):
        msg = b'\x09\x01\x33\x02'
        status = self.send(msg)

        if(status != stat_OK):
            print("Query status : FAILED")
        return status

    def Q_vidSwitch(self):
        msg = b'\x09\x06\x24'
        status = self.send(msg)

        if(status != stat_OK):
            print("Query status : FAILED")
        return status

    def Q_alsRGain(self):
        msg = b'\x09\x50\x50'
        status = self.send(msg)

        if(status != stat_OK):
            print("Query status : FAILED")
        return status

    def Q_alsBGain(self):
        msg = b'\x09\x50\x51'
        status = self.send(msg)

        if(status != stat_OK):
            print("Query status : FAILED")
        return status

    def Q_alsGGain(self):
        msg = b'\x09\x50\x52'
        status = self.send(msg)

        if(status != stat_OK):
            print("Query status : FAILED")
        return status

    def Q_alsWGain(self):
        msg = b'\x09\x50\x53'
        status = self.send(msg)

        if(status != stat_OK):
            print("Query status : FAILED")
        return status

    def Q_BestView(self):
        msg = b'\x09\x50\x60'
        status = self.send(msg)

        if(status != stat_OK):
            print("Query status : FAILED")
        return status

    def Q_upsideDown(self):
        msg = b'\x09\x50\x70'
        status = self.send(msg)

        if(status != stat_OK):
            print("Query status : FAILED")
        return status


    def send(self, command):
        """Sends a command to the camera and returns the success code"""
        #If no serial connection is established
        if self.ser == None:
            return 1

        #Is command an inquiry?
        inq = False
        if(command[0] == 9):
            inq = True

        msg = self.address
        msg += command
        msg += b'\xff'

        #Write to camera
        self.ser.write(msg)

        resp = b''
        rcvd_byte = None
        hex_str = []
        while rcvd_byte != b'\xff':
            rcvd_byte = self.ser.read()
            resp += rcvd_byte
            hex_str.append(rcvd_byte.hex())

        # Strip off first byte (address) and last (terminator)
        # We leave the reponse as bytes instead of hex because we may need to
        # do binary arithmetic on it later, might as well not just have to
        # convert back to bytes.
        resp = resp[1:-1]

        if(inq == True):
            print(hex_str)

        if(resp[0] != 80):  #\x50 = 80 in decimal
            return 1
        return 0


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