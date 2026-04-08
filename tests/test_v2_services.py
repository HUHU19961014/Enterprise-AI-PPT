import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.sie_autoppt.v2.schema import OutlineDocument, validate_deck_payload
from tools.sie_autoppt.v2.services import (
    DeckGenerationRequest,
    OutlineGenerationRequest,
    build_deck_prompts,
    build_outline_prompts,
    generate_semantic_deck_with_ai,
    make_v2_ppt,
    resolve_slide_bounds,
)


class V2ServiceTests(unittest.TestCase):
    def test_resolve_slide_bounds_supports_exact_and_range(self):
        self.assertEqual(
            resolve_slide_bounds(OutlineGenerationRequest(topic="AI", exact_slides=8)),
            (8, 8),
        )
        self.assertEqual(
            resolve_slide_bounds(OutlineGenerationRequest(topic="AI", min_slides=6, max_slides=9)),
            (6, 9),
        )

    def test_prompt_builders_include_core_constraints(self):
        outline_request = OutlineGenerationRequest(topic="AI strategy", min_slides=6, max_slides=8)
        developer_prompt, user_prompt = build_outline_prompts(outline_request)
        self.assertIn("Return 6-8 pages.", developer_prompt)
        self.assertIn("AI strategy", user_prompt)

        outline = OutlineDocument.model_validate(
            {
                "pages": [
                    {"page_no": 1, "title": "Context", "goal": "Set context."},
                    {"page_no": 2, "title": "Issues", "goal": "Explain key issues."},
                    {"page_no": 3, "title": "Plan", "goal": "Present the roadmap."},
                ]
            }
        )
        deck_request = DeckGenerationRequest(topic="AI strategy", outline=outline)
        developer_prompt, user_prompt = build_deck_prompts(deck_request)
        self.assertIn("section_break", developer_prompt)
        self.assertIn("intent", developer_prompt)
        self.assertIn("blocks", developer_prompt)
        self.assertIn("timeline", developer_prompt)
        self.assertIn("cards", developer_prompt)
        self.assertIn("stats", developer_prompt)
        self.assertIn("matrix", developer_prompt)
        self.assertIn('"page_no": 1', user_prompt)

    def test_make_v2_ppt_writes_rewritten_deck_artifacts(self):
        outline = OutlineDocument.model_validate(
            {
                "pages": [
                    {"page_no": 1, "title": "Context", "goal": "Set context."},
                    {"page_no": 2, "title": "Issues", "goal": "Explain key issues."},
                    {"page_no": 3, "title": "Plan", "goal": "Present the roadmap."},
                ]
            }
        )
        validated = validate_deck_payload(
            {
                "meta": {"title": "Test Deck", "theme": "business_red", "language": "zh-CN", "author": "AI", "version": "2.0"},
                "slides": [
                    {
                        "slide_id": "s1",
                        "layout": "title_content",
                        "title": "这是一个明显过长并且需要压缩表达的业务分析标题",
                        "content": [
                            "第一条内容明显过长，需要压缩到更适合页面承载的长度，并保留核心信息。",
                            "第二条内容也非常长，需要继续压缩表达，避免页面密度过高。",
                            "第三条需要保留。",
                            "第四条需要保留。",
                            "第五条需要保留。",
                            "第六条需要保留。",
                            "第七条用于测试自动合并。",
                        ],
                    }
                ],
            }
        )
        semantic_payload = {
            "meta": {"title": "Test Deck", "theme": "business_red", "language": "zh-CN", "author": "AI", "version": "2.0"},
            "slides": [
                {
                    "slide_id": "s1",
                    "title": "这是一个明显过长并且需要压缩表达的业务分析标题",
                    "intent": "analysis",
                    "blocks": [
                        {
                            "kind": "bullets",
                            "items": [
                                "第一条内容明显过长，需要压缩到更适合页面承载的长度，并保留核心信息。",
                                "第二条内容也非常长，需要继续压缩表达，避免页面密度过高。",
                                "第三条需要保留。",
                                "第四条需要保留。",
                                "第五条需要保留。",
                                "第六条需要保留。",
                                "第七条用于测试自动合并。",
                            ],
                        }
                    ],
                }
            ],
        }

        with patch("tools.sie_autoppt.v2.services.generate_outline_with_ai", return_value=outline), patch(
            "tools.sie_autoppt.v2.services.generate_semantic_deck_with_ai", return_value=semantic_payload
        ):
            with tempfile.TemporaryDirectory() as temp_dir:
                artifacts = make_v2_ppt(
                    topic="AI strategy",
                    output_dir=Path(temp_dir),
                    outline_output=Path(temp_dir) / "generated_outline.json",
                    semantic_output=Path(temp_dir) / "generated_semantic_deck.json",
                    deck_output=Path(temp_dir) / "generated_deck.json",
                    log_output=Path(temp_dir) / "log.txt",
                    ppt_output=Path(temp_dir) / "Enterprise-AI-PPT_Presentation.pptx",
                )

                self.assertTrue(artifacts.semantic_path.exists())
                self.assertTrue(artifacts.deck_path.exists())
                self.assertTrue(artifacts.rewrite_log_path.exists())
                self.assertTrue(artifacts.warnings_path.exists())
                payload = artifacts.deck.model_dump(mode="json")
                self.assertEqual(payload["slides"][0]["layout"], "two_columns")
                self.assertLessEqual(len(payload["slides"][0]["left"]["items"]), 6)
                self.assertLessEqual(len(payload["slides"][0]["right"]["items"]), 6)

    def test_generate_semantic_deck_with_ai_validates_before_returning(self):
        outline = OutlineDocument.model_validate(
            {
                "pages": [
                    {"page_no": 1, "title": "Context", "goal": "Set context."},
                    {"page_no": 2, "title": "Issues", "goal": "Explain issues."},
                ]
            }
        )
        semantic_payload = {
            "meta": {"title": "AI strategy", "theme": "business_red", "language": "zh-CN", "author": "AI", "version": "2.0"},
            "slides": [
                {
                    "slide_id": "s1",
                    "title": "结论",
                    "intent": "conclusion",
                    "blocks": [{"kind": "statement", "text": "先打通主链，再扩展到运营闭环。"}],
                }
            ],
        }

        fake_client = type(
            "FakeClient",
            (),
            {"create_structured_json": lambda self, **_: semantic_payload},
        )()

        with patch("tools.sie_autoppt.v2.services.load_openai_responses_config"), patch(
            "tools.sie_autoppt.v2.services.OpenAIResponsesClient", return_value=fake_client
        ):
            result = generate_semantic_deck_with_ai(
                DeckGenerationRequest(topic="AI strategy", outline=outline),
                model="test-model",
            )

        self.assertEqual(result["slides"][0]["intent"], "conclusion")
