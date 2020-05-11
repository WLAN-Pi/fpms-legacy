# -*- coding: utf-8 -*-
#
""" 
constants.py - shared constant vars
"""

from PIL import ImageFont

__version__ = "2.00 (alpha-8)"
__author__ = "wifinigel@gmail.com"

PAGE_SLEEP = 300             # Time in secs before sleep
PAGE_WIDTH = 128             # Pixel size of screen width
PAGE_HEIGHT = 64             # Pixel size of screen height
NAV_BAR_TOP = 55             # Top pixel number of nav bar
MENU_VERSION =  __version__  # fpms version

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
# Mode changer scripts
WCONSOLE_MODE_FILE = '/etc/wconsole/wconsole.on'
HOTSPOT_MODE_FILE = '/etc/wlanpihotspot/hotspot.on'
WIPERF_MODE_FILE = '/home/wlanpi/wiperf/wiperf.on'

WCONSOLE_SWITCHER_FILE ='/etc/wconsole/wconsole_switcher'
HOTSPOT_SWITCHER_FILE = '/etc/wlanpihotspot/hotspot_switcher'
WIPERF_SWITCHER_FILE = '/home/wlanpi/wiperf/wiperf_switcher'

# helper scripts to launch misc processes
KISMET_CTL_FILE = '/home/wlanpi/fpms/BakeBit/Software/Python/scripts/kismet_ctl'
BETTERCAP_CTL_FILE = '/home/wlanpi/fpms/BakeBit/Software/Python/scripts/bettercap_ctl'
PROFILER_CTL_FILE = '/home/wlanpi/fpms/BakeBit/Software/Python/scripts/profiler_ctl'

# cdp and lldp networkinfo data file names
LLDPNEIGH_FILE = '/tmp/lldpneigh.txt'
CDPNEIGH_FILE = '/tmp/cdpneigh.txt'
IPCONFIG_FILE = '/home/wlanpi/fpms/BakeBit/Software/Python/scripts/networkinfo/ipconfig.sh 2>/dev/null'
REACHABILITY_FILE = '/home/wlanpi/fpms/BakeBit/Software/Python/scripts/networkinfo/reachability.sh'
PUBLICIP_CMD = '/home/wlanpi/fpms/BakeBit/Software/Python/scripts/networkinfo/publicip.sh'

# Linux programs
IFCONFIG_FILE = '/sbin/ifconfig'
IW_FILE = '/usr/sbin/iw'
UFW_FILE = '/usr/sbin/ufw'
ETHTOOL_FILE = '/sbin/ethtool'

# key map file
BUTTONS_FILE = "/home/wlanpi/fpms/buttons.txt"

