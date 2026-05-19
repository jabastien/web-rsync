# CLAUDE.md

## Project Overview

Web-based rsync job manager — replacement for the unmaintained [websync](https://github.com/jabastien/websync). Schedule and monitor rsync jobs via a browser UI with SSH key management and real-time log streaming.

## Stack

- **Backend:** FastAPI + SQLAlchemy + SQLite (`data/web_rsync.db`)
- **Frontend:** Vue 3 + Vite + TypeScript (served from `frontend/`)
- **Scheduler:** APScheduler (in-process cron-style scheduling)
- **SSH:** paramiko (`services/ssh_manager.py`)
- **Deploy:** Docker (`docker-compose.yml`)

## Architecture

```
backend/
  main.py           # FastAPI app, lifespan startup
  config.py         # Settings (DATA_DIR, MAX_CONCURRENT_JOBS)
  database.py       # SQLAlchemy engine + session
  models/           # SQLAlchemy ORM: task.py, host.py, job_run.py
  routers/          # REST endpoints: tasks, hosts, job_runs, system
  services/
    rsync_runner.py # Subprocess rsync execution + SSE log streaming
    scheduler.py    # APScheduler job management
    ssh_manager.py  # SSH key generation (paramiko)
  static/           # Served frontend build output
frontend/
  src/              # Vue 3 components, stores, views
data/               # SQLite DB, SSH keys, logs (gitignored)
```

## Commands

```bash
# Backend only (auto-creates .venv if missing)
./run.sh            # Starts uvicorn on :8000

# Frontend dev (separate terminal — Node.js required)
cd frontend && npm install && npm run dev   # Vite dev server on :5173

# Frontend build (output → backend/static for serving)
cd frontend && npm run build

# Docker (full stack)
docker compose up --build

# Inspect DB
sqlite3 data/web_rsync.db
```

## Environment

`run.sh` loads `.env` if present. Key vars:
- `DATA_DIR` — default `./data`
- `MAX_CONCURRENT_JOBS` — default `3`


## Context & Notes

**Read `context/lessons_learned.md` at the start of every session before doing any work.**

## Tree

- `context/lessons_learned.md` — Dated lessons from past sessions

**Note:** Node.js must be installed to build/run the frontend. Backend runs standalone via `./run.sh`.

