from __future__ import annotations

import argparse
from pathlib import Path

try:
    from .sie_onepage_designer import BulletItem, LawRow, OnePageBrief, TextFragment, build_onepage_slide
except ImportError:
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from scenario_generators.sie_onepage_designer import BulletItem, LawRow, OnePageBrief, TextFragment, build_onepage_slide


PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_PPT = PROJECT_ROOT / "output" / "sie_file_upload_checklist_onepage_sie_style.pptx"


BRIEF = OnePageBrief(
    title="赛意系统文件上传清单与责任时限",
    kicker="",
    summary_fragments=(
        TextFragment("统一 2025-07-15 起始批次的文件上传口径，按电池与硅片两类梳理责任人与完成时限。"),
        TextFragment(
            "起始批次发票号 NS2507140104012、发货单号 XC2025071500000509；后续发货批次文件直接上传赛意系统。",
            bold=True,
            color=(173, 5, 61),
            new_paragraph=True,
        ),
    ),
    law_rows=(
        LawRow(
            number="01",
            title="电池文件：按三位责任人分工上传",
            badge="优先执行",
            badge_red=True,
            runs=(
                TextFragment("张津津：", bold=True, color=(15, 23, 42)),
                TextFragment("商业发票和装箱清单、补充协议、采购订单、付款凭证，ERP 发货单后 7-13 天内完成。 "),
                TextFragment("翁初阳：", bold=True, color=(15, 23, 42)),
                TextFragment("提单、原产地、报关单，ERP 发货单后 10-13 天内完成。 "),
                TextFragment("约翰娜：", bold=True, color=(15, 23, 42)),
                TextFragment("送货单，ERP 送货单生成后 1 天内完成。"),
            ),
        ),
        LawRow(
            number="02",
            title="硅片文件：石露与郑棌匀分工完成",
            badge="同步上传",
            badge_red=False,
            runs=(
                TextFragment("石露：", bold=True, color=(15, 23, 42)),
                TextFragment("检验报告、出货清单、送货单、合同、发票和装箱清单，原则上在 ERP 送货单生成时上传；付款凭证在发货单后 13 天内完成。 "),
                TextFragment("郑棌匀：", bold=True, color=(15, 23, 42)),
                TextFragment("提单、清关单、原产地，按 ERP 送货单生成时间上传。"),
            ),
        ),
        LawRow(
            number="03",
            title="执行要求：统一触发点与后续批次口径",
            badge="长期机制",
            badge_red=False,
            runs=(
                TextFragment("ERP 发货单与 ERP 送货单", bold=True, color=(15, 23, 42)),
                TextFragment("是全部时限的起算点；同批次资料需按责任人一次归集、一次上传，并在赛意系统保留可追溯记录。"),
            ),
        ),
    ),
    right_kicker="EXECUTION VIEW",
    right_title="一页看清责任、触发点与上传节奏",
    process_steps=("ERP发货", "ERP送货", "资料归集", "赛意上传", "批次留痕"),
    right_bullets=(
        BulletItem("时限口径：", "主要分为发货单后 7/10/13 天，或送货单生成时、生成后 1 天三类。"),
        BulletItem("责任聚焦：", "张津津与石露承担文件量最大，应优先准备票据类、合同类与付款凭证。"),
        BulletItem("批次说明：", "2025-07-15 起始批次使用发票号 NS2507140104012、发货单号 XC2025071500000509 作为执行基准。"),
    ),
    strategy_title="执行建议：按“品类-责任人-时限”建立上传台账与提醒机制",
    strategy_fragments=(
        TextFragment("建议围绕电池/硅片两类文件建立上传台账，按责任人拆解到日，并对 ERP 发货单、ERP 送货单两个时间节点设置自动提醒。"),
        TextFragment("目标是让后续批次文件直接上传赛意系统，形成稳定、可追溯的执行闭环。", bold=True, color=(255, 255, 255), new_paragraph=True),
    ),
    footer="STRICTLY CONFIDENTIAL | 2026 SIE 文件上传执行清单",
    page_no="01",
    required_terms=("张津津", "翁初阳", "约翰娜", "石露", "郑棌匀", "赛意系统", "NS2507140104012", "XC2025071500000509"),
    variant="auto",
    layout_strategy="auto",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a one-page SIE slide for the SIE file upload checklist.")
    parser.add_argument("--output", default=str(OUTPUT_PPT), help="Output PPTX path.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    built, review_path, score_path, _ = build_onepage_slide(BRIEF, output_path=Path(args.output).resolve(), export_review=True)
    print(built)
    print(review_path)
    print(score_path)


if __name__ == "__main__":
    main()
