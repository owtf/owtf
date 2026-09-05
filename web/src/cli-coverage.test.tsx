import { afterEach, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter } from "react-router-dom";
import type { ReactNode } from "react";
import userEvent from "@testing-library/user-event";
import PluginLauncher from "./components/PluginLauncher";
import SessionReport from "./pages/SessionReport";
import DiscoveredURLs from "./components/DiscoveredURLs";
import ExecutionMetrics from "./components/ExecutionMetrics";
import TaskDetail from "./components/TaskDetail";
import type { Task } from "./lib/types";
import AddTargets from "./pages/AddTargets";
import PluginReport from "./components/PluginReport";
import type { Report as TargetReport } from "./lib/types";
import TargetRunHistory from "./components/TargetRunHistory";
import { InterceptionEditor } from "./components/ProxyInterception";
import Repeater from "./components/Repeater";
import ProxyRules from "./components/ProxyRules";
import ImportHAR from "./components/ImportHAR";
import Targets from "./pages/Targets";

it("sends explicit target type and false scope filters", async () => {
  const fetch = vi.fn(
    async (_url: string) =>
      new Response('{"data":[],"records_filtered":0,"records_total":0}'),
  );
  vi.stubGlobal("fetch", fetch);
  mount(<Targets session="s1" />);
  await screen.findByText(
    "No targets match. Add a target or change the search.",
  );
  expect(fetch.mock.calls[0][0]).not.toContain("scope=");
  await userEvent.selectOptions(
    screen.getByLabelText("Target type"),
    "hostname",
  );
  await userEvent.selectOptions(screen.getByLabelText("Scope filter"), "false");
  await waitFor(() =>
    expect(
      fetch.mock.calls.some(
        ([url]) => url.includes("kind=hostname") && url.includes("scope=false"),
      ),
    ).toBe(true),
  );
});

it("preserves multiple plugin types in a group launch", async () => {
  const fetch = vi.fn(
    async (url: string, init?: RequestInit) =>
      new Response(
        JSON.stringify(
          init?.method === "POST"
            ? { id: "run1" }
            : url.endsWith("/plugins")
              ? ["active", "passive", "grep"].map((type) => ({
                  id: `OWTF-X-${type}`,
                  title: type,
                  description: "",
                  group: "web",
                  type,
                  availability: "ready",
                  inputs: [],
                }))
              : url.includes("/targets")
                ? [{ id: "t1", value: "http://localhost/" }]
                : [],
        ),
      ),
  );
  vi.stubGlobal("fetch", fetch);
  mount(
    <PluginLauncher
      session="s1"
      targets={["t1"]}
      onClose={() => {}}
      onLaunched={() => {}}
    />,
  );
  await userEvent.click(
    await screen.findByRole("tab", { name: "Launch in groups" }),
  );
  await userEvent.selectOptions(screen.getByLabelText("Group"), "web");
  await userEvent.click(screen.getByRole("checkbox", { name: "active" }));
  await userEvent.click(screen.getByRole("checkbox", { name: "passive" }));
  await userEvent.click(screen.getByRole("button", { name: "Run" }));
  await waitFor(() =>
    expect(fetch).toHaveBeenCalledWith(
      "/api/v2/runs",
      expect.objectContaining({ method: "POST" }),
    ),
  );
  const sent = fetch.mock.calls.find(([, init]) => init?.method === "POST")!;
  expect(JSON.parse(sent[1]!.body as string).plugin_types).toEqual([
    "active",
    "passive",
  ]);
});

