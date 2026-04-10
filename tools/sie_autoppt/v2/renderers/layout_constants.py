from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TitleBandLayout:
    left: float = 0.78
    top: float = 0.5
    width: float = 11.7
    height: float = 0.55
    subtitle_left: float = 0.82
    subtitle_width: float = 11.5
    subtitle_height: float = 0.28


@dataclass(frozen=True)
class FullCardLayout:
    left: float
    top: float
    width: float
    height: float


@dataclass(frozen=True)
class TwoColumnLayout:
    card_top: float = 1.32
    card_height: float = 4.9
    card_width: float = 5.55
    left_left: float = 0.78
    right_left: float = 7.05
    inner_horizontal_padding: float = 0.18
    heading_top_offset: float = 0.18
    heading_height: float = 0.38
    bullet_top_offset: float = 0.62
    bullet_bottom_padding: float = 0.86
    table_left: float = 0.78
    table_top: float = 1.32
    table_width: float = 11.82
    table_height: float = 4.9


@dataclass(frozen=True)
class TitleContentLayout:
    card: FullCardLayout = FullCardLayout(left=0.78, top=1.28, width=11.72, height=4.95)
    timeline_left: float = 1.0
    timeline_top: float = 1.55
    timeline_width: float = 11.06
    timeline_height: float = 4.2
    content_left: float = 1.02
    content_top: float = 1.6
    content_width: float = 11.1
    content_height: float = 4.25


@dataclass(frozen=True)
class CardsGridLayout:
    heading_left: float = 0.82
    heading_top: float = 1.04
    heading_width: float = 11.5
    heading_height: float = 0.28
    card_title_left_padding: float = 0.14
    card_title_top_padding: float = 0.16
    card_title_height: float = 0.34
    card_body_top_offset: float = 0.6
    card_body_bottom_padding: float = 0.78


@dataclass(frozen=True)
class TitleOnlyLayout:
    card: FullCardLayout = FullCardLayout(left=0.95, top=1.35, width=11.45, height=4.6)
    title_left: float = 1.55
    title_top: float = 2.55
    title_width: float = 10.2
    title_height: float = 1.2


@dataclass(frozen=True)
class TitleImageLayout:
    left_card: FullCardLayout = FullCardLayout(left=0.78, top=1.32, width=5.2, height=4.85)
    right_card: FullCardLayout = FullCardLayout(left=6.2, top=1.32, width=6.3, height=4.85)
    content_left: float = 1.0
    content_top: float = 1.65
    content_width: float = 4.75
    content_height: float = 4.1
    visual_left: float = 6.45
    visual_top: float = 1.58
    visual_width: float = 5.8
    visual_height: float = 4.33


@dataclass(frozen=True)
class TimelineLayout:
    subtitle_top: float = 1.08
    card: FullCardLayout = FullCardLayout(left=0.78, top=1.42, width=11.72, height=4.8)
    flow_left: float = 1.0
    flow_top: float = 1.7
    flow_width: float = 11.1
    flow_height: float = 4.1


TITLE_BAND = TitleBandLayout()
TWO_COLUMNS = TwoColumnLayout()
TITLE_CONTENT = TitleContentLayout()
CARDS_GRID = CardsGridLayout()
TITLE_ONLY = TitleOnlyLayout()
TITLE_IMAGE = TitleImageLayout()
TIMELINE = TimelineLayout()


def cards_grid_positions(card_count: int) -> list[tuple[float, float, float, float]]:
    if card_count == 2:
        return [
            (0.9, 1.5, TWO_COLUMNS.card_width, 4.55),
            (6.05, 1.5, TWO_COLUMNS.card_width, 4.55),
        ]
    if card_count == 3:
        return [(0.85, 1.64, 3.72, 4.2), (4.79, 1.64, 3.72, 4.2), (8.73, 1.64, 3.72, 4.2)]
    return [(0.9, 1.52, 5.5, 2.1), (6.0, 1.52, 5.5, 2.1), (0.9, 3.92, 5.5, 2.1), (6.0, 3.92, 5.5, 2.1)]
