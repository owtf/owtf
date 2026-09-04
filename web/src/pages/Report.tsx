import { useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useAPI } from "../lib/api";
import type { Report as TargetReport, Task } from "../lib/types";
import { ranks } from "../lib/types";
import {
  Button,
  ErrorMessage,
  Loading,
  PageHead,
  StateBadge,
  duration,
  safeURL,
  pretty,
} from "../components/shared";
import { Input } from "../components/ui/input";
import {
  Accordion,
  AccordionItem,
  AccordionTrigger,
  AccordionContent,
} from "../components/ui/accordion";
import {
  Tabs,
  TabsList,
  TabsTrigger,
  TabsContent,
} from "../components/ui/tabs";
import PluginLauncher from "../components/PluginLauncher";
import TaskDetail from "../components/TaskDetail";

export function groupTasks(tasks: Task[]) {
  const groups = new Map<
    string,
    { title: string; hint?: string; reference?: string; tasks: Task[] }
  >();
  for (const task of tasks)
    for (const technique of task.techniques || []) {
      if (!groups.has(technique.code))
        groups.set(technique.code, {
          title: technique.title,
          hint: technique.hint,
          reference: technique.reference,
          tasks: [],
        });
      groups.get(technique.code)!.tasks.push(task);
    }
  return [...groups.entries()].sort(([a], [b]) => a.localeCompare(b));
}
export default function Report() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [launch, setLaunch] = useState(false);
  const [filter, setFilter] = useState("");
  const [expanded, setExpanded] = useState<Record<string, boolean>>({});
  const query = useAPI<TargetReport>(
    `/targets/${id}/report`,
    (data) =>
      data?.tasks.some((task) => ["queued", "running"].includes(task.status)) ??
      false,
  );
  if (query.isPending) return <Loading />;
  if (!query.data) return <ErrorMessage error={query.error} />;
  const report = query.data;
  const groups = groupTasks(report.tasks || []).filter(([code, g]) =>
    `${code} ${g.title}`.toLowerCase().includes(filter.toLowerCase()),
  );
  return (
    <>
      <PageHead
        title={report.target.value}
        description={`Target report · ${report.target.kind}`}
      >
        <Button variant="outline" onClick={() => query.refetch()}>
          Refresh
        </Button>
        <Button onClick={() => setLaunch(true)}>Run plugins</Button>
        <a
          className="button-link"
          href={`/transactions?session=${report.target.session_id}&target=${id}`}
        >
          Transactions
        </a>
        <a
          className="button-link"
          href={`/api/v2/sessions/${report.target.session_id}/export`}
        >
          Export session report
        </a>
      </PageHead>
      <ErrorMessage error={query.error} />
      <div className="report-summary">
        <span>{report.tasks?.length || 0} executions</span>
        <span>{report.transactions?.length || 0} transactions</span>
        <span>{report.artifacts?.length || 0} artifacts</span>
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
      {!groups.length && (
        <section className="panel empty">
          {report.tasks?.length
            ? "No matching test codes."
            : "No plugin runs yet. Use Run plugins to begin."}
        </section>
      )}
      <Accordion type="multiple" className="report-accordion">
        {groups.map(([code, group]) => {
          const ids = [...new Set(group.tasks.map((t) => t.plugin_id))];
          const rank =
            ranks[
              Math.max(
                0,
                ...(report.plugin_output_reviews || [])
                  .filter((review) =>
                    group.tasks.some((task) => task.id === review.task_id),
                  )
                  .map((review) => ranks.indexOf(review.rank)),
              )
            ];
          return (
            <AccordionItem
              key={code}
              value={code}
              className={`report-rank-${rank}`}
            >
              <AccordionTrigger className="px-4">
                <span className="text-left">
                  <strong>
                    {code} {group.title}
                  </strong>
                  {group.hint && (
                    <span className="muted block font-normal">
                      {group.hint}
                    </span>
                  )}
                </span>
                <StateBadge value={rank} />
              </AccordionTrigger>
              <AccordionContent className="px-4">
                {safeURL(group.reference || "") && (
                  <a
                    href={safeURL(group.reference!)}
                    target="_blank"
                    rel="noreferrer"
                  >
                    Testing reference
                  </a>
                )}
                <Tabs defaultValue={ids[0]}>
                  <TabsList className="flex-wrap h-auto">
                    {ids.map((pid) => (
                      <TabsTrigger value={pid} key={pid}>
                        {pid.startsWith(code + "-")
                          ? pid.slice(code.length + 1).replaceAll("_", " ")
                          : pid}
                      </TabsTrigger>
                    ))}
                  </TabsList>
                  {ids.map((pid) => (
                    <TabsContent key={pid} value={pid}>
                      {group.tasks
                        .filter((t) => t.plugin_id === pid)
                        .map((task) => {
                          const review = report.plugin_output_reviews?.find(
                            (r) => r.task_id === task.id,
                          );
                          return (
                            <details
                              className="execution"
                              key={task.id}
                              onToggle={(event) => {
                                const open = event.currentTarget.open;
                                setExpanded((current) => ({
                                  ...current,
                                  [task.id]: open,
                                }));
                              }}
                            >
                              <summary>
                                <span>
                                  {new Date(task.created_at).toLocaleString()}
                                </span>{" "}
                                <StateBadge value={task.status} />{" "}
                                <StateBadge
                                  value={review?.rank || "unranked"}
                                />{" "}
                                <span className="muted">
                                  {duration(task)} · {task.id}
                                </span>
                              </summary>
                              {report.findings
                                ?.filter((f) => f.task_id === task.id)
                                .map((f) => (
                                  <section className="panel" key={f.id}>
                                    <h3>
                                      {f.title}{" "}
                                      <StateBadge value={f.severity} />
                                    </h3>
                                    <p>{f.description}</p>
                                  </section>
                                ))}
                              <div className="artifacts">
                                <h3>Output files</h3>
                                {report.artifacts
                                  ?.filter((a) => a.task_id === task.id)
                                  .map((a) => (
                                    <a
                                      key={a.id}
                                      href={`/api/v2/artifacts/${a.id}`}
                                      target="_blank"
                                      rel="noreferrer"
                                    >
                                      {a.name}{" "}
                                      <span className="muted">
                                        ({a.size} bytes)
                                      </span>
                                    </a>
                                  ))}
                              </div>
                              {report.observations
                                ?.filter((o) => o.task_id === task.id)
                                .map((o) => (
                                  <details key={o.id}>
                                    <summary>{o.kind}</summary>
                                    <pre>{pretty(o.data)}</pre>
                                  </details>
                                ))}
                              {expanded[task.id] && <TaskDetail task={task} />}
                            </details>
                          );
                        })}
                    </TabsContent>
                  ))}
                </Tabs>
              </AccordionContent>
            </AccordionItem>
          );
        })}
      </Accordion>
      <details className="panel">
        <summary>Discovered URLs ({report.urls?.length || 0})</summary>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>URL</th>
                <th>Visited</th>
                <th>Scope</th>
              </tr>
            </thead>
            <tbody>
              {report.urls?.map((u) => (
                <tr key={u.url}>
                  <td>{u.url}</td>
                  <td>{u.visited ? "Yes" : "No"}</td>
                  <td>{u.scope ? "In scope" : "Out of scope"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </details>
      {launch && (
        <PluginLauncher
          session={report.target.session_id}
          targets={[report.target.id]}
          onClose={() => setLaunch(false)}
          onLaunched={() =>
            navigate(`/work?session=${report.target.session_id}`)
          }
        />
      )}
    </>
  );
}
