import { useEffect, useState } from "react";
import {
  Routes,
  Route,
  NavLink,
  useNavigate,
  useLocation,
  useSearchParams,
} from "react-router-dom";
import { useAPI, useAction, request } from "./lib/api";
import type { Session } from "./lib/types";
import {
  Button,
  ErrorMessage,
  Loading,
  PageHead,
  safeURL,
} from "./components/shared";
import { Input } from "./components/ui/input";
import TargetSidebar from "./components/TargetSidebar";
import Targets from "./pages/Targets";
import AddTargets from "./pages/AddTargets";
import Report from "./pages/Report";
import Work from "./pages/Work";
import SessionReport from "./pages/SessionReport";
import Profiles from "./pages/Profiles";
import Runs from "./pages/Runs";
import Transactions from "./pages/Transactions";

function Help() {
  const query = useAPI<{
    sections: {
      id: string;
      title: string;
      links: { title: string; url: string; description?: string }[];
    }[];
  }>("/help");
  return (
    <>
      <PageHead
        title="Help"
        description="OWTF methodology and testing references."
      />
      <ErrorMessage error={query.error} />
      {query.isPending ? (
        <Loading />
      ) : (
        <div className="help-grid">
          {query.data?.sections.map((s) => (
            <section className="panel" key={s.id}>
              <h2>{s.title}</h2>
              <ul>
                {s.links.map((l) => (
                  <li key={l.url}>
                    <a href={safeURL(l.url)} target="_blank" rel="noreferrer">
                      {l.title}
                    </a>
                    {l.description && <p className="muted">{l.description}</p>}
                  </li>
                ))}
              </ul>
            </section>
          ))}
        </div>
      )}
    </>
  );
}
import Settings from "./pages/Settings";

export default function App() {
  const location = useLocation();
  const sessions = useAPI<Session[]>("/sessions");
  const [search, setSearch] = useSearchParams();
  const navigate = useNavigate();
  const [creating, setCreating] = useState(false);
  const [name, setName] = useState("");
  const [navigationOpen, setNavigationOpen] = useState(false);
  const session = search.get("session") || sessions.data?.[0]?.id || "";
  const exists = sessions.data?.some((s) => s.id === session);
  useEffect(() => {
    if (session && !search.get("session")) {
      const next = new URLSearchParams(search);
      next.set("session", session);
      setSearch(next, { replace: true });
    }
  }, [session, search, setSearch]);
  const create = useAction(async () => {
    const result = await request<Session>("/sessions", "POST", {
      name: name.trim(),
    });
    setCreating(false);
    setName("");
    navigate(`/targets/new?session=${result.id}`);
  });
  return (
    <>
      <div
        className={exists && !creating ? "workspace-shell" : "session-entry"}
      >
        {exists && !creating && (
          <Button
            className="workspace-menu"
            variant="ghost"
            aria-expanded={navigationOpen}
            aria-controls="workspace-navigation"
            onClick={() => setNavigationOpen(!navigationOpen)}
          >
            owtf: {navigationOpen ? "Close navigation" : "Session navigation"}
          </Button>
        )}
        {exists && !creating ? (
          <aside
            id="workspace-navigation"
            className="workspace-sidebar"
            data-open={navigationOpen}
            aria-label="Session workspace"
            onClick={(event) => {
              if ((event.target as HTMLElement).closest("a"))
                setNavigationOpen(false);
            }}
          >
            <NavLink
              className="brand"
              to={session ? `/?session=${session}` : "/"}
            >
              owtf
            </NavLink>

            <TargetSidebar key={session} session={session} />
            <nav className="sidebar-tools" aria-label="Session tools">
              {[
                ["/work", "Worklist"],
                ["/transactions", "Proxy"],
                ["/reports", "Reports"],
                ["/settings", "Settings"],
                ["/help", "Help"],
              ].map(([path, label]) => (
                <NavLink key={path} to={path + "?session=" + session}>
                  {label}
                </NavLink>
              ))}
            </nav>
          </aside>
        ) : (
          <header className="entry-controls">
            <NavLink
              className="brand"
              to="/"
              onClick={() => setCreating(false)}
            >
              owtf
            </NavLink>
          </header>
        )}
        <main key={`${location.pathname}:${session}:${creating}`}>
          {exists && !creating && (
            <header className="session-controls" aria-label="Session controls">
              <label>
                Session
                <select
                  aria-label="Session"
                  value={exists ? session : ""}
                  onChange={(e) => navigate(`/?session=${e.target.value}`)}
                >
                  <option value="" disabled>
                    Select session
                  </option>
                  {sessions.data?.map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.name}
                    </option>
                  ))}
                </select>
              </label>
              <Button
                size="sm"
                variant="ghost"
                onClick={() => {
                  create.reset();
                  setCreating(true);
                }}
              >
                New session
              </Button>
            </header>
          )}
          <ErrorMessage error={sessions.error} />
          {sessions.isPending ? (
            <Loading />
          ) : creating || !exists ? (
            <section className="session-create">
              <span className="caption">New session</span>
              <h1>Create session</h1>
              <p>A named space for targets and the evidence you collect.</p>
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  create.mutate(undefined);
                }}
              >
                <label>
                  Session name
                  <Input
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder="Client or research project"
                    required
                    maxLength={120}
                  />
                </label>
                <ErrorMessage error={create.error} />
                <Button
                  disabled={!name.trim() || create.isPending}
                  type="submit"
                >
                  Create session
                </Button>
              </form>
              {session && !exists && (
                <ErrorMessage error="Session not found. Create or open a session." />
              )}
              {!!sessions.data?.length && (
                <details>
                  <summary>Open session</summary>
                  {sessions.data.map((item) => (
                    <NavLink
                      className="session-choice"
                      key={item.id}
                      to={"/?session=" + item.id}
                      onClick={() => setCreating(false)}
                    >
                      {item.name}
                    </NavLink>
                  ))}
                </details>
              )}
            </section>
          ) : (
            <Routes>
              <Route
                path="/"
                element={<Targets key={session} session={session} />}
              />
              <Route
                path="/targets/new"
                element={<AddTargets key={session} session={session} />}
              />
              <Route path="/targets/:id" element={<Report />} />
              <Route
                path="/work"
                element={<Work key={session} session={session} />}
              />
              <Route
                path="/workers"
                element={<Work key={session} session={session} workers />}
              />
              <Route
                path="/transactions"
                element={<Transactions key={session} session={session} />}
              />
              <Route
                path="/reports"
                element={<SessionReport key={session} session={session} />}
              />
              <Route path="/profiles" element={<Profiles />} />
              <Route
                path="/runs"
                element={<Runs key={session} session={session} />}
              />
              <Route path="/settings" element={<Settings />} />
              <Route path="/help" element={<Help />} />
              <Route
                path="*"
                element={<p className="empty">Page not found.</p>}
              />
            </Routes>
          )}
        </main>
      </div>
    </>
  );
}
