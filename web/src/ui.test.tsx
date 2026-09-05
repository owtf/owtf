import { describe, it, expect, vi, afterEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter } from "react-router-dom";
import PluginLauncher, { inputValue } from "./components/PluginLauncher";
import { groupTasks } from "./pages/Report";
import { safeURL } from "./components/shared";
import { request, queryClient } from "./lib/api";
import type { Plugin, Task } from "./lib/types";
const plugins: Plugin[] = [
  {
    id: "OWTF-X-001-active",
    title: "Local fixture",
    description: "Fixture only",
    group: "web",
    type: "active",
    runtime_type: "command",
    availability: "ready",
    techniques: [],
    inputs: [{ name: "port", type: "integer" }],
  },
  {
    id: "OWTF-X-002-active",
    title: "Unavailable fixture",
    description: "Not installed",
    group: "network",
    type: "active",
    runtime_type: "command",
    availability: "blocked",
    reason: "Missing fixture",
    techniques: [],
    inputs: [],
  },
];
afterEach(() => vi.unstubAllGlobals());
function launcher() {
  const client = new QueryClient({
    defaultOptions: queryClient.getDefaultOptions(),
  });
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter>
        <PluginLauncher
          session="s1"
          targets={["t1"]}
          onClose={() => {}}
          onLaunched={() => {}}
        />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}
describe("plugin launcher", () => {
  it("starts empty, disables unavailable tools, and submits only selected IDs with typed inputs", async () => {
    const fetch = vi.fn(
      async (_url: unknown, init?: RequestInit) =>
        new Response(JSON.stringify(init?.method === "POST" ? {} : plugins), {
          status: 200,
        }),
    );
    vi.stubGlobal("fetch", fetch);
    launcher();
    expect(await screen.findByRole("button", { name: "Run" })).toBeDisabled();
    expect(screen.getByLabelText("Select OWTF-X-002-active")).toBeDisabled();
    fireEvent.click(screen.getByLabelText("Select OWTF-X-001-active"));
    fireEvent.change(screen.getByLabelText("OWTF-X-001-active port"), {
      target: { value: "8080" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Run" }));
    await waitFor(() =>
      expect(fetch.mock.calls.some(([, init]) => init?.method === "POST")).toBe(
        true,
      ),
    );
    const call = fetch.mock.calls.find(([, init]) => init?.method === "POST")!;
    expect(JSON.parse(call[1]!.body as string)).toEqual({
      session_id: "s1",
      target_ids: ["t1"],
      plugin_ids: ["OWTF-X-001-active"],
      plugin_inputs: { "OWTF-X-001-active": { port: 8080 } },
    });
  });
  it("shows launch failures without automatically retrying", async () => {
    const fetch = vi.fn(
      async (_url: unknown, init?: RequestInit) =>
        new Response(
          JSON.stringify(
            init?.method === "POST" ? { error: "Fixture refused" } : plugins,
          ),
          { status: init?.method === "POST" ? 400 : 200 },
        ),
    );
    vi.stubGlobal("fetch", fetch);
    launcher();
    fireEvent.click(await screen.findByLabelText("Select OWTF-X-001-active"));
    fireEvent.click(screen.getByRole("button", { name: "Run" }));
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Fixture refused",
    );
    expect(
      fetch.mock.calls.filter(([, init]) => init?.method === "POST"),
    ).toHaveLength(1);
    expect(queryClient.getDefaultOptions().mutations?.retry).toBe(false);
  });
});
it("rejects invalid integer input rather than truncating it", () => {
  for (const value of ["1.5", "1e2", "x", "9007199254740992"])
    expect(() =>
      inputValue({ name: "port", type: "integer" }, value),
    ).toThrow();
  expect(inputValue({ name: "port", type: "integer" }, "8080")).toBe(8080);
});
it("groups repeated report executions by plugin ID", () => {
  const tasks = [
    {
      id: "a",
      plugin_id: "OWTF-A-active",
      techniques: [{ code: "OWTF-A", title: "A" }],
    },
    {
      id: "b",
      plugin_id: "OWTF-A-active",
      techniques: [{ code: "OWTF-A", title: "A" }],
    },
  ] as Task[];
  expect(groupTasks(tasks)[0][1].tasks).toHaveLength(2);
});
it("retains repeated plugin runs without technique metadata", () => {
  const tasks = [
    { id: "first", plugin_id: "local-command", techniques: [] },
    { id: "second", plugin_id: "local-command" },
  ] as unknown as Task[];
  const groups = groupTasks(tasks);
  expect(groups).toHaveLength(1);
  expect(groups[0][0]).toBe("local-command");
  expect(groups[0][1].tasks.map((task) => task.id)).toEqual([
    "first",
    "second",
  ]);
});
it("rejects script and data links", () => {
  expect(safeURL("javascript:alert(1)")).toBeUndefined();
  expect(safeURL("data:text/html,hi")).toBeUndefined();
  expect(safeURL("https://example.com/")).toBe("https://example.com/");
});
it("handles a successful empty response", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn(async () => new Response(null, { status: 204 })),
  );
  expect(await request("/targets/t1", "DELETE")).toBeUndefined();
});

