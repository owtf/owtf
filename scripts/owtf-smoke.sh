#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
TMP_DIR=$(mktemp -d "${TMPDIR:-/tmp}/owtf-smoke.XXXXXX")
ADDRESS=${OWTF_SMOKE_ADDR:-127.0.0.1:18109}
BASE_URL="http://${ADDRESS}"
RESPONSE_FILE="${TMP_DIR}/response"
CLI_RESPONSE_FILE="${TMP_DIR}/cli-response"
SERVER_PID=""
PROXY_PID=""
GO_PATH=${OWTF_SMOKE_GOPATH:-${TMPDIR:-/tmp}/owtf-go}
GO_MODULE_CACHE=${OWTF_SMOKE_GOMODCACHE:-${GO_PATH}/pkg/mod}
PROXY_ADDRESS=${OWTF_SMOKE_PROXY_ADDR:-127.0.0.1:18118}
PROXY_API_ADDRESS=${OWTF_SMOKE_PROXY_API_ADDR:-127.0.0.1:18120}
PROXY_URL="http://${PROXY_ADDRESS}"
PROXY_API_URL="http://${PROXY_API_ADDRESS}"
PROXY_HAR="${TMP_DIR}/proxy.har"
PROXY_CA="${TMP_DIR}/proxy-ca.crt"
PROXY_KEY="${TMP_DIR}/proxy-ca.key"
EMPTY_INTERCEPTORS="${TMP_DIR}/empty-interceptors.json"
CONFIG_FILE="${TMP_DIR}/config.yaml"

