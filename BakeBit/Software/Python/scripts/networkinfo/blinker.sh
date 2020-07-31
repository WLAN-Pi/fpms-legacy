#!/bin/bash

#Default number of down & up cycles if not specified explicitly otherwise
COUNT=5
#Default interface name if not specified explicitly otherwise
INTERFACE="eth0"
#Use colors in output by default
COLOR=1

usage(){
  echo "Usage: $0 [[-c NUMBER_OF_CYCLES ] | [-t TIMEOUT_IN_SECONDS] | [-i INTERFACE_NAME] [-h] | -no-color]"
}

blink_n_times(){
  echo "Interface: $INTERFACE"
  COUNT=$1
  for (( c=1; c<="$COUNT"; c++ ))
  do
    if  [ COLOR == 1 ]; then
      echo -e "\e[91mDown"
    else
      echo "Down"
    fi
    sudo ifconfig "$INTERFACE" down
    sleep 3
    if  [ COLOR == 1 ]; then
      echo -e "\e[92mUp"
    else
      echo "Up"
    fi
    sudo ifconfig "$INTERFACE" up
    sleep 7
  done
}

blink_n_seconds(){
  echo "Interface: $INTERFACE"
  timeout $1 bash <<EOF
  while true
  do
    if  [ COLOR == 1 ]; then
      echo -e "\e[91mDown"
    else
      echo "Down"
    fi
    sudo ifconfig "$INTERFACE" down
    sleep 3
    if  [ COLOR == 1 ]; then
      echo -e "\e[92mUp"
    else
      echo "Up"
    fi
    sudo ifconfig "$INTERFACE" up
    sleep 7
  done
EOF
}

#If an incomplete argument (complete argument is 2 strings separated by space) was provided display usage, with the exception of --no-color
if [ "$#" -eq 1 ] && [[ "$*" != *'--no-color'* ]]; then
  usage
  exit
fi

#Was any interface name passed as an argument
if [[ "$*" == *'-i '* ]]; then
    INTERFACE=$(echo $@ | grep -o '\-i .*' | cut -d " " -f2)
fi

#Was --no-color argument used
if [[ "$*" == *'--no-color'* ]]; then
    COLOR=0
fi

#Parse arguments
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

#Default behaviour when script is executed without arguments
blink_n_times "$COUNT"

exit 0
