#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
TMP_DIR=$(mktemp -d "${TMPDIR:-/tmp}/owtf-next-smoke.XXXXXX")
ADDRESS=${OWTF_SMOKE_ADDR:-127.0.0.1:18109}
BASE_URL="http://${ADDRESS}"
RESPONSE_FILE="${TMP_DIR}/response"
CLI_RESPONSE_FILE="${TMP_DIR}/cli-response"
SERVER_PID=""
GO_PATH=${OWTF_SMOKE_GOPATH:-${TMPDIR:-/tmp}/owtf-go}
GO_MODULE_CACHE=${OWTF_SMOKE_GOMODCACHE:-${GO_PATH}/pkg/mod}

cleanup() {
  if [[ -n "${SERVER_PID}" ]] && kill -0 "${SERVER_PID}" 2>/dev/null; then
    kill "${SERVER_PID}" 2>/dev/null || true
    wait "${SERVER_PID}" 2>/dev/null || true
  fi
  rm -rf "${TMP_DIR}"
}
trap cleanup EXIT INT TERM

fail() {
  printf 'FAIL: %s\n' "$*" >&2
  exit 1
}

request() {
  local method=$1
  local path=$2
  local expected=$3
  local body=${4-}
  local status
  if [[ -n "${body}" ]]; then
    status=$(curl --silent --show-error --max-time 10 \
      --request "${method}" --header 'Content-Type: application/json' --data "${body}" \
      --output "${RESPONSE_FILE}" --write-out '%{http_code}' "${BASE_URL}${path}")
  else
    status=$(curl --silent --show-error --max-time 10 \
      --request "${method}" --output "${RESPONSE_FILE}" --write-out '%{http_code}' "${BASE_URL}${path}")
  fi
  if [[ "${status}" != "${expected}" ]]; then
    printf '%s %s returned %s, expected %s\n' "${method}" "${path}" "${status}" "${expected}" >&2
    cat "${RESPONSE_FILE}" >&2
    exit 1
  fi
}

assert_json() {
  local expression=$1
  local message=$2
  shift 2
  jq -e "$@" "${expression}" "${RESPONSE_FILE}" >/dev/null || fail "${message}: $(cat "${RESPONSE_FILE}")"
}

cli_json() {
  OWTF_URL="${BASE_URL}" "${TMP_DIR}/owtf-next" "$@" >"${CLI_RESPONSE_FILE}"
  jq -e . "${CLI_RESPONSE_FILE}" >/dev/null || fail "CLI returned invalid JSON for: $*"
}

wait_for_task_status() {
  local task_id=$1
  local wanted=$2
  local status=""
  local attempt
  for attempt in $(seq 1 100); do
    request GET "/api/v2/tasks/${task_id}" 200
    status=$(jq -r '.status' "${RESPONSE_FILE}")
    if [[ "${status}" == "${wanted}" ]]; then
      return 0
    fi
    if [[ "${status}" == "failed" || "${status}" == "cancelled" ]]; then
      fail "task ${task_id} reached ${status}, expected ${wanted}"
    fi
    sleep 0.05
  done
  fail "task ${task_id} remained ${status}, expected ${wanted}"
}

command -v curl >/dev/null || fail "curl is required"
command -v jq >/dev/null || fail "jq is required"
command -v go >/dev/null || fail "Go is required"
command -v sleep >/dev/null || fail "sleep is required"
if curl --silent --fail --max-time 1 "${BASE_URL}/debug/health" >/dev/null 2>&1; then
  fail "${ADDRESS} is already serving OWTF; set OWTF_SMOKE_ADDR to an unused address"
fi

mkdir -p "${TMP_DIR}/plugins"
cp -R "${ROOT_DIR}/plugins-next/." "${TMP_DIR}/plugins/"
mkdir -p "${TMP_DIR}/plugins/OWTF-SMOKE-001/active" "${TMP_DIR}/plugins/OWTF-SMOKE-002/active"
cat >"${TMP_DIR}/plugins/OWTF-SMOKE-001/active/plugin.yaml" <<'YAML'
apiVersion: owtf.dev/v1alpha1
kind: Plugin
metadata:
  id: OWTF-SMOKE-001-active
  version: 0.1.0
  title: Smoke cancellation fixture
