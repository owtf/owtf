#!/usr/bin/env bash
# Exercise the shipped image, then restore its stopped data volume into a new deployment.
set -euo pipefail
ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$ROOT"
KEEP=false
if [[ ${1:-} == --keep ]]; then KEEP=true; shift; fi
[[ $# == 0 ]] || { echo 'Usage: scripts/owtf-compose-smoke.sh [--keep]' >&2; exit 1; }
if docker compose version >/dev/null 2>&1; then COMPOSE=(docker compose); else COMPOSE=(docker-compose); fi
for tool in docker curl jq unzip openssl awk diff; do command -v "$tool" >/dev/null; done
PROJECT="owtf-proof-$$"
RESTORED="${PROJECT}-restored"
mkdir -p "$ROOT/build"
PROOF=$(mktemp -d "$ROOT/build/compose-proof.XXXXXX")
export OWTF_PORT=${OWTF_PROOF_PORT:-18209}
URL="http://127.0.0.1:${OWTF_PORT}"
OVERRIDE="$PROOF/compose.yaml"
PASSED=false
compose() { "${COMPOSE[@]}" -p "$PROJECT" -f "$ROOT/docker/docker-compose.yml" -f "$OVERRIDE" "$@"; }
restore() { "${COMPOSE[@]}" -p "$RESTORED" -f "$ROOT/docker/docker-compose.yml" -f "$OVERRIDE" "$@"; }
cleanup() {
  if ! $PASSED; then compose logs --no-color >"$PROOF/failure.log" 2>&1 || true; restore logs --no-color >>"$PROOF/failure.log" 2>&1 || true; fi
  compose down -v >/dev/null 2>&1 || true
  if ! $KEEP || ! $PASSED; then restore down -v >/dev/null 2>&1 || true; fi
  echo "Evidence: $PROOF"
}
trap cleanup EXIT
trap 'exit 130' INT TERM
mkdir -p "$PROOF/cancellation"
cat >"$PROOF/cancellation/plugin.yaml" <<'YAML'
apiVersion: owtf.dev/v1alpha1
kind: Plugin
metadata:
  id: OWTF-SMOKE-001-active
  version: 0.1.0
  title: Cancellation test fixture
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
      args: ["60"]
YAML
cat >"$OVERRIDE" <<YAML
services:
  owtf:
    volumes:
      - "$PROOF/cancellation:/app/plugins/auxiliary/OWTF-SMOKE-001/active:ro"
YAML
wait_health() {
  for attempt in $(seq 1 60); do
    if curl -fsS --max-time 2 "$URL/api/v2/health" >"$PROOF/health.json" 2>/dev/null; then return; fi
    sleep 1
  done
  echo 'OWTF did not become healthy' >&2; exit 1
}
cli() { compose exec -T owtf owtf --url http://127.0.0.1:8009 --json "$@"; }
wait_task() {
  local id=$1 wanted=$2
  for attempt in $(seq 1 100); do
    curl -fsS --max-time 3 "$URL/api/v2/tasks/$id" >"$PROOF/task.json"
    [[ $(jq -r .status "$PROOF/task.json") == "$wanted" ]] && return
    sleep 0.1
  done
  cat "$PROOF/task.json" >&2; exit 1
}
echo 'Starting a fresh Compose deployment...'
compose up -d --no-build
wait_health
cli sessions create --name 'Compose recovery demonstration' >"$PROOF/session.json"
SESSION=$(jq -r .id "$PROOF/session.json")
cli targets add --session "$SESSION" http://127.0.0.1:8009/debug/health >"$PROOF/targets.json"
TARGET=$(jq -r '.created[0].id' "$PROOF/targets.json")
cli runs create --session "$SESSION" --target "$TARGET" --plugin OWTF-WSP-001-active >"$PROOF/run.json"
TASK=$(jq -r '.tasks[0].id' "$PROOF/run.json")
wait_task "$TASK" succeeded
cli plugin review --disposition confirmed --rank informational --notes 'Verified against the local Compose health endpoint.' "$TASK" >"$PROOF/review.json"
echo 'Checking active cancellation and process cleanup...'
cli runs create --session "$SESSION" --target "$TARGET" --plugin OWTF-SMOKE-001-active >"$PROOF/cancel-run.json"
CANCEL=$(jq -r '.tasks[0].id' "$PROOF/cancel-run.json")
wait_task "$CANCEL" running
child_started=false
for attempt in $(seq 1 50); do
  if compose exec -T owtf sh -c 'for file in /proc/[0-9]*/comm; do if [ "$(cat "$file" 2>/dev/null)" = sleep ]; then exit 0; fi; done; exit 1'; then
    child_started=true
    break
  fi
  sleep 0.1
done
$child_started || { echo 'Cancellation fixture never started its child process' >&2; exit 1; }
cli tasks cancel "$CANCEL" >"$PROOF/cancel.json"
wait_task "$CANCEL" cancelled
# A cancelled task must not leave the sleep child alive in the container.
compose exec -T owtf sh -c 'for file in /proc/[0-9]*/comm; do if [ "$(cat "$file" 2>/dev/null)" = sleep ]; then exit 1; fi; done'
cli sessions report "$SESSION" >"$PROOF/before.json"
jq -e '.summary.tasks == 2 and .summary.succeeded == 1 and .summary.cancelled == 1 and .summary.artifacts > 0 and (.plugin_output_review_events | length) == 1' "$PROOF/before.json" >/dev/null
curl -fsS "$URL/api/v2/sessions/$SESSION/export" >"$PROOF/before.zip"
unzip -tqq "$PROOF/before.zip"
echo 'Checking restart persistence...'
compose restart owtf
wait_health
cli sessions report "$SESSION" >"$PROOF/restarted.json"
diff -u <(jq -S . "$PROOF/before.json") <(jq -S . "$PROOF/restarted.json")
echo 'Backing up the stopped volume and restoring into a fresh volume...'
compose stop owtf
compose run --rm --no-deps -T --entrypoint tar owtf -C /data -czf - . >"$PROOF/data.tar.gz"
restore run --rm --no-deps -T --user root --entrypoint tar owtf -C /data -xzf - <"$PROOF/data.tar.gz"
restore up -d --no-build
wait_health
curl -fsS "$URL/api/v2/sessions/$SESSION/report" >"$PROOF/restored.json"
diff -u <(jq -S . "$PROOF/before.json") <(jq -S . "$PROOF/restored.json")
curl -fsS "$URL/api/v2/sessions/$SESSION/export" >"$PROOF/restored.zip"
unzip -tqq "$PROOF/restored.zip"
mkdir "$PROOF/export"
unzip -q "$PROOF/restored.zip" -d "$PROOF/export"
# Compare every archived file against its retained SHA-256, including report links.
while IFS=$'\t' read -r id hash; do
  file=$(jq -r --arg id "$id" '.artifact_files[$id]' "$PROOF/export/manifest.json")
  [[ "$file" == artifacts/* && -f "$PROOF/export/$file" ]]
  actual=$(openssl dgst -sha256 "$PROOF/export/$file" | awk '{print $NF}')
  [[ "$actual" == "$hash" ]]
  grep -Fq "$file" "$PROOF/export/index.html"
done < <(jq -r '.artifacts[] | [.id,.sha256] | @tsv' "$PROOF/restored.json")
restore exec -T owtf owtf --url http://127.0.0.1:8009 --human plugin list --group web --type active >"$PROOF/cli-preview.txt"
cat >"$PROOF/cli" <<SH
#!/usr/bin/env bash
tty_args=()
if [[ ! -t 0 || ! -t 1 ]]; then tty_args=(-T); fi
exec ${COMPOSE[*]} -p "$RESTORED" -f "$ROOT/docker/docker-compose.yml" -f "$OVERRIDE" exec "\${tty_args[@]}" owtf owtf --url http://127.0.0.1:8009 --human "\$@"
SH
chmod +x "$PROOF/cli"
printf 'URL=%s\nSESSION=%s\nTARGET=%s\nTASK=%s\nPROJECT=%s\n' "$URL" "$SESSION" "$TARGET" "$TASK" "$RESTORED" >"$PROOF/demo.env"
PASSED=true
printf 'PASS: Compose lifecycle, cancellation, restart, backup, restore, and artifact hashes.\n'
if $KEEP; then printf 'Try: %s/cli sessions list\n' "$PROOF"; fi
