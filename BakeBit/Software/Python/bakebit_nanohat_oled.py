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

from modules.navigation import *

__version__ = "0.36 (beta)"
__author__ = "wifinigel@gmail.com"

############################
# Set display size
############################
width = 128
height = 64

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
# Initialize drawing & fonts variables
#######################################

# This variable is shared between activities and is set to True if a
# drawing action in already if progress (e.g. by another activity). An activity
# happens during each cycle of the main while loop or when a button is pressed
# (This does not appear to be threading or process spawning)
drawing_in_progress = False

#####################################
# Create global draw/image objects
#####################################
image = Image.new('1', (width, height))
draw = ImageDraw.Draw(image)

reboot_image = Image.open('reboot.png').convert('1')

#######################
# Define display fonts
#######################
smartFont = ImageFont.truetype('DejaVuSansMono-Bold.ttf', 10)
font11 = ImageFont.truetype('DejaVuSansMono.ttf', 11)
font12 = ImageFont.truetype('DejaVuSansMono.ttf', 12)
fontb12 = ImageFont.truetype('DejaVuSansMono-Bold.ttf', 12)
font14 = ImageFont.truetype('DejaVuSansMono.ttf', 14)
fontb14 = ImageFont.truetype('DejaVuSansMono-Bold.ttf', 14)
fontb24 = ImageFont.truetype('DejaVuSansMono-Bold.ttf', 24)

#######################################
# Initialize various global variables
#######################################
shutdown_in_progress = False  # True when shutdown or reboot started
screen_cleared = False        # True when display cleared (e.g. screen save)
current_menu_location = [0]   # Pointer to current location in menu structure
option_selected = 0           # Content of currently selected menu level
sig_fired = False             # Set to True when button handler fired
home_page_name = "Home"       # Display name for top level menu
current_mode = "classic"      # Currently selected mode (e.g. wconsole/classic)
nav_bar_top = 55              # top pixel of nav bar
current_scroll_selection = 0  # where we currently are in scrolling table
table_list_length = 0         # Total length of currently displayed table
result_cache = False          # used to cache results when paging info
display_state = 'page'        # current display state: 'page' or 'menu'
start_up = True               # True if in initial (home page) start-up state
disable_keys = False          # Set to true when need to ignore key presses
speedtest_status = False      # Indicates if speedtest has run or is in progress
speedtest_result_text = ''    # tablulated speedtest result data

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
    current_mode = 'wconsole'
if os.path.isfile(hotspot_mode_file):
    current_mode = 'hotspot'
if os.path.isfile(wiperf_mode_file):
    current_mode = 'wiperf'


# get & the current version of WLANPi image
ver_cmd = "grep \"WLAN Pi v\" /var/www/html/index.html | sed \"s/<[^>]\+>//g\""
try:
    wlanpi_ver = subprocess.check_output(ver_cmd, shell=True).decode().strip()
except:
    wlanpi_ver = "unknown"

# get hostname
try:
    hostname = subprocess.check_output('hostname', shell=True).decode()
except:
    hostname = "unknown"

#############################
# Get current IP for display
#############################


def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP


# Create obj for on-screen button labels
nav_button_obj = NavButton(draw, nav_bar_top, 255, smartFont)


##############################################
# Page & menu functions
##############################################


def clear_display():
    '''
    Paint display black prior to painting new page
    '''

    global width
    global height
    global draw

    # Draw a black filled box to clear the display.
    draw.rectangle((0, 0, width, height), outline=0, fill=0)


def display_simple_table(item_list, back_button_req=0, title='', font="small"):
    '''
    This function takes a list and paints each entry as a line on a
    page. It also displays appropriate up/down scroll buttons if the
    entries passed exceed a page length (one line at a time)
    '''

    global drawing_in_progress
    global draw
    global oled
    global current_scroll_selection
    global table_list_length
    global display_state

    drawing_in_progress = True
    display_state = 'page'

    # Clear display prior to painting new item
    clear_display()

    y = 0
    x = 0
    font_offset = 0

    if font == "small":
        font_type = smartFont
        font_size = 11
        item_length_max = 20
        table_display_max = 5
    elif font == "medium":
        font_type = font11
        font_size = 11
        item_length_max = 17
        table_display_max = 4

    # write title if present
    if title != '':
        draw.text((x, y + font_offset), title.center(item_length_max,
                                                     " "),  font=font_type, fill=255)
        font_offset += font_size
        table_display_max -= 1

    previous_table_list_length = table_list_length
    table_list_length = len(item_list)

    # if table length changes, reset current scroll selection
    # e.g. when showing lldp table info and eth cable
    # pulled so list size changes
    if table_list_length != previous_table_list_length:
        current_scroll_selection = 0

    # if we're going to scroll of the end of the list, adjust pointer
    if current_scroll_selection + table_display_max > table_list_length:
        current_scroll_selection -= 1

    # modify list to display if scrolling required
    if table_list_length > table_display_max:

        table_bottom_entry = current_scroll_selection + table_display_max
        item_list = item_list[current_scroll_selection: table_bottom_entry]

        # show down if not at end of list in display window
        if table_bottom_entry < table_list_length:
            nav_button_obj.down()

        # show an up button if not at start of list
        if current_scroll_selection > 0:
            nav_button_obj.next(label="Up")

    for item in item_list:

        if len(item) > item_length_max:
            item = item[0:item_length_max]

        draw.text((x, y + font_offset), item,  font=font_type, fill=255)

        font_offset += font_size

    # Back button
    if back_button_req:
        nav_button_obj.back(label="Exit")

    oled.drawImage(image)

    display_state = 'page'
    drawing_in_progress = False

    return


