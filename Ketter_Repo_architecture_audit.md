# Ketter Repo Architecture Audit

## 1. Repository structure overview
- `app/` houses the FastAPI backend, SQLAlchemy models, schemas, security helpers, services, utilities, and the `main.py` entry point that wires routers and middleware (`app/main.py:1`).
- `frontend/` contains the Vite-powered UI (components, pages, services, polling helpers) plus Docker config and release strategy docs.
- `docs/`, `tests/`, and markdown report files capture validation guides, audit summaries, and evidence for each phase.
- Scripts like `quick_validate.sh`, `run_ketter.sh`, and `validate_system.sh` exist for running validations without reaching out to Docker/Redis/DB.
- `ketter.config.yml` sits at the repo root next to configuration helpers (`app/config/__init__.py:1`), pairing declarative volume metadata with runtime hooks that auto-attach user directories for local dev.

## 2. FastAPI routing map
- **Transfers router** (`app/routers/transfers.py:37`):
  - `POST /transfers`: creates a transfer job, validates source/destination existence, sets watch flags, persists `Transfer`, logs creation, and enqueues either `transfer_file_job`, `watch_and_transfer_job`, or `watcher_continuous_job` depending on watch_mode/watch_continuous (`app/routers/transfers.py:49-220`).
  - `GET /transfers`: list with pagination and status filtering.
  - `GET /transfers/{id}`: fetch single transfer.
  - `GET /transfers/{id}/checksums`: retrieve triple SHA-256 artifacts.
  - `GET /transfers/{id}/logs`: stream audit trail entries.
  - `DELETE /transfers/{id}`: cascade delete transfer and related checksums/logs (later sections cover cancellation/pause endpoints, but they are used by the UI via `api.js` abstractions).
- **Volumes router** (`app/routers/volumes.py:1`):
  - `GET /volumes`: list configured volumes and server metadata.
  - `GET /volumes/available`: only those currently mounted.
  - `POST /volumes/reload`: reseed config from disk.
  - `GET /volumes/validate`: expose `KetterConfig.validate_path()` to the UI for dropdown guardrails.

## 3. Schema logic
- `TransferCreate` (`app/schemas.py:20-92`) enforces 1-4096 char paths, `settle_time_seconds` bounds (5-300s), `watch_mode_enabled` vs `watch_continuous`, and restricts `operation_mode` to `copy|move`. Inputs are sanitized via `sanitize_path`/`validate_path_pair` (see next section) before reaching the DB.
- Response schemas (`TransferResponse`, `TransferListResponse`, `ChecksumResponse`, etc.) expose folder metadata, watch-mode timestamps, and operation-mode fields so the UI can render badges and progress bars without recomputing them.
- `TransferUpdate` only exposes `status`, `bytes_transferred`, `progress_percent`, and `error_message`, reflecting that mutations are handled by workers, not clients.
- Volume resolution is handled by `KetterConfig` (`app/config/__init__.py:1-130`); it loads `ketter.config.yml`, resolves macOS/Windows user directories, and exposes `validate_path()` for the `/volumes/validate` endpoint.

## 4. Path security analysis
- `sanitize_path` (`app/security/path_security.py:72-202`) normalizes inputs, rejects control characters or encoded traversal, forbids `..`, resolves real paths, blocks symlinks (unless `allow_symlinks=True` for sources), and ensures the result starts with a configured volume (with VLAN awareness via `TRANSFER_NODE_MODE`/`KETTER_VLAN_ID`).
- `validate_path_pair` (`app/security/path_security.py:205-259`) reuses `sanitize_path`, handles non-existent destination parents, and enforces source ≠ destination, so MOVE/COPY operations never operate in-place.
- Helper utilities `is_path_safe` and `get_safe_path_info` allow diagnostics to inspect path validity for UI metrics or future automated audits.
- Volume protection is reinforced by default volumes in `ketter.config.yml` (e.g., `/Volumes/Nexis`, `/tmp`) and dynamic attachments such as Desktop/Documents via `ALLOW_USER_DESKTOP` in `app/config/__init__.py:71-99`.

## 5. Queue + worker architecture
- The UI always posts to FastAPI, which enqueues jobs on the RQ `default` queue created in `app/routers/transfers.py:37-40` with Redis URL from `REDIS_URL`.
- Job timeouts/TTL constants live in `app/services/worker_jobs.py:802-826` (`TRANSFER_JOB_CONFIG`, `WATCH_TRANSFER_JOB_CONFIG`, `WATCH_CONTINUOUS_JOB_CONFIG`), so enqueue statements in `create_transfer` reference consistent numbers (`app/routers/transfers.py:140-210` and the watcher logic in `worker_jobs`).
- `transfer_file_job` (standard COPY/MOVE) loads the transfer, skips canceled ones, calls `transfer_file_with_verification`, then reports final checksum or failure. Exceptions bubble so RQ can retry (`app/services/worker_jobs.py:23-131`).
- `watch_and_transfer_job` waits for stability via `watch_folder_until_stable` (`app/services/worker_jobs.py:133-322`), logs progress, then delegates to `transfer_file_with_verification`.
- `watcher_continuous_job` (`app/services/worker_jobs.py:324-659`) loops with settle-time detection per file, records detections as `WatchFile`, enqueues per-file `transfer_file_job`, and tracks audit logs/cycle counts. It can be paused externally by clearing `watch_continuous`.
- `_wait_for_file_settle` enforces settle_time seconds of unchanged size (1s sleeps) before permitting transfers, and failure thresholds (e.g., 1 hour max per cycle) prevent stuck watchers.