cleanup() {
  if [[ -n "${PROXY_PID}" ]] && kill -0 "${PROXY_PID}" 2>/dev/null; then
    kill "${PROXY_PID}" 2>/dev/null || true
    wait "${PROXY_PID}" 2>/dev/null || true
  fi
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

upload_har() {
  local target_id=$1
  local file=$2
  local expected=$3
  local status
  status=$(curl --silent --show-error --max-time 10 \
    --request POST --form "har=@${file};filename=capture.har" \
    --output "${RESPONSE_FILE}" --write-out '%{http_code}' \
    "${BASE_URL}/api/v2/targets/${target_id}/transactions/import")
  if [[ "${status}" != "${expected}" ]]; then
    printf 'HAR import returned %s, expected %s\n' "${status}" "${expected}" >&2
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
  OWTF_URL="${BASE_URL}" "${TMP_DIR}/owtf" "$@" >"${CLI_RESPONSE_FILE}"
  jq -e . "${CLI_RESPONSE_FILE}" >/dev/null || fail "CLI returned invalid JSON for: $*"
}

proxy_cli_json() {
  OWTF_PROXY_API_URL="${PROXY_API_URL}" "${TMP_DIR}/owtf" proxy "$@" >"${CLI_RESPONSE_FILE}"
  jq -e . "${CLI_RESPONSE_FILE}" >/dev/null || fail "proxy CLI returned invalid JSON for: $*"
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
command -v cmp >/dev/null || fail "cmp is required"
command -v jq >/dev/null || fail "jq is required"
command -v go >/dev/null || fail "Go is required"
command -v sleep >/dev/null || fail "sleep is required"
command -v unzip >/dev/null || fail "unzip is required"
if curl --silent --fail --max-time 1 "${BASE_URL}/debug/health" >/dev/null 2>&1; then
  fail "${ADDRESS} is already serving OWTF; set OWTF_SMOKE_ADDR to an unused address"
fi

mkdir -p "${TMP_DIR}/plugins"
cp -R "${ROOT_DIR}/plugins/." "${TMP_DIR}/plugins/"
mkdir -p "${TMP_DIR}/profiles"
cp -R "${ROOT_DIR}/profiles/." "${TMP_DIR}/profiles/"
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
  group: auxiliary
  type: active
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
  group: auxiliary
  type: active
  targetKinds: [url]
  requirements:
    commands: [owtf-command-that-does-not-exist]
  runtime:
    type: command
    command:
      executable: owtf-command-that-does-not-exist
YAML

cat >"${CONFIG_FILE}" <<YAML
apiVersion: owtf.dev/v1alpha1
kind: Config
server:
  address: "${ADDRESS}"
  dataDirectory: "${TMP_DIR}/data"
  workers: 1
  taskTimeoutSeconds: 30
plugins:
  directory: "${TMP_DIR}/plugins"
  profilesDirectory: "${TMP_DIR}/profiles"
  defaultProfile: default
  containerEngine: docker
proxy:
  listenAddress: "${PROXY_ADDRESS}"
  apiAddress: "${PROXY_API_ADDRESS}"
  output: "${PROXY_HAR}"
  caCertificate: "${PROXY_CA}"
  caKey: "${PROXY_KEY}"
  targetHosts: [127.0.0.1]
YAML

printf '%s\n' 'Building the bounded OWTF test server...'
(
  cd "${ROOT_DIR}"
  GOPATH="${GO_PATH}" GOMODCACHE="${GO_MODULE_CACHE}" GOCACHE="${TMP_DIR}/go-cache" GOMAXPROCS=2 \
    go build -o "${TMP_DIR}/owtf" ./cmd/owtf
)

"${TMP_DIR}/owtf" config validate "${CONFIG_FILE}" >"${CLI_RESPONSE_FILE}"
jq -e '.valid == true' "${CLI_RESPONSE_FILE}" >/dev/null || fail 'configuration validation failed'
"${TMP_DIR}/owtf" config show --config "${CONFIG_FILE}" >"${CLI_RESPONSE_FILE}"
jq -e --arg address "${ADDRESS}" \
  '.server.address == $address and .server.workers == 1 and .proxy.cache_entries == 1000' \
  "${CLI_RESPONSE_FILE}" >/dev/null || fail 'effective configuration is incorrect'

"${TMP_DIR}/owtf" serve --config "${CONFIG_FILE}" >"${TMP_DIR}/server.log" 2>&1 &
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
request GET /api/v2/health 200
assert_json '.status == "ok"' 'API health response is invalid'
cli_json health
jq -e '.status == "ok"' "${CLI_RESPONSE_FILE}" >/dev/null || fail 'CLI health response is invalid'
request GET / 200
request GET /assets/app.js 200
request GET /assets/InterVariable.woff2 200
request GET /api/v2/transactions 400
request GET /api/v2/runs 400
request GET /api/v2/targets/does-not-exist 404
request GET /api/v2/runs/does-not-exist 404
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
assert_json '.kind == "url" and .value == $target and .scope == true' 'normalized URL target is incorrect' --arg target "${BASE_URL}/debug/health"
request PATCH "/api/v2/targets/${URL_TARGET_ID}" 200 '{"scope":false}'
assert_json '.scope == false' 'target scope update was not persisted'
request GET "/api/v2/sessions/${SESSION_ID}/targets/search?search=debug&kind=url&scope=false&limit=1&offset=0" 200
assert_json '.records_total == 4 and .records_filtered == 1 and (.data | length) == 1 and .data[0].id == $target' 'target search is incorrect' --arg target "${URL_TARGET_ID}"
request GET "/api/v2/sessions/${SESSION_ID}/targets/search?scope=maybe" 400
assert_json '.error == "scope must be true or false"' 'invalid target search was accepted'
cli_json targets list --session "${SESSION_ID}"
jq -e 'length == 4' "${CLI_RESPONSE_FILE}" >/dev/null || fail 'CLI target list is incomplete'
cli_json targets search --session "${SESSION_ID}" --search debug --kind url --scope false --limit 1 --offset 0
jq -e --arg id "${URL_TARGET_ID}" '.records_total == 4 and .records_filtered == 1 and .data[0].id == $id' "${CLI_RESPONSE_FILE}" >/dev/null || fail 'CLI target search is incorrect'
cli_json targets update --scope true "${URL_TARGET_ID}"
jq -e '.scope == true' "${CLI_RESPONSE_FILE}" >/dev/null || fail 'CLI target scope update failed'
cli_json targets show "${URL_TARGET_ID}"
jq -e --arg id "${URL_TARGET_ID}" '.id == $id' "${CLI_RESPONSE_FILE}" >/dev/null || fail 'CLI could not show the target'

printf '%s\n' 'Checking HAR transaction import, retrieval, files, and deletion...'
HAR_FILE="${TMP_DIR}/capture.har"
cat >"${HAR_FILE}" <<JSON
{"log":{"version":"1.2","entries":[{
  "startedDateTime":"2026-09-02T10:11:12Z","time":9.4,
  "request":{"method":"POST","url":"${BASE_URL}/debug/health","headers":[{"name":"X-OWTF","value":"smoke"}],"postData":{"mimeType":"text/plain","text":"imported request"}},
  "response":{"status":201,"headers":[{"name":"Content-Type","value":"text/plain"}],"content":{"mimeType":"text/plain","text":"aW1wb3J0ZWQgcmVzcG9uc2U=","encoding":"base64"}}
}]}}
JSON
upload_har "${URL_TARGET_ID}" "${HAR_FILE}" 201
assert_json '.imported == 1 and (.source_artifact.task_id | not) and (.transactions | length == 1)' 'HAR import response is incorrect'
CURL_IMPORTED_TRANSACTION_ID=$(jq -r '.transactions[0].id' "${RESPONSE_FILE}")
CURL_SOURCE_ARTIFACT_ID=$(jq -r '.source_artifact.id' "${RESPONSE_FILE}")
CURL_REQUEST_ARTIFACT_ID=$(jq -r '.transactions[0].request_body_artifact_id' "${RESPONSE_FILE}")
CURL_RESPONSE_ARTIFACT_ID=$(jq -r '.transactions[0].response_body_artifact_id' "${RESPONSE_FILE}")
request GET "/api/v2/targets/${URL_TARGET_ID}/transactions/${CURL_IMPORTED_TRANSACTION_ID}" 200
assert_json '.task_id == null and .method == "POST" and .status_code == 201 and .duration_ms == 9' 'imported transaction detail is incorrect'
request GET "/api/v2/targets/${URL_TARGET_ID}/urls" 200
assert_json 'length == 1 and .[0].target_id == $target and .[0].url == $url and .[0].visited == true and .[0].scope == true' 'imported transaction URL is incorrect' --arg target "${URL_TARGET_ID}" --arg url "${BASE_URL}/debug/health"
request GET "/api/v2/targets/${URL_TARGET_ID}/urls/search?search=DEBUG&visited=true&scope=true&limit=1&offset=0" 200
assert_json '.records_total == 1 and .records_filtered == 1 and (.data | length) == 1' 'URL search is incorrect'
request GET "/api/v2/targets/${URL_TARGET_ID}/urls/search?visited=maybe" 400
assert_json '.error == "visited must be true or false"' 'invalid URL search was accepted'
request GET "/api/v2/artifacts/${CURL_SOURCE_ARTIFACT_ID}" 200
cmp -s "${HAR_FILE}" "${RESPONSE_FILE}" || fail 'source HAR artifact differs from upload'
request GET "/api/v2/artifacts/${CURL_REQUEST_ARTIFACT_ID}" 200
[[ $(cat "${RESPONSE_FILE}") == 'imported request' ]] || fail 'request body artifact is incorrect'
request GET "/api/v2/artifacts/${CURL_RESPONSE_ARTIFACT_ID}" 200
[[ $(cat "${RESPONSE_FILE}") == 'imported response' ]] || fail 'response body artifact is incorrect'
request DELETE "/api/v2/targets/${URL_TARGET_ID}/transactions/${CURL_IMPORTED_TRANSACTION_ID}" 204
request GET "/api/v2/targets/${URL_TARGET_ID}/transactions/${CURL_IMPORTED_TRANSACTION_ID}" 404
request GET "/api/v2/targets/${URL_TARGET_ID}/report" 200
assert_json '(.tasks | length) == 0 and (.transactions | length) == 0 and (.artifacts | length) == 0 and (.urls | length) == 1' 'transaction deletion removed its URL catalog entry or left evidence records'

cli_json transactions import --target "${URL_TARGET_ID}" "${HAR_FILE}"
jq -e '.imported == 1 and (.transactions | length == 1)' "${CLI_RESPONSE_FILE}" >/dev/null || fail 'CLI HAR import is incorrect'
IMPORTED_TRANSACTION_ID=$(jq -r '.transactions[0].id' "${CLI_RESPONSE_FILE}")
IMPORTED_SOURCE_ARTIFACT_ID=$(jq -r '.source_artifact.id' "${CLI_RESPONSE_FILE}")
IMPORTED_REQUEST_ARTIFACT_ID=$(jq -r '.transactions[0].request_body_artifact_id' "${CLI_RESPONSE_FILE}")
IMPORTED_RESPONSE_ARTIFACT_ID=$(jq -r '.transactions[0].response_body_artifact_id' "${CLI_RESPONSE_FILE}")
request GET "/api/v2/targets/${URL_TARGET_ID}/transactions/${IMPORTED_TRANSACTION_ID}" 200
assert_json '.task_id == null and .source_artifact_id == $source' 'CLI-imported transaction was not persisted' --arg source "${IMPORTED_SOURCE_ARTIFACT_ID}"
request GET "/api/v2/targets/${URL_TARGET_ID}/transactions" 200
assert_json 'length == 1 and .[0].id == $transaction' 'target transaction list is incorrect' --arg transaction "${IMPORTED_TRANSACTION_ID}"
cli_json urls list --target "${URL_TARGET_ID}"
jq -e --arg url "${BASE_URL}/debug/health" 'length == 1 and .[0].url == $url and .[0].visited == true and .[0].scope == true' "${CLI_RESPONSE_FILE}" >/dev/null || fail 'CLI URL list is incorrect'
cli_json urls search --target "${URL_TARGET_ID}" --search debug --visited true --scope true --limit 1 --offset 0
jq -e '.records_total == 1 and .records_filtered == 1 and (.data | length) == 1' "${CLI_RESPONSE_FILE}" >/dev/null || fail 'CLI URL search is incorrect'

printf '%s\n' 'Checking plugin discovery and preflight failures...'
request GET /api/v2/plugins 200
assert_json 'length == 6' 'plugin catalog is incomplete'
assert_json '[.[] | select(.availability == "ready")] | length == 5' 'ready plugin count is incorrect'
assert_json '[.[] | select(.id == "OWTF-SMOKE-002-active" and .availability == "missing_requirements" and (.reason | contains("owtf-command-that-does-not-exist")))] | length == 1' 'missing requirement is not visible'
assert_json '[.[] | select(.group == "web" and (.type == "active" or .type == "semi_passive"))] | length == 2' 'OWTF plugin group and type metadata is incorrect'
assert_json '[.[] | select(.id == "OWTF-IG-004-semi_passive" and (.inputs | map(.name)) == ["timeout_seconds","user_agent"])] | length == 1' 'plugin input schema is not visible'
assert_json '[.[] | select(.id == "OWTF-IG-004-semi_passive" and .techniques[0].code == "OWTF-IG-004" and .techniques[0].hint == "What is that site running?" and .techniques[0].priority == 99)] | length == 1' 'plugin technique metadata is not visible'
cli_json plugin list
jq -e 'length == 6' "${CLI_RESPONSE_FILE}" >/dev/null || fail 'CLI plugin catalog is incomplete'
cli_json plugin list --group web --type active
jq -e 'length == 1 and .[0].id == "OWTF-WSP-001-active"' "${CLI_RESPONSE_FILE}" >/dev/null || fail 'CLI plugin group/type filter is incorrect'
cli_json plugin list --group web --type external
jq -e 'length == 1 and .[0].id == "OWTF-IG-004-external" and .[0].runtime_type == "external" and .[0].availability == "ready"' "${CLI_RESPONSE_FILE}" >/dev/null || fail 'CLI external plugin is unavailable'
cli_json plugin list --group web --type grep
jq -e 'length == 1 and .[0].id == "OWTF-IG-004-grep" and .[0].runtime_type == "grep" and .[0].availability == "ready"' "${CLI_RESPONSE_FILE}" >/dev/null || fail 'CLI grep plugin is unavailable'
request GET /api/v2/profiles 200
assert_json 'length == 1 and .[0].name == "default" and .[0].plugins == ["OWTF-IG-004-semi_passive","OWTF-WSP-001-active"]' 'profile catalog is incorrect'
request GET /api/v2/profiles/default 200
assert_json '.name == "default" and (.plugins | length) == 2' 'default profile is incorrect'
cli_json profiles list
jq -e 'length == 1 and .[0].name == "default"' "${CLI_RESPONSE_FILE}" >/dev/null || fail 'CLI profile catalog is incorrect'
cli_json profiles show default
jq -e '.plugins == ["OWTF-IG-004-semi_passive","OWTF-WSP-001-active"]' "${CLI_RESPONSE_FILE}" >/dev/null || fail 'CLI default profile is incorrect'

UNSUPPORTED_RUN=$(jq -nc --arg session "${SESSION_ID}" --arg target "${HOST_TARGET_ID}" '{session_id:$session,target_ids:[$target],plugin_ids:["OWTF-WSP-001-active"]}')
request POST /api/v2/runs 400 "${UNSUPPORTED_RUN}"
assert_json '.error | contains("does not support hostname")' 'unsupported target kind was not rejected'
MISSING_RUN=$(jq -nc --arg session "${SESSION_ID}" --arg target "${URL_TARGET_ID}" '{session_id:$session,target_ids:[$target],plugin_ids:["OWTF-SMOKE-002-active"]}')
request POST /api/v2/runs 409 "${MISSING_RUN}"
assert_json '.error | contains("missing commands")' 'missing command run was not rejected'
INVALID_INPUT_RUN=$(jq -nc --arg session "${SESSION_ID}" --arg target "${URL_TARGET_ID}" '{session_id:$session,target_ids:[$target],plugin_ids:["OWTF-IG-004-semi_passive"],plugin_inputs:{"OWTF-IG-004-semi_passive":{timeout_seconds:"soon"}}}')
request POST /api/v2/runs 400 "${INVALID_INPUT_RUN}"
assert_json '.error | contains("timeout_seconds")' 'invalid plugin input was not rejected'
UNKNOWN_INPUT_RUN=$(jq -nc --arg session "${SESSION_ID}" --arg target "${URL_TARGET_ID}" '{session_id:$session,target_ids:[$target],plugin_ids:["OWTF-IG-004-semi_passive"],plugin_inputs:{"OWTF-IG-004-semi_passive":{unknown:true}}}')
request POST /api/v2/runs 400 "${UNKNOWN_INPUT_RUN}"
assert_json '.error | contains("unknown inputs")' 'unknown plugin input was not rejected'
UNSELECTED_INPUT_RUN=$(jq -nc --arg session "${SESSION_ID}" --arg target "${URL_TARGET_ID}" '{session_id:$session,target_ids:[$target],plugin_ids:["OWTF-WSP-001-active"],plugin_inputs:{"OWTF-IG-004-semi_passive":{timeout_seconds:5}}}')
request POST /api/v2/runs 400 "${UNSELECTED_INPUT_RUN}"
assert_json '.error | contains("unselected plugin")' 'input for an unselected plugin was not rejected'
request GET "/api/v2/tasks?session_id=${SESSION_ID}" 200
assert_json 'length == 0' 'preflight failures created tasks'

printf '%s\n' 'Checking grouped execution, workers, logs, reports, and evidence...'
GROUP_RUN=$(jq -nc --arg session "${SESSION_ID}" --arg target "${URL_TARGET_ID}" '{session_id:$session,target_ids:[$target],plugin_group:"web",plugin_types:["semi_passive","active"],plugin_inputs:{"OWTF-IG-004-semi_passive":{timeout_seconds:5,user_agent:"OWTF smoke; echo not-executed"}}}')
request POST /api/v2/runs 202 "${GROUP_RUN}"
assert_json '.run.profile == "default" and (.tasks | length) == 2 and .tasks[0].plugin_id == "OWTF-IG-004-semi_passive" and .tasks[1].plugin_id == "OWTF-WSP-001-active"' 'default profile did not order the grouped run'
GROUP_RUN_ID=$(jq -r '.run.id' "${RESPONSE_FILE}")
INPUT_TASK_ID=$(jq -r '.tasks[] | select(.plugin_id == "OWTF-IG-004-semi_passive") | .id' "${RESPONSE_FILE}")
GROUP_TASK_IDS=()
while IFS= read -r task_id; do GROUP_TASK_IDS+=("${task_id}"); done < <(jq -r '.tasks[].id' "${RESPONSE_FILE}")
for task_id in "${GROUP_TASK_IDS[@]}"; do
  wait_for_task_status "${task_id}" succeeded
  request GET "/api/v2/tasks/${task_id}/events" 200
  assert_json 'length >= 3' "task ${task_id} is missing lifecycle events"
done
request GET "/api/v2/tasks/${INPUT_TASK_ID}/events" 200
assert_json '[.[].message] | join("\n") | contains("OWTF smoke; echo not-executed")' 'resolved plugin input did not reach the command executor'
request GET "/api/v2/tasks/${INPUT_TASK_ID}/review" 200
assert_json '.task_id == $task and .rank == "unranked" and .notes == "" and .updated_at == null' 'new plugin output review is not unranked' --arg task "${INPUT_TASK_ID}"
PLUGIN_REVIEW=$(jq -nc '{rank:"high",notes:"Verified from retained transaction evidence."}')
request PATCH "/api/v2/tasks/${INPUT_TASK_ID}/review" 200 "${PLUGIN_REVIEW}"
assert_json '.task_id == $task and .rank == "high" and .notes == "Verified from retained transaction evidence." and .updated_at != null' 'plugin output review was not saved' --arg task "${INPUT_TASK_ID}"
cli_json plugin review "${INPUT_TASK_ID}"
jq -e --arg task "${INPUT_TASK_ID}" '.task_id == $task and .rank == "high" and .notes == "Verified from retained transaction evidence."' "${CLI_RESPONSE_FILE}" >/dev/null || fail 'CLI plugin output review is incorrect'
request GET "/api/v2/workers" 200
assert_json 'length == 1 and .[0].status == "idle" and .[0].completed == 2' 'worker state or accounting is incorrect'
request GET "/api/v2/targets/${URL_TARGET_ID}/report" 200
assert_json '.tasks | length == 2' 'target report is missing tasks'
assert_json '[.tasks[].techniques[].code] | sort == ["OWTF-IG-004","OWTF-WSP-001"]' 'target report is missing immutable technique metadata'
assert_json '.attempts | length == 2' 'target report is missing attempts'
assert_json '.transactions | length == 2' 'target report is missing imported or plugin transactions'
assert_json '(.urls | length) == 1 and .urls[0].visited == true and .urls[0].scope == true' 'target report is missing the deduplicated URL catalog'
assert_json '.observations | length == 2' 'target report is missing observations'
assert_json '.artifacts | length == 6' 'target report is missing retained artifacts'
assert_json '(.plugin_output_reviews | length) == 2 and any(.plugin_output_reviews[]; .task_id == $task and .rank == "high" and .notes == "Verified from retained transaction evidence.")' 'target report is missing the plugin output review' --arg task "${INPUT_TASK_ID}"
ARTIFACT_IDS=()
while IFS= read -r artifact_id; do ARTIFACT_IDS+=("${artifact_id}"); done < <(jq -r '.artifacts[].id' "${RESPONSE_FILE}")
for artifact_id in "${ARTIFACT_IDS[@]}"; do
  request GET "/api/v2/artifacts/${artifact_id}" 200
  [[ -s "${RESPONSE_FILE}" ]] || fail "artifact ${artifact_id} is empty"
done
request GET /api/v2/artifacts/does-not-exist 404
request GET "/api/v2/transactions?session_id=${SESSION_ID}" 200
assert_json 'length == 2 and ([.[].status_code] | sort) == [200,201] and all(.[]; .target_id == $target)' 'transaction list is incorrect' --arg target "${URL_TARGET_ID}"
request GET "/api/v2/transactions/search?session_id=${SESSION_ID}&target_id=${URL_TARGET_ID}&search=DEBUG&method=get&status_code=200&limit=1&offset=0" 200
assert_json '.records_total == 2 and .records_filtered == 1 and (.data | length) == 1 and .data[0].method == "GET"' 'session transaction search is incorrect'
request GET "/api/v2/targets/${URL_TARGET_ID}/transactions/search?search=debug&method=GET&status_code=200&limit=1&offset=0" 200
assert_json '.records_total == 2 and .records_filtered == 1 and (.data | length) == 1' 'target transaction search is incorrect'
request GET "/api/v2/transactions/search?session_id=${SESSION_ID}&status_code=99" 400
request GET "/api/v2/runs?session_id=${SESSION_ID}" 200
assert_json 'length == 1 and .[0].id == $run and .[0].profile == "default" and .[0].status == "succeeded"' 'run history is incorrect' --arg run "${GROUP_RUN_ID}"
request GET "/api/v2/runs/${GROUP_RUN_ID}" 200
assert_json '.profile == "default" and .status == "succeeded" and .finished_at != null' 'run was not finalized'
request GET "/api/v2/sessions/${SESSION_ID}/report" 200
assert_json '.summary.targets == 4 and .summary.runs == 1 and .summary.tasks == 2 and .summary.attempts == 2 and .summary.succeeded == 2 and .summary.urls == 1 and .summary.transactions == 2 and .summary.artifacts == 6 and .summary.observations == 2' 'session report summary is incorrect'
assert_json '(.plugin_output_reviews | length) == 2 and any(.plugin_output_reviews[]; .task_id == $task and .rank == "high")' 'session report is missing the plugin output review' --arg task "${INPUT_TASK_ID}"
request GET "/api/v2/sessions/${SESSION_ID}/export" 200
SESSION_REPORT_ZIP="${TMP_DIR}/session-report.zip"
cp "${RESPONSE_FILE}" "${SESSION_REPORT_ZIP}"
unzip -tqq "${SESSION_REPORT_ZIP}" || fail 'session report ZIP is invalid'
unzip -p "${SESSION_REPORT_ZIP}" report.json | jq -e --arg id "${SESSION_ID}" --arg task "${INPUT_TASK_ID}" '.session.id == $id and .summary.tasks == 2 and .summary.urls == 1 and (.urls | length) == 1 and any(.plugin_output_reviews[]; .task_id == $task and .rank == "high")' >/dev/null || fail 'session report JSON is incorrect'
unzip -p "${SESSION_REPORT_ZIP}" index.html | grep -q 'What is that site running?' || fail 'offline report is missing technique metadata'
unzip -p "${SESSION_REPORT_ZIP}" index.html | grep -q 'Verified from retained transaction evidence.' || fail 'offline report is missing the plugin output review'
unzip -p "${SESSION_REPORT_ZIP}" index.html | grep -q '>URLs<' || fail 'offline report is missing the URL catalog'
[[ $(unzip -Z1 "${SESSION_REPORT_ZIP}" | grep -c '^artifacts/') -eq 6 ]] || fail 'session report ZIP is missing artifacts'

cli_json worklist --session "${SESSION_ID}"
jq -e 'length == 2 and all(.[]; .status == "succeeded")' "${CLI_RESPONSE_FILE}" >/dev/null || fail 'CLI worklist is incorrect'
cli_json workers
jq -e 'length == 1 and .[0].completed == 2' "${CLI_RESPONSE_FILE}" >/dev/null || fail 'CLI worker state is incorrect'
cli_json tasks show "${GROUP_TASK_IDS[0]}"
jq -e '.status == "succeeded"' "${CLI_RESPONSE_FILE}" >/dev/null || fail 'CLI task state is incorrect'
request GET "/api/v2/tasks/${GROUP_TASK_IDS[0]}/attempts" 200
assert_json 'length == 1 and .[0].attempt_number == 1 and .[0].status == "succeeded"' 'API task attempt history is incorrect'
cli_json tasks attempts "${GROUP_TASK_IDS[0]}"
jq -e 'length == 1 and .[0].attempt_number == 1 and .[0].status == "succeeded"' "${CLI_RESPONSE_FILE}" >/dev/null || fail 'CLI task attempt history is incorrect'
cli_json tasks logs "${GROUP_TASK_IDS[0]}"
jq -e 'length >= 3' "${CLI_RESPONSE_FILE}" >/dev/null || fail 'CLI task logs are incomplete'
cli_json targets report "${URL_TARGET_ID}"
jq -e --arg task "${INPUT_TASK_ID}" '(.tasks | length == 2) and (.urls | length == 1) and ([.tasks[].techniques[].code] | sort == ["OWTF-IG-004","OWTF-WSP-001"]) and any(.plugin_output_reviews[]; .task_id == $task and .rank == "high")' "${CLI_RESPONSE_FILE}" >/dev/null || fail 'CLI target report is incomplete'
cli_json runs list --session "${SESSION_ID}"
jq -e --arg run "${GROUP_RUN_ID}" 'length == 1 and .[0].id == $run and .[0].status == "succeeded"' "${CLI_RESPONSE_FILE}" >/dev/null || fail 'CLI run history is incorrect'
cli_json runs show "${GROUP_RUN_ID}"
jq -e '.status == "succeeded" and .finished_at != null' "${CLI_RESPONSE_FILE}" >/dev/null || fail 'CLI run state is incorrect'
cli_json sessions report "${SESSION_ID}"
jq -e --arg task "${INPUT_TASK_ID}" '.summary.tasks == 2 and .summary.urls == 1 and .summary.transactions == 2 and .summary.artifacts == 6 and any(.plugin_output_reviews[]; .task_id == $task and .rank == "high")' "${CLI_RESPONSE_FILE}" >/dev/null || fail 'CLI session report is incomplete'
CLI_REPORT_ZIP="${TMP_DIR}/cli-session-report.zip"
cli_json sessions export --output "${CLI_REPORT_ZIP}" "${SESSION_ID}"
jq -e --arg output "${CLI_REPORT_ZIP}" '.output == $output and .bytes > 0' "${CLI_RESPONSE_FILE}" >/dev/null || fail 'CLI session export result is incorrect'
unzip -tqq "${CLI_REPORT_ZIP}" || fail 'CLI session export ZIP is invalid'
cli_json transactions list --session "${SESSION_ID}" --target "${URL_TARGET_ID}"
jq -e 'length == 2 and ([.[].status_code] | sort) == [200,201]' "${CLI_RESPONSE_FILE}" >/dev/null || fail 'CLI transactions are incomplete'
cli_json transactions search --session "${SESSION_ID}" --target "${URL_TARGET_ID}" --search debug --method get --status 200 --limit 1 --offset 0
jq -e '.records_total == 2 and .records_filtered == 1 and (.data | length) == 1 and .data[0].method == "GET"' "${CLI_RESPONSE_FILE}" >/dev/null || fail 'CLI transaction search is incorrect'
cli_json transactions show --target "${URL_TARGET_ID}" "${IMPORTED_TRANSACTION_ID}"
jq -e --arg id "${IMPORTED_TRANSACTION_ID}" '.id == $id and .task_id == null' "${CLI_RESPONSE_FILE}" >/dev/null || fail 'CLI transaction detail is incorrect'
CLI_ARTIFACT_FILE="${TMP_DIR}/cli-artifact"
OWTF_URL="${BASE_URL}" "${TMP_DIR}/owtf" artifacts get --output "${CLI_ARTIFACT_FILE}" "${ARTIFACT_IDS[0]}"
[[ -s "${CLI_ARTIFACT_FILE}" ]] || fail 'CLI artifact download is empty'

cli_json transactions delete --target "${URL_TARGET_ID}" "${IMPORTED_TRANSACTION_ID}"
jq -e --arg id "${IMPORTED_TRANSACTION_ID}" '.deleted == $id' "${CLI_RESPONSE_FILE}" >/dev/null || fail 'CLI transaction deletion is incorrect'
request GET "/api/v2/artifacts/${IMPORTED_SOURCE_ARTIFACT_ID}" 404
request GET "/api/v2/artifacts/${IMPORTED_REQUEST_ARTIFACT_ID}" 404
request GET "/api/v2/artifacts/${IMPORTED_RESPONSE_ARTIFACT_ID}" 404
request GET "/api/v2/transactions?session_id=${SESSION_ID}" 200
assert_json 'length == 1 and .[0].status_code == 200' 'transaction deletion removed plugin traffic or retained imported traffic'
request GET "/api/v2/targets/${URL_TARGET_ID}/urls" 200
assert_json 'length == 1' 'transaction deletion removed the deduplicated URL catalog'

cli_json runs create --session "${SESSION_ID}" --target "${URL_TARGET_ID}" --group web --type active --profile default
[[ $(jq -r '.run.profile' "${CLI_RESPONSE_FILE}") == 'default' ]] || fail 'CLI run did not persist its profile'
CLI_RUN_TASK_ID=$(jq -r '.tasks[0].id' "${CLI_RESPONSE_FILE}")
wait_for_task_status "${CLI_RUN_TASK_ID}" succeeded
cli_json scan --session "${SESSION_ID}" --plugin OWTF-IG-004-semi_passive \
  --input 'OWTF-IG-004-semi_passive.timeout_seconds=5' \
  --input 'OWTF-IG-004-semi_passive.user_agent=OWTF CLI' \
  "${BASE_URL}/debug/health"
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

printf '%s\n' 'Checking external plugin guidance and no-traffic execution...'
cli_json sessions create --name 'External plugin smoke session'
EXTERNAL_SESSION_ID=$(jq -r '.id' "${CLI_RESPONSE_FILE}")
cli_json scan --session "${EXTERNAL_SESSION_ID}" --plugin OWTF-IG-004-external http://127.0.0.1:1/must-not-be-requested
EXTERNAL_TASK_ID=$(jq -r '.tasks[0].id' "${CLI_RESPONSE_FILE}")
wait_for_task_status "${EXTERNAL_TASK_ID}" succeeded
request GET "/api/v2/sessions/${EXTERNAL_SESSION_ID}/targets" 200
EXTERNAL_TARGET_ID=$(jq -r '.[0].id' "${RESPONSE_FILE}")
request GET "/api/v2/targets/${EXTERNAL_TARGET_ID}/report" 200
assert_json '(.tasks | length) == 1 and (.transactions | length) == 0 and (.artifacts | length) == 0 and (.observations | length) == 1 and .observations[0].kind == "external.references" and (.observations[0].data | fromjson | (.references | length) == 2 and (.guidance | contains("identify server and framework markers")))' 'external plugin did not retain its no-traffic guidance'
request GET "/api/v2/sessions/${EXTERNAL_SESSION_ID}/export" 200
EXTERNAL_REPORT_ZIP="${TMP_DIR}/external-report.zip"
cp "${RESPONSE_FILE}" "${EXTERNAL_REPORT_ZIP}"
unzip -tqq "${EXTERNAL_REPORT_ZIP}" || fail 'external plugin report ZIP is invalid'
unzip -p "${EXTERNAL_REPORT_ZIP}" index.html | grep -q 'OWASP WSTG - Fingerprint Web Server' || fail 'external references are missing from the offline report'
request DELETE "/api/v2/sessions/${EXTERNAL_SESSION_ID}" 204
request GET "/api/v2/sessions/${EXTERNAL_SESSION_ID}" 404

printf '%s\n' 'Checking transaction grep evidence and report links...'
request POST /api/v2/sessions 201 '{"name":"Grep plugin smoke session"}'
GREP_SESSION_ID=$(jq -r '.id' "${RESPONSE_FILE}")
request POST "/api/v2/sessions/${GREP_SESSION_ID}/targets" 200 '{"targets":["https://grep.example.test"]}'
GREP_TARGET_ID=$(jq -r '.created[0].id' "${RESPONSE_FILE}")
GREP_HAR="${TMP_DIR}/grep.har"
cat >"${GREP_HAR}" <<'JSON'
{"log":{"version":"1.2","entries":[{
  "startedDateTime":"2026-09-02T10:11:12Z","time":4,
  "request":{"method":"GET","url":"https://grep.example.test/","headers":[]},
  "response":{"status":200,"headers":[{"name":"Server","value":"Caddy"}],"content":{"mimeType":"text/html","text":"<meta name=\"generator\" content=\"OWTF\">"}}
}]}}
JSON
upload_har "${GREP_TARGET_ID}" "${GREP_HAR}" 201
GREP_TRANSACTION_ID=$(jq -r '.transactions[0].id' "${RESPONSE_FILE}")
cli_json runs create --session "${GREP_SESSION_ID}" --target "${GREP_TARGET_ID}" --plugin OWTF-IG-004-grep
GREP_TASK_ID=$(jq -r '.tasks[0].id' "${CLI_RESPONSE_FILE}")
wait_for_task_status "${GREP_TASK_ID}" succeeded
request GET "/api/v2/targets/${GREP_TARGET_ID}/report" 200
assert_json '(.tasks | length) == 1 and (.transactions | length) == 1 and (.observations | length) == 2 and all(.observations[]; .kind == "grep.matches" and ((.data | fromjson).transaction_ids == [$transaction]))' 'grep output is not linked to the captured transaction' --arg transaction "${GREP_TRANSACTION_ID}"
request GET "/api/v2/sessions/${GREP_SESSION_ID}/export" 200
GREP_REPORT_ZIP="${TMP_DIR}/grep-report.zip"
cp "${RESPONSE_FILE}" "${GREP_REPORT_ZIP}"
unzip -tqq "${GREP_REPORT_ZIP}" || fail 'grep report ZIP is invalid'
unzip -p "${GREP_REPORT_ZIP}" index.html | grep -q "href=\"#transaction-${GREP_TRANSACTION_ID}\"" || fail 'grep observation is not linked in the offline report'
request DELETE "/api/v2/sessions/${GREP_SESSION_ID}" 204
request GET "/api/v2/sessions/${GREP_SESSION_ID}" 404

printf '%s\n' 'Checking destructive cleanup and final empty state...'
cli_json targets add --session "${SESSION_ID}" 198.51.100.9
CLI_TARGET_ID=$(jq -r '.created[0].id' "${CLI_RESPONSE_FILE}")
cli_json targets delete "${CLI_TARGET_ID}"
jq -e --arg id "${CLI_TARGET_ID}" '.deleted == [$id]' "${CLI_RESPONSE_FILE}" >/dev/null || fail 'CLI target deletion is incorrect'
cli_json sessions create --name 'CLI smoke session'
jq -e '.name == "CLI smoke session"' "${CLI_RESPONSE_FILE}" >/dev/null || fail 'CLI session creation failed'
CLI_SESSION_ID=$(jq -r '.id' "${CLI_RESPONSE_FILE}")
cli_json targets add --session "${CLI_SESSION_ID}" https://disposable.example
CLI_SESSION_TARGET_ID=$(jq -r '.created[0].id' "${CLI_RESPONSE_FILE}")
cli_json sessions delete "${CLI_SESSION_ID}"
jq -e --arg id "${CLI_SESSION_ID}" '.deleted == [$id]' "${CLI_RESPONSE_FILE}" >/dev/null || fail 'CLI session deletion is incorrect'
request GET "/api/v2/sessions/${CLI_SESSION_ID}" 404
request GET "/api/v2/targets/${CLI_SESSION_TARGET_ID}" 404
request GET "/api/v2/sessions/${SESSION_ID}/targets" 200
TARGET_IDS=()
while IFS= read -r target_id; do TARGET_IDS+=("${target_id}"); done < <(jq -r '.[].id' "${RESPONSE_FILE}")
for target_id in "${TARGET_IDS[@]}"; do
  request DELETE "/api/v2/targets/${target_id}" 204
done
request GET "/api/v2/sessions/${SESSION_ID}/targets" 200
assert_json 'length == 0' 'targets survived deletion'
request GET "/api/v2/targets/${URL_TARGET_ID}/report" 404
request GET "/api/v2/targets/${URL_TARGET_ID}/urls" 404
request GET "/api/v2/tasks?session_id=${SESSION_ID}" 200
assert_json 'length == 0' 'tasks survived target deletion'
request GET "/api/v2/transactions?session_id=${SESSION_ID}" 200
assert_json 'length == 0' 'transactions survived target deletion'
request DELETE "/api/v2/sessions/${SESSION_ID}" 204
request GET "/api/v2/sessions/${SESSION_ID}" 404
request GET /api/v2/sessions 200
assert_json 'length == 0' 'sessions survived deletion'

printf '%s\n' 'Checking proxy traffic, proxy API, repeater, history, CA, and CLI...'
if curl --silent --fail --max-time 1 "${PROXY_API_URL}/api/v2/health" >/dev/null 2>&1; then
  fail "${PROXY_API_ADDRESS} is already serving a proxy API"
fi
"${TMP_DIR}/owtf" proxy --config "${CONFIG_FILE}" \
  >"${TMP_DIR}/proxy-status.json" 2>"${TMP_DIR}/proxy.log" &
PROXY_PID=$!
for attempt in $(seq 1 100); do
  if curl --silent --fail --max-time 1 "${PROXY_API_URL}/api/v2/health" >/dev/null 2>&1; then
    break
  fi
  if ! kill -0 "${PROXY_PID}" 2>/dev/null; then
    cat "${TMP_DIR}/proxy.log" >&2
    fail 'proxy exited during startup'
  fi
  sleep 0.05
done
jq -e --arg proxy "${PROXY_ADDRESS}" --arg api "${PROXY_API_ADDRESS}" \
  '.listen == $proxy and .api == $api' "${TMP_DIR}/proxy-status.json" >/dev/null || fail 'proxy startup status is incorrect'

curl --silent --show-error --fail --max-time 10 --noproxy '' --proxy "${PROXY_URL}" \
  "${BASE_URL}/debug/health" >"${RESPONSE_FILE}"
assert_json '.status == "ok"' 'curl traffic did not pass through the proxy'

INTERCEPTOR_PAYLOAD=$(jq -nc '{rules:[{
  name:"runtime-response", phase:"response",
  match:{url_pattern:"debug/health",content_types:["application/json"]},
  action:{body_replace:[{pattern:"\"ok\"",replacement:"\"intercepted\""}]}
}]}')
request_status=$(curl --silent --show-error --max-time 10 --request PUT \
  --header 'Content-Type: application/json' --data "${INTERCEPTOR_PAYLOAD}" \
  --output "${RESPONSE_FILE}" --write-out '%{http_code}' "${PROXY_API_URL}/api/v2/interceptors")
