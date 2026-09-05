import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { request, useAPI } from "../lib/api";
import {
  Button,
  ErrorMessage,
  Loading,
  PageHead,
  SessionLink,
} from "../components/shared";
import { Textarea } from "../components/ui/textarea";

export default function Settings() {
  const config = useAPI<Record<string, unknown>>("/config");
  const [yaml, setYAML] = useState(
    "apiVersion: owtf.dev/v1alpha1\nkind: Config\n",
  );
  const validation = useMutation({
    mutationFn: () => request("/config/validate", "POST", { yaml }),
  });
  return (
    <>
      <PageHead
        title="Settings"
        description="Configuration supplied at server startup. Changes require a restart."
      />
      <ErrorMessage error={config.error} />
      <SessionLink to="/profiles" className="button-link">
        Profiles
      </SessionLink>
      {config.isPending ? (
        <Loading />
      ) : (
        config.data && (
          <section className="panel">
            <h2>Server configuration</h2>
            <p className="muted">
              Credentials are redacted. Proxy settings are startup defaults, not
              the live proxy state.
            </p>
            {Object.entries(config.data).map(([section, value]) => (
              <details key={section}>
                <summary>{section.replaceAll("_", " ")}</summary>
                <pre>{JSON.stringify(value, null, 2)}</pre>
              </details>
            ))}
          </section>
        )
      )}
      <form
        className="panel"
        onSubmit={(event) => {
          event.preventDefault();
          validation.mutate();
        }}
      >
        <h2>Validate configuration</h2>
        <p>
          Uses the same checks as <code>owtf config validate FILE</code>.
          Validation does not apply changes or read referenced files.
        </p>
        <label htmlFor="config-yaml">YAML configuration</label>
        <Textarea
          id="config-yaml"
          rows={10}
          value={yaml}
          disabled={validation.isPending}
          onChange={(event) => {
            setYAML(event.target.value);
            validation.reset();
          }}
        />
        <ErrorMessage error={validation.error} />
        {validation.isSuccess && (
          <p role="status">Configuration is valid. No changes applied.</p>
        )}
        <Button type="submit" disabled={!yaml.trim() || validation.isPending}>
          Validate
        </Button>
      </form>
    </>
  );
}
