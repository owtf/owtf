#/usr/bin/env bash

<<comm
echo "root -  $1"
echo "op_tar_dir- $2"
echo "target_scr -   $3"
echo "tar_list - $4"
echo "trans_list - $5"
comm


java -jar $1/zest/zest.jar "$1" "$2" "$3" "$4" "$5" "$6"

