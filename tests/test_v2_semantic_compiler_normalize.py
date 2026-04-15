import unittest

from tools.sie_autoppt.v2.semantic_compiler import normalize_list


class SemanticCompilerNormalizeListTests(unittest.TestCase):
    def test_normalize_list_filters_invalid_items_and_keeps_required_optional_fields(self):
        value = [
            {"title": "  A  ", "body": "  B  "},
            {"title": "C", "body": ""},
            {"title": "   ", "body": "ignored"},
            {"body": "missing required"},
            "not-a-dict",
        ]

        normalized = normalize_list(value, required_keys=["title"], optional_keys=["body"])

        self.assertEqual(normalized, [{"title": "A", "body": "B"}, {"title": "C"}])

    def test_normalize_list_requires_all_required_keys(self):
        value = [
            {"label": "Throughput", "value": "95%", "note": "weekly"},
            {"label": "Yield", "value": ""},
            {"label": "", "value": "98%"},
        ]

        normalized = normalize_list(value, required_keys=["label", "value"], optional_keys=["note"])

        self.assertEqual(normalized, [{"label": "Throughput", "value": "95%", "note": "weekly"}])

    def test_normalize_list_handles_non_list_and_empty_values(self):
        self.assertEqual(normalize_list(None, required_keys=["title"]), [])
        self.assertEqual(normalize_list("not-list", required_keys=["title"]), [])
        self.assertEqual(normalize_list([], required_keys=["title"]), [])

    def test_normalize_list_supports_optional_keys_none(self):
        value = [{"title": " Item A "}, {"title": "  "}]
        normalized = normalize_list(value, required_keys=["title"], optional_keys=None)
        self.assertEqual(normalized, [{"title": "Item A"}])

    def test_normalize_list_coerces_non_string_required_values(self):
        value = [{"title": 42, "body": 3.14}, {"title": 0, "body": None}]
        normalized = normalize_list(value, required_keys=["title"], optional_keys=["body"])
        self.assertEqual(normalized, [{"title": "42", "body": "3.14"}, {"title": "0"}])


if __name__ == "__main__":
    unittest.main()
