from __future__ import annotations

from ..schema import TitleImageSlide
from ..theme_loader import ThemeSpec
from .common import (
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


def render_title_image(prs, slide_data: TitleImageSlide, theme: ThemeSpec, log, slide_number: int, total_slides: int):
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
    add_card(slide, 0.78, 1.32, 5.2, 4.85, theme)
    add_card(slide, 6.2, 1.32, 6.3, 4.85, theme)
    add_bullet_list(
        slide,
        slide_data.content,
        left=1.0,
        top=1.65,
        width=4.75,
        height=4.1,
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
            left=6.45,
            top=1.58,
            width=5.8,
            height=4.33,
            theme=theme,
        )
    elif slide_data.image.mode == "placeholder" and visual_type == "map":
        log.info(f"{slide_data.slide_id}: rendered placeholder as capability map.")
        add_capability_map(
            slide,
            caption=slide_data.image.caption,
            nodes=list(slide_data.content),
            left=6.45,
            top=1.58,
            width=5.8,
            height=4.33,
            theme=theme,
        )
    else:
        add_local_image_or_placeholder(
            slide,
            image_mode=slide_data.image.mode,
            image_path=slide_data.image.path,
            caption=slide_data.image.caption,
            left=6.45,
            top=1.58,
            width=5.8,
            height=4.33,
            theme=theme,
            log=log,
        )
    add_page_number(slide, slide_number, total_slides, theme)
    return slide
