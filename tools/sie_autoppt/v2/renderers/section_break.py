from __future__ import annotations

from pptx.enum.text import MSO_ANCHOR, PP_ALIGN

from ..schema import SectionBreakSlide
from .common import RenderContext, add_blank_slide, add_page_number, add_textbox, fill_background
from .layout_constants import SECTION_BREAK


def render_section_break(ctx: RenderContext, slide_data: SectionBreakSlide):
    prs = ctx.prs
    theme = ctx.theme
    slide_number = ctx.slide_number
    total_slides = ctx.total_slides
    slide = add_blank_slide(prs)
    fill_background(slide, theme, theme.colors.primary)
    add_textbox(
        slide,
        left=SECTION_BREAK.title_left,
        top=SECTION_BREAK.title_top,
        width=SECTION_BREAK.title_width,
        height=SECTION_BREAK.title_height,
        text=slide_data.title,
        font_name=theme.fonts.title,
        font_size=theme.font_sizes.title + 6,
        color_hex=theme.colors.card_bg,
        bold=True,
        align=PP_ALIGN.CENTER,
        vertical_anchor=MSO_ANCHOR.MIDDLE,
    )
    if slide_data.subtitle:
        add_textbox(
            slide,
            left=SECTION_BREAK.subtitle_left,
            top=SECTION_BREAK.subtitle_top,
            width=SECTION_BREAK.subtitle_width,
            height=SECTION_BREAK.subtitle_height,
            text=slide_data.subtitle,
            font_name=theme.fonts.body,
            font_size=theme.font_sizes.subtitle + 1,
            color_hex=theme.colors.card_bg,
            align=PP_ALIGN.CENTER,
            vertical_anchor=MSO_ANCHOR.MIDDLE,
        )
    add_page_number(slide, slide_number, total_slides, theme)
    return slide
