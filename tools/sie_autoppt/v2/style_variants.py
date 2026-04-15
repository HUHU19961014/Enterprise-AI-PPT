from __future__ import annotations

import os

SUPPORTED_STYLE_VARIANTS = ("minimal", "standard", "decorative")

_USAGE_STYLE_MAP = {
    "presentation": "standard",
    "proposal": "decorative",
    "training": "minimal",
    "report": "standard",
    "meeting": "minimal",
    "analysis": "standard",
    "narrative": "standard",
}


def select_style_variant(usage_context: str, user_preference: str | None = None) -> str:
    preferred = str(user_preference or "").strip().lower()
    if preferred in SUPPORTED_STYLE_VARIANTS:
        return preferred
    context = str(usage_context or "").strip().lower()
    return _USAGE_STYLE_MAP.get(context, "standard")


def resolve_style_variant(usage_context: str) -> str:
    env_preference = os.environ.get("SIE_AUTOPPT_STYLE_VARIANT", "")
    return select_style_variant(usage_context=usage_context, user_preference=env_preference)
