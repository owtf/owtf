import { useEffect, useState } from "react";
import {
  Routes,
  Route,
  NavLink,
  useNavigate,
  useSearchParams,
} from "react-router-dom";
import { useAPI, useAction, request } from "./lib/api";
import type { Session } from "./lib/types";
import {
  Button,
  ErrorMessage,
  Loading,
  Modal,
  PageHead,
  safeURL,
} from "./components/shared";
import { Input } from "./components/ui/input";
import Targets from "./pages/Targets";
import Report from "./pages/Report";
import Work from "./pages/Work";
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
function Settings() {
  return (
    <>
      <PageHead
        title="Settings"
        description="Runtime configuration is owned by the Go service."
      />
      <section className="panel">
        <h2>Configuration file</h2>
        <p>
          Edit <code>.owtf/config.yaml</code> and restart the service. Validate
          with <code>owtf config validate FILE</code>.
        </p>
        <p>
          <code>owtf config show</code> displays the invoking process’s
          configuration, not this browser’s server settings.
        </p>
        <h3>Diagnostics and HTTP collectors</h3>
        <p>
          Use <code>logLevel</code>, <code>http.userAgent</code> and{" "}
          <code>http.requestTimeoutSeconds</code>. Plugin tools retain their own
          inputs.
        </p>
        <p className="muted">
          This page does not pretend to read or edit live settings. No generic
          configuration API is exposed.
        </p>
      </section>
    </>
  );
}
export default function App() {
  const sessions = useAPI<Session[]>("/sessions");
  const [search, setSearch] = useSearchParams();
  const navigate = useNavigate();
  const [creating, setCreating] = useState(false);
  const [name, setName] = useState("");
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
    navigate(`/?session=${result.id}`);
  });
  return (
    <>
      <header className="topbar">
        <NavLink className="brand" to={session ? `/?session=${session}` : "/"}>
          OWASP <strong>OWTF</strong>
        </NavLink>
        <nav aria-label="Primary navigation">
          {[
            ["/", "Targets"],
            ["/work", "Worklist"],
            ["/workers", "Workers"],
            ["/transactions", "Transactions"],
            ["/settings", "Settings"],
            ["/help", "Help"],
          ].map(([path, label]) => (
            <NavLink
              key={path}
              end={path === "/"}
              to={`${path}${session ? `?session=${session}` : ""}`}
            >
              {label}
            </NavLink>
          ))}
        </nav>
      </header>
      <div className="sessionbar">
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
          variant="outline"
          onClick={() => {
            create.reset();
            setCreating(true);
          }}
        >
          New session
        </Button>
      </div>
      <main>
        <ErrorMessage error={sessions.error} />
        {sessions.isPending ? (
          <Loading />
        ) : !exists ? (
          <section className="panel empty">
            <h1>{session ? "Session not found" : "Start an OWTF session"}</h1>
            <p>
              Select a session above or create one to organize targets and
              evidence.
            </p>
          </section>
        ) : (
          <Routes>
            <Route
              path="/"
              element={<Targets key={session} session={session} />}
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
            <Route path="/settings" element={<Settings />} />
            <Route path="/help" element={<Help />} />
            <Route
              path="*"
              element={<p className="empty">Page not found.</p>}
            />
          </Routes>
        )}
      </main>
      <Modal
        open={creating}
        onClose={() => {
          if (!create.isPending) setCreating(false);
        }}
        title="New session"
        description="A session groups targets and evidence. It is not an account."
      >
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
              required
              maxLength={120}
            />
          </label>
          <ErrorMessage error={create.error} />
          <Button disabled={!name.trim() || create.isPending} type="submit">
            Create session
          </Button>
        </form>
      </Modal>
    </>
  );
}
