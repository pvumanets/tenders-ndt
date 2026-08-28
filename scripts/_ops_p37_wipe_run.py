"""037 ops: wipe, RT start, short host-side status poll (no long buffered exec)."""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import paramiko

ROOT = Path(__file__).resolve().parents[1]
PRIVKEY = Path.home() / ".ssh" / "id_ed25519_tenders_ndt_vps"

_STATUS_PY = r"""
import json, os, urllib.request
BASE='http://127.0.0.1:8765'
u=os.environ['SCOUT_DIGITAL_USERNAME']; p=os.environ['SCOUT_DIGITAL_PASSWORD']
SESSION=''
def call(m,path,body=None):
    global SESSION
    data=None if body is None else json.dumps(body).encode()
    h={}
    if body is not None: h['Content-Type']='application/json'
    if SESSION: h['Cookie']=SESSION
    req=urllib.request.Request(BASE+path,data=data,method=m,headers=h)
    with urllib.request.urlopen(req,timeout=60) as resp:
        raw=resp.read().decode()
        for k,v in resp.headers.items():
            if k.lower()=='set-cookie' and v.startswith('scout_session='):
                SESSION=v.split(';',1)[0]
        return json.loads(raw) if raw else {}
call('POST','/api/auth/login',{'username':u,'password':p})
st=call('GET','/api/status')
print(json.dumps({
    'running':st.get('running'),'phase':st.get('phase'),
    'qi':st.get('queue_index'),'qt':st.get('queue_total'),
    'session':st.get('session'),'counters':st.get('counters'),
    'report':st.get('run_report'),
},ensure_ascii=False))
"""

_START_PY = r"""
import json, os, urllib.request
BASE='http://127.0.0.1:8765'
u=os.environ['SCOUT_DIGITAL_USERNAME']; p=os.environ['SCOUT_DIGITAL_PASSWORD']
SESSION=''
def call(m,path,body=None):
    global SESSION
    data=None if body is None else json.dumps(body).encode()
    h={}
    if body is not None: h['Content-Type']='application/json'
    if SESSION: h['Cookie']=SESSION
    req=urllib.request.Request(BASE+path,data=data,method=m,headers=h)
    with urllib.request.urlopen(req,timeout=60) as resp:
        raw=resp.read().decode()
        for k,v in resp.headers.items():
            if k.lower()=='set-cookie' and v.startswith('scout_session='):
                SESSION=v.split(';',1)[0]
        return json.loads(raw) if raw else {}
call('POST','/api/auth/login',{'username':u,'password':p})
st=call('GET','/api/status')
if st.get('running'):
    print('already_running')
else:
    call('POST','/api/run/start',{})
    print('started')
"""


def _load_env() -> dict[str, str]:
    out: dict[str, str] = {}
    for raw in (ROOT / ".env.vps").read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        out[k.strip()] = v.strip().strip('"').strip("'")
    return out


def _connect() -> paramiko.SSHClient:
    env = _load_env()
    key = paramiko.Ed25519Key.from_private_key_file(str(PRIVKEY))
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(env.get("SCOUT_VPS_HOST") or "77.91.94.111", username="root", pkey=key, timeout=30)
    return client


def _run(client: paramiko.SSHClient, cmd: str, timeout: int = 120) -> tuple[int, str]:
    _i, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode(errors="replace")
    err = stderr.read().decode(errors="replace")
    code = stdout.channel.recv_exit_status()
    if err and "Copied" not in err and "level=warning" not in err.lower():
        print("ERR:", err[:400], file=sys.stderr, flush=True)
    return code, out


def _upload_run(client: paramiko.SSHClient, remote: str, body: str) -> None:
    sftp = client.open_sftp()
    with sftp.file(remote, "w") as fh:
        fh.write(body)
    sftp.close()
    base = "cd /opt/tenders-ndt && "
    _run(client, f"{base}docker compose cp {remote} api:{remote}", timeout=60)


