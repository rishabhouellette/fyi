"""Thumbnail generation helpers (stubbed for Phase 2 scaffolding)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List


@dataclass
class ThumbnailVariant:
    path: Path
    palette: List[str]
    caption: str
    confidence: float


def generate_thumbnails(base_frame: Path, *, count: int = 4) -> List[ThumbnailVariant]:
    # Placeholder implementation until SDXL/Comfy integration lands.
    variants: List[ThumbnailVariant] = []
    for idx in range(count):
        variants.append(
            ThumbnailVariant(
                path=base_frame,
                palette=["#0f172a", "#f97316", "#facc15"],
                caption=f"Hook Variant {idx + 1}",
                confidence=0.5,
            )
        )
    return variants
