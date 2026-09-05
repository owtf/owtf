import { useState } from "react";
import { useParams, useNavigate, useSearchParams } from "react-router-dom";
import { useAPI } from "../lib/api";
import type { Report as TargetReport, Task } from "../lib/types";
import {
  Button,
  ErrorMessage,
  Loading,
  PageHead,
  StateBadge,
  safeURL,
} from "../components/shared";
import { Input } from "../components/ui/input";
import {
  Accordion,
  AccordionItem,
  AccordionTrigger,
  AccordionContent,
} from "../components/ui/accordion";
import PluginLauncher from "../components/PluginLauncher";
import DiscoveredURLs from "../components/DiscoveredURLs";
import PluginReport from "../components/PluginReport";
import DispositionFilter from "../components/DispositionFilter";
import TargetRunHistory from "../components/TargetRunHistory";

export function groupTasks(tasks: Task[]) {
  const groups = new Map<
    string,
    { title: string; hint?: string; reference?: string; tasks: Task[] }
  >();
  for (const task of tasks) {
    const technique = task.techniques?.[0];
    if (!groups.has(task.plugin_id))
      groups.set(task.plugin_id, {
        title: technique?.title || task.plugin_id,
        hint: technique?.hint,
        reference: technique?.reference,
        tasks: [],
      });
    groups.get(task.plugin_id)!.tasks.push(task);
  }
  return [...groups.entries()].sort(([a], [b]) => a.localeCompare(b));
}
export default function Report() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [search, setSearch] = useSearchParams();
  const reportFilters = new URLSearchParams(
    search.getAll("disposition").map((value) => ["disposition", value]),
  );
  const [launch, setLaunch] = useState(false);
  const [filter, setFilter] = useState("");
  const [view, setView] = useState("reports");
  const [openPlugins, setOpenPlugins] = useState<string[] | null>(null);
  const [reviewSelection, setReviewTask] = useState<Task | null>(null);
  const query = useAPI<TargetReport>(
    `/targets/${id}/report?${reportFilters}&group=host`,
    (data) =>
      data?.tasks.some((task) => ["queued", "running"].includes(task.status)) ??
      false,
  );
  if (query.isPending) return <Loading />;
  if (!query.data) return <ErrorMessage error={query.error} />;
  const report = query.data;
  const reviewTask =
    reviewSelection ||
    report.tasks?.find((task) => task.id === search.get("execution")) ||
    null;
  if (launch)
    return (
      <PluginLauncher
        session={report.target.session_id}
        targets={(report.targets || [report.target])
          .filter((target) => target.scope)
          .map((target) => target.id)}
        onClose={() => setLaunch(false)}
        onLaunched={() => navigate(`/work?session=${report.target.session_id}`)}
      />
    );

  const groups = groupTasks(report.tasks || []).filter(([code, g]) =>
    `${code} ${g.title}`.toLowerCase().includes(filter.toLowerCase()),
  );
  return (
    <>
      <PageHead
        title={report.host || report.target.value}
        description="Target report"
      >
        <Button variant="outline" onClick={() => query.refetch()}>
          Refresh
        </Button>
        <Button onClick={() => setLaunch(true)}>Run plugins</Button>
        <a
          className="button-link"
          href={`/api/v2/sessions/${report.target.session_id}/export?${reportFilters}`}
        >
          Export session report
        </a>
      </PageHead>
      {report.targets && (
        <details className="panel">
          <summary>Target URLs ({report.targets.length})</summary>
          {report.targets.map((target) => (
            <div key={target.id}>
              {target.value}{" "}
              <span className="muted">
                {target.scope ? "In scope" : "Out of scope"}
              </span>
            </div>
          ))}
        </details>
      )}
      <nav className="section-tabs" aria-label="Target views">
        <span aria-current="page">Target report</span>
        <a
          href={`/transactions?session=${report.target.session_id}&target=${id}`}
        >
          Proxy
        </a>
      </nav>
      <ErrorMessage error={query.error} />
      <nav className="section-tabs" aria-label="Target report views">
        <Button
          variant="ghost"
          aria-current={view === "reports" ? "page" : undefined}
          onClick={() => setView("reports")}
        >
          Plugin reports
        </Button>
        <Button
          variant="ghost"
          aria-current={view === "history" ? "page" : undefined}
          onClick={() => setView("history")}
        >
          Run history
        </Button>
      </nav>
      {view === "history" ? (
        <TargetRunHistory
          tasks={report.tasks || []}
          onReview={(task) => {
            setReviewTask(task);
            setFilter("");
            setOpenPlugins([task.plugin_id]);
            setView("reports");
          }}
        />
      ) : (
        <>
          <div className="report-summary">
            <span>{report.tasks?.length || 0} executions</span>
            <span>{report.transactions?.length || 0} transactions</span>
            <span>{report.artifacts?.length || 0} artifacts</span>
            <span>{report.observations?.length || 0} observations</span>
            <span>{report.findings?.length || 0} findings</span>
          </div>
          <label className="filters">
            Filter report
            <Input
              placeholder="Test code or title"
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
            />
          </label>
          <details>
            <summary>Filter output</summary>
            <DispositionFilter
              values={search.getAll("disposition")}
              onChange={(values) => {
                const next = new URLSearchParams(search);
                next.delete("disposition");
                values.forEach((value) => next.append("disposition", value));
                setSearch(next);
              }}
            />
          </details>
          {!groups.length && (
            <section className="panel empty">
              {report.tasks?.length
                ? "No matching test codes."
                : "No plugin runs yet. Use Run plugins to begin."}
            </section>
          )}
          <Accordion
            type="multiple"
            className="plugin-reports"
            value={openPlugins ?? (reviewTask ? [reviewTask.plugin_id] : [])}
            onValueChange={setOpenPlugins}
          >
            {groups.map(([code, group]) => {
              const latest = [...group.tasks].sort(
                (a, b) =>
                  b.created_at.localeCompare(a.created_at) ||
                  b.id.localeCompare(a.id),
              )[0];
              const rank =
                report.plugin_output_reviews?.find(
                  (review) => review.task_id === latest.id,
                )?.rank || "unranked";
              return (
                <AccordionItem key={code} value={code} data-severity={rank}>
                  <AccordionTrigger>
                    <span className="plugin-report-heading">
                      <span>
                        <code>{code}</code>{" "}
                        {group.title !== code ? group.title : ""}
                      </span>
                      <span className="muted">
                        {group.tasks.length} executions · {latest.status}
                      </span>
                    </span>
                    <StateBadge value={rank} />
                  </AccordionTrigger>
                  <AccordionContent>
                    {safeURL(group.reference || "") && (
                      <a
                        href={safeURL(group.reference!)}
                        target="_blank"
                        rel="noreferrer"
                      >
                        Testing reference
                      </a>
                    )}
                    <PluginReport
                      key={
                        reviewTask?.plugin_id === code ? reviewTask.id : code
                      }
                      report={report}
                      tasks={group.tasks}
                      initialExecution={
                        reviewTask?.plugin_id === code ? reviewTask.id : ""
                      }
                    />
                  </AccordionContent>
                </AccordionItem>
              );
            })}
          </Accordion>
        </>
      )}
      <details className="panel">
        <summary>Discovered URLs ({report.urls?.length || 0})</summary>
        {(report.targets || [report.target]).map((target) => (
          <div key={target.id}>
            <h3>{target.value}</h3>
            <DiscoveredURLs target={target.id} />
          </div>
        ))}
      </details>
    </>
  );
}
