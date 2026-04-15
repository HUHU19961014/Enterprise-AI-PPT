from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any


DEFAULT_RULES_PATH = Path(__file__).with_name("default_rules.toml")
RULES_PATH_ENV = "SIE_AUTOPPT_V2_RULES_PATH"


@dataclass(frozen=True)
class RewriteRuleConfig:
    filler_patterns: tuple[str, ...]
    filler_safe_phrases: tuple[str, ...]


@dataclass(frozen=True)
class DirectoryStyleRuleConfig:
    exact_titles: frozenset[str]
    suffixes: tuple[str, ...]
    conclusion_markers: tuple[str, ...]


@dataclass(frozen=True)
class ScoringRuleConfig:
    base_score: int
    warning_weight: int
    high_weight: int
    error_weight: int
    baseline_slide_count: int
    excellent_threshold: int
    usable_threshold: int
    review_threshold: int


@dataclass(frozen=True)
class TitleLengthRuleConfig:
    error_threshold: int
    high_threshold: int
    warning_threshold: int


@dataclass(frozen=True)
class BulletRuleConfig:
    min_items: int
    max_items: int
    recommended_min_items: int
    recommended_max_items: int


@dataclass(frozen=True)
class ContentThresholdRuleConfig:
    conclusion_title_min_hanzi: int = 10
    directory_style_max_hanzi: int = 8
    title_content_item_error_length: int = 50
    title_content_item_warning_length: int = 35
    two_columns_max_items_per_column: int = 5
    two_columns_max_item_gap: int = 3
    title_image_max_items: int = 4
    title_image_item_error_length: int = 50
    title_image_item_warning_length: int = 35
    timeline_max_stages: int = 5
    timeline_stage_detail_warning_length: int = 45
    stats_dashboard_max_metrics: int = 4
    stats_dashboard_max_insights: int = 3
    stats_dashboard_metric_note_warning_length: int = 35
    matrix_grid_recommended_min_cells: int = 4
    matrix_grid_cell_body_warning_length: int = 45
    cards_grid_max_cards: int = 3
    cards_grid_card_body_error_length: int = 50
    cards_grid_card_body_warning_length: int = 35
    repetition_fragment_min_length: int = 6
    repetition_adjacent_overlap_warning_count: int = 2


@dataclass(frozen=True)
class V2RuleConfig:
    rewrite: RewriteRuleConfig
    directory_style: DirectoryStyleRuleConfig
    scoring: ScoringRuleConfig
    title_lengths: TitleLengthRuleConfig
    bullets: BulletRuleConfig
    content_thresholds: ContentThresholdRuleConfig = ContentThresholdRuleConfig()


def _load_rule_payload(config_path: Path) -> dict[str, Any]:
    if not config_path.exists():
        raise FileNotFoundError(f"V2 rules config does not exist: {config_path}")
    with config_path.open("rb") as fh:
        payload = tomllib.load(fh)
    if not isinstance(payload, dict):
        raise ValueError("V2 rules config must be a TOML object.")
    return payload


def _list_payload(values: Any) -> tuple[str, ...]:
    if not isinstance(values, list):
        return ()
    return tuple(str(value).strip() for value in values if str(value).strip())