def display_dialog_msg(msg, back_button_req=0, wrap_limit=17, font="medium"):
    '''
    display informational dialog box
    '''

    global draw
    global oled
    global drawing_in_progress
    global display_state

    msg_list = wrap(msg, wrap_limit)
    display_simple_table(msg_list, back_button_req, title='Info:', font=font)


def display_paged_table(table_data, back_button_req=0):
    '''
    This function takes several pages of information and displays on the
    display with appropriate pg up/pg down buttons

    table data is in format:

    data = {
        'title' = 'page title',
        'pages' = [
                ['Page 1 line 1', Page 1 line 2, 'Page 1 line 3', 'Page 1 line 4'],
                ['Page 2 line 1', Page 2 line 2, 'Page 2 line 3', 'Page 2 line 4'],
                ['Page 3 line 1', Page 3 line 2, 'Page 3 line 3', 'Page 3 line 4'],
                ...etc.
        ]
    }
    '''

    global drawing_in_progress
    global draw
    global oled
    global current_scroll_selection
    global table_list_length
    global display_state

    drawing_in_progress = True
    display_state = 'page'

    # Clear display prior to painting new item
    clear_display()

    y = 0
    x = 0
    font_offset = 0
    font_size = 11
    item_length_max = 20
    table_display_max = 4

    # write title
    title = table_data['title']
    total_pages = len(table_data['pages'])

    if total_pages > 1:
        title += " ({}/{})".format(current_scroll_selection + 1, total_pages)

    draw.text((x, y + font_offset), title.center(item_length_max,
                                                 " "),  font=smartFont, fill=255)

    font_offset += font_size

    # Extract pages data
    table_pages = table_data['pages']
    page_count = len(table_pages)

    # Display the page selected - correct over-shoot of page down
    if current_scroll_selection == page_count:
        current_scroll_selection -= 1

    # Correct over-shoot of page up
    if current_scroll_selection == -1:
        current_scroll_selection = 0

    page = table_pages[current_scroll_selection]

    # If the page has greater than table_display_max entries, slice it
    if len(page) > table_display_max:
        page = page[0:table_display_max]

    for item in page:

        if len(item) > item_length_max:
            item = item[0:item_length_max]

        draw.text((x, y + font_offset), item,  font=smartFont, fill=255)

        font_offset += font_size

    # if we're going need to scroll through pages, create buttons
    if (page_count > 1):

        # if (current_scroll_selection < page_count) and (current_scroll_selection < page_count-1):
        if current_scroll_selection < page_count-1:
            nav_button_obj.down(label="PgDn")

        if (current_scroll_selection > 0) and (current_scroll_selection <= page_count - 1):
            nav_button_obj.next(label="PgUp")

    # Back button
    if back_button_req:
        nav_button_obj.back(label="Exit")

    oled.drawImage(image)

    display_state = 'page'
    drawing_in_progress = False

    return


def display_list_as_paged_table(item_list, back_button_req=0, title=''):
    '''
    This function builds on display_paged_table() and creates a paged display
    from a simple list of results. This provides a better experience that the
    simple line-by-line scrolling provided in display_simple_table()

    See display_paged_table() for required data structure
    '''
    data = {}

    data['title'] = title
    data['pages'] = []

    # slice up list in to pages
    table_display_max = 4

    counter = 0
    while item_list:
        slice = item_list[counter: counter+table_display_max]
        data['pages'].append(slice)
        item_list = item_list[counter+table_display_max:]

    display_paged_table(data, back_button_req)

    return

##############################################
# Main function to draw menu navigation pages
##############################################


def draw_page():
    global drawing_in_progress
    global image
    global draw
    global oled
    global font
    global fontb12
    global font14
    global smartFont
    global width
    global height
    global width
    global height
    global pageSleepCountdown
    global current_menu_location
    global option_selected
    global option_number_selected
    global menu
    global home_page_name
    global display_state

    # Drawing already in progress - return
    if drawing_in_progress:
        return

    # signal we are drawing
    drawing_in_progress = True

    ################################################
    # show menu list based on current menu position
    ################################################

    # FIXME: This feels clunky. Would be best to access menu locations
    #       via evaluated location rather than crawling over menu

    menu_structure = menu
    location_search = []
    depth = 0
    section_name = [home_page_name]

    # Crawl the menu structure until we hit the current specified location
    while current_menu_location != location_search:

        # List that will be used to build menu items to display
        menu_list = []

        # Current menu location choice specified in list format:
        #  current_menu_location = [2,1]
        #
        # As we move though menu depths, inpsect next level of
        # menu structure
        node = current_menu_location[depth]

        # figure out the number of menu options at this menu level
        number_menu_choices = len(menu_structure)

        if node == number_menu_choices:

            # we've fallen off the end of menu choices, fix item by zeroing
            node = 0
            current_menu_location[depth] = 0

        location_search.append(node)

        item_counter = 0

        for menu_item in menu_structure:

            item_name = menu_item['name']

            # this is the currently selected item, pre-pend name with '*'
            if (item_counter == node):
                section_name.append(item_name)
                item_name = "*" + item_name

            menu_list.append((item_name))

            item_counter = item_counter + 1

        depth = depth + 1

        # move down to next level of menu structure & repeat for new level
        menu_structure = menu_structure[node]['action']

    option_number_selected = node
    option_selected = menu_structure

    # if we're at the top of the menu tree, show the home page title
    if depth == 1:
        page_name = home_page_name
    else:
        # otherwise show the name of the parent menu item
        page_name = section_name[-2]

    page_title = ("[ " + page_name + " ]").center(17, " ")

    # Clear display prior to painting new item
    clear_display()

    # paint the page title
    draw.text((1, 1), page_title,  font=fontb12, fill=255)

    # vertical starting point for menu (under title) & incremental offset for
    # subsequent items
    y = 15
    y_offset = 13

    # define display window limit for menu table
    table_window = 3

    # determine the menu list to show based on current selection and window limits
    if (len(menu_list) > table_window):

        # We've got more items than we can fit in our window, need to slice to fit
        if (option_number_selected >= table_window):
            menu_list = menu_list[(
                option_number_selected - (table_window - 1)): option_number_selected + 1]
        else:
            # We have enough space for the menu items, so no special treatment required
            menu_list = menu_list[0: table_window]

    # paint the menu items, highlighting selected menu item
    for menu_item in menu_list:

        rect_fill = 0
        text_fill = 255

        # this is selected menu item: highlight it and remove * character
        if (menu_item[0] == '*'):
            rect_fill = 255
            text_fill = 0
            menu_item = menu_item[1:len(menu_item)]

        # convert menu item to std width format with nav indicator
        menu_item = "{:<17}>".format(menu_item)

        draw.rectangle((0, y, 127, y+y_offset), outline=0, fill=rect_fill)
        draw.text((1, y+1), menu_item,  font=font11, fill=text_fill)
        y += y_offset

    # add nav buttons
    nav_button_obj.down()
    nav_button_obj.next()
    # Don't show back button at top level of menu
    if depth != 1:
        nav_button_obj.back()
    else:
        nav_button_obj.back(label="Exit")

    oled.drawImage(image)

    drawing_in_progress = False

