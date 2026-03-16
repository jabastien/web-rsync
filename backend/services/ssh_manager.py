import logging
import os
import stat
from pathlib import Path

import paramiko

from ..config import settings

logger = logging.getLogger(__name__)

KEY_PATH = settings.ssh_dir / "id_rsa"
PUB_PATH = settings.ssh_dir / "id_rsa.pub"


def ensure_ssh_key():
    settings.ssh_dir.mkdir(parents=True, exist_ok=True)
    if not KEY_PATH.exists():
        logger.info("Generating RSA key pair at %s", KEY_PATH)
        key = paramiko.RSAKey.generate(4096)
        key.write_private_key_file(str(KEY_PATH))
        with open(PUB_PATH, "w") as f:
            f.write(f"{key.get_name()} {key.get_base64()}\n")

    current_mode = os.stat(KEY_PATH).st_mode
    if current_mode & 0o077:
        os.chmod(KEY_PATH, stat.S_IRUSR | stat.S_IWUSR)
        logger.warning("Fixed permissions on %s (was %o)", KEY_PATH, current_mode & 0o777)


def get_public_key() -> str:
    if PUB_PATH.exists():
        return PUB_PATH.read_text().strip()
    return ""


def list_ssh_keys() -> list[dict]:
    keys = []
    if PUB_PATH.exists():
        keys.append({"name": "id_rsa", "public_key": PUB_PATH.read_text().strip()})
    return keys


def deploy_key(hostname: str, port: int, username: str, password: str) -> None:
    pub_key = get_public_key()
    if not pub_key:
        raise ValueError("No public key available — generate one first")

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(hostname, port=port, username=username, password=password, timeout=10)
        stdin, stdout, stderr = client.exec_command(
            "mkdir -p ~/.ssh && chmod 700 ~/.ssh && "
            f"echo {pub_key!r} >> ~/.ssh/authorized_keys && "
            "chmod 600 ~/.ssh/authorized_keys"
        )
        exit_code = stdout.channel.recv_exit_status()
        if exit_code != 0:
            err = stderr.read().decode()
            raise RuntimeError(f"Remote command failed (exit {exit_code}): {err}")
    finally:
        client.close()
