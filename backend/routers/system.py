from fastapi import APIRouter
from ..services.scheduler import list_jobs

router = APIRouter(prefix="/api/system", tags=["system"])

_SKIP_FSTYPES = {
    "proc", "sysfs", "devtmpfs", "devpts", "tmpfs", "cgroup", "cgroup2",
    "mqueue", "hugetlbfs", "debugfs", "tracefs", "pstore", "bpf",
    "securityfs", "fusectl", "configfs", "overlay", "aufs",
}
_SKIP_PREFIXES = ("/proc", "/sys", "/dev")


@router.get("/health")
def health():
    return {"status": "ok"}


@router.get("/scheduler-jobs")
def scheduler_jobs():
    return list_jobs()


@router.get("/mounts")
def get_mounts():
    """Return mount points visible inside this container (volumes, bind-mounts)."""
    mounts = []
    try:
        with open("/proc/mounts") as f:
            for line in f:
                parts = line.split()
                if len(parts) < 4:
                    continue
                device, mountpoint, fstype, options = parts[0], parts[1], parts[2], parts[3]
                if fstype in _SKIP_FSTYPES:
                    continue
                if any(mountpoint.startswith(p) for p in _SKIP_PREFIXES):
                    continue
                mounts.append({
                    "mountpoint": mountpoint,
                    "device": device,
                    "fstype": fstype,
                    "access": "rw" if options.startswith("rw") else "ro",
                })
    except FileNotFoundError:
        pass
    return sorted(mounts, key=lambda m: m["mountpoint"])
