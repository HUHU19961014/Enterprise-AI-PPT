import json
import sys
import tempfile
import unittest
from pathlib import Path

from tools.sie_autoppt.planning.ai_planner import (
    AiSlideBounds,
    AiPlanningRequest,
    build_ai_outline_schema,
    build_external_planner_payload,
    build_ai_planning_prompts,
    build_deck_spec_from_ai_outline,
    plan_deck_spec_with_ai,
    resolve_ai_slide_bounds,
    resolve_external_planner_command,
)


class AiPlannerTests(unittest.TestCase):
    def test_plan_deck_spec_with_ai_blocks_fully_ambiguous_requests(self):
        with self.assertRaises(ValueError) as context:
            plan_deck_spec_with_ai(AiPlanningRequest(topic="帮我做PPT"))

        self.assertIn("请先回答下面的问题", str(context.exception))

    def test_outline_schema_matches_requested_page_count(self):
        schema = build_ai_outline_schema(AiSlideBounds(min_slides=3, max_slides=3))

        self.assertEqual(schema["properties"]["body_pages"]["minItems"], 3)
        self.assertEqual(schema["properties"]["body_pages"]["maxItems"], 3)
        self.assertIn("pattern_id", schema["properties"]["body_pages"]["items"]["properties"])

    def test_build_deck_spec_from_ai_outline_normalizes_patterns(self):
        deck = build_deck_spec_from_ai_outline(
            {
                "cover_title": "AI 自动化转型方案",
                "body_pages": [
                    {
                        "title": "现状与痛点",
                        "subtitle": "识别当前主要阻碍",
                        "bullets": ["流程割裂导致协同成本高", "数据口径不一致影响决策效率"],
                        "pattern_id": "pain_points",
                        "nav_title": "痛点",
                    },
                    {
                        "title": "目标架构",
                        "subtitle": "统一平台与能力中台",
                        "bullets": ["统一数据底座与集成层", "沉淀可复用业务能力模块"],
                        "pattern_id": "solution_architecture",
                        "nav_title": "架构",
                    },
                    {
                        "title": "实施路径",
                        "subtitle": "分阶段推进落地",
                        "bullets": ["先打通关键业务链路", "再扩展到跨部门协同场景"],
                        "pattern_id": "implementation_plan",
                        "nav_title": "路径",
                    },
                ],
            },
            slide_bounds=AiSlideBounds(min_slides=3, max_slides=3),
        )

        self.assertEqual(deck.cover_title, "AI 自动化转型方案")
        self.assertEqual(
            [page.pattern_id for page in deck.body_pages],
            ["pain_cards", "solution_architecture", "roadmap_timeline"],
        )
        self.assertEqual([page.page_key for page in deck.body_pages], ["ai_page_01", "ai_page_02", "ai_page_03"])

    def test_build_deck_spec_from_ai_outline_supports_dashboard_and_roadmap(self):
        deck = build_deck_spec_from_ai_outline(
            {
                "cover_title": "经营与推进总览",
                "body_pages": [
                    {
                        "title": "核心指标",
                        "subtitle": "经营表现摘要",
                        "bullets": ["收入增速: 18%", "利润改善: +6%", "上线工厂: 12 个", "客户满意度: 92%"],
                        "pattern_id": "kpi_dashboard",
                        "nav_title": "指标",
                    },
                    {
                        "title": "年度路线图",
                        "subtitle": "按季度推进",
                        "bullets": ["Q1: 完成现状诊断", "Q2: 完成平台建设", "Q3: 推进试点上线", "Q4: 规模复制推广"],
                        "pattern_id": "roadmap_timeline",
                        "nav_title": "路线图",
                    },
                ],
            },
            slide_bounds=AiSlideBounds(min_slides=2, max_slides=2),
        )

        self.assertEqual([page.pattern_id for page in deck.body_pages], ["kpi_dashboard", "roadmap_timeline"])
        self.assertIn("metrics", deck.body_pages[0].payload)
        self.assertIn("stages", deck.body_pages[1].payload)

    def test_build_deck_spec_from_ai_outline_supports_risk_and_claim_breakdown(self):
        deck = build_deck_spec_from_ai_outline(
            {
                "cover_title": "风险与金额分析",
                "body_pages": [
                    {
                        "title": "关键风险",
                        "subtitle": "风险矩阵",
                        "bullets": ["汇率风险: 影响融资偿付", "政策风险: 影响审批进度", "执行风险: 影响交付节奏", "现金流风险: 影响后续投入"],
                        "pattern_id": "risk_matrix",
                        "nav_title": "风险",
                    },
                    {
                        "title": "索赔拆解",
                        "subtitle": "主项金额构成",
                        "bullets": ["电费欠款: $2.1B", "违约利息: $1.3B", "汇率损失: $0.8B", "其他费用: $0.3B"],
                        "pattern_id": "claim_breakdown",
                        "nav_title": "索赔",
                    },
                ],
            },
            slide_bounds=AiSlideBounds(min_slides=2, max_slides=2),
        )

        self.assertEqual([page.pattern_id for page in deck.body_pages], ["risk_matrix", "claim_breakdown"])
        self.assertIn("items", deck.body_pages[0].payload)
        self.assertIn("claims", deck.body_pages[1].payload)

    def test_build_ai_planning_prompts_embed_topic_and_brief(self):
        developer_prompt, user_prompt = build_ai_planning_prompts(
            AiPlanningRequest(
                topic="制造业 ERP 智能化升级",
                chapters=3,
                audience="CIO / 业务负责人",
                brief="现有系统分散，主数据治理薄弱。",
            )
        )

        self.assertIn("Return exactly 3 body pages", developer_prompt)
        self.assertIn("制造业 ERP 智能化升级", user_prompt)
        self.assertIn("现有系统分散", user_prompt)

    def test_build_ai_planning_prompts_contains_critical_constraints(self):
        developer_prompt, user_prompt = build_ai_planning_prompts(
            AiPlanningRequest(topic="测试主题", chapters=5)
        )

        # 验证页数约束
        self.assertIn("Return exactly 5 body pages", developer_prompt)

        # 验证 pattern 枚举约束
        self.assertIn("pattern_id from the provided enum", developer_prompt)

        # 验证支持的 pattern 列表
        self.assertIn("general_business", developer_prompt)
        self.assertIn("solution_architecture", developer_prompt)
        self.assertIn("process_flow", developer_prompt)
        self.assertIn("org_governance", developer_prompt)

    def test_build_ai_planning_prompts_range_mode_constraints(self):
        developer_prompt, user_prompt = build_ai_planning_prompts(
            AiPlanningRequest(topic="测试主题", min_slides=3, max_slides=7)
        )

        # 验证范围约束
        self.assertIn("between 3 and 7 body pages", developer_prompt)
        self.assertIn("3-7", user_prompt)

        # 验证内容密度指导
        self.assertIn("content density", developer_prompt)

    def test_resolve_ai_slide_bounds_uses_content_driven_default_range(self):
        bounds = resolve_ai_slide_bounds(
            AiPlanningRequest(
                topic="企业数字化转型",
                brief="需要覆盖现状、目标架构、实施路径、组织机制和投资收益分析。" * 200,
            )
        )

        self.assertEqual((bounds.min_slides, bounds.max_slides), (10, 20))

    def test_build_external_planner_payload_contains_schema_and_prompts(self):
        request = AiPlanningRequest(topic="测试主题", chapters=2, audience="管理层", brief="补充材料")
        bounds = resolve_ai_slide_bounds(request)
        developer_prompt, user_prompt = build_ai_planning_prompts(request, slide_bounds=bounds)

        payload = build_external_planner_payload(request, developer_prompt, user_prompt, bounds)

        self.assertEqual(payload["request"]["topic"], "测试主题")
        self.assertEqual(payload["request"]["min_slides"], 2)
        self.assertEqual(payload["outline_schema"]["properties"]["body_pages"]["minItems"], 2)
        self.assertIn("Return exactly 2 body pages", payload["developer_prompt"])

    def test_plan_deck_spec_with_ai_supports_external_command(self):
        outline = {
            "cover_title": "外部规划器验证",
            "body_pages": [
                {
                    "title": "第一页",
                    "subtitle": "摘要",
                    "bullets": ["要点一", "要点二"],
                    "pattern_id": "general_business",
                    "nav_title": "第一页",
                }
            ],
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            script_path = Path(temp_dir) / "external_planner.py"
            script_path.write_text(
                "import json, sys\n"
                "json.load(sys.stdin)\n"
                f"print({json.dumps(json.dumps(outline, ensure_ascii=False))})\n",
                encoding="utf-8",
            )
            command = f'{sys.executable} "{script_path}"'

            deck = plan_deck_spec_with_ai(
                AiPlanningRequest(topic="外部命令测试", chapters=1),
                planner_command=command,
            )

        self.assertEqual(deck.cover_title, "外部规划器验证")
        self.assertEqual(deck.body_pages[0].title, "第一页")

    def test_external_command_does_not_execute_shell_chaining(self):
        outline = {
            "cover_title": "安全验证",
            "body_pages": [
                {
                    "title": "第一页",
                    "subtitle": "摘要",
                    "bullets": ["要点一", "要点二"],
                    "pattern_id": "general_business",
                    "nav_title": "第一页",
                }
            ],
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            script_path = Path(temp_dir) / "external_planner.py"
            sentinel_path = Path(temp_dir) / "injected.txt"
            script_path.write_text(
                "import json, sys\n"
                "json.load(sys.stdin)\n"
                f"print({json.dumps(json.dumps(outline, ensure_ascii=False))})\n",
                encoding="utf-8",
            )
            command = (
                f'{sys.executable} "{script_path}" '
                f'& {sys.executable} -c "from pathlib import Path; Path(r\'{sentinel_path}\').write_text(\'owned\', encoding=\'utf-8\')"'
            )

            deck = plan_deck_spec_with_ai(
                AiPlanningRequest(topic="外部命令安全测试", chapters=1),
                planner_command=command,
            )
            self.assertFalse(sentinel_path.exists())

        self.assertEqual(deck.cover_title, "安全验证")

    def test_resolve_external_planner_command_prefers_explicit_value(self):
        self.assertEqual(resolve_external_planner_command("echo test"), "echo test")
