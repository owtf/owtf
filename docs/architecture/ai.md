# AI implementation boundary

The first increment qualifies provider integrations without changing how OWTF
executes plugins or records evidence. It uses Fantasy's low-level model API, not
its agent loop. OWTF owns deadlines, request budgets, validation, and cancellation.

## Current increment

- Named provider connections and arbitrary model aliases in existing config.
- Offline `models list` and explicit `models check` CLI commands.
- OpenAI, Anthropic, Gemini, and OpenAI-compatible HTTP protocols.
- A two-request, in-memory tool probe with strict argument/result validation.
- No retries, redirects, provider fallback, plugin execution, or target access.
- Go tests use real SDK code against local protocol fixtures, not live models.

No AI tables, account system, agent framework, Python service, or UI are added.
No model is selected by default. See [operator instructions](../usage/models.md).

Verification commands:

```sh
go test -p=1 ./...
GORACE=atexit_sleep_ms=0 go test -race -p=1 ./...
bash scripts/owtf-smoke.sh
docker build -f docker/Dockerfile.backend -t owtf:ai-qualification .
docker run --rm owtf:ai-qualification models list
```

The race runtime's exit delay is disabled because existing container-engine tests
spawn several test helpers under a two-second readiness deadline. Race detection
itself remains enabled. The container build serializes compilation and applies a
soft compiler memory limit to accommodate a 2 GiB Docker VM. None of these checks
requires a provider key. Real provider/model qualification is still an explicit
operator step and can incur charges.

## Next increments

1. Read-only target report assistance. Select bounded evidence by existing task,
   artifact, and transaction IDs; explicitly preview/redact what leaves OWTF.
   Require source references for proposed findings and preserve raw evidence.
2. Review persistence. Keep model suggestions separate from operator severity,
   disposition, and notes. Record model, prompt version, inputs, and actual tool
   activity. Do not claim access to hidden model reasoning.
3. Operator-approved worklist proposals. A model can propose existing plugins and
   inputs; OWTF validates target scope and manifests before an operator queues
   work. Existing cancellation and worker limits remain authoritative.
4. Evaluate against controlled vulnerable and non-vulnerable fixtures before
   expanding execution authority. Measure evidence correctness and false findings,
   not whether the model sounds convincing.
5. Add UI affordances to existing target report accordions and worklist controls.
   Keep CLI/API paths complete and avoid creating a parallel reporting workflow.

Target responses, scanner logs, source files, and imported reports are untrusted
content, not instructions. No network target can grant execution authority by
putting text in evidence. Model output must never become a shell command or SQL
statement. AI suggestions must not silently overwrite reviewed findings, rerun
tools, widen target scope, or select a different provider for confidential data.

This is an incremental direction, not a claim that OWTF already implements the
defense-factory workflow. Live model qualification and evidence-backed assistance
remain prerequisites before autonomous behavior is considered.
