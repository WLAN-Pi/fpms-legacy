#!/bin/bash

#Deffault number of down & up cycles if not specified explicitly otherwise
COUNT=5

#Default interface name if not specified explicitly otherwise
INTERFACE="eth0"

usage(){
  echo "Usage: $0 [[-c NUMBER_OF_CYCLES ] | [-t TIMEOUT_IN_SECONDS] | [-i INTERFACE_NAME] [-h]]"
}

blink_n_times(){
  COUNT=$1
  for (( c=1; c<="$COUNT"; c++ ))
  do
    echo "Down"
    sudo ifconfig "$INTERFACE" down
    sleep 3
    echo "Up"
    sudo ifconfig "$INTERFACE" up
    sleep 7
  done
}

blink_n_seconds(){
  timeout $1 bash <<EOF
  echo "Timeout is $1"
  while true
  do
    echo "Down"
    sudo ifconfig "$INTERFACE" down
    sleep 3
    echo "Up"
    sudo ifconfig "$INTERFACE" up
    sleep 7
  done
EOF
}


#Was any interface name passed as an argument
if [[ "$*" == *'-i '* ]]
then
    INTERFACE=$(echo $@ | grep -o '\-i .*' | cut -d " " -f2)
    echo "Got interface $INTERFACE"

fi


while [ "$1" != "" ]; do
    case $1 in
        -c | --count )          shift
				echo "Got -c and it was $1"
                                blink_n_times $1
                                exit
                                ;;
        -t | --timeout )        shift
                                echo "Got -t and it was $1"
                                blink_n_seconds $1
                                exit
                                ;;
        -h | --help )           usage
                                exit
                                ;;
        * )                     if [ "$#" -ge 1 ]; then usage; exit; fi
    esac
    shift
done
blink_n_times "$COUNT"

exit 0
