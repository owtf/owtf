#!/usr/bin/env bash
# Exercise the UI-facing proxy bridge using only container-local HTTP traffic.
set -euo pipefail
IMAGE=${OWTF_IMAGE:-owtf:ui-controls-proof}
PORT=${OWTF_PROOF_PORT:-18509}
NAME="owtf-proxy-ui-proof-$$"
PROOF_ROOT=${OWTF_PROOF_ROOT:-${TMPDIR:-/tmp}}
mkdir -p "$PROOF_ROOT"
PROOF=$(mktemp -d "$PROOF_ROOT/owtf-proxy-ui.XXXXXX")
URL="http://127.0.0.1:$PORT/api/v2"
KEEP=false
[[ ${1:-} != --keep ]] || KEEP=true
cleanup() {
  docker logs "$NAME" >"$PROOF/server.log" 2>&1 || true
  if ! $KEEP; then docker rm -f "$NAME" >/dev/null 2>&1 || true; fi
  echo "Evidence: $PROOF"
  echo "Container: $NAME"
}
trap cleanup EXIT
for tool in docker curl jq; do command -v "$tool" >/dev/null; done
docker run -d --name "$NAME" -p "127.0.0.1:$PORT:8009" "$IMAGE" >/dev/null
for _ in {1..60}; do
  if curl -fsS "$URL/health" >"$PROOF/health.json" 2>/dev/null; then break; fi
  sleep 1
done
curl -fsS "$URL/config" >"$PROOF/config.json"
jq -e '.server.workers == 1' "$PROOF/config.json" >/dev/null
curl -fsS -H 'Content-Type: application/json' -d '{"yaml":"apiVersion: owtf.dev/v1alpha1\nkind: Config\n"}' "$URL/config/validate" | jq -e '.valid' >/dev/null
docker exec -d "$NAME" sh -c 'echo $$ >/data/proxy.pid; exec owtf proxy --attempts 1 --ca-cert /data/ca.crt --ca-key /data/ca.key --output /data/capture.har >/data/proxy.log 2>&1'
for _ in {1..30}; do
  if curl -fsS "$URL/proxy/health" >"$PROOF/proxy-health.json" 2>/dev/null; then break; fi
  sleep 1
done
curl -fsS "$URL/proxy/ca" >"$PROOF/ca.crt"
grep -q 'BEGIN CERTIFICATE' "$PROOF/ca.crt"
configure() {
  curl -fsS -X PUT -H 'Content-Type: application/json' -d "$1" "$URL/proxy/interception" >"$PROOF/interception.json"
}
client() {
  docker exec "$NAME" curl --noproxy '' --max-time 20 -sS -x http://127.0.0.1:8008 -o /data/client-body -w '%{http_code}' "http://127.0.0.1:8009/api/v2/health?case=$1" >"$PROOF/client-status" 2>"$PROOF/client-error" &
  CLIENT=$!
}
pending() {
  for _ in {1..50}; do
    curl -fsS "$URL/proxy/interception/pending" >"$PROOF/pending.json"
    ID=$(jq -r '.[0].id // empty' "$PROOF/pending.json")
    if [[ -n $ID ]]; then return; fi
    sleep .1
  done
  echo 'No paused exchange' >&2; exit 1
}
configure '{"enabled":true,"requests":true,"responses":false,"timeout_ms":10000}'
client request
pending
curl -fsS "$URL/proxy/interception/pending/$ID" >"$PROOF/request.json"
curl -fsS -H 'Content-Type: application/json' -d '{}' "$URL/proxy/interception/pending/$ID/continue" >"$PROOF/continued.json"
wait "$CLIENT"
[[ $(cat "$PROOF/client-status") == 200 ]]
configure '{"enabled":true,"requests":false,"responses":true,"timeout_ms":10000}'
client response
pending
curl -fsS -H 'Content-Type: application/json' -d '{"status_code":202,"body_base64":"cHJvb2Y="}' "$URL/proxy/interception/pending/$ID/continue" >"$PROOF/edited.json"
wait "$CLIENT"
[[ $(cat "$PROOF/client-status") == 202 ]]
[[ $(docker exec "$NAME" cat /data/client-body) == proof ]]
configure '{"enabled":true,"requests":true,"responses":false,"timeout_ms":10000}'
client drop
pending
curl -fsS -X POST "$URL/proxy/interception/pending/$ID/drop" >"$PROOF/dropped.json"
wait "$CLIENT" || true
[[ $(cat "$PROOF/client-status") != 200 ]]
configure '{"enabled":true,"requests":true,"responses":false,"timeout_ms":200}'
client timeout
wait "$CLIENT"
[[ $(cat "$PROOF/client-status") == 200 ]]
configure '{"enabled":false,"requests":true,"responses":false,"timeout_ms":10000}'
curl -fsS -X PUT -H 'Content-Type: application/json' \
  -d '{"rules":[{"name":"proof-header","phase":"response","priority":1,"action":{"set_headers":{"X-OWTF-Proof":"enabled"}}}]}' \
  "$URL/proxy/interceptors" >"$PROOF/rules.json"
