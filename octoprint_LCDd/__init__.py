# LCDd Plugin for Octoprint

from __future__ import absolute_import
from octoprint.printer.estimation import PrintTimeEstimator
import octoprint.plugin
import octoprint.events
import time
import datetime
import os
import sys
import socket

# Python LCDd communication class
# Based on https://github.com/tremby/pylcd by Bart Nagel

import os
import sys
import socket

class pyLCDd:
    width = None
    height = None
    cellwidth = None
    cellheight = None
    s = None
    verbose = False

    screens = {}
    widgets = []

    def getsuccess(self):
        # Get data from LCDd until a success or error message is received
        if not self.connected():
            raise Exception("not connected")
        while True:
            response = self.s.recv(1024).strip().split("\n")
            successorfail = False
            for line in response:
                if self.verbose:
                    print ("Message from LCDd: \"%s\"" % line)
                if line == "success" or line[0:4] == "huh?":
                    successorfail = True
                    break
            if successorfail:
                return line == "success"
            # else recieve data again

    def getwidth(self):
        # Get the width in cells of the LCD
        if not self.connected():
            raise Exception("not connected")
        return self.width
    def getheight(self):
        # Get the height in cells of the LCD
        if not self.connected():
            raise Exception("not connected")
        return self.height
    def getcellwidth(self):
        # Get the width in pixels of one cell of the LCD
        if not self.connected():
            raise Exception("not connected")
        return self._cellwidth
    def getcellheight(self):
        # Get the height in pixels of one cell of the LCD
        if not self.connected():
            raise Exception("not connected")
        return self.cellheight
    def getscreens(self):
        # Get an array of screen names owned by this client
        if not self.connected():
            raise Exception("not connected")
        return self.screens
    def getwidgets(self, screen):
        # Get the set of widget names owned by a particular screen of this client
        if not self.connected():
            raise Exception("not connected")
        try:
            return self.screens[screen]
        except KeyError:
            raise ValueError("screen '%s' doesn't exist" % screen)

    def send(self, message, getresponse=True):
        # Send a raw command to LCDd
        # A newline character is added.
        # If getresponse is True, wait for a success or error response and return
        # a boolean. Otherwise (if getresponse is False) the getsuccess method can
        # be used.

        self.s.send("%s\n" % message)
        if getresponse:
            return self.getsuccess()

    def printline(self, screen, line, text, usewidth = None, offset = 0, frame = None):
        # Print a string to a particular line of the display
        # Use string or scroller based on text length

        if offset >= self.getwidth():
            raise ValueError("offset too big")

        if str(line) in self.getwidgets(screen):
            if self.verbose:
                print ("Widget '%s' already exists on screen '%s', removing it" % (str(line), screen) )
            if not self.send("widget_del %s %s" % (screen, str(line))):
                if self.verbose:
                    print ("It didn't exist after all -- weird but no problem")
        if frame:
            fr = " -in %s" % frame
        if self.verbose:
            print ("Adding string widget %s" % str(line) )
        fr = ""
        self.send("widget_add %s %s string%s" % (screen, str(line), fr), False)
        if self.getsuccess():
            self.widgets.append(str(line))
        else:
            raise Exception("Could not add widget")

        if self.verbose:
            print ( "Printing \"%s\" to string widget with screenoffset %d" % (text, offset) )
        self.send("widget_set %s %s %d %d \"%s\"" % (screen, str(line), offset + 1, line + 1, text.replace('"', '\\"')), False)
        if not self.getsuccess():
            raise Exception("Could not set widget text")

    def connect(self, clientname, host="localhost", port=13666):
        # Open the socket to LCDd and do the handshake

        if self.connected(): raise Exception("already connected")
        if self.verbose:
            print ("Connecting to LCDd on %s port %d" % (host, port) )
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.connect((host, port))
        if not self.s:
            raise Exception("Could not connect to LCDd")

        # say hello and get display dimensions
        if self.verbose:
            print ("Getting display dimension information")
        self.send("hello", False)
        response = self.s.recv(1024).split()
        while len(response):
            atom = response.pop(0)
            if atom == "wid":
                self.width = int(response.pop(0))
                if self.verbose:
                    print ("Display is %d cells wide" % self.getwidth() )
            elif atom == "hgt":
                self.height = int(response.pop(0))
                if self.verbose:
                    print ("Display is %d cells high" % self.getheight() )
            elif atom == "cellwid":
                self.cellwidth = int(response.pop(0))
                if self.verbose:
                    print ("Cells are %d pixels wide" % self.getcellwidth() )
            elif atom == "cellhgt":
                self.cellheight = int(response.pop(0))
                if self.verbose:
                    print ("Cells are %d pixels high" % self.getcellheight() )

        # identify ourselves
        if self.verbose:
            print ("Identifying ourselves to LCDd")
        if not self.send("client_set -name %s" % clientname):
            raise Exception("Could not set client name")

    # TODO: disconnect method

    def addscreen(self, name, priority="hidden"):
        # Add a screen with the given name
        if self.verbose:
            print ("Adding a new screen with name %s" % name)
        if not self.send("screen_add %s" % name):
            raise Exception("Could not add screen")
        self.screens[name] = set()
        self.priority(name, priority)

    def heartbeat(self, screen, on):
        # Switch the heartbeat on or off
        if self.verbose:
            print ("Switching the heartbeat on or off")
        val = "off"
        if on:
            val = "on"
        if not self.send("screen_set %s -heartbeat %s" % (screen, val)):
            raise Exception("Could not switch off heartbeat")

    def priority(self, screen, priority):
        if priority not in self.PRIORITY:
            raise ValueError("invalid priority class '%s'" % priority)

        if self.verbose:
            print ("Setting screen to priority \"%s\"" % priority)

        if not self.send("screen_set %s -priority %s" % (screen, priority)):
            raise Exception("Could not set priority")

    def connected(self):
        return bool(self.s)

    def backlight(self, state):
        if state == False:
            self.send("backlight off")
        else:
            self.send("backlight on")

    def clear(self, screen):
        self.printline(screen, 0, '')
        self.printline(screen, 1, '')

    PRIORITY = [
            "hidden",
            "background",
            "info",
            "foreground",
            "alert",
            "input",
            ]


