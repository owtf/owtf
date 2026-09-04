Compose verification and recovery
=================================

Run ``make test-compose`` to build the shipped image and verify a fresh deployment.
The check creates unique Compose projects and volumes, performs a local HTTP scan,
cancels an active command and checks child cleanup, reviews output, exports a report,
restarts the service, then restores a stopped-volume backup into a fresh volume.
It compares reports and verifies every exported artifact against its SHA-256.
Only test-owned projects and volumes are removed. Evidence remains under
``build/compose-proof.*`` and CI uploads it for seven days.

Manual CLI walkthrough
----------------------

Run ``make demo-cli`` to perform the same check and leave the restored deployment
running at ``http://127.0.0.1:18209``. Override ``OWTF_PROOF_PORT`` if needed.
The final output names a directory containing ``cli``, ``demo.env``, the backup,
and before/after reports. Set ``PROOF`` to that printed directory::

  PROOF=/absolute/path/to/build/compose-proof.XXXXXX
  source "$PROOF/demo.env"
  "$PROOF/cli" plugin list --group web --type active
  "$PROOF/cli" sessions list
  "$PROOF/cli" targets list --session "$SESSION"
  "$PROOF/cli" worklist --session "$SESSION"
  "$PROOF/cli" workers
  "$PROOF/cli" tasks logs "$TASK"
  "$PROOF/cli" sessions report --disposition confirmed "$SESSION"
  "$PROOF/cli" scan --session "$SESSION" --plugin OWTF-WSP-001-active http://127.0.0.1:8009/debug/health

The scan URL refers to OWTF inside its container. It contacts only that local
health endpoint. The additional sleep plugin is a cancellation test fixture,
not part of the shipped catalog. Startup and plugin lists have terminal styling;
other command responses currently remain JSON even in human mode.

The standard image runs built-in HTTP, grep, external, and available command
plugins. Container-tool plugins show missing requirements because this service
does not include a Docker client or engine connection. The recovery check does
not establish Kali scanner execution support inside this Compose deployment.

The generated ``cli`` wrapper executes the container's Linux binary, so no host
Go or Python installation is needed. Stop the demo and remove its test volume::

  docker compose -p "$PROJECT" -f docker/docker-compose.yml -f "$PROOF/compose.yaml" down -v

Use ``docker-compose`` in place of ``docker compose`` on older installations.

Backing up a deployment
-----------------------

Stop the service before copying its entire data volume so SQLite and artifacts
belong to the same snapshot. A report ZIP is an export, not a database backup.
Keep the image version, Compose configuration, and any custom plugins, profiles,
and wordlists alongside the backup. With the standard project name ``owtf``::

  docker compose -p owtf -f docker/docker-compose.yml stop owtf
  docker compose -p owtf -f docker/docker-compose.yml run --rm --no-deps -T --entrypoint tar owtf -C /data -czf - . > owtf-data.tar.gz
  docker compose -p owtf -f docker/docker-compose.yml start owtf

Check command success before treating the archive as a backup. This captures all
of ``/data``, including SQLite and artifact files. Files held outside that volume,
such as separately configured proxy captures or CA keys, must be backed up separately.
Active tasks are interrupted by shutdown; perform backups when work is idle.

Restoring into a fresh deployment
---------------------------------

Use the same image version and an unused project name. Do not extract over a
running or populated data volume::

  docker compose -p owtf-restored -f docker/docker-compose.yml run --rm --no-deps -T --user root --entrypoint tar owtf -C /data -xzf - < owtf-data.tar.gz
  OWTF_PORT=18209 docker compose -p owtf-restored -f docker/docker-compose.yml up -d --no-build
  docker compose -p owtf-restored -f docker/docker-compose.yml exec owtf owtf --url http://127.0.0.1:8009 sessions list

Extraction runs as root to restore the archived file ownership; OWTF itself runs
as UID 10001. Inspect reports and exported artifacts before using the restored
instance for new work. Port binding defaults to loopback; ``OWTF_BIND`` and
``OWTF_PORT`` configure the published address, and ``OWTF_IMAGE`` selects an image.
