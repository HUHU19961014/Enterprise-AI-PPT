from __future__ import annotations

import argparse
import json
import os
from dataclasses import replace
from pathlib import Path

try:
    from .sie_onepage_designer import (
        BulletItem,
        LawRow,
        OnePageBrief,
        TextFragment,
        build_onepage_brief_from_structure,
        build_onepage_slide,
    )
    from sie_autoppt.llm_openai import OpenAIConfigurationError, OpenAIResponsesError
    from sie_autoppt.structure_service import StructureGenerationRequest, generate_structure_with_ai
except ImportError:
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from scenario_generators.sie_onepage_designer import (
        BulletItem,
        LawRow,
        OnePageBrief,
        TextFragment,
        build_onepage_brief_from_structure,
        build_onepage_slide,
    )
    from sie_autoppt.llm_openai import OpenAIConfigurationError, OpenAIResponsesError
    from sie_autoppt.structure_service import StructureGenerationRequest, generate_structure_with_ai


def _parse_text_fragment(payload: dict[str, object]) -> TextFragment:
    color_raw = payload.get("color")
    color = tuple(color_raw) if isinstance(color_raw, list) and len(color_raw) == 3 else None
    return TextFragment(
        text=str(payload.get("text", "")),
        bold=bool(payload.get("bold", False)),
        color=color,  # type: ignore[arg-type]
        new_paragraph=bool(payload.get("new_paragraph", False)),
    )


def _parse_law_row(payload: dict[str, object]) -> LawRow:
    runs = tuple(_parse_text_fragment(item) for item in payload.get("runs", []))
    return LawRow(
        number=str(payload.get("number", "")),
        title=str(payload.get("title", "")),
        badge=str(payload.get("badge", "")),
        badge_red=bool(payload.get("badge_red", False)),
        runs=runs,
    )


def _parse_bullet_item(payload: dict[str, object]) -> BulletItem:
    return BulletItem(label=str(payload.get("label", "")), body=str(payload.get("body", "")))


def load_brief_from_json(path: Path) -> OnePageBrief:
    payload = json.loads(path.read_text(encoding="utf-8"))
    layout_overrides = payload.get("layout_overrides")
    if not isinstance(layout_overrides, dict):
        layout_overrides = None
    typography_overrides = payload.get("typography_overrides")
    if not isinstance(typography_overrides, dict):
        typography_overrides = None
    return OnePageBrief(
        title=str(payload["title"]),
        kicker=str(payload.get("kicker", "")),
        summary_fragments=tuple(_parse_text_fragment(item) for item in payload.get("summary_fragments", [])),
        law_rows=tuple(_parse_law_row(item) for item in payload.get("law_rows", [])),
        right_kicker=str(payload.get("right_kicker", "")),
        right_title=str(payload.get("right_title", "")),
        process_steps=tuple(str(step) for step in payload.get("process_steps", [])),
        right_bullets=tuple(_parse_bullet_item(item) for item in payload.get("right_bullets", [])),
        strategy_title=str(payload.get("strategy_title", "")),
        strategy_fragments=tuple(_parse_text_fragment(item) for item in payload.get("strategy_fragments", [])),
        footer=str(payload.get("footer", "STRICTLY CONFIDENTIAL | 2026 SIE One-page Brief")),
        page_no=str(payload.get("page_no", "01")),
        required_terms=tuple(str(term) for term in payload.get("required_terms", [])),
        variant=str(payload.get("variant", "auto")),
        layout_strategy=str(payload.get("layout_strategy", "auto")),
        reference_request=str(payload.get("reference_request", "")),
        banned_phrases=tuple(str(term) for term in payload.get("banned_phrases", [])),
        layout_overrides=layout_overrides,
        typography_overrides=typography_overrides,
    )


def _brief_to_plain_text(brief: OnePageBrief) -> str:
    parts = [
        brief.title,
        brief.kicker,
        brief.right_kicker,
        brief.right_title,
        brief.strategy_title,
        " ".join(fragment.text for fragment in brief.summary_fragments),
        " ".join(row.title for row in brief.law_rows),
        " ".join(fragment.text for row in brief.law_rows for fragment in row.runs),
        " ".join(brief.process_steps),
        " ".join(item.label + item.body for item in brief.right_bullets),
        " ".join(fragment.text for fragment in brief.strategy_fragments),
    ]
    return "\n".join(part for part in parts if part).strip()


