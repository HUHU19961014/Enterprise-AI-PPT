import unittest

from tools.sie_autoppt.v2.content_rewriter import rewrite_deck, rewrite_slide
from tools.sie_autoppt.v2.quality_checks import quality_gate
from tools.sie_autoppt.v2.schema import validate_deck_payload


class ContentRewriterTests(unittest.TestCase):
    def test_rewrite_slide_compresses_title_content(self):
        gate_result = quality_gate(
            {
                "meta": {"title": "Test", "theme": "business_red", "language": "zh-CN", "author": "AI", "version": "2.0"},
                "slides": [
                    {
                        "slide_id": "s1",
                        "layout": "title_content",
                        "title": "这是一个明显过长并且需要压缩表达的业务分析标题",
                        "content": [
                            "第一条内容明显过长，需要压缩到更适合页面承载的长度，并保留核心信息。",
                            "第二条内容也非常长，需要继续压缩表达。",
                            "第三条",
                            "第四条",
                            "第五条",
                            "第六条",
                            "第七条",
                        ],
                    }
                ],
            }
        )
        slide = gate_result.validated_deck.deck.model_dump(mode="json")["slides"][0]
        rewritten, actions = rewrite_slide(slide, list(gate_result.all_issues()))

        self.assertLessEqual(len(rewritten["title"]), len(slide["title"]))
        self.assertLessEqual(len(rewritten["content"]), 6)
        self.assertGreater(len(actions), 0)

    def test_rewrite_deck_rebalances_two_columns(self):
        validated = validate_deck_payload(
            {
                "meta": {"title": "Test", "theme": "business_red", "language": "zh-CN", "author": "AI", "version": "2.0"},
                "slides": [
                    {
                        "slide_id": "s1",
                        "layout": "two_columns",
                        "title": "双栏内容页",
                        "left": {
                            "heading": "左侧",
                            "items": ["事项一", "事项二", "事项三", "事项四", "事项五", "事项六"],
                        },
                        "right": {
                            "heading": "右侧",
                            "items": ["要点甲"],
                        },
                    }
                ],
            }
        )
        initial_gate = quality_gate(validated)
        rewrite_result = rewrite_deck(validated, initial_gate)

        self.assertTrue(rewrite_result.applied)
        rewritten_slide = rewrite_result.validated_deck.deck.model_dump(mode="json")["slides"][0]
        self.assertLessEqual(len(rewritten_slide["left"]["items"]), 4)
        self.assertLessEqual(abs(len(rewritten_slide["left"]["items"]) - len(rewritten_slide["right"]["items"])), 3)
