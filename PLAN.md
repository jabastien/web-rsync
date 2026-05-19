# web-RSync Implementation Plan

## Context

Replacing the unmaintained Node.js `websync` project (https://github.com/jabastien/websync) with a modern Python-based equivalent. websync is a web UI for managing rsync tasks: create/schedule/run rsync jobs, manage SSH hosts, and view real-time execution logs. The original project is dead and Node.js-based; the rebuild uses FastAPI + SQLite + Vue 3 + Docker.

---

## Stack

| Layer | Choice |
|-------|--------|
| Backend | FastAPI + uvicorn |
| Database | SQLite via SQLAlchemy (WAL mode) |
| Scheduling | APScheduler (AsyncIOScheduler) |
| SSH | paramiko |
| Log streaming | SSE via `sse-starlette` |
| Frontend | Vue 3 + Vite + Pinia + Vue Router |
| Deployment | Docker (multi-stage, single container in prod) |

---

## Project Structure

```
web-RSync/
├── README.md
├── PLAN.md
├── run.sh                        # local dev launcher
├── docker-compose.yml
├── .env.example
├── backend/
│   ├── Dockerfile
│   ├── pyproject.toml            # uv-managed deps
│   ├── main.py                   # FastAPI app, lifespan, router mounts
│   ├── config.py                 # pydantic-settings, reads .env
│   ├── database.py               # engine + session, WAL pragma
│   ├── models/
│   │   ├── task.py
│   │   ├── host.py
│   │   └── job_run.py
│   ├── schemas/
│   │   ├── task.py
│   │   ├── host.py
│   │   └── job_run.py
│   ├── routers/
│   │   ├── tasks.py              # CRUD + /run + /dry-run + /clone + /preview
│   │   ├── hosts.py              # CRUD + /deploy-key + /ssh-keys
│   │   ├── job_runs.py           # list + detail + /log + /stream (SSE)
│   │   └── system.py             # /health + /scheduler-jobs
│   └── services/
│       ├── rsync_runner.py       # async subprocess, log file, JobRun lifecycle, preview
│       ├── scheduler.py          # APScheduler init, job sync with DB
│       └── ssh_manager.py        # key gen on startup, key listing, paramiko deploy
├── frontend/
│   ├── Dockerfile
│   ├── package.json
│   ├── vite.config.ts            # /api proxy to backend in dev
│   ├── src/
│   │   ├── main.ts
│   │   ├── App.vue
│   │   ├── router/index.ts
│   │   ├── stores/               # tasks.ts, hosts.ts, jobs.ts (Pinia)
│   │   ├── api/client.ts         # Axios wrapper
│   │   ├── components/
│   │   │   ├── TaskForm.vue      # includes flag reference panel + dry-run preview
│   │   │   ├── HostForm.vue
│   │   │   ├── LogViewer.vue     # SSE client, auto-scroll
│   │   │   └── ScheduleBadge.vue
│   │   └── views/
│   │       ├── Dashboard.vue
│   │       ├── TasksView.vue
│   │       ├── TaskEditView.vue
│   │       ├── HostsView.vue
│   │       ├── HostEditView.vue
│   │       └── JobHistoryView.vue
└── data/                         # volume mount: db, ssh keys, logs
    └── .gitkeep
```

---

## Data Models

### Task
- `id`, `name` (unique), `source_path`, `dest_path`
- `rsync_options: str` — raw flags string (e.g. `-avz --delete`), not parsed
- `schedule: str | None` — cron expression; null = manual only
- `enabled: bool`, `created_at`, `updated_at`

### Host
- `id`, `name`, `hostname`, `port` (default 22), `username`
- `ssh_key_path: str | None` — filesystem path only, no key material in DB

### JobRun
- `id`, `task_id: int | None` (FK, nullable for preview runs), `trigger` ("manual" | "scheduled" | "dry_run")
- `started_at`, `finished_at`, `exit_code`, `status` ("running" | "success" | "failed" | "cancelled")
- `log_path: str` — path to `data/logs/<id>.log` file (not stored as BLOB)

---

## API Endpoints

**Tasks:** CRUD at `/api/tasks`, plus `POST /{id}/run`, `POST /{id}/dry-run`, `POST /{id}/clone`, `PATCH /{id}/enabled`, `POST /preview`

**Hosts:** CRUD at `/api/hosts`, plus `POST /{id}/deploy-key`, `GET /ssh-keys`

**Job Runs:** `GET /api/job-runs` (filterable), `GET /{id}`, `GET /{id}/log`, `GET /{id}/stream` (SSE)

**System:** `GET /api/system/health`, `GET /api/system/scheduler-jobs`

---

## Key Design Decisions

**Log files, not DB blobs** — logs written to `data/logs/<run_id>.log`. SSE endpoint tails the file. Log file is a decoupling buffer: browser can reconnect mid-run, or read a completed run's full log. Keeps DB size bounded.

**SSE over WebSocket** — unidirectional, native browser support, works through proxies, simpler to implement.

**paramiko for SSH key deploy** — avoids `sshpass`/`expect` hacks. Password passed in request body, used once, never stored or logged.

**Raw rsync_options string** — preserves full rsync expressiveness without maintaining a flags vocabulary.

**Scheduler synced on every CRUD op** — no polling loop; `add_job`/`remove_job` called in the same request handler that modifies a task.

**asyncio.Semaphore for concurrency** — configurable `MAX_CONCURRENT_JOBS` (default 3), no Redis/Celery needed.

**Preview runs use nullable task_id** — ephemeral dry-runs (from the task form before saving) create a JobRun with `task_id=NULL`. This reuses the existing SSE streaming infrastructure without requiring a saved task. The `run_preview` function creates the DB record synchronously (so `run_id` is available immediately for SSE), then fires rsync as a background asyncio task.

---

## Critical Safety Notes

- **Never `shell=True`** in subprocess calls — rsync source/dest paths come from user input, shell injection risk.
- **On startup:** mark any `status="running"` JobRuns as `"failed"` (stale from crash).
- **SSH key files** must be mode 600 inside container — check and warn on startup.
- **rsync SSH args:** use `-e "ssh -i /data/ssh/id_rsa -o StrictHostKeyChecking=accept-new"` explicitly.
- **Cron validation:** call `CronTrigger.from_crontab()` on input and return HTTP 422 on parse error.
- **SQLite WAL mode:** set via `event.listens_for(Engine, "connect")` pragma to handle concurrent writes from scheduler + API.

---

## Implementation Phases

### Phase 1 — Skeleton + Core CRUD ✓
- Init git repo, `pyproject.toml` (uv), `package.json`
- `database.py`, all three ORM models, `Base.metadata.create_all()`
- Pydantic schemas, CRUD routers for tasks + hosts
- `main.py` with CORS, `run.sh`
- Verify with curl

### Phase 2 — Rsync Execution + Job Runs ✓
- `rsync_runner.py`: async subprocess, log file write, JobRun lifecycle
- `/run` and `/dry-run` endpoints on tasks router
- `job_runs.py` router: list, detail, full log text, SSE stream
- Test with a real local rsync task

### Phase 3 — Scheduling ✓
- `scheduler.py`: APScheduler setup, `add_job`/`remove_job` helpers
- Wire into FastAPI lifespan (startup loads all enabled scheduled tasks)
- Task CRUD syncs scheduler on create/update/delete/toggle
- `/api/system/scheduler-jobs` endpoint

### Phase 4 — SSH Management ✓
- `ssh_manager.py`: key generation on startup if missing, key listing
- `/deploy-key` endpoint using paramiko
- Frontend host form: deploy key button + password modal

### Phase 5 — Frontend ✓
- Scaffold Vue 3 + Vite + Pinia + Vue Router + Axios
- Views in order: Tasks → Task Edit → Hosts → Job History → Log Viewer → Dashboard
- `LogViewer.vue`: `EventSource` with cleanup on unmount, auto-scroll
- Cron input with `cronstrue` for human-readable preview and next-run times

### Phase 6 — Docker + Production ✓
- Multi-stage `Dockerfile`: stage 1 builds Vue (`node`), stage 2 Python runtime copies `dist/` → `static/`
- FastAPI serves `StaticFiles` at `/` in production
- `docker-compose.yml` with volume mount for `./data:/data`
- Test data persistence across container restart

### Phase 7 — Task Form UX Enhancements ✓

#### rsync Flag Reference Panel
- Collapsible panel toggled by "Browse flags ▾" link below the rsync options input
- ~60 flags organized into 8 groups: Common, Sync Behaviour, File Selection, Permissions & Ownership, Links & Special Files, SSH/Network, Checksums & Integrity, Output & Logging
- Each flag is a clickable chip — appends flag to the options input (skips duplicates)
- Hover shows full description; panel scrolls independently at max 420px height

#### Inline Dry-Run Preview
- **▶ Test Dry Run** button in the task form — works before the task is saved
- Posts `{source_path, dest_path, rsync_options}` to `POST /api/tasks/preview`
- Backend creates a `JobRun` record with `task_id=NULL`, fires rsync `--dry-run -v` as a background asyncio task, returns `run_id` synchronously
- Frontend opens SSE stream to `/api/job-runs/{run_id}/stream`, streams output into an inline dark log panel with auto-scroll
- Spinner while running; `✓ OK` / `✗ Failed` badge on completion; **✕ Clear** to reset
- `JobRun.task_id` made nullable to support these ephemeral preview runs

---

## Backend Dependencies (pyproject.toml)
`fastapi`, `uvicorn[standard]`, `sqlalchemy`, `alembic`, `pydantic-settings`, `apscheduler`, `sse-starlette`, `paramiko`, `python-multipart`

## Frontend Dependencies (package.json)
`vue`, `vue-router`, `pinia`, `axios`, `vite`, `@vitejs/plugin-vue`, `typescript`, `vue-tsc`, `cronstrue`

### Phase 8 — Code Review Fixes ✓

**Critical bugs:**
- `/run` and `/dry-run` now create `JobRun` synchronously and return `run_id` immediately; rsync fires as a background asyncio task. Previously `asyncio.create_task()` returned an asyncio Task object, never the integer `run_id`.
- `stream_log` SSE: added `db.expire(run)` before each status check — SQLAlchemy identity map was caching the initial `status="running"` forever, so the `done` event never fired.
- `update_task` changed from `exclude_none=True` to `exclude_unset=True` so `PUT` with `schedule: null` actually clears the schedule.

**Security:**
- `ssh_manager`: `AutoAddPolicy` → `WarningPolicy` (MITM note in comment).
- `deploy_key` rewritten to use SFTP instead of `exec_command` + `echo` — eliminates shell quoting entirely.

**Code quality:**
- `run_task`/`run_dry` unified via shared `_start_run` + `_build_rsync_cmd(dry_run=)`, removing ~40 lines of duplication.
- `log_path` removed from `JobRunRead` response schema and frontend interface (leaked filesystem paths; not used in UI).
- Frontend: Run/Dry redirect to `/history/:run_id` so the live log auto-selects.
- `cors_origins` default trimmed to dev-only `[:5173]`.
- `run.sh` env loading switched to `set -a; source .env; set +a` (robust multiline/quoted values).

**Deployment:**
- Deployed at `/docker/web-rsync/` via container-commit workaround (AppArmor blocks `docker build` in this Proxmox LXC). `rebuild.sh` automates re-deploys. `security_opt: apparmor=unconfined` added to compose for runtime.

---

### Phase 9 — UX Hardening, Feature Additions & Bug Fixes ✓

#### UI Improvements
- **Table layout**: Tasks and Hosts tables use two rows per item — data row + actions row spanning full width — eliminating horizontal scroll. Path/hostname cells truncate with CSS ellipsis. Column widths controlled by `<colgroup>`.
- **Path tooltip**: Hovering a truncated path cell in TasksView shows a dark monospace tooltip with the full path. Only shown when `el.scrollWidth > el.clientWidth`. Rendered via `<Teleport to="body">` to avoid table overflow clipping.
- **Confirmation modal**: `ConfirmModal.vue` reusable component — shown before deleting any task or host, and before purging history. Displays item name and count.
- **Deploy Key modal**: Success swaps modal content to a green checkmark state instead of `alert()`. Error renders inline.
- **Help view**: `/help` route covering path formats, Remote→Remote, rsync options (common + 15 homelab scenarios), Hosts, Job History. All "local" references clarified as "server/container filesystem" with docker-compose volume mount example.
- **Sidebar version badge**: `v<version>` at the bottom, injected at build time via Vite `define` from `package.json`.
- **crontab.guru** link added to schedule field hint, Help view, and README.

#### Task Features
- **Exclude / Include pattern fields**: `exclude_patterns` and `include_patterns` text columns on `Task` (newline-separated). Inline SQLite migration on startup. Backend writes `data/patterns/{task_id}_{exclude,include}.txt` before each run; injects `--include-from` then `--exclude-from`. Preview and clone both propagate the fields. Frontend: two side-by-side monospace textareas in `TaskForm`.

#### Remote → Remote SSH ✓
- `_build_cmd()` detects dual-remote paths and runs `ssh -A source_host "rsync … dest_path"` — agent forwarding lets the source authenticate to destination without the private key leaving the server.
- `ensure_ssh_agent()` / `stop_ssh_agent()` manage an `ssh-agent` process and load the server key on startup/shutdown.
- `run_preview` updated to use shared `_build_cmd()` (previously bypassed remote→remote logic).

#### Job History
- **Purge history**: `DELETE /api/job-runs` deletes all completed runs and log files; `running` runs are skipped. Frontend: Purge button (disabled when nothing to purge) guarded by `ConfirmModal` with exact count.
- **Live log race condition fixed**: `LogViewer` was mounting before `store.fetchAll()` resolved → `live` prop always `false` → `loadStatic()` instead of `startStream()`. Fix: `await fetchAll()` before rendering, `loaded` flag gates the `LogViewer` render.
- **Status polling**: `JobHistoryView` polls `fetchAll()` every 3 s while any run is `running`, stops automatically. `LogViewer` emits `done` on SSE close; parent refreshes store immediately. Status badge shown inline in log panel header.

#### Infrastructure
- **SPA deep-link fix**: Replaced `StaticFiles(html=True)` at `/` (which only fell back to `index.html` for `/`) with `/assets` static mount + `/{full_path:path}` catch-all returning `index.html`. Direct access to `/history/42`, `/tasks`, `/help` etc. now works.
- **docker-compose example** with volume mount guidance added to README.

---

## Verification

1. `./run.sh` — starts uvicorn; hit `GET /api/system/health` → `{"status": "ok"}`
2. `POST /api/tasks` + `POST /api/tasks/{id}/run` → log file appears in `data/logs/`, SSE stream delivers lines
3. Create a task with a cron schedule → check `/api/system/scheduler-jobs` → job listed
4. `POST /api/hosts/{id}/deploy-key` → passwordless SSH to test host works
5. `POST /api/tasks/preview` with `{source_path, dest_path, rsync_options}` → returns `run_id`, log file created, status `success`
6. `docker compose up` → UI loads at `http://localhost:8000`, create + run a task end-to-end