it("uploads a selected HAR once as multipart without replaying traffic", async () => {
  const fetch = vi.fn(async (url: string, options?: RequestInit) => {
    if (options?.method === "POST") return new Response('{"imported":2}');
    return new Response('[{"id":"target1","value":"http://localhost/"}]');
  });
  vi.stubGlobal("fetch", fetch);
  mount(<ImportHAR session="session1" onClose={() => {}} />);
  expect(screen.getByRole("button", { name: "Import" })).toBeDisabled();
  await screen.findByRole("option", { name: "http://localhost/" });
  await userEvent.selectOptions(screen.getByLabelText("Target"), "target1");
  const file = new File(['{"log":{"entries":[]}}'], "capture.har", {
    type: "application/json",
  });
  await userEvent.upload(screen.getByLabelText("HAR file"), file);
  expect(screen.getByRole("button", { name: "Import" })).toBeEnabled();
  // jsdom does not treat user-event's FileList as satisfying native required validation.
  fireEvent.submit(
    screen.getByRole("button", { name: "Import" }).closest("form")!,
  );
  await screen.findByText("Imported 2 transactions.");
  const uploads = fetch.mock.calls.filter(
    ([, options]) => options?.method === "POST",
  );
  expect(uploads).toHaveLength(1);
  expect(uploads[0][0]).toBe("/api/v2/targets/target1/transactions/import");
  expect(uploads[0][1]?.headers).toBeUndefined();
  expect((uploads[0][1]?.body as FormData).get("har")).toBe(file);
  expect(screen.getByRole("button", { name: "Import" })).toBeDisabled();
  expect(fetch.mock.calls.some(([url]) => url.includes("repeater"))).toBe(
    false,
  );
});

it("requires confirmation before changing a proxy rule", async () => {
  const fetch = vi.fn(
    async () =>
      new Response(
        JSON.stringify({
          rules: [{ name: "test", phase: "request", priority: 1 }],
        }),
      ),
  );
  vi.stubGlobal("fetch", fetch);
  mount(<ProxyRules />);
  await userEvent.click(await screen.findByRole("button", { name: "Disable" }));
  expect(
    fetch.mock.calls.every(
      (call) =>
        !((call as unknown[])[1] as RequestInit)?.method ||
        ((call as unknown[])[1] as RequestInit).method === "GET",
    ),
  ).toBe(true);
  expect(
    screen.getByRole("dialog", { name: "Change interceptor rule?" }),
  ).toBeInTheDocument();
  await userEvent.click(screen.getByRole("button", { name: "Confirm" }));
  await waitFor(() =>
    expect(fetch).toHaveBeenCalledWith(
      "/api/v2/proxy/interceptors",
      expect.objectContaining({
        method: "PATCH",
        body: '{"name":"test","enabled":false}',
      }),
    ),
  );
  expect(
    fetch.mock.calls.filter(
      (call) => ((call as unknown[])[1] as RequestInit)?.method === "PATCH",
    ),
  ).toHaveLength(1);
});

it("sends repeater traffic only explicitly and never retries failure", async () => {
  const fetch = vi.fn(
    async () => new Response('{"error":"connection failed"}', { status: 502 }),
  );
  vi.stubGlobal("fetch", fetch);
  mount(
    <Repeater
      initial={{
        method: "GET",
        url: "http://localhost/",
        headers: {},
        body_base64: "",
      }}
    />,
  );
  expect(fetch).not.toHaveBeenCalled();
  await userEvent.click(screen.getByRole("button", { name: "Send" }));
  await screen.findByText("connection failed");
  expect(fetch).toHaveBeenCalledTimes(1);
  expect(fetch).toHaveBeenCalledWith(
    "/api/v2/proxy/repeater",
    expect.objectContaining({
      method: "POST",
      body: JSON.stringify({
        method: "GET",
        url: "http://localhost/",
        headers: {},
        body_base64: "",
      }),
    }),
  );
});

afterEach(() => vi.unstubAllGlobals());
it("continues an unchanged interception with no replacements or retries", async () => {
  const fetch = vi.fn(async () => new Response("{}"));
  const resolved = vi.fn();
  vi.stubGlobal("fetch", fetch);
  mount(
    <InterceptionEditor
      item={{
        id: "paused1",
        phase: "request",
        method: "GET",
        url: "http://localhost/",
        headers: { "X-Test": ["one", "two"] },
        body_base64: "AP8=",
        expires_at: "2026-09-04T20:00:00Z",
      }}
      onResolved={resolved}
    />,
  );
  await userEvent.click(screen.getByRole("button", { name: "Continue" }));
  await waitFor(() => expect(resolved).toHaveBeenCalledOnce());
  expect(fetch).toHaveBeenCalledTimes(1);
  expect(fetch).toHaveBeenCalledWith(
    "/api/v2/proxy/interception/pending/paused1/continue",
    expect.objectContaining({ method: "POST", body: "{}" }),
  );
});