[[ "${request_status}" == 200 ]] || fail "proxy interceptor replacement returned ${request_status}: $(cat "${RESPONSE_FILE}")"
assert_json '(.rules | length) == 1 and .rules[0].name == "runtime-response"' 'runtime interceptor replacement is incorrect'
proxy_cli_json interceptors list
jq -e '(.rules | length) == 1 and .rules[0].name == "runtime-response"' "${CLI_RESPONSE_FILE}" >/dev/null || fail 'proxy CLI interceptor list is incorrect'
proxy_cli_json interceptors disable runtime-response
jq -e '.name == "runtime-response" and .enabled == false' "${CLI_RESPONSE_FILE}" >/dev/null || fail 'proxy CLI did not disable the interceptor'
proxy_cli_json interceptors enable runtime-response
jq -e '.name == "runtime-response" and .enabled == true' "${CLI_RESPONSE_FILE}" >/dev/null || fail 'proxy CLI did not enable the interceptor'

REPEAT_PAYLOAD=$(jq -nc --arg url "${BASE_URL}/debug/health" '{method:"GET",url:$url}')
request_status=$(curl --silent --show-error --max-time 10 \
  --request POST --header 'Content-Type: application/json' --data "${REPEAT_PAYLOAD}" \
  --output "${RESPONSE_FILE}" --write-out '%{http_code}' "${PROXY_API_URL}/api/v2/repeater")
