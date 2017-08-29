#!/usr/bin/env bash

if [ $# -ne 1 ]; then
	echo "Syntax $0 <test directory>"
	exit
fi

DIR=$1
for file in $(ls $DIR); do
	echo "TESTING: $file"
	cat $DIR/$file | ./sanitiser.py 
	echo "press Enter to continue"
	read key
done
