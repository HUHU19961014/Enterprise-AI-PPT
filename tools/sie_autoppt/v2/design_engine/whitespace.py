from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SpacingParams:
    margin_scale: float
    line_spacing: float
    density_factor: float


def calculate_whitespace_ratio(content_length: int, *, max_length: int = 220) -> float:
    if content_length <= 0:
        return 0.4
    density = min(content_length / max_length, 1.0)
    return max(0.15, min(0.4, 0.4 - density * 0.25))


def get_spacing_params(whitespace_ratio: float) -> SpacingParams:
    ratio = max(0.15, min(0.4, whitespace_ratio))
    density_factor = 1.0 - ((ratio - 0.15) / 0.25)
    return SpacingParams(
        margin_scale=ratio,
        line_spacing=1.15 + (1.75 - 1.15) * (1.0 - density_factor),
        density_factor=max(0.0, min(1.0, density_factor)),
    )
