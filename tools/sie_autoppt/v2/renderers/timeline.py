from __future__ import annotations

from ..schema import TimelineSlide
from ..theme_loader import ThemeSpec
from .common import add_blank_slide, add_card, add_page_number, add_textbox, add_timeline_flow, fill_background


def render_timeline(prs, slide_data: TimelineSlide, theme: ThemeSpec, log, slide_number: int, total_slides: int):
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
            top=1.08,
            width=11.5,
            height=0.28,
            text=slide_data.heading,
            font_name=theme.fonts.body,
            font_size=theme.font_sizes.small + 1,
            color_hex=theme.colors.text_sub,
            bold=True,
        )

    add_card(slide, 0.78, 1.42, 11.72, 4.8, theme)
    add_timeline_flow(
        slide,
        [(stage.title, stage.detail or stage.title) for stage in slide_data.stages],
        left=1.0,
        top=1.7,
        width=11.1,
        height=4.1,
        theme=theme,
    )
    log.info(f"{slide_data.slide_id}: rendered semantic timeline layout.")
    add_page_number(slide, slide_number, total_slides, theme)
    return slide
