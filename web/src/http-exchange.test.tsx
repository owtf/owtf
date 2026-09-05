import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { expect, it } from "vitest";
import HTTPExchange from "./components/HTTPExchange";

it("switches request and response headers and safely displays body text", async () => {
  render(
    <QueryClientProvider client={new QueryClient()}>
      <HTTPExchange
        request={{
          line: "GET /account",
          headers: { Accept: ["text/html"] },
          body: btoa("request body"),
        }}
        response={{
          line: "200",
          headers: { Server: ["local-test"] },
          body: btoa("<script>alert(1)</script>"),
        }}
      />
    </QueryClientProvider>,
  );
  expect(screen.getByText("Accept: text/html")).toBeVisible();
  await userEvent.click(
    within(screen.getByRole("tablist", { name: "request content" })).getByRole(
      "tab",
      { name: "Body" },
    ),
  );
  expect(screen.getByText("request body")).toBeVisible();
  await userEvent.click(
    screen.getByRole("tab", { name: "Response" }),
  );
  expect(screen.getByText("Server: local-test")).toBeVisible();
  await userEvent.click(
    within(screen.getByRole("tablist", { name: "response content" })).getByRole(
      "tab",
      { name: "Body" },
    ),
  );
  expect(screen.getByText("<script>alert(1)</script>")).toBeVisible();
  expect(document.querySelector("script")).toBeNull();
});