####################################
# dispatcher (menu) functions here
####################################


def show_summary():
    '''
    Summary page - taken from original bakebit script
    '''

    global width
    global height
    global draw
    global oled
    global display_state
    global drawing_in_progress

    # The commands here take quite a while to execute, so lock screen early
    # (normally done by page drawing function)
    drawing_in_progress = True

    IPAddress = get_ip()

    # determine CPU load
    cmd = "top -bn1 | grep load | awk '{printf \"CPU Load: %.2f\", $(NF-2)}'"
    try:
        CPU = subprocess.check_output(cmd, shell=True).decode()
    except:
        CPU = "unknown"

    # determine mem useage
    cmd = "free -m | awk 'NR==2{printf \"Mem: %s/%sMB %.2f%%\", $3,$2,$3*100/$2 }'"
    try:
        MemUsage = subprocess.check_output(cmd, shell=True).decode()
    except:
        MemUsage = "unknown"

    # determine disk util
    cmd = "df -h | awk '$NF==\"/\"{printf \"Disk: %d/%dGB %s\", $3,$2,$5}'"
    try:
        Disk = subprocess.check_output(cmd, shell=True).decode()
    except:
        Disk = "unknown"

    # determine temp
    try:
        tempI = int(open('/sys/class/thermal/thermal_zone0/temp').read())
    except:
        tempI = "unknown"

    if tempI > 1000:
        tempI = tempI/1000
    tempStr = "CPU TEMP: %sC" % str(tempI)

    results = [
        "IP: " + str(IPAddress),
        str(CPU),
        str(MemUsage),
        str(Disk),
        tempStr
    ]

    # final check no-one pressed a button before we render page
    if display_state == 'menu':
        return

    display_simple_table(results, back_button_req=1)

    return


def show_date():
    '''
    Date page - taken from original bakebit script & modified to add TZ

    '''

    global width
    global height
    global draw
    global oled
    global display_state
    global drawing_in_progress

    drawing_in_progress = True

    # Clear display prior to painting new item
    clear_display()

    text = time.strftime("%A")
    draw.text((1, 0), text, font=font12, fill=255)
    text = time.strftime("%e %b %Y")
    draw.text((1, 13), text, font=font12, fill=255)
    text = time.strftime("%X")
    draw.text((1, 26), text, font=fontb14, fill=255)
    text = time.strftime("%Z")
    draw.text((1, 41), "TZ: " + text, font=font12, fill=255)

    # Back button
    nav_button_obj.back()

    oled.drawImage(image)

    display_state = 'page'
    drawing_in_progress = False


def show_interfaces():
    '''
    Return a list of network interfaces found to be up, with IP address if available
    '''

    global ifconfig_file
    global iw_file
    global display_state

    try:
        ifconfig_info = subprocess.check_output(
            ifconfig_file, shell=True).decode()
    except Exception as ex:
        interfaces = ["Err: ifconfig error", str(ex)]
        display_simple_table(interfaces, back_button_req=1)
        return

    # Extract interface info with a bit of regex magic
    interface_re = re.findall(
        r'^(\w+?)\: flags(.*?)RX packets', ifconfig_info, re.DOTALL | re.MULTILINE)
    if interface_re is None:
        # Something broke is our regex - report an issue
        interfaces = ["Error: match error"]
    else:
        interfaces = []
        for result in interface_re:

            # save the interface name
            interface_name = result[0]
            if re.match(r'^eth', interface_name):
                interface_name = "e{}".format(interface_name[-1])
            elif re.match(r'^wlan', interface_name):
                interface_name = "w{}".format(interface_name[-1])
            elif re.match(r'^usb', interface_name):
                interface_name = "u{}".format(interface_name[-1])
            elif re.match(r'^zt', interface_name):
                interface_name = "zt"

            # look at the rest of the interface info & extract IP if available
            interface_info = result[1]

            inet_search = re.search(
                "inet (.+?) ", interface_info, re.MULTILINE)
            if inet_search is None:
                ip_address = "No IP address"

                # do check if this is an interface in monitor mode
                if (re.search(r"wlan\d", interface_name, re.MULTILINE)):

                    # fire up 'iw' for this interface (hmmm..is this a bit of an un-necessary ovehead?)
                    try:
                        iw_info = subprocess.check_output(
                            '{} {} info'.format(iw_file, interface_name), shell=True).decode()

                        if re.search("type monitor", iw_info, re.MULTILINE):
                            ip_address = "(Monitor)"
                    except:
                        ip_address = "unknown"
            else:
                ip_address = inet_search.group(1)

            interfaces.append('{}: {}'.format(interface_name, ip_address))

    # final check no-one pressed a button before we render page
    if display_state == 'menu':
        return

    display_list_as_paged_table(
        interfaces, back_button_req=1, title="--Interfaces--")


