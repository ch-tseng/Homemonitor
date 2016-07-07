#!/bin/bash
export CLOUDINARY_URL=cloudinary://XXXX:XXXXXXXXXX@XXX

cd /home/pi/monitor
python start.py

ps -ef | grep -v grep | grep start.py

#if [ $? -eq 1 ]
#then
#    sleep 60
#    sudo reboot
#fi
