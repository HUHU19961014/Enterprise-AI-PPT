from __future__ import annotations

from ..schema import TitleContentSlide
from .common import (
    RenderContext,
    add_blank_slide,
    add_bullet_list,
    add_card,
    add_page_number,
    add_timeline_flow,
    add_textbox,
    fill_background,
    parse_timeline_items,
    resolve_body_font_size,
)
from .layout_constants import TITLE_BAND, TITLE_CONTENT


def render_title_content(ctx: RenderContext, slide_data: TitleContentSlide):
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
    add_card(
        slide,
        TITLE_CONTENT.card.left,
        TITLE_CONTENT.card.top,
        TITLE_CONTENT.card.width,
        TITLE_CONTENT.card.height,
        theme,
    )
    timeline_items = parse_timeline_items(list(slide_data.content))
    if timeline_items:
        log.info(f"{slide_data.slide_id}: rendered staged content as timeline visualization.")
        add_timeline_flow(
            slide,
            timeline_items,
            left=TITLE_CONTENT.timeline_left,
            top=TITLE_CONTENT.timeline_top,
            width=TITLE_CONTENT.timeline_width,
            height=TITLE_CONTENT.timeline_height,
            theme=theme,
        )
    else:
        font_size = resolve_body_font_size(theme, len(slide_data.content))
        if len(slide_data.content) > 6:
            log.warn(f"{slide_data.slide_id}: content is dense, reduced bullet font size to {font_size}.")
        add_bullet_list(
            slide,
            slide_data.content,
            left=TITLE_CONTENT.content_left,
            top=TITLE_CONTENT.content_top,
            width=TITLE_CONTENT.content_width,
            height=TITLE_CONTENT.content_height,
            theme=theme,
            font_size=font_size,
        )
    add_page_number(slide, slide_number, total_slides, theme)
    return slide
