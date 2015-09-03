#!/usr/bin/env sh
# This script is a wrapper over apt-get that installs
# the packages only after checking the disk available space
#
# Usage $0 <package> [package] ..

usage() {
    echo "[*] Usage: sh $0 <package name> [package name]"
}

available_disk_size() {
    echo "$(($(stat -f --format="%a*%S" .)))"
}

# Bail out if not root privileges
if [ "$(id -u)" != "0" ]; then
   echo "This script must be run as root" 1>&2
   exit 1
fi

# Parse command line parameters.
if [ $# -lt 1 ]; then
    echo "[!] Specify the package(s) name(s)"
    usage
    exit 1
fi

# Compute the download size for the specified packages
size=0
for package in "$@"
do
    package_size=$(apt-cache --no-all-versions show $package | sed -n -e 's/^Size: //p')
    if [ package_size ]; then
        size=$(( size + package_size))
    fi
done

# Check if the current available disk size is enough.
while [ "$(available_disk_size)" -lt "$size" ]; do
    echo "[!] Not enough available space for downloading $@"
    echo "[!] Please free the required size and proceed or skip this step (press \'n\') [Y/n]"
    read yn
    if [ "$yn" = 'n' ]; then
        exit 0
    fi
done

# If all the checks passed, install the required packages.
for package in "$@"
do
    apt-get install $package
done
