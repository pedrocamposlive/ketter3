# Ketter 3.0 Operator UI

## Overview
The frontend is a Vite-powered React experience that exposes the operational panels described in `docs/ui-blueprint.md`. Its goal is to make the Automation Node visible to operators while retaining the security posture dictated by the strategy documents: monochrome aesthetic, responsive panels, and zero surprises.

## Getting Started
1. Install dependencies (Node.js 20+ required):
   ```bash
   cd frontend
   npm install
   ```
2. Provide the API gateway if it is not collocated with the UI:
   ```bash
   export VITE_API_URL="http://localhost:8000"
   export VITE_USE_MOCKS="false"
   ```
3. Start the local shell experience:
   ```bash
   npm run dev
   ```
4. When ready, produce a production bundle:
   ```bash
   npm run build
   ```

Built files land in `frontend/dist` and can be served by any static host.

## Directory Layout
- `src/main.jsx` boots `App.jsx` inside the themed React tree defined in `theme/theme.css`.
- `src/layout/Layout.jsx` wires the header, navbar, sidebar, and footer around all pages so the five canonical sections share a cohesive chrome.
- `src/pages/*` holds Dashboard, Transfers, Audit, System Health, and Settings views that correspond to the blueprint scope.
- `src/components/*` contains shared UI pieces (status indicators, job cards, alerts, file picker, transfer progress/history, logs viewer, navbar/sidebar/footer).
- `src/services` exposes HTTP helpers (`api.js`, `pollingService.js`) plus wrappers (`wrappers/securityWrapper.js`) that inject required headers and audit logging.
- `src/hooks` contains reusable hooks (`useSystemStatus`, `useTransferRefresh`) that keep the dashboard synchronized with backend polling.

## Key Pages
- **Dashboard:** Aggregates operational signals with status cards, `StatusIndicator`, and live alerts.
- **Transfers:** Hosts `FilePicker` (watch mode, settle time, copy vs move), `TransferProgress`, and `TransferHistory` along with queue snapshots and quick events.
- **Audit:** Displays immutable log feeds and real-time sync state via `LogsViewer`.
- **System Health:** Shows health metrics/latency grids driven by `services/api.js#getHealthMetrics`.
- **Settings:** Manages volumes, profiles, and global controls with data from `getVolumes()` and `getAvailableVolumes()`.

Each page lives inside the shared layout so navigation via `Navbar` and `Sidebar` scroll anchors works consistently.

## Components & Helpers
- `FilePicker` validates paths, watch mode, settle time, and operation mode before constructing the API payload with triple SHA-256 compliance metadata.
- `TransferProgress` and `TransferHistory` lean on `services/api.js` to fetch active and historical jobs, surface folder/watch badges, and provide checksum modals.
- `JobCard`, `Alerts`, `LogsViewer`, `StatusIndicator`, `Navbar`, `Sidebar`, and `Footer` keep the UI modular and reusable.
- `services/pollingService` centralizes recovery intervals and logging so each page can re-use retry/backoff logic without duplication.

## Services & Wrappers
- `services/api.js` normalizes paths, exposes mocks via `VITE_USE_MOCKS`, and routes every request through `wrappers/securityWrapper.js` so headers such as `X-Security-Mode` and `X-TPN-Compliance` are always present.
- The security wrapper also logs duration metrics and throws on failure, ensuring the UI surface stays honest with backend errors.

## Environment & Build
- Supported environment variables:
  - `VITE_API_URL` – base URL for REST requests (falls back to relative routing).
  - `VITE_USE_MOCKS` – when `true`, the UI will use in-memory fixtures from `services/api.js`.
- Local commands:
  - `npm run dev` – starts the Vite dev server with hot reload.
  - `npm run build` – produces `dist` artifacts for production deployment.
  - `npm run preview` – optionally verify the production bundle locally.

## Testing & Operational Notes
- The build command (`npm run build`) is the primary validation step and should be executed before tagging changes. The UI does not ship automated tests yet, so focus on manual smoke flows: dashboard cards, transfer creation, audit log streaming, health grid updates, and settings toggles.
- For compliance auditing, `services/api.js` and `wrappers/securityWrapper.js` document how requests are shaped and logged, so refer to them when the backend signals stricter constraints.
