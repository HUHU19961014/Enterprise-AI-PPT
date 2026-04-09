import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

from tools.sie_autoppt import cli
from tools.sie_autoppt.llm_openai import OpenAIConfigurationError, OpenAIResponsesConfig
from tools.sie_autoppt.models import BodyPageSpec, DeckSpec


class CliTests(unittest.TestCase):
    def test_help_emphasizes_primary_commands_without_listing_legacy_choices(self):
        stdout = io.StringIO()
        with (
            patch("sys.argv", ["sie-autoppt", "--help"]),
            redirect_stdout(stdout),
        ):
            with self.assertRaises(SystemExit) as ctx:
                cli.main()

        self.assertEqual(ctx.exception.code, 0)
        help_text = stdout.getvalue()
        self.assertIn("Primary commands: make, review, iterate", help_text)
        self.assertIn("Legacy V1/template commands remain available for compatibility but are hidden from help.", help_text)
        self.assertNotIn("{make,plan,render", help_text)

    def test_unknown_command_returns_curated_error_message(self):
        stderr = io.StringIO()
        with (
            patch("sys.argv", ["sie-autoppt", "unknown-cmd"]),
            redirect_stderr(stderr),
        ):
            with self.assertRaises(SystemExit) as ctx:
                cli.main()

        self.assertEqual(ctx.exception.code, 2)
        self.assertIn("unknown command 'unknown-cmd'", stderr.getvalue())
        self.assertIn("primary commands (make, review, iterate)", stderr.getvalue())

    def test_ai_check_prints_summary(self):
        deck = DeckSpec(
            cover_title="AI AutoPPT Healthcheck",
            body_pages=[
                BodyPageSpec(
                    page_key="p1",
                    title="Test Page",
                    subtitle="",
                    bullets=["Point A", "Point B"],
                    pattern_id="general_business",
                )
            ],
        )
        stdout = io.StringIO()
        with (
            patch("sys.argv", ["sie-autoppt", "ai-check", "--topic", "Healthcheck"]),
            patch(
                "tools.sie_autoppt.services.load_openai_responses_config",
                return_value=OpenAIResponsesConfig(
                    api_key="test-key",
                    base_url="https://api.openai.com/v1",
                    model="gpt-4o-mini",
                    timeout_sec=30,
                    reasoning_effort="low",
                    text_verbosity="low",
                    api_style="responses",
                ),
            ),
            patch("tools.sie_autoppt.services.plan_deck_spec_with_ai", return_value=deck),
            redirect_stdout(stdout),
        ):
            cli.main()

        payload = json.loads(stdout.getvalue().strip())
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["model"], "gpt-4o-mini")
        self.assertEqual(payload["api_style"], "responses")
        self.assertEqual(payload["page_count"], 1)
        self.assertEqual(payload["first_page_title"], "Test Page")

    def test_ai_plan_rejects_mixing_exact_and_range(self):
        stderr = io.StringIO()
        with (
            patch("sys.argv", ["sie-autoppt", "ai-plan", "--topic", "Test", "--chapters", "4", "--min-slides", "3"]),
            redirect_stderr(stderr),
        ):
            with self.assertRaises(SystemExit) as ctx:
                cli.main()

        self.assertEqual(ctx.exception.code, 2)
        self.assertIn("--chapters cannot be combined", stderr.getvalue())

    def test_ai_check_reports_missing_api_key(self):
        stderr = io.StringIO()
        with (
            patch("sys.argv", ["sie-autoppt", "ai-check"]),
            patch(
                "tools.sie_autoppt.services.load_openai_responses_config",
                side_effect=OpenAIConfigurationError("OPENAI_API_KEY is required for AI planning."),
            ),
            redirect_stderr(stderr),
        ):
            with self.assertRaises(SystemExit) as ctx:
                cli.main()

        self.assertEqual(ctx.exception.code, 1)
        self.assertIn("AI healthcheck blocked", stderr.getvalue())

    def test_clarify_outputs_session_json_and_persists_state_file(self):
        stdout = io.StringIO()
        with tempfile.TemporaryDirectory() as temp_dir:
            state_path = f"{temp_dir}\\clarifier_state.json"
            with (
                patch("sys.argv", ["sie-autoppt", "clarify", "--topic", "帮我做PPT", "--clarifier-state-file", state_path]),
                redirect_stdout(stdout),
            ):
                cli.main()

            payload = json.loads(stdout.getvalue().strip())
            self.assertEqual(payload["status"], "needs_clarification")
            self.assertTrue(payload["session"]["pending_dimensions"])

    def test_clarify_web_starts_local_server_with_host_and_port(self):
        with (
            patch("sys.argv", ["sie-autoppt", "clarify-web", "--host", "127.0.0.1", "--port", "9001"]),
            patch("tools.sie_autoppt.cli.serve_clarifier_web") as mocked_serve,
        ):
            cli.main()

        mocked_serve.assert_called_once_with(host="127.0.0.1", port=9001)

    def test_structure_command_prints_generated_structure_path(self):
        stdout = io.StringIO()
        with tempfile.TemporaryDirectory() as temp_dir:
            structure_path = f"{temp_dir}\\sample.structure.json"
            with (
                patch("sys.argv", ["sie-autoppt", "structure", "--topic", "做一个AI行业趋势汇报", "--output-dir", temp_dir]),
                patch("tools.sie_autoppt.cli.generate_structure_only", return_value=Path(structure_path)),
                redirect_stdout(stdout),
            ):
                cli.main()

        self.assertIn("sample.structure.json", stdout.getvalue())

    def test_topic_without_explicit_command_requires_clarification_before_v2_make(self):
        stderr = io.StringIO()
        with tempfile.TemporaryDirectory() as temp_dir:
            with (
                patch("sys.argv", ["sie-autoppt", "--topic", "做一份装备制造数字化方案", "--output-dir", temp_dir]),
                redirect_stderr(stderr),
            ):
                with self.assertRaises(SystemExit) as ctx:
                    cli.main()

        self.assertEqual(ctx.exception.code, 1)
        self.assertIn("Clarification required before 'v2-make'", stderr.getvalue())
        self.assertIn("semantic v2-make", stderr.getvalue())

    def test_v2_route_rejects_explicit_template_argument(self):
        stderr = io.StringIO()
        with (
            patch("sys.argv", ["sie-autoppt", "--topic", "测试主题", "--template", "custom.pptx"]),
            redirect_stderr(stderr),
        ):
            with self.assertRaises(SystemExit) as ctx:
                cli.main()

        self.assertEqual(ctx.exception.code, 2)
        self.assertIn("--template is not supported by V2 workflows", stderr.getvalue())

    def test_explicit_make_with_topic_routes_to_v2_make(self):
        stdout = io.StringIO()
        stderr = io.StringIO()
        with tempfile.TemporaryDirectory() as temp_dir:
            with (
                patch("sys.argv", ["sie-autoppt", "make", "--topic", "测试主题", "--output-dir", temp_dir]),
                patch("tools.sie_autoppt.cli.resolve_v2_clarified_context", return_value=("测试主题", "", "公司领导", None, 6, 8, "business_red")),
                patch(
                    "tools.sie_autoppt.cli.make_v2_ppt",
                    return_value=type(
                        "FakeArtifacts",
                        (),
                        {
                            "outline_path": Path(temp_dir) / "deck.outline.json",
                            "semantic_path": Path(temp_dir) / "deck.semantic.v2.json",
                            "deck_path": Path(temp_dir) / "deck.deck.v2.json",
                            "rewrite_log_path": Path(temp_dir) / "rewrite_log.json",
                            "warnings_path": Path(temp_dir) / "warnings.json",
                            "log_path": Path(temp_dir) / "deck.log.txt",
                            "pptx_path": Path(temp_dir) / "deck.pptx",
                        },
                    )(),
                ),
                redirect_stdout(stdout),
                redirect_stderr(stderr),
            ):
                cli.main()

        self.assertIn("now routes to semantic v2-make", stderr.getvalue())
        self.assertIn("deck.pptx", stdout.getvalue())

    def test_ai_make_prints_legacy_warning(self):
        stdout = io.StringIO()
        stderr = io.StringIO()
        with tempfile.TemporaryDirectory() as temp_dir:
            with (
                patch("sys.argv", ["sie-autoppt", "ai-make", "--topic", "做一份装备制造数字化方案", "--output-dir", temp_dir]),
                patch(
                    "tools.sie_autoppt.cli.render_from_ai_plan",
                    return_value=type(
                        "FakeRenderResult",
                        (),
                        {
                            "report_path": Path(temp_dir) / "legacy.report.json",
                            "output_path": Path(temp_dir) / "legacy.pptx",
                            "render_trace": None,
                        },
                    )(),
                ),
                redirect_stdout(stdout),
                redirect_stderr(stderr),
            ):
                cli.main()

        self.assertIn("legacy workflow", stderr.getvalue())
        self.assertIn("v2-make", stderr.getvalue())
