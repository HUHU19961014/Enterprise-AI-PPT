from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .schema import SUPPORTED_THEMES, ValidatedDeck, validate_deck_payload


SUPPORTED_SLIDE_INTENTS = (
    "cover",
    "section",
    "narrative",
    "comparison",
    "framework",
    "analysis",
    "summary",
    "conclusion",
)

SUPPORTED_BLOCK_KINDS = (
    "bullets",
    "comparison",
    "image",
    "statement",
    "timeline",
    "cards",
    "stats",
    "matrix",
)


@dataclass(frozen=True)
class SemanticSlideFeatures:
    slide_id: str
    title: str
    intent: str
    subtitle: str | None
    key_message: str | None
    statements: tuple[str, ...]
    bullet_blocks: tuple[dict[str, Any], ...]
    timeline_blocks: tuple[dict[str, Any], ...]
    card_blocks: tuple[dict[str, Any], ...]
    stat_blocks: tuple[dict[str, Any], ...]
    matrix_blocks: tuple[dict[str, Any], ...]
    comparison: dict[str, Any] | None
    image: dict[str, Any] | None
    content_items: tuple[str, ...]


@dataclass(frozen=True)
class SemanticLayoutPlan:
    slide_id: str
    layout: str
    reason: str


def build_semantic_deck_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "meta": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "minLength": 1, "maxLength": 80},
                    "theme": {"type": "string", "enum": list(SUPPORTED_THEMES)},
                    "language": {"type": "string", "minLength": 2, "maxLength": 16},
                    "author": {"type": "string", "minLength": 1, "maxLength": 40},
                    "version": {"type": "string", "minLength": 1, "maxLength": 10},
                },
                "required": ["title", "theme", "language", "author", "version"],
                "additionalProperties": False,
            },
            "slides": {
                "type": "array",
                "minItems": 1,
                "maxItems": 20,
                "items": {
                    "type": "object",
                    "properties": {
                        "slide_id": {"type": "string", "minLength": 1, "maxLength": 40},
                        "title": {"type": "string", "minLength": 2, "maxLength": 60},
                        "intent": {"type": "string", "enum": list(SUPPORTED_SLIDE_INTENTS)},
                        "subtitle": {"type": "string", "maxLength": 80},
                        "key_message": {"type": "string", "maxLength": 100},
                        "blocks": {
                            "type": "array",
                            "minItems": 0,
                            "maxItems": 4,
                            "items": {
                                "anyOf": [
                                    {
                                        "type": "object",
                                        "properties": {
                                            "kind": {"const": "bullets"},
                                            "heading": {"type": "string", "maxLength": 24},
                                            "items": {
                                                "type": "array",
                                                "minItems": 1,
                                                "maxItems": 8,
                                                "items": {"type": "string", "minLength": 2, "maxLength": 70},
                                            },
                                        },
                                        "required": ["kind", "items"],
                                        "additionalProperties": False,
                                    },
                                    {
                                        "type": "object",
                                        "properties": {
                                            "kind": {"const": "comparison"},
                                            "left_heading": {"type": "string", "minLength": 1, "maxLength": 24},
                                            "left_items": {
                                                "type": "array",
                                                "minItems": 1,
                                                "maxItems": 6,
                                                "items": {"type": "string", "minLength": 2, "maxLength": 60},
                                            },
                                            "right_heading": {"type": "string", "minLength": 1, "maxLength": 24},
                                            "right_items": {
                                                "type": "array",
                                                "minItems": 1,
                                                "maxItems": 6,
                                                "items": {"type": "string", "minLength": 2, "maxLength": 60},
                                            },
                                        },
                                        "required": ["kind", "left_heading", "left_items", "right_heading", "right_items"],
                                        "additionalProperties": False,
                                    },
                                    {
                                        "type": "object",
                                        "properties": {
                                            "kind": {"const": "image"},
                                            "mode": {"type": "string", "enum": ["placeholder", "local_path"]},
                                            "caption": {"type": "string", "maxLength": 40},
                                            "path": {"type": "string", "maxLength": 240},
                                        },
                                        "required": ["kind", "mode"],
                                        "additionalProperties": False,
                                    },
                                    {
                                        "type": "object",
                                        "properties": {
                                            "kind": {"const": "statement"},
                                            "text": {"type": "string", "minLength": 2, "maxLength": 100},
                                        },
                                        "required": ["kind", "text"],
                                        "additionalProperties": False,
                                    },
                                    {
                                        "type": "object",
                                        "properties": {
                                            "kind": {"const": "timeline"},
                                            "heading": {"type": "string", "maxLength": 24},
                                            "stages": {
                                                "type": "array",
                                                "minItems": 2,
                                                "maxItems": 6,
                                                "items": {
                                                    "type": "object",
                                                    "properties": {
                                                        "title": {"type": "string", "minLength": 1, "maxLength": 24},
                                                        "detail": {"type": "string", "maxLength": 60},
                                                    },
                                                    "required": ["title"],
                                                    "additionalProperties": False,
                                                },
                                            },
                                        },
                                        "required": ["kind", "stages"],
                                        "additionalProperties": False,
                                    },
                                    {
                                        "type": "object",
                                        "properties": {
                                            "kind": {"const": "cards"},
                                            "heading": {"type": "string", "maxLength": 24},
                                            "cards": {
                                                "type": "array",
                                                "minItems": 2,
                                                "maxItems": 4,
                                                "items": {
                                                    "type": "object",
                                                    "properties": {
                                                        "title": {"type": "string", "minLength": 1, "maxLength": 24},
                                                        "body": {"type": "string", "maxLength": 60},
                                                    },
                                                    "required": ["title"],
                                                    "additionalProperties": False,
                                                },
                                            },
                                        },
                                        "required": ["kind", "cards"],
                                        "additionalProperties": False,
                                    },
                                    {
                                        "type": "object",
                                        "properties": {
                                            "kind": {"const": "stats"},
                                            "heading": {"type": "string", "maxLength": 24},
                                            "metrics": {
                                                "type": "array",
                                                "minItems": 2,
                                                "maxItems": 6,
                                                "items": {
                                                    "type": "object",
                                                    "properties": {
                                                        "label": {"type": "string", "minLength": 1, "maxLength": 24},
                                                        "value": {"type": "string", "minLength": 1, "maxLength": 24},
                                                        "note": {"type": "string", "maxLength": 40},
                                                    },
                                                    "required": ["label", "value"],
                                                    "additionalProperties": False,
                                                },
                                            },
                                        },
                                        "required": ["kind", "metrics"],
                                        "additionalProperties": False,
                                    },
                                    {
                                        "type": "object",
                                        "properties": {
                                            "kind": {"const": "matrix"},
                                            "heading": {"type": "string", "maxLength": 24},
                                            "x_axis": {"type": "string", "maxLength": 24},
                                            "y_axis": {"type": "string", "maxLength": 24},
                                            "cells": {
                                                "type": "array",
                                                "minItems": 2,
                                                "maxItems": 4,
                                                "items": {
                                                    "type": "object",
                                                    "properties": {
                                                        "title": {"type": "string", "minLength": 1, "maxLength": 24},
                                                        "body": {"type": "string", "maxLength": 60},
                                                    },
                                                    "required": ["title"],
                                                    "additionalProperties": False,
                                                },
                                            },
                                        },
                                        "required": ["kind", "cells"],
                                        "additionalProperties": False,
                                    },
                                ]
                            },
                        },
                    },
                    "required": ["slide_id", "title", "intent", "blocks"],
                    "additionalProperties": False,
                },
            },
        },
        "required": ["meta", "slides"],
        "additionalProperties": False,
    }


