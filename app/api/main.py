"""FastAPI operator UI — P5.5 inbox + docs download from volume, Scout session."""
from __future__ import annotations

import asyncio
import json
import os
from contextlib import asynccontextmanager
from pathlib import Path

from uuid import UUID

from fastapi import Body, FastAPI, HTTPException, Query, Request, Response
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, ValidationError
from starlette.middleware.base import BaseHTTPMiddleware

from app.api import auth, inbox, platforms as platforms_api, results, runner, search_groups as search_groups_api
from app.api import schedule as schedule_api
from app.api import searches as searches_api
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


async def _schedule_loop() -> None:
    while True:
        await asyncio.sleep(30)
        try:
            schedule_api.tick_once()
        except Exception:  # noqa: BLE001 — ticker must not kill the api
            pass


@asynccontextmanager
async def lifespan(_app: FastAPI):
    runner.refresh_session()
    bootstrap_users()
    try:
        from app.api.search_groups import ensure_group_seeds
        from app.api.search_queue_sync import (
            sync_b2b_center_queue_from_cookies,
            sync_roseltorg_queue_from_credentials,
            sync_tender_pro_queue_from_cookies,
        )

        ensure_group_seeds()
        sync_tender_pro_queue_from_cookies()
        sync_roseltorg_queue_from_credentials()
        sync_b2b_center_queue_from_cookies()
    except Exception:  # noqa: BLE001 — startup must not die on optional sync
        pass
    task = asyncio.create_task(_schedule_loop())
    try:
        yield
    finally:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass


app = FastAPI(title="ndt-tender-scout", version="0.5.5", lifespan=lifespan)


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
    runner.refresh_session(probe_roseltorg_live=False)
    return STATE.snapshot()


@app.post("/api/run/start")
async def api_start(request: Request):
    pipeline = "manual"
    raw_bytes = await request.body()
    if raw_bytes:
        try:
            raw = json.loads(raw_bytes)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="invalid_pipeline") from None
        if isinstance(raw, dict) and raw.get("pipeline") is not None:
            pipeline = str(raw.get("pipeline"))
    if pipeline not in {"manual", "auto"}:
        raise HTTPException(status_code=400, detail="invalid_pipeline")
    if STATE.snapshot()["running"]:
        raise HTTPException(status_code=409, detail="already_running")
    try:
        runner.start_run(pipeline=pipeline)
    except RuntimeError as e:
        if str(e) == "missing_cookies":
            raise HTTPException(status_code=400, detail="missing_cookies") from e
        if str(e) == "already_running":
            raise HTTPException(status_code=409, detail="already_running") from e
        if str(e) == "empty_queue":
            raise HTTPException(status_code=400, detail="empty_queue") from e
        if str(e) == "invalid_pipeline":
            raise HTTPException(status_code=400, detail="invalid_pipeline") from e
        raise HTTPException(status_code=400, detail=str(e)) from e
    return {"ok": True, "status": STATE.snapshot()}


@app.get("/api/schedule")
def api_schedule_get():
    try:
        return schedule_api.get_schedule()
    except RuntimeError as exc:
        if str(exc) == "database_unconfigured":
            raise HTTPException(status_code=503, detail="db_down") from exc
        raise


@app.put("/api/schedule")
def api_schedule_put(body: dict | None = None):
    try:
        return schedule_api.put_schedule(body or {})
    except schedule_api.ScheduleError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        if str(exc) == "database_unconfigured":
            raise HTTPException(status_code=503, detail="db_down") from exc
        raise


@app.post("/api/run/stop")
def api_stop():
    runner.request_stop()
    return {"ok": True, "status": STATE.snapshot()}


def _search_http(exc: Exception) -> None:
    if isinstance(exc, searches_api.SearchError):
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if isinstance(exc, searches_api.SearchConflict):
        raise HTTPException(status_code=409, detail="duplicate_name") from exc
    if isinstance(exc, searches_api.SearchNotFound):
        raise HTTPException(status_code=404, detail="not_found") from exc
    if isinstance(exc, RuntimeError) and str(exc) == "database_unconfigured":
        raise HTTPException(status_code=503, detail="db_down") from exc
    raise exc


def _parse_search_body(body: dict) -> searches_api.SearchIn:
    try:
        return searches_api.SearchIn.model_validate(body)
    except ValidationError as exc:
        raise HTTPException(status_code=400, detail="invalid_search") from exc


def _parse_group_body(body: dict) -> search_groups_api.SearchGroupIn:
    try:
        return search_groups_api.SearchGroupIn.model_validate(body)
    except ValidationError as exc:
        raise HTTPException(status_code=400, detail="invalid_search_group") from exc


def _group_http(exc: Exception) -> None:
    if isinstance(exc, search_groups_api.SearchGroupError):
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if isinstance(exc, search_groups_api.SearchGroupConflict):
        raise HTTPException(status_code=409, detail="duplicate_name") from exc
    if isinstance(exc, search_groups_api.SearchGroupNotFound):
        raise HTTPException(status_code=404, detail="not_found") from exc
    if isinstance(exc, RuntimeError) and str(exc) == "database_unconfigured":
        raise HTTPException(status_code=503, detail="db_down") from exc
    raise exc


