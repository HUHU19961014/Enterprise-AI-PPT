import unittest

from tools.sie_autoppt.config import INPUT_DIR
from tools.sie_autoppt.pipeline import plan_deck_from_html
from tools.sie_autoppt.planning.deck_planner import (
    build_deck_spec_from_html,
    build_directory_lines,
    build_directory_window,
    clamp_requested_chapters,
)


class DeckPlannerTests(unittest.TestCase):
    def test_clamp_requested_chapters_respects_bounds(self):
        self.assertEqual(clamp_requested_chapters(None, 3), 3)
        self.assertEqual(clamp_requested_chapters(0, 3), 3)
        self.assertEqual(clamp_requested_chapters(2, 3), 2)
        self.assertEqual(clamp_requested_chapters(99, 3), 3)
        self.assertEqual(clamp_requested_chapters(3, 2), 2)

    def test_standard_html_builds_three_default_pages(self):
        html = (INPUT_DIR / "uat_plan_sample.html").read_text(encoding="utf-8")

        deck = build_deck_spec_from_html(html, chapters=3)

        self.assertEqual(len(deck.body_pages), 3)
        self.assertEqual([page.page_key for page in deck.body_pages], ["overview", "scope", "focus"])
        self.assertEqual(len(build_directory_lines(deck.body_pages)), 5)

    def test_slide_tag_html_uses_all_detected_pages_by_default(self):
        html = """
        <div class="title">Supply Chain Compliance</div>
        <slide data-pattern="general_business">
          <h2>Background</h2>
          <ul><li>Regulation pressure</li></ul>
        </slide>
        <slide data-pattern="process_flow">
          <h2>Roadmap</h2>
          <ul><li>Assess</li><li>Design</li><li>Launch</li></ul>
        </slide>
        <slide>
          <h2>Governance</h2>
          <p>Clarify ownership</p>
        </slide>
        <slide>
          <h2>Summary</h2>
          <p>Close the loop</p>
        </slide>
        """

        deck = build_deck_spec_from_html(html, chapters=None)

        self.assertEqual(len(deck.body_pages), 4)
        self.assertEqual([page.page_key for page in deck.body_pages], ["slide_1", "slide_2", "slide_3", "slide_4"])
        self.assertEqual([page.pattern_id for page in deck.body_pages[:2]], ["general_business", "process_flow"])
        self.assertEqual(deck.body_pages[1].payload["steps"][0]["title"], "Assess")

    def test_card_analysis_html_uses_reference_styles(self):
        html = (INPUT_DIR / "ai_pythonpptx_strategy.html").read_text(encoding="utf-8")

        deck = build_deck_spec_from_html(html, chapters=3)

        self.assertEqual(
            [page.reference_style_id for page in deck.body_pages],
            ["comparison_upgrade", "capability_ring", "five_phase_path"],
        )
        self.assertEqual(
            [page.pattern_id for page in deck.body_pages],
            ["comparison_upgrade", "capability_ring", "five_phase_path"],
        )

    def test_pipeline_returns_matching_pattern_ids_and_directory_lines(self):
        plan = plan_deck_from_html(INPUT_DIR / "architecture_program_sample.html", chapters=3)

        self.assertEqual(len(plan.pattern_ids), len(plan.deck.body_pages))
        self.assertEqual(plan.pattern_ids, [page.pattern_id for page in plan.deck.body_pages])
        self.assertEqual(len(plan.chapter_lines), 5)
        self.assertEqual(plan.chapter_lines[-1], "Q&A")

    def test_directory_window_moves_with_active_page_after_five_pages(self):
        html = """
        <slide><h2>Page 1</h2><p>A</p></slide>
        <slide><h2>Page 2</h2><p>B</p></slide>
        <slide><h2>Page 3</h2><p>C</p></slide>
        <slide><h2>Page 4</h2><p>D</p></slide>
        <slide><h2>Page 5</h2><p>E</p></slide>
        <slide><h2>Page 6</h2><p>F</p></slide>
        <slide><h2>Page 7</h2><p>G</p></slide>
        """

        deck = build_deck_spec_from_html(html, chapters=None)
        lines, active_index = build_directory_window(deck.body_pages, 6)

        self.assertEqual(lines, ["Page3", "Page4", "Page5", "Page6", "Page7"])
        self.assertEqual(active_index, 4)

    def test_pcb_sample_builds_structured_payloads_for_renderers(self):
        html = (INPUT_DIR / "pcb_erp_general_solution.html").read_text(encoding="utf-8")

        deck = build_deck_spec_from_html(html, chapters=3)

        self.assertEqual(
            [page.pattern_id for page in deck.body_pages],
            ["solution_architecture", "process_flow", "org_governance"],
        )
        self.assertEqual(len(deck.body_pages[0].payload.get("layers", [])), 4)
        self.assertEqual(len(deck.body_pages[1].payload.get("steps", [])), 4)
        self.assertEqual(deck.body_pages[2].payload.get("label_prefix"), "重点")
        self.assertTrue(deck.body_pages[2].payload.get("footer_text"))
