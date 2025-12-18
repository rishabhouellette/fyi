"""Remix service for FYI Uploader.

Transforms a single source (URL, file, or pasted text) into multiple
platform-ready assets such as Instagram captions, TikTok scripts, or
LinkedIn posts. The implementation is intentionally dependency-light so
it can run inside the existing desktop bundle while still providing
clear extension points for Whisper/LLM integrations later.
"""

from __future__ import annotations

import json
import re
import textwrap
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import requests

from ai_engine import get_ai_engine
from logger_config import get_logger

logger = get_logger(__name__)

try:  # Optional dependency for richer YouTube transcripts
	from youtube_transcript_api import YouTubeTranscriptApi  # type: ignore
except Exception:  # pragma: no cover - graceful fallback when missing
	YouTubeTranscriptApi = None  # type: ignore


REMIX_STORE = Path("data/remix_jobs.json")
REMIX_STORE.parent.mkdir(parents=True, exist_ok=True)


SUPPORTED_PLATFORMS = [
	"instagram",
	"tiktok",
	"youtube",
	"linkedin",
	"twitter",
	"threads",
	"facebook",
	"pinterest",
]


@dataclass
class RemixJob:
	"""Persistent representation of a remix request."""

	source: Dict
	targets: List[str]
	options: Dict
	outputs: Dict[str, Dict]
	created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

	def as_dict(self) -> Dict:
		return {
			"source": self.source,
			"targets": self.targets,
			"options": self.options,
			"outputs": self.outputs,
			"created_at": self.created_at,
		}


