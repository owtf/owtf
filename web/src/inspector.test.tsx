import { useState } from "react";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { expect, it } from "vitest";
import Inspector from "./components/Inspector";

function Workspace() {
  const [open, setOpen] = useState(false);
  return (
    <>
      <button onClick={() => setOpen(true)}>Inspect</button>
      {open && (
        <Inspector title="Evidence" onClose={() => setOpen(false)}>
          <p>Captured output</p>
        </Inspector>
      )}
    </>
  );
}

it("opens an optional non-modal panel and restores focus on Escape", async () => {
  render(<Workspace />);
  const trigger = screen.getByRole("button", { name: "Inspect" });
  await userEvent.click(trigger);
  expect(
    screen.getByRole("complementary", { name: "Evidence" }),
  ).toBeInTheDocument();
  expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  expect(screen.getByRole("button", { name: "Close Evidence" })).toHaveFocus();
  await userEvent.keyboard("{Escape}");
  expect(screen.queryByRole("complementary")).not.toBeInTheDocument();
  expect(trigger).toHaveFocus();
});

it("closes with the panel action", async () => {
  render(<Workspace />);
  await userEvent.click(screen.getByRole("button", { name: "Inspect" }));
  await userEvent.click(screen.getByRole("button", { name: "Close Evidence" }));
  expect(screen.queryByText("Captured output")).not.toBeInTheDocument();
});

it("expands and restores without losing its content", async () => {
  render(<Workspace />);
  await userEvent.click(screen.getByRole("button", { name: "Inspect" }));
  const toggle = screen.getByRole("button", { name: "Expand Evidence" });
  await userEvent.click(toggle);
  expect(toggle).toHaveAttribute("aria-pressed", "true");
  expect(screen.getByRole("complementary")).toHaveAttribute(
    "data-expanded",
    "true",
  );
  expect(screen.getByText("Captured output")).toBeVisible();
  await userEvent.click(toggle);
  expect(toggle).toHaveAttribute("aria-pressed", "false");
});
