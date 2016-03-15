#!/usr/bin/env sh

FILE_PATH=$(readlink -f "$0")
INSTALL_DIR=$(dirname "$FILE_PATH")
RootDir=${RootDir:-$(dirname "$INSTALL_DIR")}
local_hash_file="$RootDir/zest/release.hash"

# bring in the variables: `normal`, `info`, `warning`, `danger`, `reset`, `user_agent`
. "$(dirname "$(readlink -f "$0")")/utils.sh"

if [ -f ${local_hash_file} ]; then
  local_hash="$(cat ${local_hash_file})"
else
  local_hash=""
fi

upstream_hash="$(wget --user-agent="${user_agent}" --tries=3 -O- -q https://raw.githubusercontent.com/owtf/owtf-zest-jars/master/release.hash)"
install() {
  wget --user-agent="${user_agent}" --tries=3 https://api.github.com/repos/owtf/owtf-zest-jars/tarball -O zest-jars.tar.gz
  tar zxf zest-jars.tar.gz
  cd */.
  cp -r * ${RootDir}/zest
}



# check if local hash present
if [ -z ${local_hash} ]; then
  echo "${warning}[!] Local hash not present${reset}"
  install
else
  echo "${normal}[*] Local hash present, comparing with upstream..${reset}"
  if ! [ "${local_hash}" = "${upstream_hash}" ]; then
    echo "${warning}[!] Hashes do not match, updating jars..${reset}"
    install
  else
    echo "${normal}Hashes match. Continuing..${reset}"
  fi
fi

