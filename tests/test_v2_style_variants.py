import unittest

from tools.sie_autoppt.v2.style_variants import SUPPORTED_STYLE_VARIANTS, select_style_variant


class V2StyleVariantTests(unittest.TestCase):
    def test_select_style_variant_prefers_explicit_user_choice(self):
        selected = select_style_variant(usage_context="report", user_preference="decorative")
        self.assertEqual(selected, "decorative")

    def test_select_style_variant_uses_context_mapping_when_no_preference(self):
        self.assertEqual(select_style_variant(usage_context="meeting"), "minimal")
        self.assertEqual(select_style_variant(usage_context="proposal"), "decorative")
        self.assertEqual(select_style_variant(usage_context="presentation"), "standard")

    def test_supported_style_variants_are_stable(self):
        self.assertEqual(SUPPORTED_STYLE_VARIANTS, ("minimal", "standard", "decorative"))


if __name__ == "__main__":
    unittest.main()
