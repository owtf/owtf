import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { request, useAction, useAPI } from "../lib/api";
import type { Session, Target } from "../lib/types";
import { Button, ErrorMessage } from "../components/shared";
import { Textarea } from "../components/ui/textarea";

export default function AddTargets({ session }: { session: string }) {
  const current = useAPI<Session>(`/sessions/${session}`);
  const navigate = useNavigate();
  const [draft, setDraft] = useState("");
  const [notice, setNotice] = useState("");
  const add = useAction(async () => {
    const result = await request<{
      created: Target[];
      duplicates: Target[];
      invalid: { input: string; error: string }[];
    }>(`/sessions/${session}/targets`, "POST", {
      targets: draft
        .split("\n")
        .map((value) => value.trim())
        .filter(Boolean),
    });
    if (result.invalid.length) {
      setNotice(
        `${result.created.length} added, ${result.duplicates.length} duplicate(s). ${result.invalid.map((value) => `${value.input}: ${value.error}`).join("; ")}`,
      );
      setDraft(result.invalid.map((value) => value.input).join("\n"));
    } else {
      navigate(`/?session=${session}`);
    }
  });
  return (
    <section className="session-create">
      <span className="caption">{current.data?.name}</span>
      <h1>Add targets</h1>
      <p>Add only targets you have permission to test.</p>
      <form
        onSubmit={(event) => {
          event.preventDefault();
          add.mutate(undefined);
        }}
      >
        <label htmlFor="target-urls">Target URLs</label>
        <Textarea
          id="target-urls"
          value={draft}
          onChange={(event) => setDraft(event.target.value)}
          placeholder="https://app.example.com"
          disabled={add.isPending}
        />
        <div className="section-head">
          <span className="muted">One per line. No scan starts here.</span>
          <Button type="submit" disabled={!draft.trim() || add.isPending}>
            Add targets
          </Button>
        </div>
        {notice && <p role="status">{notice}</p>}
        <ErrorMessage error={add.error || current.error} />
      </form>
    </section>
  );
}
