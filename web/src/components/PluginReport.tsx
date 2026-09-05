import { useState } from "react";
import type { Report, Task } from "../lib/types";
import { StateBadge, pretty } from "./shared";
import TaskDetail from "./TaskDetail";

// Execution selection owns all evidence and review state in this accordion.
export default function PluginReport({
  report,
  tasks,
  initialExecution = "",
}: {
  report: Report;
  tasks: Task[];
  initialExecution?: string;
}) {
  const [selected, setSelected] = useState(initialExecution);
  const ordered = [...tasks].sort(
    (a, b) =>
      b.created_at.localeCompare(a.created_at) || b.id.localeCompare(a.id),
  );
  const task = ordered.find((item) => item.id === selected) || ordered[0];
  if (!task) return null;
  const artifacts =
    report.artifacts?.filter((a) => a.task_id === task.id) || [];
  return (
    <div className="plugin-output">
      <label>
        Execution
        <select
          value={task.id}
          onChange={(event) => setSelected(event.target.value)}
        >
          {ordered.map((item) => (
            <option key={item.id} value={item.id}>
              {new Date(item.created_at).toLocaleString()} · {item.status} ·{" "}
              {item.id}
            </option>
          ))}
        </select>
      </label>
      <div className="artifacts">
        {report.transactions
          ?.filter((transaction) => transaction.task_id === task.id)
          .map((transaction) => (
            <a
              key={transaction.id}
              href={`/transactions?${new URLSearchParams({ session: report.target.session_id, target: transaction.target_id, transaction: transaction.id })}`}
            >
              HTTP transaction {transaction.id} · {transaction.method}{" "}
              {transaction.status_code}
            </a>
          ))}
      </div>
      {report.findings
        ?.filter((f) => f.task_id === task.id)
        .map((f) => (
          <section className="panel" key={f.id}>
            <h3>
              {f.title} <StateBadge value={f.severity} />
            </h3>
            <p>{f.description}</p>
          </section>
        ))}
      {artifacts.length > 0 && (
        <div className="artifacts">
          <h3>Output files</h3>
          {artifacts.map((a) => (
            <a
              key={a.id}
              href={`/api/v2/artifacts/${a.id}`}
              target="_blank"
              rel="noreferrer"
            >
              {a.name} <span className="muted">({a.size} bytes)</span>
            </a>
          ))}
        </div>
      )}
      {report.observations
        ?.filter((o) => o.task_id === task.id)
        .map((o) => (
          <details key={o.id}>
            <summary>{o.kind}</summary>
            <pre>{pretty(o.data)}</pre>
          </details>
        ))}

      <TaskDetail key={task.id} task={task} showReview />
    </div>
  );
}
