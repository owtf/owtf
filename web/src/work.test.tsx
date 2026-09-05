import { afterEach, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter } from "react-router-dom";
import userEvent from "@testing-library/user-event";
import Work from "./pages/Work";

afterEach(() => vi.unstubAllGlobals());

it.each([
  ["queued", "Pause", "POST", "/pause", false],
  ["paused", "Resume", "POST", "/resume", false],
  ["running", "Cancel", "POST", "/cancel", true],
  ["queued", "Remove", "DELETE", "", true],
] as const)(
  "%s work: %s sends one command",
  async (status, label, method, suffix, confirm) => {
    const fetch = vi.fn(
      async (url: string, options?: RequestInit) =>
        new Response(
          JSON.stringify(
            options?.method !== "GET"
              ? {}
              : url.includes("/tasks?")
                ? [
                    {
                      id: "task1",
                      target_id: "target1",
                      plugin_id: "OWTF-X-active",
                      status,
                      position: 0,
                    },
                  ]
                : [{ id: "target1", value: "http://localhost/" }],
          ),
        ),
    );
    vi.stubGlobal("fetch", fetch);
    const client = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false },
      },
    });
    render(
      <QueryClientProvider client={client}>
        <MemoryRouter>
          <Work session="session1" />
        </MemoryRouter>
      </QueryClientProvider>,
    );
    await userEvent.click(await screen.findByRole("button", { name: label }));
    if (confirm) {
      expect(
        fetch.mock.calls.filter(([, options]) => options?.method !== "GET"),
      ).toHaveLength(0);
      await userEvent.click(screen.getByRole("button", { name: "Confirm" }));
    }
    await waitFor(() =>
      expect(fetch).toHaveBeenCalledWith(
        `/api/v2/tasks/task1${suffix}`,
        expect.objectContaining({ method }),
      ),
    );
    expect(
      fetch.mock.calls.filter(([, options]) => options?.method !== "GET"),
    ).toHaveLength(1);
  },
);
