import { useState } from "react";
import { useAPI, useAction, request } from "../lib/api";
import type { Task, Target, Worker } from "../lib/types";
import {
  Button,
  Confirm,
  ErrorMessage,
  Loading,
  PageHead,
  Pager,
  SessionLink,
  StateBadge,
  duration,
} from "../components/shared";
import { Input } from "../components/ui/input";
import TaskDetail from "../components/TaskDetail";
import Inspector from "../components/Inspector";
import ExecutionMetrics from "../components/ExecutionMetrics";

export default function Work({
  session,
  workers = false,
}: {
  session: string;
  workers?: boolean;
}) {
  const tasks = useAPI<Task[]>(`/tasks?session_id=${session}`, true);
  const targets = useAPI<Target[]>(`/sessions/${session}/targets`);
  const workerQuery = useAPI<Worker[]>(workers ? "/workers" : "", true);
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("");
  const [offset, setOffset] = useState(0);
  const [detail, setDetail] = useState<string | null>(null);
  const [confirm, setConfirm] = useState<{ id: string; action: string } | null>(
    null,
  );
  const action = useAction(
    async ({ id, action }: { id: string; action: string }) =>
      request(
        `/tasks/${id}${action === "remove" ? "" : `/${action}`}`,
        action === "remove" ? "DELETE" : "POST",
      ),
  );
  const reorder = useAction((ids: string[]) =>
    request("/worklist/order", "PUT", { session_id: session, task_ids: ids }),
  );
  const queue = (tasks.data || [])
    .filter((t) => t.status === "queued" || t.status === "paused")
    .sort((a, b) => a.position - b.position);
  const title = (id: string) =>
    targets.data?.find((t) => t.id === id)?.value || id;
  const visible = (tasks.data || [])
    .filter(
      (t) =>
        (!status || t.status === status) &&
        `${t.plugin_id} ${title(t.target_id)} ${t.id}`
          .toLowerCase()
          .includes(search.toLowerCase()),
    )
    .sort((a, b) => a.position - b.position);
  const selected = tasks.data?.find((t) => t.id === detail);
  const busy = action.isPending || reorder.isPending;
  const controls = (task: Task) => (
    <div className="actions">
      <Button size="sm" variant="outline" onClick={() => setDetail(task.id)}>
        Log
      </Button>
      {task.status === "queued" && (
        <Button
          size="sm"
          variant="outline"
          disabled={busy}
          onClick={() => action.mutate({ id: task.id, action: "pause" })}
        >
          Pause
        </Button>
      )}
      {task.status === "paused" && (
        <Button
          size="sm"
          variant="outline"
          disabled={busy}
          onClick={() => action.mutate({ id: task.id, action: "resume" })}
        >
          Resume
        </Button>
      )}
      {["queued", "paused", "running"].includes(task.status) && (
        <Button
          size="sm"
          variant="outline"
          disabled={busy}
          onClick={() => {
            action.reset();
            setConfirm({ id: task.id, action: "cancel" });
          }}
        >
          Cancel
        </Button>
      )}
      {["queued", "paused", "blocked"].includes(task.status) && (
        <Button
          size="sm"
          variant="ghost"
          disabled={busy}
          onClick={() => {
            action.reset();
            setConfirm({ id: task.id, action: "remove" });
          }}
        >
          Remove
        </Button>
      )}
      {queue.findIndex((t) => t.id === task.id) > 0 && (
        <Button
          size="sm"
          variant="ghost"
          disabled={busy}
          onClick={() => {
            const ids = queue.map((t) => t.id);
            const i = ids.indexOf(task.id);
            [ids[i - 1], ids[i]] = [ids[i], ids[i - 1]];
            reorder.mutate(ids);
          }}
        >
          Move up
        </Button>
      )}
    </div>
  );
  return (
    <>
      <PageHead
        title={workers ? "Workers" : "Worklist"}
        description={
          workers
            ? "Live worker state. Counters reset when the server restarts."
            : "Pause affects queued work only. Cancel stops running work; no automatic retries."
        }
      >
        <Button
          variant="outline"
          onClick={() => {
            tasks.refetch();
            if (workers) workerQuery.refetch();
          }}
        >
          Refresh
        </Button>
      </PageHead>
      <nav className="section-tabs" aria-label="Work views">
        <SessionLink to="/work">Worklist</SessionLink>
        <SessionLink to="/workers">Workers</SessionLink>
        <SessionLink to="/runs">Runs</SessionLink>
      </nav>
      <ErrorMessage
        error={
          tasks.error ||
          targets.error ||
          workerQuery.error ||
          action.error ||
          reorder.error
        }
      />
      {workers && <ExecutionMetrics />}
      {workers && (
        <section className="panel">
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Worker</th>
                  <th>Status</th>
                  <th>Current plugin / Target</th>
                  <th>Completed / Failed / Cancelled</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {workerQuery.data?.map((w) => (
                  <tr key={w.id}>
                    <td>
                      <code>{w.id}</code>
                    </td>
                    <td>
                      <StateBadge value={w.status} />
                    </td>
                    <td>
                      {w.plugin_id || "Idle"}
                      {w.target_id && <div>{title(w.target_id)}</div>}
                    </td>
                    <td>
                      {w.completed} / {w.failed} / {w.cancelled}
                    </td>
                    <td>
                      {w.task_id && tasks.data?.find((t) => t.id === w.task_id)
                        ? controls(tasks.data.find((t) => t.id === w.task_id)!)
                        : w.task_id
                          ? "Task belongs to another session"
                          : "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}
      <section className="panel">
        <div className="filters">
          <label>
            Search work
            <Input
              value={search}
              onChange={(e) => {
                setSearch(e.target.value);
                setOffset(0);
              }}
            />
          </label>
          <label>
            Status
            <select
              value={status}
              onChange={(e) => {
                setStatus(e.target.value);
                setOffset(0);
              }}
            >
              <option value="">All states</option>
              {[
                "queued",
                "paused",
                "running",
                "succeeded",
                "failed",
                "cancelled",
                "blocked",
              ].map((s) => (
                <option key={s}>{s}</option>
              ))}
            </select>
          </label>
        </div>
        {tasks.isPending ? (
          <Loading />
        ) : (
          <>
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Target</th>
                    <th>Plugin</th>
                    <th>Status</th>
                    <th>Duration</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {visible.slice(offset, offset + 20).map((t) => (
                    <tr key={t.id}>
                      <td>
                        <SessionLink to={`/targets/${t.target_id}`}>
                          {title(t.target_id)}
                        </SessionLink>
                      </td>
                      <td>
                        <code>{t.plugin_id}</code>
                        <div className="muted mono">{t.id}</div>
                        {t.error && <p className="text-red-700">{t.error}</p>}
                      </td>
                      <td>
                        <StateBadge value={t.status} />
                      </td>
                      <td>{duration(t)}</td>
                      <td>{controls(t)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {!visible.length && (
              <p className="empty">
                No work matches. Launch plugins from Targets.
              </p>
            )}
            <Pager
              offset={offset}
              total={visible.length}
              onChange={setOffset}
            />
          </>
        )}
      </section>
      {selected && (
        <Inspector title={selected.plugin_id} onClose={() => setDetail(null)}>
          <SessionLink to={`/targets/${selected.target_id}`}>
            Target report
          </SessionLink>
          <TaskDetail key={selected.id} task={selected} />
        </Inspector>
      )}
      <Confirm
        open={!!confirm}
        title={
          confirm?.action === "cancel"
            ? "Cancel this task?"
            : "Remove queued work?"
        }
        description={
          confirm?.action === "cancel"
            ? "Running processes will be stopped. Captured evidence is retained."
            : "This permanently removes the pending task from the worklist."
        }
        busy={action.isPending}
        error={action.error}
        onClose={() => setConfirm(null)}
        onConfirm={() => {
          if (confirm)
            action.mutate(confirm, { onSuccess: () => setConfirm(null) });
        }}
      />
    </>
  );
}