def show_wlan_interfaces():
    '''
    Create pages to summarise WLAN interface info
    '''

    global ifconfig_file
    global iw_file
    global display_state

    try:
        ifconfig_info = subprocess.check_output(
            '{} -s'.format(ifconfig_file), shell=True).decode()
    except Exception as ex:
        interfaces = ["Err: ifconfig error", str(ex)]
        display_simple_table(interfaces, back_button_req=1)
        return

    # Extract interface info
    interface_re = re.findall(
        r'^(wlan\d)  ', ifconfig_info, re.DOTALL | re.MULTILINE)
    if interface_re is None:
        interfaces = ["Error: match error"]
    else:

        interfaces = []
        for interface_name in interface_re:

            interface_info = []

            # use iw to find further info for each wlan interface
            try:
                iw_info = subprocess.check_output(
                    "{} {} info".format(iw_file, interface_name), shell=True).decode()
            except:
                iw_info = "Err: iw cmd failed"

            # split the output in to an array
            iw_list = iw_info.split('\n')

            interface_details = {}

            for iw_item in iw_list:

                iw_item = iw_item.strip()

                fields = iw_item.split()

                # skip empty lines
                if not fields:
                    continue

                interface_details[fields[0]] = fields[1:]

            # construct our page data - start with name
            interface_info.append("Interface: " + interface_name)

            # SSID (if applicable)
            if 'ssid' in interface_details.keys():
                interface_info.append(
                    "SSID: " + str(interface_details['ssid'][0]))
            else:
                interface_info.append("SSID: N/A")

            # Mode
            if 'type' in interface_details.keys():
                interface_info.append(
                    "Mode: " + str(interface_details['type'][0]))
            else:
                interface_info.append("Mode: N/A")

            # Channel
            if 'channel' in interface_details.keys():
                interface_info.append("Ch: {} ({}Mhz)".format(
                    str(interface_details['channel'][0]), str(interface_details['channel'][4])))
            else:
                interface_info.append("Ch: unknown")

            # MAC
            if 'addr' in interface_details.keys():
                interface_info.append(
                    "Addr: " + str(interface_details['addr']))
            else:
                interface_info.append("Addr: unknown")

            interfaces.append(interface_info)

        # if we had no WLAN interfaces, insert message
        if len(interfaces) == 0:
            interfaces.append(['No Wlan Interfaces'])

    data = {
        'title': '--WLAN I/F--',
        'pages': interfaces
    }

    # final check no-one pressed a button before we render page
    if display_state == 'menu':
        return

    display_paged_table(data, back_button_req=1)


def show_usb():
    '''
    Return a list of non-Linux USB interfaces found with the lsusb command
    '''
    global display_state

    lsusb = r'/usr/bin/lsusb | /bin/grep -v Linux | /usr/bin/cut -d\  -f7-'
    lsusb_info = []

    try:
        lsusb_output = subprocess.check_output(lsusb, shell=True).decode()
        lsusb_info = lsusb_output.split('\n')
    except subprocess.CalledProcessError as exc:
        output = exc.output.decode()
        #error_descr = "Issue getting usb info using lsusb command"
        interfaces = ["Err: lsusb error", str(output)]
        display_simple_table(interfaces, back_button_req=1)
        return

    interfaces = []

    for result in lsusb_info:

        # chop down the string to fit the display
        result = result[0:19]

        interfaces.append(result)

    if len(interfaces) == 0:
        interfaces.append("No devices detected")

    # final check no-one pressed a button before we render page
    if display_state == 'menu':
        return

    display_simple_table(interfaces, back_button_req=1,
                         title='--USB Interfaces--')

    return


def show_ufw():
    '''
    Return a list ufw ports
    '''
    global ufw_file
    global result_cache
    global display_state

    ufw_info = []

    # check ufw is available
    if not os.path.isfile(ufw_file):

        display_dialog_msg('UFW not installed', back_button_req=1)

        display_state = 'page'
        return

    # If no cached ufw data from previous screen paint, run ufw status
    if result_cache == False:

        try:
            ufw_output = subprocess.check_output(
                "sudo {} status".format(ufw_file), shell=True).decode()
            ufw_info = ufw_output.split('\n')
            result_cache = ufw_info  # cache results
        except Exception as ex:
            error_descr = "Issue getting ufw info using ufw command"
            interfaces = ["Err: ufw error", error_descr, str(ex)]
            display_simple_table(interfaces, back_button_req=1)
            return
    else:
        # we must have cached results from last time
        ufw_info = result_cache

    port_entries = []

    # Add in status line
    port_entries.append(ufw_info[0])

    # lose top 4 & last 2 lines of output
    ufw_info = ufw_info[4:-2]

    for result in ufw_info:

        # tidy/compress the output
        result = result.strip()
        result_list = result.split()

        final_result = ' '.join(result_list)

        port_entries.append(final_result)

    if len(port_entries) == 0:
        port_entries.append("No ufw info detected")

    # final check no-one pressed a button before we render page
    if display_state == 'menu':
        return

    display_list_as_paged_table(
        port_entries, back_button_req=1, title='--UFW Summary--')

    return


