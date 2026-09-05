import { useState } from "react";
import { useAPI } from "../lib/api";
import type { Run, Task } from "../lib/types";
import {
  Button,
  ErrorMessage,
  Loading,
  PageHead,
  SessionLink,
  StateBadge,
} from "../components/shared";
import TaskDetail from "../components/TaskDetail";
import Inspector from "../components/Inspector";

function RunDetail({ id, session }: { id: string; session: string }) {
  const run = useAPI<Run>(`/runs/${id}`, true);
  const tasks = useAPI<Task[]>(`/tasks?session_id=${session}`, true);
  return (
    <>
      <ErrorMessage error={run.error || tasks.error} />
      {run.isPending || tasks.isPending ? (
        <Loading />
      ) : (
        <>
          {run.data && (
            <p>
              <StateBadge value={run.data.status} />{" "}
              <span className="muted">
                Profile: {run.data.profile || "None"}
              </span>
            </p>
          )}
          {tasks.data
            ?.filter((task) => task.run_id === id)
            .map((task) => (
              <details className="execution" key={task.id}>
                <summary>
                  <code>{task.plugin_id}</code>
                  <StateBadge value={task.status} />
                </summary>
                <SessionLink to={`/targets/${task.target_id}`}>
                  Target report
                </SessionLink>
                <TaskDetail task={task} />
              </details>
            ))}
        </>
      )}
    </>
  );
}
export default function Runs({ session }: { session: string }) {
  const runs = useAPI<Run[]>(`/runs?session_id=${session}`, true);
  const [selected, setSelected] = useState<string | null>(null);
  return (
    <>
      <PageHead
        title="Runs"
        description="Each launch retains its own tasks and evidence."
      >
        <SessionLink to="/work" className="button-link">
          Worklist
        </SessionLink>
      </PageHead>
      <ErrorMessage error={runs.error} />
      <nav className="section-tabs" aria-label="Work views">
        <SessionLink to="/work">Worklist</SessionLink>
        <SessionLink to="/workers">Workers</SessionLink>
        <SessionLink to="/runs">Runs</SessionLink>
      </nav>
      {runs.isPending ? (
        <Loading />
      ) : (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Run</th>
                <th>Created</th>
                <th>Profile</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {runs.data?.map((run) => (
                <tr key={run.id}>
                  <td>
                    <code>{run.id}</code>
                  </td>
                  <td>{run.created_at}</td>
                  <td>{run.profile || "None"}</td>
                  <td>
                    <StateBadge value={run.status} />
                  </td>
                  <td>
                    <Button
                      variant="outline"
                      onClick={() => setSelected(run.id)}
                    >
                      Show
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {!runs.data?.length && <p className="empty">No runs yet.</p>}
        </div>
      )}
      {selected && (
        <Inspector
          title="Run"
          onClose={() => setSelected(null)}
        >
          <RunDetail id={selected} session={session} />
        </Inspector>
      )}
    </>
  );
}
