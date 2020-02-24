# OctoPrint-LCDd

This plugin uses lcdproc to display OctoPrint status.  It is heavily based on OctoPrint-Lcd1602
by Milan Popovic.

It indicates on which port the printer is connected, the printing progress, and the
remaining print time.

Although this plugin was written for use with a 16x2 LCD display connected to the i2c
bus via a hd44780 interface chip, this should work with any display supported by lcdproc.

## Setup

Install via the bundled [Plugin Manager](https://github.com/foosel/OctoPrint/wiki/Plugin:-Plugin-Manager)
or manually using this URL:

    https://github.com/christopherkobayashi/octoprint-LCDd/archive/master.zip

**MANUAL INSTALL:**

clone the repo :

`git clone https://github.com/christopherkobayashi/octoprint-LCDd.git  `

install :

`cd OctoPrint-LCDd && python setup.py install`

## Configuration

None.  All LCD interface configuration should be done via LCDd.conf
