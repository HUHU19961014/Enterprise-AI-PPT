import unittest

from tools.sie_autoppt.deck_spec_io import body_page_spec_from_dict, body_page_spec_to_dict
from tools.sie_autoppt.models import BodyPageSpec


class DeckSpecIoPayloadValidationTests(unittest.TestCase):
    def test_body_page_spec_from_dict_validates_known_pattern_payload(self):
        page = body_page_spec_from_dict(
            {
                "page_key": "p1",
                "title": "Ops",
                "subtitle": "Metrics",
                "bullets": ["a", "b"],
                "pattern_id": "kpi_dashboard",
                "payload": {
                    "headline": "Operations",
                    "metrics": [{"label": "OTD", "value": "95%"}],
                    "insights": ["Stable"],
                },
            }
        )
        self.assertEqual(page.payload["headline"], "Operations")
        self.assertEqual(page.payload["metrics"][0]["label"], "OTD")

    def test_body_page_spec_to_dict_handles_dict_payload(self):
        page = BodyPageSpec(
            page_key="p1",
            title="Ops",
            subtitle="Metrics",
            bullets=["a", "b"],
            pattern_id="kpi_dashboard",
            payload={"headline": "Operations"},
        )
        payload = body_page_spec_to_dict(page)
        self.assertEqual(payload["payload"], {"headline": "Operations"})

