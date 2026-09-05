import { useState } from "react";
import { request, useAction, useAPI } from "../lib/api";
import type { Target } from "../lib/types";
import { Button, ErrorMessage } from "./shared";

export default function CaptureTarget({ session }: { session: string }) {
  const [selected, setSelected] = useState("");
  const state = useAPI<{ target_id: string; last_error: string }>(
    "/proxy/capture",
    true,
  );
  const targets = useAPI<Target[]>(`/sessions/${session}/targets`);
  const save = useAction((target: string) =>
    request("/proxy/capture", "PUT", { target_id: target }),
  );
  const active = targets.data?.find(
    (target) => target.id === state.data?.target_id,
  );
  return (
    <section className="panel">
      <h3>Capture to target</h3>
      <p>
        Matching traffic is saved automatically, even after closing this page.
        Other origins remain in shared history. Restarting the proxy stops
        attachment.
      </p>
      <ErrorMessage error={state.error || targets.error || save.error} />
      {state.data?.last_error && (
        <p role="alert">Capture attachment failed: {state.data.last_error}</p>
      )}
      <p>
        {state.data?.target_id
          ? `Capturing to ${active?.value || state.data.target_id}`
          : "No capture target selected"}
      </p>
      <label>
        Target
        <select
          value={selected}
          onChange={(event) => setSelected(event.target.value)}
        >
          <option value="">Select target</option>
          {targets.data
            ?.filter((target) => target.kind === "url" && target.scope)
            .map((target) => (
              <option key={target.id} value={target.id}>
                {target.value}
              </option>
            ))}
        </select>
      </label>
      <div className="actions">
        <Button
          disabled={!selected || save.isPending || !state.data}
          onClick={() => save.mutate(selected)}
        >
          Capture
        </Button>
        <Button
          variant="outline"
          disabled={!state.data?.target_id || save.isPending}
          onClick={() => save.mutate("")}
        >
          Stop capture
        </Button>
      </div>
    </section>
  );
}
