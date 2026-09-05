# Operator UI

React and TypeScript, TanStack Query for API state, and selected shadcn/Radix
controls. No Redux, Bootstrap runtime, or automatic mutation retries.

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

The build writes ignored output to `web/dist`. The frontend Docker image serves
it with Nginx and forwards API requests to the separate backend. Neither Node
nor UI assets are needed to build the Go binary. CI builds and tests both images;
do not commit generated bundles.

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
