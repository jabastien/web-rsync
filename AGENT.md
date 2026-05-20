# AGENT.md — web-RSync

FastAPI + Vue 3 web UI for managing rsync jobs. Backend in `backend/`, frontend in `frontend/`, runtime data in `data/` (gitignored). Full context in `CLAUDE.md` and `PLAN.md`.

---

## Before touching anything

Read `context/lessons_learned.md`. It documents real bugs and wrong turns from prior sessions.

---

## Layout

```
backend/
  main.py           # FastAPI app + lifespan (migrations, SSH key gen, scheduler)
  config.py         # Settings: DATA_DIR, MAX_CONCURRENT_JOBS, patterns_dir
  database.py       # SQLAlchemy engine + session (WAL mode)
  models/           # task.py, host.py, job_run.py
  routers/          # tasks.py, hosts.py, job_runs.py, system.py
  services/
    rsync_runner.py # _build_cmd(), _inject_pattern_files(), run_task(), run_preview()
    scheduler.py    # APScheduler helpers
    ssh_manager.py  # Ed25519 key gen (ssh-keygen), ssh-agent lifecycle, paramiko deploy
  static/           # Built frontend (output of npm run build — do not edit)
frontend/
  src/
    views/          # Dashboard, TasksView, TaskEditView, HostsView, JobHistoryView, HelpView
    components/     # TaskForm, LogViewer, ConfirmModal, ScheduleBadge
    stores/         # tasks.ts, hosts.ts, jobs.ts
    api/client.ts   # Axios wrapper
```

---

## Commands

```bash
# Run backend locally (creates .venv if missing)
./run.sh

# Frontend dev server (requires Node.js)
cd frontend && npm run dev        # http://localhost:5173 — proxies /api to :8000

# Build frontend → backend/static/ (required before deploying)
cd frontend && npm run build

# Inspect DB
sqlite3 data/web_rsync.db

# Rebuild Docker container (Proxmox LXC — AppArmor blocks docker build)
cd frontend && npm run build && cd ..
/docker/web-rsync/rebuild.sh

# Check running container logs
docker logs web-rsync --tail=40
```

---

## Hard rules — do not break these

| Rule | Why |
|------|-----|
| **Never `shell=True`** in subprocess calls | Source/dest paths are user input — shell injection risk |
| **`--include-from` before `--exclude-from`** | rsync filter order matters; reversing it silently changes which files are excluded |
| **`db.expire(run)` before status check in `stream_log`** | SQLAlchemy identity map caches the initial `running` status forever without it |
| **`exclude_unset=True` on task PUT** | `exclude_none=True` prevents clearing nullable fields like `schedule` |
| **SPA catch-all is `/{full_path:path}` returning `index.html`** | `StaticFiles(html=True)` only catches `/`, not deep links like `/history/42` |
| **Deploy key uses SFTP, not `exec_command` + echo** | Avoids shell quoting bugs with special characters in public keys |
| **Inline SQLite migrations wrapped in try/except** | Same `ALTER TABLE` will raise on second run — idempotency required |

---

## Known pitfalls

- **`paramiko.Ed25519Key` has no `.generate()` method** — use `ssh-keygen -t ed25519 -N "" -f <path>` via subprocess instead.
- **`uv pip install -r pyproject.toml`** is correct syntax for uv. Do not change to `-e .` — hatchling is not configured.
- **Docker `RUN` steps fail on this Proxmox LXC** (AppArmor). Always use `rebuild.sh`, never `docker compose up --build`.
- **Frontend changes require a rebuild** — `backend/static/` is the served build output, not the source. Editing `.vue` files has no effect until `npm run build` is run and the container is rebuilt.

---

## Schema changes

Add new columns via inline migration in `main.py` lifespan (see existing pattern), not Alembic. Both ORM model and Pydantic schema must be updated together.

## Deployment after code changes

```bash
cd /DEV/web-RSync
git pull
cd frontend && npm run build && cd ..
/docker/web-rsync/rebuild.sh
docker logs web-rsync --tail=20   # verify clean startup
```
