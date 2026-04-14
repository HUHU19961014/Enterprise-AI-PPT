import unittest

from tools.sie_autoppt.v2.utils import normalize_data_sources, normalize_object_list, normalize_string_list, strip_text


class V2UtilsTests(unittest.TestCase):
    def test_strip_text_is_none_safe(self):
        self.assertEqual(strip_text(None), "")
        self.assertEqual(strip_text("  hello  "), "hello")
        self.assertEqual(strip_text(123), "123")

    def test_normalize_string_list_filters_empty_items(self):
        value = ["  a ", "", None, " b  ", "   "]
        self.assertEqual(normalize_string_list(value), ["a", "b"])

    def test_normalize_data_sources_filters_invalid_entries(self):
        value = [
            {"claim": " c1 ", "source": " s1 ", "confidence": "HIGH"},
            {"claim": "c2", "source": "s2", "confidence": "unknown"},
            {"claim": "", "source": "s3"},
            {"claim": "c4", "source": ""},
            "not-dict",
        ]
        self.assertEqual(
            normalize_data_sources(value),
            [
                {"claim": "c1", "source": "s1", "confidence": "high"},
                {"claim": "c2", "source": "s2", "confidence": "medium"},
            ],
        )

    def test_normalize_object_list_filters_by_required_keys(self):
        value = [
            {"title": "  A  ", "body": "  B  "},
            {"title": "C", "body": ""},
            {"title": "   ", "body": "ignored"},
            {"body": "missing required"},
            "not-a-dict",
        ]
        self.assertEqual(
            normalize_object_list(value, required_keys=["title"], optional_keys=["body"]),
            [{"title": "A", "body": "B"}, {"title": "C"}],
        )


if __name__ == "__main__":
    unittest.main()
