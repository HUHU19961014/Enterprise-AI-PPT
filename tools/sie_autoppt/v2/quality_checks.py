from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .schema import (
    CardsGridSlide,
    DeckDocument,
    MatrixGridSlide,
    StatsDashboardSlide,
    TimelineSlide,
    TitleContentSlide,
    TitleImageSlide,
    TwoColumnsSlide,
    ValidatedDeck,
    validate_deck_payload,
)
from .rule_config import load_v2_rule_config


WARNING_LEVEL_WARNING = "warning"
WARNING_LEVEL_HIGH = "high"
WARNING_LEVEL_ERROR = "error"
RULE_CONFIG = load_v2_rule_config()


@dataclass(frozen=True)
class ContentWarning:
    slide_id: str
    warning_level: str
    message: str

    def to_log_line(self) -> str:
        return f"[{self.slide_id}] [{self.warning_level}] {self.message}"

    def is_error(self) -> bool:
        return self.warning_level == WARNING_LEVEL_ERROR

    def to_dict(self) -> dict[str, str]:
        return {
            "slide_id": self.slide_id,
            "level": self.warning_level,
            "message": self.message,
        }


@dataclass(frozen=True)
class AutoScoreResult:
    auto_score: int
    level: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "auto_score": self.auto_score,
            "level": self.level,
        }


@dataclass(frozen=True)
class QualityGateResult:
    passed: bool
    review_required: bool
    warnings: tuple[ContentWarning, ...]
    high: tuple[ContentWarning, ...]
    errors: tuple[ContentWarning, ...]
    validated_deck: ValidatedDeck | None = None
    auto_score: int = 100
    auto_level: str = "优秀"

    @property
    def summary(self) -> dict[str, int]:
        return {
            "warning_count": len(self.warnings),
            "high_count": len(self.high),
            "error_count": len(self.errors),
        }

    @property
    def slide_count(self) -> int:
        if self.validated_deck is None:
            return 0
        return len(self.validated_deck.deck.slides)

    def all_issues(self) -> tuple[ContentWarning, ...]:
        return self.warnings + self.high + self.errors

    def to_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "review_required": self.review_required,
            "warnings": [issue.to_dict() for issue in self.warnings],
            "high": [issue.to_dict() for issue in self.high],
            "errors": [issue.to_dict() for issue in self.errors],
            "summary": self.summary,
            "auto_score": self.auto_score,
            "auto_level": self.auto_level,
        }


def _count_hanzi(text: str) -> int:
    return len(re.findall(r"[\u4e00-\u9fff]", text))


# Titles that usually behave like table-of-contents labels instead of business conclusions.
DIRECTORY_STYLE_EXACT_TITLES = RULE_CONFIG.directory_style.exact_titles
DIRECTORY_STYLE_SUFFIXES = RULE_CONFIG.directory_style.suffixes
CONCLUSION_MARKERS = RULE_CONFIG.directory_style.conclusion_markers


def _normalize_title_for_pattern(title: str) -> str:
    return re.sub(r"[\s:：，,。.、（）()\-]+", "", title)


def _looks_conclusion_oriented(title: str) -> bool:
    if any(marker in title for marker in CONCLUSION_MARKERS):
        return True
    return "，" in title and _count_hanzi(title) >= 10


def _has_directory_style_title(title: str) -> bool:
    """Check if title looks like a section heading instead of a business conclusion."""
    normalized = _normalize_title_for_pattern(title)
    if not normalized:
        return False
    if _looks_conclusion_oriented(title):
        return False
    if normalized in DIRECTORY_STYLE_EXACT_TITLES:
        return True
    return _count_hanzi(normalized) <= 8 and any(normalized.endswith(suffix) for suffix in DIRECTORY_STYLE_SUFFIXES)


def _title_warnings(slide) -> list[ContentWarning]:
    warnings: list[ContentWarning] = []
    hanzi_count = _count_hanzi(slide.title)

    # Error level: title too long (severe overflow risk)
    if hanzi_count > 28:
        warnings.append(
            ContentWarning(
                slide_id=slide.slide_id,
                warning_level=WARNING_LEVEL_ERROR,
                message=f"title contains {hanzi_count} Chinese characters, which exceeds the 28-character error threshold (severe overflow risk).",
            )
        )
    # High warning: title very long
    elif hanzi_count > 24:
        warnings.append(
            ContentWarning(
                slide_id=slide.slide_id,
                warning_level=WARNING_LEVEL_HIGH,
                message=f"title contains {hanzi_count} Chinese characters, which exceeds the 24-character high-warning threshold.",
            )
        )
    # Warning: title longer than recommended
    elif hanzi_count > 20:
        warnings.append(
            ContentWarning(
                slide_id=slide.slide_id,
                warning_level=WARNING_LEVEL_WARNING,
                message=f"title contains {hanzi_count} Chinese characters, which exceeds the 20-character recommended threshold.",
            )
        )

    # Warning: directory-style title (lacks conclusion orientation)
    if _has_directory_style_title(slide.title):
        warnings.append(
            ContentWarning(
                slide_id=slide.slide_id,
                warning_level=WARNING_LEVEL_WARNING,
                message=f"title '{slide.title}' appears to be directory-style; consider making it more conclusion-oriented.",
            )
        )

    return warnings


