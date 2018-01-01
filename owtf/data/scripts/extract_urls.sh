#!/usr/bin/env bash

if [ $# -ne 3 ]; then
	echo "Syntax: $0 <type> <file> <base_url>"
	exit
fi
 
TYPE=$1
FILE=$2
BASE_URL=$3

if [ ! -f $FILE ]; then
	echo "File not found: $FILE"
	exit
fi

case $TYPE in
  "hoppy")
	#grep -v " " hoppy.summary | tr "\t" "#" | grep "^##/" |sed "s|^##|$BASE_URL|g"
	grep -v " " $FILE | tr "\t" "#" | grep "^##/" |sed "s|^##|$BASE_URL|g" | uniq
	;;
  "dirbuster") 
	#grep '^\/' dirbuster_report.txt | grep -v ':' | sed "s|^/|$BASE_URL/|g"
    #grep '^\/' $FILE | grep -v ':' | sed "s|^/|$BASE_URL/|g"
    grep '^[File found|Dir found]' $FILE | grep ":" | sed "s|^File found: ||g;s|^Dir found: ||g;s| *||g;s|-||g;s|[0-90-90-9]||g;s|^/|$BASE_URL/|g" | uniq

	;;
  "nikto")
	#grep ": /" Nikto.txt | grep -v "^+ SSL Info:"| tr ":" "\n"|grep "^ /" |sed "s|^ /|$BASE_URL/|g"
	grep ": /" $FILE | grep -v "^+ SSL Info:"| tr ":" "\n"|grep "^ /" |sed "s|^ /|$BASE_URL/|g" | uniq
	;;	
  "w3af") 
	#grep "$BASE_URL" W3AF.txt |tr '>' "\n"|tr '>' "\n" |tr '"' "\n"|tr " " "\n" | grep "$BASE_URL"
	#grep "$BASE_URL" $FILE |tr '>' "\n"|tr '>' "\n" |tr '"' "\n"|tr " " "\n" | grep "$BASE_URL"
	grep "$BASE_URL" $FILE |tr '"' "\n"|tr " " "\n" | grep "^$BASE_URL" | uniq
	;;
  "arachni")
	#grep "^\[+\] http" arachni_report*.txt |tr "]" "\n" |grep "$BASE_URL"|sed 's/^ //'|grep "://"
	#grep "^\[-\] http" arachni_report*.txt |tr "]" "\n" |grep "$BASE_URL"|sed 's/^ //'|grep "://"
	#grep "^\[+\] http" $FILE |tr "]" "\n" |grep "$BASE_URL"|sed 's/^ //'|grep "://"
	#grep "^\[-\] http" $FILE |tr "]" "\n" |grep "$BASE_URL"|sed 's/^ //'|grep "://"
	grep "^\[[+-]\] http" $FILE |tr " " "\n" | grep "^$BASE_URL" | uniq
	;;
  *)
	echo "Undefined Type: $TYPE"
esac
