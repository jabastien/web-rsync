# SKILL.md — Using the web-RSync API

This document describes how an agent can drive web-RSync programmatically.  
Base URL: `http://<host>:8000` — no authentication required.

---

## Quick reference

| Goal | Method + Path |
|------|--------------|
| Health check | `GET /api/system/health` |
| List tasks | `GET /api/tasks` |
| Create task | `POST /api/tasks` |
| Run task | `POST /api/tasks/{id}/run` |
| Dry-run task | `POST /api/tasks/{id}/dry-run` |
| Ephemeral preview (no saved task) | `POST /api/tasks/preview` |
| Clone task | `POST /api/tasks/{id}/clone` |
| Toggle enabled | `PATCH /api/tasks/{id}/enabled` |
| Delete task | `DELETE /api/tasks/{id}` |
| List hosts | `GET /api/hosts` |
| Create host | `POST /api/hosts` |
| Deploy SSH key to host | `POST /api/hosts/{id}/deploy-key` |
| List job runs | `GET /api/job-runs` |
| Get run status | `GET /api/job-runs/{id}` |
| Get full log text | `GET /api/job-runs/{id}/log` |
| Purge completed runs | `DELETE /api/job-runs` |
| List scheduled jobs | `GET /api/system/scheduler-jobs` |
| List container mount points | `GET /api/system/mounts` |

Interactive Swagger UI: `http://<host>:8000/docs`

---

## Tasks

### Create a task

```bash
curl -s -X POST http://localhost:8000/api/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "name": "nas-backup",
    "source_path": "/mnt/nas/source/",
    "dest_path": "user@remote:/backup/",
    "rsync_options": "-avz --delete",
    "schedule": "0 2 * * *",
    "enabled": true,
    "exclude_patterns": "*.tmp\n*.log",
    "include_patterns": ""
  }'
```

Response: full task object including `"id"`.

**Field notes:**
- `schedule` — 5-field cron (`"0 2 * * *"`); `null` or `""` = manual only
- `exclude_patterns` / `include_patterns` — newline-separated patterns (`\n`); passed as `--exclude-from` / `--include-from`
- `enabled` — `false` prevents scheduled runs; manual runs still work

### Update a task

```bash
curl -s -X PUT http://localhost:8000/api/tasks/1 \
  -H "Content-Type: application/json" \
  -d '{"name":"nas-backup","source_path":"/mnt/nas/source/","dest_path":"user@remote:/backup/","rsync_options":"-avz","schedule":null,"enabled":true,"exclude_patterns":"","include_patterns":""}'
```

`PUT` requires all fields. To clear `schedule`, send `"schedule": null` explicitly.

### Toggle enabled

```bash
curl -s -X PATCH http://localhost:8000/api/tasks/1/enabled \
  -H "Content-Type: application/json" \
  -d '{"enabled": false}'
```

---

## Running tasks and checking results

### Run a task (async)

```bash
RUN=$(curl -s -X POST http://localhost:8000/api/tasks/1/run | python3 -c "import sys,json; print(json.load(sys.stdin)['run_id'])")
echo "run_id: $RUN"
```

Response: `{"run_id": 42}` — rsync is running in the background.

### Poll until complete

```bash
while true; do
  STATUS=$(curl -s http://localhost:8000/api/job-runs/$RUN | python3 -c "import sys,json; print(json.load(sys.stdin)['status'])")
  echo "status: $STATUS"
  [[ "$STATUS" != "running" ]] && break
  sleep 3
done
```

Possible statuses: `running` · `success` · `failed` · `cancelled`

### Fetch the log

```bash
curl -s http://localhost:8000/api/job-runs/$RUN/log | python3 -c "import sys,json; print(json.load(sys.stdin)['log'])"
```

### Ephemeral preview (validate without saving a task)

```bash
curl -s -X POST http://localhost:8000/api/tasks/preview \
  -H "Content-Type: application/json" \
  -d '{
    "source_path": "/mnt/nas/source/",
    "dest_path": "/mnt/nas/dest/",
    "rsync_options": "-avz --delete",
    "exclude_patterns": "",
    "include_patterns": ""
  }'
```

Returns `{"run_id": N}`. The run has `task_id: null` and `trigger: "dry_run"`. Poll and fetch log the same way as a normal run.

---

## Hosts and SSH key deployment

### Create a host

```bash
curl -s -X POST http://localhost:8000/api/hosts \
  -H "Content-Type: application/json" \
  -d '{"name":"nas","hostname":"192.168.1.10","port":22,"username":"backup","ssh_key_path":null}'
```

### Deploy the server's public key to a host

```bash
curl -s -X POST http://localhost:8000/api/hosts/1/deploy-key \
  -H "Content-Type: application/json" \
  -d '{"password":"secret"}'
```

The password is used once and never stored. On success: `{"status": "ok"}`.  
After deployment, rsync tasks to that host authenticate without a password.

### View the server's public key

```bash
curl -s http://localhost:8000/api/hosts/ssh-keys | python3 -c "import sys,json; [print(k['public_key']) for k in json.load(sys.stdin)]"
```

---

## Job history

### List runs (optionally filtered by task)

```bash
curl -s "http://localhost:8000/api/job-runs?task_id=1&limit=10"
```

### Purge all completed runs and their log files

```bash
curl -s -X DELETE http://localhost:8000/api/job-runs
# → {"deleted": N}
```

Running jobs are never affected.

---

## Scheduler

```bash
# List all currently scheduled jobs
curl -s http://localhost:8000/api/system/scheduler-jobs
```

Scheduling is automatic: saving a task with a non-null `schedule` and `enabled: true` registers it immediately. Deleting or disabling a task removes it from the scheduler in the same request.

---

## System / container info

### List container mount points

Useful for discovering what host paths are accessible inside the container before writing task paths.

```bash
curl -s http://localhost:8000/api/system/mounts | python3 -m json.tool
```

Response (example):

```json
[
  {"mountpoint": "/data", "device": "zpool/subvol-110", "fstype": "zfs", "access": "rw"},
  {"mountpoint": "/etc/hostname", "device": "zpool/subvol-110", "fstype": "zfs", "access": "rw"}
]
```

Virtual filesystems (`proc`, `sysfs`, `tmpfs`, `cgroup`, etc.) and `/proc`/`/sys`/`/dev` prefixes are filtered out. The list is sorted by mountpoint.

---

## Path formats

| Scenario | Source | Destination |
|----------|--------|-------------|
| Server → server | `/mnt/nas/source/` | `/mnt/nas/backup/` |
| Server → remote | `/mnt/nas/source/` | `user@host:/backup/` |
| Remote → server | `user@host:/data/` | `/mnt/nas/backup/` |
| Remote → remote | `user@host1:/data/` | `user@host2:/backup/` |

"Server" = the filesystem inside the web-RSync container (or LXC). Trailing slash on source matters: `src/` copies contents; `src` copies the directory itself.

For remote→remote, deploy the server's public key to **both** hosts first.

---

## Error handling

All errors return standard HTTP status codes with a JSON body:

```json
{"detail": "Task not found"}
```

`422 Unprocessable Entity` — invalid cron expression, missing required field  
`404` — task/host/run not found  
`409` — duplicate task name  
`500` — rsync failed to start (check log)

A job with `exit_code != 0` and `status: "failed"` means rsync ran but reported errors — always fetch the log to diagnose.