def show_eth0_ipconfig():
    '''
    Return IP configuration of eth0 including IP, default gateway, DNS servers
    '''
    global display_state

    eth0_ipconfig_info = []

    try:
        ipconfig_output = subprocess.check_output(
            ipconfig_file, shell=True).decode()
        ipconfig_info = ipconfig_output.split('\n')

    except subprocess.CalledProcessError as exc:
        output = exc.output.decode()
        #error_descr = "Issue getting ipconfig"
        ipconfigerror = ["Err: ipconfig command error", output]
        display_simple_table(ipconfigerror, back_button_req=1)
        return

    if len(ipconfig_info) == 0:
        eth0_ipconfig_info.append("Nothing to display")

    for n in ipconfig_info:
        eth0_ipconfig_info.append(n)

    # chop down output to fit up to 2 lines on display
    choppedoutput = []

    for n in eth0_ipconfig_info:
        choppedoutput.append(n[0:20])
        if len(n) > 20:
            choppedoutput.append(n[20:40])

    # final check no-one pressed a button before we render page
    if display_state == 'menu':
        return

    display_simple_table(choppedoutput, back_button_req=1,
                         title='--Eth0 IP Config--')

    return


def show_lldp_neighbour():
    '''
    Display LLDP neighbour on eth0
    '''
    global display_state

    neighbour_info = []
    neighbour_cmd = "sudo cat " + lldpneigh_file

    if os.path.exists(lldpneigh_file):

        try:
            neighbour_output = subprocess.check_output(
                neighbour_cmd, shell=True).decode()
            neighbour_info = neighbour_output.split('\n')

        except subprocess.CalledProcessError as exc:
            output = exc.output.decode()
            #error_descr = "Issue getting LLDP neighbour"
            error = ["Err: Neighbour command error", output]
            display_simple_table(error, back_button_req=1)
            return

    if len(neighbour_info) == 0:
        neighbour_info.append("No neighbour")

    # chop down output to fit up to 2 lines on display
    choppedoutput = []

    for n in neighbour_info:
        choppedoutput.append(n[0:20])
        if len(n) > 20:
            choppedoutput.append(n[20:40])

    # final check no-one pressed a button before we render page
    if display_state == 'menu':
        return

    display_simple_table(choppedoutput, back_button_req=1,
                         title='--LLDP Neighbour--')


def show_cdp_neighbour():
    '''
    Display CDP neighbour on eth0
    '''
    global display_state

    neighbour_info = []
    neighbour_cmd = "sudo cat " + cdpneigh_file

    if os.path.exists(cdpneigh_file):

        try:
            neighbour_output = subprocess.check_output(
                neighbour_cmd, shell=True).decode()
            neighbour_info = neighbour_output.split('\n')

        except subprocess.CalledProcessError as exc:
            output = exc.output.decode()
            #error_descr = "Issue getting LLDP neighbour"
            error = ["Err: Neighbour command error", output]
            display_simple_table(error, back_button_req=1)
            return

    if len(neighbour_info) == 0:
        neighbour_info.append("No neighbour")

    # chop down output to fit up to 2 lines on display
    choppedoutput = []

    for n in neighbour_info:
        choppedoutput.append(n[0:20])
        if len(n) > 20:
            choppedoutput.append(n[20:40])

    # final check no-one pressed a button before we render page
    if display_state == 'menu':
        return

    display_simple_table(choppedoutput, back_button_req=1,
                         title='--CDP Neighbour--')


def show_reachability():
    '''
    Check if default gateway, internet and DNS are reachable and working
    '''
    global display_state

    reachability_info = []
    reachability_cmd = "sudo " + reachability_file

    try:
        reachability_output = subprocess.check_output(
            reachability_cmd, shell=True).decode()
        reachability_info = reachability_output.split('\n')

    except subprocess.CalledProcessError as exc:
        output = exc.output.decode()
        #error_descr = "Issue getting reachability info"
        error = ["Err: Reachability command error", output]
        display_simple_table(error, back_button_req=1)
        return

    if len(reachability_info) == 0:
        reachability_info.append("No output sorry")

    # chop down output to fit up to 2 lines on display
    choppedoutput = []

    for n in reachability_info:
        choppedoutput.append(n[0:20])
        if len(n) > 20:
            choppedoutput.append(n[20:40])

    # final check no-one pressed a button before we render page
    if display_state == 'menu':
        return

    display_simple_table(choppedoutput, back_button_req=1,
                         title='--Reachability--')


