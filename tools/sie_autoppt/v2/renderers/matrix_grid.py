from __future__ import annotations

from .common import add_blank_slide, add_card, add_page_number, add_textbox, fill_background, rgb
from ..schema import MatrixGridSlide
from ..theme_loader import ThemeSpec


def render_matrix_grid(prs, slide_data: MatrixGridSlide, theme: ThemeSpec, log, slide_number: int, total_slides: int):
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
            top=1.05,
            width=11.5,
            height=0.28,
            text=slide_data.heading,
            font_name=theme.fonts.body,
            font_size=theme.font_sizes.small + 1,
            color_hex=theme.colors.text_sub,
            bold=True,
        )

    if slide_data.x_axis:
        add_textbox(
            slide,
            left=5.3,
            top=6.03,
            width=2.6,
            height=0.2,
            text=slide_data.x_axis,
            font_name=theme.fonts.body,
            font_size=theme.font_sizes.small,
            color_hex=theme.colors.text_sub,
            bold=True,
        )
    if slide_data.y_axis:
        add_textbox(
            slide,
            left=0.84,
            top=3.35,
            width=0.9,
            height=0.35,
            text=slide_data.y_axis,
            font_name=theme.fonts.body,
            font_size=theme.font_sizes.small,
            color_hex=theme.colors.text_sub,
            bold=True,
        )

    add_card(slide, 1.55, 1.42, 10.95, 4.65, theme)
    positions = [
        (1.78, 1.68),
        (7.08, 1.68),
        (1.78, 4.01),
        (7.08, 4.01),
    ]
    palette = ["#FFF4F4", "#FFF8EE", "#F5F9FF", "#EEF8F2"]

    for index, cell in enumerate(slide_data.cells[:4]):
        left, top = positions[index]
        shape = add_card(slide, left, top, 5.14, 2.17, theme)
        shape.fill.fore_color.rgb = rgb(palette[index % len(palette)])
        add_textbox(
            slide,
            left=left + 0.14,
            top=top + 0.14,
            width=4.86,
            height=0.3,
            text=cell.title,
            font_name=theme.fonts.title,
            font_size=theme.font_sizes.subtitle,
            color_hex=theme.colors.secondary,
            bold=True,
        )
        if cell.body:
            add_textbox(
                slide,
                left=left + 0.14,
                top=top + 0.56,
                width=4.86,
                height=1.24,
                text=cell.body,
                font_name=theme.fonts.body,
                font_size=theme.font_sizes.small + 1,
                color_hex=theme.colors.text_main,
            )

    log.info(f"{slide_data.slide_id}: rendered semantic matrix grid layout.")
    add_page_number(slide, slide_number, total_slides, theme)
    return slide