def _title_content_warnings(slide: TitleContentSlide) -> list[ContentWarning]:
    warnings: list[ContentWarning] = []
    bullet_count = len(slide.content)

    # Error level: bullet count severely out of range
    if bullet_count < 1 or bullet_count > 7:
        warnings.append(
            ContentWarning(
                slide_id=slide.slide_id,
                warning_level=WARNING_LEVEL_ERROR,
                message=f"title_content has {bullet_count} bullet items; must be between 1-7.",
            )
        )
    # Warning: bullet count outside recommended range
    elif bullet_count < 2 or bullet_count > 6:
        warnings.append(
            ContentWarning(
                slide_id=slide.slide_id,
                warning_level=WARNING_LEVEL_WARNING,
                message=f"title_content has {bullet_count} bullet items; recommended range is 2-6.",
            )
        )

    for index, item in enumerate(slide.content, start=1):
        item_length = len(item)
        # Error level: bullet extremely long (severe overflow risk)
        if item_length > 50:
            warnings.append(
                ContentWarning(
                    slide_id=slide.slide_id,
                    warning_level=WARNING_LEVEL_ERROR,
                    message=f"title_content bullet {index} length is {item_length}, which exceeds 50 characters (severe overflow risk).",
                )
            )
        # Warning: bullet longer than recommended
        elif item_length > 35:
            warnings.append(
                ContentWarning(
                    slide_id=slide.slide_id,
                    warning_level=WARNING_LEVEL_WARNING,
                    message=f"title_content bullet {index} length is {item_length}, which exceeds 35 characters (recommended threshold).",
                )
            )

    return warnings


def _two_columns_warnings(slide: TwoColumnsSlide) -> list[ContentWarning]:
    warnings: list[ContentWarning] = []
    left_count = len(slide.left.items)
    right_count = len(slide.right.items)
    if left_count > 5:
        warnings.append(
            ContentWarning(
                slide_id=slide.slide_id,
                warning_level=WARNING_LEVEL_WARNING,
                message=f"two_columns left column has {left_count} items, which exceeds 5.",
            )
        )
    if right_count > 5:
        warnings.append(
            ContentWarning(
                slide_id=slide.slide_id,
                warning_level=WARNING_LEVEL_WARNING,
                message=f"two_columns right column has {right_count} items, which exceeds 5.",
            )
        )
    if abs(left_count - right_count) > 3:
        warnings.append(
            ContentWarning(
                slide_id=slide.slide_id,
                warning_level=WARNING_LEVEL_WARNING,
                message=f"two_columns item count gap is {abs(left_count - right_count)}, which exceeds 3.",
            )
        )
    return warnings


def _title_image_warnings(slide: TitleImageSlide) -> list[ContentWarning]:
    warnings: list[ContentWarning] = []
    content_count = len(slide.content)
    if content_count > 4:
        warnings.append(
            ContentWarning(
                slide_id=slide.slide_id,
                warning_level=WARNING_LEVEL_WARNING,
                message=f"title_image has {content_count} content items, which exceeds 4.",
            )
        )
    for index, item in enumerate(slide.content, start=1):
        item_length = len(item)
        # Error level: content extremely long
        if item_length > 50:
            warnings.append(
                ContentWarning(
                    slide_id=slide.slide_id,
                    warning_level=WARNING_LEVEL_ERROR,
                    message=f"title_image content {index} length is {item_length}, which exceeds 50 characters (severe overflow risk).",
                )
            )
        # Warning: content longer than recommended
        elif item_length > 35:
            warnings.append(
                ContentWarning(
                    slide_id=slide.slide_id,
                    warning_level=WARNING_LEVEL_WARNING,
                    message=f"title_image content {index} length is {item_length}, which exceeds 35 characters (recommended threshold).",
                )
            )
    return warnings