## 6. copy_engine deep-dive
- `transfer_file_with_verification` (`app/core/copy_engine.py:320-760`) phases:
  1. Load transfer and ensure `TransferStatus.PENDING`.
  2. Acquire exclusive lock for MOVE (`acquire_transfer_lock` from `app/database.py:51-78`).
  3. Re-validate paths via `validate_path_pair`, update records, and emit audit logs.
  4. Calculate `source` checksum (`calculate_sha256`).
  5. Copy file (with ZIP Smart support): folders are zipped via `zip_folder_smart`, copied as a ZIP, then unzipped at destination (`.zip_engine` helpers).
  6. Compute destination checksum and compare to source; mismatches raise `ChecksumMismatchError` and roll back.
  7. Write FINAL checksum and progress logs.
  8. For folder transfers, unzip to destination path, cleanup temporary ZIP files, and mark `unzip_completed`.
  9. In MOVE mode, call `verify_destination_readable` (`app/core/copy_engine.py:52-156`), delete source contents or file (`delete_source_after_move`), and release the lock (`app/core/copy_engine.py:760-780`).
 10. Update transfer status to `COMPLETED` and log `AuditEventType.TRANSFER_COMPLETED`.
- Triple SHA-256 ensures data integrity; `verify_destination_readable` adds heuristics (size checks, read first/last kilobytes, non-empty folder) before deleting sources.
 
## 7. Watch mode analysis
- `watch_and_transfer_job` (`app/services/worker_jobs.py:133-322`) is used for `watch_mode_enabled`; it logs `watch_started_at`, waits up to 1 hour for stability (`watch_folder_until_stable`), records checks history, and proceeds with the normal transfer. Timeouts log errors and prevent moves.
- `watcher_continuous_job` (`app/services/worker_jobs.py:324-659`) powers continuous monitoring: loops every 5 seconds, diffs source folder contents, enqueues a `transfer_file_job` for each new file, tracks cycles/detected files (`watch_cycle_count`, `last_files_processed`), and logs each detection in `WatchFile`.
- Settle time enforcement happens via `_wait_for_file_settle` (requires `settle_time_seconds` consecutive seconds of unchanged size) before enqueueing; `max_wait_seconds=3600` caps hangups.
- Error thresholds: watch timeouts lead to audit events, retries rely on RQ (exceptions propagate); the continuous watcher keeps running for 24h (job timeout) but can be stopped via `watch_continuous` flag or transfers being deleted.

## 8. Config loader and dynamic volume attachment
- `KetterConfig` (`app/config/__init__.py:1-125`) loads `ketter.config.yml` (root) to populate volumes and server metadata, with defaults/additions when the file is absent.
- `_attach_local_user_paths` respects the `ALLOW_USER_DESKTOP` flag (default `1`) and automatically adds Desktop/Documents/Downloads on macOS/Windows to ease local dev, while avoiding duplicates via `_volume_exists` (`app/config/__init__.py:71-99`).
- `/volumes/reload` refreshes this config on-demand, enabling runtime volume changes without restarting the API.

## 9. CORS logic
- `app/main.py:20-42` seeds allowed origins from `CORS_ORIGINS` env or a whitelist of localhost dev ports, applies `CORSMiddleware` permitting credentials across explicit methods/headers, and logs the decision at startup (guards the UI hosted on Vite from unauthorized domains).
- The middleware also allows custom `X-Ketter-Client` headers, which the frontend uses in `api.js` (`DEFAULT_HEADERS`), ensuring preflight checks succeed.

## 10. Frontend integration flow
- `FilePicker` (`frontend/src/components/FilePicker.jsx:1-240`) gathers source/destination paths, watch mode selection (none/once/continuous), settle time, and copy/move toggles. It calls `createTransfer` (`frontend/src/services/api.js:105-169`) which issues `POST /transfers` with the normalized payload, clearing UI state and surfacing success/failure alerts.
- `api.js` wraps `fetch` with default headers, JSON serialization, error parsing, and helpers for transfers, checksums, history, cancellation, volume lists, and health checks. `API_BASE` falls back to `http://localhost:8000` but respects `VITE_API_URL`.
- `startPolling` (`frontend/src/services/pollingService.js:1-30`) powers `TransfersPage`, `Alerts`, `AuditPage`, and health hooks by re-fetching every 5s (fallback 15s) and wiring results into `TransferProgress`, `TransferHistory`, and alerts so the UI reflects job states and audit trails.
- `TransferProgress` displays badges derived from `TransferResponse` (folder/watch flags), a progress bar (`progress_percent`), and lets operators cancel transfers or view checksums via `getTransferChecksums`.