spec:
  techniques: [OWTF-SMOKE-001]
  variant: active
  targetKinds: [url]
  requirements:
    commands: [sleep]
  runtime:
    type: command
    command:
      executable: sleep
      args: ["30"]
YAML
cat >"${TMP_DIR}/plugins/OWTF-SMOKE-002/active/plugin.yaml" <<'YAML'
apiVersion: owtf.dev/v1alpha1
kind: Plugin
metadata:
  id: OWTF-SMOKE-002-active
  version: 0.1.0
  title: Missing requirement fixture
spec:
  techniques: [OWTF-SMOKE-002]
  variant: active
  targetKinds: [url]
  requirements:
    commands: [owtf-command-that-does-not-exist]
  runtime:
    type: command
    command:
      executable: owtf-command-that-does-not-exist
YAML

printf '%s\n' 'Building the bounded OWTF Next test server...'
(
  cd "${ROOT_DIR}"
  GOPATH="${GO_PATH}" GOMODCACHE="${GO_MODULE_CACHE}" GOCACHE="${TMP_DIR}/go-cache" GOMAXPROCS=2 \
    go build -o "${TMP_DIR}/owtf-next" ./cmd/owtf-next
)

OWTF_ADDR="${ADDRESS}" \
OWTF_DATA_DIR="${TMP_DIR}/data" \
OWTF_PLUGIN_DIR="${TMP_DIR}/plugins" \
OWTF_WORKERS=1 \
  "${TMP_DIR}/owtf-next" >"${TMP_DIR}/server.log" 2>&1 &
SERVER_PID=$!

for attempt in $(seq 1 100); do
  if curl --silent --fail --max-time 1 "${BASE_URL}/debug/health" >/dev/null 2>&1; then
    break
  fi
  if ! kill -0 "${SERVER_PID}" 2>/dev/null; then
    cat "${TMP_DIR}/server.log" >&2
    fail "server exited during startup"
  fi
  sleep 0.05
done

printf '%s\n' 'Checking health, routing, and strict request errors...'
request GET /debug/health 200
assert_json '.status == "ok"' 'health response is invalid'
cli_json health
jq -e '.status == "ok"' "${CLI_RESPONSE_FILE}" >/dev/null || fail 'CLI health response is invalid'
request GET / 200
request GET /assets/app.js 200
request GET /assets/InterVariable.woff2 200
request GET /api/v2/transactions 400
request GET /api/v2/targets/does-not-exist 404
request GET /api/v2/tasks/does-not-exist 404
request POST /api/v2/tasks/does-not-exist/cancel 404 '{}'
request POST /api/v2/sessions 400 '{"name":"invalid","unexpected":true}'

printf '%s\n' 'Checking session and target lifecycle...'
request GET /api/v2/sessions 200
assert_json 'length == 0' 'new database contains sessions'
cli_json sessions list
jq -e 'length == 0' "${CLI_RESPONSE_FILE}" >/dev/null || fail 'CLI session list is not empty'
request POST /api/v2/sessions 201 '{"name":"curl smoke session"}'
SESSION_ID=$(jq -r '.id' "${RESPONSE_FILE}")
request GET "/api/v2/sessions/${SESSION_ID}" 200
assert_json '.name == "curl smoke session"' 'session could not be read back'
cli_json sessions show "${SESSION_ID}"
jq -e --arg id "${SESSION_ID}" '.id == $id' "${CLI_RESPONSE_FILE}" >/dev/null || fail 'CLI could not show the session'
request POST "/api/v2/sessions/${SESSION_ID}/targets" 400 '{"targets":[]}'

