#!/usr/bin/env python3

'''

This script loosely based on the original bakebit_nanonhat_oled.py provided
by Friendlyarm. It has been updated to support a scalable menu structure and
a number of additional features to support the WLANPi initiative.

History:

 0.03 - Added Switch classic/rconsole mode and USB interface listing (28/06/19)
 0.04 - Added button labels & menu scrolling (28/06/19)
 0.05 - Added check for rconsole installation
        Changed name from rconsole to wconsole (needs new wconsole files)
        Added clear_display() function
        Added standard display dialogue function (29/06/19)
 0.06 - Added simple table fuction & refactored several functions to use it
        Updated nav buttons to have optional new label
        Added menu verion display (30/06/19)
 0.07 - Added confirmation options to restart option menu selections (01/07/19)
 0.08 - Added check for interfaces in monitor mode
        Added scrolling in simple tables (02/07/2019)
 0.09 - Added paged tables and WLAN interface detail option
 0.10 - Re-arranged menu structure to give network pages own area
        Added UFW info (03/07/19)
 0.11 - Added check that UFW installed & fixed missing info issue from 0.10
        Added display_list_as_paged_table() as alternative to simple table
        page as provide better scrolling experience (04/07/19)
 0.12 - Replaced 'is_menu_shown' and 'table_displayed' with single 'display state'
        variable
        Added timezone to date page (06/07/19)
 0.13   Added early screen lock to show_summary() as causes some display issues
        due to length of time external commands take to execute (07/06/19)
 0.14   Added checks in dispatchers that run external commands to see if
        a button has been pressed before rendering page (08/07/19)
 0.15   Change "wconsole" to "Wi-Fi Console" mode (09/07/19)
 0.16   Added home page on boot-up.
        Improved mode switch dialogs
        Added more try statements to improve system calls robustness
        Simplified menu data structure for mode switch consistency (24th Jul 2019)
 0.17   Fixed bug with wireless console title missing
        Added Wi-Fi hotspot mode
        Added mode indicator on home page (26th Jul 2019)
 0.18   Added exit to home page option from top of menu (27th Jul 2019)
 0.19   Added additional menu items to support start/stop/status of kismet (30th Jul 2019)
 0.20   Added bettercap web-ui support
        Moved kismet and bettercap ctl scripts to common dir structure under
        /home/wlanpi/nanohat-oled-scripts (1st Aug 2019)
 0.21   Added profiler start/stop via front panel menu & status info.
        Re-organised menu system to have dedicated "apps" area. (2nd Aug 2019)
 0.22   Added Ethernet port speed support via Ethtool on Classic mode
        home page(3rd Aug 2019)
 0.23   Added LLDP & eth0 updates submitted by Jiri Brejcha (15th Sep 2019)
 0.24   Added usb0 as default to disply when eth0 down (16th Nov 2019)
 0.25   Added new CDP menu item, new CDP script and updated LLDP features by Jiri Brejcha (26th Nov 2019)
 0.26   DNS servers are now shown in ipconfig menu, DHCP server info is now shown correctly and only if eth0 is up, cleaned up networkinfo code in bakebit menu file by Jiri (29th Nov 2019)
 0.27   Added Wiperf support (10th Dec 2019 - Nigel)
 0.28   Added reachability display - Jiri Brejcha (17th Dec 2019)
 0.29   Re-ordered menu structure & removed menu item numbers (Nigel 18/12/2019)
 0.30   Added shutdown and reboot dialog images (Nigel 22/12/2019)
 0.31   Added main loop error handling improvement and reboot image fix (Nigel 23/12/2019)
 0.32   Minor menu updates to network info menu & tests now run when no def gw (Jiri 26/12/2019)
 0.33   Secondary addr on USB causing 2 IP addr on home page - added head command to fix (Nigel 26/12/2019)
 0.34   Speedtest added by Jiri & added disable_keys global var to ignore key presses when required. Also tidied up lots of syntax issues reported by pylint & removed old menu code.
 0.35   Converted to python3
 0.36   Moved to single fpms repo

To do:
    1. Error handling to log?
    2. Add screensaver fallback to gen status if no keys pressed for a minute?
    3. Add a screen-lock ?

'''


import bakebit_128_64_oled as oled
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw
import time
import sys
import subprocess
import signal
import os
import socket
import types
import re
from textwrap import wrap

