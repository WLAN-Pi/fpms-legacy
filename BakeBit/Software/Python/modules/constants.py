# -*- coding: utf-8 -*-
#
""" 
constants.py - shared constant vars
"""

from PIL import ImageFont
import os
import pathlib

__version__ = "2.0.2"
__author__ = "wifinigel@gmail.com"

PAGE_SLEEP = 300             # Time in secs before sleep
PAGE_WIDTH = 128             # Pixel size of screen width
PAGE_HEIGHT = 64             # Pixel size of screen height
NAV_BAR_TOP = 55             # Top pixel number of nav bar
MENU_VERSION =  __version__  # fpms version

# figure out the script path
SCRIPT_PATH = str(pathlib.Path(__file__).parent.parent.absolute())

# change in to script path dir
os.chdir(SCRIPT_PATH)

# Define display fonts
SMART_FONT = ImageFont.truetype('DejaVuSansMono-Bold.ttf', 10)
FONT11 = ImageFont.truetype('DejaVuSansMono.ttf', 11)
FONT12 = ImageFont.truetype('DejaVuSansMono.ttf', 12)
FONTB12 =  ImageFont.truetype('DejaVuSansMono-Bold.ttf', 12)
FONT14 = ImageFont.truetype('DejaVuSansMono.ttf', 14)
FONTB14 =  ImageFont.truetype('DejaVuSansMono-Bold.ttf', 14)

#######################################
# File name constants
#######################################

# Linux programs
IFCONFIG_FILE = '/sbin/ifconfig'
IW_FILE = '/usr/sbin/iw'
UFW_FILE = '/usr/sbin/ufw'
ETHTOOL_FILE = '/sbin/ethtool'

# Mode changer scripts
MODE_FILE = '/etc/wlanpi-state'

WCONSOLE_SWITCHER_FILE ='/etc/wconsole/wconsole_switcher'
HOTSPOT_SWITCHER_FILE = '/etc/wlanpihotspot/hotspot_switcher'
WIPERF_SWITCHER_FILE = '/home/wlanpi/wiperf/wiperf_switcher'

#### Paths below here are relative to script dir or /tmp fixed paths ###

# helper scripts to launch misc processes
KISMET_CTL_FILE = SCRIPT_PATH + '/scripts/kismet_ctl'
BETTERCAP_CTL_FILE = SCRIPT_PATH + '/scripts/bettercap_ctl'
PROFILER_CTL_FILE = SCRIPT_PATH + '/scripts/profiler_ctl'

# cdp and lldp networkinfo data file names
LLDPNEIGH_FILE = '/tmp/lldpneigh.txt'
CDPNEIGH_FILE = '/tmp/cdpneigh.txt'
IPCONFIG_FILE = SCRIPT_PATH + '/scripts/networkinfo/ipconfig.sh 2>/dev/null'
REACHABILITY_FILE = SCRIPT_PATH + '/scripts/networkinfo/reachability.sh'
PUBLICIP_CMD = SCRIPT_PATH + '/scripts/networkinfo/publicip.sh'

# key map file
BUTTONS_FILE = SCRIPT_PATH + '/buttons.txt'

