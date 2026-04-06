from __future__ import annotations

import json
import re
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

from .quality_checks import ContentWarning, QualityGateResult, quality_gate
from .schema import ValidatedDeck, validate_deck_payload


TITLE_LIMIT = 24
BULLET_LIMIT = 32
TITLE_CONTENT_TARGET = 6
TITLE_IMAGE_TARGET = 4
TWO_COLUMNS_TARGET = 5

FIXABLE_PATTERNS = (
    "title contains",
    "bullet items",
    "bullet ",
    "title_image has",
    "title_image content",
    "left column has",
    "right column has",
    "item count gap",
)

FILLER_PATTERNS = (
    r"进一步",
    r"持续",
    r"积极",
    r"系统性",
    r"整体",
    r"相关",
    r"有效",
    r"重点",
    r"当前",
    r"主要",
    r"进行",
    r"推动",
    r"推进",
)


@dataclass(frozen=True)
class RewriteAction:
    slide_id: str
    field: str
    action: str
    before: Any
    after: Any

    def to_dict(self) -> dict[str, Any]:
        return {
            "slide_id": self.slide_id,
            "field": self.field,
            "action": self.action,
            "before": self.before,
            "after": self.after,
        }


@dataclass(frozen=True)
class RewriteDeckResult:
    attempted: bool
    applied: bool
    validated_deck: ValidatedDeck | None
    initial_quality_gate: QualityGateResult
    final_quality_gate: QualityGateResult
    actions: tuple[RewriteAction, ...] = ()
    notes: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "attempted": self.attempted,
            "applied": self.applied,
            "action_count": len(self.actions),
            "rewritten_slide_ids": sorted({action.slide_id for action in self.actions}),
            "initial_summary": self.initial_quality_gate.summary,
            "final_summary": self.final_quality_gate.summary,
            "notes": list(self.notes),
            "actions": [action.to_dict() for action in self.actions],
        }


def _normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", str(text).strip())


def _strip_parenthetical(text: str) -> str:
    return re.sub(r"[\(（][^\)）]{0,20}[\)）]", "", text)


def _cleanup_text(text: str) -> str:
    cleaned = _normalize_text(text)
    cleaned = cleaned.strip(" ,，;；:：/、")
    cleaned = re.sub(r"[，,；;]{2,}", "；", cleaned)
    cleaned = re.sub(r"[:：]{2,}", "：", cleaned)
    return cleaned or _normalize_text(text)


def _truncate_text(text: str, max_length: int) -> str:
    normalized = _cleanup_text(text)
    if len(normalized) <= max_length:
        return normalized
    clipped = normalized[:max_length].rstrip(" ,，;；:：/、")
    return clipped or normalized[:max_length]


def _compress_text(text: str, max_length: int) -> str:
    normalized = _cleanup_text(_strip_parenthetical(text))
    candidates = [normalized]

    fragment_parts = [part.strip() for part in re.split(r"[；;，,。！？!?:：/、]", normalized) if part.strip()]
    if fragment_parts:
        candidates.append("；".join(fragment_parts[:2]))
        candidates.append(fragment_parts[0])

    reduced = normalized
    for pattern in FILLER_PATTERNS:
        reduced = re.sub(pattern, "", reduced)
    candidates.append(_cleanup_text(reduced))

    for candidate in candidates:
        if candidate and len(candidate) <= max_length:
            return candidate

    compact = min((candidate for candidate in candidates if candidate), key=len, default=normalized)
    return _truncate_text(compact, max_length)


def _merge_items(items: list[str], target_count: int, max_length: int) -> list[str]:
    merged = [_cleanup_text(item) for item in items if _cleanup_text(item)]
    while len(merged) > target_count and len(merged) >= 2:
        tail_right = merged.pop()
        tail_left = merged.pop()
        merged.append(_compress_text(f"{tail_left}；{tail_right}", max_length))
    return merged


def _compress_items(items: list[str], max_length: int) -> list[str]:
    return [_compress_text(item, max_length) if len(_normalize_text(item)) > max_length else _cleanup_text(item) for item in items]


