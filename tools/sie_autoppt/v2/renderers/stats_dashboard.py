from __future__ import annotations

from ..schema import StatsDashboardSlide
from ..theme_loader import ThemeSpec
from .common import add_blank_slide, add_bullet_list, add_card, add_page_number, add_textbox, fill_background


def _metric_grid(metrics_count: int) -> tuple[int, int]:
    if metrics_count <= 2:
        return 2, 1
    if metrics_count <= 4:
        return 2, 2
    return 3, 2


def render_stats_dashboard(prs, slide_data: StatsDashboardSlide, theme: ThemeSpec, log, slide_number: int, total_slides: int):
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
            top=1.06,
            width=11.5,
            height=0.28,
            text=slide_data.heading,
            font_name=theme.fonts.body,
            font_size=theme.font_sizes.small + 1,
            color_hex=theme.colors.text_sub,
            bold=True,
        )

    metrics_top = 1.42
    metrics_height = 3.6 if slide_data.insights else 4.65
    metrics_width = 11.72
    add_card(slide, 0.78, metrics_top, metrics_width, metrics_height, theme)

    cols, rows = _metric_grid(len(slide_data.metrics))
    gap_x = 0.16
    gap_y = 0.16
    card_width = (metrics_width - 0.36 - gap_x * (cols - 1)) / cols
    card_height = (metrics_height - 0.34 - gap_y * (rows - 1)) / rows

    for index, metric in enumerate(slide_data.metrics):
        row = index // cols
        col = index % cols
        left = 0.96 + col * (card_width + gap_x)
        top = metrics_top + 0.18 + row * (card_height + gap_y)
        add_card(slide, left, top, card_width, card_height, theme)
        add_textbox(
            slide,
            left=left + 0.12,
            top=top + 0.14,
            width=card_width - 0.24,
            height=0.28,
            text=metric.label,
            font_name=theme.fonts.body,
            font_size=theme.font_sizes.small + 1,
            color_hex=theme.colors.text_sub,
            bold=True,
        )
        add_textbox(
            slide,
            left=left + 0.12,
            top=top + 0.48,
            width=card_width - 0.24,
            height=0.54,
            text=metric.value,
            font_name=theme.fonts.title,
            font_size=theme.font_sizes.title + 2,
            color_hex=theme.colors.primary,
            bold=True,
        )
        if metric.note:
            add_textbox(
                slide,
                left=left + 0.12,
                top=top + card_height - 0.62,
                width=card_width - 0.24,
                height=0.4,
                text=metric.note,
                font_name=theme.fonts.body,
                font_size=theme.font_sizes.small,
                color_hex=theme.colors.text_main,
            )

    if slide_data.insights:
        add_card(slide, 0.78, 5.22, 11.72, 1.0, theme)
        add_textbox(
            slide,
            left=1.0,
            top=5.35,
            width=2.0,
            height=0.24,
            text="Key Insights",
            font_name=theme.fonts.title,
            font_size=theme.font_sizes.small + 1,
            color_hex=theme.colors.secondary,
            bold=True,
        )
        add_bullet_list(
            slide,
            list(slide_data.insights),
            left=2.6,
            top=5.3,
            width=9.45,
            height=0.62,
            theme=theme,
            font_size=theme.font_sizes.small,
        )

    log.info(f"{slide_data.slide_id}: rendered semantic stats dashboard layout.")
    add_page_number(slide, slide_number, total_slides, theme)
    return slide
