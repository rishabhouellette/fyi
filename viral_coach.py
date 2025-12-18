"""Viral AI Coach utilities."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict

from logger_config import get_logger
from video_validator import VideoValidator

logger = get_logger(__name__)


@dataclass
class CoachReport:
    hook_score: float
    pacing_score: float
    clarity_score: float
    cta_score: float
    notes: str


class ViralCoach:
    """Provides lightweight creative critiques."""

    def __init__(self) -> None:
        self.validator = VideoValidator()

    def review_script(self, script: str) -> Dict:
        text = (script or "").strip()
        if not text:
            return {"error": "Provide script text"}
        sentences = [line.strip() for line in text.splitlines() if line.strip()]
        hooks = [s for s in sentences if any(word in s.lower() for word in ("secret", "mistake", "steal", "nobody"))]
        ctas = [s for s in sentences if any(word in s.lower() for word in ("comment", "dm", "link", "download"))]
        pacing = min(10.0, len(sentences) * 1.2)
        hook_score = 8.5 if hooks else 5.0
        cta_score = 8.0 if ctas else 4.5
        clarity = 10.0 - min(4.0, len([s for s in sentences if len(s.split()) > 30]))
        suggestions = []
        if not hooks:
            suggestions.append("Add a curiosity hook in your first sentence.")
        if pacing < 6:
            suggestions.append("Break the script into shorter beats.")
        if not ctas:
            suggestions.append("Close with a concrete CTA (comment, link, DM).")
        if clarity < 8:
            suggestions.append("Trim long sentences for easier reading.")
        return {
            "scores": {
                "hook": hook_score,
                "pacing": round(pacing, 1),
                "clarity": round(clarity, 1),
                "cta": cta_score,
            },
            "suggestions": suggestions or ["Looks strong — ready to record!"],
        }

    def review_video(self, video_path: str, platform: str = "instagram") -> Dict:
        if not video_path:
            return {"error": "Select a video file"}
        is_valid, error = self.validator.validate(video_path, platform)
        info = self.validator.get_video_info(video_path)
        return {
            "valid": is_valid,
            "error": error,
            "info": info,
        }


_coach: ViralCoach | None = None


def get_viral_coach() -> ViralCoach:
    global _coach
    if _coach is None:
        _coach = ViralCoach()
    return _coach
