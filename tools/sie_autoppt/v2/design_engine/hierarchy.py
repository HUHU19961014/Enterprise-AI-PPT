from __future__ import annotations

from typing import Iterable

from .visual_balance import ContentBlock


def assign_hierarchy_levels(blocks: Iterable[ContentBlock]) -> tuple[int, ...]:
    weighted = sorted((max(1, block.priority), idx) for idx, block in enumerate(blocks))
    levels = [2] * len(weighted)
    for rank, (_, idx) in enumerate(reversed(weighted), start=1):
        levels[idx] = min(rank, 3)
    return tuple(levels)
