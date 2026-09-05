import { useState } from "react";
import { useAPI, useAction, request } from "../lib/api";
import type { Plugin, PluginInput, Profile, Target } from "../lib/types";
import { Button, ErrorMessage, Loading, Pager, StateBadge } from "./shared";
import { Input } from "./ui/input";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "./ui/tabs";
import Inspector from "./Inspector";

export function inputValue(input: PluginInput, value: string): unknown {
  if (input.type === "integer") {
    if (!/^-?\d+$/.test(value))
      throw new Error(`${input.name} must be an integer`);
    const n = Number(value);
    if (!Number.isSafeInteger(n)) throw new Error(`${input.name} is too large`);
    return n;
  }
  if (input.type === "boolean") return value === "true";
  return value;
}
// Shared by the target table and report. Selection is always explicit.
export default function PluginLauncher({
  session,
  targets,
  onClose,
  onLaunched,
}: {
  session: string;
  targets: string[];
  onClose: () => void;
  onLaunched: () => void;
}) {
  const query = useAPI<Plugin[]>("/plugins");
  const targetQuery = useAPI<Target[]>(`/sessions/${session}/targets`);
  const [targetIDs, setTargetIDs] = useState(targets);
  const [mode, setMode] = useState("individual");
  const [profile, setProfile] = useState("");
  const profiles = useAPI<Profile[]>(mode === "groups" ? "/profiles" : "");
  const profileDetail = useAPI<Profile>(
    mode === "groups" && profile
      ? `/profiles/${encodeURIComponent(profile)}`
      : "",
  );
  const [selected, setSelected] = useState<string[]>([]);
  const [help, setHelp] = useState<Plugin | null>(null);
  const [search, setSearch] = useState("");
  const [group, setGroup] = useState("");
  const [type, setType] = useState("");
  const [groupTypes, setGroupTypes] = useState<string[]>([]);
  const [offset, setOffset] = useState(0);
  const [values, setValues] = useState<Record<string, Record<string, string>>>(
    {},
  );
  const plugins = query.data || [];
  const matches = plugins.filter(
    (p) =>
      (!group || p.group === group) &&
      (mode === "groups"
        ? !groupTypes.length || groupTypes.includes(p.type)
        : !type || p.type === type) &&
      `${p.id} ${p.title} ${p.description}`
        .toLowerCase()
        .includes(mode === "groups" ? "" : search.toLowerCase()),
  );
  const chosen =
    mode === "groups"
      ? group
        ? matches
        : []
      : plugins.filter((p) => selected.includes(p.id));
  const launch = useAction(async () => {
    const plugin_inputs: Record<string, Record<string, unknown>> = {};
    for (const plugin of chosen)
      for (const input of plugin.inputs || []) {
        const value = values[plugin.id]?.[input.name];
        if (value !== undefined && value !== "")
          (plugin_inputs[plugin.id] ??= {})[input.name] = inputValue(
            input,
            value,
          );
      }
    return request("/runs", "POST", {
      session_id: session,
      target_ids: targetIDs,
      ...(mode === "groups"
        ? {
            plugin_group: group,
            plugin_types: groupTypes,
            ...(profile ? { profile } : {}),
          }
        : { plugin_ids: selected }),
      plugin_inputs,
    });
  });
  const toggle = (id: string) =>
    setSelected((s) =>
      s.includes(id) ? s.filter((x) => x !== id) : [...s, id],
    );
  const ready = matches
    .slice(offset, offset + 10)
    .filter((p) => p.availability === "ready");
  const selectMatches = () =>
    setSelected((s) => [...new Set([...s, ...ready.map((p) => p.id)])]);
  return (
    <section className="plugin-launcher">
      <div className="section-head">
        <h1>Run plugins</h1>
        <Button variant="ghost" disabled={launch.isPending} onClick={onClose}>
          Back
        </Button>
      </div>
      <details className="picker-targets">
        <summary>
          {targetIDs.length} targets selected{" "}
          <span className="muted"> · Change</span>
        </summary>
        <ErrorMessage error={targetQuery.error} />
        {targetQuery.data?.map((target) => (
          <label className="actions" key={target.id}>
            <input
              type="checkbox"
              aria-label={"Target " + target.value}
              checked={targetIDs.includes(target.id)}
              disabled={launch.isPending}
              onChange={(event) =>
                setTargetIDs((current) =>
                  event.target.checked
                    ? [...current, target.id]
                    : current.filter((id) => id !== target.id),
                )
              }
            />
            {target.value || target.id}
          </label>
        ))}
      </details>
      <ErrorMessage error={query.error || launch.error} />
      {query.isPending ? (
        <Loading />
      ) : (
        <>
          <Tabs
            value={mode}
            onValueChange={(value) => {
              setMode(value);
              setOffset(0);
            }}
          >
            <TabsList>
              <TabsTrigger value="individual">Launch individually</TabsTrigger>
              <TabsTrigger value="groups">Launch in groups</TabsTrigger>
            </TabsList>
            <div className="filters">
              <label>
                Find a plugin
                <Input
                  disabled={mode === "groups" || launch.isPending}
                  value={search}
                  onChange={(e) => {
                    setSearch(e.target.value);
                    setOffset(0);
                  }}
                  placeholder="Name or OWTF code"
                />
              </label>
              <label>
                Group
                <select
                  value={group}
                  onChange={(e) => {
                    setGroup(e.target.value);
                    setOffset(0);
                  }}
                >
                  <option value="">All groups</option>
                  {[...new Set(plugins.map((p) => p.group))].sort().map((g) => (
                    <option key={g}>{g}</option>
                  ))}
                </select>
              </label>
              {mode === "individual" && (
                <label>
                  Plugin type
                  <select
                    value={type}
                    onChange={(e) => {
                      setType(e.target.value);
                      setOffset(0);
                    }}
                  >
                    <option value="">All types</option>
                    {[...new Set(plugins.map((p) => p.type))]
                      .sort()
                      .map((t) => (
                        <option key={t}>{t}</option>
                      ))}
                  </select>
                </label>
              )}
            </div>
            <TabsContent value="groups">
              <fieldset className="filters">
                <legend>Plugin types</legend>
                {[...new Set(plugins.map((p) => p.type))]
                  .sort()
                  .map((value) => (
                    <label className="actions" key={value}>
                      <input
                        type="checkbox"
                        checked={groupTypes.includes(value)}
                        onChange={(event) => {
                          setGroupTypes((current) =>
                            event.target.checked
                              ? [...current, value]
                              : current.filter((type) => type !== value),
                          );
                          setOffset(0);
                        }}
                      />
                      {value}
                    </label>
                  ))}
                <p className="muted">No types selected includes all types.</p>
              </fieldset>
              <p className="muted">
                The server launches the complete group/type selection.
                Unavailable or incompatible plugins are recorded as blocked.
                Profiles set order; they do not restrict selection.
              </p>
              <label>
                Profile
                <select
                  value={profile}
                  disabled={launch.isPending}
                  onChange={(e) => setProfile(e.target.value)}
                >
                  <option value="">Server default</option>
                  {profiles.data?.map((p) => (
                    <option key={p.name} value={p.name}>
                      {p.name}
                    </option>
                  ))}
                </select>
              </label>
              <ErrorMessage error={profiles.error || profileDetail.error} />
              {profileDetail.data && (
                <details>
                  <summary>Profile: {profileDetail.data.name}</summary>
                  <p>{profileDetail.data.description}</p>
                  <ol>
                    {profileDetail.data.plugins.map((id) => (
                      <li key={id}>
                        <code>{id}</code>
                      </li>
                    ))}
                  </ol>
                </details>
              )}
            </TabsContent>
            <TabsContent value="individual">
              <p className="muted">Select exactly the plugins to run.</p>
            </TabsContent>
          </Tabs>
          <div className="section-head picker-head">
            <span className="muted">
              {group || "All groups"} ·{" "}
              {matches.slice(offset, offset + 10).length} shown of{" "}
              {matches.length}
            </span>
            <Button
              variant="ghost"
              disabled={launch.isPending || mode === "groups" || !ready.length}
              onClick={selectMatches}
            >
              Select available shown
            </Button>
          </div>
          <div className="plugin-catalog">
            {matches.slice(offset, offset + 10).map((p) => (
              <div
                className="catalog-row"
                data-chosen={
                  mode === "groups" ? !!group : selected.includes(p.id)
                }
                key={p.id}
              >
                <label>
                  <input
                    type="checkbox"
                    aria-label={"Select " + p.id}
                    checked={
                      mode === "groups" ? !!group : selected.includes(p.id)
                    }
                    disabled={
                      mode === "groups" ||
                      p.availability !== "ready" ||
                      launch.isPending
                    }
                    onChange={() => toggle(p.id)}
                  />
                  <span>
                    <span className="catalog-title">
                      <strong>{p.title}</strong>
                      <StateBadge value={p.type} />
                    </span>
                    <code>{p.id}</code>
                    <span className="catalog-description">{p.description}</span>
                    {p.availability !== "ready" && (
                      <span className="catalog-unavailable">
                        {p.reason || "Unavailable"}
                      </span>
                    )}
                  </span>
                </label>
                <Button
                  variant="ghost"
                  size="sm"
                  aria-label={`Help for ${p.id}`}
                  onClick={() => setHelp(p)}
                >
                  Help
                </Button>
              </div>
            ))}
            {!matches.length && <p>No matching plugins.</p>}
          </div>
          <Pager
            offset={offset}
            total={matches.length}
            size={10}
            onChange={setOffset}
          />
          {chosen
            .filter((p) => p.inputs?.length)
            .map((p) => (
              <details key={p.id}>
                <summary>Inputs: {p.id}</summary>
                <div className="input-grid">
                  {p.inputs.map((input) => (
                    <label key={input.name}>
                      {input.name}
                      {input.required ? " *" : ""}
                      <span className="muted">{input.description}</span>
                      {input.type === "boolean" || input.choices?.length ? (
                        <select
                          value={
                            values[p.id]?.[input.name] ??
                            String(input.default ?? "")
                          }
                          onChange={(e) =>
                            setValues((v) => ({
                              ...v,
                              [p.id]: {
                                ...v[p.id],
                                [input.name]: e.target.value,
                              },
                            }))
                          }
                        >
                          <option value="">Use default</option>
                          {(input.choices?.length
                            ? input.choices
                            : ["true", "false"]
                          ).map((c) => (
                            <option key={c}>{c}</option>
                          ))}
                        </select>
                      ) : (
                        <Input
                          aria-label={`${p.id} ${input.name}`}
                          placeholder={String(input.default ?? "")}
                          value={values[p.id]?.[input.name] ?? ""}
                          onChange={(e) =>
                            setValues((v) => ({
                              ...v,
                              [p.id]: {
                                ...v[p.id],
                                [input.name]: e.target.value,
                              },
                            }))
                          }
                        />
                      )}
                    </label>
                  ))}
                </div>
              </details>
            ))}
          <div className="picker-summary">
            <div className="actions justify-between">
              <span role="status">
                {chosen.length} plugins selected
                {mode === "individual" ? " across all filters" : " in group"}
              </span>
              <Button
                variant="outline"
                disabled={launch.isPending || mode === "groups"}
                onClick={() => setSelected([])}
              >
                Clear selection
              </Button>
            </div>
            {chosen.length > 0 && (
              <details>
                <summary>
                  Review selected plugins (including hidden selections)
                </summary>
                {chosen.map((p) => (
                  <p key={p.id}>
                    <code>{p.id}</code> · {p.title}
                  </p>
                ))}
              </details>
            )}
            <div className="actions justify-between">
              <span className="muted">No automatic retries.</span>
              <Button
                disabled={
                  !chosen.length ||
                  !targetIDs.length ||
                  launch.isPending ||
                  (mode === "groups" &&
                    (!!profiles.error || (!!profile && !profileDetail.data)))
                }
                onClick={() =>
                  launch.mutate(undefined, { onSuccess: onLaunched })
                }
              >
                {launch.isPending ? "Submitting…" : "Run"}
              </Button>
            </div>
          </div>
          {launch.isError && (
            <p className="muted">
              If the response was lost, check Worklist before submitting again.
              This action is not retried automatically.
            </p>
          )}
        </>
      )}
      {help && (
        <Inspector title={help.title} onClose={() => setHelp(null)}>
          <p>
            <code>{help.id}</code>
          </p>
          <p>{help.description}</p>
          <p className="muted">
            {help.group} · {help.type} · {help.runtime_type}
          </p>
          <h3>Availability</h3>
          <p>
            {help.availability}
            {help.reason ? `: ${help.reason}` : ""}
          </p>
          <h3>Inputs</h3>
          {(help.inputs || []).map((input) => (
            <section key={input.name}>
              <h4>
                {input.name} {input.required ? "(required)" : ""}
              </h4>
              <p>{input.description}</p>
              <p className="muted">
                Type: {input.type}
                {input.default !== undefined
                  ? ` · Default: ${String(input.default)}`
                  : ""}
              </p>
              {input.choices?.length ? (
                <p>Choices: {input.choices.join(", ")}</p>
              ) : null}
            </section>
          ))}
          {!help.inputs?.length && <p>No configurable inputs.</p>}
        </Inspector>
      )}
    </section>
  );
}
