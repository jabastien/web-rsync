# Lessons Learned

## 2026-03-15 — pydantic-settings computed fields for derived paths
Use `@computed_field` + `@property` instead of `model_post_init` for derived settings in pydantic-settings v2. The `model_post_init` approach silently fails to update fields. `computed_field` works cleanly and is the documented v2 pattern.

## 2026-03-15 — Default DATA_DIR should be relative for dev
Default `data_dir = Path("./data")` (relative) rather than `Path("/data")` (absolute). Absolute default breaks local dev when /data doesn't exist and is unwritable. Docker sets `DATA_DIR=/data` explicitly via env.

## 2026-03-15 → 2026-05-20 — Node.js now installed (v22.22.2)
Node.js 22.22.2 and npm 10.9.7 are installed and working. The earlier lesson (no Node.js) is no longer accurate. `npm run build` works directly from `frontend/`.

## 2026-05-19 — uv pip install -r pyproject.toml is valid uv syntax
`uv pip install -r <pyproject.toml>` reads `[project].dependencies` directly — it is NOT wrong like pip would be. Changing it to `uv pip install -e .` breaks builds because hatchling requires a proper package structure. Only use `-e` if pyproject.toml includes `[tool.hatch.build.targets.wheel]` with the correct packages path.

## 2026-05-19 — paramiko.Ed25519Key has no generate() method
`paramiko.RSAKey`, `DSSKey`, and `ECDSAKey` have `.generate()` class methods; `Ed25519Key` does not. Use `ssh-keygen -t ed25519 -N "" -f <path>` (subprocess) to generate Ed25519 keys — `openssh-client` is already installed in the container.

## 2026-05-20 — Deploying new frontend builds to a running Docker container
When AppArmor blocks `docker build`, use `docker cp backend/static <container>:/app/backend/` to hot-swap the pre-built static files into the running container. The FastAPI static file mount reads from disk per request so there is no restart needed.

## 2026-05-20 — @mdi/font v7.4: mdi-archive-sync does not exist
`mdi-archive-sync` is not in @mdi/font 7.4.47. Use `mdi-archive-refresh` instead (the closest semantic equivalent). Always verify icon names with `grep "mdi-<name>" node_modules/@mdi/font/css/materialdesignicons.min.css`.

## 2026-05-20 — Python backend changes require container restart; static files do not
`docker cp backend/static <container>:/app/backend/` hot-swaps frontend with no restart — FastAPI reads static files from disk per request. Python file changes (routers, services, etc.) require `docker restart <container>` because uvicorn does not auto-reload in production mode.

## 2026-05-20 — CORS_ORIGINS env var causes startup failure when set in host shell
The `list[str]` pydantic-settings field for `cors_origins` expects JSON (`["...","..."]`). In the host shell, the `.env` value `CORS_ORIGINS=["..."]` may be bash-glob-expanded, causing `JSONDecodeError`. Inside the Docker container there is no `CORS_ORIGINS` env var set, so restart is safe. Only fails when launching uvicorn manually from the host shell with the env loaded.

## 2026-05-19 — Docker build fails in this Proxmox LXC (AppArmor)
All Docker `RUN` steps fail with AppArmor profile errors. Root cause: the LXC container doesn't have AppArmor kernel support but Docker tries to load its default profile. Fix requires the Proxmox host to add `lxc.apparmor.profile = unconfined` to the LXC config (`/etc/pve/lxc/CTID.conf`) and restart the container. Workaround: run the backend directly via `.venv/bin/uvicorn` — the frontend is pre-built in `backend/static/`.
