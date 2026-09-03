#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
TMP_DIR=$(mktemp -d /tmp/owtf-tools.XXXXXX)
TOOLS_IMAGE=${OWTF_TOOLS_IMAGE:-owtf/kali-tools:local}
PORT=${OWTF_TOOLS_PORT:-18129}
FIXTURE_HTTP_PORT=${OWTF_FIXTURE_HTTP_PORT:-18130}
FIXTURE_TLS_PORT=${OWTF_FIXTURE_TLS_PORT:-18131}
BASE_URL="http://127.0.0.1:${PORT}"
FIXTURE="owtf-tools-fixture-$$"
FIXTURE_IMAGE="owtf/tools-fixture:$$"
SERVER_PID=""

cleanup() {
  if [[ -n "${SERVER_PID}" ]]; then
    kill "${SERVER_PID}" >/dev/null 2>&1 || true
    wait "${SERVER_PID}" >/dev/null 2>&1 || true
  fi
  docker rm --force "${FIXTURE}" >/dev/null 2>&1 || true
  docker image rm --force "${FIXTURE_IMAGE}" >/dev/null 2>&1 || true
  rm -rf "${TMP_DIR}"
}
trap cleanup EXIT INT TERM

fail() {
  printf 'FAIL: %s\n' "$*" >&2
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
  local attempt
  for attempt in $(seq 1 50); do
    if [[ -z "$(docker ps --all --quiet --filter "label=dev.owtf.task=${task_id}")" ]] &&
      [[ -z "$(docker volume ls --quiet --filter "label=dev.owtf.task=${task_id}")" ]]; then
      return 0
    fi
    sleep 0.1
  done
  fail "task ${task_id} left a plugin container or volume behind"
}

for command in docker curl go jq openssl; do
  command -v "${command}" >/dev/null || fail "${command} is required"
done
docker image inspect "${TOOLS_IMAGE}" >/dev/null 2>&1 || fail "tools image ${TOOLS_IMAGE} is unavailable"
for port in "${PORT}" "${FIXTURE_HTTP_PORT}" "${FIXTURE_TLS_PORT}"; do
  if curl --silent --max-time 1 "http://127.0.0.1:${port}" >/dev/null 2>&1; then
    fail "port ${port} is already in use"
  fi
done

mkdir -p "${TMP_DIR}/fixture/site/admin" "${TMP_DIR}/wordlists" "${TMP_DIR}/plugins"
cp -R "${ROOT_DIR}/plugins/." "${TMP_DIR}/plugins/"
printf '<html><title>OWTF fixture</title><body>fixture</body></html>\n' >"${TMP_DIR}/fixture/site/index.html"
printf 'admin fixture\n' >"${TMP_DIR}/fixture/site/admin/index.html"
printf 'admin\nmissing\n' >"${TMP_DIR}/wordlists/smoke.txt"
seq 1 10000 | sed 's/^/missing-/' >"${TMP_DIR}/wordlists/slow.txt"
openssl req -x509 -newkey rsa:2048 -nodes -days 1 -subj '/CN=host.docker.internal' \
  -addext 'subjectAltName=DNS:host.docker.internal' \
  -keyout "${TMP_DIR}/fixture/fixture.key" -out "${TMP_DIR}/fixture/fixture.crt" >/dev/null 2>&1
