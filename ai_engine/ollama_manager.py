"""Utilities to manage local Ollama instances for text+vision inference."""

from __future__ import annotations

import json
import subprocess
import threading
from pathlib import Path
from typing import Dict, List, Optional

from logger_config import get_logger

logger = get_logger(__name__)


class OllamaManager:
    """Simple wrapper around the `ollama` CLI with caching."""

    def __init__(self, binary: str = "ollama") -> None:
        self.binary = binary
        self._lock = threading.Lock()
        self._models_cache: Optional[List[str]] = None

    def list_models(self, force_refresh: bool = False) -> List[str]:
        if self._models_cache is not None and not force_refresh:
            return self._models_cache
        output = self._run(["list", "--json"])
        models: List[str] = []
        for line in output.splitlines():
            try:
                payload = json.loads(line)
                models.append(payload.get("name", ""))
            except json.JSONDecodeError:
                logger.warning("Invalid Ollama list output: %s", line)
        self._models_cache = [m for m in models if m]
        return self._models_cache

    def pull(self, model: str) -> None:
        logger.info("Pulling Ollama model %s", model)
        self._run(["pull", model])
        self.list_models(force_refresh=True)

    def generate(self, model: str, prompt: str, *, options: Optional[Dict] = None) -> str:
        payload = {"model": model, "prompt": prompt}
        if options:
            payload["options"] = options
        output = self._run(["run", model], input_data=json.dumps(payload))
        return output

    def is_ollama_installed(self) -> bool:
        """Check if Ollama is installed on the system."""
        try:
            result = subprocess.run(
                [self.binary, "--version"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
                timeout=5,
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def list_installed_models(self) -> List[str]:
        """Get list of installed Ollama models."""
        try:
            return self.list_models()
        except Exception as e:
            logger.warning("Failed to list Ollama models: %s", e)
            return []

    def setup_recommended_models(self) -> None:
        """Pull recommended models for FYI Social."""
        recommended = ["llama3.2:latest", "llava:latest"]
        for model in recommended:
            try:
                logger.info("Setting up model: %s", model)
                self.pull(model)
            except Exception as e:
                logger.error("Failed to pull model %s: %s", model, e)

    def _run(self, args: List[str], input_data: Optional[str] = None) -> str:
        cmd = [self.binary] + args
        logger.debug("Running: %s", " ".join(cmd))
        proc = subprocess.run(
            cmd,
            input=input_data.encode("utf-8") if input_data else None,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if proc.returncode != 0:
            raise RuntimeError(proc.stderr.decode("utf-8", errors="ignore"))
        return proc.stdout.decode("utf-8", errors="ignore")


_default_manager: Optional[OllamaManager] = None


def get_ollama_manager() -> OllamaManager:
    global _default_manager
    if _default_manager is None:
        _default_manager = OllamaManager()
    return _default_manager
