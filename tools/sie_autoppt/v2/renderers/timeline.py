from __future__ import annotations

from ..schema import TimelineSlide
from .common import RenderContext, add_blank_slide, add_card, add_page_number, add_textbox, add_timeline_flow, fill_background
from .layout_constants import TIMELINE, TITLE_BAND


def render_timeline(ctx: RenderContext, slide_data: TimelineSlide):
    prs = ctx.prs
    theme = ctx.theme
    log = ctx.log
    slide_number = ctx.slide_number
    total_slides = ctx.total_slides
    slide = add_blank_slide(prs)
    fill_background(slide, theme)
    add_textbox(
        slide,
        left=TITLE_BAND.left,
        top=TITLE_BAND.top,
        width=TITLE_BAND.width,
        height=TITLE_BAND.height,
        text=slide_data.title,
        font_name=theme.fonts.title,
        font_size=theme.font_sizes.title,
        color_hex=theme.colors.primary,
        bold=True,
    )
    if slide_data.heading:
        add_textbox(
            slide,
            left=TITLE_BAND.subtitle_left,
            top=TIMELINE.subtitle_top,
            width=TITLE_BAND.subtitle_width,
            height=TITLE_BAND.subtitle_height,
            text=slide_data.heading,
            font_name=theme.fonts.body,
            font_size=theme.font_sizes.small + 1,
            color_hex=theme.colors.text_sub,
            bold=True,
        )

    add_card(slide, TIMELINE.card.left, TIMELINE.card.top, TIMELINE.card.width, TIMELINE.card.height, theme)
    add_timeline_flow(
        slide,
        [(stage.title, stage.detail or stage.title) for stage in slide_data.stages],
        left=TIMELINE.flow_left,
        top=TIMELINE.flow_top,
        width=TIMELINE.flow_width,
        height=TIMELINE.flow_height,
        theme=theme,
    )
    log.info(f"{slide_data.slide_id}: rendered semantic timeline layout.")
    add_page_number(slide, slide_number, total_slides, theme)
    return slide
