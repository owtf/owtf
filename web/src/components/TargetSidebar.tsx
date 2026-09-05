import { useState } from "react";
import { Link, NavLink, useLocation } from "react-router-dom";
import { useAPI } from "../lib/api";
import type { Target, Task } from "../lib/types";
import { ErrorMessage, Loading, Pager } from "./shared";

function host(target: Target) {
  if (target.kind === "url") {
    try {
      return new URL(target.value).hostname.toLowerCase();
    } catch {
      /* Keep malformed historical labels visible. */
    }
  }
  return target.value;
}

// Group the complete session before paginating so one host cannot split across pages.
export default function TargetSidebar({ session }: { session: string }) {
  const [offset, setOffset] = useState(0);
  const location = useLocation();
  const targets = useAPI<Target[]>(`/sessions/${session}/targets`);
  const tasks = useAPI<Task[]>(`/tasks?session_id=${session}`, true);
  const running = new Set(
    tasks.data
      ?.filter((task) => task.status === "running")
      .map((task) => task.target_id),
  );
  const groups = new Map<string, Target[]>();
  for (const target of targets.data || []) {
    const key = host(target);
    groups.set(key, [...(groups.get(key) || []), target]);
  }
  const entries = [...groups.entries()].sort(([a], [b]) => a.localeCompare(b));
  return (
    <section className="target-sidebar" aria-label="Session targets">
      <NavLink to={`/targets/new?session=${session}`} className="button-link">
        Add targets
      </NavLink>
      <div className="target-heading">
        <h2>Targets</h2>
        <NavLink to={`/?session=${session}`}>Select</NavLink>
      </div>
      <ErrorMessage error={targets.error || tasks.error} />
      {targets.isPending ? (
        <Loading />
      ) : (
        <nav aria-label="Targets">
          {entries.slice(offset, offset + 20).map(([name, members]) => {
            const active = members.some(
              (target) => location.pathname === `/targets/${target.id}`,
            );
            const busy = members.some((target) => running.has(target.id));
            const anchor = [...members].sort(
              (a, b) =>
                (a.created_at || "").localeCompare(b.created_at || "") ||
                a.id.localeCompare(b.id),
            )[0];
            return (
              <div key={name}>
                <Link
                  className={active ? "active" : undefined}
                  aria-current={active ? "page" : undefined}
                  aria-label={`${name}${busy ? " Running" : ""}`}
                  to={`/targets/${anchor.id}?session=${session}`}
                >
                  <span className="target-host" title={name}>{name}</span>
                  {busy && <small className="target-running">Running</small>}
                </Link>
                <details className="target-urls">
                  <summary>
                    {members.length} URL{members.length === 1 ? "" : "s"}
                  </summary>
                  {members.map((target) => (
                    <Link
                      key={target.id}
                      to={`/targets/${target.id}?session=${session}`}
                    >
                      {target.value}
                    </Link>
                  ))}
                </details>
              </div>
            );
          })}
          {!entries.length && <p className="muted">No targets yet.</p>}
        </nav>
      )}
      {entries.length > 20 && (
        <Pager
          offset={offset}
          total={entries.length}
          size={20}
          onChange={setOffset}
        />
      )}
    </section>
  );
}
