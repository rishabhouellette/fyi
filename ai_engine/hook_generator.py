"""Generate hooks, CTAs, and first comments using LLM prompts."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

from .ollama_manager import get_ollama_manager


@dataclass
class HookRequest:
    persona: str
    topic: str
    tone: str = "bold"
    count: int = 3


def generate_hooks(req: HookRequest) -> List[str]:
    prompt = (
        f"You are an elite social media strategist for {req.persona}.\n"
        f"Topic: {req.topic}. Tone: {req.tone}.\n"
        f"Produce {req.count} one-sentence hooks with strong pattern interrupts."
    )
    try:
        manager = get_ollama_manager()
        raw = manager.generate("llama3", prompt, options={"temperature": 0.8})
        hooks = [line.strip("- ") for line in raw.splitlines() if line.strip()]
        if hooks:
            return hooks[: req.count]
    except Exception:
        pass
    return [f"{req.topic.title()} – {req.tone.title()} Hook #{i + 1}" for i in range(req.count)]
