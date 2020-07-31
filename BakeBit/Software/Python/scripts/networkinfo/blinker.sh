#!/bin/bash

#Default number of down & up cycles if not specified explicitly otherwise
COUNT=5
#Default interface name if not specified explicitly otherwise
INTERFACE="eth0"

usage(){
  echo "Usage: $0 [[-c NUMBER_OF_CYCLES ] | [-t TIMEOUT_IN_SECONDS] | [-i INTERFACE_NAME] [-h]]"
}

blink_n_times(){
  echo "Interface: $INTERFACE"
  COUNT=$1
  for (( c=1; c<="$COUNT"; c++ ))
  do
    echo -e "\e[91mDown"
    sudo ifconfig "$INTERFACE" down
    sleep 3
    echo -e "\e[92mUp"
    sudo ifconfig "$INTERFACE" up
    sleep 7
  done
}

blink_n_seconds(){
  echo "Interface: $INTERFACE"
  timeout $1 bash <<EOF
  echo "Timeout is $1"
  while true
  do
    echo -e "\e[91mDown"
    sudo ifconfig "$INTERFACE" down
    sleep 3
    echo -e "\e[92mUp"
    sudo ifconfig "$INTERFACE" up
    sleep 7
  done
EOF
}

#Was at least 1 complete argument (2 strings separate by space) provided
if [ "$#" -eq 1 ]; then
  usage
  exit
fi

#Was any interface name passed as an argument
if [[ "$*" == *'-i '* ]]; then
    INTERFACE=$(echo $@ | grep -o '\-i .*' | cut -d " " -f2)
fi

while [ "$1" != "" ]; do
    case $1 in
        -c | --count )          shift
                                blink_n_times $1
                                exit
                                ;;
        -t | --timeout )        shift
                                blink_n_seconds $1
                                exit
                                ;;
        -h | --help )           usage
                                exit
                                ;;
        * )
    esac
    shift
done
blink_n_times "$COUNT"

exit 0