def show_vlan():
    '''
    Display untagged VLAN number on eth0
    Todo: Add tagged VLAN info
    '''

    global display_state

    vlan_info = []

    vlan_cmd = "sudo grep -a VLAN " + lldpneigh_file + \
        " || grep -a VLAN " + cdpneigh_file

    if os.path.exists(lldpneigh_file):

        try:
            vlan_output = subprocess.check_output(
                vlan_cmd, shell=True).decode()
            vlan_info = vlan_output.split('\n')

        except subprocess.CalledProcessError as exc:
            #output = exc.output.decode()
            #error_descr = "Issue getting VLAN info"
            error = ["No VLAN found"]
            display_simple_table(error, back_button_req=1)
            return

    if len(vlan_info) == 0:
        vlan_info.append("No VLAN found")

    # final chop down of the string to fit the display
    for n in vlan_info:
        n = n[0:19]

    # final check no-one pressed a button before we render page
    if display_state == 'menu':
        return

    display_simple_table(vlan_info, back_button_req=1, title='--Eth0 VLAN--')


def show_wpa_passphrase():
    '''
    Show WPA passphrase
    '''
    global display_state

    swpc = "sudo grep 'wpa_passphrase' /etc/hostapd.conf | cut -d '=' -f2"

    try:
        wpa_passphrase = []
        wpa_passphrase_output = subprocess.check_output(
            swpc, shell=True).decode()
        wpa_passphrase.append(wpa_passphrase_output)

    except subprocess.CalledProcessError as exc:
        output = exc.output.decode()
        #error_descr = "Issue getting WPA passphrase"
        swperror = ["Err: WPA passphrase", output]
        display_simple_table(swperror, back_button_req=1)
        return

    # final check no-one pressed a button before we render page
    if display_state == 'menu':
        return

    # chop down output to fit up to 2 lines on display
    choppedoutput = []

    for n in wpa_passphrase:
        choppedoutput.append(n[0:20])
        if len(n) > 20:
            choppedoutput.append(n[20:40])

    display_simple_table(choppedoutput, back_button_req=1,
                         title='--WPA passphrase--')


def show_speedtest():
    '''
    Run speedtest.net speed test and format output to fit the OLED screen
    ( *** Note that speedtest_status set back to False in menu_right() *** )
    '''
    global display_state
    global disable_keys
    global speedtest_status
    global speedtest_result_text

    # Has speedtest been run already?
    if speedtest_status == False:

        # ignore any more key presses as this could cause us issues
        disable_keys = True

        display_dialog_msg(
            'Running Speedtest. Please wait.', back_button_req=0)

        speedtest_info = []
        speedtest_cmd = "speedtest | egrep -w \"Testing from|Download|Upload\" | sed -r 's/Testing from.*?\(/My IP: /g; s/\)\.\.\.//g; s/Download/D/g; s/Upload/U/g; s/bit\/s/bps/g'"

        try:
            speedtest_output = subprocess.check_output(
                speedtest_cmd, shell=True).decode()
            speedtest_info = speedtest_output.split('\n')

        except subprocess.CalledProcessError as exc:
            output = exc.output.decode()
            #error_descr = "Speedtest error"
            error = ["Err: Speedtest error", output]
            display_simple_table(error, back_button_req=1)
            return

        if len(speedtest_info) == 0:
            speedtest_info.append("No output sorry")

        # chop down output to fit up to 2 lines on display
        speedtest_result_text = []

        for n in speedtest_info:
            speedtest_result_text.append(n[0:20])
            if len(n) > 20:
                speedtest_result_text.append(n[20:40])

        speedtest_status = True

    # re-enable front panel keys
    disable_keys = False

    display_simple_table(speedtest_result_text, back_button_req=1,
                         title='--Speedtest--')


def show_publicip():
    '''
    Shows public IP address and related details, works with any interface with internet connectivity
    '''
    global display_state

    publicip_info = []

    try:
        publicip_output = subprocess.check_output(
            publicip_cmd, shell=True).decode()
        publicip_info = publicip_output.split('\n')

    except subprocess.CalledProcessError as exc:
        output = exc.output.decode()
        #error_descr = "Public IP Error"
        error = ["Err: Public IP", output]
        display_simple_table(error, back_button_req=1)
        return

    if len(publicip_info) == 0:
        publicip_info.append("No output sorry")

    # chop down output to fit up to 2 lines on display
    choppedoutput = []

    for n in publicip_info:
        choppedoutput.append(n[0:20])
        if len(n) > 20:
            choppedoutput.append(n[20:40])

    # final check no-one pressed a button before we render page
    if display_state == 'menu':
        return

    display_simple_table(choppedoutput, back_button_req=1,
                         title='--Public IP Address--')
    time.sleep(10)


def show_menu_ver():

    global __version__

    display_simple_table(["Menu version:", __version__],
                         back_button_req=1, font="medium")


def shutdown():

    global oled
    global shutdown_in_progress
    global screen_cleared

    display_dialog_msg('Shutting down...', back_button_req=0)
    time.sleep(1)

    oled.clearDisplay()
    screen_cleared = True

    os.system('systemctl poweroff')
    shutdown_in_progress = True
    return


def reboot():

    global oled
    global shutdown_in_progress
    global screen_cleared
    global reboot_image

    display_dialog_msg('Rebooting...', back_button_req=0)
    time.sleep(1)

    oled.drawImage(reboot_image)

    screen_cleared = True

    os.system('systemctl reboot')
    shutdown_in_progress = True
    return


