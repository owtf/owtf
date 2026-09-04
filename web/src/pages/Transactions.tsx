import { useState } from "react";
import { useSearchParams } from "react-router-dom";
import { useAPI, params } from "../lib/api";
import type { Page, Transaction } from "../lib/types";
import {
  Button,
  ErrorMessage,
  Loading,
  Modal,
  PageHead,
  Pager,
  pretty,
} from "../components/shared";
import { Input } from "../components/ui/input";
import {
  Tabs,
  TabsList,
  TabsTrigger,
  TabsContent,
} from "../components/ui/tabs";

function BodyLink({ id }: { id?: string }) {
  return id ? (
    <a
      className="button-link"
      href={`/api/v2/artifacts/${id}`}
      target="_blank"
      rel="noreferrer"
    >
      Open captured body
    </a>
  ) : (
    <p className="muted">No captured body.</p>
  );
}
export default function Transactions({ session }: { session: string }) {
  const [url] = useSearchParams();
  const [search, setSearch] = useState("");
  const [method, setMethod] = useState("");
  const [status, setStatus] = useState("");
  const [offset, setOffset] = useState(0);
  const [selected, setSelected] = useState<Transaction | null>(null);
  const query = useAPI<Page<Transaction>>(
    `/transactions/search?${params({ session_id: session, target_id: url.get("target") || "", search, method, status_code: status, offset, limit: 20 })}`,
  );
  const rows = query.data?.data || [];
  const selectedIndex = rows.findIndex((row) => row.id === selected?.id);
  return (
    <>
      <PageHead
        title="Transactions"
        description="Captured HTTP requests and responses. Opening evidence does not replay traffic."
      >
        <Button variant="outline" onClick={() => query.refetch()}>
          Refresh
        </Button>
      </PageHead>
      <section className="panel">
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
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Method</th>
                    <th>Status</th>
                    <th>URL</th>
                    <th>Duration</th>
                    <th>Evidence</th>
                  </tr>
                </thead>
                <tbody>
                  {query.data?.data.map((t) => (
                    <tr key={t.id}>
                      <td>{t.method}</td>
                      <td>{t.status_code}</td>
                      <td className="break-all">{t.url}</td>
                      <td>{t.duration_ms}ms</td>
                      <td>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => setSelected(t)}
                        >
                          Inspect
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
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
      {selected && (
        <Modal
          open
          title={`${selected.method} · ${selected.status_code}`}
          description={selected.url}
          onClose={() => setSelected(null)}
        >
          <Tabs defaultValue="request">
            <TabsList>
              <TabsTrigger value="request">Request</TabsTrigger>
              <TabsTrigger value="response">Response</TabsTrigger>
            </TabsList>
            <TabsContent value="request">
              <pre>{pretty(selected.request_headers)}</pre>
              <BodyLink id={selected.request_body_artifact_id} />
            </TabsContent>
            <TabsContent value="response">
              <pre>{pretty(selected.response_headers)}</pre>
              <BodyLink id={selected.response_body_artifact_id} />
            </TabsContent>
          </Tabs>
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
        </Modal>
      )}
    </>
  );
}
