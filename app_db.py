"""Lightweight SQLite persistence for the FYI web portal.

This module is intentionally dependency-free (stdlib only) so the web portal
can run without pulling in the legacy V1/V2 graveyard backend.
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


@dataclass(frozen=True)
class Link:
    id: int
    slug: str
    target_url: str
    created_at: str


class AppDB:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _init_db(self) -> None:
        conn = self._connect()
        try:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS accounts (
                    id TEXT PRIMARY KEY,
                    platform TEXT NOT NULL,
                    name TEXT NOT NULL,
                    username TEXT NOT NULL,
                    status TEXT NOT NULL,
                    connected_at TEXT,
                    followers INTEGER DEFAULT 0,
                    total_posts INTEGER DEFAULT 0,
                    page_id TEXT,
                    ig_user_id TEXT,
                    access_token TEXT
                );

                CREATE TABLE IF NOT EXISTS scheduled_posts (
                    id TEXT PRIMARY KEY,
                    title TEXT,
                    caption TEXT,
                    platforms_json TEXT NOT NULL,
                    scheduled_time TEXT NOT NULL,
                    date TEXT,
                    time TEXT,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    payload_json TEXT,
                    result_json TEXT,
                    last_error TEXT,
                    attempts INTEGER DEFAULT 0,
                    posted_at TEXT
                );

                CREATE TABLE IF NOT EXISTS short_links (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    slug TEXT UNIQUE NOT NULL,
                    target_url TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS link_clicks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    link_id INTEGER NOT NULL,
                    clicked_at TEXT NOT NULL,
                    ip TEXT,
                    user_agent TEXT,
                    referrer TEXT,
                    FOREIGN KEY (link_id) REFERENCES short_links(id) ON DELETE CASCADE
                );

                CREATE INDEX IF NOT EXISTS idx_scheduled_posts_time ON scheduled_posts(scheduled_time);
                CREATE INDEX IF NOT EXISTS idx_link_clicks_link_id ON link_clicks(link_id);
                """
            )

            # Best-effort migration for older DBs.
            cols = {r[1] for r in conn.execute("PRAGMA table_info(scheduled_posts)").fetchall()}
            if "payload_json" not in cols:
                conn.execute("ALTER TABLE scheduled_posts ADD COLUMN payload_json TEXT")
            if "result_json" not in cols:
                conn.execute("ALTER TABLE scheduled_posts ADD COLUMN result_json TEXT")
            if "last_error" not in cols:
                conn.execute("ALTER TABLE scheduled_posts ADD COLUMN last_error TEXT")
            if "attempts" not in cols:
                conn.execute("ALTER TABLE scheduled_posts ADD COLUMN attempts INTEGER DEFAULT 0")
            if "posted_at" not in cols:
                conn.execute("ALTER TABLE scheduled_posts ADD COLUMN posted_at TEXT")

            conn.commit()
        finally:
            conn.close()

    # -------------------- Accounts --------------------

    def upsert_account(self, account: dict[str, Any]) -> None:
        conn = self._connect()
        try:
            conn.execute(
                """
                INSERT INTO accounts (
                    id, platform, name, username, status, connected_at,
                    followers, total_posts, page_id, ig_user_id, access_token
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    platform=excluded.platform,
                    name=excluded.name,
                    username=excluded.username,
                    status=excluded.status,
                    connected_at=excluded.connected_at,
                    followers=excluded.followers,
                    total_posts=excluded.total_posts,
                    page_id=excluded.page_id,
                    ig_user_id=excluded.ig_user_id,
                    access_token=excluded.access_token
                """,
                (
                    account.get("id"),
                    account.get("platform"),
                    account.get("name"),
                    account.get("username"),
                    account.get("status") or "connected",
                    account.get("connected_at"),
                    int(account.get("followers") or 0),
                    int(account.get("total_posts") or 0),
                    account.get("page_id"),
                    account.get("ig_user_id"),
                    account.get("access_token"),
                ),
            )
            conn.commit()
        finally:
            conn.close()

    def delete_account(self, account_id: str) -> None:
        conn = self._connect()
        try:
            conn.execute("DELETE FROM accounts WHERE id = ?", (account_id,))
            conn.commit()
        finally:
            conn.close()

    # -------------------- Scheduled posts --------------------

    def scheduled_posts_count(self) -> int:
        conn = self._connect()
        try:
            row = conn.execute("SELECT COUNT(1) AS c FROM scheduled_posts").fetchone()
            return int(row["c"] or 0)
        finally:
            conn.close()

    def insert_scheduled_post(self, post: dict[str, Any]) -> None:
        conn = self._connect()
        try:
            conn.execute(
                """
                INSERT INTO scheduled_posts (
                    id, title, caption, platforms_json, scheduled_time, date, time, status, created_at,
                    payload_json, result_json, last_error, attempts, posted_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    title=excluded.title,
                    caption=excluded.caption,
                    platforms_json=excluded.platforms_json,
                    scheduled_time=excluded.scheduled_time,
                    date=excluded.date,
                    time=excluded.time,
                    status=excluded.status,
                    payload_json=COALESCE(excluded.payload_json, scheduled_posts.payload_json)
                """,
                (
                    post.get("id"),
                    post.get("title"),
                    post.get("caption"),
                    json.dumps(post.get("platforms") or []),
                    post.get("scheduled_time"),
                    post.get("date"),
                    post.get("time"),
                    post.get("status") or "scheduled",
                    post.get("created_at") or _utc_now_iso(),
                    json.dumps(post.get("payload") or post.get("payload_json") or {}) if (post.get("payload") is not None or post.get("payload_json") is not None) else None,
                    json.dumps(post.get("result") or {}) if post.get("result") is not None else None,
                    post.get("last_error"),
                    int(post.get("attempts") or 0),
                    post.get("posted_at"),
                ),
            )
            conn.commit()
        finally:
            conn.close()

    def list_scheduled_posts(self, limit: int = 200) -> list[dict[str, Any]]:
        limit = max(1, min(int(limit or 200), 1000))
        conn = self._connect()
        try:
            rows = conn.execute(
                """
                SELECT * FROM scheduled_posts
                ORDER BY scheduled_time DESC, created_at DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
            result: list[dict[str, Any]] = []
            for r in rows:
                payload = None
                try:
                    payload = json.loads(r["payload_json"]) if r["payload_json"] else None
                except Exception:
                    payload = None
                result_obj = {
                    "id": r["id"],
                    "title": r["title"] or "",
                    "caption": r["caption"] or "",
                    "platforms": json.loads(r["platforms_json"] or "[]"),
                    "scheduled_time": r["scheduled_time"],
                    "date": r["date"] or "",
                    "time": r["time"] or "",
                    "status": r["status"],
                    "created_at": r["created_at"],
                    "attempts": int(r["attempts"] or 0) if "attempts" in r.keys() else 0,
                    "posted_at": r["posted_at"] if "posted_at" in r.keys() else None,
                    "last_error": r["last_error"] if "last_error" in r.keys() else None,
                }
                if payload is not None:
                    result_obj["payload"] = payload
                result.append(
                    result_obj
                )
            return result
        finally:
            conn.close()

    def list_due_scheduled_posts(self, now_iso: str, limit: int = 25) -> list[dict[str, Any]]:
        """Return scheduled posts due at/before now (status=scheduled)."""
        limit = max(1, min(int(limit or 25), 200))
        conn = self._connect()
        try:
            rows = conn.execute(
                """
                SELECT * FROM scheduled_posts
                WHERE status = 'scheduled' AND scheduled_time <= ?
                ORDER BY scheduled_time ASC
                LIMIT ?
                """,
                (now_iso, limit),
            ).fetchall()
            # Reuse the formatting logic by temporarily wrapping rows as dicts.
            out: list[dict[str, Any]] = []
            for r in rows:
                payload = None
                try:
                    payload = json.loads(r["payload_json"]) if r["payload_json"] else None
                except Exception:
                    payload = None
                obj = {
                    "id": r["id"],
                    "title": r["title"] or "",
                    "caption": r["caption"] or "",
                    "platforms": json.loads(r["platforms_json"] or "[]"),
                    "scheduled_time": r["scheduled_time"],
                    "date": r["date"] or "",
                    "time": r["time"] or "",
                    "status": r["status"],
                    "created_at": r["created_at"],
                    "attempts": int(r["attempts"] or 0) if "attempts" in r.keys() else 0,
                    "posted_at": r["posted_at"] if "posted_at" in r.keys() else None,
                    "last_error": r["last_error"] if "last_error" in r.keys() else None,
                }
                if payload is not None:
                    obj["payload"] = payload
                out.append(obj)
            return out
        finally:
            conn.close()

    def mark_scheduled_post_attempt(self, post_id: str, status: str, attempts_inc: int = 1) -> bool:
        conn = self._connect()
        try:
            cur = conn.execute(
                """
                UPDATE scheduled_posts
                SET status = ?, attempts = COALESCE(attempts, 0) + ?
                WHERE id = ?
                """,
                (status, int(attempts_inc or 0), post_id),
            )
            conn.commit()
            return cur.rowcount > 0
        finally:
            conn.close()

    def mark_scheduled_post_result(self, post_id: str, status: str, result: Optional[dict[str, Any]], error: Optional[str]) -> bool:
        conn = self._connect()
        try:
            cur = conn.execute(
                """
                UPDATE scheduled_posts
                SET status = ?,
                    result_json = ?,
                    last_error = ?,
                    posted_at = ?
                WHERE id = ?
                """,
                (
                    status,
                    json.dumps(result or {}) if result is not None else None,
                    error,
                    _utc_now_iso() if status == "posted" else None,
                    post_id,
                ),
            )
            conn.commit()
            return cur.rowcount > 0
        finally:
            conn.close()

    def update_scheduled_post(self, post_id: str, updates: dict[str, Any]) -> bool:
        allowed = {
            "title",
            "caption",
            "platforms",
            "scheduled_time",
            "date",
            "time",
            "status",
        }
        safe = {k: v for k, v in (updates or {}).items() if k in allowed}
        if not safe:
            return False

        sets: list[str] = []
        params: list[Any] = []

        if "platforms" in safe:
            sets.append("platforms_json = ?")
            params.append(json.dumps(safe.get("platforms") or []))

        for col in ("title", "caption", "scheduled_time", "date", "time", "status"):
            if col in safe:
                sets.append(f"{col} = ?")
                params.append(safe.get(col))

        params.append(post_id)
        sql = f"UPDATE scheduled_posts SET {', '.join(sets)} WHERE id = ?"

        conn = self._connect()
        try:
            cur = conn.execute(sql, tuple(params))
            conn.commit()
            return cur.rowcount > 0
        finally:
            conn.close()

    def cancel_scheduled_post(self, post_id: str) -> bool:
        return self.update_scheduled_post(post_id, {"status": "cancelled"})

    # -------------------- Link tracking --------------------

    def create_link(self, slug: str, target_url: str) -> Link:
        slug = (slug or "").strip()
        target_url = (target_url or "").strip()
        if not slug:
            raise ValueError("slug is required")
        if not target_url:
            raise ValueError("target_url is required")

        conn = self._connect()
        try:
            created_at = _utc_now_iso()
            cur = conn.execute(
                "INSERT INTO short_links (slug, target_url, created_at) VALUES (?, ?, ?)",
                (slug, target_url, created_at),
            )
            conn.commit()
            return Link(id=int(cur.lastrowid), slug=slug, target_url=target_url, created_at=created_at)
        finally:
            conn.close()

    def get_link_by_slug(self, slug: str) -> Optional[Link]:
        conn = self._connect()
        try:
            row = conn.execute(
                "SELECT id, slug, target_url, created_at FROM short_links WHERE slug = ?",
                (slug,),
            ).fetchone()
            if not row:
                return None
            return Link(id=int(row["id"]), slug=row["slug"], target_url=row["target_url"], created_at=row["created_at"])
        finally:
            conn.close()

    def list_links(self, limit: int = 200) -> list[dict[str, Any]]:
        limit = max(1, min(int(limit or 200), 1000))
        conn = self._connect()
        try:
            rows = conn.execute(
                """
                SELECT l.id, l.slug, l.target_url, l.created_at,
                       (SELECT COUNT(1) FROM link_clicks c WHERE c.link_id = l.id) AS clicks
                FROM short_links l
                ORDER BY l.created_at DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def record_click(self, link_id: int, ip: Optional[str], user_agent: Optional[str], referrer: Optional[str]) -> None:
        conn = self._connect()
        try:
            conn.execute(
                "INSERT INTO link_clicks (link_id, clicked_at, ip, user_agent, referrer) VALUES (?, ?, ?, ?, ?)",
                (int(link_id), _utc_now_iso(), ip, user_agent, referrer),
            )
            conn.commit()
        finally:
            conn.close()

    def link_stats(self, link_id: int) -> dict[str, Any]:
        conn = self._connect()
        try:
            total = conn.execute(
                "SELECT COUNT(1) AS c FROM link_clicks WHERE link_id = ?",
                (int(link_id),),
            ).fetchone()
            by_day = conn.execute(
                """
                SELECT substr(clicked_at, 1, 10) AS day, COUNT(1) AS clicks
                FROM link_clicks
                WHERE link_id = ?
                GROUP BY substr(clicked_at, 1, 10)
                ORDER BY day DESC
                LIMIT 90
                """,
                (int(link_id),),
            ).fetchall()
            return {
                "clicks_total": int(total["c"]) if total else 0,
                "clicks_by_day": [dict(r) for r in by_day],
            }
        finally:
            conn.close()