it("rejects malformed interception headers without sending a command", async () => {
  const fetch = vi.fn();
  vi.stubGlobal("fetch", fetch);
  mount(
    <InterceptionEditor
      item={{
        id: "paused2",
        phase: "response",
        method: "GET",
        url: "http://localhost/",
        status_code: 200,
        headers: {},
        body_base64: "",
        expires_at: "2026-09-04T20:00:00Z",
      }}
      onResolved={() => {}}
    />,
  );
  fireEvent.change(screen.getByLabelText("Headers (JSON, values are arrays)"), {
    target: { value: "{" },
  });
  await userEvent.click(screen.getByRole("button", { name: "Continue" }));
  await screen.findByRole("alert");
  expect(fetch).not.toHaveBeenCalled();
});
it("requires confirmation before cancelling an execution from history", async () => {
  const fetch = vi.fn(async () => new Response("{}"));
  const onReview = vi.fn();
  vi.stubGlobal("fetch", fetch);
  const task = {
    id: "active",
    plugin_id: "p",
    status: "running",
    created_at: "2026-09-01",
  } as Task;
  mount(<TargetRunHistory tasks={[task]} onReview={onReview} />);
  fireEvent.click(
    screen.getByRole("button", { name: "Review output", hidden: true }),
  );
  expect(onReview).toHaveBeenCalledWith(task);
  fireEvent.click(
    screen.getByRole("button", { name: "Cancel this run", hidden: true }),
  );
  expect(fetch).not.toHaveBeenCalled();
  await userEvent.click(screen.getByRole("button", { name: "Confirm" }));
  await waitFor(() => expect(fetch).toHaveBeenCalledTimes(1));
  expect(fetch).toHaveBeenCalledWith(
    "/api/v2/tasks/active/cancel",
    expect.objectContaining({ method: "POST" }),
  );
});
it("switches evidence and review together when selecting an older execution", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn(
      async (url: string) =>
        new Response(
          JSON.stringify(
            url.endsWith("/review")
              ? {
                  rank: "unranked",
                  disposition: "open",
                  notes: url.includes("older") ? "Older notes" : "Latest notes",
                }
              : [],
          ),
        ),
    ),
  );
  const tasks = [
    {
      id: "older",
      plugin_id: "p",
      created_at: "2026-09-01",
      status: "succeeded",
    },
    {
      id: "latest",
      plugin_id: "p",
      created_at: "2026-09-02",
      status: "succeeded",
    },
  ] as Task[];
  const report = {
    artifacts: [
      { id: "a", task_id: "older", name: "old.txt", size: 1 },
      { id: "b", task_id: "latest", name: "new.txt", size: 2 },
    ],
    findings: [],
    observations: [],
  } as unknown as TargetReport;
  mount(<PluginReport report={report} tasks={tasks} />);
  await screen.findByDisplayValue("Latest notes");
  expect(screen.getByRole("link", { name: /new.txt/ })).toBeInTheDocument();
  fireEvent.change(screen.getByLabelText("Execution"), {
    target: { value: "older" },
  });
  await screen.findByDisplayValue("Older notes");
  expect(screen.getByRole("link", { name: /old.txt/ })).toHaveAttribute(
    "href",
    "/api/v2/artifacts/a",
  );
  expect(
    screen.queryByRole("link", { name: /new.txt/ }),
  ).not.toBeInTheDocument();
});
it("launches the edited target selection from the inline catalog", async () => {
  const fetch = vi.fn(
    async (url: string, init?: RequestInit) =>
      new Response(
        JSON.stringify(
          init?.method === "POST"
            ? {}
            : url.endsWith("/targets")
              ? [
                  { id: "t1", value: "first.test" },
                  { id: "t2", value: "second.test" },
                ]
              : [
                  {
                    id: "plugin-active",
                    title: "Local plugin",
                    type: "active",
                    group: "web",
                    availability: "ready",
                    inputs: [],
                  },
                ],
        ),
      ),
  );
  vi.stubGlobal("fetch", fetch);
  mount(
    <PluginLauncher
      session="s1"
      targets={["t1"]}
      onClose={() => {}}
      onLaunched={() => {}}
    />,
  );
  await screen.findByLabelText("Target second.test");
  fireEvent.click(screen.getByLabelText("Target first.test"));
  fireEvent.click(screen.getByLabelText("Target second.test"));
  fireEvent.click(screen.getByLabelText("Select plugin-active"));
  await userEvent.click(screen.getByRole("button", { name: "Run" }));
  await waitFor(() =>
    expect(fetch.mock.calls.some(([, init]) => init?.method === "POST")).toBe(
      true,
    ),
  );
  const call = fetch.mock.calls.find(([, init]) => init?.method === "POST")!;
  expect(JSON.parse(call[1]!.body as string).target_ids).toEqual(["t2"]);
  expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  expect(screen.queryByRole("table")).not.toBeInTheDocument();
});
it("adds targets without launching work and retains invalid input for correction", async () => {
  const fetch = vi.fn(
    async (_url: string, init?: RequestInit) =>
      new Response(
        JSON.stringify(
          init?.method === "POST"
            ? {
                created: [{ id: "t1" }],
                duplicates: [],
                invalid: [{ input: "bad target", error: "invalid target" }],
              }
            : { id: "s1", name: "Local review" },
        ),
      ),
  );
  vi.stubGlobal("fetch", fetch);
  mount(<AddTargets session="s1" />);
  await screen.findByText("Local review");
  fireEvent.change(screen.getByLabelText("Target URLs"), {
    target: { value: "http://127.0.0.1\nbad target" },
  });
  await userEvent.click(screen.getByRole("button", { name: "Add targets" }));
  await screen.findByText(/1 added, 0 duplicate/);
  expect(screen.getByLabelText("Target URLs")).toHaveValue("bad target");
  expect(
    fetch.mock.calls.filter(([, init]) => init?.method === "POST"),
  ).toHaveLength(1);
  expect(fetch.mock.calls.some(([url]) => url.includes("/runs"))).toBe(false);
});
it("does not expose or fetch reviews outside target reports", async () => {
  const fetch = vi.fn(async (_url: string) => new Response("[]"));
  vi.stubGlobal("fetch", fetch);
  mount(<TaskDetail task={{ id: "task1", status: "succeeded" } as Task} />);
  await screen.findByText("No events recorded yet.");
  expect(screen.queryByText("Output review")).not.toBeInTheDocument();
  expect(
    fetch.mock.calls.every((args) => !String(args[0]).includes("/review")),
  ).toBe(true);
});

