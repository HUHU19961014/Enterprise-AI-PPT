import concurrent.futures
import unittest

from tools.sie_autoppt.v2.semantic_compiler import compile_semantic_deck_payload


def _semantic_payload() -> dict:
    return {
        "meta": {
            "title": "Concurrent Deck",
            "theme": "business_red",
            "language": "zh-CN",
            "author": "AI",
            "version": "2.0",
        },
        "slides": [
            {
                "slide_id": "s1",
                "title": "Delivery Rhythm",
                "intent": "analysis",
                "blocks": [
                    {
                        "kind": "timeline",
                        "heading": "Phase Goals",
                        "stages": [
                            {"title": "Q1", "detail": "Finalize plan alignment"},
                            {"title": "Q2", "detail": "Complete pilot launch"},
                            {"title": "Q3", "detail": "Scale operations"},
                        ],
                    }
                ],
            }
        ],
    }


class V2ConcurrencyTests(unittest.TestCase):
    def test_compile_semantic_deck_payload_is_stable_under_thread_pool_load(self):
        payload = _semantic_payload()

        def _compile_once() -> tuple[str, str, int]:
            validated = compile_semantic_deck_payload(payload).deck
            return validated.slides[0].layout, validated.meta.language, len(validated.slides)

        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
            futures = [executor.submit(_compile_once) for _ in range(40)]
            results = [future.result(timeout=10) for future in futures]

        self.assertTrue(all(layout == "timeline" for layout, _, _ in results))
        self.assertTrue(all(language == "zh-CN" for _, language, _ in results))
        self.assertTrue(all(slide_count == 1 for _, _, slide_count in results))


if __name__ == "__main__":
    unittest.main()