def switcher(resource_title, resource_switcher_file, mode_name):
    '''
    Function to perform generic set of operations to switch wlanpi mode
    '''

    global oled
    global shutdown_in_progress
    global screen_cleared
    global current_mode
    global display_state
    global reboot_image

    # check resource is available
    if not os.path.isfile(resource_switcher_file):

        display_dialog_msg('{} not available'.format(
            resource_title), back_button_req=1)
        display_state = 'page'
        return

    # Resource switcher was detected, so assume it's installed
    back_button_req = 0

    if current_mode == "classic":
        # if in classic mode, switch to the resource
        dialog_msg = 'Switching to {} mode (rebooting...)'.format(
            resource_title)
        switch = "on"
    elif current_mode == mode_name:
        dialog_msg = 'Switching to Classic mode (rebooting...)'
        switch = "off"
    else:
        dialog_msg('Unknown mode: {}'.format(current_mode), back_button_req=1)
        display_state = 'page'
        return False

    # Flip the mode
    display_dialog_msg(dialog_msg, back_button_req)
    shutdown_in_progress = True
    time.sleep(2)

    oled.drawImage(reboot_image)
    screen_cleared = True

    try:
        dialog_msg = subprocess.check_output("{} {}".format(
            resource_switcher_file, switch), shell=True).decode()  # reboots
    except subprocess.CalledProcessError as exc:
        output = exc.output.decode()
        dialog_msg = mode_name

    # We only get to this point if the switch has failed for some reason
    # (Note that the switcher script reboots the WLANPi)
    shutdown_in_progress = False
    screen_cleared = False
    display_dialog_msg("Switch failed: {}".format(
        dialog_msg), back_button_req=0)
    display_state = 'menu'

    # allow 5 secs to view failure msg
    time.sleep(3)
    # move back up to menu branch
    global current_menu_location
    current_menu_location.pop()

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
    global display_state

    # check resource is available
    if not os.path.isfile(kismet_ctl_file):
        display_dialog_msg('{} not available'.format(
            kismet_ctl_file), back_button_req=1)
        display_state = 'page'
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

    display_dialog_msg(dialog_msg, back_button_req=1)
    display_state = 'page'
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
    global display_state

    # check resource is available
    if not os.path.isfile(bettercap_ctl_file):
        display_dialog_msg('{} not available'.format(
            bettercap_ctl_file), back_button_req=1)
        display_state = 'page'
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

    display_dialog_msg(dialog_msg, back_button_req=1)
    display_state = 'page'
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
    global display_state

    # check resource is available
    if not os.path.isfile(profiler_ctl_file):
        display_dialog_msg('not available: {}'.format(
            profiler_ctl_file), back_button_req=1)
        display_state = 'page'
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

        display_simple_table(item_list, back_button_req=1,
                             title='Profiler Status')
        display_state = 'page'
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

    display_dialog_msg(dialog_msg, back_button_req=1)
    display_state = 'page'
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


def check_wiperf_status():

    status_file = '/tmp/wiperf_status.txt'
    if os.path.exists(status_file):
        try:
            statusf = open(status_file, 'r')
            msg = statusf.readline()
        except:
            # not much we can do, fail silently
            return ''

        # return extracted line
        return " ({})".format(msg)
    else:
        return ''


def home_page():

    global draw
    global oled
    global wlanpi_ver
    global current_mode
    global hostname
    global drawing_in_progress
    global display_state
    global ethtool_file

    drawing_in_progress = True
    display_state = 'page'

    if current_mode == "wconsole":
        # get wlan0 IP
        if_name = "wlan0"
        mode_name = "Wi-Fi Console"

    elif current_mode == "hotspot":
        # get wlan0 IP
        if_name = "wlan0"
        mode_name = "Hotspot " + wifi_client_count() + " clients"

    elif current_mode == "wiperf":
        # get wlan0 IP
        if_name = "wlan0"
        mode_name = "Wiperf" + check_wiperf_status()

    else:
        # get eth0 IP
        if_name = "eth0"
        mode_name = ""

        # get Ethernet port info (...for Jerry)
        try:
            # eth_speed_info  = subprocess.check_output("{} eth0  | grep -i speed | cut -d' ' -f2".format(ethtool_file), shell=True)
            eth_info = subprocess.check_output(
                '{} eth0 2>/dev/null'.format(ethtool_file), shell=True).decode()
            speed_re = re.findall(r'Speed\: (.*\/s)', eth_info, re.MULTILINE)
            duplex_re = re.findall(r'Duplex\: (.*)', eth_info, re.MULTILINE)
            link_re = re.findall(r'Link detected\: (.*)',
                                 eth_info, re.MULTILINE)

            if (speed_re is None) or (duplex_re is None) or (link_re is None):
                # Our pattern matching failed...silently fail....we must set up logging at some stage
                mode_name = ""
            elif (link_re[0] == "no"):
                # Ethernet link is down, report msg instead of speed & duplex
                mode_name = "Link down"
            else:
                # Report the speed & duplex messages from ethtool
                mode_name = "{} {}".format(speed_re[0], duplex_re[0])

        except Exception as ex:
            # Something went wrong...show nothing
            mode_name = ""

        # If eth0 is down, lets show the usb0 IP address
        # in case anyone uses OTG conection & is confused
        if mode_name == "Link down":
            if_name = "usb0"
            mode_name = ""

    ip_addr_cmd = "ip addr show {}  2>/dev/null | grep -Po \'inet \K[\d.]+\' | head -n 1".format(
        if_name)

    try:
        ip_addr = subprocess.check_output(ip_addr_cmd, shell=True).decode()
    except Exception as ex:
        ip_addr = "No IP Addr"

    clear_display()
    draw.text((0, 1), str(wlanpi_ver), font=smartFont, fill=255)
    draw.text((0, 11), str(hostname), font=font11, fill=255)
    draw.text((95, 20), if_name, font=smartFont, fill=255)
    draw.text((0, 29), str(ip_addr), font=font14, fill=255)
    draw.text((0, 43), str(mode_name), font=smartFont, fill=255)
    nav_button_obj.back('Menu')
    oled.drawImage(image)

    drawing_in_progress = False
    return