from modules.pages.screen import *
from modules.navigation import *
from modules.tables.simpletable import * 
from modules.tables.pagedtable import * 
from modules.utils import *
from modules.pages.page import *
from modules.system.system import *
from modules.network import *
from modules.pages.homepage import *

__version__ = "0.36 (beta)"
__author__ = "wifinigel@gmail.com"

############################
# Set page sleep control
############################
pageSleep = 300
pageSleepCountdown = pageSleep

####################################
# Initialize the SEEED OLED display
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

    # Set display size
    'width': 128,
    'height': 64,

    # Set page sleep control
    'pageSleep': pageSleep,
    'pageSleepCountdown': pageSleepCountdown,

    'nav_bar_top': 55,     # top pixel of nav bar
    'home_page_name': "Home",       # Display name for top level menu
    'menu_version': __version__,   # fpms version

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
}

############################
# shared objects
############################
g_vars['image'] = Image.new('1', (g_vars['width'], g_vars['height']))
g_vars['draw'] = ImageDraw.Draw(g_vars['image'])
g_vars['reboot_image'] = Image.open('reboot.png').convert('1')

#######################################
# Initialize file variables
#######################################
# Mode changer scripts
wconsole_mode_file = '/etc/wconsole/wconsole.on'
hotspot_mode_file = '/etc/wlanpihotspot/hotspot.on'
wiperf_mode_file = '/home/wlanpi/wiperf/wiperf.on'

wconsole_switcher_file = '/etc/wconsole/wconsole_switcher'
hotspot_switcher_file = '/etc/wlanpihotspot/hotspot_switcher'
wiperf_switcher_file = '/home/wlanpi/wiperf/wiperf_switcher'

# helper scripts to launch misc processes
kismet_ctl_file = '/home/wlanpi/fpms/BakeBit/Software/Python/scripts/kismet_ctl'
bettercap_ctl_file = '/home/wlanpi/fpms/BakeBit/Software/Python/scripts/bettercap_ctl'
profiler_ctl_file = '/home/wlanpi/fpms/BakeBit/Software/Python/scripts/profiler_ctl'

# cdp and lldp networkinfo data file names
lldpneigh_file = '/tmp/lldpneigh.txt'
cdpneigh_file = '/tmp/cdpneigh.txt'
ipconfig_file = '/home/wlanpi/fpms/BakeBit/Software/Python/scripts/networkinfo/ipconfig.sh 2>/dev/null'
reachability_file = '/home/wlanpi/fpms/BakeBit/Software/Python/scripts/networkinfo/reachability.sh'
publicip_cmd = '/home/wlanpi/fpms/BakeBit/Software/Python/scripts/networkinfo/publicip.sh'

# Linux programs
ifconfig_file = '/sbin/ifconfig'
iw_file = '/usr/sbin/iw'
ufw_file = '/usr/sbin/ufw'
ethtool_file = '/sbin/ethtool'


# check our current mode
if os.path.isfile(wconsole_mode_file):
    g_vars['current_mode'] = 'wconsole'
if os.path.isfile(hotspot_mode_file):
    g_vars['current_mode'] = 'hotspot'
if os.path.isfile(wiperf_mode_file):
    g_vars['current_mode'] = 'wiperf'

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
    g_vars['hostname']

####################################
# dispatcher (menu) functions here
####################################

def switcher(resource_title, resource_switcher_file, mode_name):
    '''
    Function to perform generic set of operations to switch wlanpi mode
    '''

    global oled

    global reboot_image

    # check resource is available
    if not os.path.isfile(resource_switcher_file):

        simple_table_obj. display_dialog_msg(g_vars, '{} not available'.format(
            resource_title), back_button_req=1)
        g_vars['display_state'] = 'page'
        return

    # Resource switcher was detected, so assume it's installed
    back_button_req = 0

    if g_vars['current_mode'] == "classic":
        # if in classic mode, switch to the resource
        dialog_msg = 'Switching to {} mode (rebooting...)'.format(
            resource_title)
        switch = "on"
    elif g_vars['current_mode'] == mode_name:
        dialog_msg = 'Switching to Classic mode (rebooting...)'
        switch = "off"
    else:
        dialog_msg('Unknown mode: {}'.format(g_vars['current_mode']), back_button_req=1)
        g_vars['display_state'] = 'page'
        return False

    # Flip the mode
    simple_table_obj. display_dialog_msg(g_vars, dialog_msg, back_button_req)
    g_vars['shutdown_in_progress'] = True
    time.sleep(2)

    oled.drawImage(g_vars['reboot_image'])
    g_vars['screen_cleared'] = True

    try:
        dialog_msg = subprocess.check_output("{} {}".format(
            resource_switcher_file, switch), shell=True).decode()  # reboots
    except subprocess.CalledProcessError as exc:
        output = exc.output.decode()
        dialog_msg = mode_name

    # We only get to this point if the switch has failed for some reason
    # (Note that the switcher script reboots the WLANPi)
    g_vars['shutdown_in_progress'] = False
    g_vars['screen_cleared'] = False
    simple_table_obj. display_dialog_msg(g_vars, "Switch failed: {}".format(
        dialog_msg), back_button_req=0)
    g_vars['display_state'] = 'menu'

    # allow 5 secs to view failure msg
    time.sleep(3)
    # move back up to menu branch
    g_vars['current_menu_location'].pop()

    return False


