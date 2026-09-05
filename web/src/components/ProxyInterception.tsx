import { useState } from "react";
import { request, useAPI, useAction } from "../lib/api";
import { Button, Confirm, ErrorMessage, Loading } from "./shared";
import { Input } from "./ui/input";
import { Textarea } from "./ui/textarea";
import ProxyHistory from "./ProxyHistory";
import ProxyRules from "./ProxyRules";

interface LiveConfig {
  enabled: boolean;
  requests: boolean;
  responses: boolean;
  timeout_ms: number;
}
interface Pending {
  id: string;
  phase: string;
  method: string;
  url: string;
  status_code?: number;
  headers: Record<string, string[]>;
  body_base64: string;
  expires_at: string;
}

export function InterceptionEditor({
  item,
  onResolved,
}: {
  item: Pending;
  onResolved: () => void;
}) {
  const [method, setMethod] = useState(item.method);
  const [url, setURL] = useState(item.url);
  const [status, setStatus] = useState(String(item.status_code || 200));
  const originalHeaders = JSON.stringify(item.headers, null, 2);
  const [headers, setHeaders] = useState(originalHeaders);
  const [body, setBody] = useState(item.body_base64);
  const [dropping, setDropping] = useState(false);
  const resolve = useAction(async (action: "continue" | "drop") => {
    const update: Record<string, unknown> = {};
    if (action === "continue") {
      if (item.phase === "request") {
        if (method !== item.method) update.method = method;
        if (url !== item.url) update.url = url;
      } else if (status !== String(item.status_code || 200)) {
        if (!/^\d{3}$/.test(status))
          throw new Error("Status must be a three-digit HTTP code");
        update.status_code = Number(status);
      }
      if (headers !== originalHeaders) update.headers = JSON.parse(headers);
      if (body !== item.body_base64) update.body_base64 = body;
    }
    await request(
      `/proxy/interception/pending/${encodeURIComponent(item.id)}/${action}`,
      "POST",
      update,
    );
    onResolved();
  });
  return (
    <section className="transaction-inspector">
      <h3>
        {item.phase} · {item.id}
      </h3>
      <p className="muted">
        Expires {new Date(item.expires_at).toLocaleTimeString()}. Timeout
        continues the exchange unchanged.
      </p>
      <fieldset disabled={resolve.isPending} className="stack">
        {item.phase === "request" ? (
          <div className="request-address">
            <label>
              Method
              <Input
                value={method}
                onChange={(e) => setMethod(e.target.value)}
              />
            </label>
            <label>
              URL
              <Input value={url} onChange={(e) => setURL(e.target.value)} />
            </label>
          </div>
        ) : (
          <label>
            Status code
            <Input value={status} onChange={(e) => setStatus(e.target.value)} />
          </label>
        )}
        <label>
          Headers (JSON, values are arrays)
          <Textarea
            value={headers}
            onChange={(e) => setHeaders(e.target.value)}
            rows={6}
          />
        </label>
        <details>
          <summary>Body (base64)</summary>
          <p>Binary-safe replacement. An empty value clears the body.</p>
          <Textarea
            aria-label="Body base64"
            value={body}
            onChange={(e) => setBody(e.target.value)}
          />
        </details>
        <ErrorMessage error={resolve.error} />
        <div className="actions">
          <Button onClick={() => resolve.mutate("continue")}>Continue</Button>
          <Button
            variant="outline"
            onClick={() => {
              resolve.reset();
              setDropping(true);
            }}
          >
            Drop
          </Button>
        </div>
      </fieldset>
      <Confirm
        open={dropping}
        title="Drop this exchange?"
        description="The waiting connection will fail. It will not be replayed."
        busy={resolve.isPending}
        error={resolve.error}
        onClose={() => setDropping(false)}
        onConfirm={() => resolve.mutate("drop")}
      />
    </section>
  );
}

function Configuration({ initial }: { initial: LiveConfig }) {
  const [draft, setDraft] = useState(initial);
  const [confirming, setConfirming] = useState(false);
  const save = useAction(async () => {
    await request("/proxy/interception", "PUT", draft);
    setConfirming(false);
  });
  return (
    <form
      onSubmit={(event) => {
        event.preventDefault();
        setConfirming(true);
      }}
    >
      <fieldset disabled={save.isPending} className="filters">
        <label className="actions">
          <input
            type="checkbox"
            checked={draft.enabled}
            onChange={(e) => setDraft({ ...draft, enabled: e.target.checked })}
          />
          Enabled
        </label>
        <label className="actions">
          <input
            type="checkbox"
            checked={draft.requests}
            onChange={(e) => setDraft({ ...draft, requests: e.target.checked })}
          />
          Requests
        </label>
        <label className="actions">
          <input
            type="checkbox"
            checked={draft.responses}
            onChange={(e) =>
              setDraft({ ...draft, responses: e.target.checked })
            }
          />
          Responses
        </label>
        <label>
          Timeout (ms)
          <Input
            type="number"
            min={100}
            max={300000}
            required
            value={draft.timeout_ms}
            onChange={(e) =>
              setDraft({ ...draft, timeout_ms: Number(e.target.value) })
            }
          />
        </label>
        <Button
          type="submit"
          disabled={draft.enabled && !draft.requests && !draft.responses}
        >
          Apply
        </Button>
      </fieldset>
      <Confirm
        open={confirming}
        title="Change interception?"
        description="Enabling pauses matching traffic. Disabling a phase releases its waiting exchanges unchanged."
        busy={save.isPending}
        error={save.error}
        onClose={() => setConfirming(false)}
        onConfirm={() => save.mutate(undefined)}
      />
    </form>
  );
}

export default function ProxyInterception() {
  const config = useAPI<LiveConfig>("/proxy/interception", true);
  const pending = useAPI<Pending[]>(
    config.data ? "/proxy/interception/pending" : "",
    true,
  );
  const [selected, setSelected] = useState("");
  const detail = useAPI<Pending>(
    selected
      ? `/proxy/interception/pending/${encodeURIComponent(selected)}`
      : "",
  );
  return (
    <section>
      <h2>Interception</h2>
      <ErrorMessage error={config.error || pending.error || detail.error} />
      {config.isPending ? (
        <Loading />
      ) : (
        config.data && (
          <>
            <p role="status">
              Interception {config.data.enabled ? "on" : "off"}
            </p>
            <Configuration
              key={JSON.stringify(config.data)}
              initial={config.data}
            />
            <a className="button-link" href="/api/v2/proxy/ca">
              Download CA certificate
            </a>
            <h3>Paused exchanges</h3>
            {pending.data?.map((item) => (
              <div className="transaction-row" key={item.id}>
                <Button variant="ghost" onClick={() => setSelected(item.id)}>
                  {item.phase} · {item.method} {item.url}
                </Button>
                <span className="muted">
                  Expires {new Date(item.expires_at).toLocaleTimeString()}
                </span>
              </div>
            ))}
            {pending.data?.length === 0 && (
              <p className="muted">No paused exchanges.</p>
            )}
            {detail.data && (
              <InterceptionEditor
                key={detail.data.id}
                item={detail.data}
                onResolved={() => setSelected("")}
              />
            )}
            <ProxyHistory />
            <ProxyRules />
          </>
        )
      )}
    </section>
  );
}
