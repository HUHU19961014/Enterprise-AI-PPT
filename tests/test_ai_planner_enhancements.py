import unittest
from pathlib import Path

from tools.sie_autoppt.planning.ai_planner import (
    AiPlanningRequest,
    AiSlideBounds,
    build_ai_planning_prompts,
    build_deck_spec_from_ai_outline,
)


class AiPlannerEnhancementTests(unittest.TestCase):
    def test_build_ai_planning_prompts_include_clarified_context(self):
        developer_prompt, user_prompt = build_ai_planning_prompts(
            AiPlanningRequest(
                topic="帮我做Q2业绩汇报，5页，给公司领导看，商务专业风格",
                brief="重点讲增长数据、技术突破、下阶段计划",
            )
        )

        self.assertIn("Clarifier context", developer_prompt)
        self.assertIn("商务专业", user_prompt)
        self.assertIn("公司领导", user_prompt)
        self.assertIn("5", user_prompt)

    def test_build_ai_planning_prompts_include_template_style_context(self):
        developer_prompt, user_prompt = build_ai_planning_prompts(
            AiPlanningRequest(topic="企业经营分析汇报", chapters=3),
            template_path=Path("assets/templates/business_gold/template.pptx"),
        )

        self.assertIn("Clarifier context", developer_prompt)
        self.assertIn("Executive Gold", user_prompt)
        self.assertIn("premium", user_prompt)

    def test_build_deck_spec_from_ai_outline_builds_payload_for_complex_patterns(self):
        deck = build_deck_spec_from_ai_outline(
            {
                "cover_title": "AI AutoPPT 增强规划",
                "body_pages": [
                    {
                        "title": "现状与目标对比",
                        "subtitle": "明确升级方向",
                        "bullets": [
                            "当前流程: 协同链路长",
                            "当前数据: 口径不统一",
                            "目标流程: 形成闭环交付",
                            "目标数据: 建立统一底座",
                        ],
                        "pattern_id": "comparison_upgrade",
                        "nav_title": "对比",
                    },
                    {
                        "title": "核心能力",
                        "subtitle": "能力矩阵",
                        "bullets": [
                            "数据治理: 统一标准与口径",
                            "集成协同: 打通跨系统链路",
                            "运营分析: 支撑经营决策",
                        ],
                        "pattern_id": "capability_ring",
                        "nav_title": "能力",
                    },
                    {
                        "title": "实施路径",
                        "subtitle": "阶段化推进",
                        "bullets": [
                            "阶段一: 完成现状调研",
                            "阶段二: 搭建基础底座",
                            "阶段三: 推进试点上线",
                            "阶段四: 规模化复制",
                        ],
                        "pattern_id": "five_phase_path",
                        "nav_title": "路径",
                    },
                ],
            },
            slide_bounds=AiSlideBounds(min_slides=3, max_slides=3),
        )

        self.assertEqual(deck.body_pages[0].pattern_id, "comparison_upgrade")
        self.assertIn("left_cards", deck.body_pages[0].payload)
        self.assertIn("items", deck.body_pages[1].payload)
        self.assertIn("stages", deck.body_pages[2].payload)

    def test_build_deck_spec_from_ai_outline_builds_payload_for_dashboard_and_roadmap(self):
        deck = build_deck_spec_from_ai_outline(
            {
                "cover_title": "经营节奏管理",
                "body_pages": [
                    {
                        "title": "经营指标",
                        "subtitle": "统一经营视图",
                        "bullets": ["收入增长: 18%", "利润提升: 6%", "订单交付率: 96%", "重点客户续约率: 88%"],
                        "pattern_id": "kpi_dashboard",
                        "nav_title": "指标",
                    },
                    {
                        "title": "里程碑路线图",
                        "subtitle": "年度推进安排",
                        "bullets": ["Q1: 完成调研与诊断", "Q2: 搭建数据底座", "Q3: 启动试点", "Q4: 全面推广"],
                        "pattern_id": "roadmap_timeline",
                        "nav_title": "路线图",
                    },
                ],
            },
            slide_bounds=AiSlideBounds(min_slides=2, max_slides=2),
        )

        self.assertIn("metrics", deck.body_pages[0].payload)
        self.assertIn("insights", deck.body_pages[0].payload)
        self.assertIn("stages", deck.body_pages[1].payload)

    def test_build_deck_spec_from_ai_outline_builds_payload_for_risk_and_claim(self):
        deck = build_deck_spec_from_ai_outline(
            {
                "cover_title": "仲裁分析",
                "body_pages": [
                    {
                        "title": "风险评估",
                        "subtitle": "影响与概率判断",
                        "bullets": ["汇率风险: 影响偿债能力", "政策风险: 影响谈判预期", "执行风险: 影响项目收益", "声誉风险: 影响后续合作"],
                        "pattern_id": "risk_matrix",
                        "nav_title": "风险",
                    },
                    {
                        "title": "索赔构成",
                        "subtitle": "金额拆解",
                        "bullets": ["电费欠款: $2.1B", "违约利息: $1.3B", "汇率损失: $0.8B", "其他费用: $0.3B"],
                        "pattern_id": "claim_breakdown",
                        "nav_title": "索赔",
                    },
                ],
            },
            slide_bounds=AiSlideBounds(min_slides=2, max_slides=2),
        )

        self.assertIn("items", deck.body_pages[0].payload)
        self.assertIn("claims", deck.body_pages[1].payload)
        self.assertIn("summary", deck.body_pages[1].payload)
