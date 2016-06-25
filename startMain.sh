#!/bin/bash
export CLOUDINARY_URL=cloudinary://735329816927517:_7J6qrTVtRNixIkhixkAicdnLk4@appflyer

cd /home/pi/monitor
python start.py

ps -ef | grep -v grep | grep start.py

if [ $? -eq 1 ]
then
    sleep 60
    sudo reboot
fi
