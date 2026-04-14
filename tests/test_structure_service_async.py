import unittest
from unittest.mock import AsyncMock, patch

from tools.sie_autoppt.structure_service import (
    StructureGenerationRequest,
    generate_structures_with_ai_batch,
)


class StructureServiceAsyncBatchTests(unittest.IsolatedAsyncioTestCase):
    async def test_generate_structures_with_ai_batch_returns_results_in_order(self):
        requests = [
            StructureGenerationRequest(topic="A", sections=3),
            StructureGenerationRequest(topic="B", sections=3),
        ]
        payloads = [
            {
                "core_message": "A core message",
                "structure_type": "general",
                "sections": [
                    {
                        "title": "Section A1",
                        "key_message": "Message A1",
                        "arguments": [{"point": "P1", "evidence": ""}, {"point": "P2", "evidence": ""}],
                    },
                    {
                        "title": "Section A2",
                        "key_message": "Message A2",
                        "arguments": [{"point": "P3", "evidence": ""}, {"point": "P4", "evidence": ""}],
                    },
                    {
                        "title": "Section A3",
                        "key_message": "Message A3",
                        "arguments": [{"point": "P5", "evidence": ""}, {"point": "P6", "evidence": ""}],
                    },
                ],
            },
            {
                "core_message": "B core message",
                "structure_type": "general",
                "sections": [
                    {
                        "title": "Section B1",
                        "key_message": "Message B1",
                        "arguments": [{"point": "P1", "evidence": ""}, {"point": "P2", "evidence": ""}],
                    },
                    {
                        "title": "Section B2",
                        "key_message": "Message B2",
                        "arguments": [{"point": "P3", "evidence": ""}, {"point": "P4", "evidence": ""}],
                    },
                    {
                        "title": "Section B3",
                        "key_message": "Message B3",
                        "arguments": [{"point": "P5", "evidence": ""}, {"point": "P6", "evidence": ""}],
                    },
                ],
            },
        ]
        fake_client = type("FakeClient", (), {})()
        fake_client.acreate_structured_json = AsyncMock(side_effect=payloads)
        with patch("tools.sie_autoppt.structure_service.load_openai_responses_config", return_value=object()), patch(
            "tools.sie_autoppt.structure_service.OpenAIResponsesClient",
            return_value=fake_client,
        ):
            results = await generate_structures_with_ai_batch(requests, model="test-model", concurrency=2)
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].structure.core_message, "A core message")
        self.assertEqual(results[1].structure.core_message, "B core message")

