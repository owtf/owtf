#!/bin/sh

FILE_PATH=$(readlink -f "$0")
INSTALL_DIR=$(dirname "$FILE_PATH")
RootDir=${RootDir:-$(dirname "$INSTALL_DIR")}
local_hash_file="$RootDir/zest/release.hash"

if [ -f $local_hash_file ]; then
  local_hash="$(cat $local_hash_file)"
else
  local_hash=""
fi

upstream_hash="$(wget -O- -q https://raw.githubusercontent.com/owtf/owtf-zest-jars/master/release.hash)"

install() {
  wget https://api.github.com/repos/owtf/owtf-zest-jars/tarball -O zest-jars.tar.gz
  tar zxf zest-jars.tar.gz
  cd */.
  cp -r * $RootDir/zest
}

# check if local hash present
if [ -z $local_hash ]; then
  echo "Local hash not present"
  install
else
  echo "Local hash present, comparing with upstream.."
  if ! [ "$local_hash" = "$upstream_hash" ]; then
    echo "Hashes do not match, updating jars.."
    install
  else
    echo "Hashes match. Continuing.."
  fi
fi

