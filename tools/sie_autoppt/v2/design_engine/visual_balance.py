from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class ContentBlock:
    content: str
    length: int
    priority: int
    lane: str = "center"
    media_type: str = "text"


@dataclass(frozen=True)
class BalanceScore:
    left_weight: float
    right_weight: float
    suggestion: str


def calculate_balance_score(blocks: Iterable[ContentBlock]) -> BalanceScore:
    left_score = 0.0
    right_score = 0.0
    for block in blocks:
        weight = max(1, int(block.priority)) * max(1, int(block.length))
        if block.lane == "left":
            left_score += weight
        elif block.lane == "right":
            right_score += weight
    total = left_score + right_score
    if total <= 0:
        return BalanceScore(left_weight=0.5, right_weight=0.5, suggestion="balanced")

    left_weight = left_score / total
    right_weight = right_score / total
    if left_weight >= 0.62:
        suggestion = "expand_left"
    elif right_weight >= 0.62:
        suggestion = "expand_right"
    else:
        suggestion = "balanced"
    return BalanceScore(left_weight=left_weight, right_weight=right_weight, suggestion=suggestion)
