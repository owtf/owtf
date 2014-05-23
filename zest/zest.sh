#/usr/bin/env bash

<<COMM
echo "request header -  $2"
echo "response header - $3"
echo "response body -   $4"
COMM



java -jar $5/zest/zest.jar "$1" "$2" "$3" "$4" "$5" 