TARGET_PAYLOAD=$(jq -nc --arg target "${BASE_URL}/debug/health" '{targets:[$target,$target,"example.test","192.0.2.10","192.0.2.0/28","ftp://invalid.example"]}')
request POST "/api/v2/sessions/${SESSION_ID}/targets" 200 "${TARGET_PAYLOAD}"
assert_json '.created | length == 4' 'target kinds were not created'
assert_json '.duplicates | length == 1' 'duplicate target was not reported'
assert_json '.invalid | length == 1' 'invalid target was not reported'
URL_TARGET_ID=$(jq -r '.created[] | select(.kind == "url") | .id' "${RESPONSE_FILE}")
HOST_TARGET_ID=$(jq -r '.created[] | select(.kind == "hostname") | .id' "${RESPONSE_FILE}")
request GET "/api/v2/sessions/${SESSION_ID}/targets" 200
assert_json 'length == 4' 'target list is incomplete'
request GET "/api/v2/targets/${URL_TARGET_ID}" 200
assert_json '.kind == "url" and .value == $target' 'normalized URL target is incorrect' --arg target "${BASE_URL}/debug/health"
cli_json targets list --session "${SESSION_ID}"
jq -e 'length == 4' "${CLI_RESPONSE_FILE}" >/dev/null || fail 'CLI target list is incomplete'
cli_json targets show "${URL_TARGET_ID}"
jq -e --arg id "${URL_TARGET_ID}" '.id == $id' "${CLI_RESPONSE_FILE}" >/dev/null || fail 'CLI could not show the target'

printf '%s\n' 'Checking plugin discovery and preflight failures...'
request GET /api/v2/plugins 200
assert_json 'length == 4' 'plugin catalog is incomplete'
assert_json '[.[] | select(.availability == "ready")] | length == 3' 'ready plugin count is incorrect'
assert_json '[.[] | select(.id == "OWTF-SMOKE-002-active" and .availability == "missing_requirements" and (.reason | contains("owtf-command-that-does-not-exist")))] | length == 1' 'missing requirement is not visible'
cli_json plugins list
jq -e 'length == 4' "${CLI_RESPONSE_FILE}" >/dev/null || fail 'CLI plugin catalog is incomplete'

UNSUPPORTED_RUN=$(jq -nc --arg session "${SESSION_ID}" --arg target "${HOST_TARGET_ID}" '{session_id:$session,target_ids:[$target],plugin_ids:["OWTF-WSP-001-active"]}')
request POST /api/v2/runs 400 "${UNSUPPORTED_RUN}"
assert_json '.error | contains("does not support hostname")' 'unsupported target kind was not rejected'
MISSING_RUN=$(jq -nc --arg session "${SESSION_ID}" --arg target "${URL_TARGET_ID}" '{session_id:$session,target_ids:[$target],plugin_ids:["OWTF-SMOKE-002-active"]}')
request POST /api/v2/runs 409 "${MISSING_RUN}"
assert_json '.error | contains("missing commands")' 'missing command run was not rejected'
request GET "/api/v2/tasks?session_id=${SESSION_ID}" 200
assert_json 'length == 0' 'preflight failures created tasks'

printf '%s\n' 'Checking grouped execution, workers, logs, reports, and evidence...'
GROUP_RUN=$(jq -nc --arg session "${SESSION_ID}" --arg target "${URL_TARGET_ID}" '{session_id:$session,target_ids:[$target],plugin_ids:["OWTF-IG-004-semi-passive","OWTF-WSP-001-active"]}')
request POST /api/v2/runs 202 "${GROUP_RUN}"
assert_json '.tasks | length == 2' 'grouped run did not create two tasks'
GROUP_TASK_IDS=()
while IFS= read -r task_id; do GROUP_TASK_IDS+=("${task_id}"); done < <(jq -r '.tasks[].id' "${RESPONSE_FILE}")
for task_id in "${GROUP_TASK_IDS[@]}"; do
  wait_for_task_status "${task_id}" succeeded
  request GET "/api/v2/tasks/${task_id}/events" 200
  assert_json 'length >= 3' "task ${task_id} is missing lifecycle events"
