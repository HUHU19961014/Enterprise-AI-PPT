import unittest

from tools.sie_autoppt.v2.design_engine.layout_strategy import decide_layout_strategy
from tools.sie_autoppt.v2.design_engine.visual_balance import ContentBlock, calculate_balance_score
from tools.sie_autoppt.v2.design_engine.whitespace import calculate_whitespace_ratio


class V2DesignEngineTests(unittest.TestCase):
    def test_balance_score_reports_left_heavy_when_left_content_dominates(self):
        blocks = [
            ContentBlock(content="A", length=80, priority=5, lane="left", media_type="text"),
            ContentBlock(content="B", length=20, priority=2, lane="right", media_type="text"),
        ]

        score = calculate_balance_score(blocks)

        self.assertGreater(score.left_weight, score.right_weight)
        self.assertEqual(score.suggestion, "expand_left")

    def test_whitespace_ratio_decreases_when_content_gets_denser(self):
        sparse = calculate_whitespace_ratio(30)
        dense = calculate_whitespace_ratio(220)

        self.assertGreater(sparse, dense)
        self.assertGreaterEqual(dense, 0.15)
        self.assertLessEqual(sparse, 0.4)

    def test_layout_strategy_prefers_two_columns_for_comparison_content(self):
        strategy = decide_layout_strategy(
            intent="analysis",
            blocks=[
                ContentBlock(content="left-1", length=20, priority=3, lane="left", media_type="text"),
                ContentBlock(content="right-1", length=22, priority=3, lane="right", media_type="text"),
            ],
            has_comparison=True,
            has_image=False,
        )

        self.assertEqual(strategy.layout_preference, "two_columns")
        self.assertIn(strategy.balance.suggestion, {"balanced", "expand_left", "expand_right"})


if __name__ == "__main__":
    unittest.main()
