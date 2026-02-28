"""Pydantic request/response models used across routes."""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel


# ─── Account Management ──────────────────────────────────────────────────────

class AccountCreate(BaseModel):
    platform: str
    name: str
    username: str


class OAuthStart(BaseModel):
    account_name: str
    return_url: Optional[str] = None


class ActiveAccountSetRequest(BaseModel):
    platform: str
    account_id: str


# ─── Scheduling ──────────────────────────────────────────────────────────────

class ScheduleRequest(BaseModel):
    platforms: List[str]
    content: Dict[str, Any]
    scheduledTime: Optional[str] = None
    clips: Optional[List[str]] = []
    file_id: Optional[str] = None
    interval_minutes: Optional[int] = None
    accounts: Optional[Dict[str, str]] = None
    client_request_id: Optional[str] = None


class InstantPublishRequest(BaseModel):
    platforms: List[str]
    content: Dict[str, Any]
    file_id: Optional[str] = None
    clips: Optional[List[str]] = []
    accounts: Optional[Dict[str, str]] = None
    client_request_id: Optional[str] = None


class BulkScheduleItem(BaseModel):
    platforms: List[str]
    title: Optional[str] = ""
    caption: Optional[str] = ""
    file_id: Optional[str] = None
    scheduledTime: Optional[str] = None


class BulkScheduleRequest(BaseModel):
    items: List[BulkScheduleItem]
    smart: bool = True
    interval_minutes: int = 60
    accounts: Optional[Dict[str, str]] = None


class ScheduledPostUpdateRequest(BaseModel):
    title: Optional[str] = None
    caption: Optional[str] = None
    platforms: Optional[List[str]] = None
    scheduled_time: Optional[str] = None
    status: Optional[str] = None


# ─── Platform Uploads ────────────────────────────────────────────────────────

class FacebookUploadRequest(BaseModel):
    account_id: Optional[str] = None
    page_id: Optional[str] = None
    file_id: str
    title: Optional[str] = ""
    description: Optional[str] = ""
    scheduled_publish_time: Optional[int] = None


class YouTubeUploadRequest(BaseModel):
    account_id: Optional[str] = None
    file_id: str
    title: Optional[str] = ""
    description: Optional[str] = ""
    privacy_status: Optional[str] = "private"
    publish_at: Optional[str] = None


class InstagramPublishRequest(BaseModel):
    account_id: Optional[str] = None
    file_id: str
    caption: Optional[str] = ""
    media_type: Optional[str] = "REELS"


# ─── AI ──────────────────────────────────────────────────────────────────────

class AICaptionRequest(BaseModel):
    topic: str
    platform: Optional[str] = "instagram"
    tone: Optional[str] = "casual"
    keywords: Optional[List[str]] = None
    max_length: int = 220
    include_hashtags: bool = True
    hashtags_count: int = 8


class AIHashtagsRequest(BaseModel):
    topic: str
    platform: Optional[str] = "instagram"
    count: int = 12
    include_trending: bool = True


class AIImageRequest(BaseModel):
    prompt: str
    provider: str = "openai"
    size: str = "1024x1024"
    style: Optional[str] = None
    n: int = 1


class AIVideoRequest(BaseModel):
    prompt: str
    provider: str = "runway"
    image_url: Optional[str] = None
    duration: int = 4
    aspect_ratio: str = "16:9"


class AIVoiceRequest(BaseModel):
    text: str
    provider: str = "elevenlabs"
    voice_id: Optional[str] = None
    language: str = "en"


class XYAIPromptRequest(BaseModel):
    goal: str
    platform: Optional[str] = "instagram"
    content_type: Optional[str] = "post"
    tone: Optional[str] = "engaging"
    audience: Optional[str] = None
    niche: Optional[str] = None
    count: int = 3


class XYAITrendRequest(BaseModel):
    niche: Optional[str] = None
    platform: Optional[str] = "instagram"
    country: Optional[str] = "US"


class XYAIChatRequest(BaseModel):
    message: str
    history: list = []
    context: Optional[str] = None
    preferred_model: Optional[str] = None


class XYAIContentPlanRequest(BaseModel):
    niche: str
    platform: Optional[str] = "instagram"
    days: int = 7
    posts_per_day: int = 1
    tone: Optional[str] = "engaging"


# ─── Settings / BYOK ────────────────────────────────────────────────────────

class BYOKSetKeyRequest(BaseModel):
    service: str
    api_key: str


class BYOKDeleteKeyRequest(BaseModel):
    service: str


class PlatformCredentialRequest(BaseModel):
    platform: str
    credentials: dict[str, str]


# ─── Content & Media ─────────────────────────────────────────────────────────

class IngestURLRequest(BaseModel):
    url: str
    extract_type: str = "article"


class RepurposeRequest(BaseModel):
    content: str
    source_type: str = "article"
    target_formats: List[str] = ["tweet", "linkedin", "caption"]
    language: str = "en"


class TranslateRequest(BaseModel):
    text: str
    target_language: str
    source_language: str = "auto"


class ApplyTemplateRequest(BaseModel):
    template_id: str
    variables: Dict[str, str]


class FacelessVideoWithVoiceRequest(BaseModel):
    script: str
    voice_provider: str = "elevenlabs"
    voice_id: Optional[str] = None
    width: int = 1080
    height: int = 1920
    bg_color: str = "black"
    bg_video_url: Optional[str] = None


class FacelessVideoRequest(BaseModel):
    script: str
    width: int = 1080
    height: int = 1920
    fps: int = 30
    bg_color: str = "black"
    max_words_per_caption: int = 7


class VideoProcessRequest(BaseModel):
    file_id: str
    target_clips: int = 3
    quality: str = "high"


class VideoScoreRequest(BaseModel):
    file_id: str


class LinkCreateRequest(BaseModel):
    target_url: str
    slug: Optional[str] = None
