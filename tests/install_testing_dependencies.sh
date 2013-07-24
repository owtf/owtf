#!/bin/bash

# This script installs the packages that allow running the tests of OWTF

echo -e "[+] Installing nose..."
pip install nose
echo -e "[+] Installing flexmock..."
pip install flexmock
echo -e "[+] Installing PyHamcrest..."
pip install pyhamcrest
echo -e "[+] Installing coverage..."
pip install coverage
echo -e "[+] Installation finished."