def _strip_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    result: list[str] = []
    for item in value:
        text = _strip_text(item)
        if text:
            result.append(text)
    return result


def _normalize_timeline_stages(value: Any) -> list[dict[str, str]]:
    if not isinstance(value, list):
        return []
    result: list[dict[str, str]] = []
    for item in value:
        if not isinstance(item, dict):
            continue
        title = _strip_text(item.get("title"))
        detail = _strip_text(item.get("detail"))
        if title:
            result.append({"title": title, **({"detail": detail} if detail else {})})
    return result


def _normalize_cards(value: Any) -> list[dict[str, str]]:
    if not isinstance(value, list):
        return []
    result: list[dict[str, str]] = []
    for item in value:
        if not isinstance(item, dict):
            continue
        title = _strip_text(item.get("title"))
        body = _strip_text(item.get("body"))
        if title:
            result.append({"title": title, **({"body": body} if body else {})})
    return result


def _normalize_metrics(value: Any) -> list[dict[str, str]]:
    if not isinstance(value, list):
        return []
    result: list[dict[str, str]] = []
    for item in value:
        if not isinstance(item, dict):
            continue
        label = _strip_text(item.get("label"))
        metric_value = _strip_text(item.get("value"))
        note = _strip_text(item.get("note"))
        if label and metric_value:
            result.append({"label": label, "value": metric_value, **({"note": note} if note else {})})
    return result


