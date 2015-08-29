#!/usr/bin/env bash
#
# Description:
#       Script to run w3af with appropriate switches for basic and time-efficient web app/web server vuln detection
#	Because of above no directory brute-forcing will be done here (too slow and would be done later with dirbuster, etc)
#
# Date:    2011-10-02

if [ -f ~/.w3af/startup.conf ]
then
    if ! grep -i "^accepted-disclaimer = true$" ~/.w3af/startup.conf
    then
        echo "accepted-disclaimer = true" >> ~/.w3af/startup.conf
    fi
else
    if [ ! -d ~/.w3af ]
    then
        mkdir ~/.w3af
    fi
    echo "[STARTUP_CONFIG]" >> ~/.w3af/startup.conf
    echo "auto-update = true" >> ~/.w3af/startup.conf
    echo "frequency = D" >> ~/.w3af/startup.conf
    echo "accepted-disclaimer = true" >> ~/.w3af/startup.conf
fi

if [ $# -ne 3 -a $# -ne 4 ]; then
        echo "Usage $0 <tool_bin> <target url> <proxy> (<user agent -spaces replaced by # symbol->)"
        exit
fi

TOOL_BIN=$1
URL=$2
PROXY=$3
PROXY_IP=$(echo $PROXY | cut -d ":" -f 1)
PROXY_PORT=$(echo $PROXY | cut -d ":" -f 2)
USER_AGENT="Mozilla/5.0 (X11; Linux i686; rv:6.0) Gecko/20100101 Firefox/6.0" # Default to something less obvious
if [ "$4" != "" ]; then
	USER_AGENT=$(echo $4 | sed 's/#/ /g') # Expand to real User Agent
fi

DATE=$(date +%F_%R:%S | sed 's/:/_/g')
OUTFILE="w3af_report$DATE"
REPORT_HTTP=$OUTFILE.http.txt
REPORT_TXT=$OUTFILE.txt
REPORT_HTML=$OUTFILE.html
REPORT_XML=$OUTFILE.xml
W3AF_SCRIPT=$OUTFILE.script.w3af

# "set fuzzFormComboValues all" removed because: In a form with ~10 inputs where some of those are <select> the
# following setting: "set fuzzFormComboValues all" might make w3af run for LOTS of time.
# Please see: http://sourceforge.net/mailarchive/forum.php?thread_name=CA%2B1Rt67bN3-2OpB%2B7SOGO7%3D92KWXBMdbaztpa885f%3Du2GzjcFg%40mail.gmail.com&forum_name=w3af-users

echo "# w3af script used for testing
cleanup
profiles
use full_audit
back
plugins
audit !buffer_overflow
bruteforce !basic_auth,!form_auth
crawl web_spider, robots_txt, content_negotiation, digit_sum, url_fuzzer
infrastructure shared_hosting, allowed_methods, server_status
output html_file,text_file,xml_file
output config html_file
set output_file $REPORT_HTML
back
output config text_file
set http_output_file $REPORT_HTTP
set output_file $REPORT_TXT
back
output config xml_file
set output_file $REPORT_XML
back
back
misc-settings
set fuzz_url_filenames True
set fuzz_cookies True
set max_discovery_time 240
back
http-settings
set timeout 30
set user_agent $USER_AGENT
set max_http_retries 3
back
target
set target $URL
back
start
exit
" > $W3AF_SCRIPT
#Redirecting stdout/stderr is messy due to having to use a background tail process with remains hanging if "Control+C"
#echo "./w3af_console -n -s $W3AF_SCRIPT" > $LOG_TXT 2> $ERR_FILE
COMMAND="$TOOL_BIN -n -s $W3AF_SCRIPT"
echo "[*] Running: $COMMAND"
$TOOL_BIN -n -s $W3AF_SCRIPT

strings $REPORT_HTTP > $REPORT_HTTP.tmp # Removing binary garbage
mv $REPORT_HTTP.tmp $REPORT_HTTP

echo
echo "[*] Done!"

#discovery webSpider,sharedHosting,allowedMethods,digitSum,content_negotiation,dir_bruter,robotsReader,serverStatus,urlFuzzer
#discovery detectReverseProxy,detectTransparentProxy
#discovery archiveDotOrg,bing_spider,dnsWildcard,domain_dot,findDVCS,findGit,fingerBing,fingerPKS,ghdb,phishtank,sharedHosting,xssedDotCom,yahooSiteExplorer,zone_h
#discovery fingerprint_os,frontpage_version,halberd,hmap,oracleDiscovery,phpEggs,phpinfo,pykto,ria_enumerator,dotNetErrors,wordpress_fingerprint,wsdlFinder
#discovery detectReverseProxy,detectTransparentProxy
#discovery archiveDotOrg,bing_spider,dnsWildcard,domain_dot,findDVCS,findGit,fingerBing,fingerPKS,ghdb,phishtank,sharedHosting,xssedDotCom,yahooSiteExplorer,zone_h
#discovery fingerprint_os,frontpage_version,halberd,hmap,oracleDiscovery,phpEggs,phpinfo,pykto,ria_enumerator,dotNetErrors,wordpress_fingerprint,wsdlFinder
#discovery afd,fingerprint_WAF,favicon_identification,findBackdoor,findCaptchas
#discovery allowedMethods,digitSum,content_negotiation,dir_bruter,robotsReader,serverStatus,sitemapReader,urlFuzzer,userDir
#discovery all,!wordnet <- crap!!
#discovery webSpider,sharedHosting,allowedMethods,digitSum,content_negotiation,dir_bruter,robotsReader,serverStatus,sitemapReader,urlFuzzer
