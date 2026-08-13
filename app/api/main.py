"""FastAPI operator UI — P5.5 inbox + docs download from volume, Scout session."""
from __future__ import annotations

import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query, Request, Response
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from starlette.middleware.base import BaseHTTPMiddleware

from app.api import auth, inbox, results, runner
from app.api.state import STATE
from app.db.bootstrap import bootstrap_users
from app.db.session import ping_db

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"
_REPO_ROOT = Path(__file__).resolve().parents[2]


def _web_dist() -> Path:
    env = os.environ.get("SCOUT_WEB_DIST", "").strip()
    candidates: list[Path] = []
    if env:
        candidates.append(Path(env))
    candidates.extend((Path("/app/web-dist"), _REPO_ROOT / "app" / "web" / "dist"))
    for path in candidates:
        if (path / "index.html").is_file():
            return path
    return candidates[0]


def _legacy_enabled() -> bool:
    return os.environ.get("SCOUT_LEGACY_HTML", "1").strip().lower() not in {
        "0",
        "false",
        "no",
    }


@asynccontextmanager
async def lifespan(_app: FastAPI):
    runner.refresh_session()
    bootstrap_users()
    yield


app = FastAPI(title="ndt-tender-scout", version="0.5.5", lifespan=lifespan)


class StartBody(BaseModel):
    limit: int = Field(default=1000, ge=1, le=1000)
    query: str = Field(default="неразрушающий", min_length=1)


class LoginBody(BaseModel):
    username: str = Field(min_length=1)
    password: str = Field(min_length=1)


class ScoutSessionMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if auth.is_public_api(request.method, request.url.path):
            return await call_next(request)
        try:
            principal = auth.resolve_principal(request)
        except RuntimeError:
            return JSONResponse({"detail": "unauthorized"}, status_code=401)
        if principal is None:
            return JSONResponse({"detail": "unauthorized"}, status_code=401)
        request.state.scout_user = principal
        return await call_next(request)


app.add_middleware(ScoutSessionMiddleware)


@app.post("/api/auth/login")
def api_login(body: LoginBody, response: Response):
    try:
        user = auth.authenticate(body.username.strip(), body.password)
    except RuntimeError:
        raise HTTPException(status_code=401, detail="invalid_credentials") from None
    if user is None:
        auth.login_failed_log()
        raise HTTPException(status_code=401, detail="invalid_credentials")
    token = auth.create_session(user.id)
    auth.set_session_cookie(response, token)
    auth.login_ok_log()
    return {"ok": True}


@app.post("/api/auth/logout", status_code=204)
def api_logout(request: Request, response: Response) -> None:
    try:
        auth.destroy_session(request)
    except RuntimeError:
        pass
    auth.clear_session_cookie(response)


@app.get("/api/me")
def api_me(request: Request):
    principal = getattr(request.state, "scout_user", None)
    if principal is None:
        raise HTTPException(status_code=401, detail="unauthorized")
    return {"username": principal.username, "display_name": principal.display_name}


@app.get("/api/health")
def api_health():
    db_ok = ping_db()
    body = {"ok": db_ok, "db": "ok" if db_ok else "down"}
    if not db_ok:
        return JSONResponse(body, status_code=503)
    return body


@app.get("/api/status")
def api_status():
    runner.refresh_session()
    return STATE.snapshot()


@app.post("/api/run/start")
def api_start(body: StartBody | None = None):
    body = body or StartBody()
    if STATE.snapshot()["running"]:
        raise HTTPException(status_code=409, detail="already_running")
    try:
        runner.start_run(limit=body.limit, query=body.query)
    except RuntimeError as e:
        if str(e) == "missing_cookies":
            raise HTTPException(status_code=400, detail="missing_cookies") from e
        if str(e) == "already_running":
            raise HTTPException(status_code=409, detail="already_running") from e
        raise HTTPException(status_code=400, detail=str(e)) from e
    return {"ok": True, "status": STATE.snapshot()}


@app.post("/api/run/stop")
def api_stop():
    runner.request_stop()
    return {"ok": True, "status": STATE.snapshot()}


