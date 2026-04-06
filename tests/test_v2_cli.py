import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from tools.sie_autoppt import cli
from tools.sie_autoppt.v2.schema import OutlineDocument, validate_deck_payload


class V2CliTests(unittest.TestCase):
    def test_v2_plan_prints_outline_and_deck_paths(self):
        outline = OutlineDocument.model_validate(
            {
                "pages": [
                    {"page_no": 1, "title": "Context", "goal": "Set context."},
                    {"page_no": 2, "title": "Issues", "goal": "Explain issues."},
                    {"page_no": 3, "title": "Plan", "goal": "Present plan."},
                    {"page_no": 4, "title": "Impact", "goal": "Quantify impact."},
                    {"page_no": 5, "title": "Roadmap", "goal": "Show roadmap."},
                    {"page_no": 6, "title": "Conclusion", "goal": "Close the deck."},
                ]
            }
        )
        validated = validate_deck_payload(
            {
                "meta": {"title": "Test Deck", "theme": "business_red", "language": "zh-CN", "author": "AI", "version": "2.0"},
                "slides": [{"layout": "title_only", "title": "Conclusion"}],
            }
        )

        stdout = io.StringIO()
        with tempfile.TemporaryDirectory() as temp_dir:
            with (
                patch("sys.argv", ["sie-autoppt", "v2-plan", "--topic", "AI plan", "--output-dir", temp_dir]),
                patch("tools.sie_autoppt.cli.generate_outline_with_ai", return_value=outline),
                patch("tools.sie_autoppt.cli.generate_deck_with_ai", return_value=validated),
                redirect_stdout(stdout),
            ):
                cli.main()

            output = stdout.getvalue()
            self.assertIn("generated_outline.json", output)
            self.assertIn("generated_deck.json", output)

    def test_v2_make_prints_five_artifact_paths(self):
        stdout = io.StringIO()
        with tempfile.TemporaryDirectory() as temp_dir:
            with (
                patch("sys.argv", ["sie-autoppt", "v2-make", "--topic", "AI make", "--output-dir", temp_dir]),
                patch(
                    "tools.sie_autoppt.cli.make_v2_ppt",
                    return_value=type(
                        "FakeArtifacts",
                        (),
                        {
                            "outline_path": Path(temp_dir) / "deck.outline.json",
                            "deck_path": Path(temp_dir) / "deck.deck.v2.json",
                            "warnings_path": Path(temp_dir) / "warnings.json",
                            "log_path": Path(temp_dir) / "deck.log.txt",
                            "pptx_path": Path(temp_dir) / "deck.pptx",
                        },
                    )(),
                ),
                redirect_stdout(stdout),
            ):
                cli.main()

            lines = [line.strip() for line in stdout.getvalue().splitlines() if line.strip()]
            self.assertEqual(len(lines), 5)
            self.assertTrue(lines[0].endswith(".outline.json"))
            self.assertTrue(lines[1].endswith(".deck.v2.json"))
            self.assertTrue(lines[2].endswith("warnings.json"))
            self.assertTrue(lines[3].endswith(".log.txt"))
            self.assertTrue(lines[4].endswith(".pptx"))

    def test_full_pipeline_uses_standardized_v2_output_names(self):
        stdout = io.StringIO()
        with tempfile.TemporaryDirectory() as temp_dir:
            with (
                patch("sys.argv", ["sie-autoppt", "--full-pipeline", "--topic", "AI make", "--output-dir", temp_dir]),
                patch(
                    "tools.sie_autoppt.cli.make_v2_ppt",
                    return_value=type(
                        "FakeArtifacts",
                        (),
                        {
                            "outline_path": Path(temp_dir) / "generated_outline.json",
                            "deck_path": Path(temp_dir) / "generated_deck.json",
                            "warnings_path": Path(temp_dir) / "warnings.json",
                            "log_path": Path(temp_dir) / "log.txt",
                            "pptx_path": Path(temp_dir) / "generated.pptx",
                        },
                    )(),
                ) as make_mock,
                redirect_stdout(stdout),
            ):
                cli.main()

            called = make_mock.call_args.kwargs
            self.assertEqual(called["outline_output"], Path(temp_dir) / "generated_outline.json")
            self.assertEqual(called["deck_output"], Path(temp_dir) / "generated_deck.json")
            self.assertEqual(called["log_output"], Path(temp_dir) / "log.txt")
            self.assertEqual(called["ppt_output"], Path(temp_dir) / "generated.pptx")

            lines = [line.strip() for line in stdout.getvalue().splitlines() if line.strip()]
            self.assertEqual(lines[0], str(Path(temp_dir) / "generated_outline.json"))
            self.assertEqual(lines[1], str(Path(temp_dir) / "generated_deck.json"))
            self.assertEqual(lines[2], str(Path(temp_dir) / "warnings.json"))
            self.assertEqual(lines[3], str(Path(temp_dir) / "log.txt"))
            self.assertEqual(lines[4], str(Path(temp_dir) / "generated.pptx"))
