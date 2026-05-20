# CLAUDE.md

## Project Overview

Web-based rsync job manager — replacement for the unmaintained [websync](https://github.com/furier/websync). Schedule and monitor rsync jobs via a browser UI with SSH key management and real-time log streaming.

## Stack

- **Backend:** FastAPI + SQLAlchemy + SQLite (`data/web_rsync.db`)
- **Frontend:** Vue 3 + Vite + TypeScript + `@mdi/font` (served from `frontend/`)
- **Scheduler:** APScheduler (in-process cron-style scheduling)
- **SSH:** paramiko (`services/ssh_manager.py`)
- **Deploy:** Docker (`docker-compose.yml`) or native systemd on Debian LXC

## Architecture

```
backend/
  main.py           # FastAPI app, lifespan startup, inline SQLite migrations, SPA catch-all
  config.py         # Settings (DATA_DIR, MAX_CONCURRENT_JOBS, patterns_dir)
  database.py       # SQLAlchemy engine + session (WAL mode)
  models/           # ORM: task.py (exclude/include_patterns), host.py, job_run.py (task_id nullable)
  routers/          # tasks.py, hosts.py, job_runs.py (DELETE purge), system.py
  services/
    rsync_runner.py # _build_cmd() (remote→remote detection), _inject_pattern_files(), SSE log
    scheduler.py    # APScheduler job management
    ssh_manager.py  # Key gen, ssh-agent lifecycle (ensure/stop), paramiko SFTP key deploy
  static/           # Served frontend build output
frontend/
  src/
    views/          # Dashboard, TasksView, TaskEditView, HostsView, JobHistoryView, HelpView
    components/     # TaskForm (flag panel, dry-run, pattern fields, host pickers, mounts panel), LogViewer (SSE), ConfirmModal, ScheduleBadge
    composables/    # useTheme.ts (dark/light toggle, localStorage persistence)
    stores/         # tasks.ts, hosts.ts, jobs.ts (purge)
    api/client.ts   # Axios wrapper (previewTask, purgeJobRuns, getMounts)
    style.css       # CSS custom properties: :root = dark, [data-theme="light"] = light overrides
data/               # SQLite DB, SSH keys, logs, pattern files (gitignored)
```

## Key Design Decisions (do not relitigate without reason)

- **`shell=False`** everywhere in subprocess — paths come from user input.
- **`task_id` nullable** on `JobRun` — supports ephemeral preview runs from `POST /api/tasks/preview`.
- **Pattern files** written to `data/patterns/{task_id}_{exclude,include}.txt` before each run; `--include-from` injected before `--exclude-from` (order matters).
- **Ed25519 keys** — generated at `data/ssh/id_ed25519` on first start. If a legacy `id_rsa` exists without `id_ed25519`, a warning is logged but the old key is not deleted automatically.
- **Remote→Remote**: `ssh -A source_host "rsync … dest"` with agent forwarding — private key never leaves server.
- **SPA routing**: `/assets` static mount + `/{full_path:path}` catch-all returning `index.html` (not `StaticFiles(html=True)`).
- **SSE identity map bug**: `db.expire(run)` before each status check in `stream_log` — SQLAlchemy caches the initial `status="running"` without it.
- **Inline SQLite migration** in `main.py` lifespan: `ALTER TABLE tasks ADD COLUMN … DEFAULT ''` wrapped in try/except for idempotency.
- **Deploy key via SFTP** (not `exec_command` + echo) — eliminates shell quoting risk.
- **Theme singleton**: `useTheme.ts` holds state at module level (not inside `setup()`), ensuring all components share one toggle.
- **Host picker decompose timing**: `decomposePath()` runs inside `onMounted` after `hostsStore.fetchAll()` — hosts must be loaded before parsing `user@hostname:path`.
- **Hot-deploy pattern**: `docker cp backend/static <container>:/app/backend/` deploys frontend changes without a container restart. Python changes require `docker restart`.

## Commands

```bash
# Backend only (auto-creates .venv if missing)
./run.sh            # Starts uvicorn on :8000

# Frontend dev (separate terminal — Node.js required)
cd frontend && npm install && npm run dev   # Vite dev server on :5173

# Frontend build (output → backend/static for serving)
cd frontend && npm run build

# Docker (full stack — Proxmox LXC: use rebuild.sh instead of --build)
docker compose up --build

# Native systemd (Debian LXC)
systemctl restart web-rsync   # after git pull + npm run build

# Inspect DB
sqlite3 data/web_rsync.db
```

## Environment

`run.sh` loads `.env` if present. Key vars:
- `DATA_DIR` — default `./data` (Docker sets `/data`)
- `MAX_CONCURRENT_JOBS` — default `3`

## Deployment Paths

| Path | When to use |
|------|-------------|
| `docker compose up --build` | Normal Docker host |
| `rebuild.sh` | Proxmox LXC (AppArmor blocks `docker build` RUN steps) |
| systemd + uvicorn | Native Debian LXC (no Docker) — see README |

## Completed Phases

- **Phase 1** — Skeleton + Core CRUD (tasks, hosts)
- **Phase 2** — Rsync execution + JobRun lifecycle + SSE streaming
- **Phase 3** — APScheduler integration
- **Phase 4** — SSH key management + paramiko deploy
- **Phase 5** — Vue 3 frontend (all views + LogViewer)
- **Phase 6** — Docker multi-stage build
- **Phase 7** — Flag reference panel + inline dry-run preview (`POST /api/tasks/preview`)
- **Phase 8** — Code review fixes (race conditions, security, deduplication)
- **Phase 9** — UX hardening: path tooltip, ConfirmModal, HelpView, version badge, exclude/include patterns, Remote→Remote, purge history, live log polling, SPA deep-link fix
- **Phase 10** — Docs: native Debian LXC deployment guide (systemd, no Docker)
- **Phase 11** — Ed25519 SSH keys (replaced RSA-4096); legacy `id_rsa` detection with startup warning
- **Phase 12** — Dark mode (default, user-switchable), Material Design Icons, mobile-friendly layout (hamburger + slide-in sidebar)
- **Phase 13** — Host pickers in task form (split host dropdown + path input); mount points panel (`GET /api/system/mounts`) with click-to-copy

## Related Documents

- `AGENT.md` — subagent orientation (layout, hard rules, deployment workflow)
- `SKILL.md` — API usage guide for agents consuming web-RSync as a service
- `PLAN.md` — full implementation history and design decisions

## Context & Notes

**Read `context/lessons_learned.md` at the start of every session before doing any work.**

## Tree

- `context/lessons_learned.md` — Dated lessons from past sessions

**Note:** Node.js must be installed to build/run the frontend. Backend runs standalone via `./run.sh`.
