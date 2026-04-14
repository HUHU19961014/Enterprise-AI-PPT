from __future__ import annotations

from pptx.enum.text import MSO_ANCHOR, PP_ALIGN

from ..schema import TitleOnlySlide
from .common import RenderContext, add_blank_slide, add_card, add_page_number, add_textbox, fill_background
from .layout_constants import TITLE_ONLY


def render_title_only(ctx: RenderContext, slide_data: TitleOnlySlide):
    prs = ctx.prs
    theme = ctx.theme
    slide_number = ctx.slide_number
    total_slides = ctx.total_slides
    slide = add_blank_slide(prs)
    fill_background(slide, theme)
    add_card(
        slide,
        TITLE_ONLY.card.left,
        TITLE_ONLY.card.top,
        TITLE_ONLY.card.width,
        TITLE_ONLY.card.height,
        theme,
    )
    add_textbox(
        slide,
        left=TITLE_ONLY.title_left,
        top=TITLE_ONLY.title_top,
        width=TITLE_ONLY.title_width,
        height=TITLE_ONLY.title_height,
        text=slide_data.title,
        font_name=theme.fonts.title,
        font_size=theme.font_sizes.title + 4,
        color_hex=theme.colors.primary,
        bold=True,
        align=PP_ALIGN.CENTER,
        vertical_anchor=MSO_ANCHOR.MIDDLE,
    )
    add_page_number(slide, slide_number, total_slides, theme)
    return slide
