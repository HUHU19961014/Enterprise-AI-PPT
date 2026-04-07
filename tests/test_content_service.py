import unittest

from tools.sie_autoppt.content_service import build_deck_spec_from_structure, map_structure_to_slide_schema
from tools.sie_autoppt.models import StructureArgument, StructureSection, StructureSpec


class ContentServiceTests(unittest.TestCase):
    def test_map_structure_to_slide_schema_detects_process_and_comparison(self):
        process_schema = map_structure_to_slide_schema(
            structure_type="solution_design",
            title="三阶段推进路径",
            key_message="按阶段推进以降低风险",
            arguments=[StructureArgument(point="阶段一"), StructureArgument(point="阶段二")],
        )
        comparison_schema = map_structure_to_slide_schema(
            structure_type="comparison_analysis",
            title="现状与目标对比",
            key_message="从旧模式切换到新模式",
            arguments=[
                StructureArgument(point="旧模式成本高"),
                StructureArgument(point="旧模式协同慢"),
                StructureArgument(point="新模式自动化更强"),
                StructureArgument(point="新模式治理更清晰"),
            ],
        )

        self.assertEqual(process_schema, "process")
        self.assertEqual(comparison_schema, "comparison")

    def test_build_deck_spec_from_structure_preserves_structure_order(self):
        structure = StructureSpec(
            core_message="AI 商业化需要从价值验证走向规模复制",
            structure_type="strategy_report",
            sections=[
                StructureSection(
                    title="核心结论",
                    key_message="先验证价值，再放大组织能力",
                    arguments=[
                        StructureArgument(point="先锁定高价值场景", evidence="避免范围失控"),
                        StructureArgument(point="先建立交付机制", evidence="保证复制效率"),
                    ],
                ),
                StructureSection(
                    title="实施路径",
                    key_message="按三阶段推进落地",
                    arguments=[
                        StructureArgument(point="试点验证", evidence="验证业务收益"),
                        StructureArgument(point="流程嵌入", evidence="打通协同接口"),
                        StructureArgument(point="规模复制", evidence="形成标准机制"),
                    ],
                ),
            ],
        )

        deck = build_deck_spec_from_structure(structure, topic="AI 商业化路径分析")

        self.assertEqual(deck.cover_title, "AI 商业化路径分析")
        self.assertEqual([page.title for page in deck.body_pages], ["核心结论", "实施路径"])
        self.assertEqual(deck.body_pages[0].layout_hints["slide_schema"], "conclusion")
        self.assertEqual(deck.body_pages[1].layout_hints["slide_schema"], "process")
        self.assertEqual(deck.body_pages[1].pattern_id, "process_flow")
        self.assertEqual(deck.body_pages[1].payload["steps"][0]["title"], "试点验证")

    def test_build_deck_spec_from_structure_supports_dashboard_and_roadmap(self):
        structure = StructureSpec(
            core_message="经营与执行需要共用一套节奏视图",
            structure_type="strategy_report",
            sections=[
                StructureSection(
                    title="经营指标仪表盘",
                    key_message="先统一经营指标口径",
                    arguments=[
                        StructureArgument(point="收入增长", evidence="18%"),
                        StructureArgument(point="利润提升", evidence="6%"),
                        StructureArgument(point="交付准时率", evidence="96%"),
                        StructureArgument(point="客户满意度", evidence="92%"),
                    ],
                ),
                StructureSection(
                    title="年度路线图",
                    key_message="按季度推进关键里程碑",
                    arguments=[
                        StructureArgument(point="Q1", evidence="完成现状诊断"),
                        StructureArgument(point="Q2", evidence="完成底座建设"),
                        StructureArgument(point="Q3", evidence="推进试点上线"),
                        StructureArgument(point="Q4", evidence="规模推广复制"),
                    ],
                ),
            ],
        )

        deck = build_deck_spec_from_structure(structure, topic="经营节奏管理")

        self.assertEqual(deck.body_pages[0].pattern_id, "kpi_dashboard")
        self.assertEqual(deck.body_pages[0].layout_hints["slide_schema"], "dashboard")
        self.assertIn("metrics", deck.body_pages[0].payload)
        self.assertEqual(deck.body_pages[1].pattern_id, "roadmap_timeline")
        self.assertEqual(deck.body_pages[1].layout_hints["slide_schema"], "roadmap")
        self.assertIn("stages", deck.body_pages[1].payload)

    def test_build_deck_spec_from_structure_supports_risk_and_claim(self):
        structure = StructureSpec(
            core_message="风险和金额拆解需要并行呈现",
            structure_type="analysis_report",
            sections=[
                StructureSection(
                    title="风险矩阵",
                    key_message="优先处理高影响高概率风险",
                    arguments=[
                        StructureArgument(point="汇率风险", evidence="影响偿债能力"),
                        StructureArgument(point="政策风险", evidence="影响谈判预期"),
                        StructureArgument(point="执行风险", evidence="影响交付节奏"),
                        StructureArgument(point="声誉风险", evidence="影响合作空间"),
                    ],
                ),
                StructureSection(
                    title="索赔金额拆解",
                    key_message="先识别金额最大的主项",
                    arguments=[
                        StructureArgument(point="电费欠款", evidence="$2.1B"),
                        StructureArgument(point="违约利息", evidence="$1.3B"),
                        StructureArgument(point="汇率损失", evidence="$0.8B"),
                        StructureArgument(point="其他费用", evidence="$0.3B"),
                    ],
                ),
            ],
        )

        deck = build_deck_spec_from_structure(structure, topic="仲裁分析")

        self.assertEqual(deck.body_pages[0].pattern_id, "risk_matrix")
        self.assertEqual(deck.body_pages[0].layout_hints["slide_schema"], "risk")
        self.assertIn("items", deck.body_pages[0].payload)
        self.assertEqual(deck.body_pages[1].pattern_id, "claim_breakdown")
        self.assertEqual(deck.body_pages[1].layout_hints["slide_schema"], "claim")
        self.assertIn("claims", deck.body_pages[1].payload)
