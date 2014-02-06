#!/usr/bin/env bash
#
# Date:    2013-12-30
#
# owtf is an OWASP+PTES-focused try to unite great tools and facilitate pen testing
# Copyright (c) 2011, Abraham Aranguren <name.surname@gmail.com> Twitter: @7a_ http://7-a.org
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# * Redistributions of source code must retain the above copyright 
# notice, this list of conditions and the following disclaimer.
# * Redistributions in binary form must reproduce the above copyright
# notice, this list of conditions and the following disclaimer in the
# documentation and/or other materials provided with the distribution.
# * Neither the name of the copyright owner nor the
# names of its contributors may be used to endorse or promote products
# derived from this software without specific prior written permission.
# 
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
# ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

. $(pwd)/../../../../../../../scripts/openvas/openvas_init.sh

URL=$1

CLEAN_URL=$(echo $URL |sed -e 's/^http:\/\///g' -e 's/^https:\/\///g')

DATE=$(date +%F_%R_%S | sed 's/:/_/g')

OUTFILE="OpenVAS_Main_Report_$DATE"

echo

$OWTF_DIR/scripts/openvas/openvas_quick_check.sh 

passwd=$(get_config_setting "OPENVAS_PASS")

if [[ "$passwd" = "" ]]
then 
  $OWTF_DIR/scripts/openvas/generate_pass_openvas.sh 
  passwd=$(get_config_setting "OPENVAS_PASS")
fi


echo "Runnig OpenVAS Plugin.."

echo  ""

#Creating target
TARGET_ID=$(omp -u admin -w $passwd -iX '<create_target><name>'OWTF_Target_$CLEAN_URL'</name><hosts>'$CLEAN_URL'</hosts></create_target>'  | sed 's/  *//g'|cut -f2 -d'"')
  
if [[ $TARGET_ID = *Targetexistsalready* ]]; then
  echo -e "Target already exists\nExiting from OpenVAS.."
  exit
fi

if [ "$TARGET_ID" == "" ]
then
  echo "Authentication Failure"
  exit
fi 
 


echo "#########################################################################"
echo "###                                                                   ### 
###                      __  __  __            __  __                 ###
###                     |  ||__||__ |\ | \  / |__||__                 ###
###                     |__||   |__ | \|  \/  |  | __|                ###
###                                                                   ###
### "

echo "###--------------Target Created : OWTF_Target_$CLEAN_URL..."

#Task creation

TASK_ID=$(omp -u admin -w $passwd --xml="<create_task><name>OWTF_Task_$CLEAN_URL</name>
                                       <config id=\"$CONFIG_ID\"/>
                                       <target id=\"$TARGET_ID\"/>
                    </create_task>" |  sed 's/  *//g'|cut -f2 -d'"')

echo "###-------------------------------------------------------------------###"
echo "###--------------Task Created : OWTF_Task_$CLEAN_URL..."

#getting report id

REPORT_ID=$(omp -u admin -w $passwd --xml="<start_task task_id=\"$TASK_ID\"/>" | sed 's/  *//g'|cut -f3 -d'>' |cut -f1 -d'<')

echo "###-------------------------------------------------------------------###"
echo "###--------------Task Started-----------------------------------------###"

echo "###-------------------------------------------------------------------###"

echo "###--------------Status Check-----------------------------------------###"
echo -e "\n"





STATUS=$(get_progress_status $passwd $TASK_ID)

echo "In Progress...Hang tight !!"
echo "(You can check your status of progress by going to http://127.0.0.1:$PGSAD and logging in
with the username 'admin' and the password and then going to tasks tab in scan management)".
while [[ $STATUS != *Done* ]]
do
   sleep 1 
   STATUS=$(get_progress_status $passwd $TASK_ID)
   if [[ $STATUS = *Stopped* ]];then
     break
   fi
done

#deleting the task

omp -u admin -w $passwd --delete-task $TASK_ID

echo -e "\n"
echo -n "###------------------Done !-------------------------------------------###"
echo -e "\n"
echo "###-------------------------------------------------------------------###"
echo "###--------------Status Check Complete--------------------------------###"
echo "###-------------------------------------------------------------------###"


echo "###--------------Creating report in $DIR"...

#get report

omp -u admin -w $passwd --get-report $REPORT_ID  --format $HTML_FORMAT_ID  > $OUTFILE.html

echo "###-------------------------------------------------------------------###"
echo "###--------------Report Generated-------------------------------------###"
echo -e "\n"

echo "###----------------- [*] Done!] --------------------------------------###"
echo "#########################################################################"
exit