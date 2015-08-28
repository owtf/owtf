#!/usr/bin/env sh
# Description: Installation script for tools not in Backtrack or unreliable in Backtrack
# (i.e. Backtrack chose the development version instead of the stable one)

DIR=$(dirname $0) # Get current directory
echo "Copying (linux) sbd from BT to agent directory .. (reason: GPL)"
cp /usr/bin/sbd $DIR/shell/linux/sbd