def build_ai_brief_from_source_text(
    *,
    topic: str,
    source_text: str,
    model: str | None,
    sections: int = 3,
) -> OnePageBrief:
    request = StructureGenerationRequest(topic=topic.strip(), brief=source_text.strip(), sections=sections)
    structure_result = generate_structure_with_ai(request, model=model)
    return build_onepage_brief_from_structure(
        structure_result.structure,
        topic=topic.strip(),
        layout_strategy="auto",
    )


def apply_ai_content_reframe(brief: OnePageBrief, model: str | None, sections: int = 3) -> OnePageBrief:
    ai_brief = build_ai_brief_from_source_text(
        topic=brief.title,
        source_text=_brief_to_plain_text(brief),
        model=model,
        sections=sections,
    )
    return replace(
        ai_brief,
        footer=brief.footer,
        page_no=brief.page_no,
        required_terms=brief.required_terms or ai_brief.required_terms,
        reference_request=brief.reference_request,
        banned_phrases=brief.banned_phrases,
    )


def _openai_configured() -> bool:
    return bool(os.environ.get("OPENAI_API_KEY", "").strip())


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a one-page SIE PPT with optional AI content planning and AI layout strategy."
    )
    parser.add_argument("--brief-json", help="Path to JSON brief file (UTF-8).")
    parser.add_argument("--source-text-file", help="Path to UTF-8 source text used for AI content planning.")
    parser.add_argument("--topic", help="Topic title used when --source-text-file is provided.")
    parser.add_argument("--output", required=True, help="Output PPTX path.")
    parser.add_argument(
        "--ai-mode",
        choices=("host", "openai", "off"),
        default="host",
        help="AI execution mode: host=use current chat window AI (default), openai=script-side OpenAI API, off=no AI planning.",
    )
    parser.add_argument(
        "--ai-content",
        choices=("off", "on"),
        default="on",
        help="Enable AI content planning.",
    )
    parser.add_argument(
        "--ai-strategy",
        choices=("off", "on"),
        default="on",
        help="Enable AI layout strategy selection.",
    )
    parser.add_argument("--ai-model", default=None, help="Override AI model id.")
    parser.add_argument("--skip-review", action="store_true", help="Skip post-generation review.")
    args = parser.parse_args()
    if not args.brief_json and not args.source_text_file:
        parser.error("Either --brief-json or --source-text-file is required.")
    if args.source_text_file and not args.topic:
        parser.error("--topic is required when using --source-text-file.")
    if args.ai_mode == "host" and args.source_text_file and args.brief_json:
        parser.error("In host mode, provide either --brief-json or --source-text-file, not both.")
    return args


