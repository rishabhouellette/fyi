"""AI Engine package providing hooks, scoring, thumbnails, and templates."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType
from typing import TYPE_CHECKING, Callable

# Export ollama_manager directly
from .ollama_manager import get_ollama_manager, OllamaManager

_LEGACY_MODULE: ModuleType | None = None

if TYPE_CHECKING:  # pragma: no cover - typing helper
	from typing import Any


def _load_legacy_module() -> ModuleType:
	"""Load the historical ``ai_engine.py`` module without causing import loops."""

	global _LEGACY_MODULE
	if _LEGACY_MODULE is not None:
		return _LEGACY_MODULE

	module_path = Path(__file__).resolve().parent.parent / "ai_engine.py"
	spec = importlib.util.spec_from_file_location("_ai_engine_legacy", module_path)
	if spec is None or spec.loader is None:  # pragma: no cover - defensive
		raise ImportError(f"Unable to load ai_engine module from {module_path}")

	module = importlib.util.module_from_spec(spec)
	spec.loader.exec_module(module)
	_LEGACY_MODULE = module
	return module


def __getattr__(name: str) -> "Any":  # pragma: no cover - delegation helper
	module = _load_legacy_module()
	try:
		return getattr(module, name)
	except AttributeError as exc:  # mirror normal module behavior
		raise AttributeError(name) from exc


def __dir__() -> list[str]:  # pragma: no cover - convenience for REPL
	module = _load_legacy_module()
	return sorted(set(globals().keys()) | set(dir(module)))