#######################
# other functions here
#######################


def wifi_client_count():
    wccc = "sudo /sbin/iw dev wlan0 station dump | grep 'Station' | wc -l"

    try:
        client_count = subprocess.check_output(wccc, shell=True).decode()

    except subprocess.CalledProcessError as exc:
        output = exc.output.decode()
        #error_descr = "Issue getting number of  Wi-Fi clients"
        wccerror = ["Err: Wi-Fi client count", str(output)]
        display_simple_table(wccerror, back_button_req=1)
        return

    return client_count.strip()


def menu_down():

    global current_menu_location
    global menu
    global current_scroll_selection
    global display_state

    # If we are in a table, scroll down (unless at bottom of list)
    if display_state == 'page':
        current_scroll_selection += 1
        return

    # Menu not currently shown, do nothing
    if display_state != 'menu':
        return

    # pop the last menu list item, increment & push back on
    current_selection = current_menu_location.pop()
    current_selection = current_selection + 1
    current_menu_location.append(current_selection)

    draw_page()


def menu_right():

    global current_menu_location
    global menu
    global option_number_selected
    global option_selected
    global current_scroll_selection
    global display_state
    global speedtest_status

    # make sure we know speedtest is done
    speedtest_status = False

    # If we are in a table, scroll up (unless at top of list)
    if display_state == 'page':
        if current_scroll_selection == 0:
            return
        else:
            current_scroll_selection -= 1
            return

    # Check if the "action" field at the current location is an
    # array or a function.

    # if we have an array, append the current selection and re-draw menu
    if (type(option_selected) is list):
        current_menu_location.append(0)
        draw_page()
    elif (isinstance(option_selected, types.FunctionType)):
        # if we have a function (dispatcher), execute it
        display_state = 'page'
        option_selected()


def menu_left():

    global current_menu_location
    global menu
    global option_number_selected
    global option_selected
    global current_scroll_selection
    global table_list_length
    global result_cache
    global display_state
    global start_up

    # If we're in a table we need to exit, reset table scroll counters, reset
    # result cache and draw the menu for our current level
    if display_state == 'page':
        current_scroll_selection = 0
        table_list_length = 0
        display_state = 'menu'
        display_state = 'menu'
        draw_page()
        result_cache = False
        return

    if display_state == 'menu':

        # check to make sure we aren't at top of menu structure
        if len(current_menu_location) == 1:
            # If we're at the top and hit exit (back) button, revert to start-up state
            start_up = True
            home_page()
        else:
            current_menu_location.pop()
            draw_page()
    else:
        display_state = 'menu'
        draw_page()


def go_up():

    # executed when the back navigation item is selected

    global current_menu_location
    global display_state

    display_state = 'menu'

    if len(current_menu_location) == 1:
        # we must be at top level, do nothing
        return
    else:
        # Take off last level of menu structure to go up
        # Set index to 0 so top menu item selected
        current_menu_location.pop()
        current_menu_location[-1] = 0

        draw_page()

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
if current_mode == "wconsole":
    switcher_dispatcher = wconsole_switcher
    home_page_name = "Wi-Fi Console"

if current_mode == "hotspot":
    switcher_dispatcher = hotspot_switcher
    home_page_name = "Hotspot"

if current_mode == "wiperf":
    switcher_dispatcher = wiperf_switcher
    home_page_name = "Wiperf"

if current_mode != "classic":
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


def receive_signal(signum, stack):

    global pageSleepCountdown
    global pageSleep
    global current_menu_location
    global shutdown_in_progress
    global screen_cleared
    global sig_fired
    global start_up
    global disable_keys

    if disable_keys:
        # someone disabled the front panel keys as they don't want to be interrupted
        return

    if (sig_fired):
        # signal handler already in progress, ignore this one
        return

    # user pressed a button, reset the sleep counter
    pageSleepCountdown = pageSleep

    start_up = False

    if drawing_in_progress or shutdown_in_progress:
        return

    # if display has been switched off to save screen, power back on and show home menu
    if screen_cleared:
        screen_cleared = False
        pageSleepCountdown = pageSleep
        return

    # Key 1 pressed - Down key
    if signum == signal.SIGUSR1:
        sig_fired = True
        menu_down()
        sig_fired = False
        return

    # Key 2 pressed - Right/Selection key
    if signum == signal.SIGUSR2:
        sig_fired = True
        menu_right()
        sig_fired = False
        return

    # Key 3 pressed - Left/Back key
    if signum == signal.SIGALRM:
        sig_fired = True
        menu_left()
        sig_fired = False
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

        if shutdown_in_progress or screen_cleared or drawing_in_progress:

            # we don't really want to do anything at the moment, lets
            # nap and loop around
            time.sleep(1)
            continue

        # Draw a menu or execute current action (dispatcher)
        if display_state != 'menu':
            # no menu shown, so must be executing action.

            # if we've just booted up, show home page
            if start_up == True:
                option_selected = home_page

             # Re-run current action to refresh screen
            option_selected()
        else:
            # lets try drawing our page (or refresh if already painted)
            draw_page()

        # if screen timeout is zero, clear it if not already done (blank the
        # display to reduce screenburn)
        if pageSleepCountdown == 0 and screen_cleared == False:
            oled.clearDisplay()
            screen_cleared = True

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