@lru_cache(maxsize=1)
def load_v2_rule_config() -> V2RuleConfig:
    configured_path = os.environ.get(RULES_PATH_ENV, "").strip()
    config_path = Path(configured_path).expanduser() if configured_path else DEFAULT_RULES_PATH
    payload = _load_rule_payload(config_path)

    rewrite_payload = payload.get("rewrite", {})
    quality_payload = payload.get("quality", {})
    directory_payload = quality_payload.get("directory_style", {})
    scoring_payload = quality_payload.get("scoring", {})
    title_payload = quality_payload.get("titles", {})
    bullet_payload = quality_payload.get("bullets", {})
    content_payload = quality_payload.get("content_thresholds", {})

    return V2RuleConfig(
        rewrite=RewriteRuleConfig(
            filler_patterns=_list_payload(rewrite_payload.get("filler_patterns")),
            filler_safe_phrases=_list_payload(rewrite_payload.get("filler_safe_phrases")),
        ),
        directory_style=DirectoryStyleRuleConfig(
            exact_titles=frozenset(_list_payload(directory_payload.get("exact_titles"))),
            suffixes=_list_payload(directory_payload.get("suffixes")),
            conclusion_markers=_list_payload(directory_payload.get("conclusion_markers")),
        ),
        scoring=ScoringRuleConfig(
            base_score=int(scoring_payload.get("base_score", 100)),
            warning_weight=int(scoring_payload.get("warning_weight", 2)),
            high_weight=int(scoring_payload.get("high_weight", 6)),
            error_weight=int(scoring_payload.get("error_weight", 20)),
            baseline_slide_count=max(1, int(scoring_payload.get("baseline_slide_count", 6))),
            excellent_threshold=int(scoring_payload.get("excellent_threshold", 90)),
            usable_threshold=int(scoring_payload.get("usable_threshold", 75)),
            review_threshold=int(scoring_payload.get("review_threshold", 60)),
        ),
        title_lengths=TitleLengthRuleConfig(
            error_threshold=int(title_payload.get("error_threshold", 28)),
            high_threshold=int(title_payload.get("high_threshold", 24)),
            warning_threshold=int(title_payload.get("warning_threshold", 20)),
        ),
        bullets=BulletRuleConfig(
            min_items=max(1, int(bullet_payload.get("min_items", 1))),
            max_items=max(1, int(bullet_payload.get("max_items", 6))),
            recommended_min_items=max(1, int(bullet_payload.get("recommended_min_items", 2))),
            recommended_max_items=max(1, int(bullet_payload.get("recommended_max_items", 6))),
        ),
        content_thresholds=ContentThresholdRuleConfig(
            conclusion_title_min_hanzi=max(1, int(content_payload.get("conclusion_title_min_hanzi", 10))),
            directory_style_max_hanzi=max(1, int(content_payload.get("directory_style_max_hanzi", 8))),
            title_content_item_error_length=max(1, int(content_payload.get("title_content_item_error_length", 50))),
            title_content_item_warning_length=max(
                1, int(content_payload.get("title_content_item_warning_length", 35))
            ),
            two_columns_max_items_per_column=max(
                1, int(content_payload.get("two_columns_max_items_per_column", 5))
            ),
            two_columns_max_item_gap=max(0, int(content_payload.get("two_columns_max_item_gap", 3))),
            title_image_max_items=max(1, int(content_payload.get("title_image_max_items", 4))),
            title_image_item_error_length=max(1, int(content_payload.get("title_image_item_error_length", 50))),
            title_image_item_warning_length=max(1, int(content_payload.get("title_image_item_warning_length", 35))),
            timeline_max_stages=max(1, int(content_payload.get("timeline_max_stages", 5))),
            timeline_stage_detail_warning_length=max(
                1, int(content_payload.get("timeline_stage_detail_warning_length", 45))
            ),
            stats_dashboard_max_metrics=max(1, int(content_payload.get("stats_dashboard_max_metrics", 4))),
            stats_dashboard_max_insights=max(1, int(content_payload.get("stats_dashboard_max_insights", 3))),
            stats_dashboard_metric_note_warning_length=max(
                1, int(content_payload.get("stats_dashboard_metric_note_warning_length", 35))
            ),
            matrix_grid_recommended_min_cells=max(
                1, int(content_payload.get("matrix_grid_recommended_min_cells", 4))
            ),
            matrix_grid_cell_body_warning_length=max(
                1, int(content_payload.get("matrix_grid_cell_body_warning_length", 45))
            ),
            cards_grid_max_cards=max(1, int(content_payload.get("cards_grid_max_cards", 3))),
            cards_grid_card_body_error_length=max(
                1, int(content_payload.get("cards_grid_card_body_error_length", 50))
            ),
            cards_grid_card_body_warning_length=max(
                1, int(content_payload.get("cards_grid_card_body_warning_length", 35))
            ),
            repetition_fragment_min_length=max(1, int(content_payload.get("repetition_fragment_min_length", 6))),
            repetition_adjacent_overlap_warning_count=max(
                1, int(content_payload.get("repetition_adjacent_overlap_warning_count", 2))
            ),
        ),
    )
