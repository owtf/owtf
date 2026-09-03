const state = {
  session: null,
  targets: [],
  plugins: [],
  tasks: [],
  workers: [],
  transactions: [],
  report: null,
  events: [],
  selectedTask: null,
  selectedPlugins: []
};

const app = document.querySelector("#app");
const toastElement = document.querySelector("#toast");

function escapeHTML(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

async function api(path, options = {}) {
  const response = await fetch(path, {
    ...options,
    headers: { "Content-Type": "application/json", ...(options.headers || {}) }
  });
  if (response.status === 204) return null;
  const body = await response.json().catch(() => ({}));
  if (!response.ok)
    throw new Error(body.error || `${response.status} ${response.statusText}`);
  return body;
}

function toast(message) {
  toastElement.textContent = message;
  toastElement.classList.add("show");
  window.setTimeout(() => toastElement.classList.remove("show"), 3200);
}

function badge(status) {
  return `<span class="badge ${escapeHTML(status)}">${escapeHTML(
    status
  )}</span>`;
}

function activateNav(name) {
  document
    .querySelectorAll("[data-nav]")
    .forEach(link =>
      link.classList.toggle("active", link.dataset.nav === name)
    );
}

function formatTime(value) {
  return value
    ? new Date(value).toLocaleTimeString([], {
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit"
      })
    : "—";
}

async function ensureSession() {
  const sessions = await api("/api/v2/sessions");
  state.session =
    sessions[0] ||
    (await api("/api/v2/sessions", {
      method: "POST",
      body: JSON.stringify({ name: "Local session" })
    }));
}

async function refresh() {
  const [targets, plugins, tasks, workers] = await Promise.all([
    api(`/api/v2/sessions/${state.session.id}/targets`),
    api("/api/v2/plugins"),
    api(`/api/v2/tasks?session_id=${state.session.id}`),
    api("/api/v2/workers")
  ]);
  state.targets = targets;
  state.plugins = plugins;
  state.tasks = tasks;
  state.workers = workers;
  const readyIDs = plugins
    .filter(plugin => plugin.availability === "ready")
    .map(plugin => plugin.id);
  state.selectedPlugins = state.selectedPlugins.filter(id =>
    readyIDs.includes(id)
  );
  if (!state.selectedPlugins.length && readyIDs.length) {
    state.selectedPlugins = [readyIDs[0]];
  }
}

async function refreshTasks() {
  state.tasks = await api(`/api/v2/tasks?session_id=${state.session.id}`);
}

async function refreshWorkers() {
  state.workers = await api("/api/v2/workers");
}

function taskForTarget(targetID) {
  return state.tasks.find(task => task.target_id === targetID);
}

function renderTargets() {
  activateNav("targets");
  const running = state.tasks.filter(
    task => task.status === "running" || task.status === "queued"
  ).length;
  const completed = state.tasks.filter(task => task.status === "succeeded")
    .length;
  const selectedPlugins = state.plugins.filter(item =>
    state.selectedPlugins.includes(item.id)
  );
  const pluginOptions = state.plugins
    .map(item => {
      const unavailable = item.availability !== "ready";
      const checked = state.selectedPlugins.includes(item.id);
      return `<label class="plugin-option ${unavailable ? "unavailable" : ""}">
      <input type="checkbox" data-plugin="${escapeHTML(item.id)}" ${
        checked ? "checked" : ""
      } ${unavailable ? "disabled" : ""} />
      <span><strong>${escapeHTML(
        item.title
      )}</strong><span class="mono muted">${escapeHTML(item.id)}</span>${
        unavailable
          ? `<span class="requirement">${escapeHTML(
              item.reason || item.availability
            )}</span>`
          : ""
      }</span>
      <span class="badge">${escapeHTML(item.group)} / ${escapeHTML(item.type)}</span>
    </label>`;
    })
    .join("");
  const rows = state.targets
    .map(target => {
      const task = taskForTarget(target.id);
      return `
      <tr>
        <td><a class="target-link" href="/targets/${escapeHTML(
          target.id
        )}">${escapeHTML(target.value)}</a><div class="mono muted">${escapeHTML(
        target.kind
      )}</div></td>
        <td>${
          task ? badge(task.status) : '<span class="muted">Not scanned</span>'
        }</td>
        <td class="mono muted">${escapeHTML(target.id.slice(0, 14))}</td>
        <td><div class="actions"><button class="button small" data-run="${escapeHTML(
          target.id
        )}" ${
        selectedPlugins.length ? "" : "disabled"
      }>Run</button><a class="button small" href="/targets/${escapeHTML(
        target.id
      )}">Report</a><button class="button small danger" data-delete="${escapeHTML(
        target.id
      )}">Delete</button></div></td>
      </tr>`;
    })
    .join("");

  app.innerHTML = `
    <section class="page-head">
      <div><p class="eyebrow">${escapeHTML(
        state.session.name
      )}</p><h1>Targets</h1><p class="subtitle">Define scope, launch techniques, and retain the evidence chain.</p></div>
      <button class="button primary" id="focus-target">Add target</button>
    </section>
    <div class="layout">
      <div class="stack">
        <section class="panel">
          <div class="metrics">
            <div class="metric"><strong>${
              state.targets.length
            }</strong><span>Targets in scope</span></div>
            <div class="metric"><strong>${running}</strong><span>Active tasks</span></div>
            <div class="metric"><strong>${completed}</strong><span>Completed tasks</span></div>
          </div>
          <div class="panel-head"><div><h2>Target inventory</h2><span class="panel-caption">Canonical, deduplicated scope</span></div></div>
          <div class="table-wrap">
            ${
              rows
                ? `<table><thead><tr><th>Target</th><th>Status</th><th>ID</th><th></th></tr></thead><tbody>${rows}</tbody></table>`
                : '<div class="empty">No targets yet. Add an approved URL to begin.</div>'
            }
          </div>
        </section>
      </div>
      <aside class="stack">
        <section class="panel">
          <div class="panel-head"><div><h2>Add targets</h2><span class="panel-caption">One URL, host, IP, or CIDR per line</span></div></div>
          <form class="panel-body target-form" id="target-form">
            <textarea id="targets" aria-label="Targets" placeholder="https://app.example.com"></textarea>
            <button class="button primary" type="submit">Add</button>
          </form>
        </section>
        <section class="panel" id="work">
          <div class="panel-head"><div><h2>Techniques</h2><span class="panel-caption">${
            selectedPlugins.length
          } selected for Run</span></div></div>
          <div class="panel-body plugin-card">
            ${pluginOptions || "<p>No plugins were discovered.</p>"}
          </div>
        </section>
        <section class="panel">
          <div class="panel-head"><div><h2>Recent work</h2><span class="panel-caption">Durable task state</span></div></div>
          <div class="panel-body activity">
            ${state.tasks
              .slice(0, 5)
              .map(
                task =>
                  `<div class="activity-row"><div class="activity-row-top"><span class="mono">${escapeHTML(
                    task.plugin_id
                  )}</span>${badge(
                    task.status
                  )}</div><span class="mono muted">${escapeHTML(
                    task.target_id.slice(0, 14)
                  )}</span></div>`
              )
              .join("") || '<span class="muted">No work submitted.</span>'}
          </div>
        </section>
      </aside>
    </div>`;

  document.querySelector("#target-form").addEventListener("submit", addTargets);
  document
    .querySelector("#focus-target")
    .addEventListener("click", () =>
      document.querySelector("#targets").focus()
    );
  document.querySelectorAll("[data-plugin]").forEach(input =>
    input.addEventListener("change", event => {
      const pluginID = event.target.dataset.plugin;
      state.selectedPlugins = event.target.checked
        ? [...state.selectedPlugins, pluginID]
        : state.selectedPlugins.filter(id => id !== pluginID);
      renderTargets();
    })
  );
  document
    .querySelectorAll("[data-run]")
    .forEach(button =>
      button.addEventListener("click", () => runTarget(button.dataset.run))
    );
  document
    .querySelectorAll("[data-delete]")
    .forEach(button =>
      button.addEventListener("click", () =>
        deleteTarget(button.dataset.delete)
      )
    );
}

function renderWorklist() {
  activateNav("work");
  const active = state.tasks.filter(
    task => task.status === "queued" || task.status === "running"
  ).length;
  const failed = state.tasks.filter(task => task.status === "failed").length;
  const completed = state.tasks.filter(task => task.status === "succeeded")
    .length;
  const rows = state.tasks
    .map(task => {
      const target = state.targets.find(item => item.id === task.target_id);
      const canCancel = task.status === "queued" || task.status === "running";
      return `<tr>
      <td><strong>${escapeHTML(
        task.plugin_id
      )}</strong><div class="mono muted">${escapeHTML(task.id)}</div></td>
      <td><a class="target-link" href="/targets/${escapeHTML(
        task.target_id
      )}">${escapeHTML(target?.value || task.target_id)}</a></td>
      <td>${badge(task.status)}</td>
      <td class="mono muted">${formatTime(
        task.started_at || task.created_at
      )}</td>
      <td><div class="actions"><button class="button small" data-events="${escapeHTML(
        task.id
      )}">Logs</button>${
        canCancel
          ? `<button class="button small danger" data-cancel="${escapeHTML(
              task.id
            )}">Cancel</button>`
          : ""
      }</div></td>
    </tr>`;
    })
    .join("");
  app.innerHTML = `
    <section class="page-head"><div><p class="eyebrow">${escapeHTML(
      state.session.name
    )}</p><h1>Worklist</h1><p class="subtitle">Persisted execution state, ordered newest first.</p></div></section>
    <section class="report-grid">
      <div class="report-stat"><strong>${active}</strong><span class="muted">Queued or running</span></div>
      <div class="report-stat"><strong>${completed}</strong><span class="muted">Succeeded</span></div>
      <div class="report-stat"><strong>${failed}</strong><span class="muted">Failed</span></div>
    </section>
    <div class="report-columns">
      <section class="panel">
        <div class="panel-head"><div><h2>Tasks</h2><span class="panel-caption">Database-backed run history</span></div></div>
        <div class="table-wrap">${
          rows
            ? `<table><thead><tr><th>Plugin</th><th>Target</th><th>Status</th><th>Started</th><th></th></tr></thead><tbody>${rows}</tbody></table>`
            : '<div class="empty">No tasks have been submitted.</div>'
        }</div>
      </section>
      <aside class="panel">
        <div class="panel-head"><div><h2>Task log</h2><span class="panel-caption">${
          state.selectedTask ? escapeHTML(state.selectedTask) : "Select a task"
        }</span></div></div>
        <div class="panel-body">${state.events
          .map(
            event =>
              `<div class="event"><span class="event-stream">${escapeHTML(
                event.stream
              )}</span><span class="mono">${escapeHTML(
                event.message
              )}</span></div>`
          )
          .join("") ||
          '<span class="muted">Select Logs to inspect execution output.</span>'}</div>
      </aside>
    </div>`;
  document
    .querySelectorAll("[data-events]")
    .forEach(button =>
      button.addEventListener("click", () => loadEvents(button.dataset.events))
    );
  document
    .querySelectorAll("[data-cancel]")
    .forEach(button =>
      button.addEventListener("click", () => cancelTask(button.dataset.cancel))
    );
}

function renderWorkers() {
  activateNav("workers");
  const running = state.workers.filter(
    worker => worker.status === "running" || worker.status === "starting"
  ).length;
  const rows = state.workers
    .map(
      worker => `<tr>
    <td><strong>${escapeHTML(worker.id)}</strong></td>
    <td>${badge(worker.status)}</td>
    <td>${
      worker.plugin_id
        ? `<span>${escapeHTML(
            worker.plugin_id
          )}</span><div class="mono muted">${escapeHTML(worker.task_id)}</div>`
        : '<span class="muted">No assigned task</span>'
    }</td>
    <td class="mono">${worker.completed}</td><td class="mono">${
        worker.failed
      }</td><td class="mono">${worker.cancelled}</td>
  </tr>`
    )
    .join("");
  app.innerHTML = `
    <section class="page-head"><div><p class="eyebrow">Local runner</p><h1>Workers</h1><p class="subtitle">The configured worker pool, not inferred progress.</p></div></section>
    <section class="report-grid">
      <div class="report-stat"><strong>${
        state.workers.length
      }</strong><span class="muted">Configured workers</span></div>
      <div class="report-stat"><strong>${running}</strong><span class="muted">Currently active</span></div>
      <div class="report-stat"><strong>${state.workers.length -
        running}</strong><span class="muted">Idle or stopped</span></div>
    </section>
    <section class="panel">
      <div class="panel-head"><div><h2>Worker pool</h2><span class="panel-caption">Counters apply to this server process</span></div></div>
      <div class="table-wrap"><table><thead><tr><th>Worker</th><th>Status</th><th>Current task</th><th>Completed</th><th>Failed</th><th>Cancelled</th></tr></thead><tbody>${rows}</tbody></table></div>
    </section>`;
}

function renderTransactions() {
  activateNav("transactions");
  const errors = state.transactions.filter(
    transaction => transaction.status_code >= 400
  ).length;
  const targetCount = new Set(
    state.transactions.map(transaction => transaction.target_id)
  ).size;
  const rows = state.transactions
    .map(
      transaction => `<tr>
    <td><span class="status-code">${escapeHTML(
      transaction.status_code
    )}</span></td>
    <td><strong>${escapeHTML(transaction.method)}</strong></td>
    <td><span class="transaction-url">${escapeHTML(
      transaction.url
    )}</span><div class="mono muted">${escapeHTML(
        transaction.duration_ms
      )} ms</div></td>
    <td><a class="target-link mono" href="/targets/${escapeHTML(
      transaction.target_id
    )}">${escapeHTML(transaction.target_id.slice(0, 14))}</a></td>
    <td>${
      transaction.response_body_artifact_id
        ? `<a class="button small" href="/api/v2/artifacts/${escapeHTML(
            transaction.response_body_artifact_id
          )}" target="_blank">Body</a>`
        : '<span class="muted">—</span>'
    }</td>
  </tr>`
    )
    .join("");
  app.innerHTML = `
    <section class="page-head"><div><p class="eyebrow">${escapeHTML(
      state.session.name
    )}</p><h1>Transactions</h1><p class="subtitle">HTTP transactions captured by executed techniques or imported from HAR.</p></div></section>
    <section class="report-grid">
      <div class="report-stat"><strong>${
        state.transactions.length
      }</strong><span class="muted">Transactions</span></div>
      <div class="report-stat"><strong>${targetCount}</strong><span class="muted">Targets represented</span></div>
      <div class="report-stat"><strong>${errors}</strong><span class="muted">HTTP errors</span></div>
    </section>
    <section class="panel">
      <div class="panel-head"><div><h2>Request history</h2><span class="panel-caption">Newest first</span></div></div>
      <div class="table-wrap">${
        rows
          ? `<table><thead><tr><th>Status</th><th>Method</th><th>URL</th><th>Target</th><th>Evidence</th></tr></thead><tbody>${rows}</tbody></table>`
          : '<div class="empty">No HTTP transactions captured.</div>'
      }</div>
    </section>`;
}

async function loadEvents(taskID) {
  try {
    state.selectedTask = taskID;
    state.events = await api(`/api/v2/tasks/${taskID}/events`);
    renderWorklist();
  } catch (error) {
    toast(error.message);
  }
}

async function cancelTask(taskID) {
  try {
    await api(`/api/v2/tasks/${taskID}/cancel`, { method: "POST", body: "{}" });
    state.events = await api(`/api/v2/tasks/${taskID}/events`);
    state.selectedTask = taskID;
    await refreshTasks();
    renderWorklist();
    toast("Task cancelled");
  } catch (error) {
    toast(error.message);
  }
}

async function pollWorklist() {
  if (document.hidden) return;
  try {
    await refreshTasks();
    if (state.selectedTask)
      state.events = await api(`/api/v2/tasks/${state.selectedTask}/events`);
    renderWorklist();
  } catch (error) {
    console.error(error);
  }
}

async function pollWorkers() {
  if (document.hidden) return;
  try {
    await refreshWorkers();
    renderWorkers();
  } catch (error) {
    console.error(error);
  }
}

async function addTargets(event) {
  event.preventDefault();
  const field = document.querySelector("#targets");
  const targets = field.value
    .split("\n")
    .map(value => value.trim())
    .filter(Boolean);
  if (!targets.length) return;
  try {
    const result = await api(`/api/v2/sessions/${state.session.id}/targets`, {
      method: "POST",
      body: JSON.stringify({ targets })
    });
    field.value = "";
    const notes = [`${result.created.length} added`];
    if (result.duplicates.length)
      notes.push(`${result.duplicates.length} duplicate`);
    if (result.invalid.length) notes.push(`${result.invalid.length} invalid`);
    toast(notes.join(", "));
    await refresh();
    renderTargets();
  } catch (error) {
    toast(error.message);
  }
}

async function runTarget(targetID) {
  const pluginIDs = state.plugins
    .filter(
      item =>
        state.selectedPlugins.includes(item.id) && item.availability === "ready"
    )
    .map(item => item.id);
  if (!pluginIDs.length) return;
  try {
    await api("/api/v2/runs", {
      method: "POST",
      body: JSON.stringify({
        session_id: state.session.id,
        target_ids: [targetID],
        plugin_ids: pluginIDs
      })
    });
    toast(
      `${pluginIDs.length} task${pluginIDs.length === 1 ? "" : "s"} queued`
    );
    await refresh();
    renderTargets();
  } catch (error) {
    toast(error.message);
  }
}

async function deleteTarget(targetID) {
  if (!window.confirm("Delete this target and all of its task evidence?"))
    return;
  try {
    await api(`/api/v2/targets/${targetID}`, { method: "DELETE" });
    toast("Target deleted");
    await refresh();
    renderTargets();
  } catch (error) {
    toast(error.message);
  }
}

function renderReport() {
  activateNav("targets");
  const report = state.report;
  const latestTask = report.tasks[0];
  app.innerHTML = `
    <section class="page-head">
      <div><p class="eyebrow">Target report</p><h1>${escapeHTML(
        report.target.value
      )}</h1><p class="subtitle mono">${escapeHTML(report.target.id)}</p></div>
      <div class="actions"><a class="button" href="/">Back to targets</a>${
        latestTask ? badge(latestTask.status) : ""
      }</div>
    </section>
    <section class="report-grid">
      <div class="report-stat"><strong>${
        report.transactions.length
      }</strong><span class="muted">HTTP transactions</span></div>
      <div class="report-stat"><strong>${
        report.observations.length
      }</strong><span class="muted">Observations</span></div>
      <div class="report-stat"><strong>${
        report.artifacts.length
      }</strong><span class="muted">Evidence artifacts</span></div>
    </section>
    <div class="report-columns">
      <div class="stack">
        <section class="panel">
          <div class="panel-head"><div><h2>Transactions</h2><span class="panel-caption">Captured by plugins or imported from HAR</span></div></div>
          <div class="panel-body">
            ${report.transactions
              .map(
                transaction =>
                  `<div class="transaction"><span class="status-code">${escapeHTML(
                    transaction.status_code
                  )}</span><span><strong>${escapeHTML(
                    transaction.method
                  )}</strong> ${escapeHTML(
                    transaction.url
                  )}<br><span class="mono muted">${escapeHTML(
                    transaction.duration_ms
                  )} ms</span></span>${
                    transaction.response_body_artifact_id
                      ? `<a class="button small" href="/api/v2/artifacts/${escapeHTML(
                          transaction.response_body_artifact_id
                        )}" target="_blank">Body</a>`
                      : ""
                  }</div>`
              )
              .join("") || '<div class="empty">No transactions captured.</div>'}
          </div>
        </section>
        <section class="panel" id="evidence">
          <div class="panel-head"><div><h2>Evidence</h2><span class="panel-caption">Content-addressed artifacts and observations</span></div></div>
          <div class="panel-body">
            ${report.artifacts
              .map(
                artifact =>
                  `<div class="artifact"><span><a href="/api/v2/artifacts/${escapeHTML(
                    artifact.id
                  )}" target="_blank">${escapeHTML(
                    artifact.name
                  )}</a><br><span class="mono muted">sha256:${escapeHTML(
                    artifact.sha256.slice(0, 16)
                  )} · ${escapeHTML(
                    artifact.size
                  )} bytes</span></span><span class="mono muted">${escapeHTML(
                    artifact.media_type
                  )}</span></div>`
              )
              .join("") || '<div class="empty">No artifacts retained.</div>'}
            ${report.observations
              .map(
                observation =>
                  `<div class="artifact"><span><strong>${escapeHTML(
                    observation.technique_code
                  )}</strong><br><span class="json">${escapeHTML(
                    observation.data
                  )}</span></span><span class="badge">${escapeHTML(
                    observation.kind
                  )}</span></div>`
              )
              .join("")}
          </div>
        </section>
      </div>
      <aside class="stack">
        <section class="panel" id="work">
          <div class="panel-head"><div><h2>Task history</h2><span class="panel-caption">Persisted execution attempts</span></div></div>
          <div class="panel-body activity">
            ${report.tasks
              .map(
                task =>
                  `<div class="activity-row"><div class="activity-row-top"><strong>${escapeHTML(
                    task.plugin_id
                  )}</strong>${badge(
                    task.status
                  )}</div><span class="mono muted">${escapeHTML(
                    task.id
                  )}</span>${
                    task.error
                      ? `<p class="json">${escapeHTML(task.error)}</p>`
                      : ""
                  }</div>`
              )
              .join("") ||
              '<span class="muted">This target has not been scanned.</span>'}
          </div>
        </section>
        <section class="panel">
          <div class="panel-head"><div><h2>Execution log</h2><span class="panel-caption">Plugin stdout, stderr, and lifecycle</span></div></div>
          <div class="panel-body">
            ${report.events
              .map(
                event =>
                  `<div class="event"><span class="event-stream">${escapeHTML(
                    event.stream
                  )}</span><span class="mono">${escapeHTML(
                    event.message
                  )}</span></div>`
              )
              .join("") || '<span class="muted">No events recorded.</span>'}
          </div>
        </section>
      </aside>
    </div>`;
}

async function init() {
  try {
    await ensureSession();
    await refresh();
    const path = window.location.pathname;
    const match = path.match(/^\/targets\/([^/]+)$/);
    if (match) {
      state.report = await api(
        `/api/v2/targets/${encodeURIComponent(match[1])}/report`
      );
      renderReport();
    } else if (path === "/work") {
      renderWorklist();
      window.setInterval(pollWorklist, 1500);
    } else if (path === "/workers") {
      renderWorkers();
      window.setInterval(pollWorkers, 2000);
    } else if (path === "/transactions") {
      state.transactions = await api(
        `/api/v2/transactions?session_id=${state.session.id}`
      );
      renderTransactions();
    } else {
      renderTargets();
      window.setInterval(async () => {
        if (
          !state.tasks.some(
            task => task.status === "queued" || task.status === "running"
          )
        )
          return;
        if (document.hidden) return;
        await refreshTasks();
        renderTargets();
      }, 1000);
    }
  } catch (error) {
    app.innerHTML = `<div class="panel empty"><strong>OWTF could not load.</strong><p>${escapeHTML(
      error.message
    )}</p></div>`;
  }
}

init();
