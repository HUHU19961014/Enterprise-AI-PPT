import unittest

from tools.sie_autoppt.v2.renderers.layout_constants import (
    CARDS_GRID,
    MATRIX_GRID,
    SECTION_BREAK,
    STATS_DASHBOARD,
    TIMELINE,
    TITLE_BAND,
    TITLE_CONTENT,
    TITLE_IMAGE,
    TITLE_ONLY,
    TWO_COLUMNS,
    cards_grid_positions,
    resolve_matrix_grid_layout,
)
from tools.sie_autoppt.v2.theme_loader import ThemeSpec


class V2LayoutConstantsTests(unittest.TestCase):
    def test_title_band_and_core_layouts_expose_expected_geometry(self):
        self.assertEqual(TITLE_BAND.left, 0.78)
        self.assertEqual(TITLE_BAND.top, 0.5)
        self.assertGreater(TITLE_CONTENT.card.width, 11.0)
        self.assertGreater(TITLE_ONLY.card.height, 4.0)
        self.assertGreater(TITLE_IMAGE.right_card.width, TITLE_IMAGE.left_card.width)
        self.assertGreater(TIMELINE.flow_width, 11.0)
        self.assertEqual(SECTION_BREAK.title_top, 1.55)
        self.assertEqual(STATS_DASHBOARD.metrics_top, 1.42)
        self.assertEqual(len(MATRIX_GRID.cell_positions), 4)

    def test_cards_grid_positions_cover_supported_card_counts(self):
        two_cards = cards_grid_positions(2)
        three_cards = cards_grid_positions(3)
        four_cards = cards_grid_positions(4)
        two_cards_again = cards_grid_positions(2)

        self.assertEqual(len(two_cards), 2)
        self.assertEqual(len(three_cards), 3)
        self.assertEqual(len(four_cards), 4)
        self.assertIs(two_cards, two_cards_again)
        self.assertIsInstance(two_cards, tuple)
        self.assertEqual(two_cards[0][2], TWO_COLUMNS.card_width)
        self.assertEqual(TWO_COLUMNS.inner_card_text_padding, 0.22)
        self.assertEqual(CARDS_GRID.card_title_left_padding, 0.14)
        self.assertEqual(CARDS_GRID.card_body_top_offset, 0.6)

    def test_resolve_matrix_grid_layout_uses_theme_override_when_provided(self):
        theme = ThemeSpec.model_validate(
            {
                "theme_name": "custom",
                "page": {"width": 13.333, "height": 7.5},
                "colors": {
                    "primary": "#123456",
                    "secondary": "#234567",
                    "text_main": "#345678",
                    "text_sub": "#456789",
                    "bg": "#56789A",
                    "card_bg": "#6789AB",
                    "line": "#789ABC",
                },
                "fonts": {"title": "Arial", "body": "Arial", "fallback": "Arial"},
                "font_sizes": {"title": 28, "subtitle": 18, "body": 14, "small": 12},
                "spacing": {
                    "page_margin_left": 0.5,
                    "page_margin_right": 0.5,
                    "page_margin_top": 0.5,
                    "page_margin_bottom": 0.5,
                    "block_gap": 0.2,
                },
                "layouts": {"matrix_outer_card": {"left": 1.2, "top": 1.1, "width": 10.6, "height": 4.9}},
            }
        )

        resolved = resolve_matrix_grid_layout(theme)

        self.assertEqual(resolved.outer_card.left, 1.2)
        self.assertEqual(resolved.outer_card.top, 1.1)
        self.assertEqual(resolved.outer_card.width, 10.6)
        self.assertEqual(resolved.outer_card.height, 4.9)


if __name__ == "__main__":
    unittest.main()
