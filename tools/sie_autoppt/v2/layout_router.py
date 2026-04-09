from __future__ import annotations

from pptx import Presentation

from .renderers.cards_grid import render_cards_grid
from .renderers.matrix_grid import render_matrix_grid
from .renderers.section_break import render_section_break
from .renderers.stats_dashboard import render_stats_dashboard
from .renderers.timeline import render_timeline
from .renderers.title_content import render_title_content
from .renderers.title_image import render_title_image
from .renderers.title_only import render_title_only
from .renderers.two_columns import render_two_columns
from .schema import SlideModel
from .theme_loader import ThemeSpec


def render_slide(
    prs: Presentation,
    slide_data: SlideModel,
    theme: ThemeSpec,
    log,
    slide_number: int,
    total_slides: int,
):
    layout = slide_data.layout
    if layout == "section_break":
        return render_section_break(prs, slide_data, theme, log, slide_number, total_slides)
    if layout == "title_only":
        return render_title_only(prs, slide_data, theme, log, slide_number, total_slides)
    if layout == "title_content":
        return render_title_content(prs, slide_data, theme, log, slide_number, total_slides)
    if layout == "two_columns":
        return render_two_columns(prs, slide_data, theme, log, slide_number, total_slides)
    if layout == "title_image":
        return render_title_image(prs, slide_data, theme, log, slide_number, total_slides)
    if layout == "timeline":
        return render_timeline(prs, slide_data, theme, log, slide_number, total_slides)
    if layout == "stats_dashboard":
        return render_stats_dashboard(prs, slide_data, theme, log, slide_number, total_slides)
    if layout == "matrix_grid":
        return render_matrix_grid(prs, slide_data, theme, log, slide_number, total_slides)
    if layout == "cards_grid":
        return render_cards_grid(prs, slide_data, theme, log, slide_number, total_slides)
    raise ValueError(f"Unsupported layout: {layout}")
