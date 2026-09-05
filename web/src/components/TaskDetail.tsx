import { useState } from "react";
import { useAPI, useAction, request } from "../lib/api";
import type {
  Task,
  Event,
  Review,
  ReviewEvent,
  TaskAttempt,
} from "../lib/types";
import { ranks, dispositions } from "../lib/types";
import { Button, ErrorMessage, Loading, StateBadge } from "./shared";
import { Textarea } from "./ui/textarea";

export function ReviewEditor({
  task,
  initial,
}: {
  task: string;
  initial: Review;
}) {
  const [rank, setRank] = useState(initial.rank);
  const [disposition, setDisposition] = useState(initial.disposition);
  const [notes, setNotes] = useState(initial.notes);
  const [saved, setSaved] = useState(false);
  const mutation = useAction(() =>
    request(`/tasks/${task}/review`, "PATCH", { rank, disposition, notes }),
  );
  return (
    <form
      className="review"
      onSubmit={(e) => {
        e.preventDefault();
        mutation.mutate(undefined, { onSuccess: () => setSaved(true) });
      }}
      onChange={() => setSaved(false)}
    >
      <div className="filters">
        <label>
          Severity
          <select value={rank} onChange={(e) => setRank(e.target.value)}>
            {ranks.map((r) => (
              <option key={r}>{r}</option>
            ))}
          </select>
        </label>
        <label>
          Disposition
          <select
            value={disposition}
            onChange={(e) => setDisposition(e.target.value)}
          >
            {dispositions.map((r) => (
              <option key={r} value={r}>
                {r.replaceAll("_", " ")}
              </option>
            ))}
          </select>
        </label>
      </div>
      <label>
        Notes
        <Textarea
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          maxLength={65536}
        />
      </label>
      <ErrorMessage error={mutation.error} />
      <div className="actions">
        <Button disabled={mutation.isPending} type="submit">
          Save review
        </Button>
        {saved && <span role="status">Review saved</span>}
      </div>
    </form>
  );
}
export default function TaskDetail({
  task,
  showReview = false,
}: {
  task: Task;
  showReview?: boolean;
}) {
  const events = useAPI<Event[]>(
    `/tasks/${task.id}/events`,
    task.status === "running",
  );
  const review = useAPI<Review>(showReview ? `/tasks/${task.id}/review` : "");
  const attempts = useAPI<TaskAttempt[]>(
    `/tasks/${task.id}/attempts`,
    task.status === "running",
  );
  const history = useAPI<ReviewEvent[]>(
    showReview ? `/tasks/${task.id}/review/history` : "",
  );
  return (
    <div className="stack">
      <div className="actions">
        <code>{task.id}</code>
        <StateBadge value={task.status} />
      </div>
      <ErrorMessage
        error={
          task.error ||
          events.error ||
          review.error ||
          history.error ||
          attempts.error
        }
      />
      <details>
        <summary>Execution attempts</summary>
        {attempts.isPending ? (
          <Loading />
        ) : (
          attempts.data?.map((attempt) => (
            <div className="history" key={attempt.id}>
              <span>Attempt {attempt.attempt_number} </span>
              <StateBadge value={attempt.status} />
              <p>
                {attempt.started_at}{" "}
                {attempt.ended_at ? `to ${attempt.ended_at}` : ""}
              </p>
              <ErrorMessage error={attempt.error} />
            </div>
          ))
        )}
      </details>
      <h3>Execution log</h3>
      {events.isPending ? (
        <Loading />
      ) : (
        <pre className="log" aria-label="Execution log">
          {events.data
            ?.map((e) => `${e.created_at} [${e.stream}] ${e.message}`)
            .join("\n") || "No events recorded yet."}
        </pre>
      )}
      {showReview && (
        <>
          <h3>Output review</h3>
          <p className="muted">
            Execution success is not a security finding. Review changes preserve
            evidence.
          </p>
          {review.data && (
            <ReviewEditor key={task.id} task={task.id} initial={review.data} />
          )}
          <details>
            <summary>Review history ({history.data?.length || 0})</summary>
            {history.data?.map((e) => (
              <div key={e.id} className="history">
                <span>{new Date(e.created_at).toLocaleString()}</span>{" "}
                <StateBadge value={e.rank} />{" "}
                <StateBadge value={e.disposition} />
                <pre>{e.notes}</pre>
              </div>
            ))}
          </details>
        </>
      )}
    </div>
  );
}
