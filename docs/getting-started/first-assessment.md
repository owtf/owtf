# Run your first assessment

This walkthrough covers the normal OWTF flow: create a session, add an authorized target, select plugins, watch the worklist, and review evidence.

!!! danger "Confirm scope first"

    Do not add a target until you have explicit permission to test it. Confirm the exact hosts, paths, test window, and allowed techniques with the system owner.

## 1. Start the stack

From the repository root:

```bash
make compose-safe
```

Open `http://localhost:8019` after the services are ready.

## 2. Create or select a session

A session keeps the targets and work for an engagement together. Use a clear name that identifies the authorized scope without putting secrets in the title.

## 3. Add targets

Open the target manager and add one URL per line. Include the scheme so OWTF knows whether the target uses HTTP or HTTPS:

```text
https://app.example.test
https://api.example.test
```

Start with a single non-production target while validating your environment.

## 4. Choose plugin intensity

OWTF groups web plugins by how they interact with the target:

- **Passive** plugins analyze existing data without sending new requests to the target.
- **Semi-passive** plugins make ordinary application requests.
- **Active** plugins probe for vulnerabilities and can be disruptive.

Begin with passive work. Add semi-passive or active plugins only when the rules of engagement allow them.

## 5. Watch workers and the worklist

Launching a plugin adds a plugin-target pair to the worklist. Workers claim queued work and execute it. You can pause queued work, pause workers, or abort work that should no longer run.

[Understand workers and the worklist →](../guides/workers-and-worklist.md)

## 6. Review results

Open the target report to inspect plugin output. Record analyst context with rankings and notes; tool output alone is not a confirmed vulnerability.

[Review and report results →](../guides/results-and-reporting.md)

## Next steps

- [Organize targets and sessions](../guides/targets-and-sessions.md)
- [Understand plugin categories](../guides/plugins.md)
- [Configure the intercepting proxy](../proxy/index.md)
