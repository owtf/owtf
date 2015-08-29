#!/usr/bin/env sh
#
# Description:
#       Script to fix the MetaSploit install on Samurai by removing default ruby-bundler

echo "[*] Removing current package ruby-bundler to avoid conflict with MetaSploit-Framework.."
sudo -E apt-get remove ruby-bundler
echo "[*] Done!"