def _timeline_warnings(slide: TimelineSlide) -> list[ContentWarning]:
    warnings: list[ContentWarning] = []
    if len(slide.stages) > 5:
        warnings.append(
            ContentWarning(
                slide_id=slide.slide_id,
                warning_level=WARNING_LEVEL_WARNING,
                message=f"timeline has {len(slide.stages)} stages, which exceeds the 5-stage recommended threshold.",
            )
        )
    for index, stage in enumerate(slide.stages, start=1):
        if stage.detail and len(stage.detail) > 45:
            warnings.append(
                ContentWarning(
                    slide_id=slide.slide_id,
                    warning_level=WARNING_LEVEL_WARNING,
                    message=f"timeline stage {index} detail length is {len(stage.detail)}, which exceeds 45 characters (recommended threshold).",
                )
            )
    return warnings


def _stats_dashboard_warnings(slide: StatsDashboardSlide) -> list[ContentWarning]:
    warnings: list[ContentWarning] = []
    if len(slide.metrics) > 4:
        warnings.append(
            ContentWarning(
                slide_id=slide.slide_id,
                warning_level=WARNING_LEVEL_WARNING,
                message=f"stats_dashboard has {len(slide.metrics)} metrics, which exceeds 4.",
            )
        )
    if len(slide.insights) > 3:
        warnings.append(
            ContentWarning(
                slide_id=slide.slide_id,
                warning_level=WARNING_LEVEL_WARNING,
                message=f"stats_dashboard has {len(slide.insights)} insight items, which exceeds 3.",
            )
        )
    for index, metric in enumerate(slide.metrics, start=1):
        if metric.note and len(metric.note) > 35:
            warnings.append(
                ContentWarning(
                    slide_id=slide.slide_id,
                    warning_level=WARNING_LEVEL_WARNING,
                    message=f"stats_dashboard metric {index} note length is {len(metric.note)}, which exceeds 35 characters (recommended threshold).",
                )
            )
    return warnings


def _matrix_grid_warnings(slide: MatrixGridSlide) -> list[ContentWarning]:
    warnings: list[ContentWarning] = []
    if len(slide.cells) < 4:
        warnings.append(
            ContentWarning(
                slide_id=slide.slide_id,
                warning_level=WARNING_LEVEL_WARNING,
                message=f"matrix_grid has {len(slide.cells)} cells; 4 cells are recommended for a balanced quadrant view.",
            )
        )
    for index, cell in enumerate(slide.cells, start=1):
        if cell.body and len(cell.body) > 45:
            warnings.append(
                ContentWarning(
                    slide_id=slide.slide_id,
                    warning_level=WARNING_LEVEL_WARNING,
                    message=f"matrix_grid cell {index} body length is {len(cell.body)}, which exceeds 45 characters (recommended threshold).",
                )
            )
    return warnings


def _cards_grid_warnings(slide: CardsGridSlide) -> list[ContentWarning]:
    warnings: list[ContentWarning] = []
    if len(slide.cards) > 3:
        warnings.append(
            ContentWarning(
                slide_id=slide.slide_id,
                warning_level=WARNING_LEVEL_WARNING,
                message=f"cards_grid has {len(slide.cards)} cards, which exceeds 3.",
            )
        )
    for index, card in enumerate(slide.cards, start=1):
        if card.body and len(card.body) > 50:
            warnings.append(
                ContentWarning(
                    slide_id=slide.slide_id,
                    warning_level=WARNING_LEVEL_ERROR,
                    message=f"cards_grid card {index} body length is {len(card.body)}, which exceeds 50 characters (severe overflow risk).",
                )
            )
        elif card.body and len(card.body) > 35:
            warnings.append(
                ContentWarning(
                    slide_id=slide.slide_id,
                    warning_level=WARNING_LEVEL_WARNING,
                    message=f"cards_grid card {index} body length is {len(card.body)}, which exceeds 35 characters (recommended threshold).",
                )
            )
    return warnings


def check_slide_content(slide) -> list[ContentWarning]:
    warnings = _title_warnings(slide)
    if isinstance(slide, TitleContentSlide):
        warnings.extend(_title_content_warnings(slide))
    elif isinstance(slide, TwoColumnsSlide):
        warnings.extend(_two_columns_warnings(slide))
    elif isinstance(slide, TitleImageSlide):
        warnings.extend(_title_image_warnings(slide))
    elif isinstance(slide, TimelineSlide):
        warnings.extend(_timeline_warnings(slide))
    elif isinstance(slide, StatsDashboardSlide):
        warnings.extend(_stats_dashboard_warnings(slide))
    elif isinstance(slide, MatrixGridSlide):
        warnings.extend(_matrix_grid_warnings(slide))
    elif isinstance(slide, CardsGridSlide):
        warnings.extend(_cards_grid_warnings(slide))
    return warnings


def check_deck_content(deck: DeckDocument) -> list[ContentWarning]:
    warnings: list[ContentWarning] = []
    for slide in deck.slides:
        warnings.extend(check_slide_content(slide))
    warnings.extend(_check_deck_structure(deck))
    return warnings


