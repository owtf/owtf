import { afterEach, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import TargetSidebar from "./components/TargetSidebar";
import App from "./App";

afterEach(() => vi.unstubAllGlobals());
it("does not render a sidebar before a session exists", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn(async () => new Response("[]")),
  );
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  render(
    <QueryClientProvider client={client}>
      <MemoryRouter>
        <App />
      </MemoryRouter>
    </QueryClientProvider>,
  );
  await screen.findByRole("heading", { name: "Create session" });
  expect(screen.queryByRole("complementary")).not.toBeInTheDocument();
  expect(
    screen.queryByRole("navigation", { name: "Primary navigation" }),
  ).not.toBeInTheDocument();
  expect(screen.getByRole("button", { name: "Create session" })).toBeDisabled();
  expect(screen.getByRole("link", { name: "owtf" })).toBeInTheDocument();
});
function mount(targets: unknown[], tasks: unknown[] = []) {
  vi.stubGlobal(
    "fetch",
    vi.fn(
      async (url: string) =>
        new Response(JSON.stringify(url.includes("/tasks?") ? tasks : targets)),
    ),
  );
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={["/targets/t1?session=s1"]}>
        <TargetSidebar session="s1" />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}
it("shows an empty session without inventing targets", async () => {
  mount([]);
  expect(await screen.findByText("No targets yet.")).toBeInTheDocument();
  expect(screen.getByRole("link", { name: "Add targets" })).toHaveAttribute(
    "href",
    "/targets/new?session=s1",
  );
});
it("groups same-host URLs without merging subdomains", async () => {
  mount([
    { id: "t1", kind: "url", value: "https://example.test/a" },
    { id: "t2", kind: "url", value: "http://example.test:8080/b" },
    { id: "t3", kind: "url", value: "https://api.example.test/" },
  ]);
  expect(
    await screen.findByRole("link", { name: "example.test" }),
  ).toHaveAttribute("aria-current", "page");
  expect(
    screen.getByRole("link", { name: "api.example.test" }),
  ).toBeInTheDocument();
  expect(screen.getByText("2 URLs")).toBeInTheDocument();
});
it("distinguishes the viewed target from a running background target", async () => {
  mount(
    [
      { id: "t1", kind: "url", value: "https://first.test" },
      { id: "t2", kind: "url", value: "https://second.test" },
    ],
    [{ target_id: "t2", status: "running" }],
  );
  const viewed = await screen.findByRole("link", {
    name: "first.test",
  });
  expect(viewed).toHaveAttribute("aria-current", "page");
  const running = await screen.findByRole("link", {
    name: "second.test Running",
  });
  expect(running).not.toHaveAttribute("aria-current");
  expect(running).toHaveAttribute("href", "/targets/t2?session=s1");
});