def wconsole_switcher():

    global wconsole_switcher_file

    resource_title = "Wi-Fi Console"
    mode_name = "wconsole"
    resource_switcher_file = wconsole_switcher_file

    # switch
    switcher(resource_title, resource_switcher_file, mode_name)
    return True


def hotspot_switcher():

    global hotspot_switcher_file

    resource_title = "Hotspot"
    mode_name = "hotspot"
    resource_switcher_file = hotspot_switcher_file

    switcher(resource_title, resource_switcher_file, mode_name)
    return True


def wiperf_switcher():

    global wiperf_switcher_file

    resource_title = "Wiperf"
    mode_name = "wiperf"
    resource_switcher_file = wiperf_switcher_file

    switcher(resource_title, resource_switcher_file, mode_name)
    return True


def kismet_ctl(action="status"):
    '''
    Function to start/stop and get status of Kismet processes
    '''

    global kismet_ctl_file


    # check resource is available
    if not os.path.isfile(kismet_ctl_file):
        simple_table_obj. display_dialog_msg(g_vars, '{} not available'.format(
            kismet_ctl_file), back_button_req=1)
        g_vars['display_state'] = 'page'
        return

    if action == "status":
        # check kismet status & return text
        try:
            dialog_msg = subprocess.check_output(
                "{} {}".format(kismet_ctl_file, action), shell=True).decode()
        except subprocess.CalledProcessError as exc:
            output = exc.output.decode()
            dialog_msg = 'Status failed! {}'.format(output)

    elif action == "start":
        try:
            dialog_msg = subprocess.check_output(
                "{} {}".format(kismet_ctl_file, action), shell=True).decode()
        except subprocess.CalledProcessError as exc:
            output = exc.output.decode()
            dialog_msg = 'Start failed! {}'.format(output)

    elif action == "stop":
        try:
            dialog_msg = subprocess.check_output(
                "{} {}".format(kismet_ctl_file, action), shell=True).decode()
        except subprocess.CalledProcessError as exc:
            output = exc.output.decode()
            dialog_msg = 'Stop failed! {}'.format(output)

    simple_table_obj. display_dialog_msg(g_vars, dialog_msg, back_button_req=1)
    g_vars['display_state'] = 'page'
    return True


def kismet_status():
    kismet_ctl(action="status")
    return


def kismet_stop():
    kismet_ctl(action="stop")
    return


def kismet_start():
    kismet_ctl(action="start")
    return


def bettercap_ctl(action="status"):
    '''
    Function to start/stop and get status of Kismet processes
    '''

    global bettercap_ctl_file


    # check resource is available
    if not os.path.isfile(bettercap_ctl_file):
        simple_table_obj. display_dialog_msg(g_vars, '{} not available'.format(
            bettercap_ctl_file), back_button_req=1)
        g_vars['display_state'] = 'page'
        return

    if action == "status":
        # check bettercap status & return text
        try:
            dialog_msg = subprocess.check_output(
                "{} {}".format(bettercap_ctl_file, action), shell=True).decode()
        except subprocess.CalledProcessError as exc:
            output = exc.output.decode()
            dialog_msg = 'Status failed! {}'.format(output)

    elif action == "start":
        try:
            dialog_msg = subprocess.check_output(
                "{} {}".format(bettercap_ctl_file, action), shell=True).decode()
        except subprocess.CalledProcessError as exc:
            output = exc.output.decode()
            dialog_msg = 'Start failed! {}'.format(output)

    elif action == "stop":
        try:
            dialog_msg = subprocess.check_output(
                "{} {}".format(bettercap_ctl_file, action), shell=True).decode()
        except subprocess.CalledProcessError as exc:
            output = exc.output.decode()
            dialog_msg = 'Stop failed! {}'.format(output)

    simple_table_obj. display_dialog_msg(g_vars, dialog_msg, back_button_req=1)
    g_vars['display_state'] = 'page'
    return True