docker exec "$NAME" curl --noproxy '' --max-time 20 -fsS -D - -o /dev/null \
  -x http://127.0.0.1:8008 'http://127.0.0.1:8009/api/v2/health?case=rule-on' >"$PROOF/rule-on.headers"
grep -qi '^X-OWTF-Proof: enabled' "$PROOF/rule-on.headers"
curl -fsS -X PATCH -H 'Content-Type: application/json' \
  -d '{"name":"proof-header","enabled":false}' "$URL/proxy/interceptors" >"$PROOF/rule-disabled.json"
docker exec "$NAME" curl --noproxy '' --max-time 20 -fsS -D - -o /dev/null \
  -x http://127.0.0.1:8008 'http://127.0.0.1:8009/api/v2/health?case=rule-off' >"$PROOF/rule-off.headers"
if grep -qi '^X-OWTF-Proof:' "$PROOF/rule-off.headers"; then
  echo 'Disabled rule still changed traffic' >&2; exit 1
fi
curl -fsS -X PUT -H 'Content-Type: application/json' -d '{"rules":[]}' \
  "$URL/proxy/interceptors" >"$PROOF/rules-cleared.json"
curl -fsS "$URL/proxy/transactions/stats" >"$PROOF/stats.json"
jq -e '.total >= 3' "$PROOF/stats.json" >/dev/null
docker exec "$NAME" sh -c 'kill -TERM "$(cat /data/proxy.pid)"'
for _ in {1..50}; do
  if docker exec "$NAME" test -s /data/capture.har; then break; fi
  sleep .1
done
docker cp "$NAME:/data/capture.har" "$PROOF/capture.har" >/dev/null
SESSION=$(curl -fsS -H 'Content-Type: application/json' -d '{"name":"HAR lifecycle proof"}' "$URL/sessions" | jq -er '.id')
TARGET=$(curl -fsS -H 'Content-Type: application/json' -d '{"targets":["http://127.0.0.1:8009/api/v2/health"]}' "$URL/sessions/$SESSION/targets" | jq -er '.created[0].id')
curl -fsS -F "har=@$PROOF/capture.har" "$URL/targets/$TARGET/transactions/import" >"$PROOF/import.json"
jq -e '.imported > 0' "$PROOF/import.json" >/dev/null
curl -fsS "$URL/targets/$TARGET/transactions" >"$PROOF/imported-transactions.json"
TRANSACTION=$(jq -er '.[0].id' "$PROOF/imported-transactions.json")
curl -fsS "$URL/targets/$TARGET/transactions/$TRANSACTION" >"$PROOF/imported-detail.json"
curl -fsS -X DELETE "$URL/targets/$TARGET/transactions/$TRANSACTION" >/dev/null
[[ $(curl -sS -o /dev/null -w '%{http_code}' "$URL/targets/$TARGET/transactions/$TRANSACTION") == 404 ]]
curl -fsS -X DELETE "$URL/sessions/$SESSION" >/dev/null
[[ $(curl -sS -o /dev/null -w '%{http_code}' "$URL/sessions/$SESSION") == 404 ]]
echo 'PASS: config, CA, interception, rule effects, HAR import/show/delete, session cleanup'
