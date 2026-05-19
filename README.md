# web-RSync

A web UI for managing rsync tasks — replacement for the unmaintained [websync](https://github.com/jabastien/websync) project.

## Architecture

![Architecture Diagram](docs/architecture.png)

> [Open in Excalidraw](https://excalidraw.com/#json=qptvNRHEOhVo4dtsWBhtq,BdGljb7rRpciXu4Sf5ynag)

---

## Features

- Create, schedule, and run rsync tasks via a web UI
- **Inline dry-run test** — validate paths and options before saving, with live log output
- **rsync flag reference** — searchable flag panel with ~60 flags; click to append to options
- Real-time log streaming over SSE (Server-Sent Events)
- SSH host management with automated public-key deployment
- Cron scheduling with human-readable previews
- Job run history with full per-run logs

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

---

## Quick Start (dev)

```bash
cp .env.example .env
./run.sh          # starts backend on http://localhost:8000
```

Frontend hot-reload dev server (requires Node 18+):

```bash
cd frontend
npm install
npm run dev       # http://localhost:5173 — proxies /api to :8000
```

## Docker (production)

Deployed at `/docker/web-rsync/` with a persistent data volume:

```bash
# First deploy (or after code changes)
/docker/web-rsync/rebuild.sh

# Start / stop / restart
docker compose -f /docker/web-rsync/docker-compose.yml up -d
docker compose -f /docker/web-rsync/docker-compose.yml down
```

UI and API both served at `http://localhost:8000`. The Vue frontend is built into the container and served as static files by FastAPI.

> **Note — Proxmox LXC:** `docker compose up --build` fails on this host due to AppArmor restrictions in LXC containers. `rebuild.sh` works around this by building via container commit. To enable normal builds, add `lxc.apparmor.profile = unconfined` to the LXC config on the Proxmox host and restart the container.

---

## Configuration

Copy `.env.example` to `.env` and adjust:

| Variable | Default | Description |
|----------|---------|-------------|
| `DATA_DIR` | `./data` | Root for DB, logs, and SSH keys |
| `MAX_CONCURRENT_JOBS` | `3` | Max simultaneous rsync processes |

## Data Layout

```
data/
├── web_rsync.db      # SQLite database (WAL mode)
├── logs/             # One .log file per job run (named by run ID)
└── ssh/              # Auto-generated RSA key pair (created on first start)
    ├── id_rsa        # Private key — chmod 600, never leave the server
    └── id_rsa.pub    # Public key — deployed to remote hosts
```

> **Note:** `data/` should be a persistent volume (Docker) or a directory outside your repo (dev). It is git-ignored except for the `.gitkeep` placeholder.

---

## Usage Guide

### Tasks

A **Task** defines one rsync job: source, destination, options, and an optional cron schedule.

**To create a task:**

1. Go to **Tasks → New Task**
2. Fill in:
   - **Name** — a unique label for this task
   - **Source Path** — local path (`/srv/data/`) or remote (`user@host:/path/`)
   - **Destination Path** — same format; at least one side must be local unless using an rsync daemon
   - **rsync Options** — raw flags passed directly to rsync (default: `-avz`). Use the **Browse flags** panel to explore available options.
   - **Schedule** — optional cron expression (e.g. `0 2 * * *` = every day at 02:00). Leave blank for manual-only. A human-readable translation appears as you type.
   - **Enabled** — uncheck to disable without deleting
3. Use **▶ Test Dry Run** to validate your paths and options before saving. This runs rsync with `--dry-run` immediately and streams the output inline — no files are transferred and the task does not need to be saved first.
4. Click **Save**

**To run a task manually:** click **Run** in the Tasks list. The page redirects to Job History where you can watch the live log.

**To clone a task:** click **Clone**. A copy is created with schedule cleared and enabled set to false — safe to modify without affecting the original.

#### Path formats

| Scenario | Source example | Destination example |
|----------|---------------|-------------------|
| Local → local | `/home/alain/docs/` | `/mnt/backup/docs/` |
| Local → remote (SSH) | `/home/alain/docs/` | `alain@nas:/backup/docs/` |
| Remote → local (SSH) | `alain@nas:/data/` | `/mnt/local/` |

> Trailing slash on the source matters to rsync: `src/` copies the *contents*; `src` copies the *directory itself*.

#### Common rsync option sets

| Use case | Options |
|----------|---------|
| Standard archive | `-avz` |
| Archive + delete removed files | `-avz --delete` |
| Archive + preserve hard links | `-avzH` |
| Bandwidth-limited backup | `-avz --bwlimit=5000` |
| Mirror with dry-run first | `-avz --delete -n` |

---

### Hosts

A **Host** is a remote SSH target. Registering a host lets web-RSync deploy its SSH public key to that machine, enabling passwordless rsync over SSH.

> You do **not** need to register a host to use it in a task — you can type `user@host:/path` directly. Hosts are only needed for the automated key-deployment feature.

**To add a host:**

1. Go to **Hosts → New Host**
2. Fill in:
   - **Name** — a label (e.g. `nas`, `vps-backup`)
   - **Hostname / IP** — the address rsync/SSH will connect to
   - **Port** — SSH port (default 22)
   - **Username** — the SSH user on the remote machine
   - **SSH Key Path** — leave blank to use the auto-generated server key (`data/ssh/id_rsa`)
3. Click **Save**

**To deploy the SSH public key to a host:**

1. The remote host must have SSH running and you must know the password for the target user.
2. On the Hosts page, click **Deploy Key** next to the host.
3. Enter the SSH password in the modal. The key is appended to `~/.ssh/authorized_keys` on the remote machine.
4. After deployment, rsync tasks targeting that host will use key-based authentication — no password required.

**What "Deploy Key" does under the hood:**

- Connects to the host via paramiko using the password you provide (used once, never stored)
- Runs: `mkdir -p ~/.ssh && chmod 700 ~/.ssh && echo '<pubkey>' >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys`
- The password is never written to disk or logs

**To view the server's public key** (to add manually to a host): it is shown at the top of the Hosts page. You can also find it at `data/ssh/id_rsa.pub`.

#### SSH key prerequisites on the remote host

- SSH server must be running (`openssh-server`)
- The target user must exist
- `~/.ssh/` does not need to exist — the deploy step creates it
- `StrictHostKeyChecking` is set to `accept-new` for rsync connections, so the first connection will automatically trust the host key

---

### Scheduling

Schedules use standard **5-field cron syntax**: `minute hour day month weekday`

| Expression | Meaning |
|------------|---------|
| `0 2 * * *` | Every day at 02:00 |
| `0 */6 * * *` | Every 6 hours |
| `30 1 * * 0` | Every Sunday at 01:30 |
| `0 0 1 * *` | First day of every month at midnight |

The form shows a human-readable translation as you type. Scheduled tasks only run when **Enabled** is checked.

---

### Job History

Every run (manual, scheduled, or dry-run) creates a **Job Run** record with:

- Status: `running` / `success` / `failed` / `cancelled`
- Trigger: `manual` / `scheduled` / `dry_run`
- Full rsync output log, persisted to `data/logs/<id>.log`

Click any row in Job History to view its log. Running jobs stream live output via SSE; completed jobs load the full log from disk.

---

## API Reference

Full interactive docs available at `http://localhost:8000/docs` (Swagger UI).

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/system/health` | Health check |
| GET | `/api/system/scheduler-jobs` | List active scheduled jobs |
| GET | `/api/tasks` | List all tasks |
| POST | `/api/tasks` | Create task |
| GET | `/api/tasks/{id}` | Get task |
| PUT | `/api/tasks/{id}` | Update task |
| DELETE | `/api/tasks/{id}` | Delete task |
| PATCH | `/api/tasks/{id}/enabled` | Toggle enabled |
| POST | `/api/tasks/{id}/run` | Trigger manual run |
| POST | `/api/tasks/{id}/dry-run` | Trigger dry run (saved task) |
| POST | `/api/tasks/{id}/clone` | Clone task |
| POST | `/api/tasks/preview` | Ephemeral dry-run (no saved task) |
| GET | `/api/hosts` | List hosts |
| POST | `/api/hosts` | Create host |
| PUT | `/api/hosts/{id}` | Update host |
| DELETE | `/api/hosts/{id}` | Delete host |
| GET | `/api/hosts/ssh-keys` | List server SSH keys |
| POST | `/api/hosts/{id}/deploy-key` | Deploy public key to host |
| GET | `/api/job-runs` | List runs (filter: `?task_id=N&limit=N`) |
| GET | `/api/job-runs/{id}` | Get run detail |
| GET | `/api/job-runs/{id}/log` | Get full log text |
| GET | `/api/job-runs/{id}/stream` | SSE live log stream |