def bettercap_status():
    bettercap_ctl(action="status")
    return


def bettercap_stop():
    bettercap_ctl(action="stop")
    return


def bettercap_start():
    bettercap_ctl(action="start")
    return


def profiler_ctl(action="status"):
    '''
    Function to start/stop and get status of Profiler processe
    '''

    global profiler_ctl_file


    # check resource is available
    if not os.path.isfile(profiler_ctl_file):
        simple_table_obj. display_dialog_msg(g_vars, 'not available: {}'.format(
            profiler_ctl_file), back_button_req=1)
        g_vars['display_state'] = 'page'
        return

    if action == "status":
        # check profiler status & return text
        try:
            status_file_content = subprocess.check_output(
                "{} {}".format(profiler_ctl_file, action), shell=True).decode()
            item_list = status_file_content.splitlines()
        except subprocess.CalledProcessError as exc:
            output = exc.output.decode()
            item_list = ['Status failed!', str(output)]

        simple_table_obj.display_simple_table(g_vars, item_list, back_button_req=1,
                             title='Profiler Status')
        g_vars['display_state'] = 'page'
        return True

    elif action == "start":
        try:
            dialog_msg = subprocess.check_output(
                "{} {}".format(profiler_ctl_file, action), shell=True).decode()
        except subprocess.CalledProcessError as exc:
            output = exc.output.decode()
            dialog_msg = 'Start failed! {}'.format(output)

    elif action == "start_no11r":
        try:
            dialog_msg = subprocess.check_output(
                "{} {}".format(profiler_ctl_file, action), shell=True).decode()
        except subprocess.CalledProcessError as exc:
            output = exc.output.decode()
            dialog_msg = 'Start failed! {}'.format(output)

    elif action == "stop":
        try:
            dialog_msg = subprocess.check_output(
                "{} {}".format(profiler_ctl_file, action), shell=True).decode()
        except subprocess.CalledProcessError as exc:
            output = exc.output.decode()
            dialog_msg = 'Stop failed! {}'.format(output)

    elif action == "purge":
        try:
            dialog_msg = subprocess.check_output(
                "{} {}".format(profiler_ctl_file, action), shell=True).decode()
        except subprocess.CalledProcessError as exc:
            output = exc.output.decode()
            dialog_msg = 'Report purge failed! {}'.format(output)

    simple_table_obj. display_dialog_msg(g_vars, dialog_msg, back_button_req=1)
    g_vars['display_state'] = 'page'
    return True


def profiler_status():
    profiler_ctl(action="status")
    return


def profiler_stop():
    profiler_ctl(action="stop")
    return


def profiler_start():
    profiler_ctl(action="start")
    return


def profiler_start_no11r():
    profiler_ctl(action="start_no11r")
    return


def profiler_purge():
    profiler_ctl(action="purge")
    return

#######################
# other functions here
#######################





def menu_down():

    global menu


    # If we are in a table, scroll down (unless at bottom of list)
    if g_vars['display_state'] == 'page':
        g_vars['current_scroll_selection'] += 1
        return

    # Menu not currently shown, do nothing
    if g_vars['display_state'] != 'menu':
        return

    # pop the last menu list item, increment & push back on
    current_selection = g_vars['current_menu_location'].pop()
    current_selection = current_selection + 1
    g_vars['current_menu_location'].append(current_selection)

    page_obj.draw_page(g_vars, menu)


def menu_right(g_vars=g_vars):

    global menu

    global speedtest_status

    # make sure we know speedtest is done
    g_vars['speedtest_status'] = False

    # If we are in a table, scroll up (unless at top of list)
    if g_vars['display_state'] == 'page':
        if g_vars['current_scroll_selection'] == 0:
            return
        else:
            g_vars['current_scroll_selection'] -= 1
            return

    # Check if the "action" field at the current location is an
    # array or a function.

    # if we have an array, append the current selection and re-draw menu
    if (type(g_vars['option_selected']) is list):
        g_vars['current_menu_location'].append(0)
        page_obj.draw_page(g_vars, menu)
    elif (isinstance(g_vars['option_selected'], types.FunctionType)):
        # if we have a function (dispatcher), execute it
        g_vars['display_state'] = 'page'
        g_vars['option_selected']()


