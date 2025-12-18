"""Clip scoring heuristics for long-form to short-form conversion."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass
class ClipCandidate:
    start: float
    end: float
    transcript: str
    energy_score: float
    emotion_score: float


@dataclass
class ClipScore:
    score: float
    tags: List[str]
    rationale: str


def score_clip(candidate: ClipCandidate) -> ClipScore:
    duration = max(candidate.end - candidate.start, 1.0)
    hook_density = _hook_density(candidate.transcript)
    score = (candidate.energy_score * 0.4) + (candidate.emotion_score * 0.3) + (hook_density * 0.3)
    tags = []
    if hook_density > 0.7:
        tags.append("hook")
    if duration < 30:
        tags.append("short")
    else:
        tags.append("story")
    rationale = f"Density={hook_density:.2f}, energy={candidate.energy_score:.2f}, emotion={candidate.emotion_score:.2f}"
    return ClipScore(score=min(score, 1.0), tags=tags, rationale=rationale)


def _hook_density(transcript: str) -> float:
    keywords = ["imagine", "secret", "what if", "nobody", "stop", "start"]
    hits = sum(1 for kw in keywords if kw in transcript.lower())
    return min(hits / 3.0, 1.0)
