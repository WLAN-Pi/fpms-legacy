#!/bin/bash
# Detects CDP neighbour on eth0 interface

#Check if the script is running as root
if [[ $EUID -ne 0 ]]; then
   echo "This script must be run as root"
   exit 1
fi

#Prevent multiple instances of the script to run at the same time
for pid in $(pidof -x $0); do
    if [ $pid != $$ ]; then
        echo "Another instance of the script is already running. Wait for it to finish first."
        exit 1
    fi
done

DIRECTORY="/home/wlanpi/fpms/BakeBit/Software/Python/scripts/networkinfo"
CAPTUREFILE="/tmp/cdpneightcpdump.cap"
OUTPUTFILE="/tmp/cdpneigh.txt"

#Clean up the output files
sudo "$DIRECTORY"/cdpcleanup.sh

logger "networkinfo script: looking for a CDP neighbour"

#Run packet capture for up to 61 seconds or stop after we have got the right packets
TIMETOSTOP=0
while [ "$TIMETOSTOP" == 0 ]; do
    timeout 61 sudo tcpdump -v -s 1500 -c 1 'ether[20:2] == 0x2000' -Q in > "$CAPTUREFILE"
    TIMETOSTOP=$(cat "$CAPTUREFILE" | grep "CDP")
done

#If we didn't capture any LLDP packets then return
if [ -z "$TIMETOSTOP" ]; then
    logger "networkinfo script: no CDP neighbour detected"
    exit 0
else 
    logger "networkinfo script: found a new CDP neighbour"
fi

#Be careful this first statement uses tee without -a and overwrites the content of the text file
DEVICEID=$(cat "$CAPTUREFILE" | grep "Device-ID" | cut -d "'" -f2)
echo -e "Name: $DEVICEID" 2>&1 | tee "$OUTPUTFILE"

PORT=$(cat "$CAPTUREFILE" | grep "Port-ID" | cut -d "'" -f2)
if [ "$PORT" ]; then
    echo -e "Port: $PORT" 2>&1 | tee -a "$OUTPUTFILE"
fi

#UBNT devices send <reverse-ip-address>.in-addr.arpa in their CDP messages
ISREVERSEADDRESS=$(grep "in-addr.arpa" "$CAPTUREFILE")
ADDRESS=$(sudo cat "$CAPTUREFILE" | grep "Address " | grep -E -o "([0-9]{1,3}[\.]){3}[0-9]{1,3}")
if [ "$ISREVERSEADDRESS" ]; then
    ADDRESS=$(echo "$ADDRESS" | awk -F. '{OFS=FS;print $4,$3,$2,$1}')
fi
if [ "$ADDRESS" ]; then
    echo -e "IP: $ADDRESS" 2>&1 | tee -a "$OUTPUTFILE"
fi

NATIVEVLAN=$(cat "$CAPTUREFILE" | grep "Native VLAN ID" | cut -d ':' -f3)
if [ "$NATIVEVLAN" ]; then
    echo -e "Native VLAN:$NATIVEVLAN" 2>&1 | tee -a "$OUTPUTFILE"
fi

PLATFORM=$(cat "$CAPTUREFILE" | grep "Platform" | cut -d "'" -f2)
echo -e "Model: $PLATFORM" 2>&1 | tee -a "$OUTPUTFILE"

exit 0
