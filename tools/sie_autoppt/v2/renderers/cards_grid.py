from __future__ import annotations

from .common import add_blank_slide, add_card, add_page_number, add_textbox, fill_background, rgb
from ..schema import CardsGridSlide
from ..theme_loader import ThemeSpec


def _card_positions(card_count: int) -> list[tuple[float, float, float, float]]:
    if card_count == 2:
        return [(0.9, 1.5, 5.55, 4.55), (6.05, 1.5, 5.55, 4.55)]
    if card_count == 3:
        return [(0.85, 1.64, 3.72, 4.2), (4.79, 1.64, 3.72, 4.2), (8.73, 1.64, 3.72, 4.2)]
    return [(0.9, 1.52, 5.5, 2.1), (6.0, 1.52, 5.5, 2.1), (0.9, 3.92, 5.5, 2.1), (6.0, 3.92, 5.5, 2.1)]


def render_cards_grid(prs, slide_data: CardsGridSlide, theme: ThemeSpec, log, slide_number: int, total_slides: int):
    slide = add_blank_slide(prs)
    fill_background(slide, theme)
    add_textbox(
        slide,
        left=0.78,
        top=0.5,
        width=11.7,
        height=0.55,
        text=slide_data.title,
        font_name=theme.fonts.title,
        font_size=theme.font_sizes.title,
        color_hex=theme.colors.primary,
        bold=True,
    )
    if slide_data.heading:
        add_textbox(
            slide,
            left=0.82,
            top=1.04,
            width=11.5,
            height=0.28,
            text=slide_data.heading,
            font_name=theme.fonts.body,
            font_size=theme.font_sizes.small + 1,
            color_hex=theme.colors.text_sub,
            bold=True,
        )

    for index, (card, position) in enumerate(zip(slide_data.cards, _card_positions(len(slide_data.cards)))):
        left, top, width, height = position
        shape = add_card(slide, left, top, width, height, theme)
        if index % 2 == 0:
            shape.fill.fore_color.rgb = rgb("#FCF7F8")
        add_textbox(
            slide,
            left=left + 0.14,
            top=top + 0.16,
            width=width - 0.28,
            height=0.34,
            text=card.title,
            font_name=theme.fonts.title,
            font_size=theme.font_sizes.subtitle,
            color_hex=theme.colors.secondary,
            bold=True,
        )
        if card.body:
            add_textbox(
                slide,
                left=left + 0.14,
                top=top + 0.6,
                width=width - 0.28,
                height=height - 0.78,
                text=card.body,
                font_name=theme.fonts.body,
                font_size=theme.font_sizes.small + 1,
                color_hex=theme.colors.text_main,
            )

    log.info(f"{slide_data.slide_id}: rendered semantic cards grid layout.")
    add_page_number(slide, slide_number, total_slides, theme)
    return slide
