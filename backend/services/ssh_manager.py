import logging
import os
import stat
import subprocess
from pathlib import Path

import paramiko

from ..config import settings

logger = logging.getLogger(__name__)

KEY_PATH = settings.ssh_dir / "id_ed25519"
PUB_PATH = settings.ssh_dir / "id_ed25519.pub"
_LEGACY_KEY = settings.ssh_dir / "id_rsa"

_agent_pid: int | None = None


def ensure_ssh_agent() -> None:
    """Start ssh-agent and load the managed key into it.

    Sets SSH_AUTH_SOCK + SSH_AGENT_PID in the process environment so all
    child processes (including rsync's ssh transport) inherit the agent.
    Required for remote→remote sync: the agent is forwarded via ssh -A to
    the source host, allowing rsync there to authenticate to the destination.
    """
    global _agent_pid

    # Reuse an already-running agent if the socket is still live
    existing_sock = os.environ.get("SSH_AUTH_SOCK")
    if existing_sock and Path(existing_sock).exists() and _agent_pid:
        return

    try:
        result = subprocess.run(
            ["ssh-agent", "-s"], capture_output=True, text=True, check=True
        )
        for line in result.stdout.splitlines():
            if "=" in line and ";" in line:
                kv = line.split(";")[0].strip()
                k, _, v = kv.partition("=")
                os.environ[k.strip()] = v.strip()
                if k.strip() == "SSH_AGENT_PID":
                    _agent_pid = int(v.strip())

        subprocess.run(["ssh-add", str(KEY_PATH)], check=True, capture_output=True)
        logger.info("SSH agent started (PID %d) and key loaded", _agent_pid or 0)
    except Exception as e:
        logger.warning("Could not start SSH agent (remote→remote sync unavailable): %s", e)


def stop_ssh_agent() -> None:
    """Kill the ssh-agent started by ensure_ssh_agent."""
    global _agent_pid
    if _agent_pid:
        try:
            subprocess.run(["kill", str(_agent_pid)], check=True, capture_output=True)
            logger.info("SSH agent stopped (PID %d)", _agent_pid)
        except Exception:
            pass
        _agent_pid = None
        os.environ.pop("SSH_AUTH_SOCK", None)
        os.environ.pop("SSH_AGENT_PID", None)


def ensure_ssh_key():
    settings.ssh_dir.mkdir(parents=True, exist_ok=True)
    if _LEGACY_KEY.exists() and not KEY_PATH.exists():
        logger.warning(
            "Legacy RSA key found at %s but no Ed25519 key exists. "
            "Delete data/ssh/id_rsa* and restart to generate an Ed25519 key.",
            _LEGACY_KEY,
        )
    if not KEY_PATH.exists():
        logger.info("Generating Ed25519 key pair at %s", KEY_PATH)
        key = paramiko.Ed25519Key.generate()
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
        keys.append({"name": "id_ed25519", "public_key": PUB_PATH.read_text().strip()})
    return keys


def deploy_key(hostname: str, port: int, username: str, password: str) -> None:
    pub_key = get_public_key()
    if not pub_key:
        raise ValueError("No public key available — generate one first")

    client = paramiko.SSHClient()
    # WarningPolicy logs unknown hosts; AutoAddPolicy would silently trust any host key (MITM risk).
    # A pre-populated known_hosts file (RejectPolicy) would be fully secure.
    client.set_missing_host_key_policy(paramiko.WarningPolicy())
    try:
        client.connect(hostname, port=port, username=username, password=password, timeout=10)

        _, stdout, stderr = client.exec_command("mkdir -p ~/.ssh && chmod 700 ~/.ssh")
        if stdout.channel.recv_exit_status() != 0:
            raise RuntimeError(f"Failed to create ~/.ssh: {stderr.read().decode()}")

        # Resolve home directory — SFTP paths don't expand ~
        _, home_out, _ = client.exec_command("echo $HOME")
        home = home_out.read().decode().strip()
        if not home:
            raise RuntimeError("Could not determine remote home directory")
        auth_path = f"{home}/.ssh/authorized_keys"

        # Use SFTP to write the key — avoids shell quoting issues entirely
        sftp = client.open_sftp()
        try:
            try:
                with sftp.open(auth_path, "r") as f:
                    existing = f.read().decode(errors="replace")
            except IOError:
                existing = ""
            if pub_key not in existing:
                with sftp.open(auth_path, "a") as f:
                    f.write((pub_key + "\n").encode())
            sftp.chmod(auth_path, 0o600)
        finally:
            sftp.close()
    finally:
        client.close()
