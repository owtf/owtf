import { useState } from "react";
import type { Task } from "../lib/types";
import { request, useAction } from "../lib/api";
import { Button, Confirm, StateBadge, duration } from "./shared";
import TaskDetail from "./TaskDetail";

export default function TargetRunHistory({
  tasks,
  onReview,
}: {
  tasks: Task[];
  onReview: (task: Task) => void;
}) {
  const [cancelling, setCancelling] = useState<Task | null>(null);
  const [expanded, setExpanded] = useState<Record<string, boolean>>({});
  const cancel = useAction(async () => {
    if (cancelling) await request(`/tasks/${cancelling.id}/cancel`, "POST");
    setCancelling(null);
  });
  return (
    <>
      <p className="muted">Execution history for this target.</p>
      {[...tasks]
        .sort(
          (a, b) =>
            b.created_at.localeCompare(a.created_at) ||
            b.id.localeCompare(a.id),
        )
        .map((task) => (
          <details
            className="target-run"
            key={task.id}
            onToggle={(event) => {
              const open = event.currentTarget.open;
              setExpanded((current) => ({ ...current, [task.id]: open }));
            }}
          >
            <summary>
              <span className="catalog-title">
                <span>{task.techniques?.[0]?.title || task.plugin_id}</span>
                <StateBadge value={task.status} />
              </span>
              <span className="muted">
                {new Date(task.created_at).toLocaleString()} · {task.plugin_id}{" "}
                · {duration(task)}
              </span>
            </summary>
            {expanded[task.id] && <TaskDetail task={task} />}
            <div className="actions">
              <Button variant="outline" onClick={() => onReview(task)}>
                Review output
              </Button>
              {["queued", "paused", "running"].includes(task.status) && (
                <Button
                  variant="ghost"
                  onClick={() => {
                    cancel.reset();
                    setCancelling(task);
                  }}
                >
                  Cancel this run
                </Button>
              )}
            </div>
          </details>
        ))}
      {!tasks.length && <p>No plugin runs yet.</p>}
      <Confirm
        open={!!cancelling}
        title="Cancel this run?"
        description="Stops this task and its processes. Captured evidence is retained."
        busy={cancel.isPending}
        error={cancel.error}
        onClose={() => setCancelling(null)}
        onConfirm={() => cancel.mutate(undefined)}
      />
    </>
  );
}
