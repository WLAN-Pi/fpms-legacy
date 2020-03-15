#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
This script loosely based on the original bakebit_nanonhat_oled.py provided
by Friendlyarm. It has been updated to support a scalable menu structure and
a number of additional features to support the WLANPi initiative.

History:

 2.00 - Complete re-write to move to modular architcture - Nigel 03/03/2020

"""

import bakebit_128_64_oled as oled
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw
import time
import subprocess
import signal
import os
import os.path
import socket
import random

from modules.constants import (
    PAGE_SLEEP,
    PAGE_HEIGHT,
    PAGE_WIDTH,
    NAV_BAR_TOP,
    MENU_VERSION,
)

from modules.navigation import *
from modules.buttons import *

from modules.pages.display import *
from modules.pages.homepage import *
from modules.pages.simpletable import * 
from modules.pages.pagedtable import * 
from modules.pages.page import *

from modules.network import *
from modules.utils import *
from modules.modes import *
from modules.system import *

from modules.apps import *



####################################
# Initialize the SEED OLED display
####################################
oled.init()
# Set display to normal mode (i.e non-inverse mode)
oled.setNormalDisplay()
oled.setHorizontalMode()

#######################################
# Initialize various global variables
#######################################
g_vars = {

    ############################
    # Shared constants
    ############################

    # Define display fonts
    'smartFont': ImageFont.truetype('DejaVuSansMono-Bold.ttf', 10),
    'font11': ImageFont.truetype('DejaVuSansMono.ttf', 11),
    'font12': ImageFont.truetype('DejaVuSansMono.ttf', 12),
    'fontb12': ImageFont.truetype('DejaVuSansMono-Bold.ttf', 12),
    'font14': ImageFont.truetype('DejaVuSansMono.ttf', 14),
    'fontb14': ImageFont.truetype('DejaVuSansMono-Bold.ttf', 14),
    'fontb24': ImageFont.truetype('DejaVuSansMono-Bold.ttf', 24),

    ##################################################
    # Shared status signals (may be changed anywhere)
    ##################################################

    # This variable is shared between activities and is set to True if a
    # drawing action in already if progress (e.g. by another activity). An activity
    # happens during each cycle of the main while loop or when a button is pressed
    # (This does not appear to be threading or process spawning)

    'shutdown_in_progress': False,  # True when shutdown or reboot started
    'drawing_in_progress': False, # True when page being painted on screen
    'screen_cleared': False,        # True when display cleared (e.g. screen save)
    'display_state': 'page',        # current display state: 'page' or 'menu'
    'sig_fired': False,             # Set to True when button handler fired 
    'option_selected': 0,        # Content of currently selected menu level
    'current_menu_location': [0],   # Pointer to current location in menu structure
    'current_scroll_selection': 0,  # where we currently are in scrolling table
    'current_mode': 'classic',      # Currently selected mode (e.g. wconsole/classic)
    'start_up': True,            # True if in initial (home page) start-up state
    'disable_keys': False,       # Set to true when need to ignore key presses
    'table_list_length': 0,         # Total length of currently displayed table
    'result_cache': False,          # used to cache results when paging info
    'speedtest_status': False,   # Indicates if speedtest has run or is in progress
    'speedtest_result_text': '', # tablulated speedtest result data
    'button_press_count': 0, # global count of button pressses
    'last_button_press_count': 0, # copy of count of button pressses used in main loop
    'pageSleepCountdown': PAGE_SLEEP, # Set page sleep control
    'home_page_name': "Home",       # Display name for top level menu

    #######################################
    # Initialize file variables
    #######################################
    # Mode changer scripts
    'wconsole_mode_file': '/etc/wconsole/wconsole.on',
    'hotspot_mode_file': '/etc/wlanpihotspot/hotspot.on',
    'wiperf_mode_file': '/home/wlanpi/wiperf/wiperf.on',

    'wconsole_switcher_file': '/etc/wconsole/wconsole_switcher',
    'hotspot_switcher_file': '/etc/wlanpihotspot/hotspot_switcher',
    'wiperf_switcher_file': '/home/wlanpi/wiperf/wiperf_switcher',

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
}

############################
# shared objects
############################
g_vars['image'] = Image.new('1', (PAGE_WIDTH, PAGE_HEIGHT))
g_vars['draw'] = ImageDraw.Draw(g_vars['image'])
g_vars['reboot_image'] = Image.open('reboot.png').convert('1')

# check our current mode
if os.path.isfile(g_vars['wconsole_mode_file']):
    g_vars['current_mode'] = 'wconsole'
if os.path.isfile(g_vars['hotspot_mode_file']):
    g_vars['current_mode'] = 'hotspot'
if os.path.isfile(g_vars['wiperf_mode_file']):
    g_vars['current_mode'] = 'wiperf'

# if the buttons file exists, read content
if os.path.isfile(g_vars['buttons_file']):
    with open(g_vars['buttons_file'], 'r') as f:
        key_map = f.readline()
        g_vars['key_map'] = key_map

##################################
# Static info we want to get once
##################################

# get & the current version of WLANPi image
ver_cmd = "grep \"WLAN Pi v\" /var/www/html/index.html | sed \"s/<[^>]\+>//g\""
try:
    g_vars['wlanpi_ver'] = subprocess.check_output(ver_cmd, shell=True).decode().strip()
except:
    g_vars['wlanpi_ver'] = "unknown"
        
# get hostname
try:
    g_vars['hostname'] = subprocess.check_output('hostname', shell=True).decode()
except:
    g_vars['hostname'] = 'Unknown'

###########################
# Network menu area utils
###########################
def show_interfaces():
    network_obj = Network(g_vars)
    network_obj.show_interfaces(g_vars)

def show_wlan_interfaces():
    network_obj = Network(g_vars)
    network_obj.show_wlan_interfaces(g_vars)

def show_eth0_ipconfig():
    network_obj = Network(g_vars)
    network_obj.show_eth0_ipconfig(g_vars)

def show_vlan():
    network_obj = Network(g_vars)
    network_obj.show_vlan(g_vars)

def show_lldp_neighbour():
    network_obj = Network(g_vars)
    network_obj.show_lldp_neighbour(g_vars)

def show_cdp_neighbour():
    network_obj = Network(g_vars)
    network_obj.show_cdp_neighbour(g_vars)

def show_publicip():
    network_obj = Network(g_vars)
    network_obj.show_publicip(g_vars)

###########################
# Utils menu area
###########################
def show_reachability():
    utils_obj = Utils(g_vars)
    utils_obj.show_reachability(g_vars)

def show_speedtest():
    utils_obj = Utils(g_vars)
    utils_obj.show_speedtest(g_vars)

def show_wpa_passphrase():
    utils_obj = Utils(g_vars)
    utils_obj.show_wpa_passphrase(g_vars)

def show_usb():
    utils_obj = Utils(g_vars)
    utils_obj.show_usb(g_vars)

def show_ufw():
    utils_obj = Utils(g_vars)
    utils_obj.show_ufw(g_vars)

############################
# Modes area
############################
def wconsole_switcher():
    mode_obj = Mode(g_vars)
    mode_obj.wconsole_switcher(g_vars)

def hotspot_switcher():
    mode_obj = Mode(g_vars)
    mode_obj.hotspot_switcher(g_vars)

def wiperf_switcher():
    mode_obj = Mode(g_vars)
    mode_obj.wiperf_switcher(g_vars)
    
###########################
# Apps area
###########################
def kismet_status():
    app_obj = App(g_vars)
    app_obj.kismet_status(g_vars)

def kismet_stop():
    app_obj = App(g_vars)
    app_obj.kismet_stop(g_vars)

def kismet_start():
    app_obj = App(g_vars)
    app_obj.kismet_start(g_vars)

def bettercap_status():
    app_obj = App(g_vars)
    app_obj.bettercap_status(g_vars)

def bettercap_stop():
    app_obj = App(g_vars)
    app_obj.bettercap_stop(g_vars)

def bettercap_start():
    app_obj = App(g_vars)
    app_obj.bettercap_start(g_vars)

def profiler_status():
    app_obj = App(g_vars)
    app_obj.profiler_status(g_vars)

def profiler_stop():
    app_obj = App(g_vars)
    app_obj.profiler_stop(g_vars)

def profiler_start():
    app_obj = App(g_vars)
    app_obj.profiler_start(g_vars)

def profiler_start_no11r():
    app_obj = App(g_vars)
    app_obj.profiler_start_no11r(g_vars)

def profiler_purge():
    app_obj = App(g_vars)
    app_obj.profiler_purge(g_vars)

###########################
# System menu area utils
###########################

def shutdown():
    system_obj = System(g_vars)
    system_obj.shutdown(g_vars)

def reboot():
    system_obj = System(g_vars)
    system_obj.reboot(g_vars)

def show_summary():
    system_obj = System(g_vars)
    system_obj.show_summary(g_vars)

def show_date():
    system_obj = System(g_vars)
    system_obj.show_date(g_vars)

def show_menu_ver():
    system_obj = System(g_vars)
    system_obj.fpms_version(g_vars)

#############################
# Button presses & home page
#############################
def home_page():
    homepage_obj = HomePage(g_vars)
    homepage_obj.home_page(g_vars, menu)

def menu_down():
    button_obj = Button(g_vars, menu)
    button_obj.menu_down(g_vars, menu)

def menu_left():
    button_obj = Button(g_vars, menu)
    button_obj.menu_left(g_vars, menu)

def menu_right():
    button_obj = Button(g_vars, menu)
    button_obj.menu_right(g_vars, menu)

def go_up():
    button_obj = Button(g_vars, menu)
    button_obj.go_up(g_vars, menu)

def buttons_classic():
    button_obj = Button(g_vars, menu)
    button_obj.buttons_classic(g_vars)

def buttons_intuitive():
    button_obj = Button(g_vars, menu)
    button_obj.buttons_intuitive(g_vars)

def buttons_symbol():
    button_obj = Button(g_vars, menu)
    button_obj.buttons_symbol(g_vars)

# Key mappings
g_vars['key_mappings'] = { 
        'classic': {
                'key_actions': { 'key1': menu_down,  'key2': menu_right, 'key3': menu_left },
                'key_functions':  { 
                                'down':   { 'label': 'Down', 'position': 0 },
                                'pgdown': { 'label': 'PgDn', 'position': 0 },
                                

                                'next':   { 'label': 'Next', 'position': 50 },
                                'up':     { 'label': 'Up', '  position': 50 },
                                'pgup':   { 'label': 'PgUp', 'position': 50 },

                                'back':   { 'label': 'Back', 'position': 100 },
                                'menu':   { 'label': 'Menu', 'position': 100 },
                                'exit':   { 'label': 'Exit', 'position': 100 },

                },
                'type': 'text',
         },
        'alt': {
                'key_actions': { 'key1': menu_left,  'key2': menu_down, 'key3': menu_right },
                'key_functions':  { 
                                'back':   { 'label': 'Back', 'position': 0 },
                                'exit':   { 'label': 'Exit', 'position': 0 },
                                'menu':   { 'label': 'Menu', 'position': 0 },

                                'down':   { 'label': 'Down', 'position': 50 },
                                'pgdown': { 'label': 'PgDn', 'position': 50 },

                                'next': { 'label': 'Next', 'position': 100 },
                                'up':   { 'label': 'Up', '  position': 100 },
                                'pgup': { 'label': 'PgUp', 'position': 100 },
                },
                'type': 'text',
         },
        'symbols': {
                'key_actions': { 'key1': menu_left,  'key2': menu_down, 'key3': menu_right },
                'key_functions':  { 
                                'back':   { 'label': u" \u2190", 'position': 0 },
                                
                                'exit':   { 'label': u" \u21B0", 'position': 0 },
                                'menu':   { 'label': u" \u2193", 'position': 0 },
                                
                                'down':   { 'label': u"  \u2193", 'position': 55 },
                                'pgdown': { 'label': u"  \u2193", 'position': 55 },


                                'next': { 'label': u"  \u2192", 'position': 103 },
                                'up':   { 'label': u"  \u2191", 'position': 103 },
                                'pgup': { 'label': u"  \u2191", 'position': 103 },
                },
                'type': 'symbol',
         },
}
#######################
# menu structure here
#######################

# assume classic mode menu initially...
menu = [
    {"name": "Network", "action": [
        {"name": "Interfaces", "action": show_interfaces},
        {"name": "WLAN Interfaces", "action": show_wlan_interfaces},
        {"name": "Eth0 IP Config", "action": show_eth0_ipconfig},
        {"name": "Eth0 VLAN", "action": show_vlan},
        {"name": "LLDP Neighbour", "action": show_lldp_neighbour},
        {"name": "CDP Neighbour", "action": show_cdp_neighbour},
        {"name": "Public IP Address", "action": show_publicip},
    ]
    },
    {"name": "Utils", "action": [
        {"name": "Reachability", "action": show_reachability},
        {"name": "Speedtest", "action": [
            {"name": "Back", "action": go_up},
            {"name": "Start Test", "action": show_speedtest},
        ]
        },
        {"name": "WPA Passphrase", "action": show_wpa_passphrase},
        {"name": "USB Devices", "action": show_usb},
        {"name": "UFW Ports", "action": show_ufw},
    ]
    },
    {"name": "Modes", "action": [
        {"name": "Wi-Fi Console",   "action": [
            {"name": "Cancel", "action": go_up},
            {"name": "Confirm", "action": wconsole_switcher},
        ]
        },
        {"name": "Hotspot",   "action": [
            {"name": "Cancel", "action": go_up},
            {"name": "Confirm", "action": hotspot_switcher},
        ]
        },
        {"name": "Wiperf",   "action": [
            {"name": "Cancel", "action": go_up},
            {"name": "Confirm", "action": wiperf_switcher},
        ]
        },
    ]
    },
    {"name": "Apps", "action": [
        {"name": "Kismet",   "action": [
            {"name": "Status", "action": kismet_status},
            {"name": "Stop", "action":   kismet_stop},
            {"name": "Start", "action":  kismet_start},
        ]
        },
        {"name": "Bettercap",   "action": [
            {"name": "Status", "action": bettercap_status},
            {"name": "Stop", "action":   bettercap_stop},
            {"name": "Start", "action":  bettercap_start},
        ]
        },
        {"name": "Profiler",   "action": [
            {"name": "Status", "action":          profiler_status},
            {"name": "Stop", "action":            profiler_stop},
            {"name": "Start", "action":           profiler_start},
            {"name": "Start (no 11r)", "action":  profiler_start_no11r},
            {"name": "Purge Reports", "action":   profiler_purge},
        ]
        },
    ]
    },
    {"name": "System", "action": [
        {"name": "Shutdown", "action": [
            {"name": "Cancel", "action": go_up},
            {"name": "Confirm", "action": shutdown},
        ]
        },
        {"name": "Reboot",   "action": [
            {"name": "Cancel", "action": go_up},
            {"name": "Confirm", "action": reboot},
        ]
        },
        {"name": "Button Config", "action": [
            {"name": "Classic", "action": buttons_classic},
            {"name": "Intuitive", "action": buttons_intuitive},
            {"name": "Symbols", "action": buttons_symbol},
        ]
        },
        {"name": "Summary", "action": show_summary},
        {"name": "Date/Time", "action": show_date},
        {"name": "Version", "action": show_menu_ver},
    ]
    },
]

# update menu options data structure if we're in non-classic mode
if g_vars['current_mode'] == "wconsole":
    switcher_dispatcher = wconsole_switcher
    g_vars['home_page_name'] = "Wi-Fi Console"

if g_vars['current_mode'] == "hotspot":
    switcher_dispatcher = hotspot_switcher
    g_vars['home_page_name'] = "Hotspot"

if g_vars['current_mode'] == "wiperf":
    switcher_dispatcher = wiperf_switcher
    g_vars['home_page_name'] = "Wiperf"

if g_vars['current_mode'] != "classic":
    menu[2] = {"name": "Mode", "action": [
        {"name": "Classic Mode",   "action": [
            {"name": "Cancel", "action": go_up},
            {"name": "Confirm", "action": switcher_dispatcher},
        ]
        },
    ]
    }

    menu.pop(3)

# Set up handlers to process key presses
def receive_signal(signum, stack, g_vars=g_vars):

    if g_vars['disable_keys'] == True:
        # someone disabled the front panel keys as they don't want to be interrupted
        return

    if (g_vars['sig_fired']):
        # signal handler already in progress, ignore this one
        return

    # user pressed a button, reset the sleep counter
    g_vars['pageSleepCountdown'] = PAGE_SLEEP

    g_vars['start_up'] = False

    if g_vars['drawing_in_progress'] or g_vars['shutdown_in_progress']:
        return
    
    # If we get this far, an action wil be taken as a result of the button press
    # increment the button press counter to indicate the something has been done 
    # and a page refresh is required
    g_vars['button_press_count'] += 1

    # if display has been switched off to save screen, power back on and show home menu
    if g_vars['screen_cleared']:
        g_vars['screen_cleared'] = False
        g_vars['pageSleepCountdown'] = PAGE_SLEEP
        return

    # Key 1 pressed - Down key
    if signum == signal.SIGUSR1:
        g_vars['sig_fired'] = True
        g_vars['key_mappings'][ g_vars['key_map'] ]['key_actions']['key1']()
        #menu_down()
        g_vars['sig_fired'] = False
        return

    # Key 2 pressed - Right/Selection key
    if signum == signal.SIGUSR2:
        g_vars['sig_fired'] = True
        g_vars['key_mappings'][ g_vars['key_map'] ]['key_actions']['key2']()
        #menu_right()
        g_vars['sig_fired'] = False
        return

    # Key 3 pressed - Left/Back key
    if signum == signal.SIGALRM:
        g_vars['sig_fired'] = True
        g_vars['key_mappings'][ g_vars['key_map'] ]['key_actions']['key3']()
        #menu_left()
        g_vars['sig_fired'] = False
        return

###############################################################################
#
# ****** MAIN *******
#
###############################################################################

# First time around (power-up), draw logo on display
rogues_gallery = [ 'wlanprologo.png', 'jolla.png', 'wifinigel.png', 'jiribrejcha.png']
random_image = random.choice(rogues_gallery)
image0 = Image.open(random_image).convert('1')

oled.drawImage(image0)
time.sleep(2)

# Set signal handlers for button presses - these fire every time a button
# is pressed
signal.signal(signal.SIGUSR1, receive_signal)
signal.signal(signal.SIGUSR2, receive_signal)
signal.signal(signal.SIGALRM, receive_signal)

##############################################################################
# Constant 'while' loop to paint images on display or execute actions in
# response to selections made with buttons. When any of the 3 WLANPi buttons
# are pressed, I believe the signal handler takes over the Python interpreter
# and executes the code associated with the button. The original flow continues
# once the button press action has been completed.
#
# The current sleep period of the while loop is ignored when a button is
# pressed.
#
# All global variables defined outside of the while loop are preserved and may
# read/set as required. The same variables are available for read/write even
# when a button is pressed and an interrupt occurs: no additional thread or
# interpreter with its own set of vars appears to be launched. For this reason,
# vars may be used to signal between the main while loop and any button press
# activity to indicate that processes such as screen paints are in progress.
#
# Despite the sample code suggesting threading is used I do not believe this
# is the case, based on testing with variable scopes and checking for process
# IDs when different parts of the script are executing.
##############################################################################
while True:

    try:

        if g_vars['shutdown_in_progress'] or g_vars['screen_cleared'] or g_vars['drawing_in_progress']:

            # we don't really want to do anything at the moment, lets
            # nap and loop around
            time.sleep(1)
            continue

        # Draw a menu or execute current action (dispatcher)
        if g_vars['display_state'] != 'menu':
            # no menu shown, so must be executing action.

            # if we've just booted up, show home page
            if g_vars['start_up'] == True:
                g_vars['option_selected'] = home_page

             # Re-run current action to refresh screen
            g_vars['option_selected']()
        else:
            # lets try drawing our page (or refresh if already painted)

            # No point in repainting screen if we are on a
            # menu page and no buttons pressed since last loop cycle
            # In reality, this condition will rarely (if ever) be true
            # as the page painting is driven from the key press which 
            # interrupts this flow anyhow. Left in as a safeguard
            if g_vars['button_press_count'] > g_vars['last_button_press_count']:
                page_obj = Page(g_vars)
                page_obj.draw_page(g_vars, menu)

        # if screen timeout is zero, clear it if not already done (blank the
        # display to reduce screenburn)
        if g_vars['pageSleepCountdown'] == 0 and g_vars['screen_cleared'] == False:
            oled.clearDisplay()
            g_vars['screen_cleared'] = True

        g_vars['pageSleepCountdown'] = g_vars['pageSleepCountdown'] - 1

        # have a nap before we start our next loop
        time.sleep(1)

    except KeyboardInterrupt:
        break
    except IOError as ex:
        print("Error " + str(ex))
    
    g_vars['last_button_press_count'] = g_vars['button_press_count']

'''
Discounted ideas

    1. Vary sleep timer for main while loop (e.g. longer for less frequently
       updating data) - doesn;t work as main while loop may be in middle of 
       long sleep when button action taken, so screen refresh very long.

'''
