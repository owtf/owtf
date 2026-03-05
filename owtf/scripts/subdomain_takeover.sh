#!/bin/bash
# Description:
#       Script to enumerate subdomains for a given domain
#       and checks if it's vulnerable to takeover
#
# Requires:
# - amass
# - sublist3r
# - subjack
#
# Arguments:
#   $1 - target domain (host_name)
#   $2 - plugin output directory (###plugin_output_dir###)
#   $3 - subjack binary path (@@@TOOL_SUBJACK@@@)
#   $4 - subjack fingerprints path (@@@TOOL_SUBJACK_FINGERPRINTS@@@)
#   $5 - sublist3r script path (@@@TOOL_SUBLIST3R@@@)

echo
echo "----------------------------------------------------"
echo "                 Sub_Takeover                      "
echo " Checks if subdomains are vulnerable for Takeover  "
echo "----------------------------------------------------"
echo

# --- Argument validation ---
if [ $# -ne 5 ]; then
    echo "[!] Usage: $0 <domain> <output_dir> <subjack_bin> <subjack_fingerprints> <sublist3r_path>"
    exit 1
fi

DOMAIN=$1
OUTPUT_DIR=$2
SUBJACK_BIN=$3
SUBJACK_FINGERPRINTS=$4
SUBLIST3R_PATH=$5

# --- Tool availability check ---
check_tool() {
    if [ ! -f "$1" ] && ! command -v "$1" &>/dev/null; then
        echo "[!] Required tool not found: $1"
        return 1
    fi
    return 0
}

# --- Output directory setup ---
mkdir -p "$OUTPUT_DIR"
SUBDOMAIN_TEMP="$OUTPUT_DIR/subdomain_${DOMAIN}.txt"
SUBDOMAIN_FINAL="$OUTPUT_DIR/subdomains_${DOMAIN}.txt"
TAKEOVER_OUT="$OUTPUT_DIR/takeover_${DOMAIN}.txt"
SUBLIST3R_OUT="$OUTPUT_DIR/sublist3r_${DOMAIN}.txt"

touch "$SUBDOMAIN_TEMP"

# --- Level 1: Online sources ---
subdomain_without_tools() {
    echo "[*] STARTING SUBDOMAIN ENUMERATION...."
    echo
    echo "[*] Level 1: Subdomain Enumeration using Online services"
    echo "[*] Level 2: Subdomain Enumeration using Amass"
    echo "[*] Level 3: Subdomain Enumeration using Sublist3r"
    echo
    echo "[*] Starting Level 1"

    # certspotter.com
    curl -s -N "https://certspotter.com/api/v1/issuances?domain=$DOMAIN&expand=dns_names" \
        | jq -r '.[].dns_names[]' 2>/dev/null \
        | grep -o "\w.*$DOMAIN" | sort -u >> "$SUBDOMAIN_TEMP" &

    # crt.sh
    curl -s -N "https://crt.sh/?q=%25.$DOMAIN&output=json" \
        | jq -r '.[].name_value' 2>/dev/null \
        | sed 's/\*\.//g' | sort -u \
        | grep -o "\w.*$DOMAIN" >> "$SUBDOMAIN_TEMP" &

    # hackertarget.com
    curl -s -N "https://api.hackertarget.com/hostsearch/?q=$DOMAIN" \
        | cut -d ',' -f1 | sort -u >> "$SUBDOMAIN_TEMP" &

    # alienvault.com
    curl -s -N "https://otx.alienvault.com/api/v1/indicators/domain/$DOMAIN/passive_dns" \
        | jq '.passive_dns[].hostname' 2>/dev/null \
        | grep -o "\w.*$DOMAIN" | sort -u >> "$SUBDOMAIN_TEMP" &

    # virustotal.com
    curl -s -N "https://www.virustotal.com/ui/domains/$DOMAIN/subdomains?limit=40" \
        | grep '"id":' | cut -d '"' -f4 | sort -u >> "$SUBDOMAIN_TEMP" &

    # web.archive.org
    curl -s -N "http://web.archive.org/cdx/search/cdx?url=*.$DOMAIN/*&output=text&fl=original&collapse=urlkey" \
        | sort | sed -e 's_https*://__' -e "s/\/.*//" -e 's/:.*//' -e 's/^www\.//' \
        | sort -u >> "$SUBDOMAIN_TEMP" &

    # urlscan.io
    curl -s -N "https://urlscan.io/api/v1/search/?q=domain:$DOMAIN" \
        | jq '.results[].page.domain' 2>/dev/null \
        | grep -o "\w.*$DOMAIN" | sort -u >> "$SUBDOMAIN_TEMP" &

    # threatminer.org
    curl -s -N "https://api.threatminer.org/v2/domain.php?q=$DOMAIN&rt=5" \
        | jq -r '.results[]' 2>/dev/null \
        | grep -o "\w.*$DOMAIN" | sort -u >> "$SUBDOMAIN_TEMP" &

    # rapiddns.io
    curl -s "https://rapiddns.io/subdomain/$DOMAIN?full=1#result" \
        | grep -oaEi "https?://[^\"\\'> ]+" | grep "$DOMAIN" \
        | cut -d "/" -f3 | sort -u >> "$SUBDOMAIN_TEMP" &

    # jldc
    curl -s -N "https://jldc.me/anubis/subdomains/$DOMAIN" \
        | jq -r '.[]' 2>/dev/null \
        | grep -o "\w.*$DOMAIN" | sort -u >> "$SUBDOMAIN_TEMP" &

    # Wait for all background jobs before proceeding
    wait
    echo
    echo "[*] Level 1 Done!!"
}

# --- Level 2 & 3: Tool-based enumeration ---
subdomain_with_tools() {
    echo
    echo "[*] Starting Level 2 (Amass)"
    echo
    if check_tool "amass"; then
        amass enum -d "$DOMAIN" >> "$SUBDOMAIN_TEMP"
        echo "[*] Done Level 2"
    else
        echo "[!] Amass not found, skipping Level 2"
    fi

    echo
    echo "[*] Starting Level 3 (Sublist3r)"
    echo
    if check_tool "$SUBLIST3R_PATH"; then
        python3 "$SUBLIST3R_PATH" -d "$DOMAIN" -o "$SUBLIST3R_OUT"
        cat "$SUBLIST3R_OUT" >> "$SUBDOMAIN_TEMP"
        echo "[*] Done Level 3"
    else
        echo "[!] Sublist3r not found, skipping Level 3"
    fi

    echo
    echo "[*] SUBDOMAIN ENUMERATION DONE!!"
    echo
}

# --- Takeover check ---
checkTakeover() {
    echo "[*] CHECKING IF SUBDOMAINS ARE VULNERABLE TO TAKEOVER..."
    echo
    if check_tool "$SUBJACK_BIN"; then
        if [ ! -f "$SUBJACK_FINGERPRINTS" ]; then
            echo "[!] Subjack fingerprints file not found: $SUBJACK_FINGERPRINTS"
            echo "[!] Skipping takeover check."
            return
        fi
        "$SUBJACK_BIN" -a -v -w "$SUBDOMAIN_FINAL" -t 20 -timeout 15 \
            -c "$SUBJACK_FINGERPRINTS" -o "$TAKEOVER_OUT"
        echo
        echo "[*] DONE"
    else
        echo "[!] Subjack not found, skipping takeover check"
    fi
    echo
}

# --- Main ---
subdomain_without_tools
subdomain_with_tools

# Deduplicate
awk '!a[$0]++' "$SUBDOMAIN_TEMP" > "$SUBDOMAIN_FINAL"

TOTAL_SUBDOMAINS=$(wc -l < "$SUBDOMAIN_FINAL")
echo "[*] Total Subdomains Found: $TOTAL_SUBDOMAINS"

checkTakeover

# Cleanup temp files
[ -f "$SUBDOMAIN_TEMP" ] && rm "$SUBDOMAIN_TEMP"
[ -f "$SUBLIST3R_OUT" ] && rm "$SUBLIST3R_OUT"

# Output summary
echo "[*] Output Information:"
echo "[*] Subdomains : $SUBDOMAIN_FINAL"
echo "[*] Takeover   : $TAKEOVER_OUT"
echo
echo "[*] SCANNING DONE!!"
