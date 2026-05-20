# CLAUDE.md

## Project Overview

Web-based rsync job manager — replacement for the unmaintained [websync](https://github.com/jabastien/websync). Schedule and monitor rsync jobs via a browser UI with SSH key management and real-time log streaming.

## Stack

- **Backend:** FastAPI + SQLAlchemy + SQLite (`data/web_rsync.db`)
- **Frontend:** Vue 3 + Vite + TypeScript (served from `frontend/`)
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
    components/     # TaskForm (flag panel, dry-run, pattern fields), LogViewer (SSE), ConfirmModal, ScheduleBadge
    stores/         # tasks.ts, hosts.ts, jobs.ts (purge)
    api/client.ts   # Axios wrapper (previewTask, purgeJobRuns)
data/               # SQLite DB, SSH keys, logs, pattern files (gitignored)
```

## Key Design Decisions (do not relitigate without reason)

- **`shell=False`** everywhere in subprocess — paths come from user input.
- **`task_id` nullable** on `JobRun` — supports ephemeral preview runs from `POST /api/tasks/preview`.
- **Pattern files** written to `data/patterns/{task_id}_{exclude,include}.txt` before each run; `--include-from` injected before `--exclude-from` (order matters).
- **Remote→Remote**: `ssh -A source_host "rsync … dest"` with agent forwarding — private key never leaves server.
- **SPA routing**: `/assets` static mount + `/{full_path:path}` catch-all returning `index.html` (not `StaticFiles(html=True)`).
- **SSE identity map bug**: `db.expire(run)` before each status check in `stream_log` — SQLAlchemy caches the initial `status="running"` without it.
- **Inline SQLite migration** in `main.py` lifespan: `ALTER TABLE tasks ADD COLUMN … DEFAULT ''` wrapped in try/except for idempotency.
- **Deploy key via SFTP** (not `exec_command` + echo) — eliminates shell quoting risk.

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

## Context & Notes

**Read `context/lessons_learned.md` at the start of every session before doing any work.**

## Tree

- `context/lessons_learned.md` — Dated lessons from past sessions

**Note:** Node.js must be installed to build/run the frontend. Backend runs standalone via `./run.sh`.
