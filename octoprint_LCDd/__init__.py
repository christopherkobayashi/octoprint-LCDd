# LCDd Plugin for Octoprint

from __future__ import absolute_import
from octoprint.printer.estimation import PrintTimeEstimator
import .pylcdd
import octoprint.plugin
import octoprint.events
import time
import datetime
import os
import sys
import socket

class LCDdplugin(octoprint.plugin.StartupPlugin,
				octoprint.plugin.EventHandlerPlugin,
				octoprint.plugin.ProgressPlugin):

	screen = "octoprint"


  	def __init__(self):
  		# backlight_enabled=True, charmap='A00')
		self.lcd = pyLCDd()
		self.lcd.connect(screen)
    	if not self.lcd.connected():
    		print ("No connection to LCDd")
    	else:
    		self.lcd.backlight(True)
    		self.lcd.addscreen(screen, priority = "foreground")

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
      		lcd.printline(screen, 0, self.birdy[pos], offset = pos)
      		time.sleep(0.5)
    	lcd.printline(screen, 0, 'Job is Done')
    	lcd.printline(screen, 1, '\,,/(^_^)\,,/')


  	def on_after_startup(self):
		lcd = self.lcd
    	self._logger.info("plugin initialized !")


  	def on_print_progress(self,storage,path,progress):
		lcd = self.lcd
		percent = int(progress/6.25)+1
		completed = '\x01' * percent
		lcd.printline(screen, 0, "Completed: "+str(progress)+"%")

    	if progress==1 :
      		self.start_date=time.time()

    	if progress > 10 and progress < 100:
      		now = time.time()
      		elapsed = now - self.start_date
      		average=elapsed/(progress-1)
      		remaining=int((100-progress)*average)
      		remaining=str(datetime.timedelta(seconds=remaining))
      		#lcd.cursor_pos = (1,3)
      		lcd.printline(screen, 1, remaining)

    	if progress==100 :
      		self.JobIsDone(lcd)

  	def on_event(self,event,payload):
		lcd = self.lcd

    	if event in "Connected":
      		lcd.printline(screen, 0, 'Connected to:')
      		lcd.printline(screen, 1, payload["port"])

    	if event in "Shutdown":
      		lcd.clear()
      		lcd.printline(screen, 0, 'Shutting down')
      		time.sleep(1)
      		lcd.self.backlight(False)
      		lcd.close()

    	if event in "PrinterStateChanged":

		if payload["state_string"] in "Offline":
        		lcd.clear()
        		lcd.printline(screen, 0, 'Disconnected')
        		time.sleep(2)
        		lcd.clear()
        		lcd.printline(screen, 0, 'Eco mode on')
        		time.sleep(5)
        		lcd.backlight(False)

      	if payload["state_string"] in "Operational":
        		lcd.backlight(True)
        		lcd.clear()
        		lcd.printline(screen, 0, 'Operational')

      	if payload["state_string"] in "Cancelling":
        		lcd.clear()
        		lcd.printline(screen, 0, 'Cancelling job')
        		time.sleep(0.2)

      	if payload["state_string"] in "PrintCancelled":
        		lcd.clear()
        		time.sleep(0.5)
        		lcd.printline(screen, 0, 'Job cancelled')
        		time.sleep(2)

      	if payload["state_string"] in "Paused":
        		lcd.clear()
        		time.sleep(0.5)
        		lcd.printline(screen, 0, 'Job paused')

      	if payload["state_string"] in "Resuming":
        		lcd.clear()
        		lcd.printline(screen, 0, 'Job resuming')
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
