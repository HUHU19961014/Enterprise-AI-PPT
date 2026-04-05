from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class ContentProfile:
    item_count: int
    avg_chars: int
    max_chars: int
    total_chars: int
    density: str
    has_long_item: bool


DEFAULT_DENSITY_THRESHOLDS = {
    "compact": 60,
    "balanced": 90,
    "dense": 120,
}


def normalize_text_length(text: str) -> int:
    return len(re.sub(r"\s+", " ", text or "").strip())


def classify_density(avg_chars: int, max_chars: int, thresholds: dict[str, int] | None = None) -> str:
    active = {**DEFAULT_DENSITY_THRESHOLDS, **(thresholds or {})}
    signal = max(avg_chars, max_chars)
    if signal <= active["compact"]:
        return "compact"
    if signal <= active["balanced"]:
        return "balanced"
    return "dense"


def profile_bullets(bullets: list[str], thresholds: dict[str, int] | None = None) -> ContentProfile:
    lengths = [normalize_text_length(item) for item in bullets if normalize_text_length(item) > 0]
    if not lengths:
        return ContentProfile(
            item_count=0,
            avg_chars=0,
            max_chars=0,
            total_chars=0,
            density="compact",
            has_long_item=False,
        )

    total_chars = sum(lengths)
    avg_chars = round(total_chars / len(lengths))
    max_chars = max(lengths)
    density = classify_density(avg_chars, max_chars, thresholds=thresholds)
    dense_threshold = {**DEFAULT_DENSITY_THRESHOLDS, **(thresholds or {})}["balanced"]
    return ContentProfile(
        item_count=len(lengths),
        avg_chars=avg_chars,
        max_chars=max_chars,
        total_chars=total_chars,
        density=density,
        has_long_item=max_chars > dense_threshold,
    )
