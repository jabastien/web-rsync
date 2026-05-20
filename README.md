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
- **Exclude / include pattern editor** — per-task `--exclude-from` and `--include-from` pattern lists, managed as text fields (no manual file editing)
- **Remote → Remote sync** — both paths as `user@host:/path`; web-RSync SSHes into the source and forwards its agent so rsync authenticates to the destination without the private key leaving the server
- Real-time log streaming over SSE (Server-Sent Events); status badges update live, no reload required
- SSH host management with automated public-key deployment
- Cron scheduling with human-readable previews ([crontab.guru](https://crontab.guru/) linked)
- Job run history with full per-run logs; **purge history** with confirmation
- Confirmation modal on all destructive actions (delete task, delete host, purge history)
- In-app **Help** page covering all features, path formats, and homelab rsync recipes
- Version badge in sidebar; SPA deep-links (`/history/42`, `/tasks`, etc.) work on direct access / refresh

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

## Deploy on a New System

### Prerequisites

| Requirement | Version |
|-------------|---------|
| Docker + Compose plugin | 24+ |
| git | any |
| Node.js *(Proxmox LXC path only)* | 18+ |

### 1 — Clone from Gitea

```bash
git clone https://gitea.vertieres.net/alain/web-RSync.git
cd web-RSync
```

### 2 — Create the data directory and config

```bash
mkdir -p /docker/web-rsync/data
cp .env.example /docker/web-rsync/.env   # edit if needed
```

Create `/docker/web-rsync/docker-compose.yml` (see [example below](#docker-composeyml-example)).

### 3 — Build and start

**Normal Docker host** (standard multi-stage build — Node + Python in one step):

```bash
cp docker-compose.yml /docker/web-rsync/docker-compose.yml   # or write your own
docker compose -f /docker/web-rsync/docker-compose.yml up --build -d
```

**Proxmox LXC** (AppArmor blocks `docker build` RUN steps — use the container-commit workaround):

```bash
# Build the Vue frontend first (requires Node.js on the host)
cd frontend && npm install && npm run build && cd ..

# Copy rebuild script to deploy location and run it
cp /docker/web-rsync/rebuild.sh /docker/web-rsync/rebuild.sh   # already present if cloned
/docker/web-rsync/rebuild.sh
```

> If `rebuild.sh` is not yet at `/docker/web-rsync/`, copy it from the repo root:
> ```bash
> cp rebuild.sh /docker/web-rsync/rebuild.sh
> chmod +x /docker/web-rsync/rebuild.sh
> ```

### 4 — Verify

```bash
curl http://localhost:8000/api/system/health
# → {"status":"ok"}
```

Open `http://<host-ip>:8000` in a browser.

### Re-deploying after code changes

```bash
git pull
# Normal host:
docker compose -f /docker/web-rsync/docker-compose.yml up --build -d
# Proxmox LXC:
cd frontend && npm run build && cd .. && /docker/web-rsync/rebuild.sh
```

---

## Native Debian LXC (no Docker)

Run web-RSync directly under systemd — no container overhead.

### 1 — Install system packages

```bash
apt update && apt install -y git python3 python3-pip python3-venv curl rsync openssh-client

# uv (Python package manager)
curl -Ls https://astral.sh/uv/install.sh | sh
source "$HOME/.local/bin/env"   # or open a new shell

# Node.js 22 LTS (only needed for the one-time frontend build)
curl -fsSL https://deb.nodesource.com/setup_22.x | bash -
apt install -y nodejs
```

### 2 — Clone and build

```bash
git clone https://gitea.vertieres.net/alain/web-RSync.git /opt/web-rsync
cd /opt/web-rsync

# Build Vue frontend → backend/static/
cd frontend && npm install && npm run build && cd ..

# Python virtualenv + dependencies
cd backend
uv venv
uv pip install -r pyproject.toml
cd ..
```

### 3 — Configure

```bash
mkdir -p /opt/web-rsync/data
cp .env.example /opt/web-rsync/backend/.env
```

Edit `/opt/web-rsync/backend/.env`:

```env
DATA_DIR=/opt/web-rsync/data
MAX_CONCURRENT_JOBS=3
```

### 4 — Systemd service

Create `/etc/systemd/system/web-rsync.service`:

```ini
[Unit]
Description=web-RSync
After=network.target

[Service]
WorkingDirectory=/opt/web-rsync/backend
EnvironmentFile=/opt/web-rsync/backend/.env
ExecStart=/opt/web-rsync/backend/.venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
systemctl daemon-reload
systemctl enable --now web-rsync
systemctl status web-rsync
```

### 5 — Verify

```bash
curl http://localhost:8000/api/system/health
# → {"status":"ok"}
```

Open `http://<lxc-ip>:8000` in a browser.

### Re-deploying after code changes

```bash
cd /opt/web-rsync
git pull
cd frontend && npm run build && cd ..
systemctl restart web-rsync
```

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

### docker-compose.yml example

```yaml
services:
  web-rsync:
    image: web-rsync:latest
    container_name: web-rsync
    ports:
      - "8000:8000"       # UI + API
    volumes:
      - ./data:/data       # DB, SSH keys, logs — must be persistent
      - /mnt/nas:/mnt/nas  # expose host paths for rsync tasks (add as needed)
    environment:
      - DATA_DIR=/data
      - MAX_CONCURRENT_JOBS=3
    security_opt:
      - apparmor=unconfined   # required on Proxmox LXC
    restart: unless-stopped
```

> Any host directory used in a task's source or destination path must be mounted into the container. `./data` is the minimum required volume. Add further mounts for each path rsync needs to reach on the host filesystem.

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

> **All rsync processes run on the web-RSync server, not in your browser.** Your browser is a control panel only — it sends instructions and displays logs but is never part of the file transfer.
>
> When running in Docker, **"local" paths refer to the filesystem inside the Docker container**, not the machine where you open the browser. To expose host directories to the container, add volume mounts to `docker-compose.yml`:
> ```yaml
> volumes:
>   - ./data:/data          # already present (DB, logs, SSH keys)
>   - /mnt/nas:/mnt/nas     # add any host path rsync should reach
> ```

**To create a task:**

1. Go to **Tasks → New Task**
2. Fill in:
   - **Name** — a unique label for this task
   - **Source Path** — path on the web-RSync server (`/mnt/nas/source/`) or remote SSH path (`user@host:/path/`). Not your browser's machine.
   - **Destination Path** — same format; both sides can be remote (see [Remote → Remote](#remote--remote-ssh--ssh))
   - **rsync Options** — raw flags passed directly to rsync (default: `-avz`). Use the **Browse flags** panel to explore available options. The field is not shell-processed — `$(date +%F)` will not expand.
   - **Include Patterns** (`--include-from`) — one pattern per line; included before excludes are evaluated
   - **Exclude Patterns** (`--exclude-from`) — one pattern per line; e.g. `*.tmp`, `node_modules/`
   - **Schedule** — optional cron expression (e.g. `0 2 * * *` = every day at 02:00). Leave blank for manual-only. A human-readable translation appears as you type. See [crontab.guru](https://crontab.guru/).
   - **Enabled** — uncheck to disable without deleting
3. Use **▶ Test Dry Run** to validate your paths, options, and patterns before saving. This runs rsync with `--dry-run` immediately and streams the output inline — no files are transferred and the task does not need to be saved first.
4. Click **Save**

**To run a task manually:** click **Run** in the Tasks list. The page redirects to Job History where you can watch the live log.

**To clone a task:** click **Clone**. A copy is created with schedule cleared and enabled set to false — safe to modify without affecting the original.

#### Path formats

A bare path starting with `/` is **local to the web-RSync server** (inside the Docker container when using Docker). A path in `user@host:/path` form is a remote SSH endpoint.

| Scenario | Source example | Destination example |
|----------|---------------|-------------------|
| Server → server *(both paths are on the container's filesystem)* | `/mnt/nas/source/` | `/mnt/nas/backup/` |
| Server → remote (SSH) | `/mnt/nas/source/` | `user@host2:/backup/` |
| Remote → server (SSH) | `user@host1:/data/` | `/mnt/nas/backup/` |
| Remote → remote (SSH) | `user@host1:/data/` | `user@host2:/backup/` |

> Trailing slash on the source matters to rsync: `src/` copies the *contents*; `src` copies the *directory itself*.

#### Remote → Remote (SSH → SSH)

rsync does not natively support two remote endpoints. web-RSync handles this transparently: when both paths are SSH remotes, the server SSHes into the source host and runs rsync from there, forwarding its SSH agent (`-A`) so the source can authenticate to the destination — the private key never leaves the server.

```
web-RSync server  →ssh -A→  source host  →rsync→  destination host
```

**Prerequisites:**

1. Deploy the server's public key to **both** hosts using the **Deploy Key** button on the Hosts page.
2. Create the task with both paths as `user@host:/path/` — the server detects the scenario automatically, no extra configuration required.

**Notes:**
- The source host must have `rsync` installed.
- `StrictHostKeyChecking` is set to `accept-new` on both hops, so first-time connections are handled automatically.
- For large transfers, consider adding `--info=progress2` to rsync options for cleaner progress output in the log viewer.

#### rsync option sets

> The options field is passed directly to rsync — it is **not** processed by a shell. Constructs like `$(date +%F)` will not expand; use a fixed path instead.

**Common**

| Use case | Options | Notes |
|----------|---------|-------|
| Standard archive | `-avz` | Recursive, preserves permissions/times, compresses in transit |
| Strict mirror | `-avz --delete` | Removes destination files that no longer exist at source |
| Preserve hard links | `-avzH` | Important for deduplicated backups and system directories |
| Bandwidth throttle | `-avz --bwlimit=50000` | Value is KB/s (50000 ≈ 50 MB/s) |
| Mirror with dry-run first | `-avz --delete -n` | Validate what would be deleted before running for real |

**Homelab scenarios**

| Use case | Options | Notes |
|----------|---------|-------|
| VM / disk images | `-av --sparse` | Preserves sparse regions in qcow2, raw images, LXC rootfs. Drop `-z` — compressing binary images wastes CPU |
| VM images + resumable | `-av --sparse --inplace --partial` | In-place writes halve peak disk usage; `--partial` resumes an interrupted transfer |
| Cross-system (different UIDs) | `-avz --numeric-ids` | Uses numeric UID/GID instead of names — essential between Proxmox nodes or containers with different user databases |
| Docker volumes / full permissions | `-avzAX` | Adds ACL (`-A`) and extended attribute (`-X`) preservation — important for Docker named volumes and system directories |
| Stay within one filesystem | `-avz -x` | Don't cross mount points — prevents accidentally syncing bind-mounted paths or overlapping volumes |
| Checksum-based comparison | `-avz --checksum` | Compares by file content instead of mtime+size — slower but reliable after a restore or when clocks differ between hosts |
| Skip large files | `-avz --max-size=500m` | Avoid accidentally syncing large ISOs or VM disk images; supports `k`, `m`, `g` suffixes |
| Exclude temp / cache | `-avz --exclude='*.tmp' --exclude='*.log'` | Chain as many `--exclude` flags as needed |
| Include only one file type | `-avz --include='*/' --include='*.conf' --exclude='*'` | Recursively sync only `.conf` files. `--include='*/'` is required so rsync descends into directories; the final `--exclude='*'` rejects everything not already included. Useful for config-only backups across many service directories |
| Set destination permissions | `-avz --chmod=D755,F644` | Override permissions at the destination regardless of source. `D` = directories, `F` = files. Useful when syncing media to a NAS where Jellyfin or Plex requires specific read permissions, or when source and destination users differ |
| Only recent files (hot backup) | `-avz --max-age=7` | Transfer only files modified in the last 7 days. Ideal for frequent incremental jobs that capture recent activity without re-syncing a large unchanged archive. Value is in days |
| Archive old files only | `-avz --min-age=90` | Transfer only files not modified in 90+ days. Useful for tiering cold data to a NAS or off-site target. Combine with `--remove-source-files` to implement a move-to-archive pattern |
| Protect files from --delete | `-avz --delete --filter='protect .env'` | Mirror with deletion but shield specific files from being removed at the destination. The `protect` filter rule prevents rsync from deleting a matching file even if it is absent from the source. Chain multiple: `--filter='protect *.env' --filter='protect *.secret'` |
| Resumable over unreliable links | `-avz --partial` | Keeps partially transferred files so the next run resumes from where it stopped |
| Live progress (large transfers) | `-avz --info=progress2` | Compact single-line progress — cleaner than `-v` for thousands of files |

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

> Use **[crontab.guru](https://crontab.guru/)** to build and validate expressions interactively.

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

Click any row in Job History to view its log. Running jobs stream live output via SSE; completed jobs load the full log from disk. Status badges update automatically — no reload needed. Use **Purge History** (with confirmation) to delete all completed runs and their log files in one step; running jobs are never affected.

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
| DELETE | `/api/job-runs` | Purge all completed runs and log files |
