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

cleanup() {
  if [[ -n "${SERVER_PID}" ]]; then
    kill "${SERVER_PID}" >/dev/null 2>&1 || true
    wait "${SERVER_PID}" >/dev/null 2>&1 || true
  fi
  [[ ! -f "${TMP_DIR}/server.log" ]] || cp "${TMP_DIR}/server.log" "${EVIDENCE_DIR}/server.log"
  docker logs "${FIXTURE}" >"${EVIDENCE_DIR}/requests.log" 2>&1 || true
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

for command in docker curl go jq openssl; do
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
  access_log /dev/stdout owtf;
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
start_server 240

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

if [[ "${MODE}" == all ]]; then
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
jq -e '.tasks.failed == 2 and .tasks.cancelled == 1 and .tasks.running == 0 and .tasks.queued == 0 and
  .attempts.total == .tasks.total and .attempts.failed == 2 and .attempts.cancelled == 1 and
  .workers.total == 1 and .workers.idle == 1 and .workers.completed == 0' \
  "${EVIDENCE_DIR}/metrics.json" >/dev/null || fail 'failure metrics or restart state are incorrect'
request GET "/api/v2/sessions/${SESSION_ID}/report" >"${EVIDENCE_DIR}/report.json"
jq -e '.summary.failed == 2 and .summary.cancelled == 1 and .summary.attempts == .summary.tasks' \
  "${EVIDENCE_DIR}/report.json" >/dev/null || fail 'failure report is incomplete'

if [[ "${MODE}" == all ]]; then
  printf '%s\n' 'Kali container compatibility passed for testssl.sh, WAFW00F, Gobuster, WhatWeb, Nuclei, and Wapiti.'
  printf '%s\n' 'Metagoofil startup passed; it has no deterministic local search-provider mode.'
fi
printf 'PASS: terminal states and single attempts survived restart. Evidence: %s\n' "${EVIDENCE_DIR}"
