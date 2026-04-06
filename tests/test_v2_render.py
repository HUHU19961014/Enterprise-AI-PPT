import json
import tempfile
import unittest
from pathlib import Path

from pptx import Presentation

from tools.sie_autoppt.v2.ppt_engine import generate_ppt
from tools.sie_autoppt.v2.schema import validate_deck_payload


class V2RenderTests(unittest.TestCase):
    def test_generate_ppt_renders_sample_deck(self):
        sample_path = Path("samples/sample_deck_v2.json")
        payload = json.loads(sample_path.read_text(encoding="utf-8"))
        validated = validate_deck_payload(payload)

        with tempfile.TemporaryDirectory() as temp_dir:
            ppt_path = Path(temp_dir) / "sample_v2.pptx"
            log_path = Path(temp_dir) / "sample_v2.log.txt"
            result = generate_ppt(validated, output_path=ppt_path, log_path=log_path)

            self.assertTrue(result.output_path.exists())
            self.assertTrue(log_path.exists())
            self.assertIsNotNone(result.warnings_path)
            self.assertTrue(result.warnings_path.exists())
            self.assertIsNotNone(result.rewrite_log_path)
            self.assertTrue(result.rewrite_log_path.exists())

            prs = Presentation(str(result.output_path))
            self.assertEqual(len(prs.slides), len(validated.deck.slides))
            all_text = "\n".join(shape.text for slide in prs.slides for shape in slide.shapes if hasattr(shape, "text"))
            self.assertIn("项目背景", all_text)
            self.assertIn("重构前后对比", all_text)

            warnings_payload = json.loads(result.warnings_path.read_text(encoding="utf-8"))
            self.assertIn("passed", warnings_payload)
            self.assertIn("review_required", warnings_payload)
            self.assertIn("warnings", warnings_payload)
            self.assertIn("high", warnings_payload)
            self.assertIn("errors", warnings_payload)
            self.assertIn("summary", warnings_payload)

            rewrite_payload = json.loads(result.rewrite_log_path.read_text(encoding="utf-8"))
            self.assertIn("attempted", rewrite_payload)
            self.assertIn("applied", rewrite_payload)
            self.assertIn("actions", rewrite_payload)

    def test_generate_ppt_applies_single_rewrite_pass(self):
        payload = {
            "meta": {"title": "Test", "theme": "business_red", "language": "zh-CN", "author": "AI", "version": "2.0"},
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

        with tempfile.TemporaryDirectory() as temp_dir:
            ppt_path = Path(temp_dir) / "rewritten.pptx"
            log_path = Path(temp_dir) / "rewritten.log.txt"
            deck_path = Path(temp_dir) / "generated_deck.json"
            result = generate_ppt(payload, output_path=ppt_path, log_path=log_path, deck_output_path=deck_path)

            self.assertTrue(result.rewrite_applied)
            self.assertTrue(deck_path.exists())
            self.assertTrue(result.output_path.exists())

            rewritten_deck = json.loads(deck_path.read_text(encoding="utf-8"))
            slide = rewritten_deck["slides"][0]
            self.assertLessEqual(len(slide["content"]), 6)

            rewrite_payload = json.loads(result.rewrite_log_path.read_text(encoding="utf-8"))
            self.assertTrue(rewrite_payload["attempted"])
            self.assertTrue(rewrite_payload["applied"])
            self.assertGreater(rewrite_payload["action_count"], 0)
