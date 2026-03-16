# web-RSync

A web UI for managing rsync tasks — replacement for the unmaintained [websync](https://github.com/jabastien/websync) project.

## Features

- Create, schedule, and run rsync tasks via a web UI
- Real-time log streaming over SSE
- SSH host management with automated key deployment
- Cron scheduling with human-readable previews
- Job run history with full logs

## Stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI + uvicorn |
| Database | SQLite (WAL mode) via SQLAlchemy |
| Scheduling | APScheduler |
| SSH | paramiko |
| Log streaming | SSE via sse-starlette |
| Frontend | Vue 3 + Vite + Pinia + Vue Router |
| Deployment | Docker (multi-stage) |

## Quick Start (dev)

```bash
cp .env.example .env
./run.sh
```

Frontend dev server (requires Node 18+):

```bash
cd frontend
npm install
npm run dev   # proxies /api to localhost:8000
```

## Docker

```bash
docker compose up --build
```

UI available at http://localhost:8000

## Configuration

Copy `.env.example` to `.env` and adjust:

| Variable | Default | Description |
|----------|---------|-------------|
| `DATA_DIR` | `./data` | Where DB, logs, and SSH keys are stored |
| `MAX_CONCURRENT_JOBS` | `3` | Max simultaneous rsync processes |

## Data Layout

```
data/
├── web_rsync.db     # SQLite database
├── logs/            # One .log file per job run
└── ssh/             # Auto-generated RSA key pair
    ├── id_rsa
    └── id_rsa.pub
```

## API

- `GET  /api/system/health` — health check
- `GET  /api/tasks` — list tasks
- `POST /api/tasks/{id}/run` — trigger a run
- `GET  /api/job-runs/{id}/stream` — SSE log stream
- Full docs at `/docs` (Swagger UI)
