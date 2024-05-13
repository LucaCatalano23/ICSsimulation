#!/bin/bash
source ../env/bin/activate

echo $DISPLAY

python3 PLC-RoboticArm.py & python3 HMI-RoboticArm.py
