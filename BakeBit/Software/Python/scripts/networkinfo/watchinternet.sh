#!/bin/bash

#Author: Jiri Brejcha, jirka@jiribrejcha.net
#Monitors internet connection

CURRENTLY="offline"
PREVIOUSLY="offline"
DIRECTORY="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"


logger "networkinfo internet watchdog: Started"


function changed_to_online {
echo -e "\e[92mChanged to online"
logger "networkinfo internet watchdog: WLAN Pi is now online"
}

function changed_to_offline {
echo -e "\e[91mChanged to offline"
logger "networkinfo internet watchdog: WLAN Pi is now offline"
}


while true; do
  if timeout 3 nc -zw1 canireachthe.net 443 2>/dev/null 1>/dev/null; then
    CURRENTLY="online"
    echo -e "\e[0mCurrently: $CURRENTLY"
    echo -e "\e[0mPreviously: $PREVIOUSLY"
  else
    CURRENTLY="offline"
    echo -e "\e[0mCurrently: $CURRENTLY"
    echo -e "\e[0mPreviously: $PREVIOUSLY"
  fi

  #Went from offline to online
  if [[ "$CURRENTLY" == "online" ]] && [[ "$PREVIOUSLY" == "offline" ]]; then
    changed_to_online
    timeout 10 "$DIRECTORY"/telegrambot.sh &
  fi

  #Went from online to offline
  if [[ "$CURRENTLY" == "offline" ]] && [[ "$PREVIOUSLY" == "online" ]]; then
    changed_to_offline
  fi

  PREVIOUSLY="$CURRENTLY"
  sleep 3
done