[[ "${request_status}" == 200 ]] || fail "proxy repeater returned ${request_status}: $(cat "${RESPONSE_FILE}")"
assert_json '.status_code == 200 and .truncated == false and (.body_base64 | @base64d | fromjson | .status == "intercepted")' 'runtime interceptor did not transform repeater traffic'
request_status=$(curl --silent --show-error --max-time 10 --request PUT \
  --header 'Content-Type: application/json' --data '{"rules":[{"name":"broken","phase":"request","match":{"url_pattern":"["},"action":{}}]}' \
  --output "${RESPONSE_FILE}" --write-out '%{http_code}' "${PROXY_API_URL}/api/v2/interceptors")
[[ "${request_status}" == 400 ]] || fail "invalid proxy interceptor replacement returned ${request_status}"
curl --silent --show-error --fail --max-time 10 "${PROXY_API_URL}/api/v2/interceptors" >"${RESPONSE_FILE}"
assert_json '(.rules | length) == 1 and .rules[0].name == "runtime-response" and .rules[0].enabled == true' 'invalid replacement changed active interceptors'
printf '%s\n' '{"rules":[]}' >"${EMPTY_INTERCEPTORS}"
proxy_cli_json interceptors replace "${EMPTY_INTERCEPTORS}"
jq -e '(.rules | length) == 0' "${CLI_RESPONSE_FILE}" >/dev/null || fail 'proxy CLI did not replace interceptors'

