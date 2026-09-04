#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
MODE=${1:-all}
if (($# > 1)) || [[ "${MODE}" != all && "${MODE}" != --failure-only ]]; then
  printf 'Usage: %s [--failure-only]\n' "$0" >&2
  exit 2
fi
TMP_DIR=$(mktemp -d /tmp/owtf-tools.XXXXXX)
mkdir -p "${ROOT_DIR}/build/test-evidence"
EVIDENCE_DIR=$(mktemp -d "${ROOT_DIR}/build/test-evidence/tools.XXXXXX")
TOOLS_IMAGE=${OWTF_TOOLS_IMAGE:-owtf/kali-tools:local}
PORT=${OWTF_TOOLS_PORT:-18129}
FIXTURE_HTTP_PORT=${OWTF_FIXTURE_HTTP_PORT:-18130}
FIXTURE_TLS_PORT=${OWTF_FIXTURE_TLS_PORT:-18131}
BASE_URL="http://127.0.0.1:${PORT}"
FIXTURE="owtf-tools-fixture-$$"
FIXTURE_IMAGE="owtf/tools-fixture:$$"
SERVER_PID=""
EXPECTED_FAILURES=2

cleanup() {
  if [[ -n "${SERVER_PID}" ]]; then
    kill "${SERVER_PID}" >/dev/null 2>&1 || true
    wait "${SERVER_PID}" >/dev/null 2>&1 || true
  fi
  [[ ! -f "${TMP_DIR}/server.log" ]] || cp "${TMP_DIR}/server.log" "${EVIDENCE_DIR}/server.log"
  docker logs "${FIXTURE}" >"${EVIDENCE_DIR}/requests.log" 2>&1 || true
  docker cp "${FIXTURE}:/var/log/vsftpd.log" "${EVIDENCE_DIR}/ftp.log" >/dev/null 2>&1 || true
  docker cp "${FIXTURE}:/var/log/nginx/vhosts.log" "${EVIDENCE_DIR}/vhosts.log" >/dev/null 2>&1 || true
  if [[ "${MODE}" == all ]]; then
    docker cp "${FIXTURE}:/var/log/smtp.log" "${EVIDENCE_DIR}/smtp.log" >/dev/null 2>&1 || true
    docker cp "${FIXTURE}:/var/log/samba" "${EVIDENCE_DIR}/samba-logs" >/dev/null 2>&1 || true
    docker cp "${FIXTURE}:/var/log/dns.log" "${EVIDENCE_DIR}/dns.log" >/dev/null 2>&1 || true
  fi
  docker rm --force "${FIXTURE}" >/dev/null 2>&1 || true
  docker image rm --force "${FIXTURE_IMAGE}" >/dev/null 2>&1 || true
  rm -rf "${TMP_DIR}"
}
trap cleanup EXIT INT TERM

fail() {
  printf 'FAIL: %s\n' "$*" >&2
  printf 'Evidence: %s\n' "${EVIDENCE_DIR}" >&2
  [[ ! -f "${TMP_DIR}/server.log" ]] || cat "${TMP_DIR}/server.log" >&2
  exit 1
}

request() {
  local method=$1
  local path=$2
  local body=${3-}
  if [[ -n "${body}" ]]; then
    curl --fail --silent --show-error --max-time 30 --request "${method}" \
      --header 'Content-Type: application/json' --data "${body}" "${BASE_URL}${path}"
  else
    curl --fail --silent --show-error --max-time 30 --request "${method}" "${BASE_URL}${path}"
  fi
}

wait_for_status() {
  local task_id=$1
  local expected=$2
  local status=""
  local attempt
  for attempt in $(seq 1 1500); do
    status=$(request GET "/api/v2/tasks/${task_id}" | jq -r '.status')
    if [[ "${status}" == "${expected}" ]]; then
      return 0
    fi
    case "${status}" in
      failed|blocked|cancelled|succeeded)
        request GET "/api/v2/tasks/${task_id}/events" >&2 || true
        fail "task ${task_id} reached ${status}, expected ${expected}"
        ;;
    esac
    sleep 0.2
  done
  fail "task ${task_id} remained ${status}, expected ${expected}"
}

launch() {
  local target_id=$1
  local plugin_id=$2
  local inputs='{}'
  if (($# >= 3)); then
    inputs=$3
  fi
  jq -nc --arg session "${SESSION_ID}" --arg target "${target_id}" \
    --arg plugin "${plugin_id}" --argjson inputs "${inputs}" \
    '{session_id:$session,target_ids:[$target],plugin_ids:[$plugin],plugin_inputs:{($plugin):$inputs}}' |
    curl --fail --silent --show-error --max-time 30 \
      --header 'Content-Type: application/json' --data @- "${BASE_URL}/api/v2/runs" |
    jq -r '.tasks[0].id'
}

assert_removed() {
  local task_id=$1
  local attempt containers volumes
  for attempt in $(seq 1 50); do
    containers=$(docker ps --all --quiet --filter "label=dev.owtf.task=${task_id}") || fail 'cannot inspect Docker containers'
    volumes=$(docker volume ls --quiet --filter "label=dev.owtf.task=${task_id}") || fail 'cannot inspect Docker volumes'
    if [[ -z "${containers}" && -z "${volumes}" ]]; then
      return 0
    fi
    sleep 0.1
  done
  fail "task ${task_id} left a plugin container or volume behind"
}

start_server() {
  TMPDIR="${TMP_DIR}/task-tmp" OWTF_TASK_TIMEOUT="$1" "${TMP_DIR}/owtf" serve --config "${TMP_DIR}/config.yaml" >>"${TMP_DIR}/server.log" 2>&1 &
  SERVER_PID=$!
  local attempt
  for attempt in $(seq 1 150); do
    if curl --silent --fail --max-time 1 "${BASE_URL}/api/v2/health" >/dev/null 2>&1; then
      return 0
    fi
    kill -0 "${SERVER_PID}" >/dev/null 2>&1 || fail 'OWTF stopped during startup'
    sleep 0.2
  done
  fail 'OWTF did not become healthy'
}

stop_server() {
  kill "${SERVER_PID}"
  wait "${SERVER_PID}"
  SERVER_PID=""
}

# Wait for both a target-side request and scanner output, not just dispatch.
wait_for_scan() {
  local task_id=$1
  local case_name=$2
  local attempt container_id status
  for attempt in $(seq 1 100); do
    request GET "/api/v2/tasks/${task_id}/events" >"${EVIDENCE_DIR}/${case_name}-events.json"
    docker logs "${FIXTURE}" >"${EVIDENCE_DIR}/requests.log" 2>&1 || fail 'cannot read fixture requests'
    container_id=$(docker ps --quiet --filter "label=dev.owtf.task=${task_id}" \
      --filter 'label=dev.owtf.plugin=OWTF-CM-006-active') || fail 'cannot inspect scanner container'
    if [[ -n "${container_id}" ]] &&
      grep -Fxq "GET /${case_name}/admin" "${EVIDENCE_DIR}/requests.log" &&
      jq -e 'any(.[]; .stream == "stdout" and (.message | contains("admin")))' "${EVIDENCE_DIR}/${case_name}-events.json" >/dev/null; then
      docker inspect "${container_id}" >"${EVIDENCE_DIR}/${case_name}-container.json"
      docker top "${container_id}" -eo pid,ppid,comm >"${EVIDENCE_DIR}/${case_name}-processes.txt"
      jq -e '.[0].State.Running and ([.[0].Mounts[] | select(.Type == "volume")] | length == 2)' \
        "${EVIDENCE_DIR}/${case_name}-container.json" >/dev/null || fail 'scanner input and artifact volumes are missing'
      printf '%s\n' "${container_id}"
      return 0
    fi
    status=$(request GET "/api/v2/tasks/${task_id}" | jq -r '.status')
    [[ "${status}" == queued || "${status}" == running ]] || fail "${case_name} reached ${status} before scanner activity"
    sleep 0.1
  done
  fail "${case_name} did not send a request and emit scanner output"
}

assert_terminal() {
  local task_id=$1
  local case_name=$2
  local expected=$3
  local error_text=$4
  local attempt run_id attempt_id
  wait_for_status "${task_id}" "${expected}"
  assert_removed "${task_id}"
  for attempt in $(seq 1 100); do
    if request GET /api/v2/workers | jq -e 'length == 1 and .[0].status == "idle" and (.[0].task_id // "") == ""' >/dev/null; then
      break
    fi
    sleep 0.1
  done
  request GET /api/v2/workers | jq -e 'length == 1 and .[0].status == "idle"' >/dev/null || fail 'worker did not return to idle'
  [[ -z "$(find "${TMP_DIR}/task-tmp" -mindepth 1 -print -quit)" ]] || fail 'task temporary files survived cleanup'
  request GET "/api/v2/tasks/${task_id}" >"${EVIDENCE_DIR}/${case_name}-task.json"
  jq -e --arg status "${expected}" --arg error "${error_text}" \
    '.status == $status and .started_at != null and .ended_at != null and (.error | contains($error))' \
    "${EVIDENCE_DIR}/${case_name}-task.json" >/dev/null || fail "${case_name} task status/error is incorrect"
  OWTF_URL="${BASE_URL}" "${TMP_DIR}/owtf" --json tasks attempts "${task_id}" >"${EVIDENCE_DIR}/${case_name}-attempts.json"
  jq -e --arg status "${expected}" --arg error "${error_text}" \
    'length == 1 and .[0].attempt_number == 1 and .[0].status == $status and .[0].ended_at != null and (.[0].error | contains($error))' \
    "${EVIDENCE_DIR}/${case_name}-attempts.json" >/dev/null || fail "${case_name} attempt is missing or was retried"
  attempt_id=$(jq -r '.[0].id' "${EVIDENCE_DIR}/${case_name}-attempts.json")
  OWTF_URL="${BASE_URL}" "${TMP_DIR}/owtf" --json tasks logs "${task_id}" >"${EVIDENCE_DIR}/${case_name}-events.json"
  jq -e --arg status "${expected}" --arg error "${error_text}" --arg attempt "${attempt_id}" \
    'all(.[]; .attempt_id == $attempt) and any(.[]; .stream == "stdout" and (.message | contains("admin"))) and
     any(.[]; if $status == "cancelled" then .message == "task cancelled" else .stream == "stderr" and (.message | contains($error)) end)' \
    "${EVIDENCE_DIR}/${case_name}-events.json" >/dev/null || fail "${case_name} scanner/terminal logs were not retained"
  run_id=$(jq -r '.run_id' "${EVIDENCE_DIR}/${case_name}-task.json")
  request GET "/api/v2/runs/${run_id}" | jq -e --arg status "${expected}" \
    '.status == $status and .finished_at != null' >/dev/null || fail "${case_name} run did not finish correctly"
}

for command in docker curl go jq openssl unzip; do
  command -v "${command}" >/dev/null || fail "${command} is required"
done
docker image inspect "${TOOLS_IMAGE}" >/dev/null 2>&1 || fail "tools image ${TOOLS_IMAGE} is unavailable"
for port in "${PORT}" "${FIXTURE_HTTP_PORT}" "${FIXTURE_TLS_PORT}"; do
  if curl --silent --max-time 1 "http://127.0.0.1:${port}" >/dev/null 2>&1; then
    fail "port ${port} is already in use"
  fi
done

mkdir -p "${TMP_DIR}/fixture/site/admin" "${TMP_DIR}/wordlists" "${TMP_DIR}/plugins" "${TMP_DIR}/task-tmp"
cp -R "${ROOT_DIR}/plugins/." "${TMP_DIR}/plugins/"
printf '<html><title>OWTF fixture</title><body>fixture</body></html>\n' >"${TMP_DIR}/fixture/site/index.html"
printf 'admin fixture\n' >"${TMP_DIR}/fixture/site/admin/index.html"
printf 'admin\nmissing\n' >"${TMP_DIR}/wordlists/smoke.txt"
printf 'admin\nmissing\n' >"${TMP_DIR}/wordlists/vhosts.txt"
printf 'www\napi\nmissing\n' >"${TMP_DIR}/wordlists/dns.txt"
printf '../outside\n' >"${TMP_DIR}/wordlists/dns-invalid.txt"
printf 'admin\n' >"${TMP_DIR}/wordlists/slow.txt"
seq 1 9999 | sed 's/^/missing-/' >>"${TMP_DIR}/wordlists/slow.txt"
for case_name in cancel crash timeout; do
  mkdir -p "${TMP_DIR}/fixture/site/${case_name}/admin"
  printf 'admin fixture\n' >"${TMP_DIR}/fixture/site/${case_name}/admin/index.html"
done
openssl req -x509 -newkey rsa:2048 -nodes -days 1 -subj '/CN=host.docker.internal' \
  -addext 'subjectAltName=DNS:host.docker.internal' \
  -keyout "${TMP_DIR}/fixture/fixture.key" -out "${TMP_DIR}/fixture/fixture.crt" >/dev/null 2>&1
cat >"${TMP_DIR}/fixture/nginx.conf" <<'NGINX'
events {}
http {
  log_format owtf '$request_method $uri';
  log_format hosts '$host $status';
  access_log /dev/stdout owtf;
  access_log /var/log/nginx/vhosts.log hosts;
  server {
    listen 80;
    server_name admin.host.docker.internal;
    return 200 'OWTF virtual host fixture\n';
  }
  server {
    listen 80 default_server;
    server_name _;
    root /site;
    location / { try_files $uri $uri/ =404; }
  }
  server {
    listen 443 ssl;
    server_name _;
    ssl_certificate /certs/fixture.crt;
    ssl_certificate_key /certs/fixture.key;
    root /site;
    location / { try_files $uri $uri/ =404; }
  }
}
NGINX
cat >"${TMP_DIR}/fixture/vsftpd.conf" <<'FTP'
listen=YES
listen_ipv6=NO
background=YES
anonymous_enable=YES
local_enable=NO
write_enable=NO
anon_root=/site
no_anon_password=YES
pasv_min_port=30000
pasv_max_port=30005
xferlog_enable=YES
log_ftp_protocol=YES
vsftpd_log_file=/var/log/vsftpd.log
FTP
cat >"${TMP_DIR}/fixture/postfix.cf" <<'SMTP'
myhostname = smtp.owtf.test
mydomain = owtf.test
myorigin = $mydomain
inet_interfaces = all
inet_protocols = ipv4
mynetworks = 127.0.0.0/8
mydestination =
relay_domains =
smtpd_banner = $myhostname ESMTP Postfix
smtpd_relay_restrictions = reject
smtpd_recipient_restrictions = reject
default_transport = error:mail delivery disabled in OWTF fixture
relay_transport = error:mail relay disabled in OWTF fixture
smtpd_sasl_auth_enable = no
smtpd_tls_security_level = none
disable_vrfy_command = yes
SMTP
cat >"${TMP_DIR}/fixture/smb.conf" <<'SMB'
[global]
server role = standalone server
workgroup = OWTF
netbios name = OWTFSMOKE
server string = OWTF Samba fixture
server min protocol = SMB2_02
server max protocol = SMB3_11
server signing = mandatory
smb ports = 445
disable netbios = yes
load printers = no
log level = 3
log file = /var/log/samba/log.smbd
max log size = 256
SMB
cat >"${TMP_DIR}/fixture/dnsmasq.conf" <<'DNS'
no-resolv
no-hosts
port=5353
user=root
local=/owtf.test/
host-record=www.dns.owtf.test,192.0.2.10,2001:db8::10
host-record=api.dns.owtf.test,192.0.2.11
address=/wild.owtf.test/192.0.2.200
log-queries
log-facility=/var/log/dns.log
DNS
cat >"${TMP_DIR}/fixture/Dockerfile" <<'DOCKERFILE'
FROM nginx:alpine
ARG NETWORK_PACKAGES
RUN apk add --no-cache vsftpd ${NETWORK_PACKAGES}
COPY nginx.conf /etc/nginx/nginx.conf
COPY vsftpd.conf /etc/vsftpd/vsftpd.conf
COPY postfix.cf /etc/postfix/main.cf
COPY smb.conf /etc/samba/smb.conf
COPY dnsmasq.conf /etc/dnsmasq.conf
COPY fixture.crt fixture.key /certs/
COPY site/ /site/
DOCKERFILE

NETWORK_PACKAGES=""
[[ "${MODE}" != all ]] || NETWORK_PACKAGES="postfix samba-server samba-common-tools dnsmasq"
docker build --quiet --build-arg "NETWORK_PACKAGES=${NETWORK_PACKAGES}" --tag "${FIXTURE_IMAGE}" "${TMP_DIR}/fixture" >/dev/null
docker run --detach --name "${FIXTURE}" \
  --publish "127.0.0.1:${FIXTURE_HTTP_PORT}:80" \
  --publish "127.0.0.1:${FIXTURE_TLS_PORT}:443" \
  "${FIXTURE_IMAGE}" >/dev/null
docker exec "${FIXTURE}" /usr/sbin/vsftpd /etc/vsftpd/vsftpd.conf
NETWORK_HOST=$(docker inspect --format '{{.NetworkSettings.IPAddress}}' "${FIXTURE}")
[[ -n "${NETWORK_HOST}" ]] || fail 'fixture has no bridge IP address'
if [[ "${MODE}" == all ]]; then
  docker exec "${FIXTURE}" syslogd -O /var/log/smtp.log
  docker exec "${FIXTURE}" postfix start
  docker exec "${FIXTURE}" testparm --suppress-prompt >"${EVIDENCE_DIR}/smb-required-config.txt" 2>&1 || fail 'SMB fixture configuration validation failed'
  docker exec "${FIXTURE}" smbd --daemon --no-process-group
  for attempt in $(seq 1 50); do
    if docker exec "${FIXTURE}" sh -c 'nc -z -w 1 127.0.0.1 25 && nc -z -w 1 127.0.0.1 445'; then
      break
    fi
    sleep 0.1
  done
  docker exec "${FIXTURE}" sh -c 'nc -z -w 1 127.0.0.1 25 && nc -z -w 1 127.0.0.1 445' || fail 'SMTP/SMB fixture did not become ready'
  docker exec "${FIXTURE}" postconf mail_version >"${EVIDENCE_DIR}/fixture-versions.txt"
  docker exec "${FIXTURE}" smbd --version >>"${EVIDENCE_DIR}/fixture-versions.txt"
  docker exec "${FIXTURE}" dnsmasq --test
  docker exec "${FIXTURE}" dnsmasq
  docker exec "${FIXTURE}" dnsmasq --version >>"${EVIDENCE_DIR}/fixture-versions.txt"
fi

cat >"${TMP_DIR}/config.yaml" <<YAML
apiVersion: owtf.dev/v1alpha1
kind: Config
server:
  address: 127.0.0.1:${PORT}
  dataDirectory: ${TMP_DIR}/data
  workers: 1
  taskTimeoutSeconds: 240
plugins:
  directory: ${TMP_DIR}/plugins
  profilesDirectory: ${ROOT_DIR}/profiles
  wordlistDirectory: ${TMP_DIR}/wordlists
  defaultProfile: default
  containerEngine: docker
proxy:
  listenAddress: 127.0.0.1:18228
  apiAddress: 127.0.0.1:18229
YAML

printf '%s\n' 'Building and starting OWTF...'
GOPATH="${OWTF_SMOKE_GOPATH:-/tmp/owtf-go}" \
GOMODCACHE="${OWTF_SMOKE_GOMODCACHE:-/tmp/owtf-go/pkg/mod}" \
GOCACHE="${TMP_DIR}/go-cache" GOMAXPROCS=2 \
  go build -trimpath -o "${TMP_DIR}/owtf" "${ROOT_DIR}/cmd/owtf"
start_server 240

printf '%s\n' 'Checking the Kali tool catalog...'
docker run --rm --entrypoint /bin/sh "${TOOLS_IMAGE}" -c '
  set -eu
  for command in testssl.sh wafw00f gobuster metagoofil whatweb nuclei wapiti nmap nikto; do
    command -v "$command" >/dev/null
  done
  metagoofil --help >/dev/null 2>&1
' >"${EVIDENCE_DIR}/tools.txt" || fail 'one or more retained tools are unavailable'
docker run --rm --entrypoint dpkg-query "${TOOLS_IMAGE}" -W nmap nikto gobuster >>"${EVIDENCE_DIR}/tools.txt"
PLUGINS=$(request GET /api/v2/plugins)
if ! jq -e '
  [.[] | select(
    .id == "OWTF-CM-001-active" or .id == "OWTF-CM-003-active" or
    .id == "OWTF-CM-006-active" or .id == "OWTF-IG-002-semi_passive" or
    .id == "OWTF-IG-004-active" or .id == "OWTF-IG-005-active" or
    .id == "OWTF-ST-001-active" or .id == "OWTF-CL-002-active" or
    .id == "OWTF-WVS-002-active" or .id == "OWTF-WVS-003-active" or
    .group == "network"
  ) | select(.availability == "ready")] | length == 19
' <<<"${PLUGINS}" >/dev/null; then
  jq '[.[] | select(.runtime_type == "container")] | map({id, availability, reason})' <<<"${PLUGINS}" >&2
  fail 'Kali-backed plugin availability is incorrect'
fi
OWTF_URL="${BASE_URL}" "${TMP_DIR}/owtf" --json plugin list | jq -e '
  any(.[]; .id == "OWTF-WVS-003-active" and .availability == "ready")
' >/dev/null || fail 'CLI plugin availability is incorrect'

SESSION_ID=$(request POST /api/v2/sessions '{"name":"Kali tool compatibility"}' | jq -r '.id')
HTTP_URL="http://host.docker.internal:${FIXTURE_HTTP_PORT}/"
TLS_URL="https://host.docker.internal:${FIXTURE_TLS_PORT}/"
TARGETS=$(jq -nc --arg http "${HTTP_URL}" --arg tls "${TLS_URL}" '{targets:[$http,$tls]}' |
  curl --fail --silent --show-error --header 'Content-Type: application/json' --data @- \
    "${BASE_URL}/api/v2/sessions/${SESSION_ID}/targets")
HTTP_TARGET=$(jq -r --arg value "${HTTP_URL}" '.created[] | select(.value == $value) | .id' <<<"${TARGETS}")
TLS_TARGET=$(jq -r --arg value "${TLS_URL}" '.created[] | select(.value == $value) | .id' <<<"${TARGETS}")
[[ -n "${HTTP_TARGET}" && -n "${TLS_TARGET}" ]] || fail 'fixture targets were not created'

if [[ "${MODE}" == all ]]; then
  NETWORK_TARGET=$(request POST "/api/v2/sessions/${SESSION_ID}/targets" \
    "$(jq -nc --arg host "${NETWORK_HOST}" '{targets:[$host]}')" | jq -r '.created[0].id')
  printf '%s\n' 'Running retained scanners through the container executor...'
  TASKS=()
  TASKS+=("$(launch "${TLS_TARGET}" OWTF-CM-001-active)")
  TASKS+=("$(launch "${HTTP_TARGET}" OWTF-CM-003-active '{"request_timeout_seconds":5}')")
  TASKS+=("$(launch "${HTTP_TARGET}" OWTF-CM-006-active '{"wordlist":"smoke.txt","threads":2,"delay":"0s","request_timeout":"5s"}')")
  TASKS+=("$(launch "${HTTP_TARGET}" OWTF-IG-004-active '{"aggression":"1","threads":1}')")
  TASKS+=("$(launch "${HTTP_TARGET}" OWTF-ST-001-active '{"rate_limit":1,"concurrency":1,"request_timeout_seconds":5}')")
  TASKS+=("$(launch "${HTTP_TARGET}" OWTF-WVS-003-active '{"scope":"folder","max_scan_time_seconds":15,"max_attack_time_seconds":5,"max_files_per_directory":10,"request_timeout_seconds":5}')")
  NMAP_TASK=$(launch "${NETWORK_TARGET}" PTES-001-active '{"port":21}')
  NMAP_CLOSED_TASK=$(launch "${NETWORK_TARGET}" PTES-001-active '{"port":65000}')
  SMTP_TASK=$(launch "${NETWORK_TARGET}" PTES-002-active)
  SMB_REQUIRED_TASK=$(launch "${NETWORK_TARGET}" PTES-009-active)
  SMTP_CLOSED_TASK=$(launch "${NETWORK_TARGET}" PTES-002-active '{"port":65000}')
  SMB_CLOSED_TASK=$(launch "${NETWORK_TARGET}" PTES-009-active '{"port":65000}')
  NIKTO_TASK=$(launch "${HTTP_TARGET}" OWTF-WVS-002-active '{"max_time_seconds":20,"request_timeout_seconds":5}')
  VHOST_TASK=$(launch "${HTTP_TARGET}" OWTF-IG-005-active '{"wordlist":"vhosts.txt","threads":1,"delay":"0s","request_timeout":"5s"}')
  TASKS+=("${NMAP_TASK}" "${NMAP_CLOSED_TASK}" "${SMTP_TASK}" "${SMB_REQUIRED_TASK}" "${SMTP_CLOSED_TASK}" "${SMB_CLOSED_TASK}" "${NIKTO_TASK}" "${VHOST_TASK}")
  request GET "/api/v2/tasks?session_id=${SESSION_ID}" >"${EVIDENCE_DIR}/worklist-during-scan.json"
  request GET /api/v2/workers >"${EVIDENCE_DIR}/worker-during-scan.json"
  wait_for_status "${SMB_REQUIRED_TASK}" succeeded
  docker exec "${FIXTURE}" sed -i 's/server signing = mandatory/server signing = auto/' /etc/samba/smb.conf
  docker exec "${FIXTURE}" smbcontrol all reload-config
  docker exec "${FIXTURE}" testparm --suppress-prompt >"${EVIDENCE_DIR}/smb-optional-config.txt" 2>&1
  SMB_OPTIONAL_TASK=$(launch "${NETWORK_TARGET}" PTES-009-active)
  TASKS+=("${SMB_OPTIONAL_TASK}")
  # Close 445 so custom-port success cannot be caused by an NSE fallback.
  wait_for_status "${SMB_OPTIONAL_TASK}" succeeded
  docker exec "${FIXTURE}" smbcontrol all shutdown
  docker exec "${FIXTURE}" sed -i -e 's/smb ports = 445/smb ports = 1445/' -e 's/server signing = auto/server signing = mandatory/' /etc/samba/smb.conf
  for attempt in $(seq 1 50); do
    if ! docker exec "${FIXTURE}" pgrep -x smbd >/dev/null; then break; fi
    sleep 0.1
  done
  docker exec "${FIXTURE}" smbd --daemon --no-process-group
  for attempt in $(seq 1 50); do
    if docker exec "${FIXTURE}" nc -z -w 1 127.0.0.1 1445; then break; fi
    sleep 0.1
  done
  docker exec "${FIXTURE}" nc -z -w 1 127.0.0.1 1445 || fail 'custom SMB port is not listening'
  if docker exec "${FIXTURE}" nc -z -w 1 127.0.0.1 445; then fail 'default SMB port must be closed'; fi
  docker exec "${FIXTURE}" testparm --suppress-prompt >"${EVIDENCE_DIR}/smb-custom-config.txt" 2>&1
  SMB_CUSTOM_TASK=$(launch "${NETWORK_TARGET}" PTES-009-active '{"port":1445}')
  DNS_TARGET=$(request POST "/api/v2/sessions/${SESSION_ID}/targets" '{"targets":["dns.owtf.test"]}' | jq -r '.created[0].id')
  DNS_EMPTY_TARGET=$(request POST "/api/v2/sessions/${SESSION_ID}/targets" '{"targets":["empty.owtf.test"]}' | jq -r '.created[0].id')
  DNS_WILD_TARGET=$(request POST "/api/v2/sessions/${SESSION_ID}/targets" '{"targets":["wild.owtf.test"]}' | jq -r '.created[0].id')
  DNS_INPUTS=$(jq -nc --arg resolver "${NETWORK_HOST}:5353" '{wordlist:"dns.txt",resolver:$resolver,threads:1,delay:"100ms",timeout:"1s"}')
  for inputs in '{"wordlist":"dns.txt","resolver":"resolver.test:53"}' '{"wordlist":"dns.txt","resolver":"192.0.2.53:0"}' \
    "$(jq '.threads=11' <<<"${DNS_INPUTS}")"; do
    status=$(jq -nc --arg session "${SESSION_ID}" --arg target "${DNS_TARGET}" --argjson inputs "${inputs}" \
      '{session_id:$session,target_ids:[$target],plugin_ids:["PTES-011-bruteforce"],plugin_inputs:{"PTES-011-bruteforce":$inputs}}' | \
      curl --silent --show-error --max-time 10 -o "${EVIDENCE_DIR}/dns-invalid-input.json" -w '%{http_code}' \
        --header 'Content-Type: application/json' --data @- "${BASE_URL}/api/v2/runs")
    [[ "${status}" == 400 ]] || fail 'invalid DNS launch inputs were accepted'
  done
  DNS_TASK=$(launch "${DNS_TARGET}" PTES-011-bruteforce "${DNS_INPUTS}")
  DNS_EMPTY_TASK=$(OWTF_URL="${BASE_URL}" "${TMP_DIR}/owtf" --json runs create --session "${SESSION_ID}" \
    --target "${DNS_EMPTY_TARGET}" --plugin PTES-011-bruteforce --input PTES-011-bruteforce.wordlist=dns.txt \
    --input "PTES-011-bruteforce.resolver=${NETWORK_HOST}:5353" --input PTES-011-bruteforce.threads=1 \
    --input PTES-011-bruteforce.delay=100ms --input PTES-011-bruteforce.timeout=1s | jq -r '.tasks[0].id')
  TASKS+=("${SMB_CUSTOM_TASK}" "${DNS_TASK}" "${DNS_EMPTY_TASK}")
  mkdir -p "${EVIDENCE_DIR}/artifacts"
  for task_id in "${TASKS[@]}"; do
    wait_for_status "${task_id}" succeeded
    assert_removed "${task_id}"
    request GET "/api/v2/tasks/${task_id}/events" >"${EVIDENCE_DIR}/${task_id}-events.json"
    jq -e \
      'any(.[]; .stream == "system" and (.message | startswith("container owtf/kali-tools:local")))' \
      "${EVIDENCE_DIR}/${task_id}-events.json" >/dev/null || fail "task ${task_id} is missing its container command log"
    OWTF_URL="${BASE_URL}" "${TMP_DIR}/owtf" --json tasks attempts "${task_id}" >"${EVIDENCE_DIR}/${task_id}-attempts.json"
    jq -e 'length == 1 and .[0].status == "succeeded" and .[0].attempt_number == 1' \
      "${EVIDENCE_DIR}/${task_id}-attempts.json" >/dev/null || fail "task ${task_id} did not finish in one attempt"
  done

  DNS_WILD_TASK=$(launch "${DNS_WILD_TARGET}" PTES-011-bruteforce "${DNS_INPUTS}")
  DNS_INVALID_TASK=$(launch "${DNS_TARGET}" PTES-011-bruteforce "$(jq '.wordlist = "dns-invalid.txt"' <<<"${DNS_INPUTS}")")
  DNS_UNAVAILABLE_TASK=$(launch "${DNS_TARGET}" PTES-011-bruteforce "$(jq '.resolver = "127.0.0.1:65000"' <<<"${DNS_INPUTS}")")
  for task_id in "${DNS_WILD_TASK}" "${DNS_INVALID_TASK}" "${DNS_UNAVAILABLE_TASK}"; do
    wait_for_status "${task_id}" failed
    assert_removed "${task_id}"
    request GET "/api/v2/tasks/${task_id}/events" >"${EVIDENCE_DIR}/${task_id}-events.json"
    request GET "/api/v2/tasks/${task_id}/attempts" | jq -e 'length == 1 and .[0].status == "failed"' >/dev/null || fail 'DNS failure was retried'
  done
  jq -e 'any(.[]; (.message | contains("same IP for every domain")))' "${EVIDENCE_DIR}/${DNS_WILD_TASK}-events.json" >/dev/null || fail 'wildcard DNS diagnostic missing'
  jq -e 'all(.[]; (.message | startswith("container owtf/kali-tools:local")) | not)' "${EVIDENCE_DIR}/${DNS_INVALID_TASK}-events.json" >/dev/null || fail 'invalid DNS labels reached the container'
  jq -e 'any(.[]; (.message | startswith("[ERROR]")))' "${EVIDENCE_DIR}/${DNS_UNAVAILABLE_TASK}-events.json" >/dev/null || fail 'resolver errors were hidden'
  EXPECTED_FAILURES=5

  HTTP_REPORT=$(request GET "/api/v2/targets/${HTTP_TARGET}/report")
  TLS_REPORT=$(request GET "/api/v2/targets/${TLS_TARGET}/report")
  request GET "/api/v2/targets/${NETWORK_TARGET}/report" >"${EVIDENCE_DIR}/network-report.json"
  request GET "/api/v2/targets/${DNS_TARGET}/report" >"${EVIDENCE_DIR}/dns-report.json"
  request GET "/api/v2/targets/${DNS_EMPTY_TARGET}/report" >"${EVIDENCE_DIR}/dns-empty-report.json"
  request GET "/api/v2/targets/${DNS_WILD_TARGET}/report" >"${EVIDENCE_DIR}/dns-wild-report.json"
  jq -e --arg task "${DNS_UNAVAILABLE_TASK}" 'any(.tasks[]; .id == $task and .status == "failed" and (.error | contains("output reported errors"))) and
    all(.observations[]; .task_id != $task) and any(.artifacts[]; .task_id == $task and .name == "dns.txt")' \
    "${EVIDENCE_DIR}/dns-report.json" >/dev/null || fail 'resolver failure was treated as empty discovery or lost its raw report'
  for name in dns-empty dns-wild; do
    jq -e '(.findings | length) == 0 and (.urls | length) == 0 and all(.observations[]; .kind != "dns.name")' \
      "${EVIDENCE_DIR}/${name}-report.json" >/dev/null || fail 'DNS empty/wildcard results fabricated discoveries'
  done
  docker cp "${FIXTURE}:/var/log/dns.log" "${EVIDENCE_DIR}/dns.log" >/dev/null
  for name in www.dns.owtf.test api.dns.owtf.test missing.dns.owtf.test; do
    grep -Fq "${name}" "${EVIDENCE_DIR}/dns.log" || fail "DNS server saw no query for ${name}"
  done
  if grep -Eq '(www|api|missing)\.wild\.owtf\.test' "${EVIDENCE_DIR}/dns.log"; then fail 'wildcard detection did not stop dictionary queries'; fi
  printf '%s\n' "${HTTP_REPORT}" >"${EVIDENCE_DIR}/http-report.json"
  printf '%s\n' "${TLS_REPORT}" >"${EVIDENCE_DIR}/tls-report.json"
  jq -r '.artifacts[] | [.id,.task_id,.name] | @tsv' \
    "${EVIDENCE_DIR}/http-report.json" "${EVIDENCE_DIR}/network-report.json" "${EVIDENCE_DIR}/tls-report.json" \
    "${EVIDENCE_DIR}/dns-report.json" "${EVIDENCE_DIR}/dns-empty-report.json" >"${EVIDENCE_DIR}/artifacts.tsv"
  while IFS=$'\t' read -r artifact_id task_id name; do
    request GET "/api/v2/artifacts/${artifact_id}" >"${EVIDENCE_DIR}/artifacts/${task_id}-${name}"
  done <"${EVIDENCE_DIR}/artifacts.tsv"
  NMAP_XML="${EVIDENCE_DIR}/artifacts/${NMAP_TASK}-nmap.xml"
  NMAP_CLOSED_XML="${EVIDENCE_DIR}/artifacts/${NMAP_CLOSED_TASK}-nmap.xml"
  NIKTO_XML="${EVIDENCE_DIR}/artifacts/${NIKTO_TASK}-nikto.xml"
  grep -q 'portid="21"' "${NMAP_XML}" && grep -q 'state="open"' "${NMAP_XML}" &&
    grep -q 'name="ftp"' "${NMAP_XML}" && grep -q 'Anonymous FTP login allowed' "${NMAP_XML}" || fail 'Nmap did not identify the FTP service and anonymous access'
  grep -q 'state="closed"' "${NMAP_CLOSED_XML}" || fail 'Nmap did not distinguish the closed port'
  grep -q 'PIPELINING' "${EVIDENCE_DIR}/artifacts/${SMTP_TASK}-nmap.xml" || fail 'raw SMTP capabilities are missing'
  grep -q 'Message signing enabled and required' "${EVIDENCE_DIR}/artifacts/${SMB_REQUIRED_TASK}-nmap.xml" || fail 'raw SMB required-signing evidence is missing'
  grep -q 'Message signing enabled but not required' "${EVIDENCE_DIR}/artifacts/${SMB_OPTIONAL_TASK}-nmap.xml" || fail 'raw SMB optional-signing evidence is missing'
  for task_id in "${SMTP_TASK}" "${SMB_REQUIRED_TASK}" "${SMB_OPTIONAL_TASK}"; do
    jq -e 'any(.[]; .stream == "stdout" and (.message | test("smtp-commands|smb2-security-mode")))' \
      "${EVIDENCE_DIR}/${task_id}-events.json" >/dev/null || fail "task ${task_id} did not retain actual scanner output"
  done
  docker cp "${FIXTURE}:/var/log/smtp.log" "${EVIDENCE_DIR}/smtp.log" >/dev/null
  grep -q 'postfix/smtpd.*ehlo=' "${EVIDENCE_DIR}/smtp.log" || fail 'SMTP server did not log an EHLO session'
  docker exec "${FIXTURE}" postqueue -p >"${EVIDENCE_DIR}/smtp-queue.txt"
  grep -q 'Mail queue is empty' "${EVIDENCE_DIR}/smtp-queue.txt" || fail 'SMTP fixture accepted queued mail'
  docker cp "${FIXTURE}:/var/log/samba/log.smbd" "${EVIDENCE_DIR}/smb.log" >/dev/null
  grep -q 'Selected protocol SMB' "${EVIDENCE_DIR}/smb.log" || fail 'SMB server did not log protocol negotiation'
  grep -q '<niktoscan' "${NIKTO_XML}" && grep -q '<item ' "${NIKTO_XML}" &&
    grep -qi 'x-content-type-options' "${NIKTO_XML}" || fail 'Nikto XML did not retain the fixture header finding'
  if ! jq -e --arg vhost "http://admin.host.docker.internal:${FIXTURE_HTTP_PORT}/" '([.tasks[] | select(.status == "succeeded")] | length) == 7 and
    any(.artifacts[]; .name == "wafw00f.json") and
    any(.artifacts[]; .name == "gobuster.txt") and
    any(.artifacts[]; .name == "whatweb.json") and
    any(.artifacts[]; .name == "wapiti.json") and
    any(.artifacts[]; .name == "nikto.xml") and
    any(.artifacts[]; .name == "vhosts.txt") and
    any(.observations[]; .kind == "waf.fingerprint") and
    any(.observations[]; .kind == "web.fingerprint") and
    any(.observations[]; .kind == "host.discovery" and (.data | fromjson | .urls == 1)) and
    any(.observations[]; .kind == "container.completed") and
    any(.urls[]; (.url | contains("/admin"))) and
    any(.urls[]; .url == $vhost and .visited)' <<<"${HTTP_REPORT}" >/dev/null; then
    jq '{tasks: [.tasks[] | {plugin_id, status}], artifacts: [.artifacts[].name], observations: [.observations[].kind], urls: [.urls[].url], findings: [.findings[].title]}' <<<"${HTTP_REPORT}" >&2
    fail 'HTTP scanner evidence is incomplete'
  fi
  if ! jq -e '([.tasks[] | select(.status == "succeeded")] | length) == 1 and
    any(.artifacts[]; .name == "testssl.json") and
    any(.observations[]; .kind == "container.completed") and
    (.findings | length) > 0' <<<"${TLS_REPORT}" >/dev/null; then
    jq '{tasks: [.tasks[] | {plugin_id, status}], artifacts: [.artifacts[].name], observations: [.observations[].kind], findings: [.findings[].title]}' <<<"${TLS_REPORT}" >&2
    fail 'TLS scanner evidence is incomplete'
  fi

  assert_nmap_results() {
    jq -e --arg open "${NMAP_TASK}" --arg closed "${NMAP_CLOSED_TASK}" '
      any(.observations[]; .task_id == $open and .kind == "network.port" and
        (.data | fromjson | .port == 21 and .state == "open" and .protocol == "tcp" and
          .service.name == "ftp" and .service.product == "vsftpd" and (.service.version | length) > 0)) and
      any(.observations[]; .task_id == $open and .kind == "network.script" and
        (.data | fromjson | .id == "ftp-anon" and (.output | contains("Anonymous FTP login allowed")))) and
      any(.observations[]; .task_id == $closed and .kind == "network.port" and
        (.data | fromjson | .port == 65000 and .state == "closed")) and
      all(.findings[]; .task_id != $open and .task_id != $closed)
    ' "$1" >/dev/null || fail "structured Nmap evidence is incomplete in $1"
  }
  assert_nikto_results() {
    jq -e --arg task "${NIKTO_TASK}" --arg url "${HTTP_URL}" '
      [.findings[] | select(.task_id == $task)] as $findings |
      ($findings | length) > 0 and
      all($findings[]; .severity == "unranked" and .technique_code == "OWTF-WVS-002") and
      any($findings[]; (.description | ascii_downcase | contains("x-content-type-options")) and
        (.description | contains("URL: " + $url))) and
      any(.urls[]; .url == $url and .visited) and
      any(.artifacts[]; .name == "nikto.xml" and .task_id == $task)
    ' "$1" >/dev/null || fail "structured Nikto findings are incomplete in $1"
  }
  assert_network_results() {
    jq -e --arg smtp "${SMTP_TASK}" --arg required "${SMB_REQUIRED_TASK}" --arg optional "${SMB_OPTIONAL_TASK}" \
      --arg smtp_closed "${SMTP_CLOSED_TASK}" --arg smb_closed "${SMB_CLOSED_TASK}" --arg custom "${SMB_CUSTOM_TASK}" '
      def records($task; $kind): [.observations[] | select(.task_id == $task and .kind == $kind) | .data | fromjson];
      def signing($task; $message): any(records($task; "network.script")[];
        .id == "smb2-security-mode" and (.output | contains($message)));
      def closed($task): any(records($task; "network.port")[]; .port == 65000 and .state == "closed") and
        (records($task; "network.script") | length) == 0;
      any(records($smtp; "network.port")[]; .port == 25 and .state == "open" and .service.name == "smtp") and
      any(records($smtp; "network.script")[]; .id == "smtp-commands" and
        (.output | contains("smtp.owtf.test") and contains("PIPELINING") and contains("SIZE"))) and
      any(records($required; "network.port")[]; .port == 445 and .state == "open") and
      any(records($required; "network.script")[]; .id == "smb-protocols" and
        (.output | contains("2.0.2") and contains("3.1.1") and (contains("SMBv1") | not))) and
      any(records($required; "network.script")[]; .id == "smb2-capabilities" and (.output | contains("Multi-credit operations"))) and
      signing($required; "Message signing enabled and required") and
      signing($optional; "Message signing enabled but not required") and
      any(records($custom; "network.port")[]; .port == 1445 and .state == "open") and
      signing($custom; "Message signing enabled and required") and
      any(records($custom; "network.script")[]; .id == "smb-protocols" and (.output | contains("3.1.1"))) and
      closed($smtp_closed) and closed($smb_closed) and
      all(.findings[]; .task_id != $smtp and .task_id != $required and .task_id != $optional and
        .task_id != $smtp_closed and .task_id != $smb_closed)
    ' "$1" >/dev/null || fail "SMTP/SMB observations are incomplete in $1"
  }
  assert_dns_results() {
    jq -e --arg task "${DNS_TASK}" '
      [.observations[] | select(.task_id == $task and .kind == "dns.name") | .data | fromjson] as $names |
      ($names | length) == 2 and
      any($names[]; .hostname == "www.dns.owtf.test" and .addresses == ["192.0.2.10","2001:db8::10"]) and
      any($names[]; .hostname == "api.dns.owtf.test" and .addresses == ["192.0.2.11"]) and
      all(.findings[]; .task_id != $task) and any(.artifacts[]; .task_id == $task and .name == "dns.txt")
    ' "$1" >/dev/null || fail "DNS discoveries missing in $1"
  }
  assert_dns_results "${EVIDENCE_DIR}/dns-report.json"
  jq -e '(.urls | length) == 0' "${EVIDENCE_DIR}/dns-report.json" >/dev/null || fail 'DNS answers became URLs'
  request GET "/api/v2/sessions/${SESSION_ID}/targets" >"${EVIDENCE_DIR}/targets-after-dns.json"
  jq -e 'all(.[]; .value != "www.dns.owtf.test" and .value != "api.dns.owtf.test")' \
    "${EVIDENCE_DIR}/targets-after-dns.json" >/dev/null || fail 'DNS expanded scan targets automatically'
  OWTF_URL="${BASE_URL}" "${TMP_DIR}/owtf" --json targets report "${DNS_TARGET}" >"${EVIDENCE_DIR}/dns-cli-report.json"
  assert_dns_results "${EVIDENCE_DIR}/dns-cli-report.json"
  assert_nmap_results "${EVIDENCE_DIR}/network-report.json"
  assert_network_results "${EVIDENCE_DIR}/network-report.json"
  assert_nikto_results "${EVIDENCE_DIR}/http-report.json"
  OWTF_URL="${BASE_URL}" "${TMP_DIR}/owtf" --json targets report "${HTTP_TARGET}" >"${EVIDENCE_DIR}/http-cli-report.json"
  OWTF_URL="${BASE_URL}" "${TMP_DIR}/owtf" --json targets report "${NETWORK_TARGET}" >"${EVIDENCE_DIR}/network-cli-report.json"
  assert_nmap_results "${EVIDENCE_DIR}/network-cli-report.json"
  assert_network_results "${EVIDENCE_DIR}/network-cli-report.json"
  assert_nikto_results "${EVIDENCE_DIR}/http-cli-report.json"
  request GET /api/v2/metrics | jq -e '
    .tasks.total == 21 and .tasks.succeeded == 18 and .attempts.succeeded == 18 and .tasks.failed == 3 and
    .workers.total == 1 and .workers.idle == 1 and .outputs.artifacts >= 5 and
    .outputs.observations > 0 and .outputs.findings > 0
  ' >/dev/null || fail 'tool execution metrics are incorrect'
  request GET "/api/v2/sessions/${SESSION_ID}/export" >"${EVIDENCE_DIR}/report.zip"
  unzip -tqq "${EVIDENCE_DIR}/report.zip" || fail 'offline report ZIP is invalid'
  unzip -p "${EVIDENCE_DIR}/report.zip" report.json | jq -e \
    '.summary.succeeded == 18 and any(.artifacts[]; .name == "nmap.xml") and any(.artifacts[]; .name == "nikto.xml") and any(.artifacts[]; .name == "vhosts.txt")' \
    >/dev/null || fail 'offline report is missing scanner evidence'
  unzip -p "${EVIDENCE_DIR}/report.zip" report.json >"${EVIDENCE_DIR}/export-report.json"
  assert_nmap_results "${EVIDENCE_DIR}/export-report.json"
  assert_dns_results "${EVIDENCE_DIR}/export-report.json"
  assert_network_results "${EVIDENCE_DIR}/export-report.json"
  assert_nikto_results "${EVIDENCE_DIR}/export-report.json"
  unzip -p "${EVIDENCE_DIR}/report.zip" index.html >"${EVIDENCE_DIR}/report.html"
  for text in network.port network.script vsftpd 'Anonymous FTP login allowed' 'Nikto:' x-content-type-options unranked \
    smtp-commands PIPELINING smb-protocols smb2-capabilities 'Message signing enabled and required' 'Message signing enabled but not required' \
    dns.name www.dns.owtf.test 2001:db8::10; do
    grep -Fq "${text}" "${EVIDENCE_DIR}/report.html" || fail "offline HTML is missing ${text}"
  done
  unzip -p "${EVIDENCE_DIR}/report.zip" manifest.json >"${EVIDENCE_DIR}/export-manifest.json"
  while IFS=$'\t' read -r artifact_id task_id name; do
    archive_path=$(jq -r --arg id "${artifact_id}" '.artifact_files[$id]' "${EVIDENCE_DIR}/export-manifest.json")
    grep -Fq "href=\"${archive_path}\"" "${EVIDENCE_DIR}/report.html" || fail "offline HTML has no link to ${name}"
    unzip -p "${EVIDENCE_DIR}/report.zip" "${archive_path}" | cmp - "${EVIDENCE_DIR}/artifacts/${task_id}-${name}" \
      || fail "offline report changed artifact ${name}"
  done <"${EVIDENCE_DIR}/artifacts.tsv"
  printf '%s\n' 'PASS: Nmap/Nikto structured results in API, CLI, and offline JSON/HTML; raw artifacts match byte for byte.'
  printf '%s\n' 'PASS: SMTP capabilities, SMB2/SMB3 dialects and both signing modes, closed ports, server logs, and one attempt per scan.'
  printf '%s\n' 'PASS: custom SMB port with 445 closed; DNS A/AAAA discovery, NXDOMAIN, wildcard refusal, resolver failures, invalid wordlists, and no automatic targets.'
fi

printf '%s\n' 'Checking cancellation, crash, and timeout after real scanner activity...'
stop_server
start_server 15
for case_name in cancel crash timeout; do
  target_id=$(request POST "/api/v2/sessions/${SESSION_ID}/targets" \
    "$(jq -nc --arg url "${HTTP_URL}${case_name}/" '{targets:[$url]}')" | jq -r '.created[0].id')
  task_id=$(launch "${target_id}" OWTF-CM-006-active \
    '{"wordlist":"slow.txt","threads":1,"delay":"1s","request_timeout":"5s"}')
  container_id=$(wait_for_scan "${task_id}" "${case_name}")
  case "${case_name}" in
    cancel)
      request POST "/api/v2/tasks/${task_id}/cancel" '{}' >/dev/null
      expected=cancelled
      error_text='cancelled by operator'
      ;;
    crash)
      docker exec "${container_id}" pkill -KILL -x gobuster
      expected=failed
      error_text='exit status 137'
      ;;
    timeout)
      expected=failed
      error_text='context deadline exceeded'
      ;;
  esac
  assert_terminal "${task_id}" "${case_name}" "${expected}" "${error_text}"
  printf 'PASS: %s after target request and scanner output; status=%s, attempts=1, containers=0, volumes=0\n' "${case_name}" "${expected}"