cat >"${TMP_DIR}/fixture/nginx.conf" <<'NGINX'
events {}
http {
  access_log off;
  server {
    listen 80;
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
cat >"${TMP_DIR}/fixture/Dockerfile" <<'DOCKERFILE'
FROM nginx:alpine
COPY nginx.conf /etc/nginx/nginx.conf
COPY fixture.crt fixture.key /certs/
COPY site/ /site/
DOCKERFILE

docker build --quiet --tag "${FIXTURE_IMAGE}" "${TMP_DIR}/fixture" >/dev/null
docker run --detach --name "${FIXTURE}" \
  --publish "127.0.0.1:${FIXTURE_HTTP_PORT}:80" \
  --publish "127.0.0.1:${FIXTURE_TLS_PORT}:443" \
  "${FIXTURE_IMAGE}" >/dev/null

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
"${TMP_DIR}/owtf" serve --config "${TMP_DIR}/config.yaml" >"${TMP_DIR}/server.log" 2>&1 &
SERVER_PID=$!

for attempt in $(seq 1 150); do
  if curl --silent --fail --max-time 1 "${BASE_URL}/api/v2/health" >/dev/null 2>&1; then
    break
  fi
  kill -0 "${SERVER_PID}" >/dev/null 2>&1 || fail 'OWTF stopped during startup'
  sleep 0.2
done
request GET /api/v2/health | jq -e '.status == "ok"' >/dev/null || fail 'OWTF did not become healthy'

printf '%s\n' 'Checking the Kali tool catalog...'
docker run --rm --entrypoint /bin/sh "${TOOLS_IMAGE}" -c '
  set -eu
  for command in testssl.sh wafw00f gobuster metagoofil whatweb nuclei wapiti; do
    command -v "$command" >/dev/null
  done
  metagoofil --help >/dev/null 2>&1
' || fail 'one or more retained tools are unavailable'
PLUGINS=$(request GET /api/v2/plugins)
if ! jq -e '
  [.[] | select(
    .id == "OWTF-CM-001-active" or .id == "OWTF-CM-003-active" or
    .id == "OWTF-CM-006-active" or .id == "OWTF-IG-002-semi_passive" or
    .id == "OWTF-IG-004-active" or .id == "OWTF-IG-005-active" or
    .id == "OWTF-ST-001-active" or .id == "OWTF-CL-002-active" or
    .id == "OWTF-WVS-003-active"
  ) | select(.availability == "ready")] | length == 9
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

printf '%s\n' 'Running retained scanners through the container executor...'
TASKS=()
TASKS+=("$(launch "${TLS_TARGET}" OWTF-CM-001-active)")
TASKS+=("$(launch "${HTTP_TARGET}" OWTF-CM-003-active '{"request_timeout_seconds":5}')")
TASKS+=("$(launch "${HTTP_TARGET}" OWTF-CM-006-active '{"wordlist":"smoke.txt","threads":2,"delay":"0s","request_timeout":"5s"}')")
TASKS+=("$(launch "${HTTP_TARGET}" OWTF-IG-004-active '{"aggression":"1","threads":1}')")
TASKS+=("$(launch "${HTTP_TARGET}" OWTF-ST-001-active '{"rate_limit":1,"concurrency":1,"request_timeout_seconds":5}')")
TASKS+=("$(launch "${HTTP_TARGET}" OWTF-WVS-003-active '{"scope":"folder","max_scan_time_seconds":15,"max_attack_time_seconds":5,"max_files_per_directory":10,"request_timeout_seconds":5}')")
for task_id in "${TASKS[@]}"; do
  wait_for_status "${task_id}" succeeded
  assert_removed "${task_id}"
  request GET "/api/v2/tasks/${task_id}/events" | jq -e \
    'any(.[]; .stream == "system" and (.message | startswith("container owtf/kali-tools:local")))' \
    >/dev/null || fail "task ${task_id} is missing its container command log"
done

HTTP_REPORT=$(request GET "/api/v2/targets/${HTTP_TARGET}/report")
TLS_REPORT=$(request GET "/api/v2/targets/${TLS_TARGET}/report")
if ! jq -e '([.tasks[] | select(.status == "succeeded")] | length) == 5 and
  any(.artifacts[]; .name == "wafw00f.json") and
  any(.artifacts[]; .name == "gobuster.txt") and
  any(.artifacts[]; .name == "whatweb.json") and
  any(.artifacts[]; .name == "wapiti.json") and
  any(.observations[]; .kind == "waf.fingerprint") and
  any(.observations[]; .kind == "web.fingerprint") and
  any(.observations[]; .kind == "container.completed") and
  any(.urls[]; (.url | contains("/admin")))' <<<"${HTTP_REPORT}" >/dev/null; then
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

OWTF_URL="${BASE_URL}" "${TMP_DIR}/owtf" --json targets report "${HTTP_TARGET}" |
  jq -e 'any(.artifacts[]; .name == "wapiti.json")' >/dev/null || fail 'CLI target report is incomplete'
request GET /api/v2/metrics | jq -e '
  .tasks.total == 6 and .tasks.succeeded == 6 and .attempts.succeeded == 6 and
  .workers.total == 1 and .workers.idle == 1 and .outputs.artifacts >= 5 and
  .outputs.observations > 0 and .outputs.findings > 0
' >/dev/null || fail 'tool execution metrics are incorrect'

printf '%s\n' 'Checking cancellation and process cleanup...'
CANCEL_TASK=$(launch "${HTTP_TARGET}" OWTF-CM-006-active \
  '{"wordlist":"slow.txt","threads":1,"delay":"1s","request_timeout":"5s"}')
wait_for_status "${CANCEL_TASK}" running
request POST "/api/v2/tasks/${CANCEL_TASK}/cancel" '{}' | jq -e '.status == "cancelled"' >/dev/null || fail 'cancellation was not persisted'
assert_removed "${CANCEL_TASK}"

printf '%s\n' 'Kali container compatibility passed for testssl.sh, WAFW00F, Gobuster, WhatWeb, Nuclei, and Wapiti.'
printf '%s\n' 'Metagoofil startup passed; it has no deterministic local search-provider mode.'
