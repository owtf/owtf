#!/bin/sh

FILE_PATH=$(readlink -f "$0")
INSTALL_DIR=$(dirname "$FILE_PATH")
RootDir=${RootDir:-$(dirname "$INSTALL_DIR")}

local_hash="$(cat $RootDir/zest/release.hash)"
upstream_hash="$(wget -O- -q https://raw.githubusercontent.com/owtf/owtf-zest-jars/master/release.hash)"
install_command="wget https://api.github.com/repos/owtf/owtf-zest-jars/tarball -O zest-jars.tar.gz; tar zxf zest-jars.tar.gz; cd */.; cp -r * $RootDir/zest"


# check if local hash present
if [ ! $local_hash ]; then
  echo "Local hash not present"
  $install_command
fi

echo "Local hash present, comparing with upstream.."

if ! [ "$local_hash" = "$upstream_hash" ]; then
	echo "Hashes do not match, updating jars"
  $install_command
else
  echo "Hashes match. Continuing.."
fi

