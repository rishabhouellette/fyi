"""Layout template registry for clip overlays."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class Template:
    name: str
    primary_color: str
    secondary_color: str
    font_family: str
    text_position: str


def get_default_templates() -> Dict[str, Template]:
    return {
        "mrbeast": Template(
            name="mrbeast",
            primary_color="#0ea5e9",
            secondary_color="#f97316",
            font_family="Anton",
            text_position="bottom",
        ),
        "documentary": Template(
            name="documentary",
            primary_color="#facc15",
            secondary_color="#0f172a",
            font_family="Inter",
            text_position="top",
        ),
    }


def resolve_template(persona: str) -> Template:
    registry = get_default_templates()
    return registry.get(persona.lower(), registry["documentary"])
