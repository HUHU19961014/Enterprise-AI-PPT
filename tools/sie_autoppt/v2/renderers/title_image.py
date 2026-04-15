from __future__ import annotations

from ..schema import TitleImageSlide
from .common import (
    RenderContext,
    add_architecture_placeholder,
    add_blank_slide,
    add_bullet_list,
    add_capability_map,
    add_card,
    add_page_number,
    add_textbox,
    classify_placeholder_visual,
    add_local_image_or_placeholder,
    fill_background,
    resolve_body_font_size,
)
from .layout_constants import TITLE_BAND, TITLE_IMAGE


def render_title_image(ctx: RenderContext, slide_data: TitleImageSlide):
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
        TITLE_IMAGE.left_card.left,
        TITLE_IMAGE.left_card.top,
        TITLE_IMAGE.left_card.width,
        TITLE_IMAGE.left_card.height,
        theme,
    )
    add_card(
        slide,
        TITLE_IMAGE.right_card.left,
        TITLE_IMAGE.right_card.top,
        TITLE_IMAGE.right_card.width,
        TITLE_IMAGE.right_card.height,
        theme,
    )
    add_bullet_list(
        slide,
        slide_data.content,
        left=TITLE_IMAGE.content_left,
        top=TITLE_IMAGE.content_top,
        width=TITLE_IMAGE.content_width,
        height=TITLE_IMAGE.content_height,
        theme=theme,
        font_size=resolve_body_font_size(theme, len(slide_data.content)),
    )
    visual_type = classify_placeholder_visual(slide_data.title, slide_data.image.caption, list(slide_data.content))
    if slide_data.image.mode == "placeholder" and visual_type == "architecture":
        log.info(f"{slide_data.slide_id}: rendered placeholder as architecture diagram.")
        add_architecture_placeholder(
            slide,
            caption=slide_data.image.caption,
            layers=list(slide_data.content),
            left=TITLE_IMAGE.visual_left,
            top=TITLE_IMAGE.visual_top,
            width=TITLE_IMAGE.visual_width,
            height=TITLE_IMAGE.visual_height,
            theme=theme,
        )
    elif slide_data.image.mode == "placeholder" and visual_type == "map":
        log.info(f"{slide_data.slide_id}: rendered placeholder as capability map.")
        add_capability_map(
            slide,
            caption=slide_data.image.caption,
            nodes=list(slide_data.content),
            left=TITLE_IMAGE.visual_left,
            top=TITLE_IMAGE.visual_top,
            width=TITLE_IMAGE.visual_width,
            height=TITLE_IMAGE.visual_height,
            theme=theme,
        )
    else:
        add_local_image_or_placeholder(
            slide,
            image_mode=slide_data.image.mode,
            image_path=slide_data.image.path,
            caption=slide_data.image.caption,
            left=TITLE_IMAGE.visual_left,
            top=TITLE_IMAGE.visual_top,
            width=TITLE_IMAGE.visual_width,
            height=TITLE_IMAGE.visual_height,
            theme=theme,
            log=log,
        )
    add_page_number(slide, slide_number, total_slides, theme)
    return slide