def main() -> None:
    args = parse_args()
    if args.ai_mode == "host":
        if args.brief_json:
            brief = load_brief_from_json(Path(args.brief_json).resolve())
        else:
            source_text = Path(args.source_text_file).resolve().read_text(encoding="utf-8")
            print(
                "[warn] host mode expects brief.json from current chat AI. "
                "No --brief-json supplied; fallback to minimal brief rendering."
            )
            brief = OnePageBrief(
                title=str(args.topic),
                kicker="",
                summary_fragments=(TextFragment(source_text[:180]),),
                law_rows=(),
                right_kicker="HOST AI MODE",
                right_title=f"{args.topic}（待AI结构化）",
                process_steps=("提炼目标", "结构规划", "版式选择", "渲染输出"),
                right_bullets=(BulletItem("建议：", "请让当前对话窗口AI先产出 brief.json 后再渲染。"),),
                strategy_title="执行建议：先由窗口AI结构化内容，再调用渲染器生成SIE页面",
                strategy_fragments=(TextFragment("当前为 host_ai 最小降级输出。"),),
                footer="STRICTLY CONFIDENTIAL | 2026 SIE One-page Brief",
                page_no="01",
                required_terms=(str(args.topic),),
                variant="auto",
                layout_strategy="auto",
            )
        # host mode does not call script-side OpenAI APIs by default
        require_ai_strategy = False
    elif args.ai_mode == "openai":
        if args.source_text_file:
            source_text = Path(args.source_text_file).resolve().read_text(encoding="utf-8")
            if args.ai_content == "on":
                try:
                    brief = build_ai_brief_from_source_text(
                        topic=str(args.topic),
                        source_text=source_text,
                        model=args.ai_model,
                        sections=3,
                    )
                except (OpenAIConfigurationError, OpenAIResponsesError, ValueError) as exc:
                    print(f"[warn] AI content planning unavailable, fallback to minimal brief: {exc}")
                    brief = OnePageBrief(
                        title=str(args.topic),
                        kicker="",
                        summary_fragments=(TextFragment(source_text[:140]),),
                        law_rows=(),
                        right_kicker="EXECUTION VIEW",
                        right_title=str(args.topic),
                        process_steps=("信息梳理", "结构提炼", "页面生成", "人工复核"),
                        right_bullets=(BulletItem("说明：", "AI 不可用，已使用降级路径输出可编辑页面。"),),
                        strategy_title="后续建议：补充可用 AI 通道后再进行内容重写",
                        strategy_fragments=(TextFragment("当前为降级生成版本。"),),
                        footer="STRICTLY CONFIDENTIAL | 2026 SIE One-page Brief",
                        page_no="01",
                        required_terms=(str(args.topic),),
                        variant="auto",
                        layout_strategy="auto",
                    )
            else:
                brief = OnePageBrief(
                    title=str(args.topic),
                    kicker="",
                    summary_fragments=(TextFragment(source_text[:140]),),
                    law_rows=(),
                    right_kicker="EXECUTION VIEW",
                    right_title=str(args.topic),
                    process_steps=("信息梳理", "结构提炼", "页面生成", "人工复核"),
                    right_bullets=(BulletItem("说明：", "未启用 AI 内容规划，使用最小内容渲染。"),),
                    strategy_title="后续建议：启用 AI 内容规划以提升表达质量",
                    strategy_fragments=(TextFragment("当前为最小内容渲染版本。"),),
                    footer="STRICTLY CONFIDENTIAL | 2026 SIE One-page Brief",
                    page_no="01",
                    required_terms=(str(args.topic),),
                    variant="auto",
                    layout_strategy="auto",
                )
        else:
            brief = load_brief_from_json(Path(args.brief_json).resolve())
            if args.ai_content == "on":
                try:
                    brief = apply_ai_content_reframe(brief, model=args.ai_model, sections=3)
                except (OpenAIConfigurationError, OpenAIResponsesError, ValueError) as exc:
                    print(f"[warn] AI content reframe unavailable, keep source brief: {exc}")
        require_ai_strategy = args.ai_strategy == "on" and _openai_configured()
        if args.ai_strategy == "on" and not require_ai_strategy:
            print("[warn] AI strategy requested but OPENAI_API_KEY is missing; fallback to heuristic strategy.")
    else:
        if args.source_text_file:
            source_text = Path(args.source_text_file).resolve().read_text(encoding="utf-8")
            brief = OnePageBrief(
                title=str(args.topic),
                kicker="",
                summary_fragments=(TextFragment(source_text[:140]),),
                law_rows=(),
                right_kicker="EXECUTION VIEW",
                right_title=str(args.topic),
                process_steps=("信息梳理", "结构提炼", "页面生成", "人工复核"),
                right_bullets=(BulletItem("说明：", "已关闭 AI 规划，使用最小内容渲染。"),),
                strategy_title="后续建议：开启 host_ai 或 openai 模式提升质量",
                strategy_fragments=(TextFragment("当前为无AI模式。"),),
                footer="STRICTLY CONFIDENTIAL | 2026 SIE One-page Brief",
                page_no="01",
                required_terms=(str(args.topic),),
                variant="auto",
                layout_strategy="auto",
            )
        else:
            brief = load_brief_from_json(Path(args.brief_json).resolve())
        require_ai_strategy = False

    built, review_path, score_path, score = build_onepage_slide(
        brief,
        output_path=Path(args.output).resolve(),
        export_review=not args.skip_review,
        model=args.ai_model,
        require_ai_strategy=require_ai_strategy,
    )
    print(str(built))
    print(str(review_path) if review_path else "")
    print(str(score_path))
    print(f"score={score.total}, level={score.level}, variant={score.selected_variant}")


if __name__ == "__main__":
    main()
