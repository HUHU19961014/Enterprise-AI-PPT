import unittest

from tools.sie_autoppt.v2.deck_director import compile_semantic_deck_payload, plan_semantic_slide_layout


class V2DeckDirectorTests(unittest.TestCase):
    def test_plan_semantic_slide_layout_prefers_title_content_for_simple_narrative(self):
        plan = plan_semantic_slide_layout(
            {
                "slide_id": "s1",
                "title": "项目背景",
                "intent": "narrative",
                "blocks": [{"kind": "bullets", "items": ["说明业务背景", "界定本次范围", "确认关键约束"]}],
            }
        )

        self.assertEqual(plan.layout, "title_content")
        self.assertEqual(plan.reason, "default-content")

    def test_compile_comparison_slide_to_two_columns(self):
        validated = compile_semantic_deck_payload(
            {
                "meta": {"title": "Test", "theme": "business_red", "language": "zh-CN", "author": "AI", "version": "2.0"},
                "slides": [
                    {
                        "slide_id": "s1",
                        "title": "当前与目标",
                        "intent": "comparison",
                        "blocks": [
                            {
                                "kind": "comparison",
                                "left_heading": "当前",
                                "left_items": ["流程分散", "响应慢"],
                                "right_heading": "目标",
                                "right_items": ["流程打通", "响应快"],
                            }
                        ],
                    }
                ],
            }
        )

        slide = validated.deck.slides[0]
        self.assertEqual(slide.layout, "two_columns")
        self.assertEqual(slide.left.heading, "当前")
        self.assertEqual(slide.right.heading, "目标")

    def test_compile_framework_with_image_block_to_title_image(self):
        validated = compile_semantic_deck_payload(
            {
                "meta": {"title": "Test", "theme": "business_red", "language": "zh-CN", "author": "AI", "version": "2.0"},
                "slides": [
                    {
                        "slide_id": "s1",
                        "title": "能力框架",
                        "intent": "framework",
                        "key_message": "四层能力共同支撑转型落地。",
                        "blocks": [
                            {"kind": "image", "mode": "placeholder", "caption": "框架示意"},
                            {"kind": "bullets", "items": ["业务层", "数据层", "平台层"]},
                        ],
                    }
                ],
            }
        )

        slide = validated.deck.slides[0]
        self.assertEqual(slide.layout, "title_image")
        self.assertEqual(slide.image.mode, "placeholder")
        self.assertIn("四层能力共同支撑转型落地。", slide.content)

    def test_compile_dense_analysis_to_two_columns(self):
        validated = compile_semantic_deck_payload(
            {
                "meta": {"title": "Test", "theme": "business_red", "language": "zh-CN", "author": "AI", "version": "2.0"},
                "slides": [
                    {
                        "slide_id": "s1",
                        "title": "关键举措",
                        "intent": "analysis",
                        "blocks": [
                            {
                                "kind": "bullets",
                                "heading": "措施",
                                "items": ["措施一", "措施二", "措施三", "措施四", "措施五", "措施六", "措施七"],
                            }
                        ],
                    }
                ],
            }
        )

        slide = validated.deck.slides[0]
        self.assertEqual(slide.layout, "two_columns")
        self.assertEqual(slide.left.heading, "措施")
        self.assertEqual(slide.right.heading, "进一步展开")

    def test_compile_conclusion_statement_to_title_only(self):
        validated = compile_semantic_deck_payload(
            {
                "meta": {"title": "Test", "theme": "business_red", "language": "zh-CN", "author": "AI", "version": "2.0"},
                "slides": [
                    {
                        "slide_id": "s1",
                        "title": "结论",
                        "intent": "conclusion",
                        "blocks": [{"kind": "statement", "text": "先打通主链，再扩展到运营闭环。"}],
                    }
                ],
            }
        )

        slide = validated.deck.slides[0]
        self.assertEqual(slide.layout, "title_only")
        self.assertEqual(slide.title, "先打通主链，再扩展到运营闭环。")


    def test_compile_cards_pair_to_two_columns(self):
        validated = compile_semantic_deck_payload(
            {
                "meta": {"title": "Test", "theme": "business_red", "language": "zh-CN", "author": "AI", "version": "2.0"},
                "slides": [
                    {
                        "slide_id": "s1",
                        "title": "Core Capabilities",
                        "intent": "framework",
                        "blocks": [
                            {
                                "kind": "cards",
                                "cards": [
                                    {"title": "Plan", "body": "Drive aligned decisions"},
                                    {"title": "Execute", "body": "Stabilize delivery control"},
                                ],
                            }
                        ],
                    }
                ],
            }
        )

        slide = validated.deck.slides[0]
        self.assertEqual(slide.layout, "two_columns")
        self.assertEqual(slide.left.heading, "Plan")
        self.assertEqual(slide.right.heading, "Execute")

    def test_compile_stats_pair_to_two_columns(self):
        validated = compile_semantic_deck_payload(
            {
                "meta": {"title": "Test", "theme": "business_red", "language": "zh-CN", "author": "AI", "version": "2.0"},
                "slides": [
                    {
                        "slide_id": "s1",
                        "title": "KPI Snapshot",
                        "intent": "analysis",
                        "blocks": [
                            {
                                "kind": "stats",
                                "metrics": [
                                    {"label": "OTD", "value": "95%", "note": "Target >=93%"},
                                    {"label": "Yield", "value": "98%", "note": "Stable month-on-month"},
                                ],
                            }
                        ],
                    }
                ],
            }
        )

        slide = validated.deck.slides[0]
        self.assertEqual(slide.layout, "two_columns")
        self.assertEqual(slide.left.heading, "OTD")
        self.assertEqual(slide.right.heading, "Yield")

    def test_compile_timeline_dense_to_two_columns(self):
        validated = compile_semantic_deck_payload(
            {
                "meta": {"title": "Test", "theme": "business_red", "language": "zh-CN", "author": "AI", "version": "2.0"},
                "slides": [
                    {
                        "slide_id": "s1",
                        "title": "Roadmap",
                        "intent": "narrative",
                        "blocks": [
                            {
                                "kind": "timeline",
                                "stages": [
                                    {"title": "Q1", "detail": "Scope and align"},
                                    {"title": "Q2", "detail": "Build core workflows"},
                                    {"title": "Q3", "detail": "Scale pilot"},
                                    {"title": "Q4", "detail": "Roll out governance"},
                                ],
                            }
                        ],
                    }
                ],
            }
        )

        slide = validated.deck.slides[0]
        self.assertEqual(slide.layout, "two_columns")

    def test_compile_matrix_block_to_two_columns(self):
        validated = compile_semantic_deck_payload(
            {
                "meta": {"title": "Test", "theme": "business_red", "language": "zh-CN", "author": "AI", "version": "2.0"},
                "slides": [
                    {
                        "slide_id": "s1",
                        "title": "Risk Matrix",
                        "intent": "analysis",
                        "blocks": [
                            {
                                "kind": "matrix",
                                "x_axis": "Impact",
                                "y_axis": "Probability",
                                "cells": [
                                    {"title": "Low-Low", "body": "Monitor routinely"},
                                    {"title": "Low-High", "body": "Prepare response"},
                                    {"title": "High-Low", "body": "Assign owner"},
                                    {"title": "High-High", "body": "Escalate now"},
                                ],
                            }
                        ],
                    }
                ],
            }
        )

        slide = validated.deck.slides[0]
        self.assertEqual(slide.layout, "two_columns")
        self.assertEqual(slide.left.heading, "Impact")
        self.assertEqual(slide.right.heading, "Probability")

if __name__ == "__main__":
    unittest.main()
