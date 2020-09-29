#!/bin/bash

#Author: Jiri Brejcha, jirka@jiribrejcha.net
#Sends current IP address and other useful details to you as a Telegram message, requires internet connectivity on eth0 interface

#--------------------------------------------
# READ THIS FIRST
#
# Enter your Telegram API key by executing the below command from from shell. Remove "#" and replace xxx with your API key before executing.
#
# sudo bash -c 'echo TELEGRAM_API_KEY="xxx" >> /etc/environment'
#
#--------------------------------------------

#Load environmental variables
source /etc/environment

#Got the API key?
if [ -z "$TELEGRAM_API_KEY" ]; then
  echo "Error: No Telegram API key found"
  echo "Replace xxx with your Telegram API key and execute this command once:"
  echo ""
  echo "sudo bash -c 'echo TELEGRAM_API_KEY=\"xxx\" >> /etc/environment'"
  echo ""
  logger "networkinfo telegrambot: Error - No API key found!"
  exit 1 
fi

#Get Chat ID - for this to work you have to send a Telegram message to the bot first from your laptop or phone
if [ -z "$TELEGRAM_CHAT_ID" ] || [ "$TELEGRAM_CHAT_ID" == "null" ]; then
  TELEGRAM_CHAT_ID=$(curl -s -X GET https://api.telegram.org/bot"$TELEGRAM_API_KEY"/getUpdates | jq -r ".result[0].message.chat.id")
  if [ -z "$TELEGRAM_CHAT_ID" ] || [ "$TELEGRAM_CHAT_ID" == "null" ]; then
    echo "Error: Telegram Chat ID not found. Send a Telegram message with any text to the bot. This is mandatory!"
    logger "networkinfo telegrambot: Error - No Chat ID found!"
    exit 2
  else
      sudo bash -c "echo TELEGRAM_CHAT_ID=\"$TELEGRAM_CHAT_ID\" >> /etc/environment"
  fi
fi

logger "networkinfo telegrambot: Collecting data"

#Collect all data
ETH0SPEED=$(ethtool eth0 2>/dev/null | grep -q "Link detected: yes" && ethtool eth0 2>/dev/null | grep "Speed" | sed 's/....$//' | cut -d ' ' -f2  || echo "disconnected")
ETH0DUPLEX=$(ethtool eth0 2>/dev/null | grep -q "Link detected: yes" && ethtool eth0 2>/dev/null | grep "Duplex" | cut -d ' ' -f 2 || echo "disconnected")
HOSTNAME=$(hostname)
UPTIME=$(uptime -p | cut -c4-)
MODE=$(cat /etc/wlanpi-state)

#Get public IP data
DATAINJSON=$(timeout 3 curl -s 'ifconfig.co/json')
PUBLICIP=$(echo "$DATAINJSON" | grep -Po '"ip":"\K[^"]*')
PUBLICIPCOUNTRY=$(echo "$DATAINJSON" | grep -Po '"country":"\K[^"]*')
PUBLICIPASNORG=$(echo "$DATAINJSON" | grep -Po '"asn_org":"\K[^"]*')
PUBLICIPHOSTNAME=$(echo "$DATAINJSON" | grep -Po '"hostname":"\K[^"]*')
PUBLICIPASN=$(echo "$DATAINJSON" | grep -Po '"asn":"\K[^"]*')
ETH0IP=$(ip a | grep "eth0" | grep "inet" | grep -v "secondary" | head -n1 | cut -d '/' -f1 | cut -d ' ' -f6)
UPLINK=$(ip route show | grep "default" | cut -d " " -f5)
UPLINKIP=$(ip a | grep "$UPLINK" | grep "inet" | grep -v "secondary" | head -n1 | cut -d '/' -f1 | cut -d ' ' -f6)

if [ -z "$ETH0IP" ]; then
  CURRENTIP="$UPLINKIP"
else
  CURRENTIP="$ETH0IP"
fi

#Compose the message
TEXT=''
TEXT+="%f0%9f%9f%a2 <b>$HOSTNAME is now online</b> %0A"
if [ "$ETH0IP" ]; then
  TEXT+="Eth0 IP address: <code>$ETH0IP</code> %0A"
fi
if [[ "$ETH0SPEED" == "disconnected" ]]; then
  TEXT+="Eth0 is down %0A"
else
  TEXT+="Eth0 speed: $ETH0SPEED %0A"
  TEXT+="Eth0 duplex: $ETH0DUPLEX %0A"
fi
TEXT+="WLAN Pi mode: $MODE %0A"
TEXT+="Uptime: $UPTIME %0A"

TEXT+="%0A"
TEXT+="Uplink to internet: $UPLINK %0A"
if [[ "$UPLINK" != "eth0" ]]; then
  TEXT+="Local $UPLINK IP address: $UPLINKIP %0A"
fi
TEXT+="Public IP: <code>$PUBLICIP</code>, <code>$PUBLICIPHOSTNAME</code> %0A"

if [ ! -z "$CURRENTIP" ]; then
  TEXT+="%0A"
  TEXT+="Web interface: http://$CURRENTIP %0A"
  #TEXT+="Web console: https://$CURRENTIP:9090 %0A"
  TEXT+="SSH: <code>ssh://wlanpi@$CURRENTIP</code> %0A"
  #TEXT+="Copy file to TFTP server: copy flash:filename tftp://$CURRENTIP %0A"
fi

#Try using this instead for complex text
#curl --data chat_id=12345678 --data-urlencode "text=Some complex text $25 78%"  "https://api.telegram.org/bot0000000:KEYKEYKEYKEYKEYKEY/sendMessage"

#First attempt to send message
timeout 5 curl -s -X POST "https://api.telegram.org/bot$TELEGRAM_API_KEY/sendMessage?chat_id=$TELEGRAM_CHAT_ID&parse_mode=html&text=$TEXT" > /dev/null
if [ "$?" != 0 ]; then
  sleep 3
  echo "Error: First attempt to send message failed! Resending now..."
  #Second attempt to send message
  timeout 5 curl -s -X POST "https://api.telegram.org/bot$TELEGRAM_API_KEY/sendMessage?chat_id=$TELEGRAM_CHAT_ID&parse_mode=html&text=$TEXT" > /dev/null

  if [ "$?" != 0 ]; then
    echo "Error: Second attempt to send meesage failed! Giving up."
    exit 3
  else
    echo "Message successfully sent at second attempt"
  fi
else
  echo "Message successfully sent"
  logger "networkinfo telegrambot: Message successfully sent"
fi

