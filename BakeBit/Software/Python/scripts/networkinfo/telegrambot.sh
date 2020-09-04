#!/bin/bash

#Sends current IP address to you using a Telegram bot, requires internet connectivity

ETH0SPEED=$(ethtool eth0 2>/dev/null | grep -q "Link detected: yes" && ethtool eth0 2>/dev/null | grep "Speed" | sed 's/....$//' | cut -d ' ' -f2  || echo "Disconnected")
ETH0DUPLEX=$(ethtool eth0 2>/dev/null | grep -q "Link detected: yes" && ethtool eth0 2>/dev/null | grep "Duplex" | cut -d ' ' -f 2 || echo "Disconnected")
HOSTNAME=$(hostname)
UPTIME=$(uptime -p | cut -c4-)
MODE=$(cat /etc/wlanpi-state)

APIKEY="1309738878:AAEohYK84-mr7cvxFgIWtCuOWB556J1tb2s"
CHATID="981901222"

#Get public IP data in JSON format 
DATAINJSON=$(timeout 3 curl -s 'ifconfig.co/json')

#Parse
PUBLICIP=$(echo "$DATAINJSON" | grep -Po '"ip":"\K[^"]*')
PUBLICIPCOUNTRY=$(echo "$DATAINJSON" | grep -Po '"country":"\K[^"]*')
PUBLICIPASNORG=$(echo "$DATAINJSON" | grep -Po '"asn_org":"\K[^"]*')
PUBLICIPHOSTNAME=$(echo "$DATAINJSON" | grep -Po '"hostname":"\K[^"]*')
PUBLICIPASN=$(echo "$DATAINJSON" | grep -Po '"asn":"\K[^"]*')

echo "before while"

while true; do 
  ETH0IP=$(ip a | grep "eth0" | grep "inet" | grep -v "secondary" | head -n1 | cut -d '/' -f1 | cut -d ' ' -f6)
  sleep 0.5
  echo "in while after sleep"
  if [ ! -z "$ETH0IP" ]; then
    sleep 1
    logger "Telegram bot: sending IP details"
    echo "inside if"
    TEXT=''
    TEXT+="<u>Your $HOSTNAME is now online</u> %0A"
    TEXT+="Eth0 IP Address: <code>$ETH0IP</code> %0A"
    TEXT+="Speed: $ETH0SPEED %0A"
    TEXT+="Duplex: $ETH0DUPLEX %0A"
    TEXT+="Mode: $MODE %0A"
    TEXT+="Uptime: $UPTIME %0A"
    TEXT+="Web Interface: http://$ETH0IP %0A"
    #TEXT+="Web Console: https://$ETH0IP:9090 %0A"
    TEXT+="SSH Connection: <code>ssh://wlanpi@$ETH0IP</code> %0A"
    #TEXT+="Copy File to TFTP Server: copy flash:filename tftp://$ETH0IP %0A"
    TEXT+="Public IP Address: <code>$PUBLICIP</code>, <code>$PUBLICIPHOSTNAME</code> %0A"
TEXT="123"

    #Try using this instead for complex text
    #curl --data chat_id=12345678 --data-urlencode "text=Some complex text $25 78%"  "https://api.telegram.org/bot0000000:KEYKEYKEYKEYKEYKEY/sendMessage"
    echo "before sending"
    timeout 5 curl -s -X POST "https://api.telegram.org/bot$APIKEY/sendMessage?chat_id=$CHATID&parse_mode=html&text=$TEXT"
    if [ "$?" != 0  ]; then
      MESSAGE_SENT="no"
      echo "Message failed! Resending now."
      timeout 5 curl -s -X POST "https://api.telegram.org/bot$APIKEY/sendMessage?chat_id=$CHATID&parse_mode=html&text=$TEXT"
      if [ "$?" != 0  ]; then
        MESSAGE_SENT="no"
        echo "Message failed again! Giving up!"
      else "Message successfully sent second time"
      fi
    else
      echo "Message successfully sent"
    fi
    break
  fi
  sleep 1
done

echo "done"
