import unittest
from unittest.mock import AsyncMock, patch

from tools.sie_autoppt.v2.schema import OutlineDocument
from tools.sie_autoppt.v2.services import (
    DeckGenerationRequest,
    generate_semantic_decks_with_ai_batch,
)


class V2ServicesBatchTests(unittest.IsolatedAsyncioTestCase):
    async def test_generate_semantic_decks_with_ai_batch_uses_async_client_batch(self):
        outline = OutlineDocument.model_validate(
            {
                "pages": [
                    {"page_no": 1, "title": "Context", "goal": "Set context."},
                    {"page_no": 2, "title": "Decision", "goal": "Ask for decision."},
                ]
            }
        )
        requests = [
            DeckGenerationRequest(topic="Topic A", outline=outline),
            DeckGenerationRequest(topic="Topic B", outline=outline),
        ]
        payloads = [
            {
                "meta": {"title": "Topic A", "theme": "sie_consulting_fixed", "language": "zh-CN", "author": "AI", "version": "2.0"},
                "slides": [{"slide_id": "s1", "title": "A", "intent": "conclusion", "blocks": [{"kind": "statement", "text": "A"}]}],
            },
            {
                "meta": {"title": "Topic B", "theme": "sie_consulting_fixed", "language": "zh-CN", "author": "AI", "version": "2.0"},
                "slides": [{"slide_id": "s1", "title": "B", "intent": "conclusion", "blocks": [{"kind": "statement", "text": "B"}]}],
            },
        ]
        fake_client = type("FakeClient", (), {})()
        fake_client.acreate_structured_json_batch = AsyncMock(return_value=payloads)
        with patch(
            "tools.sie_autoppt.v2.services.ensure_generation_context",
            return_value=({}, {}),
        ), patch(
            "tools.sie_autoppt.v2.services._create_structured_client",
            return_value=fake_client,
        ), patch(
            "tools.sie_autoppt.v2.services.compile_semantic_deck_payload",
        ):
            results = await generate_semantic_decks_with_ai_batch(requests, model="test-model", concurrency=2)
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["meta"]["title"], "Topic A")
        self.assertEqual(results[1]["meta"]["title"], "Topic B")

