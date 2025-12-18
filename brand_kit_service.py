"""Brand kit + stock asset helper for Phase 2."""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, List, Optional

import requests

from logger_config import get_logger

logger = get_logger(__name__)


@dataclass
class BrandKit:
    kit_id: str
    team_id: int
    name: str
    tone: str
    primary_color: str
    secondary_color: str
    accent_color: str
    fonts: List[str]
    voice_notes: str
    logo_path: Optional[str] = None

    def to_dict(self) -> Dict:
        return asdict(self)


class BrandKitService:
    """Stores brand kits and proxies stock-asset lookups."""

    def __init__(
        self,
        kits_path: Path | str = "data/brand_kits.json",
        stock_cache: Path | str = "data/stock_cache.json",
    ) -> None:
        self.kits_path = Path(kits_path)
        self.stock_cache = Path(stock_cache)
        self.kits_path.parent.mkdir(parents=True, exist_ok=True)
        self.kits: List[BrandKit] = []
        self._load_or_seed()
        self._seed_stock_cache()

    # ------------------------------------------------------------------
    def list_kits(self, team_id: int = 1) -> List[BrandKit]:
        return [kit for kit in self.kits if kit.team_id == team_id]

    def save_kit(self, kit: BrandKit) -> None:
        existing = next((idx for idx, item in enumerate(self.kits) if item.kit_id == kit.kit_id), None)
        if existing is None:
            self.kits.append(kit)
        else:
            self.kits[existing] = kit
        self._save()

    def search_stock(self, query: str, media_type: str = "image", limit: int = 6) -> List[Dict]:
        api_key = os.getenv("PEXELS_API_KEY")
        if api_key:
            try:
                return self._hit_pexels(api_key, query, media_type, limit)
            except Exception as exc:  # pragma: no cover - external call
                logger.warning("Pexels search failed, falling back to cache: %s", exc)
        return self._cached_assets(query, limit)

    # ------------------------------------------------------------------
    def _load_or_seed(self) -> None:
        if not self.kits_path.exists():
            self._seed_kits()
            return
        try:
            payload = json.loads(self.kits_path.read_text(encoding="utf-8"))
            self.kits = [BrandKit(**entry) for entry in payload]
        except Exception as exc:  # pragma: no cover
            logger.error("Unable to read brand kits: %s", exc)
            self.kits = []
            self._seed_kits()

    def _save(self) -> None:
        data = [kit.to_dict() for kit in self.kits]
        self.kits_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def _seed_kits(self) -> None:
        self.kits = [
            BrandKit(
                kit_id="default_saas",
                team_id=1,
                name="FYI Default",
                tone="Bold, data-backed, no fluff",
                primary_color="#5B5FFF",
                secondary_color="#181A27",
                accent_color="#00E0B8",
                fonts=["Sora Bold", "Inter Regular"],
                voice_notes="Short declarative headlines + proof points.",
                logo_path=None,
            ),
            BrandKit(
                kit_id="creator_personal",
                team_id=1,
                name="Creator Personal",
                tone="Friendly, behind-the-scenes, emoji-friendly",
                primary_color="#FF6F61",
                secondary_color="#1F1F1F",
                accent_color="#FFD166",
                fonts=["Poppins SemiBold", "Poppins Light"],
                voice_notes="Use conversational first-person voice + callouts.",
                logo_path=None,
            ),
        ]
        self._save()

    # ------------------------------------------------------------------
    def _seed_stock_cache(self) -> None:
        if self.stock_cache.exists():
            return
        sample_assets = [
            {
                "id": "pexels_mock_1",
                "preview": "https://images.pexels.com/photos/3184292/pexels-photo-3184292.jpeg",
                "photographer": "Faux Agency",
                "color": "#4A90E2",
                "query": "workspace",
                "type": "image",
            },
            {
                "id": "pexels_mock_2",
                "preview": "https://images.pexels.com/photos/3861969/pexels-photo-3861969.jpeg",
                "photographer": "Creative Mix",
                "color": "#00BFA6",
                "query": "creator",
                "type": "image",
            },
            {
                "id": "pexels_mock_3",
                "preview": "https://images.pexels.com/photos/768472/pexels-photo-768472.jpeg",
                "photographer": "Studio 51",
                "color": "#222",
                "query": "fitness",
                "type": "video",
            },
        ]
        self.stock_cache.write_text(json.dumps(sample_assets, indent=2), encoding="utf-8")

    def _cached_assets(self, query: str, limit: int) -> List[Dict]:
        try:
            assets = json.loads(self.stock_cache.read_text(encoding="utf-8"))
        except Exception:  # pragma: no cover
            return []
        query_lower = query.lower()
        filtered = [asset for asset in assets if query_lower in asset.get("query", "")] or assets
        return filtered[:limit]

    def _hit_pexels(self, api_key: str, query: str, media_type: str, limit: int) -> List[Dict]:
        endpoint = "https://api.pexels.com/v1/search"
        if media_type == "video":
            endpoint = "https://api.pexels.com/videos/search"
        headers = {"Authorization": api_key}
        params = {"query": query, "per_page": limit}
        resp = requests.get(endpoint, headers=headers, params=params, timeout=20)
        resp.raise_for_status()
        data = resp.json()
        assets: List[Dict] = []
        if media_type == "video":
            for item in data.get("videos", []):
                assets.append(
                    {
                        "id": item.get("id"),
                        "preview": item.get("image"),
                        "duration": item.get("duration"),
                        "url": item.get("url"),
                        "type": "video",
                    }
                )
        else:
            for item in data.get("photos", []):
                assets.append(
                    {
                        "id": item.get("id"),
                        "preview": item.get("src", {}).get("medium"),
                        "photographer": item.get("photographer"),
                        "color": item.get("avg_color"),
                        "url": item.get("url"),
                        "type": "image",
                    }
                )
        return assets[:limit]


_service: Optional[BrandKitService] = None


def get_brand_kit_service() -> BrandKitService:
    global _service
    if _service is None:
        _service = BrandKitService()
    return _service
