import unittest

from tools.sie_autoppt.models import (
    ClaimBreakdownPageModel,
    ComparisonUpgradePageModel,
    KpiDashboardPageModel,
    GovernancePageModel,
    ProcessFlowPageModel,
    RiskMatrixPageModel,
    SolutionArchitecturePageModel,
    validate_body_page_payload,
)


class PayloadModelMigrationTests(unittest.TestCase):
    def test_process_flow_page_model_validates_and_trims_text(self):
        model = ProcessFlowPageModel.model_validate(
            {
                "steps": [
                    {"number": " 1 ", "title": " Discover ", "detail": " Align scope "},
                    {"number": "2", "title": "Build", "detail": "Implement workflows"},
                ]
            }
        )
        self.assertEqual(model.steps[0].number, "1")
        self.assertEqual(model.steps[0].title, "Discover")

    def test_solution_architecture_page_model_accepts_optional_banner(self):
        model = SolutionArchitecturePageModel.model_validate(
            {
                "layers": [
                    {"label": "L1", "title": "Data", "detail": "Ingestion and quality"},
                    {"label": "L2", "title": "App", "detail": "Service and API"},
                ],
                "banner_text": "North-star architecture",
            }
        )
        self.assertEqual(len(model.layers), 2)
        self.assertEqual(model.banner_text, "North-star architecture")

    def test_governance_page_model_rejects_empty_card_detail(self):
        with self.assertRaises(ValueError):
            GovernancePageModel.model_validate(
                {
                    "cards": [
                        {"label": "Policy", "detail": ""},
                    ]
                }
            )

    def test_comparison_upgrade_page_model_supports_partial_payload(self):
        model = ComparisonUpgradePageModel.model_validate(
            {
                "headline": "Before vs After",
                "left_cards": [{"title": "Current", "detail": "Manual checks"}],
                "right_cards": [{"title": "Target", "detail": "Closed-loop governance"}],
            }
        )
        self.assertEqual(model.headline, "Before vs After")
        self.assertEqual(model.left_cards[0].title, "Current")

    def test_validate_body_page_payload_uses_pattern_specific_model(self):
        result = validate_body_page_payload(
            "kpi_dashboard",
            {
                "headline": "Operations",
                "metrics": [{"label": "OTD", "value": "95%"}],
                "insights": ["Stable"],
            },
        )
        self.assertIsInstance(result, KpiDashboardPageModel)
        self.assertEqual(result.metrics[0].label, "OTD")

    def test_validate_body_page_payload_returns_raw_dict_for_unknown_pattern(self):
        result = validate_body_page_payload("unknown_pattern", {"any": "value"})
        self.assertEqual(result, {"any": "value"})

    def test_claim_and_risk_models_accept_optional_fields(self):
        claim = ClaimBreakdownPageModel.model_validate(
            {
                "headline": "Claims",
                "claims": [{"label": "Late fee", "value": "1.2M"}],
            }
        )
        risk = RiskMatrixPageModel.model_validate(
            {
                "headline": "Risk",
                "items": [{"title": "Supply risk", "quadrant": "high_high"}],
            }
        )
        self.assertEqual(claim.claims[0].label, "Late fee")
        self.assertEqual(risk.items[0].quadrant, "high_high")


if __name__ == "__main__":
    unittest.main()
