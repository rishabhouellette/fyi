"""
FYI Social ∞ - Video Lab Package
Video processing pipeline for creating viral shorts
"""

__version__ = "2.0.0"

from .auto_editor import AutoEditor, get_auto_editor
from .caption_burner import CaptionBurner, CaptionStyle, get_caption_burner
from .broll_inserter import BRollInserter, get_broll_inserter
from .sound_detector import SoundDetector, get_sound_detector
from .voice_clone import VoiceClone, get_voice_clone

__all__ = [
    'AutoEditor',
    'CaptionBurner',
    'CaptionStyle',
    'BRollInserter',
    'SoundDetector',
    'VoiceClone',
    'get_auto_editor',
    'get_caption_burner',
    'get_broll_inserter',
    'get_sound_detector',
    'get_voice_clone'
]
