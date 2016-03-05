#!/usr/bin/env bash
stable="Package: *\nPin: release a=stable\nPin-Priority: 1000\n"

testing="\n# The following is if youare also using unstable and/or testing repo\n#Package: *\n#Pin: release a=testing\n#Pin-Priority: 950\n"

unstable="\n#Package: *\n#Pin: release a=unstable\n#Pin-Priority: 900\n"

kali="\nPackage: *\nPin: release n=kali\nPin-Priority: 850\n"

kaliEdge="\nPackage: *\nPin: release n=kali-bleeding-edge\nPin-Priority: 800"

echo -e ${stable} ${testing} ${unstable} ${kali} ${kaliEdge} > /etc/apt/preferences.d/kali_pref