done

# Terminal work must stay terminal when the queue is restored on restart.
stop_server
start_server 15
for case_name in cancel crash timeout; do
  task_id=$(jq -r '.id' "${EVIDENCE_DIR}/${case_name}-task.json")
  expected=$(jq -r '.status' "${EVIDENCE_DIR}/${case_name}-task.json")
  error_text=$(jq -r '.error' "${EVIDENCE_DIR}/${case_name}-task.json")
  assert_terminal "${task_id}" "${case_name}" "${expected}" "${error_text}"
done
request GET /api/v2/metrics >"${EVIDENCE_DIR}/metrics.json"
jq -e --argjson failed "${EXPECTED_FAILURES}" '.tasks.failed == $failed and .tasks.cancelled == 1 and .tasks.running == 0 and .tasks.queued == 0 and
  .attempts.total == .tasks.total and .attempts.failed == $failed and .attempts.cancelled == 1 and
  .workers.total == 1 and .workers.idle == 1 and .workers.completed == 0' \
  "${EVIDENCE_DIR}/metrics.json" >/dev/null || fail 'failure metrics or restart state are incorrect'
request GET "/api/v2/sessions/${SESSION_ID}/report" >"${EVIDENCE_DIR}/report.json"
jq -e --argjson failed "${EXPECTED_FAILURES}" '.summary.failed == $failed and .summary.cancelled == 1 and .summary.attempts == .summary.tasks' \
  "${EVIDENCE_DIR}/report.json" >/dev/null || fail 'failure report is incomplete'

if [[ "${MODE}" == all ]]; then
  printf '%s\n' 'Kali compatibility passed for testssl.sh, WAFW00F, Gobuster dir/vhost, WhatWeb, Nuclei, Wapiti, Nmap FTP/SMTP/SMB/closed ports, and Nikto.'
  printf '%s\n' 'Metagoofil startup passed; it has no deterministic local search-provider mode.'
fi
printf 'PASS: terminal states and single attempts survived restart. Evidence: %s\n' "${EVIDENCE_DIR}"