def _check_deck_structure(deck: DeckDocument) -> list[ContentWarning]:
    """Check overall deck structure for best practices."""
    warnings: list[ContentWarning] = []

    if not deck.slides:
        return warnings

    first_slide = deck.slides[0]
    last_slide = deck.slides[-1]

    # Warning: first slide should ideally be section_break
    if first_slide.layout not in ("section_break", "title_only"):
        warnings.append(
            ContentWarning(
                slide_id=first_slide.slide_id,
                warning_level=WARNING_LEVEL_WARNING,
                message=f"first slide uses layout '{first_slide.layout}'; consider using 'section_break' to set context.",
            )
        )

    # Warning: last slide should ideally be title_only or section_break
    if last_slide.layout not in ("title_only", "section_break"):
        warnings.append(
            ContentWarning(
                slide_id=last_slide.slide_id,
                warning_level=WARNING_LEVEL_WARNING,
                message=f"last slide uses layout '{last_slide.layout}'; consider using 'title_only' to converge conclusion.",
            )
        )

    return warnings


def count_errors(warnings: list[ContentWarning]) -> int:
    """Count the number of error-level warnings."""
    return sum(1 for w in warnings if w.is_error())


def count_by_level(warnings: list[ContentWarning]) -> dict[str, int]:
    """Count warnings by level."""
    counts = {WARNING_LEVEL_ERROR: 0, WARNING_LEVEL_HIGH: 0, WARNING_LEVEL_WARNING: 0}
    for w in warnings:
        counts[w.warning_level] = counts.get(w.warning_level, 0) + 1
    return counts


def calculate_auto_score(
    warning_count: int,
    high_count: int,
    error_count: int,
    slide_count: int = 0,
) -> AutoScoreResult:
    scoring = RULE_CONFIG.scoring
    weighted_penalty = (
        warning_count * scoring.warning_weight
        + high_count * scoring.high_weight
        + error_count * scoring.error_weight
    )
    scaling_factor = max(1.0, math.sqrt(max(slide_count, 1) / scoring.baseline_slide_count))
    scaled_penalty = math.ceil(weighted_penalty / scaling_factor)
    score = max(0, scoring.base_score - scaled_penalty)
    if score >= scoring.excellent_threshold:
        level = "优秀"
    elif score >= scoring.usable_threshold:
        level = "可用"
    elif score >= scoring.review_threshold:
        level = "需复核"
    else:
        level = "不可用"
    return AutoScoreResult(auto_score=score, level=level)


def _build_quality_gate_result(
    issues: list[ContentWarning],
    *,
    validated_deck: ValidatedDeck | None,
) -> QualityGateResult:
    warnings = tuple(issue for issue in issues if issue.warning_level == WARNING_LEVEL_WARNING)
    high = tuple(issue for issue in issues if issue.warning_level == WARNING_LEVEL_HIGH)
    errors = tuple(issue for issue in issues if issue.warning_level == WARNING_LEVEL_ERROR)

    if errors:
        passed = False
        review_required = False
    elif high:
        passed = True
        review_required = True
    else:
        passed = True
        review_required = False

    auto_score = calculate_auto_score(
        warning_count=len(warnings),
        high_count=len(high),
        error_count=len(errors),
        slide_count=(len(validated_deck.deck.slides) if validated_deck is not None else 0),
    )
    return QualityGateResult(
        passed=passed,
        review_required=review_required,
        warnings=warnings,
        high=high,
        errors=errors,
        validated_deck=validated_deck,
        auto_score=auto_score.auto_score,
        auto_level=auto_score.level,
    )


def quality_gate(deck_data: DeckDocument | ValidatedDeck | dict[str, object]) -> QualityGateResult:
    if isinstance(deck_data, ValidatedDeck):
        validated = deck_data
    elif isinstance(deck_data, DeckDocument):
        validated = ValidatedDeck(deck=deck_data)
    elif isinstance(deck_data, dict):
        try:
            validated = validate_deck_payload(deck_data)
        except Exception as exc:
            return _build_quality_gate_result(
                [
                    ContentWarning(
                        slide_id="schema",
                        warning_level=WARNING_LEVEL_ERROR,
                        message=str(exc),
                    )
                ],
                validated_deck=None,
            )
    else:
        raise TypeError("deck_data must be a DeckDocument, ValidatedDeck, or JSON object.")

    return _build_quality_gate_result(
        list(check_deck_content(validated.deck)),
        validated_deck=validated,
    )


def write_quality_gate_result(result: QualityGateResult, output_path: str | Path) -> Path:
    target_path = Path(output_path)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_text(
        json.dumps(result.to_dict(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return target_path
