"""AI video generation service.

Converts plain text scripts into faceless, subtitle-ready short videos by
combining programmatic slides with synthesized voiceovers. The goal is to
offer a self-hosted alternative to paid faceless-video tools while keeping
dependencies lightweight and offline-friendly.
"""

from __future__ import annotations

import contextlib
import os
import textwrap
import tempfile
import wave
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional
from uuid import uuid4

import numpy as np
import pyttsx3
import requests
from moviepy.editor import (
	AudioFileClip,
	CompositeVideoClip,
	ImageClip,
	concatenate_videoclips,
)
from PIL import Image, ImageDraw, ImageFont

from logger_config import get_logger

logger = get_logger(__name__)


@dataclass
class GeneratedSegment:
	"""Represents a single scripted beat."""

	text: str
	duration: float


@dataclass
class VoiceProfile:
	"""Metadata for a selectable voice option."""

	key: str
	label: str
	provider: str  # pyttsx3 | elevenlabs
	voice_id: Optional[str] = None
	settings: Optional[Dict] = None


class VideoAIGenerator:
	"""Generate faceless videos from a script."""

	STYLES: Dict[str, Dict] = {
		"motivation": {
			"background": (20, 20, 20),
			"overlay": (80, 35, 215),
			"text": (255, 255, 255),
		},
		"listicle": {
			"background": (19, 39, 79),
			"overlay": (26, 192, 232),
			"text": (255, 255, 255),
		},
		"news": {
			"background": (10, 10, 10),
			"overlay": (232, 76, 61),
			"text": (245, 245, 245),
		},
	}

	def __init__(self, output_dir: Path | str = "data/library/generated"):
		self.output_dir = Path(output_dir)
		self.output_dir.mkdir(parents=True, exist_ok=True)
		self.font = self._load_font()
		self.voice_profiles = self._discover_voice_profiles()

	# ------------------------------------------------------------------
	# Public API
	# ------------------------------------------------------------------
	def list_styles(self) -> List[str]:
		return list(self.STYLES.keys())

	def list_voices(self) -> List[Dict[str, str]]:
		"""Return available voice options for UI consumption."""
		return [profile.__dict__ for profile in self.voice_profiles.values()]

	def generate_video(
		self,
		script: str,
		style: str = "motivation",
		voice: str = "creator_female",
		burn_subtitles: bool = True,
	) -> Dict:
		script = (script or "").strip()
		if not script:
			raise ValueError("Provide a script to generate video")

		style_key = style.lower()
		theme = self.STYLES.get(style_key, self.STYLES["motivation"])
		voice_profile = self.voice_profiles.get(voice) or next(iter(self.voice_profiles.values()))
		chunks = self._chunk_script(script)
		if not chunks:
			raise ValueError("Unable to parse script into segments")

		image_paths: List[Path] = []
		audio_paths: List[Path] = []
		segments: List[GeneratedSegment] = []
		clips: List[ImageClip] = []
		audio_clip: AudioFileClip | None = None
		video_clip = None
		subtitles: List[Dict[str, float | str]] = []
		elapsed_pointer = 0.0

		try:
			for idx, chunk in enumerate(chunks):
				audio_path = self._synthesize_voice(chunk, idx, voice_profile)
				duration = self._audio_duration(audio_path)
				duration = max(duration, 1.8)  # ensure each beat stays on screen
				image_path = self._render_slide(chunk, theme, idx, len(chunks))

				with Image.open(image_path) as frame_img:
					frame = np.array(frame_img.convert("RGB"))

				clip: ImageClip | CompositeVideoClip = ImageClip(frame).set_duration(duration)
				if burn_subtitles:
					subtitle_clip = self._build_subtitle_clip(chunk, duration, clip.size)
					clip = CompositeVideoClip([clip, subtitle_clip])
				clips.append(clip)
				audio_paths.append(audio_path)
				image_paths.append(image_path)
				segments.append(GeneratedSegment(chunk, round(duration, 2)))
				subtitles.append({
					"text": chunk,
					"start": round(elapsed_pointer, 2),
					"end": round(elapsed_pointer + duration, 2),
				})
				elapsed_pointer += duration

			audio_output = self.output_dir / f"ai_voice_{uuid4().hex}.wav"
			self._concat_audio(audio_paths, audio_output)

			video_output = self.output_dir / f"ai_video_{uuid4().hex}.mp4"
			audio_clip = AudioFileClip(str(audio_output))
			video_clip = concatenate_videoclips(clips, method="compose")
			video_clip = video_clip.set_audio(audio_clip)
			video_clip.write_videofile(
				str(video_output),
				fps=30,
				codec="libx264",
				audio_codec="aac",
				verbose=False,
				logger=None,
			)

			thumbnail: Path | None = None
			srt_path: Path | None = None
			if image_paths:
				thumbnail = self.output_dir / f"thumbnail_{uuid4().hex}.png"
				image_paths[0].replace(thumbnail)
				image_paths = image_paths[1:]
			if subtitles:
				srt_path = self._write_srt(subtitles)

			return {
				"video_path": str(video_output),
				"audio_path": str(audio_output),
				"thumbnail": str(thumbnail) if thumbnail else None,
				"style": style_key,
				"voice": voice_profile.label,
				"subtitle_file": str(srt_path) if srt_path else None,
				"segments": [segment.__dict__ for segment in segments],
			}
		finally:
			for clip in clips:
				with contextlib.suppress(Exception):
					clip.close()
			if audio_clip is not None:
				with contextlib.suppress(Exception):
					audio_clip.close()
			if video_clip is not None:
				with contextlib.suppress(Exception):
					video_clip.close()
			self._cleanup_temp_files(audio_paths, image_paths)

	# ------------------------------------------------------------------
	# Helpers
	# ------------------------------------------------------------------
	def _chunk_script(self, script: str, max_chars: int = 160) -> List[str]:
		sentences = textwrap.wrap(script.replace("\n", " "), width=max_chars)
		return [s.strip() for s in sentences if s.strip()]

	def _synthesize_voice(self, text: str, idx: int, profile: VoiceProfile) -> Path:
		if profile.provider == "elevenlabs":
			return self._synthesize_elevenlabs(text, idx, profile)

		engine = pyttsx3.init()
		if profile.voice_id:
			with contextlib.suppress(Exception):
				engine.setProperty("voice", profile.voice_id)
		if profile.settings and profile.settings.get("rate"):
			with contextlib.suppress(Exception):
				engine.setProperty("rate", profile.settings["rate"])
		tmp_path = Path(tempfile.gettempdir()) / f"fyi_voice_{uuid4().hex}_{idx}.wav"
		engine.save_to_file(text, str(tmp_path))
		engine.runAndWait()
		engine.stop()
		return tmp_path

	def _synthesize_elevenlabs(self, text: str, idx: int, profile: VoiceProfile) -> Path:
		api_key = os.getenv("ELEVENLABS_API_KEY")
		voice_id = profile.voice_id or ""  # API requires explicit voice ID
		if not api_key or not voice_id:
			raise RuntimeError("ElevenLabs voice selected but ELEVENLABS_API_KEY or voice_id is missing")
		url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
		headers = {
			"Accept": "audio/wav",
			"Content-Type": "application/json",
			"xi-api-key": api_key,
		}
		payload = {
			"text": text,
			"voice_settings": profile.settings or {"stability": 0.4, "similarity_boost": 0.7},
		}
		response = requests.post(url, headers=headers, json=payload, timeout=30)
		if not response.ok:
			raise RuntimeError(f"ElevenLabs error: {response.status_code} {response.text}")
		tmp_path = Path(tempfile.gettempdir()) / f"fyi_voice_{uuid4().hex}_{idx}.wav"
		tmp_path.write_bytes(response.content)
		return tmp_path

	def _audio_duration(self, path: Path) -> float:
		with wave.open(str(path), "rb") as wav_file:
			frames = wav_file.getnframes()
			rate = wav_file.getframerate()
			return frames / float(rate)

	def _concat_audio(self, chunk_paths: List[Path], output_path: Path) -> None:
		if not chunk_paths:
			raise ValueError("No audio chunks to merge")

		with wave.open(str(output_path), "wb") as out:
			with wave.open(str(chunk_paths[0]), "rb") as first:
				out.setparams(first.getparams())
			for chunk in chunk_paths:
				with wave.open(str(chunk), "rb") as src:
					out.writeframes(src.readframes(src.getnframes()))

	def _render_slide(self, text: str, theme: Dict, idx: int, total_segments: int, size=(720, 1280)) -> Path:
		img = Image.new("RGB", size, color=theme["background"])
		draw = ImageDraw.Draw(img)

		overlay_height = int(size[1] * 0.65)
		overlay_top = size[1] - overlay_height
		draw.rectangle([0, overlay_top, size[0], size[1]], fill=theme["overlay"], width=0)

		wrapped = textwrap.wrap(text, width=22)
		current_y = overlay_top + 40
		for line in wrapped:
			w, h = draw.textsize(line, font=self.font)
			draw.text(((size[0] - w) / 2, current_y), line, font=self.font, fill=theme["text"])
			current_y += h + 10

		badge = f"Clip {idx + 1}/{total_segments}"
		draw.text((20, 20), badge, font=self.font, fill=(255, 255, 255))

		out_path = Path(tempfile.gettempdir()) / f"fyi_slide_{uuid4().hex}_{idx}.png"
		img.save(out_path)
		return out_path

	def _build_subtitle_clip(self, text: str, duration: float, base_size: tuple[int, int]) -> ImageClip:
		width, height = base_size
		canvas_height = 180
		img = Image.new("RGBA", (width, canvas_height), (0, 0, 0, 0))
		draw = ImageDraw.Draw(img)
		draw.rectangle([20, 20, width - 20, canvas_height - 20], fill=(0, 0, 0, 200))
		wrapped = textwrap.wrap(text, width=32)
		current_y = 40
		for line in wrapped:
			w, h = draw.textsize(line, font=self.font)
			draw.text(((width - w) / 2, current_y), line, font=self.font, fill=(255, 255, 255, 255))
			current_y += h + 8
		arr = np.array(img)
		color = arr[..., :3]
		alpha = arr[..., 3] / 255.0
		mask = ImageClip(alpha, ismask=True).set_duration(duration)
		subtitle = ImageClip(color, ismask=False).set_duration(duration)
		subtitle = subtitle.set_mask(mask)
		subtitle = subtitle.set_position(("center", height - canvas_height - 20))
		return subtitle

	def _cleanup_temp_files(self, audio_paths: List[Path], image_paths: List[Path]) -> None:
		for path in audio_paths + image_paths:
			with contextlib.suppress(Exception):
				path.unlink()

	def _write_srt(self, subtitles: List[Dict[str, float | str]]) -> Path:
		def fmt(ts: float) -> str:
			millis = int(round((ts - int(ts)) * 1000))
			total_seconds = int(ts)
			hours, remainder = divmod(total_seconds, 3600)
			minutes, seconds = divmod(remainder, 60)
			return f"{hours:02d}:{minutes:02d}:{seconds:02d},{millis:03d}"

		srt_path = self.output_dir / f"subtitles_{uuid4().hex}.srt"
		lines = []
		for idx, entry in enumerate(subtitles, start=1):
			start = fmt(entry["start"])
			end = fmt(entry["end"])
			text = entry["text"]
			lines.extend([str(idx), f"{start} --> {end}", text, ""])
		srt_path.write_text("\n".join(lines), encoding="utf-8")
		return srt_path

	def _discover_voice_profiles(self) -> Dict[str, VoiceProfile]:
		profiles: Dict[str, VoiceProfile] = {}
		engine = pyttsx3.init()
		voices = engine.getProperty("voices")
		engine.stop()

		def find_voice(matchers: List[str]) -> Optional[str]:
			for matcher in matchers:
				matcher = matcher.lower()
				for voice in voices:
					name = (voice.name or "").lower()
					if matcher in name or matcher in voice.id.lower():
						return voice.id
			return voices[0].id if voices else None

		profiles["creator_female"] = VoiceProfile(
			key="creator_female",
			label="Creator Female",
			provider="pyttsx3",
			voice_id=find_voice(["female", "zira", "eva"]),
			settings={"rate": 190},
		)
		profiles["creator_male"] = VoiceProfile(
			key="creator_male",
			label="Creator Male",
			provider="pyttsx3",
			voice_id=find_voice(["male", "guy", "david"]),
			settings={"rate": 185},
		)
		profiles["narrator_deep"] = VoiceProfile(
			key="narrator_deep",
			label="Narrator Deep",
			provider="pyttsx3",
			voice_id=find_voice(["baritone", "hazen", "rich"]),
			settings={"rate": 165},
		)

		api_key = os.getenv("ELEVENLABS_API_KEY")
		voice_id = os.getenv("ELEVENLABS_VOICE_ID")
		if api_key and voice_id:
			profiles["elevenlabs_signature"] = VoiceProfile(
				key="elevenlabs_signature",
				label="ElevenLabs Signature",
				provider="elevenlabs",
				voice_id=voice_id,
				settings={"stability": 0.5, "similarity_boost": 0.8},
			)

		return profiles

	def _load_font(self) -> ImageFont.FreeTypeFont:
		possible = [
			Path("C:/Windows/Fonts/SegoeUIBold.ttf"),
			Path("C:/Windows/Fonts/seguiemj.ttf"),
			Path("/System/Library/Fonts/SFNSDisplay.ttf"),
		]
		for font_path in possible:
			if font_path.exists():
				return ImageFont.truetype(str(font_path), size=42)
		return ImageFont.load_default()


_video_ai_generator: VideoAIGenerator | None = None


def get_video_ai_generator() -> VideoAIGenerator:
	global _video_ai_generator
	if _video_ai_generator is None:
		_video_ai_generator = VideoAIGenerator()
	return _video_ai_generator

