#!/usr/bin/env bash
#
# owtf is an OWASP+PTES-focused try to unite great tools and facilitate pen testing
# Copyright (c) 2011, Abraham Aranguren <name.surname@gmail.com> Twitter: @7a_ http://7-a.org
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# * Redistributions of source code must retain the above copyright 
# notice, this list of conditions and the following disclaimer.
# * Redistributions in binary form must reproduce the above copyright
# notice, this list of conditions and the following disclaimer in the
# documentation and/or other materials provided with the distribution.
# * Neither the name of the copyright owner nor the
# names of its contributors may be used to endorse or promote products
# derived from this software without specific prior written permission.
# 
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
# ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#

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
	grep -v " " $FILE | tr "\t" "#" | grep "^##/" |sed "s|^##|$BASE_URL|g"
	;;
  "dirbuster") 
	#grep '^\/' dirbuster_report.txt | grep -v ':' | sed "s|^/|$BASE_URL/|g"
    #grep '^\/' $FILE | grep -v ':' | sed "s|^/|$BASE_URL/|g"
    grep '^[File found|Dir found]' $FILE | grep ":" | sed "s|^File found: ||g;s|^Dir found: ||g;s| *||g;s|-||g;s|[0-90-90-9]||g;s|^/|$BASE_URL/|g"

	;;
  "nikto")
	#grep ": /" Nikto.txt | grep -v "^+ SSL Info:"| tr ":" "\n"|grep "^ /" |sed "s|^ /|$BASE_URL/|g"
	grep ": /" $FILE | grep -v "^+ SSL Info:"| tr ":" "\n"|grep "^ /" |sed "s|^ /|$BASE_URL/|g"
	;;	
  "w3af") 
	#grep "$BASE_URL" W3AF.txt |tr '>' "\n"|tr '>' "\n" |tr '"' "\n"|tr " " "\n" | grep "$BASE_URL"
	#grep "$BASE_URL" $FILE |tr '>' "\n"|tr '>' "\n" |tr '"' "\n"|tr " " "\n" | grep "$BASE_URL"
	grep "$BASE_URL" $FILE |tr '"' "\n"|tr " " "\n" | grep "^$BASE_URL"
	;;
  "arachni")
	#grep "^\[+\] http" arachni_report*.txt |tr "]" "\n" |grep "$BASE_URL"|sed 's/^ //'|grep "://"
	#grep "^\[-\] http" arachni_report*.txt |tr "]" "\n" |grep "$BASE_URL"|sed 's/^ //'|grep "://"
	#grep "^\[+\] http" $FILE |tr "]" "\n" |grep "$BASE_URL"|sed 's/^ //'|grep "://"
	#grep "^\[-\] http" $FILE |tr "]" "\n" |grep "$BASE_URL"|sed 's/^ //'|grep "://"
	grep "^\[[+-]\] http" $FILE |tr " " "\n" | grep "^$BASE_URL"
	;;
  *)
	echo "Undefined Type: $TYPE"
esac