curl --silent --show-error --fail --max-time 10 \
  "${PROXY_API_URL}/api/v2/transactions?method=GET&status=200&url=debug%2Fhealth&limit=10" >"${RESPONSE_FILE}"
assert_json 'length == 2 and all(.[]; .method == "GET" and .status_code == 200)' 'proxy transaction filtering is incorrect'
curl --silent --show-error --fail --max-time 10 \
  "${PROXY_API_URL}/api/v2/transactions/1" >"${RESPONSE_FILE}"
assert_json '.id == 1 and .response_body_base64 != ""' 'proxy transaction detail is incomplete'
curl --silent --show-error --fail --max-time 10 \
  "${PROXY_API_URL}/api/v2/transactions/stats" >"${RESPONSE_FILE}"
assert_json '.total == 2 and .methods.GET == 2 and .statuses["200"] == 2' 'proxy transaction stats are incorrect'
curl --silent --show-error --fail --max-time 10 \
  "${PROXY_API_URL}/api/v2/ca" >"${TMP_DIR}/downloaded-ca.crt"
cmp -s "${PROXY_CA}" "${TMP_DIR}/downloaded-ca.crt" || fail 'proxy CA download differs from generated CA'

proxy_cli_json status
jq -e '.status == "ok"' "${CLI_RESPONSE_FILE}" >/dev/null || fail 'proxy CLI status is incorrect'
proxy_cli_json transactions --url debug/health --limit 10
jq -e 'length == 2' "${CLI_RESPONSE_FILE}" >/dev/null || fail 'proxy CLI transactions are incorrect'
proxy_cli_json transaction 1
jq -e '.id == 1 and .status_code == 200' "${CLI_RESPONSE_FILE}" >/dev/null || fail 'proxy CLI transaction detail is incorrect'
proxy_cli_json stats
jq -e '.total == 2' "${CLI_RESPONSE_FILE}" >/dev/null || fail 'proxy CLI stats are incorrect'
proxy_cli_json repeat "${BASE_URL}/debug/health"
jq -e '.status_code == 200 and (.body_base64 | @base64d | fromjson | .status == "ok")' "${CLI_RESPONSE_FILE}" >/dev/null || fail 'proxy CLI repeater is incorrect'
proxy_cli_json ca --output "${TMP_DIR}/cli-proxy-ca.crt"
cmp -s "${PROXY_CA}" "${TMP_DIR}/cli-proxy-ca.crt" || fail 'proxy CLI CA differs from generated CA'

request_status=$(curl --silent --show-error --max-time 10 --request DELETE \
  --output "${RESPONSE_FILE}" --write-out '%{http_code}' "${PROXY_API_URL}/api/v2/transactions")
[[ "${request_status}" == 200 ]] || fail "proxy clear returned ${request_status}: $(cat "${RESPONSE_FILE}")"
assert_json '.removed == 3' 'proxy history clear count is incorrect'
proxy_cli_json stats
jq -e '.total == 0' "${CLI_RESPONSE_FILE}" >/dev/null || fail 'proxy history survived clear'

kill "${PROXY_PID}"
wait "${PROXY_PID}"
PROXY_PID=""
jq -e '.log.entries | length == 0' "${PROXY_HAR}" >/dev/null || fail 'cleared proxy history remained in shutdown HAR'

printf '%s\n' 'PASS: curl API smoke test completed.'
