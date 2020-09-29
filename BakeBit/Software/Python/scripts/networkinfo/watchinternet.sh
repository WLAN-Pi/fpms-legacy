#!/bin/bash

#Author: Jiri Brejcha, jirka@jiribrejcha.net
#Monitors internet connection

CURRENTLY="offline"
PREVIOUSLY="offline"
DIRECTORY="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

logger "networkinfo watchinternet: Started"

function gone_online {
echo -e "\e[92mChanged to online\033[0m"
logger "networkinfo watchinternet: WLAN Pi is now online"
}

function gone_offline {
echo -e "\e[91mChanged to offline\033[0m"
logger "networkinfo watchinternet: WLAN Pi is now offline"
}

echo "-----------------------"

while true; do

  #Current default route interface
  DEFAULT_ROUTE_VIA=$(ip route show | grep "default" | cut -d " " -f5)
  if [ -z "$DEFAULT_ROUTE_VIA" ]; then
    echo -e "\e[91mNo default route\033[0m"
  else
    echo "Default route via: $DEFAULT_ROUTE_VIA"
  fi

  if timeout 3 nc -zw1 canireachthe.net 443 2>/dev/null 1>/dev/null; then
    CURRENTLY="online"
    echo "Currently: $CURRENTLY"
    echo "Previously: $PREVIOUSLY"
  else
    CURRENTLY="offline"
    echo "Currently: $CURRENTLY"
    echo "Previously: $PREVIOUSLY"
  fi

  #WLAN Pi is now online
  if [[ "$CURRENTLY" == "online" ]] && [[ "$PREVIOUSLY" == "offline" ]]; then
    gone_online
    timeout 10 "$DIRECTORY"/telegrambot.sh >/dev/null 2>&1 &
  fi

  #WLAN Pi is now offline
  if [[ "$CURRENTLY" == "offline" ]] && [[ "$PREVIOUSLY" == "online" ]]; then
    gone_offline
  fi

  PREVIOUSLY="$CURRENTLY"
  echo "-----------------------"
  sleep 3
done

