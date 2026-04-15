from __future__ import annotations

from ..schema import MatrixGridSlide
from .common import RenderContext, add_blank_slide, add_card, add_page_number, add_textbox, fill_background, rgb
from .layout_constants import TITLE_BAND, resolve_matrix_grid_layout


def render_matrix_grid(ctx: RenderContext, slide_data: MatrixGridSlide):
    prs = ctx.prs
    theme = ctx.theme
    log = ctx.log
    slide_number = ctx.slide_number
    total_slides = ctx.total_slides
    matrix_layout = resolve_matrix_grid_layout(theme)
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
            top=matrix_layout.heading_top,
            width=TITLE_BAND.subtitle_width,
            height=TITLE_BAND.subtitle_height,
            text=slide_data.heading,
            font_name=theme.fonts.body,
            font_size=theme.font_sizes.small + 1,
            color_hex=theme.colors.text_sub,
            bold=True,
        )

    if slide_data.x_axis:
        add_textbox(
            slide,
            left=matrix_layout.x_axis_left,
            top=matrix_layout.x_axis_top,
            width=matrix_layout.x_axis_width,
            height=matrix_layout.x_axis_height,
            text=slide_data.x_axis,
            font_name=theme.fonts.body,
            font_size=theme.font_sizes.small,
            color_hex=theme.colors.text_sub,
            bold=True,
        )
    if slide_data.y_axis:
        add_textbox(
            slide,
            left=matrix_layout.y_axis_left,
            top=matrix_layout.y_axis_top,
            width=matrix_layout.y_axis_width,
            height=matrix_layout.y_axis_height,
            text=slide_data.y_axis,
            font_name=theme.fonts.body,
            font_size=theme.font_sizes.small,
            color_hex=theme.colors.text_sub,
            bold=True,
        )

    add_card(
        slide,
        matrix_layout.outer_card.left,
        matrix_layout.outer_card.top,
        matrix_layout.outer_card.width,
        matrix_layout.outer_card.height,
        theme,
    )

    for index, cell in enumerate(slide_data.cells[:4]):
        left, top = matrix_layout.cell_positions[index]
        shape = add_card(slide, left, top, matrix_layout.cell_width, matrix_layout.cell_height, theme)
        role = matrix_layout.palette_roles[index % len(matrix_layout.palette_roles)]
        shape.fill.fore_color.rgb = rgb(getattr(theme.colors, role))
        add_textbox(
            slide,
            left=left + matrix_layout.card_title_left_padding,
            top=top + matrix_layout.card_title_top_padding,
            width=matrix_layout.card_title_width,
            height=matrix_layout.card_title_height,
            text=cell.title,
            font_name=theme.fonts.title,
            font_size=theme.font_sizes.subtitle,
            color_hex=theme.colors.secondary,
            bold=True,
        )
        if cell.body:
            add_textbox(
                slide,
                left=left + matrix_layout.card_title_left_padding,
                top=top + matrix_layout.card_body_top_offset,
                width=matrix_layout.card_body_width,
                height=matrix_layout.card_body_height,
                text=cell.body,
                font_name=theme.fonts.body,
                font_size=theme.font_sizes.small + 1,
                color_hex=theme.colors.text_main,
            )

    log.info(f"{slide_data.slide_id}: rendered semantic matrix grid layout.")
    add_page_number(slide, slide_number, total_slides, theme)
    return slide