def prep(client: paramiko.SSHClient) -> None:
    base = "cd /opt/tenders-ndt && "
    _run(
        client,
        base
        + "docker compose exec -T db psql -U scout -d scout -c "
        + "\"UPDATE searches SET in_queue=false WHERE platform_id='tender-pro';\"",
    )
    _run(
        client,
        base
        + "docker compose exec -T db psql -U scout -d scout -c "
        + "\"TRUNCATE TABLE documents, lot_state, lots RESTART IDENTITY CASCADE;\"",
    )
    _run(
        client,
        base
        + "docker compose exec -T api sh -c "
        + "'find /data/docs -mindepth 1 -maxdepth 1 -exec rm -rf {} +; echo docs_cleared'",
    )


def start_run(client: paramiko.SSHClient) -> None:
    remote = "/tmp/scout_p37_start.py"
    _upload_run(client, remote, _START_PY)
    code, out = _run(client, f"cd /opt/tenders-ndt && docker compose exec -T api python -u {remote}", timeout=90)
    print(out.strip(), flush=True)
    if code != 0:
        raise SystemExit(code)


def poll_until_idle(client: paramiko.SSHClient, *, interval_s: int = 15, max_s: int = 3600) -> dict:
    remote = "/tmp/scout_p37_status.py"
    _upload_run(client, remote, _STATUS_PY)
    cmd = f"cd /opt/tenders-ndt && docker compose exec -T api python -u {remote}"
    deadline = time.time() + max_s
    last: dict = {}
    while time.time() < deadline:
        code, out = _run(client, cmd, timeout=90)
        line = out.strip().splitlines()[-1] if out.strip() else ""
        if not line:
            print("poll empty", flush=True)
            time.sleep(interval_s)
            continue
        try:
            last = json.loads(line)
        except json.JSONDecodeError:
            print("poll raw", line[:200], flush=True)
            time.sleep(interval_s)
            continue
        print(
            f"poll running={last.get('running')} phase={last.get('phase')} "
            f"q={last.get('qi')}/{last.get('qt')} L1={(last.get('counters') or {}).get('L1')} "
            f"session={last.get('session')}",
            flush=True,
        )
        if not last.get("running"):
            return last
        time.sleep(interval_s)
    raise SystemExit("poll timeout")


def sanity(client: paramiko.SSHClient) -> None:
    base = "cd /opt/tenders-ndt && "
    checks = [
        "SELECT tier, count(*) FROM lots GROUP BY 1 ORDER BY 1;",
        "SELECT count(*) AS bad FROM lots WHERE tier='L1' AND (title ILIKE '%расходн%' OR title ILIKE '%дефектоскоп%' OR title ILIKE '%поверк%');",
        "SELECT count(*) AS l1, count(*) FILTER (WHERE customer_name IS NOT NULL AND btrim(customer_name)<>'') AS cust FROM lots WHERE tier='L1';",
    ]
    for sql in checks:
        code, out = _run(
            client,
            base + f"docker compose exec -T db psql -U scout -d scout -c \"{sql}\"",
            timeout=60,
        )
        print(out, flush=True)
        if code != 0:
            raise SystemExit(code)


def main() -> None:
    step = (sys.argv[1] if len(sys.argv) > 1 else "all").strip()
    client = _connect()
    try:
        if step in ("all", "prep"):
            print("=== prep", flush=True)
            prep(client)
        if step in ("all", "start"):
            print("=== start", flush=True)
            start_run(client)
        if step in ("all", "poll"):
            print("=== poll", flush=True)
            final = poll_until_idle(client)
            print("final", json.dumps(final, ensure_ascii=False), flush=True)
        if step in ("all", "sanity"):
            print("=== sanity", flush=True)
            sanity(client)
    finally:
        client.close()
    print("done", flush=True)


if __name__ == "__main__":
    main()
