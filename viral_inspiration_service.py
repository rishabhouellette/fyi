"""Viral inspiration data store for Phase 2 research features.

This module tracks high-performing social posts across niches/platforms so the
UI can surface concrete examples, hooks, and stat breakdowns.
"""

from __future__ import annotations

import json
import random
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, List, Optional

from logger_config import get_logger

logger = get_logger(__name__)


@dataclass
class ViralPost:
    """Normalized representation of a viral post entry."""

    post_id: str
    platform: str
    niche: str
    hook: str
    summary: str
    url: str
    creator: str
    metrics: Dict[str, float]
    captured_at: float

    def to_dict(self) -> Dict:
        data = asdict(self)
        data["captured_at"] = self.captured_at
        return data


class ViralInspirationService:
    """Loads, caches, and refreshes viral inspiration data."""

    def __init__(self, db_path: Path | str = "data/viral_inspiration.json"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.posts: List[ViralPost] = []
        self._load_or_seed()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def get_trending(
        self,
        niche: Optional[str] = None,
        platform: Optional[str] = None,
        limit: int = 10,
    ) -> List[ViralPost]:
        """Return high-performing posts filtered by niche/platform."""

        results = self.posts
        if niche and niche.lower() != "all":
            results = [p for p in results if p.niche.lower() == niche.lower()]
        if platform and platform.lower() != "all":
            results = [p for p in results if p.platform.lower() == platform.lower()]

        def score(post: ViralPost) -> float:
            metrics = post.metrics
            return (
                metrics.get("engagement_rate", 0) * 100
                + metrics.get("views", 0) * 0.0001
                + metrics.get("saves", 0) * 0.01
            )

        return sorted(results, key=score, reverse=True)[:limit]

    def get_heatmap(self) -> Dict[str, Dict[str, float]]:
        """Aggregate engagement rate per niche/platform for quick insights."""

        heatmap: Dict[str, Dict[str, List[float]]] = {}
        for post in self.posts:
            heatmap.setdefault(post.niche, {}).setdefault(post.platform, []).append(
                post.metrics.get("engagement_rate", 0)
            )

        averaged: Dict[str, Dict[str, float]] = {}
        for niche, platform_map in heatmap.items():
            averaged[niche] = {}
            for platform, values in platform_map.items():
                averaged[niche][platform] = round(sum(values) / max(len(values), 1), 3)
        return averaged

    def refresh_sample_data(self) -> None:
        """Inject a new synthetic sample to simulate nightly refresh."""

        niches = ["saas", "fitness", "beauty", "finance"]
        platforms = ["instagram", "tiktok", "youtube", "twitter"]
        hooks = [
            "This automation killed our content calendar",
            "I tried the 3-3-3 storytelling trick",
            "The macro everyone ignored in 2024",
            "Steal this retention loop",
        ]

        post = ViralPost(
            post_id=f"sample_{int(time.time())}",
            platform=random.choice(platforms),
            niche=random.choice(niches),
            hook=random.choice(hooks),
            summary="Auto-refreshed insight generated for demo purposes.",
            url="https://example.com/viral",  # placeholder
            creator="@trendwatch",
            metrics={
                "views": random.randint(50_000, 750_000),
                "likes": random.randint(2_000, 25_000),
                "comments": random.randint(50, 1_200),
                "saves": random.randint(200, 4_000),
                "engagement_rate": round(random.uniform(0.045, 0.12), 3),
            },
            captured_at=time.time(),
        )
        self.posts.append(post)
        self.posts = self.posts[-200:]
        self._save()

    # ------------------------------------------------------------------
    # Persistence helpers
    # ------------------------------------------------------------------
    def _load_or_seed(self) -> None:
        if not self.db_path.exists():
            self._seed_samples()
            return

        try:
            payload = json.loads(self.db_path.read_text(encoding="utf-8"))
            self.posts = [ViralPost(**item) for item in payload]
        except Exception as exc:  # pragma: no cover - corrupted user file
            logger.error("Failed to load viral inspiration DB: %s", exc)
            self.posts = []
            self._seed_samples()

    def _save(self) -> None:
        data = [post.to_dict() for post in self.posts]
        self.db_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def _seed_samples(self) -> None:
        seed_posts = [
            ViralPost(
                post_id="ig_growth_loop",
                platform="instagram",
                niche="saas",
                hook="We tripled demo signups with this 3-slide carousel",
                summary="Breaks down a carousel using curiosity gaps + CTA ladder.",
                url="https://www.instagram.com/p/demo",
                creator="@growthloops",
                metrics={
                    "views": 185_000,
                    "likes": 12_400,
                    "comments": 487,
                    "saves": 2_950,
                    "engagement_rate": 0.084,
                },
                captured_at=time.time() - 86_400,
            ),
            ViralPost(
                post_id="tt_story_broll",
                platform="tiktok",
                niche="fitness",
                hook="Day 45 of fixing my posture (what no one tells you)",
                summary="Split-screen TikTok showing before/after overlays and on-screen steps.",
                url="https://www.tiktok.com/@coach/video/demo",
                creator="@coachLayla",
                metrics={
                    "views": 920_000,
                    "likes": 61_000,
                    "comments": 3_200,
                    "saves": 7_800,
                    "engagement_rate": 0.102,
                },
                captured_at=time.time() - 43_200,
            ),
            ViralPost(
                post_id="yt_b2b_case",
                platform="youtube",
                niche="finance",
                hook="We automated our CFO stack (and saved $480k)",
                summary="Talking-head + b-roll case study with timeline overlays.",
                url="https://youtube.com/watch?v=demo",
                creator="FinanceOps Daily",
                metrics={
                    "views": 310_000,
                    "likes": 9_400,
                    "comments": 640,
                    "saves": 1_900,
                    "engagement_rate": 0.058,
                },
                captured_at=time.time() - 65_000,
            ),
        ]
        self.posts = seed_posts
        self._save()


_service: Optional[ViralInspirationService] = None


def get_viral_inspiration_service() -> ViralInspirationService:
    global _service
    if _service is None:
        _service = ViralInspirationService()
    return _service
