from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .hierarchy import assign_hierarchy_levels
from .visual_balance import BalanceScore, ContentBlock, calculate_balance_score
from .whitespace import SpacingParams, calculate_whitespace_ratio, get_spacing_params


@dataclass(frozen=True)
class LayoutStrategy:
    layout_preference: str
    balance: BalanceScore
    spacing: SpacingParams
    hierarchy: tuple[int, ...]


def decide_layout_strategy(
    *,
    intent: str,
    blocks: Iterable[ContentBlock],
    has_comparison: bool,
    has_image: bool,
) -> LayoutStrategy:
    block_list = list(blocks)
    total_length = sum(max(1, block.length) for block in block_list)
    balance = calculate_balance_score(block_list)
    spacing = get_spacing_params(calculate_whitespace_ratio(total_length))
    hierarchy = assign_hierarchy_levels(block_list)

    if has_comparison:
        layout_preference = "two_columns"
    elif has_image and total_length > 40:
        layout_preference = "title_image"
    elif intent in {"summary", "conclusion"} and total_length <= 40:
        layout_preference = "title_only"
    elif total_length >= 120 or balance.suggestion in {"expand_left", "expand_right"}:
        layout_preference = "two_columns"
    else:
        layout_preference = "title_content"

    return LayoutStrategy(
        layout_preference=layout_preference,
        balance=balance,
        spacing=spacing,
        hierarchy=hierarchy,
    )
