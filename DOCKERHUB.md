# web-RSync

A web UI for managing rsync jobs — replacement for the unmaintained [websync](https://github.com/furier/websync) project.

Schedule, run, and monitor rsync tasks from a browser. Supports local→remote, remote→local, and remote→remote (SSH agent forwarding). Real-time log streaming, SSH key management, cron scheduling, and job history.

**Source:** [github.com/jabastien/web-rsync](https://github.com/jabastien/web-rsync)

---

## Quick Start

```bash
docker run -d \
  --name web-rsync \
  -p 8000:8000 \
  -v web-rsync-data:/data \
  jabastien/web-rsync:latest
```

Open `http://localhost:8000`.

---

## Docker Compose

```yaml
services:
  web-rsync:
    image: jabastien/web-rsync:latest
    container_name: web-rsync
    ports:
      - "8000:8000"
    volumes:
      - ./data:/data          # DB, SSH keys, logs — must be persistent
      - /mnt/nas:/mnt/nas     # expose host paths for rsync tasks (add as needed)
    environment:
      - DATA_DIR=/data
      - MAX_CONCURRENT_JOBS=3
    restart: unless-stopped
```

> Any host path used in a task's source or destination must be mounted into the container.

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATA_DIR` | `/data` | Root for SQLite DB, SSH keys, and job logs |
| `MAX_CONCURRENT_JOBS` | `3` | Max simultaneous rsync processes |

---

## Ports & Volumes

| Port | Description |
|------|-------------|
| `8000` | Web UI + REST API |

| Volume path | Description |
|-------------|-------------|
| `/data` | Persistent data — database, SSH keys, logs. **Must be a persistent volume.** |

---

## Data Layout

```
/data/
├── web_rsync.db          # SQLite database
├── logs/                 # One log file per job run
└── ssh/
    ├── id_ed25519        # Auto-generated Ed25519 private key (created on first start)
    └── id_ed25519.pub    # Public key — deploy to remote hosts for passwordless rsync
```

---

## Tags

| Tag | Description |
|-----|-------------|
| `latest` | Latest release |
| `0.1`, `0.1.0` | Specific version |

---

## Features

- Create, schedule, and run rsync tasks via a web UI
- Remote → Remote sync via SSH agent forwarding (private key never leaves the server)
- Real-time log streaming over SSE; status badges update live
- SSH host management with one-click public key deployment (paramiko SFTP)
- Cron scheduling with human-readable previews
- Inline dry-run validation before saving a task
- Searchable rsync flag reference panel (~60 flags)
- Exclude / include pattern editor (per-task `--exclude-from` / `--include-from`)
- Job history with full per-run logs and purge-all option
- Dark mode by default (user-switchable), mobile-friendly layout
- Full Swagger UI at `http://localhost:8000/docs`

---

## License

MIT — see [LICENSE](https://github.com/jabastien/web-rsync/blob/main/LICENSE)
