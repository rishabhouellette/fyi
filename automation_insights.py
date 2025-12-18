"""Automation intelligence helpers for Phase 3 features."""

from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from statistics import mean
from typing import Dict, List, Tuple

from database_manager import get_db_manager
from logger_config import get_logger

logger = get_logger(__name__)

def _hour_bucket(timestamp: str | None) -> Tuple[str, int]:
    if not timestamp:
        now = datetime.now()
        return now.strftime("%a"), now.hour
    try:
        dt = datetime.fromisoformat(timestamp)
    except ValueError:
        dt = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
    return dt.strftime("%a"), dt.hour


class AutoSchedulingEngine:
    """Learns best posting windows + recycling candidates from analytics."""

    def __init__(self, cache_path: Path | str = "data/automation_cache.json"):
        self.db = get_db_manager()
        self.cache_path = Path(cache_path)
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        self.cache = self._load_cache()

    # ------------------------------------------------------------------
    def best_windows(self, team_id: int = 1, platform: str | None = None, limit: int = 5) -> List[Dict]:
        posts = self.db.get_posts(team_id, filters={"platform": platform} if platform else None)
        analytics = self.db.get_analytics(team_id, days=60)
        metric_index = self._metric_index(analytics)

        buckets: Dict[Tuple[str, int], List[float]] = defaultdict(list)
        for post in posts:
            weekday, hour = _hour_bucket(post.scheduled_time or post.published_time)
            metrics = metric_index.get(post.id, [])
            score = self._engagement_score(metrics)
            if score == 0:
                score = 1 if post.status == "published" else 0.2
            buckets[(weekday, hour)].append(score)

        ranked = [
            {
                "weekday": weekday,
                "hour": hour,
                "score": round(mean(scores), 2),
                "samples": len(scores),
            }
            for (weekday, hour), scores in buckets.items()
            if scores
        ]
        ranked.sort(key=lambda item: item["score"], reverse=True)
        return ranked[:limit] or self._fallback_windows()

    def recycling_queue(self, team_id: int = 1, platform: str | None = None, limit: int = 5) -> List[Dict]:
        posts = self.db.get_posts(team_id, filters={"status": "published", "platform": platform} if platform else None)
        analytics = self.db.get_analytics(team_id, days=120)
        metric_index = self._metric_index(analytics)
        ignored = set(self.cache.get("recycled_post_ids", []))
        results: List[Dict] = []
        for post in posts:
            if post.id in ignored:
                continue
            metrics = metric_index.get(post.id, [])
            score = self._engagement_score(metrics)
            if score < 25:
                continue
            last_run = self._last_run(post)
            if last_run and (datetime.now() - last_run).days < 21:
                continue
            results.append({
                "post_id": post.id,
                "platform": post.platform,
                "title": post.title or (post.content or "Untitled")[:40],
                "score": round(score, 1),
                "suggested_date": (datetime.now() + timedelta(days=5)).strftime("%b %d"),
                "recommendation": "Repurpose top performer with updated hook",
            })
        results.sort(key=lambda item: item["score"], reverse=True)
        return results[:limit]

    def mark_recycled(self, post_id: int) -> None:
        recycled = set(self.cache.get("recycled_post_ids", []))
        recycled.add(post_id)
        self.cache["recycled_post_ids"] = list(recycled)
        self._save_cache()

    def auto_reschedule(self, platform: str, count: int = 3) -> List[Dict]:
        windows = self.best_windows(platform=platform, limit=count)
        queue = []
        base = datetime.now()
        for offset, window in enumerate(windows):
            target_date = base + timedelta(days=offset)
            scheduled = target_date.replace(hour=window["hour"], minute=0, second=0)
            queue.append({
                "platform": platform,
                "scheduled_at": scheduled.isoformat(),
                "confidence": window["score"],
                "weekday": window["weekday"],
            })
        return queue

    # ------------------------------------------------------------------
    def _metric_index(self, metrics) -> Dict[int, List]:
        index: Dict[int, List] = defaultdict(list)
        for metric in metrics:
            if metric.post_id:
                index[metric.post_id].append(metric)
        return index

    def _engagement_score(self, metrics) -> float:
        if not metrics:
            return 0
        return mean([
            m.engagement or (m.likes + m.comments + m.shares * 1.5)
            for m in metrics
        ])

    def _last_run(self, post) -> datetime | None:
        timestamp = post.published_time or post.updated_at or post.scheduled_time
        if not timestamp:
            return None
        try:
            return datetime.fromisoformat(timestamp)
        except ValueError:
            return None

    def _fallback_windows(self) -> List[Dict]:
        popular = [("Tue", 10), ("Wed", 13), ("Thu", 19), ("Sat", 9)]
        return [
            {"weekday": day, "hour": hour, "score": 50.0, "samples": 0}
            for day, hour in popular
        ]

    def _load_cache(self) -> Dict:
        if not self.cache_path.exists():
            return {}
        try:
            return json.loads(self.cache_path.read_text(encoding="utf-8"))
        except Exception:
            return {}

    def _save_cache(self):
        self.cache_path.write_text(json.dumps(self.cache, indent=2), encoding="utf-8")


_scheduler_instance: AutoSchedulingEngine | None = None


def get_auto_scheduler() -> AutoSchedulingEngine:
    global _scheduler_instance
    if _scheduler_instance is None:
        _scheduler_instance = AutoSchedulingEngine()
    return _scheduler_instance
