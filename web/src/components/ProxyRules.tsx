import { useState } from "react";
import { request, useAPI, useAction } from "../lib/api";
import { Button, Confirm, ErrorMessage, Loading } from "./shared";
import { Textarea } from "./ui/textarea";

interface Rule {
  name: string;
  enabled?: boolean;
  phase: string;
  priority: number;
}
interface Configuration {
  rules: Rule[] | null;
}

export default function ProxyRules() {
  const config = useAPI<Configuration>("/proxy/interceptors");
  const [draft, setDraft] = useState<string | null>(null);
  const [change, setChange] = useState<
    { name: string; enabled: boolean } | "replace" | null
  >(null);
  const save = useAction(async () => {
    if (!change) return;
    if (change === "replace") {
      const value = JSON.parse(draft || "");
      if (!value || !Array.isArray(value.rules))
        throw new Error("Configuration must contain a rules array");
      await request("/proxy/interceptors", "PUT", value);
      setDraft(null);
    } else {
      await request("/proxy/interceptors", "PATCH", change);
    }
    setChange(null);
  });
  return (
    <section>
      <h2>Interceptor rules</h2>
      <p className="muted">
        Rules modify matching traffic in the shared proxy. Changes affect
        subsequent exchanges, not retained evidence.
      </p>
      <ErrorMessage error={config.error} />
      {config.isPending ? (
        <Loading />
      ) : (
        config.data && (
          <>
            {(config.data.rules || []).map((rule) => (
              <div className="transaction-row" key={rule.name}>
                <span>
                  {rule.name} · {rule.phase} · priority {rule.priority}
                </span>
                <Button
                  variant="outline"
                  onClick={() => {
                    save.reset();
                    setChange({
                      name: rule.name,
                      enabled: rule.enabled === false,
                    });
                  }}
                >
                  {rule.enabled === false ? "Enable" : "Disable"}
                </Button>
              </div>
            ))}
            {!config.data.rules?.length && <p>No interceptor rules.</p>}
            {draft === null ? (
              <Button
                variant="outline"
                onClick={() =>
                  setDraft(
                    JSON.stringify(
                      { ...config.data, rules: config.data.rules || [] },
                      null,
                      2,
                    ),
                  )
                }
              >
                Edit rules
              </Button>
            ) : (
              <div className="stack">
                <label>
                  Interceptor configuration (JSON)
                  <Textarea
                    rows={14}
                    value={draft}
                    onChange={(event) => setDraft(event.target.value)}
                  />
                </label>
                <p className="muted">
                  Replace applies the complete rule list. An empty rules array
                  removes all rules. The server validates before applying.
                </p>
                <div className="actions">
                  <Button
                    onClick={() => {
                      save.reset();
                      setChange("replace");
                    }}
                  >
                    Replace
                  </Button>
                  <Button variant="outline" onClick={() => setDraft(null)}>
                    Cancel
                  </Button>
                </div>
              </div>
            )}
          </>
        )
      )}
      <Confirm
        open={change !== null}
        title={
          change === "replace"
            ? "Replace interceptor rules?"
            : "Change interceptor rule?"
        }
        description="This changes how the shared proxy modifies future matching traffic."
        busy={save.isPending}
        error={save.error}
        onClose={() => setChange(null)}
        onConfirm={() => save.mutate(undefined)}
      />
    </section>
  );
}
