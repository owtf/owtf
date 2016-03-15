#!/usr/bin/env sh

# ======================================
#  COLORS
# ======================================
bold=$(tput bold)
reset=$(tput sgr0)

danger=${bold}$(tput setaf 1)   # red
warning=${bold}$(tput setaf 3)  # yellow
info=${bold}$(tput setaf 6)     # cyan
normal=${bold}$(tput setaf 7)   # white
# =======================================


# =======================================
#  USER-AGENT
# =======================================

user_agent='Mozilla/5.0 (X11; Linux i686; rv:6.0) Gecko/20100101 Firefox/15.0'