done
request GET "/api/v2/workers" 200
assert_json 'length == 1 and .[0].status == "idle" and .[0].completed == 2' 'worker state or accounting is incorrect'
request GET "/api/v2/targets/${URL_TARGET_ID}/report" 200
assert_json '.tasks | length == 2' 'target report is missing tasks'
assert_json '.transactions | length == 1' 'target report is missing the builtin HTTP transaction'
assert_json '.observations | length == 2' 'target report is missing observations'
assert_json '.artifacts | length == 3' 'target report is missing retained artifacts'
ARTIFACT_IDS=()
while IFS= read -r artifact_id; do ARTIFACT_IDS+=("${artifact_id}"); done < <(jq -r '.artifacts[].id' "${RESPONSE_FILE}")
for artifact_id in "${ARTIFACT_IDS[@]}"; do
  request GET "/api/v2/artifacts/${artifact_id}" 200
  [[ -s "${RESPONSE_FILE}" ]] || fail "artifact ${artifact_id} is empty"
done
request GET /api/v2/artifacts/does-not-exist 404
request GET "/api/v2/transactions?session_id=${SESSION_ID}" 200
assert_json 'length == 1 and .[0].status_code == 200 and .[0].target_id == $target' 'transaction list is incorrect' --arg target "${URL_TARGET_ID}"

cli_json worklist --session "${SESSION_ID}"
jq -e 'length == 2 and all(.[]; .status == "succeeded")' "${CLI_RESPONSE_FILE}" >/dev/null || fail 'CLI worklist is incorrect'
cli_json workers
jq -e 'length == 1 and .[0].completed == 2' "${CLI_RESPONSE_FILE}" >/dev/null || fail 'CLI worker state is incorrect'
cli_json tasks show "${GROUP_TASK_IDS[0]}"
jq -e '.status == "succeeded"' "${CLI_RESPONSE_FILE}" >/dev/null || fail 'CLI task state is incorrect'
cli_json tasks logs "${GROUP_TASK_IDS[0]}"
jq -e 'length >= 3' "${CLI_RESPONSE_FILE}" >/dev/null || fail 'CLI task logs are incomplete'
cli_json targets report "${URL_TARGET_ID}"
jq -e '.tasks | length == 2' "${CLI_RESPONSE_FILE}" >/dev/null || fail 'CLI target report is incomplete'
cli_json transactions list --session "${SESSION_ID}" --target "${URL_TARGET_ID}"
jq -e 'length == 1 and .[0].status_code == 200' "${CLI_RESPONSE_FILE}" >/dev/null || fail 'CLI transactions are incomplete'
CLI_ARTIFACT_FILE="${TMP_DIR}/cli-artifact"
OWTF_URL="${BASE_URL}" "${TMP_DIR}/owtf-next" artifacts get --output "${CLI_ARTIFACT_FILE}" "${ARTIFACT_IDS[0]}"
[[ -s "${CLI_ARTIFACT_FILE}" ]] || fail 'CLI artifact download is empty'

cli_json runs create --session "${SESSION_ID}" --target "${URL_TARGET_ID}" --plugin OWTF-WSP-001-active
CLI_RUN_TASK_ID=$(jq -r '.tasks[0].id' "${CLI_RESPONSE_FILE}")
wait_for_task_status "${CLI_RUN_TASK_ID}" succeeded
cli_json scan --session "${SESSION_ID}" --plugin OWTF-WSP-001-active "${BASE_URL}/debug/health"
CLI_SCAN_TASK_ID=$(jq -r '.tasks[0].id' "${CLI_RESPONSE_FILE}")
wait_for_task_status "${CLI_SCAN_TASK_ID}" succeeded
cli_json workers
jq -e '.[0].completed == 4' "${CLI_RESPONSE_FILE}" >/dev/null || fail 'CLI-launched work was not completed'