def _normalize_matrix_cells(value: Any) -> list[dict[str, str]]:
    if not isinstance(value, list):
        return []
    result: list[dict[str, str]] = []
    for item in value:
        if not isinstance(item, dict):
            continue
        title = _strip_text(item.get("title"))
        body = _strip_text(item.get("body"))
        if title:
            result.append({"title": title, **({"body": body} if body else {})})
    return result


def _normalize_semantic_payload(
    payload: dict[str, Any],
    *,
    default_title: str,
    default_theme: str,
    default_language: str,
    default_author: str,
) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("semantic deck payload must be a JSON object.")

    meta = payload.get("meta", {})
    if not isinstance(meta, dict):
        meta = {}
    normalized_meta = {
        "title": _strip_text(meta.get("title")) or default_title,
        "theme": _strip_text(meta.get("theme")) or default_theme,
        "language": _strip_text(meta.get("language")) or default_language,
        "author": _strip_text(meta.get("author")) or default_author,
        "version": _strip_text(meta.get("version")) or "2.0",
    }

    raw_slides = payload.get("slides", [])
    if not isinstance(raw_slides, list):
        raise ValueError("slides must be a list.")

    normalized_slides: list[dict[str, Any]] = []
    for index, raw_slide in enumerate(raw_slides, start=1):
        if not isinstance(raw_slide, dict):
            raise ValueError(f"slide {index} must be an object.")
        slide_id = _strip_text(raw_slide.get("slide_id")) or f"s{index}"
        title = _strip_text(raw_slide.get("title"))
        intent = _strip_text(raw_slide.get("intent"))
        subtitle = _strip_text(raw_slide.get("subtitle")) or None
        key_message = _strip_text(raw_slide.get("key_message")) or None
        raw_blocks = raw_slide.get("blocks", [])
        if not isinstance(raw_blocks, list):
            raise ValueError(f"slide {slide_id} blocks must be a list.")

        blocks: list[dict[str, Any]] = []
        for raw_block in raw_blocks:
            if not isinstance(raw_block, dict):
                raise ValueError(f"slide {slide_id} contains a non-object block.")
            kind = _strip_text(raw_block.get("kind"))
            if kind == "bullets":
                items = _string_list(raw_block.get("items"))
                if not items:
                    raise ValueError(f"slide {slide_id} bullets block must include items.")
                blocks.append(
                    {
                        "kind": "bullets",
                        "heading": _strip_text(raw_block.get("heading")) or None,
                        "items": items,
                    }
                )
            elif kind == "comparison":
                left_items = _string_list(raw_block.get("left_items"))
                right_items = _string_list(raw_block.get("right_items"))
                if not left_items or not right_items:
                    raise ValueError(f"slide {slide_id} comparison block must include both columns.")
                blocks.append(
                    {
                        "kind": "comparison",
                        "left_heading": _strip_text(raw_block.get("left_heading")),
                        "left_items": left_items,
                        "right_heading": _strip_text(raw_block.get("right_heading")),
                        "right_items": right_items,
                    }
                )
            elif kind == "image":
                mode = _strip_text(raw_block.get("mode")) or "placeholder"
                blocks.append(
                    {
                        "kind": "image",
                        "mode": mode,
                        "caption": _strip_text(raw_block.get("caption")) or None,
                        "path": _strip_text(raw_block.get("path")) or None,
                    }
                )
            elif kind == "statement":
                text = _strip_text(raw_block.get("text"))
                if not text:
                    raise ValueError(f"slide {slide_id} statement block must include text.")
                blocks.append({"kind": "statement", "text": text})
            elif kind == "timeline":
                stages = _normalize_timeline_stages(raw_block.get("stages"))
                if len(stages) < 2:
                    raise ValueError(f"slide {slide_id} timeline block must include at least 2 stages.")
                blocks.append(
                    {
                        "kind": "timeline",
                        "heading": _strip_text(raw_block.get("heading")) or None,
                        "stages": stages,
                    }
                )
            elif kind == "cards":
                cards = _normalize_cards(raw_block.get("cards"))
                if len(cards) < 2:
                    raise ValueError(f"slide {slide_id} cards block must include at least 2 cards.")
                blocks.append(
                    {
                        "kind": "cards",
                        "heading": _strip_text(raw_block.get("heading")) or None,
                        "cards": cards,
                    }
                )
            elif kind == "stats":
                metrics = _normalize_metrics(raw_block.get("metrics"))
                if len(metrics) < 2:
                    raise ValueError(f"slide {slide_id} stats block must include at least 2 metrics.")
                blocks.append(
                    {
                        "kind": "stats",
                        "heading": _strip_text(raw_block.get("heading")) or None,
                        "metrics": metrics,
                    }
                )
            elif kind == "matrix":
                cells = _normalize_matrix_cells(raw_block.get("cells"))
                if len(cells) < 2:
                    raise ValueError(f"slide {slide_id} matrix block must include at least 2 cells.")
                blocks.append(
                    {
                        "kind": "matrix",
                        "heading": _strip_text(raw_block.get("heading")) or None,
                        "x_axis": _strip_text(raw_block.get("x_axis")) or None,
                        "y_axis": _strip_text(raw_block.get("y_axis")) or None,
                        "cells": cells,
                    }
                )
            else:
                raise ValueError(f"slide {slide_id} has unsupported block kind: {kind}")

        normalized_slides.append(
            {
                "slide_id": slide_id,
                "title": title,
                "intent": intent,
                "subtitle": subtitle,
                "key_message": key_message,
                "blocks": blocks,
            }
        )

    return {"meta": normalized_meta, "slides": normalized_slides}


