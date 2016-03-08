#!/usr/bin/env sh
# This script is a wrapper over apt-get that installs
# the packages only after checking the disk available space
#
# Usage $0 <package> [package] ..

# bring in the color variables: `normal`, `info`, `warning`, `danger`, `reset`
. "$(dirname "$(readlink -f "$0")")/colors.sh"

usage() {
    echo "${info}[*] Usage: sh $0 <package name> [package name]${reset}"
}

available_disk_size() {
    echo "${info}$(($(stat -f --format="%a*%S" .)))${reset}"
}

# Bail out if not root privileges
if [ "$(id -u)" != "0" ]; then
   echo "${warning}[!] This script must be run as root${reset}" 1>&2
   exit 1
fi

# Parse command line parameters.
if [ $# -lt 1 ]; then
    echo "${warning}[!] Specify the package(s) name(s)${reset}"
    usage
    exit 1
fi

# Compute the download size for the specified packages
size=0
for package in "$@"
do
    package_size=$(apt-cache --no-all-versions show ${package} | sed -n -e 's/^Size: //p')
    if [ package_size ]; then
        size=$(( size + package_size))
    fi
done

# Check if the current available disk size is enough.
while [ "${reset}$(available_disk_size)" -lt "$size" ]; do
    echo "${warning}[!] Not enough available space for downloading $@${reset}"
    echo "${warning}[!] Please free the required size and proceed or skip this step (press \'n\') [Y/n]${reset}"
    read yn
    if [ "$yn" = 'n' ]; then
        exit 0
    fi
done

# If all the checks passed, install the required packages.
for package in "$@"
do
    apt-get -y install ${package}
done
