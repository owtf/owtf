import { useState } from "react";
import { useAPI, useAction, request } from "../lib/api";
import type { Plugin, PluginInput } from "../lib/types";
import {
  Button,
  ErrorMessage,
  Loading,
  Modal,
  Pager,
  StateBadge,
} from "./shared";
import { Input } from "./ui/input";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "./ui/tabs";

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
  const [selected, setSelected] = useState<string[]>([]);
  const [search, setSearch] = useState("");
  const [group, setGroup] = useState("");
  const [type, setType] = useState("");
  const [offset, setOffset] = useState(0);
  const [values, setValues] = useState<Record<string, Record<string, string>>>(
    {},
  );
  const plugins = query.data || [];
  const matches = plugins.filter(
    (p) =>
      (!group || p.group === group) &&
      (!type || p.type === type) &&
      `${p.id} ${p.title} ${p.description}`
        .toLowerCase()
        .includes(search.toLowerCase()),
  );
  const chosen = plugins.filter((p) => selected.includes(p.id));
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
      target_ids: targets,
      plugin_ids: selected,
      plugin_inputs,
    });
  });
  const toggle = (id: string) =>
    setSelected((s) =>
      s.includes(id) ? s.filter((x) => x !== id) : [...s, id],
    );
  const ready = matches.filter((p) => p.availability === "ready");
  const selectMatches = () =>
    setSelected((s) => [...new Set([...s, ...ready.map((p) => p.id)])]);
  return (
    <Modal
      open
      title="Run plugins"
      description={`${targets.length} selected target(s). New runs preserve previous evidence.`}
      onClose={() => {
        if (!launch.isPending) onClose();
      }}
    >
      <ErrorMessage error={query.error || launch.error} />
      {query.isPending ? (
        <Loading />
      ) : (
        <>
          <Tabs defaultValue="individual">
            <TabsList>
              <TabsTrigger value="individual">Launch individually</TabsTrigger>
              <TabsTrigger value="groups">Launch in groups</TabsTrigger>
            </TabsList>
            <div className="filters">
              <label>
                Search plugins
                <Input
                  value={search}
                  onChange={(e) => {
                    setSearch(e.target.value);
                    setOffset(0);
                  }}
                  placeholder="Code, name or help"
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
              <label>
                Type
                <select
                  value={type}
                  onChange={(e) => {
                    setType(e.target.value);
                    setOffset(0);
                  }}
                >
                  <option value="">All types</option>
                  {[...new Set(plugins.map((p) => p.type))].sort().map((t) => (
                    <option key={t}>{t}</option>
                  ))}
                </select>
              </label>
            </div>
            <TabsContent value="groups">
              <p className="muted">
                Choose group and type above. Only available matching plugins are
                selected; unavailable plugins remain visible below.
              </p>
              <Button
                variant="outline"
                disabled={!group || launch.isPending}
                onClick={selectMatches}
              >
                Select available in group
              </Button>
            </TabsContent>
            <TabsContent value="individual">
              <p className="muted">Select exactly the plugins to run.</p>
            </TabsContent>
          </Tabs>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>
                    <input
                      type="checkbox"
                      aria-label="Select available matching plugins"
                      checked={
                        ready.length > 0 &&
                        ready.every((p) => selected.includes(p.id))
                      }
                      onChange={(e) =>
                        e.target.checked
                          ? selectMatches()
                          : setSelected((s) =>
                              s.filter((id) => !ready.some((p) => p.id === id)),
                            )
                      }
                      disabled={launch.isPending}
                    />
                  </th>
                  <th>Code / Name</th>
                  <th>Type</th>
                  <th>Group</th>
                  <th>Help / Availability</th>
                </tr>
              </thead>
              <tbody>
                {matches.slice(offset, offset + 10).map((p) => (
                  <tr key={p.id}>
                    <td>
                      <input
                        type="checkbox"
                        aria-label={`Select ${p.id}`}
                        checked={selected.includes(p.id)}
                        disabled={
                          p.availability !== "ready" || launch.isPending
                        }
                        onChange={() => toggle(p.id)}
                      />
                    </td>
                    <td>
                      <code>{p.id}</code>
                      <div>{p.title}</div>
                    </td>
                    <td>{p.type.replaceAll("_", " ")}</td>
                    <td>{p.group}</td>
                    <td className="help-cell">
                      {p.description}
                      {p.availability !== "ready" && (
                        <div>
                          <StateBadge value="blocked" />
                          <p>{p.reason}</p>
                        </div>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {!matches.length && <p className="empty">No matching plugins.</p>}
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
          <div className="actions justify-between">
            <span role="status">
              {selected.length} plugins selected across all filters
            </span>
            <Button
              variant="outline"
              disabled={launch.isPending}
              onClick={() => setSelected([])}
            >
              Clear selection
            </Button>
            <Button
              disabled={!selected.length || launch.isPending}
              onClick={() =>
                launch.mutate(undefined, { onSuccess: onLaunched })
              }
            >
              {launch.isPending
                ? "Submitting…"
                : `Run ${selected.length} plugin(s)`}
            </Button>
          </div>
          {launch.isError && (
            <p className="muted">
              If the response was lost, check Worklist before submitting again.
              This action is not retried automatically.
            </p>
          )}
        </>
      )}
    </Modal>
  );
}