def _split_evenly(items: list[str]) -> tuple[list[str], list[str]]:
    midpoint = (len(items) + 1) // 2
    return items[:midpoint], items[midpoint:]


def _statement_texts(blocks: list[dict[str, Any]]) -> list[str]:
    return [_strip_text(block.get("text")) for block in blocks if block.get("kind") == "statement" and _strip_text(block.get("text"))]


def _bullet_blocks(blocks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [block for block in blocks if block.get("kind") == "bullets"]


def _timeline_blocks(blocks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [block for block in blocks if block.get("kind") == "timeline"]


def _card_blocks(blocks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [block for block in blocks if block.get("kind") == "cards"]


def _stat_blocks(blocks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [block for block in blocks if block.get("kind") == "stats"]


def _matrix_blocks(blocks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [block for block in blocks if block.get("kind") == "matrix"]


def _comparison_block(blocks: list[dict[str, Any]]) -> dict[str, Any] | None:
    for block in blocks:
        if block.get("kind") == "comparison":
            return block
    return None


def _image_block(blocks: list[dict[str, Any]]) -> dict[str, Any] | None:
    for block in blocks:
        if block.get("kind") == "image":
            return block
    return None


def _flatten_timeline_block(block: dict[str, Any]) -> list[str]:
    result: list[str] = []
    for stage in block["stages"]:
        text = stage["title"]
        if stage.get("detail"):
            text = f"{text}: {stage['detail']}"
        result.append(text)
    return result


def _flatten_card_block(block: dict[str, Any]) -> list[str]:
    result: list[str] = []
    for card in block["cards"]:
        text = card["title"]
        if card.get("body"):
            text = f"{text}: {card['body']}"
        result.append(text)
    return result


def _flatten_stat_block(block: dict[str, Any]) -> list[str]:
    result: list[str] = []
    for metric in block["metrics"]:
        text = f"{metric['label']}: {metric['value']}"
        if metric.get("note"):
            text = f"{text} ({metric['note']})"
        result.append(text)
    return result


def _flatten_matrix_block(block: dict[str, Any]) -> list[str]:
    result: list[str] = []
    for cell in block["cells"]:
        text = cell["title"]
        if cell.get("body"):
            text = f"{text}: {cell['body']}"
        result.append(text)
    return result


def _compile_semantic_slide_legacy_unused(slide: dict[str, Any]) -> dict[str, Any]:
    slide_id = slide["slide_id"]
    title = slide["title"]
    intent = slide["intent"]
    subtitle = slide.get("subtitle")
    key_message = slide.get("key_message")
    blocks = slide["blocks"]
    statements = _statement_texts(blocks)
    bullet_blocks = _bullet_blocks(blocks)
    comparison = _comparison_block(blocks)
    image = _image_block(blocks)

    if intent in {"cover", "section"}:
        payload = {
            "slide_id": slide_id,
            "layout": "section_break",
            "title": title,
        }
        if subtitle or key_message:
            payload["subtitle"] = subtitle or key_message
        return payload

    if comparison:
        return {
            "slide_id": slide_id,
            "layout": "two_columns",
            "title": title,
            "left": {
                "heading": comparison["left_heading"],
                "items": comparison["left_items"],
            },
            "right": {
                "heading": comparison["right_heading"],
                "items": comparison["right_items"],
            },
        }

    if image:
        content: list[str] = []
        if key_message:
            content.append(key_message)
        if statements:
            content.extend(statements)
        for block in bullet_blocks:
            content.extend(block["items"])
        content = [item for item in content if item][:8]
        if not content:
            content = [subtitle or title]
        return {
            "slide_id": slide_id,
            "layout": "title_image",
            "title": title,
            "content": content,
            "image": {
                "mode": image.get("mode", "placeholder"),
                **({"caption": image["caption"]} if image.get("caption") else {}),
                **({"path": image["path"]} if image.get("path") else {}),
            },
        }

    if intent in {"summary", "conclusion"} and not bullet_blocks and len(statements) <= 1:
        return {
            "slide_id": slide_id,
            "layout": "title_only",
            "title": statements[0] if statements else (key_message or title),
        }

    if len(bullet_blocks) >= 2:
        left_block = bullet_blocks[0]
        right_block = bullet_blocks[1]
        return {
            "slide_id": slide_id,
            "layout": "two_columns",
            "title": title,
            "left": {
                "heading": left_block.get("heading") or "左侧要点",
                "items": left_block["items"][:6],
            },
            "right": {
                "heading": right_block.get("heading") or "右侧要点",
                "items": right_block["items"][:6],
            },
        }

    content_items: list[str] = []
    if key_message:
        content_items.append(key_message)
    if statements:
        content_items.extend(statements)
    for block in bullet_blocks:
        content_items.extend(block["items"])
    if subtitle and not content_items:
        content_items.append(subtitle)
    content_items = [item for item in content_items if item]

    if len(content_items) > 6:
        left_items, right_items = _split_evenly(content_items)
        heading = bullet_blocks[0].get("heading") if bullet_blocks else ""
        return {
            "slide_id": slide_id,
            "layout": "two_columns",
            "title": title,
            "left": {
                "heading": heading or "核心要点",
                "items": left_items[:6],
            },
            "right": {
                "heading": "进一步展开",
                "items": right_items[:6] or [subtitle or title],
            },
        }

    if not content_items:
        content_items = [subtitle or title]

    return {
        "slide_id": slide_id,
        "layout": "title_content",
        "title": title,
        "content": content_items[:10],
    }


def _build_slide_features(slide: dict[str, Any]) -> SemanticSlideFeatures:
    blocks = slide["blocks"]
    statements = tuple(_statement_texts(blocks))
    bullet_blocks = tuple(_bullet_blocks(blocks))
    timeline_blocks = tuple(_timeline_blocks(blocks))
    card_blocks = tuple(_card_blocks(blocks))
    stat_blocks = tuple(_stat_blocks(blocks))
    matrix_blocks = tuple(_matrix_blocks(blocks))
    content_items: list[str] = []
    if slide.get("key_message"):
        content_items.append(slide["key_message"])
    content_items.extend(statements)
    for block in bullet_blocks:
        content_items.extend(block["items"])
    for block in timeline_blocks:
        content_items.extend(_flatten_timeline_block(block))
    for block in card_blocks:
        content_items.extend(_flatten_card_block(block))
    for block in stat_blocks:
        content_items.extend(_flatten_stat_block(block))
    for block in matrix_blocks:
        content_items.extend(_flatten_matrix_block(block))
    if slide.get("subtitle") and not content_items:
        content_items.append(slide["subtitle"])
    return SemanticSlideFeatures(
        slide_id=slide["slide_id"],
        title=slide["title"],
        intent=slide["intent"],
        subtitle=slide.get("subtitle"),
        key_message=slide.get("key_message"),
        statements=statements,
        bullet_blocks=bullet_blocks,
        timeline_blocks=timeline_blocks,
        card_blocks=card_blocks,
        stat_blocks=stat_blocks,
        matrix_blocks=matrix_blocks,
        comparison=_comparison_block(blocks),
        image=_image_block(blocks),
        content_items=tuple(item for item in content_items if item),
    )


def plan_semantic_slide_layout(slide: dict[str, Any]) -> SemanticLayoutPlan:
    features = _build_slide_features(slide)

    if features.intent in {"cover", "section"}:
        return SemanticLayoutPlan(features.slide_id, "section_break", "section-intent")

    candidates: list[tuple[int, str, str]] = []
    if features.comparison:
        candidates.append((100, "two_columns", "comparison-block"))
    if features.image:
        candidates.append((90, "title_image", "image-block"))
    if features.intent in {"summary", "conclusion"} and not features.bullet_blocks and len(features.statements) <= 1:
        candidates.append((85, "title_only", "single-conclusion-statement"))
    if len(features.card_blocks) == 1 and len(features.card_blocks[0]["cards"]) == 2 and not features.bullet_blocks:
        candidates.append((82, "two_columns", "cards-pair"))
    if len(features.stat_blocks) == 1 and len(features.stat_blocks[0]["metrics"]) == 2 and not features.bullet_blocks:
        candidates.append((81, "two_columns", "stats-pair"))
    if len(features.matrix_blocks) == 1:
        candidates.append((79, "two_columns", "matrix-block"))
    if len(features.bullet_blocks) >= 2:
        candidates.append((80, "two_columns", "multi-block-bullets"))
    if features.timeline_blocks and len(features.timeline_blocks[0]["stages"]) >= 4:
        candidates.append((76, "two_columns", "dense-timeline"))
    if len(features.content_items) > 6:
        candidates.append((70, "two_columns", "dense-content"))
    if features.content_items:
        candidates.append((60, "title_content", "default-content"))
    else:
        candidates.append((50, "title_content", "fallback-content"))

    _, layout, reason = max(candidates, key=lambda item: item[0])
    return SemanticLayoutPlan(features.slide_id, layout, reason)


def _compile_semantic_slide(slide: dict[str, Any]) -> dict[str, Any]:
    features = _build_slide_features(slide)
    plan = plan_semantic_slide_layout(slide)

    if plan.layout == "section_break":
        payload = {
            "slide_id": features.slide_id,
            "layout": "section_break",
            "title": features.title,
        }
        if features.subtitle or features.key_message:
            payload["subtitle"] = features.subtitle or features.key_message
        return payload

    if plan.layout == "two_columns" and features.comparison:
        return {
            "slide_id": features.slide_id,
            "layout": "two_columns",
            "title": features.title,
            "left": {
                "heading": features.comparison["left_heading"],
                "items": features.comparison["left_items"],
            },
            "right": {
                "heading": features.comparison["right_heading"],
                "items": features.comparison["right_items"],
            },
        }

    if plan.layout == "title_image" and features.image:
        content = list(features.content_items)[:8]
        if not content:
            content = [features.subtitle or features.title]
        return {
            "slide_id": features.slide_id,
            "layout": "title_image",
            "title": features.title,
            "content": content,
            "image": {
                "mode": features.image.get("mode", "placeholder"),
                **({"caption": features.image["caption"]} if features.image.get("caption") else {}),
                **({"path": features.image["path"]} if features.image.get("path") else {}),
            },
        }

    if plan.layout == "title_only":
        return {
            "slide_id": features.slide_id,
            "layout": "title_only",
            "title": features.statements[0] if features.statements else (features.key_message or features.title),
        }

    if plan.layout == "two_columns" and len(features.card_blocks) == 1 and len(features.card_blocks[0]["cards"]) == 2:
        left_card, right_card = features.card_blocks[0]["cards"]
        return {
            "slide_id": features.slide_id,
            "layout": "two_columns",
            "title": features.title,
            "left": {
                "heading": left_card["title"],
                "items": [left_card.get("body") or left_card["title"]],
            },
            "right": {
                "heading": right_card["title"],
                "items": [right_card.get("body") or right_card["title"]],
            },
        }

    if plan.layout == "two_columns" and len(features.stat_blocks) == 1 and len(features.stat_blocks[0]["metrics"]) == 2:
        left_metric, right_metric = features.stat_blocks[0]["metrics"]
        return {
            "slide_id": features.slide_id,
            "layout": "two_columns",
            "title": features.title,
            "left": {
                "heading": left_metric["label"],
                "items": [left_metric["value"]] + ([left_metric["note"]] if left_metric.get("note") else []),
            },
            "right": {
                "heading": right_metric["label"],
                "items": [right_metric["value"]] + ([right_metric["note"]] if right_metric.get("note") else []),
            },
        }

    if plan.layout == "two_columns" and len(features.matrix_blocks) == 1:
        cells = features.matrix_blocks[0]["cells"]
        left_cells, right_cells = _split_evenly(cells)

        def _cell_items(group: list[dict[str, str]]) -> list[str]:
            items: list[str] = []
            for cell in group:
                items.append(cell["title"])
                if cell.get("body"):
                    items.append(cell["body"])
            return items[:6]

        x_axis = features.matrix_blocks[0].get("x_axis")
        y_axis = features.matrix_blocks[0].get("y_axis")
        return {
            "slide_id": features.slide_id,
            "layout": "two_columns",
            "title": features.title,
            "left": {
                "heading": x_axis or features.matrix_blocks[0].get("heading") or "Matrix Left",
                "items": _cell_items(left_cells),
            },
            "right": {
                "heading": y_axis or "Matrix Right",
                "items": _cell_items(right_cells or left_cells),
            },
        }

    if plan.layout == "two_columns" and len(features.bullet_blocks) >= 2:
        left_block = features.bullet_blocks[0]
        right_block = features.bullet_blocks[1]
        return {
            "slide_id": features.slide_id,
            "layout": "two_columns",
            "title": features.title,
            "left": {
                "heading": left_block.get("heading") or "核心要点",
                "items": left_block["items"][:6],
            },
            "right": {
                "heading": right_block.get("heading") or "补充说明",
                "items": right_block["items"][:6],
            },
        }

    content_items = list(features.content_items)
    if plan.layout == "two_columns" and content_items:
        left_items, right_items = _split_evenly(content_items)
        heading = features.bullet_blocks[0].get("heading") if features.bullet_blocks else ""
        return {
            "slide_id": features.slide_id,
            "layout": "two_columns",
            "title": features.title,
            "left": {
                "heading": heading or "核心要点",
                "items": left_items[:6],
            },
            "right": {
                "heading": "进一步展开",
                "items": right_items[:6] or [features.subtitle or features.title],
            },
        }

    if not content_items:
        content_items = [features.subtitle or features.title]

    return {
        "slide_id": features.slide_id,
        "layout": "title_content",
        "title": features.title,
        "content": content_items[:10],
    }


def compile_semantic_deck_payload(
    payload: dict[str, Any],
    *,
    default_title: str = "AI Auto PPT",
    default_theme: str = "business_red",
    default_language: str = "zh-CN",
    default_author: str = "AI Auto PPT",
) -> ValidatedDeck:
    normalized = _normalize_semantic_payload(
        payload,
        default_title=default_title,
        default_theme=default_theme,
        default_language=default_language,
        default_author=default_author,
    )
    slides = normalized["slides"]
    for slide in slides:
        if slide["intent"] not in SUPPORTED_SLIDE_INTENTS:
            raise ValueError(f"unsupported slide intent: {slide['intent']}")
        if not slide["title"]:
            raise ValueError(f"slide {slide['slide_id']} title cannot be empty.")

    compiled = {
        "meta": normalized["meta"],
        "slides": [_compile_semantic_slide(slide) for slide in slides],
    }
    return validate_deck_payload(
        compiled,
        default_title=default_title,
        default_theme=default_theme,
        default_language=default_language,
        default_author=default_author,
    )
