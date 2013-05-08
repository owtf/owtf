#!/usr/bin/env bash
# Description: This script grabs all the excellent CMS Explorer dictionaries, updates them and converts them into DirBuster format (much faster than CMS Explorer)
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

CMS_EXPLORER_DIR="$(dirname $0)/cms-explorer/cms-explorer-1.0"
CMS_DICTIONARIES_DIR="$(dirname $0)/restricted/cms" 

DICTIONARIES="$CMS_EXPLORER_DIR/drupal_plugins.txt
$CMS_EXPLORER_DIR/joomla_themes.txt
$CMS_EXPLORER_DIR/wp_plugins.txt
$CMS_EXPLORER_DIR/drupal_themes.txt
$CMS_EXPLORER_DIR/wp_themes.txt
$CMS_EXPLORER_DIR/joomla_plugins.txt"

echo "[*] Going into directory: $CMS_EXPLORER_DIR"
cd $CMS_EXPLORER_DIR

echo "[*] Updating cms-explorer.pl dictionaries.."
./cms-explorer.pl -update

# leaving the directory in order to copy the lists from dict_root
cd ../../

echo "[*] Copying updated dictionaries from $CMS_EXPLORER_DIR to $CMS_DICTIONARIES_DIR"
for i in $(echo $DICTIONARIES); do
	cp $i $CMS_DICTIONARIES_DIR # echo "[*] Copying $i .."
done

cd $CMS_DICTIONARIES_DIR

DIRBUSTER_PREFIX="dir_buster"
for cms in $(echo "drupal joomla wp"); do
	mkdir -p $cms # Create CMS specific directory
	rm -f $cms/* # Remove previous dictionaries
	mv $cms* $cms 2> /dev/null # Move relevant dictionaries to directory, getting rid of "cannot move to myself" error, which is ok
	cd $cms # Enter directory
	for dict in $(ls); do # Now process each CMS-specific dictionary and convert it
		cat $dict | tr '/' "\n" | sort -u > $DIRBUSTER_PREFIX.$dict # Convert to DirBuster format (i.e. get rid of the "/" and duplicate parent directories)
		rm -f $dict # Remove since this only works with CMS explorer
	done
	# Create all-in-one CMS-specific dictionaries:
	cat $DIRBUSTER_PREFIX* > $DIRBUSTER_PREFIX.all.$cms.txt
	cd ..
done

echo "[*] Creating all-in-one CMS dictionaries for DirBuster and CMS Explorer"
for bruteforcer in $(echo "$DIRBUSTER_PREFIX"); do
	ALLINONE_DICT="$bruteforcer.all_in_one.txt"
	rm -f $ALLINONE_DICT # Remove previous, potentially outdated all-in-one dict
	for all_dict in $(find . -name *all*.txt | grep $bruteforcer); do
		cat $all_dict >> $ALLINONE_DICT
	done
	cat $ALLINONE_DICT | sort -u > $ALLINONE_DICT.tmp # Remove duplicates, just in case
	mv $ALLINONE_DICT.tmp $ALLINONE_DICT
done
