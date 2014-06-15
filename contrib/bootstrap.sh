#!/bin/bash


Install(){
  cd install/; python install.py
}

echo "Please ensure that you have minimum 60 MB space free on your current partition.."

echo "Select OWTF version, stable or bleeding-edge:"

OPTIONS=("OWTF 0.45.0 Winter Blizzard (stable)" "OWTF GSoC'14-dev" "Quit")
select opt in "${OPTIONS[@]}"
do
    case $opt in
        "OWTF 0.45.0 Winter Blizzard (stable)")
            echo "Fetching repository and starting installation process"
            echo "Make sure you have sudo access."
            curl -L https://github.com/owtf/owtf/archive/v0.45.0_Winter_Blizzard.tar.gz | tar xvz
            mv owtf-0.45.0_Winter_Blizzard owtf/
            cd owtf/
            Install
            ;;
        "OWTF GSoC'14 Lions (developement)")
            echo "Fetching bleeding edge repository.."
            echo "Make sure you have sudo access."
            curl -L https://github.com/owtf/owtf/archive/lions_2014.zip
            unzip owtf-lions_2014.zip && mv owtf-lions_2014 owtf/
            cd owtf
            Install
            ;;
        "Quit")
            break
            ;;
        *) echo invalid option;;
    esac
done
