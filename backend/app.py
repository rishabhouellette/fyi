"""Core FastAPI application factory for FYI Social."""

from __future__ import annotations

import csv
import io
import json
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from config import get_config
from backend.routes import api_v1_router
from backend.services.account_manager import get_account_manager
from backend.services.scheduler_engine import get_scheduler_engine
from database_manager import Post as DBPost
from database_manager import get_db_manager

logger = logging.getLogger("fyi.backend")

try:  # NiceGUI is optional during early scaffolding
    from nicegui import app as nicegui_app
    from nicegui import ui
except Exception:  # noqa: BLE001 - keep backend usable without NiceGUI installed
    nicegui_app = None
    ui = None


def _load_calendar_rows(data_dir: Path) -> List[Dict[str, str]]:
    """Read the lightweight schedule cache for the NiceGUI calendar view."""

    cache_path = data_dir / "last_schedules.json"
    if not cache_path.exists():
        return []
    try:
        payload = json.loads(cache_path.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001 - diagnostics already handled elsewhere
        logger.warning("Unable to parse %s", cache_path)
        return []

    rows: List[Dict[str, str]] = []
    for account, timestamp in payload.items():
        try:
            dt = datetime.fromtimestamp(float(timestamp), timezone.utc)
        except Exception:  # noqa: BLE001 - skip malformed entries
            continue
        rows.append(
            {
                "account": str(account),
                "utc": dt.isoformat(),
                "local": dt.astimezone().strftime("%Y-%m-%d %H:%M"),
            }
        )
    rows.sort(key=lambda item: item["utc"])
    return rows


def _parse_bulk_csv(raw_csv: str, default_platform: str) -> List[Dict[str, str]]:
    """Convert uploaded CSV text into normalized draft dictionaries."""

    reader = csv.DictReader(io.StringIO(raw_csv))
    drafts: List[Dict[str, str]] = []
    now = datetime.now(timezone.utc)
    for index, row in enumerate(reader):
        scheduled = row.get("scheduled_time") or (
            now + timedelta(hours=index)
        ).isoformat()
        drafts.append(
            {
                "platform": (row.get("platform") or default_platform or "facebook").strip(),
                "title": (row.get("title") or "").strip(),
                "content": row.get("content") or "",
                "media_path": row.get("media_path") or row.get("media_url") or "",
                "scheduled_time": scheduled,
            }
        )
    return drafts


class BulkUploadRequest(BaseModel):
    """Payload accepted from the lightweight Tauri dashboard."""

    csv_text: str
    default_platform: str = "facebook"
    team_id: int = 1
    account_id: int = 1

    class Config:
        anystr_strip_whitespace = True


def create_app() -> FastAPI:
    """Build the FastAPI instance with default middleware and routes."""

    cfg = get_config()

    @asynccontextmanager
    async def lifespan(_app: FastAPI):  # pragma: no cover - log side-effect only
        logger.info("FYI Social backend online at %s:%s", cfg.server_host, cfg.server_port)
        yield

    app = FastAPI(
        title="FYI Social Backend",
        version="0.1.0",
        summary="Unified core powering desktop, web, and future SaaS surfaces.",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    _register_routes(app, cfg)
    _mount_nicegui(app, cfg)

    return app


def _register_routes(app: FastAPI, cfg) -> None:
    @app.get("/", tags=["meta"])
    def root() -> Dict[str, Any]:
        return {
            "message": "FYI Social backend running",
            "docs": "/docs",
            "ui": "/ui/",
        }

    @app.get("/health", tags=["meta"])
    def health() -> Dict[str, Any]:
        now = datetime.now(timezone.utc)
        return {
            "status": "ok",
            "timestamp": now.isoformat(),
            "latency_ms": 0,
        }

    @app.get("/version", tags=["meta"])
    def version() -> Dict[str, str]:
        return {"version": app.version}

    app.include_router(api_v1_router)

    @app.get("/queue/summary", tags=["scheduler"])
    def queue_summary() -> Dict[str, Any]:
        return _serialize_summary(get_scheduler_engine().get_summary())

    @app.get("/ui-bootstrap/overview", tags=["ui"])
    def ui_bootstrap_overview() -> Dict[str, Any]:
        summary = _serialize_summary(get_scheduler_engine().get_summary())
        accounts = _serialize_accounts(get_account_manager().get_all_accounts())
        calendar = _load_calendar_rows(cfg.data_dir)
        return {
            "summary": summary,
            "accounts": accounts,
            "calendar": calendar[:50],
        }

    @app.post("/ui-bootstrap/bulk-upload", tags=["ui"])
    def ui_bulk_upload(payload: BulkUploadRequest) -> Dict[str, Any]:
        drafts = _parse_bulk_csv(payload.csv_text or "", payload.default_platform or "facebook")
        if not drafts:
            return {"created": 0, "drafts": 0, "post_ids": []}

        db = get_db_manager()
        created = 0
        post_ids: List[int] = []
        for row in drafts:
            post = DBPost(
                team_id=payload.team_id,
                account_id=payload.account_id,
                platform=row["platform"],
                title=row["title"],
                content=row["content"],
                media_paths=[row["media_path"]] if row["media_path"] else [],
                scheduled_time=row["scheduled_time"],
                status="draft",
                created_by_user_id=1,
            )
            post_id = db.create_post(post)
            if post_id:
                db.schedule_post(post_id, row["scheduled_time"], "scheduled")
                created += 1
                post_ids.append(post_id)

        return {"created": created, "drafts": len(drafts), "post_ids": post_ids}


def _serialize_summary(summary: Dict[str, Any]) -> Dict[str, Any]:
    normalized = summary.copy()
    for key in ("last_updated", "next_run_at"):
        value = normalized.get(key)
        if value is None:
            normalized[key] = None
            continue
        normalized[key] = value.isoformat() if hasattr(value, "isoformat") else value
    return normalized


def _serialize_accounts(accounts) -> List[Dict[str, str]]:
    serialized: List[Dict[str, str]] = []
    for account in accounts[:50]:
        serialized.append(
            {
                "platform": getattr(account, "platform", "unknown"),
                "name": getattr(account, "name", getattr(account, "account_name", "—")) or "—",
                "username": getattr(account, "username", getattr(account, "account_id", "")) or "—",
            }
        )
    return serialized


def _mount_nicegui(app: FastAPI, cfg) -> None:
    if nicegui_app is None or ui is None:
        logger.warning("NiceGUI not installed; skip UI mount.")
        return

    # Initialize NiceGUI with FastAPI
    ui.run_with(
        app,
        mount_path="/ui",
        storage_secret="fyi-social-secret-key-change-in-production",
    )

    @ui.page("/")
    def _dashboard() -> None:  # pragma: no cover - UI side-effects only
        ui.page_title("FYI Social Backend Console")
        ui.label("FYI Social — Core Metrics").classes("text-2xl font-bold")
        ui.label("Shared FastAPI spine powering desktop, web, and Tauri frontends.").classes(
            "text-sm text-gray-400 mb-4"
        )

        cards_row = ui.row().classes("w-full gap-4")
        accounts_table = ui.table(
            columns=[
                {"name": "platform", "label": "Platform", "field": "platform"},
                {"name": "name", "label": "Name", "field": "name"},
                {"name": "username", "label": "Username", "field": "username"},
            ],
            rows=[],
        ).classes("w-full mt-4")

        meta_label = ui.label().classes("text-xs text-gray-500 mt-2")

        def refresh_dashboard() -> None:
            summary = get_scheduler_engine().get_summary()
            cards_row.clear()
            metrics = [
                ("Pending", summary["pending"]),
                ("Workers", summary["workers_active"]),
                ("Completed today", summary["completed_today"]),
                ("Failed backlog", summary["failed_backlog"]),
            ]
            for label, value in metrics:
                with cards_row:
                    with ui.card().classes("bg-slate-900 text-white w-48"):
                        ui.label(label).classes("text-sm text-gray-400")
                        ui.label(str(value)).classes("text-3xl font-semibold")

            accounts = get_account_manager().get_all_accounts()
            accounts_table.rows = [
                {
                    "platform": acc.platform,
                    "name": acc.name,
                    "username": acc.username or "—",
                }
                for acc in accounts[:10]
            ]
            meta_label.text = (
                f"Last updated {summary['last_updated'].strftime('%Y-%m-%d %H:%M:%S %Z')} • {len(accounts)} linked accounts"
            )

        refresh_dashboard()
        ui.timer(5, refresh_dashboard)

        ui.separator().classes("my-6")
        ui.label("Web Parity — Calendar & Bulk Upload").classes("text-xl font-semibold mb-2")

        tabs = ui.tabs().classes("mb-4")
        calendar_tab = ui.tab("Content Calendar")
        bulk_tab = ui.tab("Bulk Upload")

        with ui.tab_panels(tabs, value=calendar_tab):
            with ui.tab_panel(calendar_tab):
                ui.label("Upcoming schedule (synced from data/last_schedules.json)").classes(
                    "text-sm text-gray-400 mb-2"
                )
                calendar_table = ui.table(
                    columns=[
                        {"name": "account", "label": "Account", "field": "account"},
                        {"name": "utc", "label": "UTC", "field": "utc"},
                        {"name": "local", "label": "Local", "field": "local"},
                    ],
                    rows=[],
                ).classes("w-full")

                def refresh_calendar() -> None:
                    calendar_table.rows = _load_calendar_rows(cfg.data_dir)

                refresh_calendar()
                ui.button("Refresh calendar", on_click=refresh_calendar).classes("mt-3")

            with ui.tab_panel(bulk_tab):
                ui.label("Upload CSVs from the desktop Bulk Upload tab to schedule drafts from the browser.").classes(
                    "text-sm text-gray-400 mb-4"
                )

                team_input = ui.input("Team ID", value="1").props("type=number").classes("max-w-xs")
                account_input = ui.input("Account ID", value="1").props("type=number").classes("max-w-xs mt-2")
                platform_select = ui.select(
                    ["facebook", "instagram", "linkedin", "youtube"],
                    value="facebook",
                    label="Default platform",
                ).classes("max-w-xs mt-2")

                pending_rows: List[Dict[str, str]] = []
                preview_table = ui.table(
                    columns=[
                        {"name": "platform", "label": "Platform", "field": "platform"},
                        {"name": "title", "label": "Title", "field": "title"},
                        {"name": "scheduled_time", "label": "Scheduled", "field": "scheduled_time"},
                    ],
                    rows=[],
                ).classes("w-full mt-4")

                status_label = ui.label("Upload a CSV to begin.").classes("text-xs text-gray-500 mt-2")

                def handle_upload(event) -> None:
                    nonlocal pending_rows
                    try:
                        data = event.content.read().decode("utf-8")
                    except Exception as exc:  # noqa: BLE001
                        ui.notify(f"Upload failed: {exc}", color="negative")
                        return
                    pending_rows = _parse_bulk_csv(data, platform_select.value or "facebook")
                    preview_table.rows = pending_rows
                    status_label.text = f"Ready to schedule {len(pending_rows)} draft(s)."
                    ui.notify(f"Loaded {len(pending_rows)} drafts", color="primary")

                ui.upload(on_upload=handle_upload).props("accept=.csv label='Drop CSV here'").classes("mt-4")

                def schedule_batch() -> None:
                    nonlocal pending_rows
                    if not pending_rows:
                        ui.notify("Upload a CSV first", color="negative")
                        return
                    try:
                        team_id = int(team_input.value or 1)
                    except ValueError:
                        team_id = 1
                    try:
                        account_id = int(account_input.value or 1)
                    except ValueError:
                        account_id = 1

                    db = get_db_manager()
                    created = 0
                    for row in pending_rows:
                        post = DBPost(
                            team_id=team_id,
                            account_id=account_id,
                            platform=row["platform"],
                            title=row["title"],
                            content=row["content"],
                            media_paths=[row["media_path"]] if row["media_path"] else [],
                            scheduled_time=row["scheduled_time"],
                            status="draft",
                            created_by_user_id=1,
                        )
                        post_id = db.create_post(post)
                        if post_id:
                            db.schedule_post(post_id, row["scheduled_time"], "scheduled")
                            created += 1

                    pending_rows = []
                    preview_table.rows = []
                    status_label.text = f"Scheduled {created} draft(s)."
                    ui.notify(f"Scheduled {created} draft(s)", color="positive")

                def clear_preview() -> None:
                    nonlocal pending_rows
                    pending_rows = []
                    preview_table.rows = []
                    status_label.text = "Upload a CSV to begin."

                with ui.row().classes("gap-4 mt-4"):
                    ui.button("Schedule batch", on_click=schedule_batch, color="primary")
                    ui.button("Clear", on_click=clear_preview, color="secondary")

        ui.link("Open API docs", "/docs").classes("mt-4 inline-block text-primary")

    logger.info("Mounted NiceGUI preview at %s://%s:%s/ui/", _scheme(cfg), cfg.server_host, cfg.server_port)


def _scheme(cfg) -> str:
    if cfg.oauth_redirect_origin.startswith("https://"):
        return "https"
    return "http"
