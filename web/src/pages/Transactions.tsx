import { useState } from "react";
import { useSearchParams } from "react-router-dom";
import { useAPI, useAction, request, params } from "../lib/api";
import type { Page, Transaction } from "../lib/types";
import {
  Button,
  Confirm,
  ErrorMessage,
  Loading,
  PageHead,
  Pager,
} from "../components/shared";
import ImportHAR from "../components/ImportHAR";
import ProxyInterception from "../components/ProxyInterception";
import CaptureTarget from "../components/CaptureTarget";
import Inspector from "../components/Inspector";
import HTTPExchange from "../components/HTTPExchange";
import { Input } from "../components/ui/input";

export default function Transactions({ session }: { session: string }) {
  const [url, setURL] = useSearchParams();
  const [importing, setImporting] = useState(false);
  const [controls, setControls] = useState(false);
  const [deleting, setDeleting] = useState<Transaction | null>(null);
  const remove = useAction(async () => {
    if (!deleting) return;
    await request(
      `/targets/${deleting.target_id}/transactions/${deleting.id}`,
      "DELETE",
    );
    if (selection?.id === deleting.id) setSelected(null);
    if (url.get("transaction") === deleting.id) {
      const next = new URLSearchParams(url);
      next.delete("transaction");
      setURL(next);
    }
    setDeleting(null);
  });
  const [search, setSearch] = useState("");
  const [method, setMethod] = useState("");
  const [status, setStatus] = useState("");
  const [offset, setOffset] = useState(0);
  const [selection, setSelected] = useState<Transaction | null>(null);
  const detail = useAPI<Transaction>(
    url.get("target") && url.get("transaction")
      ? `/targets/${encodeURIComponent(url.get("target")!)}/transactions/${encodeURIComponent(url.get("transaction")!)}`
      : "",
  );
  const selected = selection || detail.data;
  const query = useAPI<Page<Transaction>>(
    `/transactions/search?${params({ session_id: session, target_id: url.get("target") || "", search, method, status_code: status, offset, limit: 20 })}`,
    true,
  );
  const rows = query.data?.data || [];
  const selectedIndex = rows.findIndex((row) => row.id === selected?.id);
  return (
    <>
      <PageHead
        title="Proxy"
        description="Captured HTTP requests and responses. Opening evidence does not replay traffic."
      >
        <Button variant="outline" onClick={() => setImporting(true)}>
          Import HAR
        </Button>
        <Button variant="outline" onClick={() => query.refetch()}>
          Refresh
        </Button>
      </PageHead>
      <details
        open={controls}
        onToggle={(event) => {
          const open = event.currentTarget.open;
          setControls(open);
          if (open) {
            setSelected(null);
            if (url.has("transaction")) {
              const next = new URLSearchParams(url);
              next.delete("transaction");
              setURL(next);
            }
          }
        }}
      >
        <summary>Proxy controls</summary>
        {controls && (
          <>
            <CaptureTarget session={session} />
            <ProxyInterception />
          </>
        )}
      </details>
      <ErrorMessage error={detail.error} />
      <section className="proxy-history">
        <h2>Captured requests</h2>
        <div className="filters">
          <label>
            Search URL
            <Input
              value={search}
              onChange={(e) => {
                setSearch(e.target.value);
                setOffset(0);
              }}
            />
          </label>
          <label>
            Method
            <select
              value={method}
              onChange={(e) => {
                setMethod(e.target.value);
                setOffset(0);
              }}
            >
              <option value="">All methods</option>
              {[
                "GET",
                "HEAD",
                "POST",
                "PUT",
                "PATCH",
                "DELETE",
                "OPTIONS",
                "CONNECT",
              ].map((m) => (
                <option key={m}>{m}</option>
              ))}
            </select>
          </label>
          <label>
            Status code
            <Input
              type="number"
              min="100"
              max="599"
              value={status}
              onChange={(e) => {
                setStatus(e.target.value);
                setOffset(0);
              }}
              placeholder="Any"
            />
          </label>
        </div>
        <ErrorMessage error={query.error} />
        {query.isPending ? (
          <Loading />
        ) : (
          <>
            <div className="transaction-list" aria-label="Captured requests">
              {rows.map((t) => (
                <div
                  className="transaction-row"
                  data-selected={selected?.id === t.id}
                  key={t.id}
                >
                  <Button
                    variant="ghost"
                    onClick={() => {
                      setControls(false);
                      setSelected(t);
                    }}
                  >
                    <code>
                      {t.method} {t.url}
                    </code>
                  </Button>
                  <span>
                    {t.status_code} · {t.duration_ms} ms
                  </span>
                  <span className="muted">
                    {t.task_id ||
                      (t.source_artifact_id
                        ? "Imported traffic"
                        : "Proxy capture")}
                  </span>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => {
                      remove.reset();
                      setDeleting(t);
                    }}
                  >
                    Delete
                  </Button>
                </div>
              ))}
            </div>
            {!query.data?.data.length && (
              <p className="empty">No captured transactions match.</p>
            )}
            <Pager
              offset={offset}
              total={query.data?.records_filtered || 0}
              onChange={setOffset}
            />
          </>
        )}
      </section>
      {importing && (
        <ImportHAR session={session} onClose={() => setImporting(false)} />
      )}
      <Confirm
        open={!!deleting}
        title="Delete transaction"
        description="Remove this transaction from retained HTTP history. This cannot be undone."
        busy={remove.isPending}
        error={remove.error}
        onClose={() => setDeleting(null)}
        onConfirm={() => remove.mutate(undefined)}
      />
      {selected && (
        <Inspector
          title="Transaction request and response"
          onClose={() => {
            setSelected(null);
            const next = new URLSearchParams(url);
            next.delete("transaction");
            setURL(next);
          }}
        >
          <h2>Transaction {selected.id} · request / response</h2>
          <p className="muted">{selected.url}</p>
          <HTTPExchange
            key={selected.id}
            request={{
              line: selected.method + " " + selected.url,
              headers: selected.request_headers,
              artifact: selected.request_body_artifact_id,
            }}
            response={{
              line: String(selected.status_code),
              headers: selected.response_headers,
              artifact: selected.response_body_artifact_id,
            }}
          />
          {selected.task_id && (
            <a
              className="button-link"
              href={
                "/targets/" +
                selected.target_id +
                "?" +
                new URLSearchParams({ session, execution: selected.task_id })
              }
            >
              Review this evidence
            </a>
          )}
          <div className="actions">
            <Button
              variant="outline"
              disabled={selectedIndex <= 0}
              onClick={() => setSelected(rows[selectedIndex - 1] || null)}
            >
              Previous transaction
            </Button>
            <Button
              variant="outline"
              disabled={selectedIndex < 0 || selectedIndex >= rows.length - 1}
              onClick={() => setSelected(rows[selectedIndex + 1] || null)}
            >
              Next transaction
            </Button>
          </div>
        </Inspector>
      )}
    </>
  );
}
