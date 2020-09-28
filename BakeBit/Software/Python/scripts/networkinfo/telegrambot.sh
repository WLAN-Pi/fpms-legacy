#!/bin/bash

#Author: Jiri Brejcha, jirka@jiribrejcha.net
#Sends current IP address and other useful details to you as a Telegram message, requires internet connectivity on eth0 interface

#--------------------------------------------
# READ THIS FIRST
#
# Enter your Telegram API key by executing the below command from from shell. Remove "#" and replace all "x" characters with your API key before executing.
#
# echo 'export TELEGRAM_API_KEY="xxxxxxxxxx:xxxxxxxxx-xxxxxxxxxxxxxxxxxxxxxxxxx"' >> ~/.bashrc && source ~/.bashrc
#
#--------------------------------------------

#Connectivity check
if !  curl -s -X GET https://api.telegram.org > /dev/null ; then
  echo "Error: Cannot connect to the Telegram API. Check your internet connection."
  logger "networkinfo Telegram bot: Error - Check your internet connection!"
  exit 1
fi

#Got the API key?
if [ -z $TELEGRAM_API_KEY ]; then
  echo "Error: No Telegram API key found. Use the below command to enter the key."
  echo 'echo export TELEGRAM_API_KEY="xxxxxxxxxx:xxxxxxxxx-xxxxxxxxxxxxxxxxxxxxxxxxx" >> ~/.bashrc && source ~/.bashrc'
  logger "networkinfo Telegram bot: Error - No API key found!"
  exit 2 
fi

#Get Chat ID - for this to work you have to send a Telegram message to the bot first from your laptop or phone
TELEGRAM_CHAT_ID=$(curl -s -X GET https://api.telegram.org/bot$TELEGRAM_API_KEY/getUpdates | jq -r ".result[0].message.chat.id")

if [ -z $TELEGRAM_CHAT_ID ]; then
  echo "Error: Telegram Chat ID not found. Send a Telegram message with any text to the bot. This is mandatory!"
  logger "networkinfo Telegram bot: Error - No Chat ID found!"
  exit 3 
fi

#Collect all data
ETH0SPEED=$(ethtool eth0 2>/dev/null | grep -q "Link detected: yes" && ethtool eth0 2>/dev/null | grep "Speed" | sed 's/....$//' | cut -d ' ' -f2  || echo "Disconnected")
ETH0DUPLEX=$(ethtool eth0 2>/dev/null | grep -q "Link detected: yes" && ethtool eth0 2>/dev/null | grep "Duplex" | cut -d ' ' -f 2 || echo "Disconnected")
HOSTNAME=$(hostname)
UPTIME=$(uptime -p | cut -c4-)
MODE=$(cat /etc/wlanpi-state)

#Get public IP data in JSON format
DATAINJSON=$(timeout 3 curl -s 'ifconfig.co/json')

#Parse
PUBLICIP=$(echo "$DATAINJSON" | grep -Po '"ip":"\K[^"]*')
PUBLICIPCOUNTRY=$(echo "$DATAINJSON" | grep -Po '"country":"\K[^"]*')
PUBLICIPASNORG=$(echo "$DATAINJSON" | grep -Po '"asn_org":"\K[^"]*')
PUBLICIPHOSTNAME=$(echo "$DATAINJSON" | grep -Po '"hostname":"\K[^"]*')
PUBLICIPASN=$(echo "$DATAINJSON" | grep -Po '"asn":"\K[^"]*')

while true; do
  ETH0IP=$(ip a | grep "eth0" | grep "inet" | grep -v "secondary" | head -n1 | cut -d '/' -f1 | cut -d ' ' -f6)
  sleep 0.5

  if [ ! -z "$ETH0IP" ]; then
    sleep 1
    TEXT=''
    TEXT+="%f0%9f%9f%a2 <b>$HOSTNAME is now online</b> %0A"
    TEXT+="Eth0 IP address: <code>$ETH0IP</code> %0A"
    TEXT+="Speed: $ETH0SPEED %0A"
    TEXT+="Duplex: $ETH0DUPLEX %0A"
    TEXT+="Mode: $MODE %0A"
    TEXT+="Uptime: $UPTIME %0A"
    TEXT+="Web interface: http://$ETH0IP %0A"
    #TEXT+="Web console: https://$ETH0IP:9090 %0A"
    TEXT+="SSH to the Pi: <code>ssh://wlanpi@$ETH0IP</code> %0A"
    #TEXT+="Copy file to TFTP server: copy flash:filename tftp://$ETH0IP %0A"
    TEXT+="Public IP: <code>$PUBLICIP</code>, <code>$PUBLICIPHOSTNAME</code> %0A"

    #Try using this instead for complex text
    #curl --data chat_id=12345678 --data-urlencode "text=Some complex text $25 78%"  "https://api.telegram.org/bot0000000:KEYKEYKEYKEYKEYKEY/sendMessage"

    #First attempt to send message
    timeout 5 curl -s -X POST "https://api.telegram.org/bot$TELEGRAM_API_KEY/sendMessage?chat_id=$TELEGRAM_CHAT_ID&parse_mode=html&text=$TEXT" # > /dev/null
    if [ "$?" != 0  ]; then
      MESSAGE_SENT="no"
      echo "Message failed! Resending now."
      #Second attempt to send message
      timeout 5 curl -s -X POST "https://api.telegram.org/bot$TELEGRAM_API_KEY/sendMessage?chat_id=$TELEGRAM_CHAT_ID&parse_mode=html&text=$TEXT" > /dev/null

      if [ "$?" != 0  ]; then
        MESSAGE_SENT="no"
        echo "Message failed again! Giving up."
        exit 4
      else "Message sent second time"
      fi
    else
      echo ""
      echo "Message successfully sent"
      logger "networkinfo Telegram bot: Message successfully sent"
    fi
    break
  fi
  sleep 1
done

