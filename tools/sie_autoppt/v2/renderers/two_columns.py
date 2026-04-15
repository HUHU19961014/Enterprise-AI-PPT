from __future__ import annotations

from typing import Literal

from ..schema import TwoColumnsSlide
from .common import (
    RenderContext,
    add_blank_slide,
    add_bullet_list,
    add_card,
    add_comparison_table,
    add_page_number,
    add_textbox,
    fill_background,
    resolve_body_font_size,
    should_render_comparison_table,
)
from .layout_constants import TITLE_BAND, TWO_COLUMNS, calculate_two_column_layout


def _resolve_density_factor(
    *,
    style_variant: Literal["minimal", "standard", "decorative"] | None,
    left_items: int,
    right_items: int,
) -> float:
    dense_baseline = 0.8 if max(left_items, right_items) > 5 else 0.4
    if style_variant == "minimal":
        return max(0.0, dense_baseline - 0.25)
    if style_variant == "decorative":
        return min(1.0, dense_baseline + 0.25)
    return dense_baseline


def render_two_columns(ctx: RenderContext, slide_data: TwoColumnsSlide):
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

    dynamic_layout = calculate_two_column_layout(
        left_items_count=len(slide_data.left.items),
        right_items_count=len(slide_data.right.items),
        density_factor=_resolve_density_factor(
            style_variant=slide_data.style_variant,
            left_items=len(slide_data.left.items),
            right_items=len(slide_data.right.items),
        ),
    )
    card_top = dynamic_layout.card_top
    card_height = dynamic_layout.card_height
    left_left = dynamic_layout.left_left
    right_left = dynamic_layout.right_left
    left_card_width = dynamic_layout.left_card_width or TWO_COLUMNS.card_width
    right_card_width = dynamic_layout.right_card_width or TWO_COLUMNS.card_width
    if should_render_comparison_table(
        slide_data.left.heading,
        slide_data.right.heading,
        list(slide_data.left.items),
        list(slide_data.right.items),
    ):
        log.info(f"{slide_data.slide_id}: rendered balanced two-column content as comparison table.")
        add_comparison_table(
            slide,
            left_heading=slide_data.left.heading,
            right_heading=slide_data.right.heading,
            left_items=list(slide_data.left.items),
            right_items=list(slide_data.right.items),
            left=TWO_COLUMNS.table_left,
            top=TWO_COLUMNS.table_top,
            width=TWO_COLUMNS.table_width,
            height=TWO_COLUMNS.table_height,
            theme=theme,
        )
    else:
        add_card(slide, left_left, card_top, left_card_width, card_height, theme)
        add_card(slide, right_left, card_top, right_card_width, card_height, theme)
        add_textbox(
            slide,
            left=left_left + TWO_COLUMNS.inner_card_text_padding,
            top=card_top + TWO_COLUMNS.heading_top_offset,
            width=left_card_width - TWO_COLUMNS.inner_card_text_padding * 2,
            height=TWO_COLUMNS.heading_height,
            text=slide_data.left.heading,
            font_name=theme.fonts.title,
            font_size=theme.font_sizes.subtitle + 1,
            color_hex=theme.colors.secondary,
            bold=True,
        )
        add_textbox(
            slide,
            left=right_left + TWO_COLUMNS.inner_card_text_padding,
            top=card_top + TWO_COLUMNS.heading_top_offset,
            width=right_card_width - TWO_COLUMNS.inner_card_text_padding * 2,
            height=TWO_COLUMNS.heading_height,
            text=slide_data.right.heading,
            font_name=theme.fonts.title,
            font_size=theme.font_sizes.subtitle + 1,
            color_hex=theme.colors.secondary,
            bold=True,
        )

        left_font_size = min(resolve_body_font_size(theme, len(slide_data.left.items)), int(dynamic_layout.font_size))
        right_font_size = min(resolve_body_font_size(theme, len(slide_data.right.items)), int(dynamic_layout.font_size))
        if len(slide_data.left.items) > 5 or len(slide_data.right.items) > 5:
            log.warn(f"{slide_data.slide_id}: two_columns content is dense and may need manual review.")
        add_bullet_list(
            slide,
            slide_data.left.items,
            left=left_left + TWO_COLUMNS.inner_horizontal_padding,
            top=card_top + TWO_COLUMNS.bullet_top_offset,
            width=left_card_width - TWO_COLUMNS.inner_horizontal_padding * 2,
            height=card_height - TWO_COLUMNS.bullet_bottom_padding,
            theme=theme,
            font_size=left_font_size,
        )
        add_bullet_list(
            slide,
            slide_data.right.items,
            left=right_left + TWO_COLUMNS.inner_horizontal_padding,
            top=card_top + TWO_COLUMNS.bullet_top_offset,
            width=right_card_width - TWO_COLUMNS.inner_horizontal_padding * 2,
            height=card_height - TWO_COLUMNS.bullet_bottom_padding,
            theme=theme,
            font_size=right_font_size,
        )
    add_page_number(slide, slide_number, total_slides, theme)
    return slide
