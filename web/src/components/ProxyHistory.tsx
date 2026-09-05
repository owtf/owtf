import { useState } from "react";
import { params, request, useAPI, useAction } from "../lib/api";
import { Button, Confirm, ErrorMessage, Loading } from "./shared";
import Repeater from "./Repeater";
import Inspector from "./Inspector";
import HTTPExchange from "./HTTPExchange";
import { Input } from "./ui/input";

interface Exchange {
  id: number;
  method: string;
  url: string;
  status_code: number;
  duration_ms: number;
  request_headers: Record<string, string[]>;
  response_headers: Record<string, string[]>;
  request_body_base64: string;
  response_body_base64: string;
}

export default function ProxyHistory() {
  const [filters, setFilters] = useState({
    search: "",
    method: "",
    status: "",
    url: "",
  });
  const [offset, setOffset] = useState(0);
  const history = useAPI<Exchange[]>(
    `/proxy/transactions?${params({ ...filters, offset, limit: 21 })}`,
    true,
  );
  const stats = useAPI<{
    total: number;
    methods: Record<string, number>;
    statuses: Record<string, number>;
  }>("/proxy/transactions/stats", true);
  const [selected, setSelected] = useState<number | null>(null);
  const [clearing, setClearing] = useState(false);
  const detail = useAPI<Exchange>(
    selected ? `/proxy/transactions/${selected}` : "",
  );
  const clear = useAction(async () => {
    await request("/proxy/transactions", "DELETE");
    setSelected(null);
    setOffset(0);
    setClearing(false);
  });
  return (
    <section className="proxy-history">
      <h2>Live proxy history</h2>
      <p className="muted">
        Shared proxy traffic, not session-specific. Clearing this history does
        not delete retained target evidence.
      </p>
      {stats.data && (
        <details>
          <summary>{stats.data.total} exchanges in shared history</summary>
          <pre>
            {JSON.stringify(
              { methods: stats.data.methods, statuses: stats.data.statuses },
              null,
              2,
            )}
          </pre>
        </details>
      )}
      <div className="filters">
        {(
          [
            ["search", "Search traffic"],
            ["url", "URL contains"],
            ["method", "HTTP method"],
            ["status", "HTTP status"],
          ] as const
        ).map(([key, label]) => (
          <label key={key}>
            {label}
            <Input
              value={filters[key]}
              onChange={(event) => {
                setFilters({ ...filters, [key]: event.target.value });
                setOffset(0);
              }}
            />
          </label>
        ))}
      </div>
      <Button
        variant="outline"
        disabled={!stats.data?.total}
        onClick={() => {
          clear.reset();
          setClearing(true);
        }}
      >
        Clear history
      </Button>
      <ErrorMessage error={history.error || detail.error || stats.error} />
      {history.isPending ? (
        <Loading />
      ) : (
        history.data?.slice(0, 20).map((item) => (
          <div
            className="transaction-row"
            key={item.id}
            data-selected={selected === item.id}
          >
            <Button variant="ghost" onClick={() => setSelected(item.id)}>
              {item.method} {item.url}
            </Button>
            <span>
              {item.status_code} · {item.duration_ms} ms
            </span>
          </div>
        ))
      )}
      {history.data?.length === 0 && (
        <p className="empty">No live transactions.</p>
      )}
      <div className="actions">
        <Button
          variant="outline"
          disabled={offset === 0 || history.isFetching}
          onClick={() => setOffset(Math.max(0, offset - 20))}
        >
          Previous
        </Button>
        <Button
          variant="outline"
          disabled={
            !history.data || history.data.length <= 20 || history.isFetching
          }
          onClick={() => setOffset(offset + 20)}
        >
          Next
        </Button>
      </div>
      {detail.data && (
        <Inspector title="Live HTTP exchange" onClose={() => setSelected(null)}>
          <HTTPExchange
            key={detail.data.id}
            request={{
              line: detail.data.method + " " + detail.data.url,
              headers: detail.data.request_headers,
              body: detail.data.request_body_base64,
            }}
            response={{
              line: String(detail.data.status_code),
              headers: detail.data.response_headers,
              body: detail.data.response_body_base64,
            }}
          />
          <details key={detail.data.id}>
            <summary>Repeater</summary>
            <Repeater
              initial={{
                method: detail.data.method,
                url: detail.data.url,
                headers: detail.data.request_headers,
                body_base64: detail.data.request_body_base64,
              }}
            />
          </details>
        </Inspector>
      )}
      <Confirm
        open={clearing}
        title="Clear live proxy history?"
        description="Remove all exchanges from the shared proxy history. Retained target transactions and artifacts are unchanged."
        busy={clear.isPending}
        error={clear.error}
        onClose={() => setClearing(false)}
        onConfirm={() => clear.mutate(undefined)}
      />
    </section>
  );
}
