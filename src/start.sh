#!/bin/bash

#cd src

name="$1"
num="$2"
hmi_plc="$3"

if [ -z "$1" ]
then
      echo "start command need module_name to initiate!"
      exit 1
fi
if [ -z "$2" ]
then
      echo "start command need plc_num to initiate!"
      exit 1
fi

if [ $1 = "PLC.py" ]
then 
      sleep 7
	python3 $1 $2 & python3 $3 $2
elif [ $1 = "HMI.py" ]
then
      sleep 10
      python3 $1 $2
elif [ $1 = "usersHandler.py" ]
then
      sleep 10
      python3 $1
else
	echo "the is no command with name: $1"
fi