class LCDdPlugin(octoprint.plugin.StartupPlugin,
                octoprint.plugin.EventHandlerPlugin,
                octoprint.plugin.ProgressPlugin):

    screen = "octoprint"


    def __init__(self):
        # backlight_enabled=True, charmap='A00')
        self.lcd = pyLCDd()
        self.lcd.connect(self.screen)
        if not self.lcd.connected():
            print ("No connection to LCDd")
        else:
            self.lcd.backlight(True)
            self.lcd.addscreen(self.screen, priority = "foreground")
            self.lcd.heartbeat(self.screen, False)

            # create block for progress bar
            #self.block = bytearray(b'\xFF\xFF\xFF\xFF\xFF\xFF\xFF')
            #self.block.(255)
            #self.lcd.create_char(1, self.block)

            # init vars
            self.start_date = 0

    def JobIsDone(self,lcd):

        # create final anim
        self.birdy = [ '^_-' , '^_^', '-_^' , '^_^', '0_0', '-_-', '^_-', '^_^','@_@','*_*','$_$','<_<','>_>']

        for pos in range(0,13):
            lcd.printline(self.screen, 0, self.birdy[pos], offset = pos)
            time.sleep(0.5)
        lcd.printline(self.screen, 0, 'Job is Done')
        lcd.printline(self.screen, 1, '\,,/(^_^)\,,/')


    def on_after_startup(self):
        lcd = self.lcd
        self._logger.info("plugin initialized !")


    def on_print_progress(self,storage,path,progress):
        lcd = self.lcd
        percent = int(progress/6.25)+1
        completed = '\x01' * percent
        lcd.printline(self.screen, 0, "Completed: "+str(progress)+"%")

        if progress==1 :
            self.start_date=time.time()

        if progress > 10 and progress < 100:
            now = time.time()
            elapsed = now - self.start_date
            average=elapsed/(progress-1)
            remaining=int((100-progress)*average)
            remaining=str(datetime.timedelta(seconds=remaining))
            #lcd.cursor_pos = (1,3)
            lcd.printline(self.screen, 1, remaining)

        if progress==100 :
            self.JobIsDone(lcd)

    def on_event(self,event,payload):
        lcd = self.lcd

        if event in "Connected":
            lcd.printline(self.screen, 0, 'Connected to:')
            lcd.printline(self.screen, 1, payload["port"])

        if event in "Shutdown":
            lcd.clear(self.screen)
            lcd.printline(self.screen, 0, 'Shutting down')
            time.sleep(1)
            lcd.self.backlight(False)
#            lcd.close()

        if event in "PrinterStateChanged":

            if payload["state_string"] in "Offline":
                lcd.clear(self.screen)
                lcd.printline(self.screen, 0, 'Disconnected')
                time.sleep(2)
                lcd.clear(self.screen)
                lcd.printline(self.screen, 0, 'Eco mode on')
                time.sleep(5)
                lcd.backlight(False)

            if payload["state_string"] in "Operational":
                lcd.backlight(True)
                lcd.clear(self.screen)
                lcd.printline(self.screen, 0, 'Operational')

            if payload["state_string"] in "Cancelling":
                lcd.clear(self.screen)
                lcd.printline(self.screen, 0, 'Cancelling job')
                time.sleep(0.2)

            if payload["state_string"] in "PrintCancelled":
                lcd.clear(self.screen)
                time.sleep(0.5)
                lcd.printline(self.screen, 0, 'Job cancelled')
                time.sleep(2)

            if payload["state_string"] in "Paused":
                lcd.clear(self.screen)
                time.sleep(0.5)
                lcd.printline(self.screen, 0, 'Job paused')

            if payload["state_string"] in "Resuming":
                lcd.clear(self.screen)
                lcd.printline(self.screen, 0, 'Job resuming')
                time.sleep(0.2)

    def get_update_information(self):
        return dict(
            LCDd=dict(
                displayName="LCDd display",
                displayVersion=self._plugin_version,

                type="github_release",
                current=self._plugin_version,
                user="christopherkoba",
                repo="OctoPrint-LCDd",

                pip="https://github.com/christopherkoba/octoprint-LCDd/archive/{target}.zip"
            )
        )

__plugin_name__ = "LCDd display"

def __plugin_load__():
    global __plugin_implementation__
    __plugin_implementation__ = LCDdPlugin()

    global __plugin_hooks__
    __plugin_hooks__ = {
        "octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information
    }
