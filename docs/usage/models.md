# Model qualification

AI support begins with an explicit, CLI-only provider check. It is not an agent,
scanner, report writer, or finding validator. Existing OWTF workflows do not need
a model or credentials and make no model requests automatically.

OWTF uses [Fantasy](https://github.com/charmbracelet/fantasy), pinned in `go.mod`.
The backend remains Go; the frontend remains a separate application. Fantasy
v0.43.0 requires Go 1.27, including the backend container and CI toolchain.

## Configure connections and aliases

Add an `ai` section to an OWTF configuration file. Model IDs are chosen by the
operator, not hardcoded into OWTF. The IDs below are placeholders to replace with
models available through your provider account or local server.

```yaml
apiVersion: owtf.dev/v1alpha1
kind: Config
ai:
  providers:
    cloud:
      protocol: anthropic
      apiKeyEnv: OWTF_ANTHROPIC_KEY
    local:
      protocol: openaicompat
      baseURL: http://127.0.0.1:11434/v1
  models:
    review:
      provider: cloud
      model: your-anthropic-model-id
    local-review:
      provider: local
      model: your-installed-model-id
  defaultModel: local-review
  timeoutSeconds: 30
  maxOutputTokens: 1024
```

Supported protocols in this phase:

| Protocol | Default endpoint | Credential reference |
| --- | --- | --- |
| `openai` | `https://api.openai.com/v1` (Chat Completions) | Required `apiKeyEnv` |
| `anthropic` | `https://api.anthropic.com` (Messages) | Required `apiKeyEnv` |
| `google` | `https://generativelanguage.googleapis.com` (Gemini API) | Required `apiKeyEnv` |
| `openaicompat` | Explicit `baseURL` required | Optional `apiKeyEnv` |

Native Bedrock, Vertex, Azure credentials, the OpenAI Responses API, and other
provider-specific features are not implemented here. Compatible gateways can use
`openaicompat`; compatibility is something to check, not a guarantee that every
model supports tools. Models without tool calling will fail this check. That does
not imply they are unusable for every future read-only task.

Endpoints require HTTPS except on loopback. URL credentials, query strings, and
fragments are rejected. There is deliberately no YAML field for a literal key.
The referenced environment variable is read only for `models check`; ambient SDK
credential variables are not implicitly used. This command bypasses HTTP_PROXY
and HTTPS_PROXY so credentials do not enter OWTF's traffic capture by accident.
It does not currently support an explicit corporate egress proxy.

## Run

```sh
./build/owtf config validate /path/to/config.yaml
./build/owtf models list --config /path/to/config.yaml
./build/owtf models check --config /path/to/config.yaml --model local-review
```

`list` is offline, sorted by alias, and does not require credentials or an OWTF
server. `check` can incur provider charges. It sends only generated test values
and a fixed prompt, never targets, reports, files, or HTTP transactions. Both
commands print JSON; failure exits nonzero without printing a success object.
There is no provider-check HTTP endpoint in the unauthenticated OWTF API.

The check requires exactly one call to an in-memory `echo_probe` tool. After
validating the tool arguments, OWTF supplies a **new** nonce and requires the model
to return it in a strict JSON object. Extra fields, duplicate fields, wrong values,
additional tool calls, incomplete responses, and markdown wrappers fail.

Limits apply to the entire check: two HTTP requests, one deadline (30 seconds by
default, at most 120), bounded output tokens per call (1024 by default, at most
4096), and an 8 MiB decompressed response limit per request. Cancellation stops the
current request. No automatic retry, redirect, alternate provider, or fallback
model is allowed. Provider response bodies and raw SDK errors are not printed.

## What passing means

`tool_round_trip: true` and `validated_json: true` mean this invocation completed
the probe. They do **not** certify native JSON-schema enforcement, streaming,
multimodal input, reasoning quality, vulnerability detection, or safe autonomous
operation. The result is not persisted as a permanent capability flag. Token
usage and cost are omitted rather than presenting missing data as zero.

Local HTTP fixtures exercise the real Fantasy provider serializers and parsers
for all four protocols, including cancellation and failure behavior. They are not
live commercial-provider tests. Run `models check` with your chosen models before
using them in a later AI workflow.

A regression test covers Fantasy v0.43.0 panicking on Gemini responses without
usage metadata. OWTF contains third-party response-processing panics at the SDK
call boundary and returns a failed check, never a partial success.