def menu_left():

    global menu

    # If we're in a table we need to exit, reset table scroll counters, reset
    # result cache and draw the menu for our current level
    if g_vars['display_state'] == 'page':
        g_vars['current_scroll_selection'] = 0
        g_vars['table_list_length'] = 0
        g_vars['display_state'] = 'menu'
        page_obj.draw_page(g_vars, menu)
        g_vars['result_cache'] = False
        return

    if g_vars['display_state'] == 'menu':

        # check to make sure we aren't at top of menu structure
        if len(g_vars['current_menu_location']) == 1:
            # If we're at the top and hit exit (back) button, revert to start-up state
            g_vars['start_up'] = True
            home_page()
        else:
            g_vars['current_menu_location'].pop()
            page_obj.draw_page(g_vars, menu)
    else:
        g_vars['display_state'] = 'menu'
        page_obj.draw_page(g_vars, menu)


def go_up():

    # executed when the back navigation item is selected

    g_vars['display_state'] = 'menu'

    if len(g_vars['current_menu_location']) == 1:
        # we must be at top level, do nothing
        return
    else:
        # Take off last level of menu structure to go up
        # Set index to 0 so top menu item selected
        g_vars['current_menu_location'].pop()
        g_vars['current_menu_location'][-1] = 0

        page_obj.draw_page(g_vars, menu)

# Instantiate objects
screen_obj = Screen(g_vars)
simple_table_obj = SimpleTable(g_vars)
nav_button_obj = NavButton(g_vars, 255, g_vars['smartFont'])
paged_table_obj = PagedTable(g_vars)
page_obj = Page(g_vars)

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

def home_page():
    homepage_obj = HomePage(g_vars)
    homepage_obj.home_page(g_vars, menu)

# Set up handlers to process key presses


def receive_signal(signum, stack, g_vars=g_vars):

    global pageSleepCountdown
    global pageSleep
    global disable_keys

    if g_vars['disable_keys'] == True:
        # someone disabled the front panel keys as they don't want to be interrupted
        return

    if (g_vars['sig_fired']):
        # signal handler already in progress, ignore this one
        return

    # user pressed a button, reset the sleep counter
    pageSleepCountdown = pageSleep

    g_vars['start_up'] = False

    if g_vars['drawing_in_progress'] or g_vars['shutdown_in_progress']:
        return

    # if display has been switched off to save screen, power back on and show home menu
    if g_vars['screen_cleared']:
        g_vars['screen_cleared'] = False
        pageSleepCountdown = pageSleep
        return

    # Key 1 pressed - Down key
    if signum == signal.SIGUSR1:
        g_vars['sig_fired'] = True
        menu_down()
        g_vars['sig_fired'] = False
        return

    # Key 2 pressed - Right/Selection key
    if signum == signal.SIGUSR2:
        g_vars['sig_fired'] = True
        menu_right()
        g_vars['sig_fired'] = False
        return

    # Key 3 pressed - Left/Back key
    if signum == signal.SIGALRM:
        g_vars['sig_fired'] = True
        menu_left()
        g_vars['sig_fired'] = False
        return

###############################################################################
#
# ****** MAIN *******
#
###############################################################################


# First time around (power-up), draw logo on display
image0 = Image.open('wlanprologo.png').convert('1')
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
            page_obj.draw_page(g_vars, menu)

        # if screen timeout is zero, clear it if not already done (blank the
        # display to reduce screenburn)
        if pageSleepCountdown == 0 and g_vars['screen_cleared'] == False:
            oled.clearDisplay()
            g_vars['screen_cleared'] = True

        pageSleepCountdown = pageSleepCountdown - 1

        # have a nap before we start our next loop
        time.sleep(1)

    except KeyboardInterrupt:
        break
    except IOError as ex:
        print("Error " + str(ex))

'''
Discounted ideas

    1. Vary sleep timer for main while loop (e.g. longer for less frequently
       updating data) - doesn;t work as main while loop may be in middle of 
       long sleep when button action taken, so screen refresh very long.

'''