## 11. Cross-module lifecycle
- **UI → API:** `FilePicker` issues `POST /transfers` and relies on `TransfersPage` polling to reflect new jobs.
- **API → DB:** `create_transfer` persists the `Transfer` with status `PENDING`, zeroed bytes, and watch metadata via SQLAlchemy models (`app/models.py:26-210`).
- **DB → Redis:** Upon save, FastAPI enqueues `transfer_file_job`/`watch_and_transfer_job`/`watcher_continuous_job` on RQ (`app/routers/transfers.py`), adding audit logs for queue events.
- **Redis → Worker:** Worker jobs (defined in `app/services/worker_jobs.py`) pull payloads via `RQ`, load the session (`SessionLocal`), and call `transfer_file_with_verification`.
- **Worker → copy_engine:** Copy engine handles filesystem operations, checksum records, folder zipping/unzipping, MOVE deletions, and audit event logging.
- **Copy_engine → AuditLog:** Throughout the flow, `log_event` emits `AuditLog` entries for events like security validation, checksum calculations, unzip completion, and errors (`app/core/copy_engine.py:760-780`).
- **AuditLog → UI:** UI polls `/transfers/{id}/logs` and `/transfers` (history) via `api.js` to show audit data, progress badges, and checksum modals; alerts are derived from that same `/transfers` data for real-time status.

## 12. Identified inconsistencies, potential risks, and missing validations
- `FilePicker` sends `watch_mode` as strings (`'none'`, `'once'`, `'continuous'`), but `TransferCreate` only understands boolean flags `watch_mode_enabled` and `watch_continuous`, so the API currently relies on the router to interpret those (`frontend` does not map `'once'` to `watch_mode_enabled` before posting) – risk of incorrect payloads if UI state diverges.
- `sanitize_path` rejects any path containing `..`, so legitimate relative paths (e.g., `./project`) must be absolute; UI placeholders already encourage absolute usage, yet the API does not soften the restriction if the operator pastes a relative path.
- `watch_and_transfer_job` sleeps up to 1 second per settle check inside a loop without exponential backoff; repeated watch failures can hog worker threads if the folder keeps fluctuating.
- The continuous watcher assumes a single Redis connection (`watcher_continuous_job` re-imports `Queue`/`Redis` per loop) but lacks circuit breaker logic when Redis is unreachable; that could stall detection loops and flood logs.
- No schema-level validation enforces minimum `settle_time_seconds` when `watch_continuous` is `true`, nor is there a server-side guard preventing `move` mode without sufficient audit (the UI gate is all that enforces it).

## 13. Recommended improvements
1. Normalize front-end payloads by deriving `watch_mode_enabled`/`watch_continuous` booleans from the `watchMode` radio (transfer once vs continuous) before calling `createTransfer`, ensuring API schemas receive the expected shape.
2. Inject request-level path normalization in routers to expand relative paths (e.g., via `os.path.abspath`) before `schema` validation to reduce friction while retaining defense-in-depth.
3. Add debounce/backoff to `watch_and_transfer_job` and circuit-breaker guards for Redis in `watcher_continuous_job` so repeated timeouts don’t exhaust worker slots or flood `AuditLog`.
4. Introduce server-side enforcement for `settle_time_seconds` when watch modes are enabled (currently the schema allows 5–300 regardless of context), plus an explicit check forbidding `operation_mode='move'` unless watchers confirm the destination is readable via `verify_destination_readable`.

## 14. Suggested pytest tests to strengthen validation
- Extend `tests/test_path_security.py` with scenarios that send relative paths (`./foo/bar`) and symlink parents to confirm `validate_path_pair` still raises or normalizes appropriately.
- Add a regression test around `watch_mode` payload interpretation so `watchMode='once'` results in `watch_mode_enabled=True` and `watch_continuous=False` even if the UI state changes.
- Create targeted tests mimicking Redis failures inside `watcher_continuous_job` to ensure the loop backs off and logs once rather than spinning (mock `Redis.from_url` and `Queue.enqueue`).
- Add a `transfer_file_with_verification` test for MOVE mode where `verify_destination_readable` fails (e.g., read permission denied) to guarantee proper rollback and audit logging; reuse the existing `tests/test_comprehensive_move_copy.py` patterns.

## 15. Conclusions and next-step recommendations
- The repo cleanly separates concerns: FastAPI routers expose a deterministic transfer API; schemas defend against malformed inputs; security modules enforce path hygiene; the worker layer orchestrates queueing, watch modes, and the copy engine; audit logs provide traceability; and the React UI polls for real-time state while allowing operators to intervene.
- Run the full test suite currently available in `tests/` (e.g., `pytest tests/test_path_security.py tests/test_comprehensive_move_copy.py tests/test_watcher_continuous_job.py`) once Redis/Postgres simulators are available in the sandbox-free environment.
- Prioritize syncing UI payload shapes with backend flags, hardening watch-mode resilience, and extending `sanitize_path` coverage as described above to reduce operational risk before hitting production deployments.