def _is_fixable_issue(issue: ContentWarning) -> bool:
    return any(pattern in issue.message for pattern in FIXABLE_PATTERNS)


def _group_issues_by_slide(issues: tuple[ContentWarning, ...]) -> dict[str, list[ContentWarning]]:
    grouped: dict[str, list[ContentWarning]] = {}
    for issue in issues:
        if not _is_fixable_issue(issue):
            continue
        grouped.setdefault(issue.slide_id, []).append(issue)
    return grouped


def _rewrite_title(slide_id: str, title: str, actions: list[RewriteAction]) -> str:
    rewritten = _compress_text(title, TITLE_LIMIT)
    if rewritten != title:
        actions.append(
            RewriteAction(
                slide_id=slide_id,
                field="title",
                action="compress_title",
                before=title,
                after=rewritten,
            )
        )
    return rewritten


def _rewrite_content_items(
    slide_id: str,
    items: list[str],
    *,
    max_length: int,
    target_count: int,
    actions: list[RewriteAction],
    field: str,
) -> list[str]:
    updated = list(items)
    compressed = _compress_items(updated, max_length)
    if compressed != updated:
        actions.append(
            RewriteAction(
                slide_id=slide_id,
                field=field,
                action="compress_items",
                before=updated,
                after=compressed,
            )
        )
        updated = compressed

    merged = _merge_items(updated, target_count, max_length)
    if merged != updated:
        actions.append(
            RewriteAction(
                slide_id=slide_id,
                field=field,
                action="merge_items",
                before=updated,
                after=merged,
            )
        )
        updated = merged
    return updated


def _rewrite_two_columns(slide: dict[str, Any], actions: list[RewriteAction]) -> dict[str, Any]:
    updated = dict(slide)
    left = dict(updated["left"])
    right = dict(updated["right"])

    left_items = _compress_items(list(left["items"]), BULLET_LIMIT)
    right_items = _compress_items(list(right["items"]), BULLET_LIMIT)

    if left_items != left["items"]:
        actions.append(
            RewriteAction(
                slide_id=slide["slide_id"],
                field="left.items",
                action="compress_items",
                before=list(left["items"]),
                after=left_items,
            )
        )
    if right_items != right["items"]:
        actions.append(
            RewriteAction(
                slide_id=slide["slide_id"],
                field="right.items",
                action="compress_items",
                before=list(right["items"]),
                after=right_items,
            )
        )

    while len(left_items) > TWO_COLUMNS_TARGET:
        next_items = _merge_items(left_items, len(left_items) - 1, BULLET_LIMIT)
        if next_items == left_items:
            break
        actions.append(
            RewriteAction(
                slide_id=slide["slide_id"],
                field="left.items",
                action="merge_items",
                before=left_items,
                after=next_items,
            )
        )
        left_items = next_items

    while len(right_items) > TWO_COLUMNS_TARGET:
        next_items = _merge_items(right_items, len(right_items) - 1, BULLET_LIMIT)
        if next_items == right_items:
            break
        actions.append(
            RewriteAction(
                slide_id=slide["slide_id"],
                field="right.items",
                action="merge_items",
                before=right_items,
                after=next_items,
            )
        )
        right_items = next_items

    while abs(len(left_items) - len(right_items)) > 3:
        if len(left_items) > len(right_items):
            next_items = _merge_items(left_items, len(left_items) - 1, BULLET_LIMIT)
            if next_items == left_items:
                break
            actions.append(
                RewriteAction(
                    slide_id=slide["slide_id"],
                    field="left.items",
                    action="rebalance_items",
                    before=left_items,
                    after=next_items,
                )
            )
            left_items = next_items
        else:
            next_items = _merge_items(right_items, len(right_items) - 1, BULLET_LIMIT)
            if next_items == right_items:
                break
            actions.append(
                RewriteAction(
                    slide_id=slide["slide_id"],
                    field="right.items",
                    action="rebalance_items",
                    before=right_items,
                    after=next_items,
                )
            )
            right_items = next_items

    left["items"] = left_items
    right["items"] = right_items
    updated["left"] = left
    updated["right"] = right
    return updated


