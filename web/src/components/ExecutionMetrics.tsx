import { useAPI } from "../lib/api";
import { ErrorMessage, Loading } from "./shared";

type Metrics = {
  tasks: Record<
    | "total"
    | "queued"
    | "blocked"
    | "paused"
    | "running"
    | "succeeded"
    | "failed"
    | "cancelled",
    number
  >;
  attempts: Record<
    | "total"
    | "running"
    | "succeeded"
    | "failed"
    | "cancelled"
    | "total_duration_ms"
    | "average_duration_ms"
    | "maximum_duration_ms",
    number
  >;
  outputs: Record<
    "urls" | "transactions" | "artifacts" | "observations" | "findings",
    number
  >;
  workers: Record<
    "total" | "idle" | "running" | "completed" | "failed" | "cancelled",
    number
  >;
};

export default function ExecutionMetrics() {
  const metrics = useAPI<Metrics>("/metrics", true);
  const health = useAPI<{ status: string }>("/health", true);
  return (
    <section className="panel">
      <div className="section-head">
        <h2>Execution metrics</h2>
        <span role="status">
          {health.error
            ? "Service unavailable"
            : health.data?.status === "ok"
              ? "Service healthy"
              : "Checking service"}
        </span>
      </div>
      <p className="muted">
        All sessions. Worker counters reset when the server restarts; task and
        evidence counts are persisted.
      </p>
      <ErrorMessage error={metrics.error || health.error} />
      {metrics.isPending ? (
        <Loading />
      ) : (
        metrics.data && (
          <div className="help-grid">
            {Object.entries(metrics.data).map(([group, counts]) => (
              <details key={group}>
                <summary>{group[0].toUpperCase() + group.slice(1)}</summary>
                <dl className="metric-values">
                  {Object.entries(counts).map(([key, count]) => (
                    <div key={key}>
                      <dt>{key.replaceAll("_", " ").replace(/ ms$/, "")}</dt>
                      <dd>
                        {count.toLocaleString()}
                        {key.endsWith("_ms") ? " ms" : ""}
                      </dd>
                    </div>
                  ))}
                </dl>
              </details>
            ))}
          </div>
        )
      )}
    </section>
  );
}
