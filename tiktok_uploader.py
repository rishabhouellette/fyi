"""TikTok Open API uploader.

Handles the multi-step upload workflow used by TikTok's v2 Open API:
1. Initialize an upload session (returns signed upload URL).
2. Upload the binary to the signed URL.
3. Publish or schedule the video with caption + cover.

This module also exposes a simulation mode for development environments
where TikTok credentials are not available yet.
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Dict, List, Optional

import requests

from account_manager import get_account_manager
from logger_config import get_logger

logger = get_logger(__name__)


class TikTokUploader:
	"""Upload helper around TikTok Open API v2."""

	BASE_URL = "https://open-api.tiktok.com"

	def __init__(self, simulate: Optional[bool] = None):
		env_override = os.getenv("TIKTOK_SIMULATE")
		if simulate is None and env_override is not None:
			simulate = env_override not in {"0", "false", "False"}
		self.simulate = simulate if simulate is not None else False
		self.account_manager = get_account_manager()

	# ------------------------------------------------------------------
	# Public API
	# ------------------------------------------------------------------
	def upload_video(
		self,
		account_id: str,
		video_path: str,
		caption: str,
		hashtags: Optional[List[str]] = None,
		schedule_time: Optional[int] = None,
		cover_time_ms: Optional[int] = None,
	) -> Dict:
		"""Upload and optionally schedule a TikTok video."""

		account = self._require_account(account_id)
		video_file = Path(video_path)
		if not video_file.exists():
			raise FileNotFoundError(f"Video file not found: {video_path}")

		open_id = account.page_id or account.username
		if not open_id:
			raise ValueError("TikTok account missing open_id. Store it in page_id or username.")

		caption_text = self._build_caption(caption, hashtags)

		if self.simulate:
			logger.info("[SIM] TikTok upload simulated for %s", video_file.name)
			return {
				"status": "simulated",
				"video": video_file.name,
				"caption": caption_text,
				"scheduled": schedule_time,
			}

		upload_data = self._init_upload(open_id, account.access_token, video_file)
		self._upload_binary(upload_data["upload_url"], video_file)
		publish_resp = self._publish_video(
			open_id=open_id,
			access_token=account.access_token,
			upload_id=upload_data["upload_id"],
			caption=caption_text,
			schedule_time=schedule_time,
			cover_time_ms=cover_time_ms,
		)

		logger.info("TikTok publish response: %s", publish_resp)
		return publish_resp

	# ------------------------------------------------------------------
	# Internal helpers
	# ------------------------------------------------------------------
	def _require_account(self, account_id: str):
		account = self.account_manager.get_account(account_id)
		if not account:
			raise ValueError(f"Account {account_id} not found")
		if not account.access_token:
			raise ValueError("TikTok account missing access token")
		return account

	@staticmethod
	def _build_caption(caption: str, hashtags: Optional[List[str]]) -> str:
		tags = " ".join(tag if tag.startswith("#") else f"#{tag}" for tag in (hashtags or []))
		text = caption.strip()
		if tags:
			text = f"{text} {tags}".strip()
		return text[:2200]

	def _init_upload(self, open_id: str, access_token: str, video_file: Path) -> Dict:
		url = f"{self.BASE_URL}/v2/post/publish/video/init/"
		payload = {
			"open_id": open_id,
			"source_info": {
				"source": "FILE_UPLOAD",
				"video_size": video_file.stat().st_size,
			},
		}
		resp = self._post(url, access_token, payload)
		data = resp.get("data", {})
		upload_url = data.get("upload_url")
		upload_id = data.get("upload_id")
		if not upload_url or not upload_id:
			raise RuntimeError(f"Invalid TikTok init response: {resp}")
		return {"upload_id": upload_id, "upload_url": upload_url}

	def _upload_binary(self, upload_url: str, video_file: Path) -> None:
		with video_file.open("rb") as f:
			response = requests.put(upload_url, data=f, timeout=60)
		if not response.ok:
			raise RuntimeError(f"TikTok upload failed: {response.status_code} {response.text}")

	def _publish_video(
		self,
		open_id: str,
		access_token: str,
		upload_id: str,
		caption: str,
		schedule_time: Optional[int],
		cover_time_ms: Optional[int],
	) -> Dict:
		url = f"{self.BASE_URL}/v2/post/publish/video/"
		post_info: Dict[str, object] = {
			"caption": caption,
			"disable_duet": False,
			"disable_comment": False,
		}
		if schedule_time:
			post_info["schedule_time"] = schedule_time
		if cover_time_ms is not None:
			post_info["cover_time"] = cover_time_ms

		payload = {
			"open_id": open_id,
			"upload_id": upload_id,
			"post_info": post_info,
		}
		return self._post(url, access_token, payload)

	@staticmethod
	def _post(url: str, access_token: str, json_body: Dict) -> Dict:
		headers = {
			"Authorization": f"Bearer {access_token}",
			"Content-Type": "application/json",
		}
		response = requests.post(url, headers=headers, json=json_body, timeout=30)
		try:
			response.raise_for_status()
		except requests.HTTPError as exc:  # pragma: no cover - network errors
			raise RuntimeError(f"TikTok API error: {exc} :: {response.text}") from exc
		return response.json()


_uploader: Optional[TikTokUploader] = None


def get_tiktok_uploader() -> TikTokUploader:
	global _uploader
	if _uploader is None:
		_uploader = TikTokUploader()
	return _uploader

