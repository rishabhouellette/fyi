"""Hook + prompt library for ideation workflows."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, List, Optional

from logger_config import get_logger

logger = get_logger(__name__)


@dataclass
class HookTemplate:
    template_id: str
    label: str
    audience: str
    format: str
    use_case: str
    text: str
    metrics: Dict[str, float]


@dataclass
class PromptTemplate:
    prompt_id: str
    goal: str
    tone: str
    instruction: str
    variables: List[str]


class HookPromptLibrary:
    """Persisted JSON store for hook + prompt templates."""

    def __init__(self, db_path: Path | str = "data/hook_prompt_library.json"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.hooks: List[HookTemplate] = []
        self.prompts: List[PromptTemplate] = []
        self._load_or_seed()

    # ------------------------------------------------------------------
    def list_hooks(self, audience: Optional[str] = None, use_case: Optional[str] = None) -> List[HookTemplate]:
        hooks = self.hooks
        if audience and audience.lower() != "all":
            hooks = [hook for hook in hooks if hook.audience.lower() == audience.lower()]
        if use_case and use_case.lower() != "all":
            hooks = [hook for hook in hooks if hook.use_case.lower() == use_case.lower()]
        return hooks

    def list_prompts(self, goal: Optional[str] = None) -> List[PromptTemplate]:
        prompts = self.prompts
        if goal and goal.lower() != "all":
            prompts = [prompt for prompt in prompts if prompt.goal.lower() == goal.lower()]
        return prompts

    def add_hook(self, hook: HookTemplate) -> None:
        self.hooks.append(hook)
        self._save()

    def add_prompt(self, prompt: PromptTemplate) -> None:
        self.prompts.append(prompt)
        self._save()

    # ------------------------------------------------------------------
    def _load_or_seed(self) -> None:
        if not self.db_path.exists():
            self._seed()
            return
        try:
            payload = json.loads(self.db_path.read_text(encoding="utf-8"))
            self.hooks = [HookTemplate(**hook) for hook in payload.get("hooks", [])]
            self.prompts = [PromptTemplate(**prompt) for prompt in payload.get("prompts", [])]
        except Exception as exc:  # pragma: no cover
            logger.error("Failed to load hook library: %s", exc)
            self.hooks, self.prompts = [], []
            self._seed()

    def _save(self) -> None:
        data = {
            "hooks": [asdict(hook) for hook in self.hooks],
            "prompts": [asdict(prompt) for prompt in self.prompts],
        }
        self.db_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def _seed(self) -> None:
        self.hooks = [
            HookTemplate(
                template_id="hook_problem",
                label="Problem → Discovery",
                audience="saas",
                format="carousel",
                use_case="awareness",
                text="We were losing $42k/month to this onboarding bug (until this fix)",
                metrics={"save_rate": 0.34, "avg_watch": 0.71},
            ),
            HookTemplate(
                template_id="hook_builder",
                label="Builder POV",
                audience="creator",
                format="video",
                use_case="launch",
                text="I built an AI agent that repurposes 30 clips in 13 minutes",
                metrics={"save_rate": 0.28, "avg_watch": 0.64},
            ),
            HookTemplate(
                template_id="hook_myth",
                label="Myth Bust",
                audience="fitness",
                format="video",
                use_case="education",
                text="You don't need 2 hours in the gym — use the 5/25/5 split",
                metrics={"save_rate": 0.41, "avg_watch": 0.79},
            ),
        ]
        self.prompts = [
            PromptTemplate(
                prompt_id="prompt_carousel",
                goal="carousels",
                tone="authoritative",
                instruction=(
                    "You are a senior social strategist. Craft a {slide_count}-slide LinkedIn carousel "
                    "explaining {topic}. Each slide should have a short headline + 2 bullet takeaways."
                ),
                variables=["slide_count", "topic"],
            ),
            PromptTemplate(
                prompt_id="prompt_hook_variations",
                goal="hook_variations",
                tone="energetic",
                instruction=(
                    "Generate 5 hook variations for a {audience} audience about {topic}. "
                    "Use pattern interrupts and curiosity gaps."
                ),
                variables=["audience", "topic"],
            ),
            PromptTemplate(
                prompt_id="prompt_longform",
                goal="longform",
                tone="mentor",
                instruction="Outline a 7-part storytelling thread about {topic} using the PAS framework.",
                variables=["topic"],
            ),
        ]
        self._save()


_library: Optional[HookPromptLibrary] = None


def get_hook_prompt_library() -> HookPromptLibrary:
    global _library
    if _library is None:
        _library = HookPromptLibrary()
    return _library
