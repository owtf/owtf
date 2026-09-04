# Operator UI

React and TypeScript, TanStack Query for API state, and selected shadcn/Radix
controls. No Redux, Bootstrap runtime, separate production frontend service,
or automatic mutation retries.

## Development

Use Node 22 or newer. Start the Go service with Docker Compose, then:

```sh
cd web
npm ci
npm run dev
```

Vite proxies `/api` to `http://127.0.0.1:8009`. Set `OWTF_DEV_API` to use a
different local service. Never put service credentials in frontend variables.

```sh
npm run check
npm test
npm run build
```

The build replaces `internal/api/ui`. Commit that generated bundle with source
changes so ordinary Go builds do not require Node. Docker rebuilds it from source.
CI also builds and tests the UI. Do not edit the generated bundle by hand.

## Structure

- `pages/`: Targets, target report, Worklist/Workers, Transactions.
- `components/PluginLauncher.tsx`: shared explicit plugin selection and inputs.
- `components/TaskDetail.tsx`: ordered logs and persisted output reviews.
- `components/ui/`: copied shadcn components; license in `SHADCN-LICENSE.md`.
- `lib/api.ts`: requests, invalidation, and polling. Mutations are never retried.
- `lib/types.ts`: API wire records, retaining Go JSON field names.

Keep selection/form state local. Keep session context in the URL. Render scanner
output as text; open artifacts through the backend's isolated artifact endpoint.
An execution's success is not its security severity. Accordion severity reflects
the highest saved rank among its retained executions, not a new finding.

See `docs/architecture/operator-ui.md` for the historical references, behavior
contract, and deliberately unsupported controls.
