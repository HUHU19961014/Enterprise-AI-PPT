import unittest

from tools.sie_autoppt.v2.schema import OutlineDocument, ThemeMeta

try:
    from hypothesis import given
    from hypothesis import strategies as st
except ImportError:  # pragma: no cover - optional dev dependency in some environments
    given = None
    st = None


if given is not None and st is not None:

    class V2SchemaHypothesisTests(unittest.TestCase):
        @given(
            title=st.text(min_size=1, max_size=80).filter(lambda s: bool(s.strip())),
            author=st.text(min_size=1, max_size=40).filter(lambda s: bool(s.strip())),
        )
        def test_theme_meta_trims_and_preserves_bounds(self, title: str, author: str):
            meta = ThemeMeta.model_validate(
                {
                    "title": f"  {title}  ",
                    "theme": "sie_consulting_fixed",
                    "language": "zh-CN",
                    "author": f" {author} ",
                    "version": "2.0",
                }
            )
            self.assertTrue(1 <= len(meta.title) <= 80)
            self.assertEqual(meta.title, meta.title.strip())
            self.assertTrue(1 <= len(meta.author) <= 40)
            self.assertEqual(meta.author, meta.author.strip())

        @given(
            goals=st.lists(
                st.text(min_size=4, max_size=40).filter(lambda s: bool(s.strip())),
                min_size=1,
                max_size=6,
            ),
        )
        def test_outline_document_accepts_contiguous_page_numbers(self, goals: list[str]):
            pages = [
                {
                    "page_no": index,
                    "title": f"Page {index}",
                    "goal": goal,
                }
                for index, goal in enumerate(goals, start=1)
            ]
            outline = OutlineDocument.model_validate({"pages": pages})
            self.assertEqual(len(outline.pages), len(goals))
            self.assertEqual([item.page_no for item in outline.pages], list(range(1, len(goals) + 1)))

else:

    class V2SchemaHypothesisTests(unittest.TestCase):
        @unittest.skip("hypothesis is not installed")
        def test_hypothesis_dependency_not_installed(self):
            self.fail("hypothesis is not installed")


if __name__ == "__main__":
    unittest.main()
