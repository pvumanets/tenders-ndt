"""First-time VPS: SSH pubkey, Docker, clone GitHub, compose on loopback.

Reads host/user/password from local gitignored `.env.vps`. Never prints secrets.
PasswordAuthentication stays yes. Does not expose :8765/:5433 on 0.0.0.0.
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

import paramiko

ROOT = Path(__file__).resolve().parents[1]
ENV_VPS = ROOT / ".env.vps"
APP_ENV = ROOT / ".env"
PUBKEY = Path.home() / ".ssh" / "id_ed25519_tenders_ndt_vps.pub"
PRIVKEY = Path.home() / ".ssh" / "id_ed25519_tenders_ndt_vps"
REMOTE_DIR = "/opt/tenders-ndt"
GITHUB = "https://github.com/pvumanets/tenders-ndt.git"
COPY_ENV_KEYS = (
    "POSTGRES_USER",
    "POSTGRES_PASSWORD",
    "POSTGRES_DB",
    "SCOUT_DIGITAL_USERNAME",
    "SCOUT_DIGITAL_PASSWORD",
    "SCOUT_DIGITAL_DISPLAY",
    "SCOUT_DIRECTOR_USERNAME",
    "SCOUT_DIRECTOR_PASSWORD",
    "SCOUT_DIRECTOR_DISPLAY",
    "DOWNLOAD_DOCS",
    "SCOUT_LEGACY_HTML",
    "ROSTENDER_BASE_URL",
    "ROSTENDER_USER",
    "ROSTENDER_PASSWORD",
    "SIBUR_COOKIES_FILE",
    "ONLINECONTRACT_COOKIES_FILE",
    "ONLINECONTRACT_USER",
    "ONLINECONTRACT_PASSWORD",
    "TENDER_PRO_COOKIES_FILE",
)
SKIP_ENV_PREFIXES = ("SCOUT_VPS_",)
COOKIE_GLOBS = ("cookies*.txt",)
HOST_PUBLIC = "tenders.ndtexam.ru"
HOST_IP = "77.91.94.111"


def _load_dotenv(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, val = line.split("=", 1)
        out[key.strip()] = val.strip().strip('"').strip("'")
    return out


def _expand(path: str) -> str:
    return os.path.expanduser(path.replace("/", os.sep) if os.name == "nt" else path)


def _ssh(host: str, user: str, *, password: str | None = None, key: Path | None = None) -> paramiko.SSHClient:
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    kwargs: dict = {"hostname": host, "username": user, "timeout": 45, "allow_agent": False, "look_for_keys": False}
    if key is not None:
        kwargs["pkey"] = paramiko.Ed25519Key.from_private_key_file(str(key))
    else:
        kwargs["password"] = password
    client.connect(**kwargs)
    return client


def _run(client: paramiko.SSHClient, cmd: str, *, timeout: int = 120) -> tuple[int, str, str]:
    stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode("utf-8", errors="replace")
    err = stderr.read().decode("utf-8", errors="replace")
    code = stdout.channel.recv_exit_status()
    return code, out, err


def _must(client: paramiko.SSHClient, cmd: str, *, timeout: int = 120) -> str:
    code, out, err = _run(client, cmd, timeout=timeout)
    if code != 0:
        raise SystemExit(f"remote failed ({code}): {cmd}\n{err or out}")
    return out


def _sftp_put(client: paramiko.SSHClient, local: Path, remote: str) -> None:
    sftp = client.open_sftp()
    sftp.put(str(local), remote)
    sftp.close()


def _sftp_write(client: paramiko.SSHClient, remote: str, data: str) -> None:
    sftp = client.open_sftp()
    with sftp.file(remote, "w") as fh:
        fh.write(data)
    sftp.close()


def _install_pubkey(client: paramiko.SSHClient, pub: str) -> None:
    _must(client, "mkdir -p /root/.ssh && chmod 700 /root/.ssh")
    # idempotent append
    escaped = pub.replace("'", "'\"'\"'")
    _must(
        client,
        "touch /root/.ssh/authorized_keys && chmod 600 /root/.ssh/authorized_keys && "
        f"grep -qxF '{escaped}' /root/.ssh/authorized_keys || echo '{escaped}' >> /root/.ssh/authorized_keys",
    )
    # Keep password login. Enable pubkey.
    _must(
        client,
        "python3 - <<'PY'\n"
        "from pathlib import Path\n"
        "p = Path('/etc/ssh/sshd_config')\n"
        "text = p.read_text(encoding='utf-8', errors='replace')\n"
        "lines = []\n"
        "seen_pw = seen_pub = False\n"
        "for line in text.splitlines():\n"
        "    s = line.strip()\n"
        "    if s.lower().startswith('passwordauthentication'):\n"
        "        lines.append('PasswordAuthentication yes')\n"
        "        seen_pw = True\n"
        "        continue\n"
        "    if s.lower().startswith('pubkeyauthentication'):\n"
        "        lines.append('PubkeyAuthentication yes')\n"
        "        seen_pub = True\n"
        "        continue\n"
        "    lines.append(line)\n"
        "if not seen_pw:\n"
        "    lines.append('PasswordAuthentication yes')\n"
        "if not seen_pub:\n"
        "    lines.append('PubkeyAuthentication yes')\n"
        "p.write_text('\\n'.join(lines) + '\\n', encoding='utf-8')\n"
        "PY",
    )
    _run(client, "systemctl reload sshd || systemctl reload ssh || true")


def _ensure_docker(client: paramiko.SSHClient) -> None:
    code, _, _ = _run(client, "docker compose version")
    if code == 0:
        print("docker: already present")
        return
    print("docker: installing (get.docker.com)")
    _must(client, "curl -fsSL https://get.docker.com | sh", timeout=600)
    _run(client, "systemctl enable --now docker")


def _app_env_text(src: dict[str, str]) -> str:
    missing = [k for k in ("POSTGRES_PASSWORD", "SCOUT_DIGITAL_PASSWORD", "SCOUT_DIRECTOR_PASSWORD") if not src.get(k)]
    if missing:
        raise SystemExit(f"local .env missing required keys: {', '.join(missing)}")
    lines = ["# Generated on VPS by scripts/vps-bootstrap.py. Not in git."]
    for key in COPY_ENV_KEYS:
        if any(key.startswith(p) for p in SKIP_ENV_PREFIXES):
            continue
        if key not in src:
            continue
        lines.append(f"{key}={src[key]}")
    lines.append("SCOUT_COOKIE_SECURE=1")
    lines.append("ROSTENDER_COOKIES_FILE=./cookies.rostender.txt")
    lines.append("")
    return "\n".join(lines)


def _sync_cookies(client: paramiko.SSHClient) -> list[str]:
    copied: list[str] = []
    for pattern in COOKIE_GLOBS:
        for path in sorted(ROOT.glob(pattern)):
            if not path.is_file():
                continue
            _sftp_put(client, path, f"{REMOTE_DIR}/{path.name}")
            copied.append(path.name)
            size = path.stat().st_size
            print(f"cookies: {path.name} bytes={size}")
    if "cookies.rostender.txt" not in copied:
        _must(client, f"test -f {REMOTE_DIR}/cookies.rostender.txt || : > {REMOTE_DIR}/cookies.rostender.txt")
        print("cookies: cookies.rostender.txt missing locally — empty placeholder on VPS")
    return copied


def _ensure_ufw(client: paramiko.SSHClient) -> None:
    code, _, _ = _run(client, "command -v ufw")
    if code != 0:
        print("ufw: not installed, skip")
        return
    _run(client, "ufw allow OpenSSH || ufw allow 22/tcp")
    _run(client, "ufw allow 80/tcp && ufw allow 443/tcp && ufw allow 443/udp")
    _run(client, "ufw --force enable || true")
    print("ufw: 22/80/443 allowed")


def _wait_dns(client: paramiko.SSHClient) -> None:
    print(f"dns: waiting {HOST_PUBLIC} -> {HOST_IP}")
    for _ in range(36):
        code, out, err = _run(
            client,
            f"getent hosts {HOST_PUBLIC} || python3 -c \"import socket; print(socket.gethostbyname('{HOST_PUBLIC}'))\"",
            timeout=20,
        )
        text = (out or err).strip()
        if HOST_IP in text:
            print(f"dns: {text.splitlines()[0]}")
            return
        time.sleep(5)
    raise SystemExit(f"dns: {HOST_PUBLIC} does not resolve to {HOST_IP} yet")


def _sync_prod_files(client: paramiko.SSHClient) -> None:
    _must(client, f"mkdir -p {REMOTE_DIR}/runs")
    _sftp_write(client, f"{REMOTE_DIR}/.env", _app_env_text(_load_dotenv(APP_ENV)))
    _sync_cookies(client)
    _sftp_put(client, ROOT / "docker-compose.prod.yml", f"{REMOTE_DIR}/docker-compose.prod.yml")
    _sftp_put(client, ROOT / "Caddyfile", f"{REMOTE_DIR}/Caddyfile")
    print("files: .env, cookies, compose, Caddyfile")


def _wait_local_health(client: paramiko.SSHClient) -> None:
    print("health: waiting loopback")
    health = ""
    for _ in range(36):
        time.sleep(5)
        _, out, err = _run(client, "curl -fsS http://127.0.0.1:8765/api/health || true", timeout=20)
        health = (out or err).strip()
        if '"db":"ok"' in health or '"db": "ok"' in health:
            print(f"health: {health}")
            return
    logs = _run(client, f"cd {REMOTE_DIR} && docker compose -f docker-compose.prod.yml logs --tail 80", timeout=60)
    print(logs[1] or logs[2])
    raise SystemExit(f"health not ok: {health or '(empty)'}")


def _wait_https(client: paramiko.SSHClient) -> None:
    print(f"https: waiting https://{HOST_PUBLIC}/api/health")
    last = ""
    for _ in range(36):
        time.sleep(5)
        _, out, err = _run(
            client,
            f"curl -fsS https://{HOST_PUBLIC}/api/health || true",
            timeout=30,
        )
        last = (out or err).strip()
        if '"db":"ok"' in last or '"db": "ok"' in last:
            print(f"https: {last}")
            return
    logs = _run(client, f"cd {REMOTE_DIR} && docker compose -f docker-compose.prod.yml logs caddy --tail 80", timeout=60)
    print(logs[1] or logs[2])
    raise SystemExit(f"https not ok: {last or '(empty)'}")


def sync_p7() -> None:
    """Key-only: sync secrets, Caddy, TLS. Server must already have Docker + clone."""
    if not APP_ENV.is_file():
        raise SystemExit("missing local .env")
    if not PRIVKEY.is_file():
        raise SystemExit("missing ~/.ssh/id_ed25519_tenders_ndt_vps")
    vps = _load_dotenv(ENV_VPS) if ENV_VPS.is_file() else {}
    host = vps.get("SCOUT_VPS_HOST") or HOST_IP
    user = vps.get("SCOUT_VPS_USER") or "root"
    print(f"ssh: key {user}@{host}")
    client = _ssh(host, user, key=PRIVKEY)
    try:
        print("remote:", _must(client, "hostname").strip())
        _sync_prod_files(client)
        _ensure_ufw(client)
        _wait_dns(client)
        print("compose: up (Caddy + api Secure=1)")
        _must(
            client,
            f"cd {REMOTE_DIR} && docker compose -f docker-compose.prod.yml up -d",
            timeout=300,
        )
        _wait_local_health(client)
        _wait_https(client)
        listen = _run(client, "ss -lnt | grep -E ':8765|:5433|:80|:443' || true")[1]
        print("listen:\n" + (listen.strip() or "(none)"))
    finally:
        client.close()
    print(f"done: https://{HOST_PUBLIC}/")


def main() -> None:
    if not ENV_VPS.is_file():
        raise SystemExit("missing .env.vps (gitignored). See docs/delivery/vps.md")
    if not APP_ENV.is_file():
        raise SystemExit("missing local .env with Scout/Postgres values")
    if not PUBKEY.is_file() or not PRIVKEY.is_file():
        raise SystemExit("missing ~/.ssh/id_ed25519_tenders_ndt_vps")

    vps = _load_dotenv(ENV_VPS)
    host = vps.get("SCOUT_VPS_HOST") or ""
    user = vps.get("SCOUT_VPS_USER") or "root"
    password = vps.get("SCOUT_VPS_PASSWORD") or ""
    if not host or not password:
        raise SystemExit(".env.vps needs SCOUT_VPS_HOST and SCOUT_VPS_PASSWORD")

    pub = PUBKEY.read_text(encoding="utf-8").strip()
    print(f"ssh: connecting {user}@{host} (password, first time)")
    client = _ssh(host, user, password=password)
    try:
        uname = _must(client, "uname -a").strip()
        print(f"remote: {uname}")
        _install_pubkey(client, pub)
        print("ssh: pubkey installed; PasswordAuthentication remains yes")
    finally:
        client.close()

    print("ssh: verifying key login")
    client = _ssh(host, user, key=PRIVKEY)
    try:
        _ensure_docker(client)
        _must(client, f"mkdir -p {REMOTE_DIR}")
        code, _, _ = _run(client, f"test -d {REMOTE_DIR}/.git")
        if code != 0:
            print("git: clone origin")
            _must(client, f"git clone {GITHUB} {REMOTE_DIR}", timeout=180)
        else:
            print("git: pull origin main")
            _must(client, f"git -C {REMOTE_DIR} fetch origin && git -C {REMOTE_DIR} checkout main && git -C {REMOTE_DIR} pull --ff-only origin main")

        print("files: app .env, cookies, prod compose, Caddyfile")
        _sync_prod_files(client)
        _ensure_ufw(client)

        print("compose: build and up")
        _must(
            client,
            f"cd {REMOTE_DIR} && docker compose -f docker-compose.prod.yml up -d --build",
            timeout=900,
        )
        _wait_local_health(client)

        pub_8765 = _run(client, "ss -lnt | grep -E ':8765|:5433|:80|:443' || true")[1]
        print("listen:\n" + (pub_8765.strip() or "(none)"))
    finally:
        client.close()
    print(f"done: https://{HOST_PUBLIC}/")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--sync", action="store_true", help="P7: key login, secrets, Caddy, TLS")
    args = parser.parse_args()
    if args.sync:
        sync_p7()
    else:
        main()
