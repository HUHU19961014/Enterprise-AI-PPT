from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Iterable

from ..llm_openai import OpenAIResponsesClient, load_openai_responses_config


@dataclass(frozen=True)
class LLMLayoutDecision:
    layout: str
    confidence: float
    reason: str


def _layout_decision_schema(available_layouts: Iterable[str]) -> dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "recommended_layout": {"type": "string", "enum": list(available_layouts)},
            "confidence": {"type": "number", "minimum": 0, "maximum": 1},
            "reason": {"type": "string", "minLength": 1, "maxLength": 160},
        },
        "required": ["recommended_layout", "confidence", "reason"],
        "additionalProperties": False,
    }


def parse_layout_decision_payload(payload: dict[str, Any]) -> LLMLayoutDecision:
    layout = str(payload.get("recommended_layout", "")).strip()
    reason = str(payload.get("reason", "")).strip()
    confidence = float(payload.get("confidence", 0.0))
    if not layout or not reason:
        raise ValueError("invalid layout decision payload")
    confidence = max(0.0, min(1.0, confidence))
    return LLMLayoutDecision(layout=layout, confidence=confidence, reason=reason)


def decide_layout_with_llm_or_none(
    *,
    slide_title: str,
    intent: str,
    content_items: tuple[str, ...],
    available_layouts: tuple[str, ...],
    client: Any | None = None,
) -> LLMLayoutDecision | None:
    if os.environ.get("SIE_AUTOPPT_ENABLE_LLM_LAYOUT_DECISIONS", "").strip().lower() not in {"1", "true", "yes"}:
        return None
    if not available_layouts:
        return None

    active_client = client
    if active_client is None:
        active_client = OpenAIResponsesClient(load_openai_responses_config())

    content_preview = "\n".join(f"- {item}" for item in content_items[:8]) or "- (no content)"
    developer_prompt = (
        "You are a slide layout decision assistant. Pick the most suitable layout for the given content.\n"
        "Favor readability, visual balance, and content-structure fit."
    )
    user_prompt = (
        f"Slide title: {slide_title}\n"
        f"Intent: {intent}\n"
        f"Content:\n{content_preview}\n"
        f"Available layouts: {', '.join(available_layouts)}\n"
        "Return JSON only."
    )
    try:
        payload = active_client.create_structured_json(
            developer_prompt=developer_prompt,
            user_prompt=user_prompt,
            schema_name="v2_layout_decision",
            schema=_layout_decision_schema(available_layouts),
        )
        decision = parse_layout_decision_payload(payload)
        if decision.layout not in available_layouts:
            return None
        return decision
    except Exception:
        return None