class RemixService:
	"""Generate multi-platform assets from a single source."""

	def __init__(self):
		self.ai = get_ai_engine()
		if not REMIX_STORE.exists():
			REMIX_STORE.write_text("[]", encoding="utf-8")

	# ------------------------------------------------------------------
	# Public API
	# ------------------------------------------------------------------
	def remix(self, source: Dict, targets: Optional[List[str]] = None, options: Optional[Dict] = None) -> RemixJob:
		"""Generate content variants for each target platform.

		Args:
			source: {"type": "url|text|file", "value": str}
			targets: list of target platform names; defaults to SUPPORTED_PLATFORMS
			options: misc options like tone, call_to_action, hashtags
		"""

		targets = targets or SUPPORTED_PLATFORMS
		options = options or {}

		raw_text = self._extract_source_text(source)
		if not raw_text:
			raise ValueError("Unable to extract text from provided source")

		summary = self._summarize_text(raw_text)
		key_points = self._extract_keypoints(raw_text)

		outputs: Dict[str, Dict] = {}
		for target in targets:
			try:
				outputs[target] = self._generate_for_platform(
					target.lower(), raw_text, summary, key_points, options
				)
			except Exception as exc:  # pragma: no cover - defensive guard
				logger.error("Remix generation failed for %s: %s", target, exc)
				outputs[target] = {
					"error": str(exc),
					"content": "",
				}

		job = RemixJob(source=source, targets=targets, options=options, outputs=outputs)
		self._persist_job(job)
		return job

	def recent_jobs(self, limit: int = 10) -> List[Dict]:
		"""Return latest remix jobs for UI history."""

		try:
			data = json.loads(REMIX_STORE.read_text(encoding="utf-8"))
			return list(reversed(data))[:limit]
		except Exception as exc:
			logger.error("Failed reading remix history: %s", exc)
			return []

	# ------------------------------------------------------------------
	# Text gathering helpers
	# ------------------------------------------------------------------
	def _extract_source_text(self, source: Dict) -> str:
		s_type = (source or {}).get("type", "text")
		value = (source or {}).get("value", "")

		if s_type == "text":
			return value.strip()
		if s_type == "file":
			path = Path(value)
			if not path.exists():
				raise FileNotFoundError(f"Remix file not found: {path}")
			return path.read_text(encoding="utf-8", errors="ignore")
		if s_type == "url":
			return self._fetch_url_text(value)
		raise ValueError(f"Unsupported source type: {s_type}")

	def _fetch_url_text(self, url: str) -> str:
		if "youtube.com" in url or "youtu.be" in url:
			text = self._fetch_youtube_transcript(url)
			if text:
				return text
		if "tiktok.com" in url:
			try:
				resp = requests.get(url, timeout=10)
				resp.raise_for_status()
				return self._clean_html(resp.text)
			except Exception as exc:
				logger.error("Failed to fetch TikTok data: %s", exc)
		# Fallback: fetch page text
		try:
			resp = requests.get(url, timeout=10)
			resp.raise_for_status()
			return self._clean_html(resp.text)
		except Exception as exc:
			logger.error("Failed to fetch URL for remix: %s", exc)
			return ""

	def _fetch_youtube_transcript(self, url: str) -> str:
		video_id_match = re.search(r"(?:v=|youtu\.be/)([A-Za-z0-9_-]{11})", url)
		if not video_id_match:
			return ""
		video_id = video_id_match.group(1)
		if YouTubeTranscriptApi is None:
			logger.warning("youtube-transcript-api not installed; falling back to metadata scrape")
			return ""
		try:
			transcript = YouTubeTranscriptApi.get_transcript(video_id)
			return " ".join(chunk["text"] for chunk in transcript)
		except Exception as exc:
			logger.error("YouTube transcript fetch failed: %s", exc)
			return ""

	@staticmethod
	def _clean_html(html_text: str) -> str:
		text = re.sub(r"<script.*?</script>", " ", html_text, flags=re.S)
		text = re.sub(r"<style.*?</style>", " ", text, flags=re.S)
		text = re.sub(r"<[^>]+>", " ", text)
		return re.sub(r"\s+", " ", text)

	@staticmethod
	def _summarize_text(text: str, max_sentences: int = 5) -> str:
		sentences = re.split(r"(?<=[.!?])\s+", text.strip())
		top = sentences[:max_sentences]
		return " ".join(top)

	@staticmethod
	def _extract_keypoints(text: str, limit: int = 5) -> List[str]:
		sentences = re.split(r"(?<=[.!?])\s+", text.strip())
		points = []
		for sentence in sentences:
			clean = sentence.strip()
			if not clean:
				continue
			points.append(clean)
			if len(points) >= limit:
				break
		return points

	# ------------------------------------------------------------------
	# Generation helpers
	# ------------------------------------------------------------------
	def _generate_for_platform(
		self,
		platform: str,
		raw_text: str,
		summary: str,
		key_points: List[str],
		options: Dict,
	) -> Dict:
		platform = platform.lower()
		if platform not in SUPPORTED_PLATFORMS:
			raise ValueError(f"Unsupported platform: {platform}")

		tone = options.get("tone", "casual")
		cta = options.get("cta", "Drop your thoughts below ⬇️")
		topic_hint = key_points[0] if key_points else summary[:120]

		if platform == "instagram":
			hashtags = self.ai.generate_hashtags({
				"platform": "instagram",
				"topic": topic_hint,
				"count": 15,
				"trending": True,
			})
			caption = textwrap.shorten(summary, width=1200, placeholder="...")
			caption = f"{caption}\n\n{cta}\n\n{' '.join(hashtags)}"
			return {"type": "caption", "content": caption}

		if platform == "tiktok":
			beats = [
				"Hook", "Context", "Value nugget", "CTA"
			]
			script_lines = []
			for beat, point in zip(beats, key_points + [cta]):
				script_lines.append(f"{beat}: {textwrap.shorten(point, width=120)}")
			return {"type": "script", "content": "\n".join(script_lines)}

		if platform == "youtube":
			hook = textwrap.shorten(key_points[0] if key_points else summary, width=150)
			outline = "\n".join(f"• {p}" for p in key_points)
			description = f"{summary}\n\nKEY TAKEAWAYS:\n{outline}\n\nCTA: {cta}"
			tags = self.ai.generate_hashtags({"platform": "youtube", "topic": topic_hint, "count": 10, "trending": False})
			return {
				"type": "video_outline",
				"content": description,
				"metadata": {"hook": hook, "tags": tags},
			}

		if platform == "linkedin":
			paragraphs = []
			for point in key_points:
				paragraphs.append(textwrap.fill(point, width=500))
			outro = "What are you seeing on your side?" if "?" not in cta else cta
			content = "\n\n".join(paragraphs) + f"\n\n{outro}"
			return {"type": "article", "content": content}

		if platform == "twitter":
			tweets = []
			for point in key_points[:4]:
				tweets.append(textwrap.shorten(point, width=240, placeholder="…"))
			tweets.append(cta[:260])
			return {"type": "thread", "content": "\n\n".join(tweets)}

		if platform == "threads":
			content = textwrap.shorten(summary, width=350, placeholder="…")
			content = f"{content}\n\n{cta}"
			return {"type": "microblog", "content": content}

		if platform == "facebook":
			body = textwrap.shorten(summary, width=2000, placeholder="…")
			hashtags = self.ai.generate_hashtags({"platform": "facebook", "topic": topic_hint, "count": 5, "trending": False})
			return {"type": "caption", "content": f"{body}\n\n{cta}\n{' '.join(hashtags)}"}

		if platform == "pinterest":
			idea = textwrap.shorten(summary, width=500, placeholder="…")
			return {"type": "idea_pin", "content": idea}

		raise ValueError(f"Unhandled platform: {platform}")

	# ------------------------------------------------------------------
	# Persistence helpers
	# ------------------------------------------------------------------
	def _persist_job(self, job: RemixJob) -> None:
		try:
			existing = json.loads(REMIX_STORE.read_text(encoding="utf-8"))
		except Exception:
			existing = []
		existing.append(job.as_dict())
		# keep latest 50 jobs to prevent unbounded growth
		existing = existing[-50:]
		REMIX_STORE.write_text(json.dumps(existing, indent=2), encoding="utf-8")


_remix_service: Optional[RemixService] = None


def get_remix_service() -> RemixService:
	global _remix_service
	if _remix_service is None:
		_remix_service = RemixService()
	return _remix_service

