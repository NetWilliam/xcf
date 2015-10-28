#!/bin/bash
kill `pgrep -f "python /home/pi/source/xcf/index.py"`
spawn-fcgi -d /home/pi/source/xcf/ -f /home/pi/source/xcf/index.py -a 127.0.0.1 -p 9527
ret=$?

while [ ! $ret ]
do
    spawn-fcgi -d /home/pi/source/xcf/ -f /home/pi/source/xcf/index.py -a 127.0.0.1 -p 9527
    ret=$?
done   