import Work from "./pages/Work";
import Transactions from "./pages/Transactions";
import { ReviewEditor } from "./components/TaskDetail";
import App from "./App";
import type { ReactNode } from "react";
function page(children: ReactNode) {
  return render(
    <QueryClientProvider
      client={
        new QueryClient({ defaultOptions: queryClient.getDefaultOptions() })
      }
    >
      <MemoryRouter>{children}</MemoryRouter>
    </QueryClientProvider>,
  );
}
it("exposes only supported work transitions and requires cancellation confirmation", async () => {
  const task = {
    id: "task1",
    plugin_id: "fixture",
    target_id: "t1",
    status: "running",
    position: 1,
    created_at: new Date().toISOString(),
  };
  const fetch = vi.fn(
    async (url: unknown) =>
      new Response(
        JSON.stringify(String(url).includes("/tasks?") ? [task] : []),
      ),
  );
  vi.stubGlobal("fetch", fetch);
  page(<Work session="s1" />);
  fireEvent.click(await screen.findByRole("button", { name: "Cancel" }));
  expect(
    screen.queryByRole("button", { name: "Pause" }),
  ).not.toBeInTheDocument();
  expect(
    screen.queryByRole("button", { name: "Remove" }),
  ).not.toBeInTheDocument();
  expect(
    fetch.mock.calls.some(([url]) => String(url).endsWith("/cancel")),
  ).toBe(false);
  fireEvent.click(screen.getByRole("button", { name: "Confirm" }));
  await waitFor(() =>
    expect(
      fetch.mock.calls.some(([url]) =>
        String(url).endsWith("/tasks/task1/cancel"),
      ),
    ).toBe(true),
  );
});
it("shows resume and removal for paused work", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn(
      async (url: unknown) =>
        new Response(
          JSON.stringify(
            String(url).includes("/tasks?")
              ? [
                  {
                    id: "t1",
                    plugin_id: "fixture",
                    target_id: "x",
                    status: "paused",
                    position: 1,
                  },
                ]
              : [],
          ),
        ),
    ),
  );
  page(<Work session="s1" />);
  expect(await screen.findByRole("button", { name: "Resume" })).toBeEnabled();
  expect(screen.getByRole("button", { name: "Remove" })).toBeEnabled();
  expect(
    screen.queryByRole("button", { name: "Pause" }),
  ).not.toBeInTheDocument();
});
it("saves rank, disposition, and notes together", async () => {
  const fetch = vi.fn(async () => new Response("{}"));
  vi.stubGlobal("fetch", fetch);
  page(
    <ReviewEditor
      task="t1"
      initial={{
        task_id: "t1",
        rank: "unranked",
        disposition: "open",
        notes: "",
      }}
    />,
  );
  fireEvent.change(screen.getByLabelText("Notes"), {
    target: { value: "Evidence reviewed" },
  });
  fireEvent.change(screen.getByLabelText("Severity"), {
    target: { value: "low" },
  });
  fireEvent.click(screen.getByRole("button", { name: "Save review" }));
  expect(await screen.findByRole("status")).toHaveTextContent("Review saved");
  expect(fetch).toHaveBeenCalledWith(
    "/api/v2/tasks/t1/review",
    expect.objectContaining({
      method: "PATCH",
      body: JSON.stringify({
        rank: "low",
        disposition: "open",
        notes: "Evidence reviewed",
      }),
    }),
  );
});
it("inspects captured transactions without sending replay traffic", async () => {
  const fetch = vi.fn(
    async () =>
      new Response(
        JSON.stringify({
          records_total: 1,
          records_filtered: 1,
          data: [
            {
              id: "x",
              method: "GET",
              status_code: 200,
              url: "http://localhost/",
              request_headers: '{"X-Test":["<script>bad</script>"]}',
              response_headers: "{}",
              duration_ms: 1,
            },
          ],
        }),
      ),
  );
  vi.stubGlobal("fetch", fetch);
  page(<Transactions session="s1" />);
  fireEvent.click(
    await screen.findByRole("button", { name: "GET http://localhost/" }),
  );
  expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  expect(screen.getByText(/<script>bad/)).toBeInTheDocument();
  expect(document.querySelector("script")).toBeNull();
  expect(
    screen.getByRole("button", { name: "Next transaction" }),
  ).toBeDisabled();
  expect(fetch).toHaveBeenCalledTimes(1);
});
it("does not create sessions implicitly", async () => {
  const fetch = vi.fn(async () => new Response("[]"));
  vi.stubGlobal("fetch", fetch);
  page(<App />);
  expect(
    await screen.findByRole("heading", { name: "Create session" }),
  ).toBeInTheDocument();
  expect(fetch).toHaveBeenCalledTimes(1);
});
it("renders API failures instead of silently treating them as success", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn(
      async () =>
        new Response('{"error":"Database unavailable"}', { status: 503 }),
    ),
  );
  page(<Transactions session="s1" />);
  expect(await screen.findByRole("alert")).toHaveTextContent(
    "Database unavailable",
  );
});
