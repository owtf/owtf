#!/usr/bin/env bash
#
# Description:
# Some tools (whatweb and others) require ruby 1.8 and others (i.e. BeEF) require ruby 1.9.2
# This script allows you to quickly change from ruby 1.8 to 1.9.2 and viceversa

# TODO: replace Ruby 1.9.2 with 1.9.3

SCRIPT=`basename $0`

if [ $# -ne 1 ]; then
    cat <<-EOF
	Usage: $SCRIPT <ruby_version: 1.8, 1.9.2>

	Examples:
	  - Set ruby 1.8: $SCRIPT 1.8
	  - Set ruby 1.9.2: $SCRIPT 1.9.2
EOF
    exit
fi

VERSION=$1
echo "* Switching to Ruby $VERSION..."

OPTION="1"
if [ $VERSION == '1.9.2' ]; then
    OPTION="2"
fi

# Export version gem paths
export GEM_PATH=/var/lib/gems/$VERSION/gems
export GEM_HOME=/var/lib/gems/$VERSION/gems

# Pick ruby version
(sleep 2 ; echo $OPTION) | update-alternatives --config ruby

if [ -z $? ] ; then
    echo "* Successfully switched to Ruby $VERSION."
else
    echo "* Could not switch to Ruby $VERSION."
fi
