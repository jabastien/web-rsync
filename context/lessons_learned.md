# Lessons Learned

## 2026-03-15 — pydantic-settings computed fields for derived paths
Use `@computed_field` + `@property` instead of `model_post_init` for derived settings in pydantic-settings v2. The `model_post_init` approach silently fails to update fields. `computed_field` works cleanly and is the documented v2 pattern.

## 2026-03-15 — Default DATA_DIR should be relative for dev
Default `data_dir = Path("./data")` (relative) rather than `Path("/data")` (absolute). Absolute default breaks local dev when /data doesn't exist and is unwritable. Docker sets `DATA_DIR=/data` explicitly via env.

## 2026-03-15 — Node.js not installed on this machine
Node.js (`nodejs`, `npm`) is not installed. Frontend files are written but cannot be built until installed. Vue 3 + Vite requires Node 18+. Docker multi-stage build will handle this in prod.

## 2026-05-19 — uv pip install -r pyproject.toml is valid uv syntax
`uv pip install -r <pyproject.toml>` reads `[project].dependencies` directly — it is NOT wrong like pip would be. Changing it to `uv pip install -e .` breaks builds because hatchling requires a proper package structure. Only use `-e` if pyproject.toml includes `[tool.hatch.build.targets.wheel]` with the correct packages path.

## 2026-05-19 — paramiko.Ed25519Key has no generate() method
`paramiko.RSAKey`, `DSSKey`, and `ECDSAKey` have `.generate()` class methods; `Ed25519Key` does not. Use `ssh-keygen -t ed25519 -N "" -f <path>` (subprocess) to generate Ed25519 keys — `openssh-client` is already installed in the container.

## 2026-05-19 — Docker build fails in this Proxmox LXC (AppArmor)
All Docker `RUN` steps fail with AppArmor profile errors. Root cause: the LXC container doesn't have AppArmor kernel support but Docker tries to load its default profile. Fix requires the Proxmox host to add `lxc.apparmor.profile = unconfined` to the LXC config (`/etc/pve/lxc/CTID.conf`) and restart the container. Workaround: run the backend directly via `.venv/bin/uvicorn` — the frontend is pre-built in `backend/static/`.
