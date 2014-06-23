#!/usr/bin/env bash
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# This script is for running the Zest command line tool

#Check the java version (min java 7)
JAVAV=`java -version 2>&1 |awk 'NR==1{ gsub(/"/,""); print $3 }'`

if [[ $JAVAV == 1.[78]* ]]; then
    # OK
    echo "Using Java version: $JAVAV"
else
    echo "Exiting: Zest requires a minimum of Java 7 to run."
    exit 1
fi

#Dereference from link to the real directory
SCRIPTNAME=$0

#While name of this script is symbolic link
while [ -L "$SCRIPTNAME" ] ; do 
    #Dereference the link to the name of the link target 
    SCRIPTNAME=$(ls -l "$SCRIPTNAME" | awk '{ print $NF; }')
done

#Base directory where Zest is installed
BASEDIR=$(dirname "$SCRIPTNAME")

#Switch to the directory where Zest is installed
cd "$BASEDIR"

#Start Zest command line
exec java -jar "${BASEDIR}/zest_runner.jar" "$1" "$2"