def rewrite_slide(slide_data: dict[str, Any], issues: list[ContentWarning]) -> tuple[dict[str, Any], tuple[RewriteAction, ...]]:
    updated = dict(slide_data)
    actions: list[RewriteAction] = []
    issue_messages = [issue.message for issue in issues]
    layout = updated.get("layout", "")
    slide_id = str(updated.get("slide_id", "unknown"))

    if any("title contains" in message for message in issue_messages):
        updated["title"] = _rewrite_title(slide_id, str(updated.get("title", "")), actions)

    if layout == "title_content":
        content = list(updated.get("content", []))
        if any("bullet" in message for message in issue_messages):
            updated["content"] = _rewrite_content_items(
                slide_id,
                content,
                max_length=BULLET_LIMIT,
                target_count=TITLE_CONTENT_TARGET,
                actions=actions,
                field="content",
            )
    elif layout == "title_image":
        content = list(updated.get("content", []))
        if any("title_image has" in message or "title_image content" in message for message in issue_messages):
            updated["content"] = _rewrite_content_items(
                slide_id,
                content,
                max_length=BULLET_LIMIT,
                target_count=TITLE_IMAGE_TARGET,
                actions=actions,
                field="content",
            )
    elif layout == "two_columns":
        if any("column has" in message or "item count gap" in message for message in issue_messages):
            updated = _rewrite_two_columns(updated, actions)

    return updated, tuple(actions)


def rewrite_deck(
    validated_deck: ValidatedDeck | None,
    quality_result: QualityGateResult,
) -> RewriteDeckResult:
    if validated_deck is None:
        return RewriteDeckResult(
            attempted=False,
            applied=False,
            validated_deck=None,
            initial_quality_gate=quality_result,
            final_quality_gate=quality_result,
            notes=("schema validation failed; rewrite skipped",),
        )

    issues_by_slide = _group_issues_by_slide(quality_result.all_issues())
    if not issues_by_slide:
        return RewriteDeckResult(
            attempted=False,
            applied=False,
            validated_deck=validated_deck,
            initial_quality_gate=quality_result,
            final_quality_gate=quality_result,
            notes=("no fixable quality issues found",),
        )

    payload = validated_deck.deck.model_dump(mode="json")
    slide_actions: list[RewriteAction] = []
    rewritten_slides: list[dict[str, Any]] = []

    for slide in payload["slides"]:
        slide_id = str(slide.get("slide_id", ""))
        if slide_id not in issues_by_slide:
            rewritten_slides.append(slide)
            continue
        rewritten_slide, actions = rewrite_slide(slide, issues_by_slide[slide_id])
        slide_actions.extend(actions)
        rewritten_slides.append(rewritten_slide)

    if not slide_actions:
        return RewriteDeckResult(
            attempted=True,
            applied=False,
            validated_deck=validated_deck,
            initial_quality_gate=quality_result,
            final_quality_gate=quality_result,
            notes=("fixable issues were detected but no safe rewrite was produced",),
        )

    rewritten_payload = {"meta": payload["meta"], "slides": rewritten_slides}
    rewritten_validated = validate_deck_payload(rewritten_payload)
    final_quality = quality_gate(rewritten_validated)
    if final_quality.summary["high_count"] > 0 or final_quality.summary["error_count"] > 0:
        final_quality = replace(final_quality, review_required=True)

    return RewriteDeckResult(
        attempted=True,
        applied=True,
        validated_deck=rewritten_validated,
        initial_quality_gate=quality_result,
        final_quality_gate=final_quality,
        actions=tuple(slide_actions),
        notes=("rewrite pass completed",),
    )


def write_rewrite_log(result: RewriteDeckResult, output_path: str | Path) -> Path:
    target_path = Path(output_path)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_text(
        json.dumps(result.to_dict(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return target_path
