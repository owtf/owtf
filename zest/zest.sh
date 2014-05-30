#/usr/bin/env bash

<<comm
echo "op -  $1"
echo "root- $2"
echo "script -   $3"
echo "trns - $4"
comm


java -jar $1/zest/zest.jar "$1" "$2" "$3" "$4"

