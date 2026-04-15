import unittest
from unittest.mock import patch

from tools.sie_autoppt.v2.llm_layout_planner import (
    LLMLayoutDecision,
    decide_layout_with_llm_or_none,
    parse_layout_decision_payload,
)


class _FakeClient:
    def __init__(self, payload):
        self._payload = payload

    def create_structured_json(self, **kwargs):
        return self._payload


class _BrokenClient:
    def create_structured_json(self, **kwargs):
        raise RuntimeError("simulated error")


class V2LLMLayoutPlannerTests(unittest.TestCase):
    def test_parse_layout_decision_payload_returns_decision(self):
        payload = {"recommended_layout": "timeline", "confidence": 0.82, "reason": "timeline-structure"}
        decision = parse_layout_decision_payload(payload)

        self.assertEqual(decision, LLMLayoutDecision(layout="timeline", confidence=0.82, reason="timeline-structure"))

    def test_decide_layout_with_llm_or_none_returns_none_when_disabled(self):
        with patch.dict("os.environ", {"SIE_AUTOPPT_ENABLE_LLM_LAYOUT_DECISIONS": "0"}, clear=False):
            result = decide_layout_with_llm_or_none(
                slide_title="Roadmap",
                intent="analysis",
                content_items=("Q1", "Q2"),
                available_layouts=("title_content", "two_columns", "timeline"),
                client=_FakeClient({"recommended_layout": "timeline", "confidence": 0.9, "reason": "ok"}),
            )
        self.assertIsNone(result)

    def test_decide_layout_with_llm_or_none_falls_back_to_none_on_error(self):
        with patch.dict("os.environ", {"SIE_AUTOPPT_ENABLE_LLM_LAYOUT_DECISIONS": "1"}, clear=False):
            result = decide_layout_with_llm_or_none(
                slide_title="Roadmap",
                intent="analysis",
                content_items=("Q1", "Q2"),
                available_layouts=("title_content", "two_columns", "timeline"),
                client=_BrokenClient(),
            )
        self.assertIsNone(result)

    def test_decide_layout_with_llm_or_none_returns_decision_when_enabled(self):
        with patch.dict("os.environ", {"SIE_AUTOPPT_ENABLE_LLM_LAYOUT_DECISIONS": "1"}, clear=False):
            result = decide_layout_with_llm_or_none(
                slide_title="Roadmap",
                intent="analysis",
                content_items=("Q1", "Q2"),
                available_layouts=("title_content", "two_columns", "timeline"),
                client=_FakeClient({"recommended_layout": "timeline", "confidence": 0.86, "reason": "best-fit"}),
            )
        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result.layout, "timeline")
        self.assertGreaterEqual(result.confidence, 0.8)


if __name__ == "__main__":
    unittest.main()
