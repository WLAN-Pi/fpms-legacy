#!/bin/bash
#Keeps an eye on the syslog for eth0 up and down events and triggers networkinfo (i.e. LLDP) scripts

DIRECTORY="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

#Start neighbour detection immediately after the WLAN Pi boots up
sudo "$DIRECTORY"/lldpneigh.sh &
sudo "$DIRECTORY"/cdpneigh.sh  &
#timeout 10 "$DIRECTORY"/telegrambot.sh &
"$DIRECTORY"/watchinternet.sh &

#Monitor up/down status changes of eth0 and execute neighbour detection or cleanup
tail -fn0 /var/log/messages |
while read -r line
do
  case "$line" in
  *".ethernet eth0: Link is Up"*)
    logger "networkinfo script: eth0 went up"
    #Execute neighbour detection scripts
    sudo "$DIRECTORY"/lldpneigh.sh &
    sudo "$DIRECTORY"/cdpneigh.sh  &
    #timeout 10 "$DIRECTORY"/telegrambot.sh &
  ;;
  *".ethernet eth0: Link is Down"*)
    logger "networkinfo script: eth0 went down"
    #Execute cleanup scripts
    sudo "$DIRECTORY"/lldpcleanup.sh
    sudo "$DIRECTORY"/cdpcleanup.sh
    #Kill any running instances of the CDP and LLDP scripts
    pgrep cdpneigh.sh | xargs sudo pkill -P 2>/dev/null
    pgrep lldpneigh.sh | xargs sudo pkill -P 2>/dev/null
  ;;
  *)
  esac
done
