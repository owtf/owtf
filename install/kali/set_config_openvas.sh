#!/usr/bin/env bash


echo -n "Enter the port for gsad web interface, default is 9392 (Use default (Y/N)):"
read ch
if  ([[ $ch = "y" ]]  || [[ $ch = "Y" ]] || [[ -z $ch ]])
then 
 echo $ch
 port=9392
else 
 echo -n "Enter the port :"
 read port
fi
dir=$(pwd)
dir1="$dir/../../profiles/general/default.cfg"
sed -i '/OPENVAS_GSAD_PORT/d' $dir1
echo "OPENVAS_GSAD_PORT: "$port >> $dir1

read -s -p "Enter password for admin(cannot be blank) : `echo  $'\n '`Password :" PASS
sed -i '/OPENVAS_PASS/d' $dir1
echo "OPENVAS_PASS: "$PASS >> $dir1
echo
echo

echo -e "Enter the scan configuration type \n1)Full and Fast \n2)Full and fast ultimate \n3)Full and very deep \n4)Full and very deep ultimate:"

flag=1
while [[ $flag -eq 1 ]]
do
echo -n "Enter your choice (by default it's Full and Fast ) :"
read ch
flag=0
if  ([[ $ch = "1" ]]  || [[ -z $ch ]])
then 
 configid="daba56c8-73ec-11df-a475-002264764cea"
elif [[ $ch = "2" ]]
then
 configid="698f691e-7489-11df-9d8c-002264764cea"
elif [[ $ch = "3" ]]
then
 configid="708f25c4-7489-11df-8094-002264764cea"
elif [[ $ch = "4" ]]
then
 configid="74db13d6-7489-11df-91b9-002264764cea"
else 
 flag=1
fi
done

sed -i '/OPENVAS_CONFIG_ID/d' $dir1
echo "OPENVAS_CONFIG_ID: "$configid >> $dir1