@app.get("/api/searches")
def api_searches_list():
    try:
        return searches_api.list_searches()
    except RuntimeError as exc:
        _search_http(exc)


@app.post("/api/searches")
def api_searches_create(body: dict):
    try:
        return searches_api.create_search(_parse_search_body(body))
    except (searches_api.SearchError, searches_api.SearchConflict, RuntimeError) as exc:
        _search_http(exc)


@app.put("/api/searches/{search_id}")
def api_searches_update(search_id: UUID, body: dict):
    try:
        return searches_api.update_search(search_id, _parse_search_body(body))
    except (
        searches_api.SearchError,
        searches_api.SearchConflict,
        searches_api.SearchNotFound,
        RuntimeError,
    ) as exc:
        _search_http(exc)


@app.delete("/api/searches/{search_id}", status_code=204)
def api_searches_delete(search_id: UUID) -> None:
    try:
        searches_api.delete_search(search_id)
    except (searches_api.SearchNotFound, RuntimeError) as exc:
        _search_http(exc)


@app.get("/api/search-groups")
def api_search_groups_list():
    try:
        return search_groups_api.list_groups()
    except RuntimeError as exc:
        _group_http(exc)


@app.post("/api/search-groups")
def api_search_groups_create(body: dict):
    try:
        return search_groups_api.create_group(_parse_group_body(body))
    except (
        search_groups_api.SearchGroupError,
        search_groups_api.SearchGroupConflict,
        RuntimeError,
    ) as exc:
        _group_http(exc)


@app.put("/api/search-groups/{group_id}")
def api_search_groups_update(group_id: UUID, body: dict):
    try:
        return search_groups_api.update_group(group_id, _parse_group_body(body))
    except (
        search_groups_api.SearchGroupError,
        search_groups_api.SearchGroupConflict,
        search_groups_api.SearchGroupNotFound,
        RuntimeError,
    ) as exc:
        _group_http(exc)


@app.delete("/api/search-groups/{group_id}", status_code=204)
def api_search_groups_delete(group_id: UUID) -> None:
    try:
        search_groups_api.delete_group(group_id)
    except (search_groups_api.SearchGroupNotFound, RuntimeError) as exc:
        _group_http(exc)


@app.get("/api/platforms")
def api_platforms_list():
    try:
        return platforms_api.list_platforms()
    except RuntimeError as exc:
        if str(exc) == "database_unconfigured":
            raise HTTPException(status_code=503, detail="db_down") from exc
        raise


@app.put("/api/platforms/{platform_id}")
def api_platforms_update(platform_id: str, body: dict):
    try:
        patch = platforms_api.PlatformPatch.model_validate(body)
    except ValidationError as exc:
        raise HTTPException(status_code=400, detail="invalid_platform") from exc
    try:
        return platforms_api.set_platform_enabled(platform_id, enabled=patch.enabled)
    except platforms_api.PlatformNotFound as exc:
        raise HTTPException(status_code=404, detail="not_found") from exc
    except RuntimeError as exc:
        if str(exc) == "database_unconfigured":
            raise HTTPException(status_code=503, detail="db_down") from exc
        raise


@app.post("/api/platforms/{platform_id}/cookies")
def api_platforms_cookies(platform_id: str, body: object = Body(...)):
    try:
        return platforms_api.upload_platform_cookies(platform_id, body)
    except platforms_api.PlatformNotFound as exc:
        raise HTTPException(status_code=404, detail="not_found") from exc
    except platforms_api.CookieUploadError as exc:
        detail = str(exc) or "invalid_cookies_json"
        if detail == "cookies_write_failed":
            raise HTTPException(status_code=500, detail=detail) from exc
        raise HTTPException(status_code=400, detail=detail) from exc
    except RuntimeError as exc:
        if str(exc) == "database_unconfigured":
            raise HTTPException(status_code=503, detail="db_down") from exc
        raise


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
    ai_reviewed: str | None = Query(default=None),
    ai_trigger: str | None = Query(default=None),
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
            ai_reviewed=ai_reviewed,
            ai_trigger=ai_trigger,
        )
    except (inbox.InboxQueryError, inbox.InboxNotFound, RuntimeError) as exc:
        _inbox_http(exc)


@app.post("/api/inbox/ai-review")
def api_inbox_ai_review(body: dict | None = None):
    try:
        return inbox.run_ai_review(body or {})
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


@app.put("/api/inbox/{tender_id}/board-hidden")
def api_inbox_board_hidden(tender_id: str, body: dict):
    try:
        return inbox.set_board_hidden(tender_id, body)
    except (inbox.InboxQueryError, inbox.InboxNotFound, RuntimeError) as exc:
        _inbox_http(exc)


@app.post("/api/inbox/{tender_id}/ai-wrong")
def api_inbox_ai_wrong(tender_id: str, body: dict | None = None):
    try:
        return inbox.mark_ai_wrong(tender_id, body or {})
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