it("shows actual metrics, zero counts, and a separate service health state", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn(
      async (url: string) =>
        new Response(
          JSON.stringify(
            url.endsWith("/health")
              ? { status: "ok" }
              : {
                  tasks: { total: 0 },
                  attempts: { average_duration_ms: 125 },
                  outputs: { transactions: 7 },
                  workers: { running: 0 },
                },
          ),
        ),
    ),
  );
  mount(<ExecutionMetrics />);
  await screen.findByText("Service healthy");
  expect(await screen.findByText("125 ms")).toBeInTheDocument();
  expect(screen.getByText("7")).toBeInTheDocument();
  expect(screen.getAllByText("0")).toHaveLength(2);
  expect(screen.queryByRole("progressbar")).not.toBeInTheDocument();
});
function mount(element: ReactNode) {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={["/?session=s1"]}>{element}</MemoryRouter>
    </QueryClientProvider>,
  );
}
it("uses server group semantics and the selected profile, not individual IDs", async () => {
  const fetch = vi.fn(
    async (url: string, init?: RequestInit) =>
      new Response(
        JSON.stringify(
          init?.method === "POST"
            ? {}
            : url.endsWith("/plugins")
              ? [
                  {
                    id: "OWTF-X-active",
                    title: "Ready",
                    description: "",
                    group: "web",
                    type: "active",
                    inputs: [],
                    availability: "ready",
                  },
                  {
                    id: "OWTF-Y-active",
                    title: "Missing",
                    description: "",
                    group: "web",
                    type: "active",
                    inputs: [],
                    availability: "blocked",
                    reason: "No executable",
                  },
                ]
              : url.endsWith("/profiles/default")
                ? { name: "default", plugins: ["OWTF-X-active"] }
                : [{ name: "default", plugins: ["OWTF-X-active"] }],
        ),
      ),
  );
  vi.stubGlobal("fetch", fetch);
  mount(
    <PluginLauncher
      session="s1"
      targets={["t1"]}
      onClose={() => {}}
      onLaunched={() => {}}
    />,
  );
  await userEvent.click(
    await screen.findByRole("tab", { name: "Launch in groups" }),
  );
  fireEvent.change(screen.getByLabelText("Group"), {
    target: { value: "web" },
  });
  await screen.findByRole("option", { name: "default" });
  fireEvent.change(screen.getByLabelText("Profile"), {
    target: { value: "default" },
  });
  await screen.findByText("Profile: default");
  expect(screen.getByLabelText("Select OWTF-Y-active")).toBeChecked();
  expect(screen.getByLabelText("Select OWTF-Y-active")).toBeDisabled();
  fireEvent.click(screen.getByRole("button", { name: "Run" }));
  await waitFor(() =>
    expect(fetch.mock.calls.some(([, init]) => init?.method === "POST")).toBe(
      true,
    ),
  );
  const body = JSON.parse(
    fetch.mock.calls.find(([, init]) => init?.method === "POST")![1]!
      .body as string,
  );
  expect(body).toEqual({
    session_id: "s1",
    target_ids: ["t1"],
    plugin_group: "web",
    plugin_types: [],
    profile: "default",
    plugin_inputs: {},
  });
});
it("uses the same disposition selection for report and export", async () => {
  const fetch = vi.fn(
    async (_url: string) =>
      new Response(
        JSON.stringify({
          session: { id: "s1", name: "Review" },
          summary: { targets: 0, tasks: 0, transactions: 0, artifacts: 0 },
          targets: [],
          tasks: [],
        }),
      ),
  );
  vi.stubGlobal("fetch", fetch);
  mount(<SessionReport session="s1" />);
  await screen.findByText("No targets in this session.");
  fireEvent.click(screen.getByLabelText("confirmed"));
  await waitFor(() => expect(fetch.mock.calls.length).toBe(2));
  expect(fetch.mock.calls[1][0]).toBe(
    "/api/v2/sessions/s1/report?disposition=confirmed",
  );
  expect(
    screen.getByRole("link", { name: "Export session report" }),
  ).toHaveAttribute("href", "/api/v2/sessions/s1/export?disposition=confirmed");
});
it("omits unset URL booleans and sends explicit false filters", async () => {
  const fetch = vi.fn(
    async (_url: string) =>
      new Response(
        JSON.stringify({ data: [], records_total: 0, records_filtered: 0 }),
      ),
  );
  vi.stubGlobal("fetch", fetch);
  mount(<DiscoveredURLs target="t1" />);
  await screen.findByText("No results");
  fireEvent.change(screen.getByLabelText("Visited"), {
    target: { value: "false" },
  });
  await waitFor(() => expect(fetch.mock.calls.length).toBe(2));
  expect(fetch.mock.calls[0][0]).not.toContain("visited=");
  expect(fetch.mock.calls[1][0]).toContain("visited=false");
  expect(fetch.mock.calls[1][0]).not.toContain("scope=");
  expect(screen.getByLabelText("Visited")).toHaveValue("false");
});

it("sends HAR FormData without a JSON content type and does not retry failure", async () => {
  const { request } = await import("./lib/api");
  const fetch = vi.fn(
    async (_url: string, _init?: RequestInit) =>
      new Response(JSON.stringify({ error: "Invalid HAR" }), { status: 400 }),
  );
  vi.stubGlobal("fetch", fetch);
  const form = new FormData();
  form.append(
    "har",
    new File(["{}"], "capture.har", { type: "application/json" }),
  );
  await expect(
    request("/targets/t1/transactions/import", "POST", form),
  ).rejects.toThrow("Invalid HAR");
  expect(fetch).toHaveBeenCalledTimes(1);
  expect(fetch.mock.calls[0][1]?.body).toBe(form);
  expect(fetch.mock.calls[0][1]?.headers).toBeUndefined();
});
