#!/bin/bash

#Author: Jiri Brejcha, jirka@jiribrejcha.net
#Monitors internet connection

CURRENTLY="offline"
PREVIOUSLY="offline"
DIRECTORY="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

logger "networkinfo watchinternet: Started"

function gone_online {
echo -e "\e[92mWLAN Pi is now online\033[0m"
logger "networkinfo watchinternet: WLAN Pi is now online"
timeout 10 "$DIRECTORY"/telegrambot.sh >/dev/null 2>&1 &
}

function gone_offline {
echo -e "\e[91mWLAN Pi is now offline\033[0m"
logger "networkinfo watchinternet: WLAN Pi is now offline"
}

while true; do

  #Current default route interface
  DEFAULT_ROUTE_CURRENTLY=$(ip route show | grep "default" | cut -d " " -f5)
  #if [ -z "$DEFAULT_ROUTE_CURRENTLY" ]; then
  #  echo -e "\e[91mNo default route\033[0m"
  #fi

  if [[ "$DEFAULT_ROUTE_CURRENTLY" != "$DEFAULT_ROUTE_PREVIOUSLY" ]] && [[ "$DEFAULT_ROUTE_CURRENTLY" ]]; then
    echo "Default route via: $DEFAULT_ROUTE_CURRENTLY"
  fi

  if timeout 3 nc -zw1 canireachthe.net 443 2>/dev/null 1>/dev/null; then
    CURRENTLY="online"
  else
    CURRENTLY="offline"
  fi

  #WLAN Pi is now online
  if [[ "$CURRENTLY" == "online" ]] && [[ "$PREVIOUSLY" == "offline" ]]; then
    gone_online
  fi

  #WLAN Pi is now offline
  if [[ "$CURRENTLY" == "offline" ]] && [[ "$PREVIOUSLY" == "online" ]]; then
    gone_offline
  fi

  PREVIOUSLY="$CURRENTLY"
  sleep 3

  DEFAULT_ROUTE_PREVIOUSLY="$DEFAULT_ROUTE_CURRENTLY"

done

