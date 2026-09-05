import { useState } from "react";
import { request, useAction } from "../lib/api";
import { Button, ErrorMessage } from "./shared";
import { Input } from "./ui/input";
import { Textarea } from "./ui/textarea";

interface RequestDraft {
  method: string;
  url: string;
  headers: Record<string, string[]>;
  body_base64: string;
}
interface Response {
  status_code: number;
  headers: Record<string, string[]>;
  body_base64: string;
  truncated: boolean;
  duration_ms: number;
}

export default function Repeater({ initial }: { initial: RequestDraft }) {
  const [method, setMethod] = useState(initial.method);
  const [url, setURL] = useState(initial.url);
  const [headers, setHeaders] = useState(
    JSON.stringify(initial.headers, null, 2),
  );
  const [body, setBody] = useState(initial.body_base64);
  const [response, setResponse] = useState<Response | null>(null);
  const send = useAction(async () => {
    setResponse(null);
    const parsed: unknown = JSON.parse(headers);
    if (
      !parsed ||
      typeof parsed !== "object" ||
      Array.isArray(parsed) ||
      !Object.values(parsed).every(
        (value) =>
          Array.isArray(value) &&
          value.every((item) => typeof item === "string"),
      )
    ) {
      throw new Error("Headers must be a JSON object with arrays of strings");
    }
    setResponse(
      await request<Response>("/proxy/repeater", "POST", {
        method,
        url,
        headers: parsed,
        body_base64: body,
      }),
    );
  });
  return (
    <form
      onSubmit={(event) => {
        event.preventDefault();
        send.mutate(undefined);
      }}
    >
      <h3>Repeater</h3>
      <p className="muted">
        Send makes a new network request. It is not automatically retried. Only
        send to targets you are authorized to test.
      </p>
      <fieldset className="stack" disabled={send.isPending}>
        <div className="request-address">
          <label>
            Method
            <Input
              required
              value={method}
              onChange={(event) => setMethod(event.target.value)}
            />
          </label>
          <label>
            URL
            <Input
              required
              type="url"
              value={url}
              onChange={(event) => setURL(event.target.value)}
            />
          </label>
        </div>
        <label>
          Headers (JSON, values are arrays)
          <Textarea
            rows={6}
            value={headers}
            onChange={(event) => setHeaders(event.target.value)}
          />
        </label>
        <label>
          Request body (base64)
          <Textarea
            value={body}
            onChange={(event) => setBody(event.target.value)}
          />
        </label>
        <Button type="submit">{send.isPending ? "Sending…" : "Send"}</Button>
      </fieldset>
      <ErrorMessage error={send.error} />
      {response && (
        <section aria-label="Repeater response">
          <h3>
            Response {response.status_code} · {response.duration_ms} ms
          </h3>
          {response.truncated && (
            <p role="status">
              Response body truncated by the proxy capture limit.
            </p>
          )}
          <pre>{JSON.stringify(response.headers, null, 2)}</pre>
          <details>
            <summary>Response body (base64)</summary>
            <pre>{response.body_base64 || "Empty body"}</pre>
          </details>
        </section>
      )}
    </form>
  );
}
