#!/bin/bash
#Keeps an eye on the syslog for eth0 up and down events and triggers networkinfo (i.e. LLDP) scripts

DIRECTORY="/home/wlanpi/fpms/BakeBit/Software/Python/scripts/networkinfo"

tail -fn0 /var/log/messages |
while read -r line
do
  case "$line" in
  *"device (eth0): link connected"*)
    logger "networkinfo script: eth0 went up"
    #Execute neighbour detection scripts
    sudo "$DIRECTORY"/lldpneigh.sh &
    sudo "$DIRECTORY"/cdpneigh.sh &
  ;;
  *"eth0: Link is Down"*)
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
