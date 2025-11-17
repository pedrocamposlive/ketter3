# API Function Matrix

## Front-end function usage

| Function | Components / Hooks | Backend endpoint | Notes |
| --- | --- | --- | --- |
| `createTransfer` | `FilePicker.jsx` | `POST /transfers` | Normalizes UI form into the TransferCreate schema, enqueues a transfer job. |
| `getTransfers` | `TransfersPage.jsx`, `AlertsPanel.jsx`, `Alerts.jsx` (indirect via `getAlerts`) | `GET /transfers` | Polls the live queue with optional status/limit filters. |
| `getTransfer` | _Not yet consumed_ | `GET /transfers/{transfer_id}` | Available for future transfer detail views; returns a single `TransferResponse`. |
| `getTransferChecksums` | `TransferProgress.jsx` | `GET /transfers/{transfer_id}/checksums` | Fetches the triple SHA-256 verification set for the selected job. |
| `getTransferLogs` | `TransferHistory.jsx` | `GET /transfers/{transfer_id}/logs` | Retrieves the audit trail for a completed/failed transfer. |
| `deleteTransfer` | `TransferHistory.jsx` | `DELETE /transfers/{transfer_id}` | Removes a transfer from history (guarded against running jobs). |
| `downloadTransferReport` | `TransferHistory.jsx` | `GET /transfers/{transfer_id}/report` | Streams the signed PDF report and triggers a browser download.
| `getRecentTransfers` | `TransferHistory.jsx` | `GET /transfers/history/recent` | Lists the last 30 days of transfers for the history view. |
| `pauseWatchMode` | _Not yet consumed_ | `POST /transfers/{transfer_id}/pause-watch` | Stops a continuous watch job without cancelling running transfers. |
| `resumeWatchMode` | _Not yet consumed_ | `POST /transfers/{transfer_id}/resume-watch` | Re-enqueues the continuous watch job. |
| `getWatchHistory` | _Not yet consumed_ | `GET /transfers/{transfer_id}/watch-history` | Returns paginated watch detections for a watch-enabled transfer. |
| `cancelTransfer` | `TransfersPage.jsx`, `TransferProgress.jsx` (via `onCancel`) | `POST /transfers/{transfer_id}/cancel` | Gracefully cancels active transfers and logs the cancellation event. |
| `getAlerts` | `AlertsPanel.jsx`, `Alerts.jsx` | Derived from `GET /transfers` | Synthesizes a lightweight alerts array from transfer statuses (failed/cancelled/pending). |
| `getStatus` | `hooks/useSystemStatus.jsx` | `GET /status` | Polls API, DB, Redis, and worker health metadata. |
| `getSystemHealth` | `hooks/useSystemHealth.jsx` | `GET /health` | Simple health check used for dashboards and monitors. |
| `getVolumes` | `SettingsPage.jsx` | `GET /volumes` | Loads configured volumes, statuses, and server info. |
| `getAvailableVolumes` | `SettingsPage.jsx` | `GET /volumes/available` | Returns mounted/usable volumes for dropdowns. |
| `reloadVolumes` | _Not yet consumed_ | `POST /volumes/reload` | Hot-reloads `ketter.config.yml` without restarting the service. |
| `validateVolumePath` | _Not yet consumed_ | `GET /volumes/validate` | Confirms that a provided path falls under the configured volumes. |
| `getAuditLogs` | `AuditPage.jsx` | Derived from `GET /transfers/history/recent` | Builds a flattened audit-style stream for the compliance page. |

## Backend endpoint summary

| Method | Path | Purpose | Primary frontend function |
| --- | --- | --- | --- |
| `POST` | `/transfers` | Create a new transfer job with watch/move controls. | `createTransfer` |
| `GET` | `/transfers` | List transfers for dashboards, queue snapshots, and alerts. | `getTransfers` |
| `GET` | `/transfers/{transfer_id}` | Read a single transfer record. | `getTransfer` |
| `GET` | `/transfers/{transfer_id}/checksums` | Fetch triple SHA-256 checksums. | `getTransferChecksums` |
| `GET` | `/transfers/{transfer_id}/logs` | Retrieve audit events for a transfer. | `getTransferLogs` |
| `DELETE` | `/transfers/{transfer_id}` | Remove a transfer (not allowed for running jobs). | `deleteTransfer` |
| `GET` | `/transfers/{transfer_id}/report` | Stream a PDF transfer report. | `downloadTransferReport` |
| `GET` | `/transfers/history/recent` | List transfers from the last N days (default 30). | `getRecentTransfers`, `getAuditLogs` |
| `POST` | `/transfers/{transfer_id}/pause-watch` | Pause a continuous watch job. | `pauseWatchMode` |
| `POST` | `/transfers/{transfer_id}/resume-watch` | Resume a paused watch job. | `resumeWatchMode` |
| `GET` | `/transfers/{transfer_id}/watch-history` | Paginated watch detection history. | `getWatchHistory` |
| `POST` | `/transfers/{transfer_id}/cancel` | Cancel an active transfer. | `cancelTransfer` |
| `GET` | `/volumes` | List all configured volumes and server metadata. | `getVolumes` |
| `GET` | `/volumes/available` | List currently mounted/available volumes. | `getAvailableVolumes` |
| `POST` | `/volumes/reload` | Reload configuration without restarting. | `reloadVolumes` |
| `GET` | `/volumes/validate` | Validate that a path is under the allowed volumes. | `validateVolumePath` |
| `GET` | `/status` | Detailed API/DB/Redis/worker health. | `getStatus` |
| `GET` | `/health` | Lightweight health probe. | `getSystemHealth` |

## Notes

- The alerts and audit streams are synthesized from the transfer lists because dedicated `/alerts` and `/audit/logs` endpoints are not implemented yet.
- Watch mode helpers are exported so UI pages can leverage the endpoints once the controls are wired up.
- `downloadTransferReport` handles the PDF response and triggers a browser download via the `Content-Disposition` header.
