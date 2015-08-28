#!/usr/bin/env bash

TEST_URLS=$(echo "$(dirname $0)/test_urls.txt")

if [ $# -ne 1 ]; then
	echo "Please specify OWTF directory to test!"
	echo "Syntax $0 <OWTF release directory>"
	exit
fi
OWTF_DIR=$1

$OWTF_DIR/owtf.py -t passive $TEST_URLS
$OWTF_DIR/owtf.py -t semi_passive $TEST_URLS
$OWTF_DIR/owtf.py -t active $TEST_URLS
