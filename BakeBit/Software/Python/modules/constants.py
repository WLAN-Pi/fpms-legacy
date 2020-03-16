# -*- coding: utf-8 -*-
#
""" 
constants.py - shared constant vars
"""

from PIL import ImageFont

__version__ = "2.00 (alpha-7)"
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

"""
# helper scripts to launch misc processes
'kismet_ctl_file': '/home/wlanpi/fpms/BakeBit/Software/Python/scripts/kismet_ctl',
'bettercap_ctl_file': '/home/wlanpi/fpms/BakeBit/Software/Python/scripts/bettercap_ctl',
'profiler_ctl_file': '/home/wlanpi/fpms/BakeBit/Software/Python/scripts/profiler_ctl',

# cdp and lldp networkinfo data file names
'lldpneigh_file': '/tmp/lldpneigh.txt',
'cdpneigh_file': '/tmp/cdpneigh.txt',
'ipconfig_file': '/home/wlanpi/fpms/BakeBit/Software/Python/scripts/networkinfo/ipconfig.sh 2>/dev/null',
'reachability_file': '/home/wlanpi/fpms/BakeBit/Software/Python/scripts/networkinfo/reachability.sh',
'publicip_cmd': '/home/wlanpi/fpms/BakeBit/Software/Python/scripts/networkinfo/publicip.sh',

# Linux programs
'ifconfig_file':'/sbin/ifconfig',
'iw_file': '/usr/sbin/iw',
'ufw_file': '/usr/sbin/ufw',
'ethtool_file': '/sbin/ethtool',

# options: classic, alt, symbols
'buttons_file': "/home/wlanpi/fpms/buttons.txt",
'key_map': 'classic',
"""
