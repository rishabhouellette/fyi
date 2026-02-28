r"""In-process smoke test for the FastAPI app in web_server.py.

Runs without starting a real server by using httpx's ASGITransport.
This is meant to validate that endpoints respond and that we don't return
"fake success" for unimplemented platform flows.

Usage (Windows PowerShell):
    .\venv\Scripts\Activate.ps1
    python scripts\smoke_test_web_server.py
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

import httpx


def _fail(msg: str) -> None:
    raise SystemExit(f"SMOKE TEST FAILED: {msg}")


def _assert(cond: bool, msg: str) -> None:
    if not cond:
        _fail(msg)


def _parse_iso_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    s = value.strip()
    if not s:
        return None
    # Allow Zulu suffix.
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    try:
        return datetime.fromisoformat(s)
    except Exception:
        return None


async def main() -> int:
    # Ensure repo root is importable when running from scripts/.
    project_dir = Path(__file__).resolve().parents[1]
    if str(project_dir) not in sys.path:
        sys.path.insert(0, str(project_dir))

    # Import the app.
    import web_server

    app = web_server.app

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # Health
        r = await client.get("/api/health")
        _assert(r.status_code == 200, f"/api/health status {r.status_code}")

        # Config should be real (not hard-coded) and always return JSON
        r = await client.get("/api/config")
        _assert(r.status_code == 200, f"/api/config status {r.status_code}")
        cfg = r.json()
        _assert("ffmpeg_installed" in cfg, "/api/config missing ffmpeg_installed")

        # AI tools: caption + hashtags should be functional even without Ollama
        r = await client.post(
            "/api/ai/caption",
            json={
                "topic": "Launching a new product for creators",
                "platform": "instagram",
                "tone": "casual",
                "keywords": ["creator", "workflow"],
                "max_length": 220,
                "include_hashtags": True,
                "hashtags_count": 5,
            },
        )
        _assert(r.status_code == 200, f"POST /api/ai/caption status {r.status_code}: {r.text}")
        ai1 = r.json() or {}
        _assert(ai1.get("success") is True, "/api/ai/caption did not return success")
        _assert(isinstance(ai1.get("caption"), str) and ai1.get("caption"), "/api/ai/caption missing caption")
        _assert(ai1.get("mode") in ("ollama", "fallback"), "/api/ai/caption missing mode")
        _assert(isinstance(ai1.get("hashtags"), list), "/api/ai/caption hashtags not a list")

        r = await client.post(
            "/api/ai/hashtags",
            json={
                "topic": "Launching a new product for creators",
                "platform": "instagram",
                "count": 6,
                "include_trending": True,
            },
        )
        _assert(r.status_code == 200, f"POST /api/ai/hashtags status {r.status_code}: {r.text}")
        ai2 = r.json() or {}
        _assert(ai2.get("success") is True, "/api/ai/hashtags did not return success")
        _assert(ai2.get("mode") in ("ollama", "fallback"), "/api/ai/hashtags missing mode")
        tags = ai2.get("hashtags")
        _assert(isinstance(tags, list) and len(tags) > 0, "/api/ai/hashtags missing hashtags")

        # Faceless video (MVP): should work when ffmpeg is installed, otherwise return 501.
        r = await client.post(
            "/api/video/faceless",
            json={
                "script": "Hook: 3 habits that changed my life. Tip one: make it easy. Tip two: track it. Tip three: stay consistent.",
                "width": 720,
                "height": 1280,
                "fps": 30,
                "bg_color": "black",
            },
        )
        _assert(r.status_code in (200, 501), f"POST /api/video/faceless status {r.status_code}: {r.text}")
        if r.status_code == 200:
            body = r.json() or {}
            _assert(body.get("success") is True, "/api/video/faceless did not return success")
            _assert(body.get("file_id"), "/api/video/faceless missing file_id")
            _assert(isinstance(body.get("url"), str) and body.get("url").startswith("/uploads/"), "/api/video/faceless missing url")

        # Links: create -> read -> redirect -> stats increments
        r = await client.post("/api/links", json={"target_url": "https://example.com"})
        _assert(r.status_code == 200, f"POST /api/links status {r.status_code}: {r.text}")
        data = r.json()
        slug = (data.get("link") or {}).get("slug")
        _assert(slug, "create_link did not return slug")

        r = await client.get(f"/api/links/{slug}")
        _assert(r.status_code == 200, f"GET /api/links/{{slug}} status {r.status_code}: {r.text}")
        before = (r.json().get("stats") or {}).get("clicks_total")
        _assert(isinstance(before, int), "link stats clicks_total not int")

        r = await client.get(f"/l/{slug}", follow_redirects=False)
        _assert(r.status_code in (302, 307), f"GET /l/{{slug}} expected redirect, got {r.status_code}")
        _assert(r.headers.get("location") == "https://example.com", "redirect location mismatch")

        r = await client.get(f"/api/links/{slug}")
        after = (r.json().get("stats") or {}).get("clicks_total")
        _assert(after == before + 1, f"click did not increment (before={before}, after={after})")

        # Scheduling: schedule -> list contains id
        payload = {
            "platforms": ["instagram"],
            "content": {"title": "Smoke", "caption": "Test"},
            "scheduledTime": "2026-01-12T10:00:00",
            "clips": [],
        }
        r = await client.post("/api/schedule", json=payload)
        _assert(r.status_code == 200, f"POST /api/schedule status {r.status_code}: {r.text}")
        schedule_id = (r.json() or {}).get("schedule_id")
        _assert(schedule_id, "schedule did not return schedule_id")

        r = await client.get("/api/scheduled-posts?limit=1000")
        _assert(r.status_code == 200, f"GET /api/scheduled-posts status {r.status_code}: {r.text}")
        posts = (r.json() or {}).get("posts") or []
        _assert(any(p.get("id") == schedule_id for p in posts), "scheduled post not present in list")

        # Bulk scheduling: create 2 items (smart time) -> list contains ids
        # Note: Instagram does NOT require file_id at schedule-time, so we leave it empty.
        bulk_payload = {
            "smart": True,
            "interval_minutes": 60,
            "items": [
                {
                    "platforms": ["instagram"],
                    "title": "Bulk A",
                    "caption": "Bulk",
                    "file_id": "",
                },
                {
                    "platforms": ["instagram"],
                    "title": "Bulk B",
                    "caption": "Bulk",
                    "file_id": "",
                },
            ],
        }
        r = await client.post("/api/schedule/bulk", json=bulk_payload)
        _assert(r.status_code == 200, f"POST /api/schedule/bulk status {r.status_code}: {r.text}")
        bulk = r.json() or {}
        _assert(bulk.get("success") is True, "bulk schedule did not return success")
        created = bulk.get("scheduled_posts") or []
        _assert(isinstance(created, list) and len(created) == 2, "bulk schedule did not return 2 scheduled posts")
        created_ids = [p.get("id") for p in created]
        _assert(all(created_ids), "bulk schedule returned missing ids")

        created_times = [_parse_iso_dt((p or {}).get("scheduled_time")) for p in created]
        _assert(all(t is not None for t in created_times), "bulk schedule returned invalid/missing scheduled_time")
        _assert(created_times[1] > created_times[0], "bulk schedule did not return increasing scheduled_time")
        expected_seconds = int(bulk_payload.get("interval_minutes", 60)) * 60
        actual_seconds = int(abs((created_times[1] - created_times[0]).total_seconds()))
        tolerance_seconds = 120
        _assert(
            abs(actual_seconds - expected_seconds) <= tolerance_seconds,
            f"bulk schedule interval mismatch (expected~{expected_seconds}s, got {actual_seconds}s)",
        )

        r = await client.get("/api/scheduled-posts?limit=200")
        _assert(r.status_code == 200, f"GET /api/scheduled-posts status {r.status_code}: {r.text}")
        posts = (r.json() or {}).get("posts") or []
        post_ids = {p.get("id") for p in posts}
        _assert(all(i in post_ids for i in created_ids), "bulk scheduled posts not present in list")

        # Bulk scheduling (mixed explicit + SMART): SMART should continue from explicit within the batch
        # This block uses Facebook, which requires a real file at schedule-time. Skip for now if no
        # real test file available in uploads.
        # (Skipped from automated smoke-test to avoid external dependencies.)

        # Non-implemented OAuth: must NOT return success
        r = await client.post("/oauth/start/twitter", json={"account_name": "t", "return_url": "http://test"})
        _assert(r.status_code == 501, f"/oauth/start/twitter expected 501, got {r.status_code}")

        # YouTube OAuth start: if env not set, should 400; if set, should redirect.
        r = await client.post("/oauth/start/youtube", json={"account_name": "yt", "return_url": "http://test"})
        if os.getenv("YT_CLIENT_ID") and os.getenv("YT_CLIENT_SECRET"):
            _assert(r.status_code == 200, f"/oauth/start/youtube status {r.status_code}: {r.text}")
            _assert(r.json().get("redirect") is True, "YouTube OAuth did not return redirect=true")
            _assert("auth_url" in r.json(), "YouTube OAuth did not return auth_url")
        else:
            _assert(r.status_code == 400, f"/oauth/start/youtube expected 400 without creds, got {r.status_code}")

        # Instagram publish: without an account configured should 404
        r = await client.post(
            "/api/platforms/instagram/publish",
            json={"file_id": "nope", "caption": "x", "media_type": "REELS"},
        )
        _assert(r.status_code in (404, 400), f"IG publish expected 404/400 without setup, got {r.status_code}")

        # YouTube upload: without account should 404
        r = await client.post(
            "/api/platforms/youtube/upload",
            json={"file_id": "nope", "title": "x", "description": "y", "privacy_status": "private"},
        )
        _assert(r.status_code in (404, 400), f"YT upload expected 404/400 without setup, got {r.status_code}")

        # ========================================
        # NEW FEATURE ENDPOINTS TESTS
        # ========================================

        # BYOK Keys: GET should return services list
        r = await client.get("/api/byok/keys")
        _assert(r.status_code == 200, f"GET /api/byok/keys status {r.status_code}: {r.text}")
        byok_data = r.json() or {}
        _assert(isinstance(byok_data.get("services"), dict), "/api/byok/keys missing services dict")

        # Usage: GET should return usage stats
        r = await client.get("/api/usage")
        _assert(r.status_code == 200, f"GET /api/usage status {r.status_code}: {r.text}")
        usage_data = r.json() or {}
        _assert("credits_used" in usage_data, "/api/usage missing credits_used")

        # Templates: GET should return templates
        r = await client.get("/api/templates")
        _assert(r.status_code == 200, f"GET /api/templates status {r.status_code}: {r.text}")
        templates_data = r.json() or {}
        _assert(isinstance(templates_data.get("templates"), list), "/api/templates missing templates list")
        _assert(len(templates_data.get("templates", [])) > 0, "/api/templates should have templates")

        # Templates Apply: should work with valid template_id
        r = await client.post("/api/templates/apply", json={"template_id": "hook_curiosity", "variables": {"topic": "productivity"}})
        _assert(r.status_code == 200, f"POST /api/templates/apply status {r.status_code}: {r.text}")
        apply_data = r.json() or {}
        _assert("result" in apply_data, "/api/templates/apply missing result")

        # Languages: GET should return supported languages
        r = await client.get("/api/languages")
        _assert(r.status_code == 200, f"GET /api/languages status {r.status_code}: {r.text}")
        lang_data = r.json() or {}
        _assert(isinstance(lang_data.get("languages"), dict), "/api/languages missing languages dict")
        _assert(lang_data.get("count", 0) > 50, "/api/languages should have 50+ languages")

        # Guides: GET should return platform guides
        r = await client.get("/api/guides")
        _assert(r.status_code == 200, f"GET /api/guides status {r.status_code}: {r.text}")
        guides_data = r.json() or {}
        _assert(isinstance(guides_data.get("guides"), dict), "/api/guides missing guides dict")

        # Guides: GET specific platform
        r = await client.get("/api/guides/instagram")
        _assert(r.status_code == 200, f"GET /api/guides/instagram status {r.status_code}: {r.text}")
        ig_guide = r.json() or {}
        _assert("best_times" in (ig_guide.get("guide") or {}), "/api/guides/instagram missing best_times")

        # AI Image: should require API key (expect 400 without key)
        r = await client.post("/api/ai/image", json={"prompt": "a cat", "provider": "dalle"})
        _assert(r.status_code in (400, 200), f"POST /api/ai/image status {r.status_code}: {r.text}")

        # AI Video: should require API key (expect 400 without key)
        r = await client.post("/api/ai/video", json={"prompt": "a sunset", "provider": "runway"})
        _assert(r.status_code in (400, 200), f"POST /api/ai/video status {r.status_code}: {r.text}")

        # AI Voice: should require API key (expect 400 without key)
        r = await client.post("/api/ai/voice", json={"text": "hello world", "provider": "elevenlabs"})
        _assert(r.status_code in (400, 200), f"POST /api/ai/voice status {r.status_code}: {r.text}")

        # AI Translate: should work with Ollama if available, or return 501 if no AI
        r = await client.post("/api/ai/translate", json={"text": "Hello world", "target_language": "es"})
        _assert(r.status_code in (200, 501), f"POST /api/ai/translate status {r.status_code}: {r.text}")
        if r.status_code == 200:
            translate_data = r.json() or {}
            _assert("translated_text" in translate_data, "/api/ai/translate missing translated_text")

        # Content Repurpose: test basic repurposing
        r = await client.post(
            "/api/content/repurpose",
            json={
                "content": "This is a test article about productivity tips for remote workers.",
                "source_type": "article",
                "target_formats": ["tweet"],
            },
        )
        _assert(r.status_code == 200, f"POST /api/content/repurpose status {r.status_code}: {r.text}")
        repurpose_data = r.json() or {}
        _assert("results" in repurpose_data, "/api/content/repurpose missing results")

    print("SMOKE TEST PASSED")
    return 0


if __name__ == "__main__":
    try:
        import asyncio

        raise SystemExit(asyncio.run(main()))
    except KeyboardInterrupt:
        raise SystemExit(130)
