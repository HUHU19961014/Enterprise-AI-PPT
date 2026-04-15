from __future__ import annotations

from typing import Any


def strip_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def normalize_string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    normalized: list[str] = []
    for item in value:
        text = strip_text(item)
        if text:
            normalized.append(text)
    return normalized


def normalize_data_sources(value: Any) -> list[dict[str, str]]:
    if not isinstance(value, list):
        return []
    normalized: list[dict[str, str]] = []
    for item in value:
        if not isinstance(item, dict):
            continue
        claim = strip_text(item.get("claim"))
        source = strip_text(item.get("source"))
        confidence = strip_text(item.get("confidence")).lower() or "medium"
        if not claim or not source:
            continue
        if confidence not in {"high", "medium", "low"}:
            confidence = "medium"
        normalized.append({"claim": claim, "source": source, "confidence": confidence})
    return normalized


def normalize_object_list(
    value: Any, *, required_keys: list[str], optional_keys: list[str] | None = None
) -> list[dict[str, str]]:
    if not isinstance(value, list):
        return []
    optional = optional_keys or []
    normalized_items: list[dict[str, str]] = []
    for item in value:
        if not isinstance(item, dict):
            continue
        normalized: dict[str, str] = {}
        missing_required = False
        for key in required_keys:
            text = strip_text(item.get(key))
            if not text:
                missing_required = True
                break
            normalized[key] = text
        if missing_required:
            continue
        for key in optional:
            text = strip_text(item.get(key))
            if text:
                normalized[key] = text
        normalized_items.append(normalized)
    return normalized_items
