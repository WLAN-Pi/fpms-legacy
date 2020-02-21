#!/bin/bash
# Shows public IP address and related details 

#Get all data in JSON format 
DATAINJSON=$(timeout 2 curl -s 'ifconfig.co/json')

if [ ! "$DATAINJSON" ]; then
    echo "No public IP address detected"
    #Conciously exiting with 0 to prevent error message in Python code that calls this script 
    exit 0
fi

#Parse them
PUBLICIP=$(echo "$DATAINJSON" | grep -Po '"ip":"\K[^"]*')
PUBLICIPCOUNTRY=$(echo "$DATAINJSON" | grep -Po '"country":"\K[^"]*')
PUBLICIPASNORG=$(echo "$DATAINJSON" | grep -Po '"asn_org":"\K[^"]*')
PUBLICIPHOSTNAME=$(echo "$DATAINJSON" | grep -Po '"hostname":"\K[^"]*')
PUBLICIPASN=$(echo "$DATAINJSON" | grep -Po '"asn":"\K[^"]*')

#Display data
if [ "$PUBLICIP" ]; then
    echo "$PUBLICIP"
    echo "$PUBLICIPCOUNTRY"
    echo "$PUBLICIPASNORG"
    echo "$PUBLICIPHOSTNAME"
    echo "$PUBLICIPASN"
else
    echo "No public IP address detected"
fi

exit 0

