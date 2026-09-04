import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAPI, useAction, request, params } from "../lib/api";
import type { Target, Page } from "../lib/types";
import {
  Button,
  Confirm,
  ErrorMessage,
  Loading,
  PageHead,
  Pager,
  SessionLink,
} from "../components/shared";
import { Input } from "../components/ui/input";
import { Textarea } from "../components/ui/textarea";
import PluginLauncher from "../components/PluginLauncher";

export default function Targets({ session }: { session: string }) {
  const navigate = useNavigate();
  const [search, setSearch] = useState("");
  const [offset, setOffset] = useState(0);
  const [draft, setDraft] = useState("");
  const [notice, setNotice] = useState("");
  const [selected, setSelected] = useState<string[]>([]);
  const [launch, setLaunch] = useState<string[] | null>(null);
  const [deleting, setDeleting] = useState<string[] | null>(null);
  const query = useAPI<Page<Target>>(
    `/sessions/${session}/targets/search?${params({ search, offset, limit: 20 })}`,
  );
  const add = useAction(async () => {
    const result = await request<{
      created: Target[];
      duplicates: Target[];
      invalid: { input: string; error: string }[];
    }>(`/sessions/${session}/targets`, "POST", {
      targets: draft
        .split("\n")
        .map((v) => v.trim())
        .filter(Boolean),
    });
    setNotice(
      `${result.created.length} added, ${result.duplicates.length} duplicate(s). ${result.invalid.map((v) => `${v.input}: ${v.error}`).join("; ")}`,
    );
    setDraft(result.invalid.map((v) => v.input).join("\n"));
  });
  const remove = useAction(async () => {
    // Sequential deletes preserve the first failure and never replay a mutation.
    for (const id of deleting || []) {
      await request(`/targets/${id}`, "DELETE");
      setSelected((s) => s.filter((v) => v !== id));
      setDeleting((s) => s?.filter((v) => v !== id) || null);
    }
    setDeleting(null);
  });
  return (
    <>
      <PageHead
        title="Targets"
        description="Define targets, select plugins, review results."
      >
        <a className="button-link" href={`/api/v2/sessions/${session}/export`}>
          Export session report
        </a>
      </PageHead>
      <section className="panel">
        <h2>Add targets</h2>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            add.mutate(undefined);
          }}
        >
          <label htmlFor="new-targets">
            One URL, hostname, IP address or CIDR per line
          </label>
          <Textarea
            id="new-targets"
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            placeholder="https://app.example.com"
          />
          <div className="actions">
            <Button disabled={!draft.trim() || add.isPending} type="submit">
              {add.isPending ? "Adding…" : "Add targets"}
            </Button>
            <p role="status">{notice}</p>
          </div>
          <ErrorMessage error={add.error} />
        </form>
      </section>
      <section className="panel">
        <div className="section-head">
          <h2>Target list</h2>
          <div className="actions">
            <Button
              disabled={!selected.length}
              onClick={() => setLaunch(selected)}
            >
              Run plugins ({selected.length})
            </Button>
            <Button
              variant="outline"
              disabled={!selected.length}
              onClick={() => {
                remove.reset();
                setDeleting([...selected]);
              }}
            >
              Delete selected
            </Button>
          </div>
        </div>
        <div className="filters">
          <label>
            Search targets
            <Input
              value={search}
              onChange={(e) => {
                setSearch(e.target.value);
                setOffset(0);
              }}
            />
          </label>
          <span className="muted">{selected.length} selected across pages</span>
          <Button variant="ghost" onClick={() => setSelected([])}>
            Clear selection
          </Button>
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
                    <th>
                      <input
                        aria-label="Select targets on this page"
                        type="checkbox"
                        checked={
                          !!query.data?.data.length &&
                          query.data.data.every((t) => selected.includes(t.id))
                        }
                        onChange={(e) =>
                          setSelected((s) =>
                            e.target.checked
                              ? [
                                  ...new Set([
                                    ...s,
                                    ...(query.data?.data || []).map(
                                      (t) => t.id,
                                    ),
                                  ]),
                                ]
                              : s.filter(
                                  (id) =>
                                    !query.data?.data.some((t) => t.id === id),
                                ),
                          )
                        }
                      />
                    </th>
                    <th>Target</th>
                    <th>Type</th>
                    <th>Scope</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {query.data?.data.map((t) => (
                    <tr key={t.id}>
                      <td>
                        <input
                          type="checkbox"
                          aria-label={`Select ${t.value}`}
                          checked={selected.includes(t.id)}
                          onChange={(e) =>
                            setSelected((s) =>
                              e.target.checked
                                ? [...s, t.id]
                                : s.filter((id) => id !== t.id),
                            )
                          }
                        />
                      </td>
                      <td>
                        <SessionLink to={`/targets/${t.id}`}>
                          {t.value}
                        </SessionLink>
                        <div className="muted mono">{t.id}</div>
                      </td>
                      <td>{t.kind}</td>
                      <td>{t.scope ? "In scope" : "Out of scope"}</td>
                      <td>
                        <div className="actions">
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => setLaunch([t.id])}
                          >
                            Run plugins
                          </Button>
                          <SessionLink
                            className="button-link"
                            to={`/targets/${t.id}`}
                          >
                            Report
                          </SessionLink>
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() => {
                              remove.reset();
                              setDeleting([t.id]);
                            }}
                          >
                            Delete
                          </Button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {!query.data?.data.length && (
              <p className="empty">
                No targets match. Add a target or change the search.
              </p>
            )}
            <Pager
              offset={offset}
              total={query.data?.records_filtered || 0}
              onChange={setOffset}
            />
          </>
        )}
      </section>
      {launch && (
        <PluginLauncher
          session={session}
          targets={launch}
          onClose={() => setLaunch(null)}
          onLaunched={() => navigate(`/work?session=${session}`)}
        />
      )}
      <Confirm
        open={deleting !== null}
        title={`Delete ${deleting?.length || 0} target(s)?`}
        description="This permanently deletes these targets and their stored evidence. Running work must be cancelled first."
        busy={remove.isPending}
        error={remove.error}
        onClose={() => setDeleting(null)}
        onConfirm={() => remove.mutate(undefined)}
      />
    </>
  );
}
