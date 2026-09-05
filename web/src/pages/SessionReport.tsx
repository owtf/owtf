import DispositionFilter from "../components/DispositionFilter";
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAPI, useAction, request } from "../lib/api";
import { type Session, type Target, type Task } from "../lib/types";
import {
  Button,
  Confirm,
  ErrorMessage,
  Loading,
  PageHead,
  SessionLink,
} from "../components/shared";

interface SessionEvidence {
  session: Session;
  summary: Record<string, number>;
  targets: Target[];
  tasks: Task[];
}
export default function SessionReport({ session }: { session: string }) {
  const navigate = useNavigate();
  const [filters, setFilters] = useState<string[]>([]);
  const [deleting, setDeleting] = useState(false);
  const suffix = filters.length
    ? `?${new URLSearchParams(filters.map((value) => ["disposition", value]))}`
    : "";
  const report = useAPI<SessionEvidence>(
    `/sessions/${session}/report${suffix}`,
  );
  const remove = useAction(async () => {
    await request(`/sessions/${session}`, "DELETE");
    setDeleting(false);
    navigate("/");
  });
  return (
    <>
      <PageHead title="Session report" description={report.data?.session.name}>
        <a
          className="button-link"
          href={`/api/v2/sessions/${session}/export${suffix}`}
        >
          Export session report
        </a>
        <Button
          variant="outline"
          onClick={() => {
            remove.reset();
            setDeleting(true);
          }}
        >
          Delete session
        </Button>
      </PageHead>
      <DispositionFilter values={filters} onChange={setFilters} />
      <ErrorMessage error={report.error} />
      {report.isPending ? (
        <Loading />
      ) : (
        report.data && (
          <>
            <div className="report-summary">
              {["targets", "tasks", "transactions", "artifacts"].map((key) => (
                <span key={key}>
                  {report.data!.summary[key]} {key}
                </span>
              ))}
            </div>
            {report.data.targets.map((target) => (
              <section className="panel" key={target.id}>
                <div className="section-head">
                  <h2>{target.value}</h2>
                  <SessionLink
                    to={`/targets/${target.id}${suffix}`}
                    className="button-link"
                  >
                    Target report
                  </SessionLink>
                </div>
                <p>
                  {
                    report.data!.tasks.filter(
                      (task) => task.target_id === target.id,
                    ).length
                  }{" "}
                  plugin outputs
                </p>
              </section>
            ))}
            {!report.data.targets.length && (
              <p className="empty">No targets in this session.</p>
            )}
          </>
        )
      )}
      <Confirm
        open={deleting}
        title="Delete session"
        description="Delete this session and its retained targets and evidence. This cannot be undone. Active work must be stopped first."
        busy={remove.isPending}
        error={remove.error}
        onClose={() => setDeleting(false)}
        onConfirm={() => remove.mutate(undefined)}
      />
    </>
  );
}
