"""
FYI Social ∞ - AI Engine Package
Local AI pipeline: Ollama + Whisper + CLIP
100% free, 100% local, no API keys needed
"""

__version__ = "2.0.0"

from .ollama_manager import OllamaManager, get_ollama_manager
from .clip_scoring import ClipScoring, get_clip_scoring
from .hook_generator import HookGenerator, get_hook_generator
from .thumbnail_ai import ThumbnailAI, get_thumbnail_ai
from .growth_mentor import GrowthMentor, get_growth_mentor
from .template_engine import TemplateEngine, get_template_engine, TemplateStyle

__all__ = [
    'OllamaManager',
    'ClipScoring',
    'HookGenerator',
    'ThumbnailAI',
    'GrowthMentor',
    'TemplateEngine',
    'TemplateStyle',
    'get_ollama_manager',
    'get_clip_scoring',
    'get_hook_generator',
    'get_thumbnail_ai',
    'get_growth_mentor',
    'get_template_engine'
]
