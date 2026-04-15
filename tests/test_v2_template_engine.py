import unittest

from tools.sie_autoppt.v2.template_engine.template_index import build_default_template_index
from tools.sie_autoppt.v2.template_engine.template_matcher import TemplateMatcher


class V2TemplateEngineTests(unittest.TestCase):
    def test_default_template_index_loads_builtin_chart_library(self):
        index = build_default_template_index()
        timeline_templates = index.filter_by_type("timeline")
        comparison_templates = index.filter_by_type("comparison")

        self.assertGreaterEqual(len(index.templates), 40)
        self.assertGreaterEqual(len(timeline_templates), 1)
        self.assertGreaterEqual(len(comparison_templates), 1)

    def test_template_matcher_returns_non_fallback_for_known_content_type(self):
        matcher = TemplateMatcher()
        match = matcher.match(content_type="timeline", style_variant="standard")

        self.assertFalse(match.fallback)
        self.assertEqual(match.content_type, "timeline")
        self.assertGreaterEqual(match.confidence, 0.6)

    def test_template_matcher_falls_back_for_unknown_content_type(self):
        matcher = TemplateMatcher()
        match = matcher.match(content_type="unknown_type", style_variant="decorative")

        self.assertTrue(match.fallback)
        self.assertEqual(match.template_id, "")
        self.assertLess(match.confidence, 0.6)

    def test_default_template_index_also_includes_layout_library(self):
        index = build_default_template_index()
        has_layout_template = any("/templates/layouts/" in item.template_path.replace("\\", "/") for item in index.templates)
        self.assertTrue(has_layout_template)


if __name__ == "__main__":
    unittest.main()