printf '%s\n' 'Checking cancellation and worker cleanup...'
CANCEL_RUN=$(jq -nc --arg session "${SESSION_ID}" --arg target "${URL_TARGET_ID}" '{session_id:$session,target_ids:[$target],plugin_ids:["OWTF-SMOKE-001-active"]}')
request POST /api/v2/runs 202 "${CANCEL_RUN}"
CANCEL_TASK_ID=$(jq -r '.tasks[0].id' "${RESPONSE_FILE}")
wait_for_task_status "${CANCEL_TASK_ID}" running
request GET /api/v2/workers 200
assert_json 'length == 1 and .[0].status == "running" and .[0].task_id == $task' 'worker did not expose the running task' --arg task "${CANCEL_TASK_ID}"
request POST "/api/v2/tasks/${CANCEL_TASK_ID}/cancel" 200 '{}'
assert_json '.status == "cancelled"' 'cancel endpoint did not persist cancellation'
for attempt in $(seq 1 100); do
  request GET /api/v2/workers 200
  if jq -e '.[0].status == "idle" and .[0].cancelled == 1' "${RESPONSE_FILE}" >/dev/null; then
    break
  fi
  sleep 0.05
done
assert_json '.[0].status == "idle" and .[0].cancelled == 1' 'worker did not return to idle after cancellation'
request GET "/api/v2/tasks/${CANCEL_TASK_ID}/events" 200
assert_json '[.[].message] | index("task cancelled") != null' 'cancellation event is missing'

cli_json runs create --session "${SESSION_ID}" --target "${URL_TARGET_ID}" --plugin OWTF-SMOKE-001-active
CLI_CANCEL_TASK_ID=$(jq -r '.tasks[0].id' "${CLI_RESPONSE_FILE}")
wait_for_task_status "${CLI_CANCEL_TASK_ID}" running
cli_json tasks cancel "${CLI_CANCEL_TASK_ID}"
jq -e '.status == "cancelled"' "${CLI_RESPONSE_FILE}" >/dev/null || fail 'CLI cancellation did not persist'
for attempt in $(seq 1 100); do
  request GET /api/v2/workers 200
  if jq -e '.[0].status == "idle" and .[0].cancelled == 2' "${RESPONSE_FILE}" >/dev/null; then
    break
  fi
  sleep 0.05
done
assert_json '.[0].status == "idle" and .[0].cancelled == 2' 'worker did not clean up after CLI cancellation'

printf '%s\n' 'Checking destructive cleanup and final empty state...'
cli_json targets add --session "${SESSION_ID}" 198.51.100.9
CLI_TARGET_ID=$(jq -r '.created[0].id' "${CLI_RESPONSE_FILE}")
cli_json targets delete "${CLI_TARGET_ID}"
jq -e --arg id "${CLI_TARGET_ID}" '.deleted == [$id]' "${CLI_RESPONSE_FILE}" >/dev/null || fail 'CLI target deletion is incorrect'
cli_json sessions create --name 'CLI smoke session'
jq -e '.name == "CLI smoke session"' "${CLI_RESPONSE_FILE}" >/dev/null || fail 'CLI session creation failed'
request GET "/api/v2/sessions/${SESSION_ID}/targets" 200
TARGET_IDS=()
while IFS= read -r target_id; do TARGET_IDS+=("${target_id}"); done < <(jq -r '.[].id' "${RESPONSE_FILE}")
for target_id in "${TARGET_IDS[@]}"; do
  request DELETE "/api/v2/targets/${target_id}" 204
done
request GET "/api/v2/sessions/${SESSION_ID}/targets" 200
assert_json 'length == 0' 'targets survived deletion'
request GET "/api/v2/targets/${URL_TARGET_ID}/report" 404
request GET "/api/v2/tasks?session_id=${SESSION_ID}" 200
assert_json 'length == 0' 'tasks survived target deletion'
request GET "/api/v2/transactions?session_id=${SESSION_ID}" 200
assert_json 'length == 0' 'transactions survived target deletion'

printf '%s\n' 'PASS: curl API smoke test completed.'
