#!/bin/bash
# Description:
#       Script to emumerate subdomains for a given domain
#       and checks if it's vulnerable to takeover
#
# Requires:
# - amass
# - sublist3r
# - subjack


echo 
echo ----------------------------------------------------
echo "                 Sub_Takeover                    "
echo " Checks if subdomains are vulnerable for Takeover"
echo ----------------------------------------------------

echo
echo

SUBLIST3R_PATH="/root/.owtf/tools/restricted/sublist3r/Sublist3r"
SUBJACK_PATH="/root/go/bin"
SUBJACK_FINGERPRINT_PATH="/root/go/src/github.com/haccer/subjack/"

#Creating a temporary file to append all the subdomains found
touch subdomain_$1.txt


#Find subdomains from online services(without tools)
subdomain_without_tools(){
echo "[*]STARTING SUBDOMAIN ENUMERATION...."
echo
echo "[*]Level 1:Subdomain Enumeration using Online services"
echo "[*]Level 2:Subdomain Enumeration using Amass"
echo "[*]Level 3:Subdomain Enumeration using Sublist3r"
echo
echo "[*] Starting Level 1"
#certspotter.com
curl -s -N "https://certspotter.com/api/v1/issuances?domain=$1&expand=dns_names" | jq -r '.[].dns_names[]' 2>/dev/null | grep -o "\w.*$1" | sort -u >> subdomain_$1.txt &
#crt.sh
curl -s -N "https://crt.sh/?q=%25.$1&output=json"| jq -r '.[].name_value' 2>/dev/null | sed 's/\*\.//g' | sort -u | grep -o "\w.*$1" >> subdomain_$1.txt &
#hackertarget.com
curl -s -N "https://api.hackertarget.com/hostsearch/?q=$1" | cut -d ',' -f1 | sort -u >> subdomain_$1.txt &
#alienvault.com
curl -s -N "https://otx.alienvault.com/api/v1/indicators/domain/$1/passive_dns"|jq '.passive_dns[].hostname' 2>/dev/null |grep -o "\w.*$1"|sort -u >> subdomain_$1.txt &
#riddler.io
curl -s -N "https://riddler.io/search/exportcsv?q=pld:$1"| grep -o "\w.*$1"|awk -F, '{print $6}'|sort -u  >> subdomain_$1.txt &
#virustotal.com
curl -s -N "https://www.virustotal.com/ui/domains/$1/subdomains?limit=40" | grep '"id":' | cut -d '"' -f4 | sort -u >> subdomain_$1.txt &
#web.archive.org
curl -s -N "http://web.archive.org/cdx/search/cdx?url=*.$1/*&output=text&fl=original&collapse=urlkey" | sort | sed -e 's_https*://__' -e "s/\/.*//" -e 's/:.*//' -e 's/^www\.//' |sort -u >> subdomain_$1.txt &
#urlscan.io
curl -s -N "https://urlscan.io/api/v1/search/?q=domain:$1"|jq '.results[].page.domain' 2>/dev/null |grep -o "\w.*$1"|sort -u >> subdomain_$1.txt &
# threatminer.org
curl -s -N "https://api.threatminer.org/v2/domain.php?q=$1&rt=5" | jq -r '.results[]' 2>/dev/null |grep -o "\w.*$1"|sort -u >> subdomain_$1.txt &
# threatcrowd.org
curl -s -N "https://www.threatcrowd.org/searchApi/v2/domain/report/?domain=$1"|jq -r '.subdomains' 2>/dev/null |grep -o "\w.*$1" |sort -u >> subdomain_$1.txt &
#bufferover.run Rapid7
curl -s -N "https://dns.bufferover.run/dns?q=.$1" | jq -r .FDNS_A[] 2>/dev/null | cut -d ',' -f2 | grep -o "\w.*$1" | sort -u >> subdomain_$1.txt &
curl -s -N "https://dns.bufferover.run/dns?q=.$1" | jq -r .RDNS[] 2>/dev/null | cut -d ',' -f2 | grep -o "\w.*$1" | sort -u >> subdomain_$1.txt &
curl -s -N "https://tls.bufferover.run/dns?q=.$1" | jq -r .Results 2>/dev/null | cut -d ',' -f3 |grep -o "\w.*$1"| sort -u >> subdomain_$1.txt &
#dnsdumpster
cmdtoken=$(curl -ILs https://dnsdumpster.com | grep csrftoken | cut -d " " -f2 | cut -d "=" -f2 | tr -d ";");curl -s --header "Host:dnsdumpster.com" --referer https://dnsdumpster.com --user-agent "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:45.0) Gecko/20100101 Firefox/45.0" --data "csrfmiddlewaretoken=$cmdtoken&targetip=$1" --cookie "csrftoken=$cmdtoken; _ga=GA1.2.1737013576.1458811829; _gat=1" https://dnsdumpster.com > dnsdumpster.html;cat dnsdumpster.html|grep "https://api.hackertarget.com/httpheaders"|grep -o "\w.*$1"|cut -d "/" -f7|sort -u >> subdomain_$1.txt;rm dnsdumpster.html &&
#rapiddns.io
curl -s "https://rapiddns.io/subdomain/$1?full=1#result" | grep -oaEi "https?://[^\"\\'> ]+" | grep $1 | cut -d "/" -f3 | sort -u >> subdomain_$1.txt &
# jldc
curl -s -N "https://jldc.me/anubis/subdomains/$1?limit=40" | grep '"id":' | cut -d '"' -f4 | sort -u >> subdomain_$1.txt
echo
echo "[*] Level 1 Done!!"
}

#Find Subdomains using Sublist3r, Amass and bbot
subdomain_with_tools()
{
echo
echo "[*] Starting Level 2"
echo
amass enum -d $1 >> subdomain_$1.txt
echo
echo "[*] Done Level 2"
echo
echo "[*] Starting Level 3"
echo
python3 $SUBLIST3R_PATH/sublist3r.py -d $1 -o sublist3r_$1.txt
#Appending file contents to subdomain.txt(Not appending directly because ASCII art in Sublist3r is being obfuscated,due to which junk data is being added to subdomains list)
cat sublist3r_$1.txt >> subdomain_$1.txt
bbot -y -s -t google.com -f subdomain-enum -om human | grep '[DNS_NAME]' | cut -f2 >> bbot_$1.txt
cat bbot_$1.txt >> subdomain_$1.txt


echo
echo "[*] Level 3 Done!!"
echo
echo "[*]SUBDOMAIN ENUMERATION DONE!!"
echo
}

#Invoking Functions
subdomain_without_tools $1
subdomain_with_tools $1

#Removing duplicates
awk '!a[$0]++' subdomain_$1.txt > subdomains_$1.txt

#Calculating Total subdomains
TOTAL_SUBDOMAINS=$(wc -l < subdomains_$1.txt)
echo "[*]Total Subdomains Found:$TOTAL_SUBDOMAINS"

echo 
checkTakeover(){
echo "[*]CHECKING IF SUBDOMAINS ARE VULNERABLE TO TAKEOVER..."
echo
$SUBJACK_PATH/subjack -a -v -w subdomains_$1.txt -t 20 -timeout 15 -c $SUBJACK_FINGERPRINT_PATH/fingerprints.json -o takeover_$1.txt
echo 
echo "[*]DONE"
echo
}

#Invoking function
checkTakeover $1

#Removing temporary files
rm -r subdomain_$1.txt
rm -r sublist3r_$1.txt
rm -r bbot_$1.txt

#OutputInformation
echo "[*]Output Information:"
echo
echo "[*]Subdomains: subdomains_$1.txt"
echo "[*]Takeover: takeover_$1.txt"
echo
echo "[*]SCANNING DONE!!"
echo