def _inbox_http(exc: Exception) -> None:
    if isinstance(exc, inbox.InboxQueryError):
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if isinstance(exc, inbox.InboxNotFound):
        raise HTTPException(status_code=404, detail="not_found") from exc
    if isinstance(exc, RuntimeError) and str(exc) == "database_unconfigured":
        raise HTTPException(status_code=503, detail="db_down") from exc
    raise exc


@app.get("/api/inbox")
def api_inbox(
    unread: str | None = Query(default=None),
    tier: str = Query(default="fit"),
    q: str = Query(default=""),
    deadline_from: str | None = Query(default=None),
    deadline_to: str | None = Query(default=None),
    ingested_from: str | None = Query(default=None),
    ingested_to: str | None = Query(default=None),
):
    try:
        return inbox.list_inbox(
            unread=unread,
            tier=tier,
            q=q,
            deadline_from=deadline_from,
            deadline_to=deadline_to,
            ingested_from=ingested_from,
            ingested_to=ingested_to,
        )
    except (inbox.InboxQueryError, inbox.InboxNotFound, RuntimeError) as exc:
        _inbox_http(exc)


@app.get("/api/inbox/{tender_id}")
def api_inbox_one(tender_id: str):
    try:
        return inbox.get_inbox_item(tender_id)
    except (inbox.InboxQueryError, inbox.InboxNotFound, RuntimeError) as exc:
        _inbox_http(exc)


@app.put("/api/inbox/{tender_id}/viewed")
def api_inbox_viewed(tender_id: str, body: dict):
    try:
        return inbox.set_viewed(tender_id, body)
    except (inbox.InboxQueryError, inbox.InboxNotFound, RuntimeError) as exc:
        _inbox_http(exc)


@app.put("/api/inbox/{tender_id}/priority")
def api_inbox_priority(tender_id: str, body: dict):
    try:
        return inbox.set_priority(tender_id, body)
    except (inbox.InboxQueryError, inbox.InboxNotFound, RuntimeError) as exc:
        _inbox_http(exc)


@app.get("/api/inbox/{tender_id}/documents")
def api_inbox_documents(tender_id: str):
    try:
        return inbox.list_documents(tender_id)
    except (inbox.InboxQueryError, inbox.InboxNotFound, RuntimeError) as exc:
        _inbox_http(exc)


@app.get("/api/inbox/{tender_id}/documents/{filename}")
def api_inbox_document_file(tender_id: str, filename: str):
    try:
        path = inbox.download_document(tender_id, filename)
    except (inbox.InboxQueryError, inbox.InboxNotFound, RuntimeError) as exc:
        _inbox_http(exc)
        return
    return FileResponse(path, filename=filename, media_type="application/octet-stream")


@app.get("/api/results")
def api_results(
    tier: str = Query(default="fit", description="L1|L2|L3|fit|all"),
    q: str = Query(default="", description="search title/customer/location"),
    run_dir: str | None = Query(default=None),
):
    return results.list_results(tier=tier, q=q, run_dir=run_dir)


@app.get("/api/results/{tender_id}")
def api_result_one(tender_id: str, run_dir: str | None = Query(default=None)):
    found = results.get_result(tender_id, run_dir=run_dir)
    if found is None:
        raise HTTPException(status_code=404, detail="not_found")
    return found


@app.get("/legacy")
def legacy_index():
    if not _legacy_enabled():
        raise HTTPException(status_code=404, detail="legacy_disabled")
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/")
def index():
    dist_index = _web_dist() / "index.html"
    if dist_index.is_file():
        return FileResponse(dist_index)
    return FileResponse(STATIC_DIR / "index.html")


app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

_dist = _web_dist()
_assets = _dist / "assets"
if _assets.is_dir():
    app.mount("/assets", StaticFiles(directory=str(_assets)), name="spa-assets")
_platforms = _dist / "platforms"
if _platforms.is_dir():
    app.mount("/platforms", StaticFiles(directory=str(_platforms)), name="spa-platforms")
