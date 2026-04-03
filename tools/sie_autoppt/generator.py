import gc
import datetime
import re
import shutil
import subprocess
import sys
import textwrap
import time
import zipfile
from copy import deepcopy
from dataclasses import dataclass, field
from pathlib import Path
from xml.etree import ElementTree

try:
    import win32com.client  # type: ignore[attr-defined]
except ImportError:  # pragma: no cover
    win32com = None

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.util import Pt

from .config import (
    COLOR_ACTIVE,
    COLOR_INACTIVE,
    DEFAULT_MIN_TEMPLATE_SLIDES,
    DEFAULT_OUTPUT_DIR,
    FONT_NAME,
    IDX_BODY_TEMPLATE,
    IDX_DIRECTORY,
    IDX_THEME,
)
from .patterns import infer_pattern
from .reference_styles import build_reference_import_plan, populate_reference_body_pages


DEFAULT_TITLE = "\u9879\u76ee\u6982\u89c8\u4e0eUAT\u9636\u6bb5\u8ba1\u5212"
DEFAULT_SUBTITLE = "\u6839\u636e\u8f93\u5165 HTML \u81ea\u52a8\u5f52\u7eb3\u6d4b\u8bd5\u7ae0\u8282\u4e0e\u6838\u5fc3\u8981\u70b9\u3002"
DEFAULT_SCOPE_TITLE = "\u6d4b\u8bd5\u8303\u56f4\u4e0e\u5173\u952e\u573a\u666f"
DEFAULT_SCOPE_SUBTITLE = "\u6839\u636e\u8f93\u5165\u573a\u666f\u81ea\u52a8\u5f52\u7eb3\u6d4b\u8bd5\u8986\u76d6\u8303\u56f4\u3002"
DEFAULT_FOCUS_TITLE = "\u6d4b\u8bd5\u5173\u6ce8\u70b9\u4e0e\u9a8c\u6536\u6807\u51c6"
DEFAULT_FOCUS_SUBTITLE = "\u6839\u636e\u8f93\u5165\u5173\u6ce8\u70b9\u81ea\u52a8\u751f\u6210\u9a8c\u6536\u63d0\u793a\u3002"
DEFAULT_SUMMARY_TITLE = "\u603b\u7ed3\u4e0e\u884c\u52a8"
DEFAULT_EMPTY_OVERVIEW = "\u8865\u5145 phase-* \u5185\u5bb9\u540e\uff0c\u53ef\u81ea\u52a8\u751f\u6210\u9879\u76ee\u6982\u89c8\u9875\u3002"
DEFAULT_EMPTY_SCOPE = "\u8865\u5145 scenario \u5185\u5bb9\u540e\uff0c\u53ef\u81ea\u52a8\u751f\u6210\u6d4b\u8bd5\u8303\u56f4\u4e0e\u5173\u952e\u573a\u666f\u9875\u3002"
DEFAULT_EMPTY_FOCUS = "\u8865\u5145 note \u6216 footer \u5185\u5bb9\u540e\uff0c\u53ef\u81ea\u52a8\u751f\u6210\u6d4b\u8bd5\u5173\u6ce8\u70b9\u4e0e\u9a8c\u6536\u6807\u51c6\u9875\u3002"
THEME_TITLE_FONT_PT = 40
DIRECTORY_TITLE_FONT_PT = 24


@dataclass(frozen=True)
class InputPayload:
    title: str
    subtitle: str
    footer: str
    phases: list[dict[str, str]]
    scenarios: list[str]
    notes: list[str]


@dataclass(frozen=True)
class BodyPageSpec:
    page_key: str
    title: str
    subtitle: str
    bullets: list[str]
    pattern_id: str
    nav_title: str = ""
    reference_style_id: str | None = None
    payload: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class DeckSpec:
    cover_title: str
    body_pages: list[BodyPageSpec]


def strip_tags(s: str) -> str:
    return re.sub(r"<.*?>", "", s).strip()


def clean_heading_text(text: str) -> str:
    cleaned = strip_tags(text)
    cleaned = re.sub(r"^[^\w\u4e00-\u9fff]+", "", cleaned)
    return cleaned.strip()


def extract_single(html: str, cls: str) -> str:
    match = re.search(rf'<div class="{cls}">(.*?)</div>', html, flags=re.S)
    return strip_tags(match.group(1)) if match else ""


def extract_list(html: str, cls: str) -> list[str]:
    return [strip_tags(item) for item in re.findall(rf'<div class="{cls}">(.*?)</div>', html, flags=re.S)]


def extract_first_tag_text(html: str, tag: str) -> str:
    match = re.search(rf"<{tag}[^>]*>(.*?)</{tag}>", html, flags=re.S)
    return strip_tags(match.group(1)) if match else ""


def extract_tag_with_class(html: str, tag: str, class_name: str) -> str:
    match = re.search(rf'<{tag}[^>]*class="[^"]*\b{re.escape(class_name)}\b[^"]*"[^>]*>(.*?)</{tag}>', html, flags=re.S)
    return strip_tags(match.group(1)) if match else ""


def extract_tag_inside_block(html: str, block_class_pattern: str, tag: str) -> str:
    match = re.search(
        rf'<div class="{block_class_pattern}">.*?<{tag}[^>]*>(.*?)</{tag}>',
        html,
        flags=re.S,
    )
    return strip_tags(match.group(1)) if match else ""


def extract_list_items_from_block(html: str, class_pattern: str) -> list[str]:
    match = re.search(
        rf'<div class="{class_pattern}">.*?<ul>(.*?)</ul>',
        html,
        flags=re.S,
    )
    if not match:
        return []
    return [strip_tags(item) for item in re.findall(r"<li>(.*?)</li>", match.group(1), flags=re.S)]


def extract_steps(html: str) -> list[tuple[str, str]]:
    return [
        (clean_heading_text(title), strip_tags(desc))
        for title, desc in re.findall(
            r'<div class="step">\s*<div class="step-number">.*?</div>\s*<h3>(.*?)</h3>\s*<p>(.*?)</p>\s*</div>',
            html,
            flags=re.S,
        )
    ]


def extract_phases(html: str) -> list[dict[str, str]]:
    phase_keys = ("phase-time", "phase-name", "phase-code", "phase-func", "phase-owner")
    values = {key: extract_list(html, key) for key in phase_keys}
    phase_count = max((len(items) for items in values.values()), default=0)
    phases = []
    for index in range(phase_count):
        phase = {
            "time": values["phase-time"][index] if index < len(values["phase-time"]) else "",
            "name": values["phase-name"][index] if index < len(values["phase-name"]) else "",
            "code": values["phase-code"][index] if index < len(values["phase-code"]) else "",
            "func": values["phase-func"][index] if index < len(values["phase-func"]) else "",
            "owner": values["phase-owner"][index] if index < len(values["phase-owner"]) else "",
        }
        if any(phase.values()):
            phases.append(phase)
    return phases


def parse_html_payload(html: str) -> InputPayload:
    return InputPayload(
        title=extract_single(html, "title"),
        subtitle=extract_single(html, "subtitle"),
        footer=extract_single(html, "footer"),
        phases=extract_phases(html),
        scenarios=extract_list(html, "scenario"),
        notes=extract_list(html, "note"),
    )


def validate_payload(payload: InputPayload):
    has_meaningful_content = any(
        [
            payload.title,
            payload.subtitle,
            payload.footer,
            payload.phases,
            payload.scenarios,
            payload.notes,
        ]
    )
    if not has_meaningful_content:
        raise ValueError(
            "\u8f93\u5165 HTML \u672a\u8bc6\u522b\u5230\u53ef\u7528\u5185\u5bb9\u3002\u8bf7\u81f3\u5c11\u63d0\u4f9b title\u3001subtitle\u3001phase-*\u3001scenario\u3001note\u3001footer \u4e2d\u7684\u4e00\u90e8\u5206\u3002"
        )

    if not payload.phases and not payload.scenarios and not payload.notes:
        raise ValueError(
            "\u8f93\u5165 HTML \u7f3a\u5c11\u6b63\u6587\u5185\u5bb9\u3002\u8bf7\u81f3\u5c11\u8865\u5145\u4e00\u7ec4 phase-*\u3001scenario \u6216 note\uff0c\u624d\u80fd\u751f\u6210\u6709\u610f\u4e49\u7684\u6b63\u6587\u9875\u3002"
        )


def format_phase_summary(phase: dict[str, str]) -> str:
    prefix = phase["name"]
    if phase["time"]:
        prefix = f"{prefix}\uff08{phase['time']}\uff09" if prefix else phase["time"]
    detail = phase["func"] or phase["code"] or phase["owner"]
    return f"{prefix}\uff1a{detail}".strip("\uff1a")


def build_overview_bullets(payload: InputPayload) -> list[str]:
    bullets = [format_phase_summary(phase) for phase in payload.phases[:4] if format_phase_summary(phase)]
    if bullets:
        return bullets
    fallbacks = [item for item in (payload.subtitle, payload.footer) if item][:4]
    return fallbacks or [DEFAULT_EMPTY_OVERVIEW]


def build_scope_bullets(payload: InputPayload) -> list[str]:
    bullets = payload.scenarios[:4]
    if bullets:
        return bullets
    phase_names = [phase["name"] for phase in payload.phases if phase["name"]][:4]
    return phase_names or [DEFAULT_EMPTY_SCOPE]


def build_focus_bullets(payload: InputPayload) -> list[str]:
    bullets = payload.notes[:4]
    if payload.footer and payload.footer not in bullets:
        bullets.append(payload.footer)
    bullets = bullets[:4]
    return bullets or [DEFAULT_EMPTY_FOCUS]


def split_title_detail(text: str) -> tuple[str, str]:
    normalized = re.sub(r"\s+", " ", text).strip()
    for sep in ("：", ":"):
        if sep in normalized:
            title, detail = normalized.split(sep, 1)
            return title.strip(), detail.strip()
    return normalized, normalized


def compact_text(text: str, max_chars: int) -> str:
    compact = re.sub(r"\s+", " ", text).strip()
    if len(compact) <= max_chars:
        return compact
    return compact[: max_chars - 1].rstrip(" ,;，；。") + "…"


def concise_text(text: str, max_chars: int) -> str:
    parts = [part.strip() for part in re.split(r"[。；;，,]", re.sub(r"\s+", " ", text)) if part.strip()]
    if not parts:
        return compact_text(text, max_chars)
    candidate = parts[0]
    if len(parts) > 1 and len(candidate) + len(parts[1]) + 1 <= max_chars:
        candidate = f"{candidate}，{parts[1]}"
    return compact_text(candidate, max_chars)


def short_stage_label(text: str, max_chars: int = 8) -> str:
    compact = re.sub(r"\s+", "", text)
    compact = re.sub(r"\(.*?\)", "", compact)
    compact = re.sub(r"（.*?）", "", compact)
    compact = compact.replace("最佳实践", "").replace("工业化流水线", "流水线")
    if len(compact) <= max_chars:
        return compact
    return compact[:max_chars]


def derive_comparison_cards(raw_items: list[str], fallback_title: str, synthetic_tail: tuple[str, str]) -> list[dict[str, str]]:
    cards = []
    for item in raw_items:
        title, detail = split_title_detail(item)
        cards.append(
            {
                "title": compact_text(title or fallback_title, 14),
                "detail": concise_text(detail or title, 34),
            }
        )
    while len(cards) < 3:
        cards.append(
            {
                "title": fallback_title,
                "detail": concise_text(fallback_title, 34),
            }
        )
    cards = cards[:3]
    cards.append({"title": compact_text(synthetic_tail[0], 14), "detail": concise_text(synthetic_tail[1], 34)})
    return cards


def build_principle_items(success_bullets: list[str], steps: list[tuple[str, str]], conclusion: str) -> list[dict[str, str]]:
    items = []
    for item in success_bullets[:3]:
        title, detail = split_title_detail(item)
        items.append({"title": compact_text(title, 14), "detail": concise_text(detail, 28)})
    for title, detail in steps[:4]:
        items.append({"title": compact_text(short_stage_label(title, 10), 14), "detail": concise_text(detail, 28)})
    while len(items) < 7:
        items.append({"title": "协同交付", "detail": concise_text(conclusion or "保持模板骨架稳定，给 AI 留出创作空间。", 28)})
    return items[:7]


def build_pipeline_payload(steps: list[tuple[str, str]], conclusion: str, subtitle: str) -> dict[str, object]:
    default_stages = [
        ("阶段一\n业务抽象", ["梳理业务逻辑", "提炼关键信息", "统一输入结构", "输出标准数据", "明确渲染边界"]),
        ("阶段二\n组件沉淀", ["抽取复用组件", "沉淀原子函数", "约束版式规则", "绑定模板元素", "控制样式参数"]),
        ("阶段三\n自动渲染", ["批量生成页面", "写入目录导航", "完成基础 QA"]),
        ("阶段四\n人工抛光", ["分组与对齐", "视觉微调", "检查遮挡溢出", "补充动画过渡", "形成交付底稿"]),
        ("阶段五\n价值兑现", ["沉淀最佳实践", "回灌模板库", "效率与质量兼得", "形成稳定交付闭环"]),
    ]
    stage_headers = []
    stage_tasks = []
    for index, (title, detail) in enumerate(steps[:4], start=1):
        stage_headers.append(f"阶段{index}\n{short_stage_label(title)}")
        sentence_parts = [part.strip() for part in re.split(r"[。；;，,]", detail) if part.strip()]
        tasks = [compact_text(part, 14) for part in sentence_parts[:5]]
        while len(tasks) < len(default_stages[index - 1][1]):
            tasks.append(default_stages[index - 1][1][len(tasks)])
        stage_tasks.append(tasks[: len(default_stages[index - 1][1])])
    while len(stage_headers) < 4:
        title, tasks = default_stages[len(stage_headers)]
        stage_headers.append(title)
        stage_tasks.append(tasks)
    stage_headers.append("阶段五\n价值兑现")
    stage_tasks.append(default_stages[4][1])

    stages = []
    for header, tasks in zip(stage_headers[:5], stage_tasks[:5]):
        stages.append({"header": header, "tasks": tasks})

    return {
        "intro": conclusion or subtitle,
        "stages": stages,
        "legend": ["AI", "Python", "模板", "设计"],
    }


def build_card_analysis_page_specs(html: str, chapters: int) -> DeckSpec | None:
    if "comparison-grid" not in html or "pipeline-section" not in html:
        return None

    cover_title = extract_first_tag_text(html, "h1")
    subtitle = extract_tag_with_class(html, "p", "subtitle")
    danger_title = clean_heading_text(extract_tag_inside_block(html, "card card-danger", "h2"))
    danger_bullets = extract_list_items_from_block(html, "card card-danger")
    success_title = clean_heading_text(extract_tag_inside_block(html, "card card-success", "h2"))
    success_bullets = extract_list_items_from_block(html, "card card-success")
    pipeline_title = clean_heading_text(extract_tag_inside_block(html, "pipeline-section", "h2"))
    conclusion = extract_tag_with_class(html, "div", "conclusion")
    steps = extract_steps(html)

    if not any([cover_title, subtitle, danger_bullets, success_bullets, steps, conclusion]):
        return None

    danger_cards = derive_comparison_cards(
        danger_bullets,
        fallback_title="视觉风险",
        synthetic_tail=("调试成本放大", "长链路对话会放大排错与回归成本。"),
    )
    success_cards = derive_comparison_cards(
        success_bullets,
        fallback_title="工程化解法",
        synthetic_tail=("保留创作空间", conclusion or "固定骨架，让 AI 在内容与表达上创造增量价值。"),
    )
    principle_items = build_principle_items(success_bullets, steps, conclusion)
    comparison_payload = {
        "headline": subtitle or "先识别能力边界，再设计工程化交付路径。",
        "left_label": "● 一键生成式交付",
        "right_label": "● 工程化协同交付",
        "left_cards": danger_cards,
        "right_cards": success_cards,
        "center_kicker": "ENGINEERING COPILOT",
        "center_title": "结构化内容交付中枢",
        "center_subtitle": "内容引擎 · 模块化代码助手 · 人工视觉抛光",
        "center_top_label": "协同原则层",
        "center_section_title": "人机协同 (Human in the Loop)",
        "center_row1_left": "结构化输入",
        "center_row1_right": "模板化渲染",
        "center_row2_left": "视觉 QA",
        "center_row2_right": "人工微调",
        "center_divider": "♦ 先守住骨架，再释放 AI 创作空间 ♦",
        "center_bottom_label": "交付结果层",
        "center_bottom_title": "高质量输出 (Deliverable)",
        "center_bottom_left": "稳定复用",
        "center_bottom_right": "风格一致",
        "center_bottom_footer": "效率与质量兼得",
        "bottom_left_caption": "识别边界",
        "bottom_right_caption": "交付升级",
    }

    page_specs = [
        BodyPageSpec(
            page_key="comparison_upgrade",
            title="\u80fd\u529b\u8fb9\u754c\u4e0e\u5de5\u7a0b\u5316\u89e3\u6cd5",
            subtitle=subtitle or DEFAULT_SUBTITLE,
            bullets=(danger_bullets[:3] + success_bullets[:3]) or [DEFAULT_EMPTY_OVERVIEW],
            pattern_id="comparison_upgrade",
            nav_title=shorten_for_nav("\u80fd\u529b\u8fb9\u754c\u5bf9\u6bd4"),
            reference_style_id="comparison_upgrade",
            payload=comparison_payload,
        ),
        BodyPageSpec(
            page_key="practice_principles",
            title=success_title or "\u5de5\u7a0b\u5316\u5b9e\u8df5\u539f\u5219",
            subtitle=conclusion or DEFAULT_SCOPE_SUBTITLE,
            bullets=[item["title"] for item in principle_items],
            pattern_id="capability_ring",
            nav_title=shorten_for_nav("\u5b9e\u8df5\u539f\u5219"),
            reference_style_id="capability_ring",
            payload={"items": principle_items},
        ),
        BodyPageSpec(
            page_key="delivery_pipeline",
            title=pipeline_title or "\u5de5\u4e1a\u5316\u6d41\u6c34\u7ebf\u5b9e\u65bd\u8def\u5f84",
            subtitle=conclusion or DEFAULT_FOCUS_SUBTITLE,
            bullets=[f"{step_title}\uff1a{step_desc}" for step_title, step_desc in steps[:4]] or [DEFAULT_EMPTY_FOCUS],
            pattern_id="five_phase_path",
            nav_title=shorten_for_nav("\u5b9e\u65bd\u8def\u5f84"),
            reference_style_id="five_phase_path",
            payload=build_pipeline_payload(steps, conclusion, subtitle),
        ),
    ]
    return DeckSpec(
        cover_title=cover_title or DEFAULT_TITLE,
        body_pages=page_specs[: max(1, min(chapters, 3))],
    )


def build_page_specs(payload: InputPayload, chapters: int) -> DeckSpec:
    requested_chapters = max(1, min(chapters, 3))
    page_specs = [
        BodyPageSpec(
            page_key="overview",
            title=payload.title or DEFAULT_TITLE,
            subtitle=payload.subtitle or DEFAULT_SUBTITLE,
            bullets=build_overview_bullets(payload),
            pattern_id="general_business",
            nav_title=shorten_for_nav(payload.title or DEFAULT_TITLE),
        ),
        BodyPageSpec(
            page_key="scope",
            title=DEFAULT_SCOPE_TITLE,
            subtitle=DEFAULT_SCOPE_SUBTITLE,
            bullets=build_scope_bullets(payload),
            pattern_id="general_business",
            nav_title=shorten_for_nav(DEFAULT_SCOPE_TITLE),
        ),
        BodyPageSpec(
            page_key="focus",
            title=DEFAULT_FOCUS_TITLE,
            subtitle=payload.footer or DEFAULT_FOCUS_SUBTITLE,
            bullets=build_focus_bullets(payload),
            pattern_id="general_business",
            nav_title=shorten_for_nav(DEFAULT_FOCUS_TITLE),
        ),
    ][:requested_chapters]

    return DeckSpec(
        cover_title=payload.title or DEFAULT_TITLE,
        body_pages=[
            BodyPageSpec(
                page_key=page.page_key,
                title=page.title,
                subtitle=page.subtitle,
                bullets=page.bullets,
                pattern_id=infer_pattern(page.title, page.bullets),
                nav_title=page.nav_title or shorten_for_nav(page.title),
            )
            for page in page_specs
        ],
    )


def build_directory_lines(body_pages: list[BodyPageSpec]) -> list[str]:
    lines = [page.nav_title or page.title for page in body_pages[:5]]
    for fallback in (DEFAULT_SUMMARY_TITLE, "Q&A"):
        if len(lines) >= 5:
            break
        lines.append(fallback)
    while len(lines) < 5:
        lines.append(f"\u7ae0\u8282{len(lines) + 1}")
    return lines[:5]


def set_shape_text(shape, text: str, size_pt: int = 18, bold: bool = False, align=PP_ALIGN.LEFT):
    if not getattr(shape, "has_text_frame", False):
        return
    text_frame = shape.text_frame
    text_frame.clear()
    paragraph = text_frame.paragraphs[0]
    paragraph.alignment = align
    run = paragraph.add_run()
    run.text = text
    run.font.name = FONT_NAME
    run.font.size = Pt(size_pt)
    run.font.bold = bold


def normalize_text_for_box(text: str, max_chars: int = 44) -> str:
    compact = re.sub(r"\s+", " ", text).strip()
    lines = textwrap.wrap(compact, width=max_chars)
    return "\n".join(lines[:4])


def choose_title_font_size(text: str, default: int = 24) -> int:
    n = len(text)
    if n > 28:
        return 16
    if n > 22:
        return 18
    if n > 16:
        return 20
    return default


def choose_nav_font_size(text: str) -> int:
    return DIRECTORY_TITLE_FONT_PT


def shorten_for_nav(text: str, max_chars: int = 10) -> str:
    compact = re.sub(r"\s+", "", text)
    compact = re.sub(r"（.*?）", "", compact)
    compact = compact.replace("(最佳实践)", "").replace("(V3.0战略视图)", "")
    compact = compact.replace("：", "").replace("?", "").replace("？", "")
    if len(compact) <= max_chars:
        return compact
    if "与" in compact:
        candidate = "与".join(compact.split("与")[:2])
        if len(candidate) <= max_chars:
            return candidate
    return compact[:max_chars]


def choose_font_size_by_length(text: str, base: int = 13) -> int:
    n = len(text)
    if n > 120:
        return max(10, base - 3)
    if n > 90:
        return max(11, base - 2)
    if n > 70:
        return max(12, base - 1)
    return base


def replace_text_preserve_runs(shape, text: str, force_color=None, font_size_pt: int | None = None):
    if not getattr(shape, "has_text_frame", False):
        return
    text_frame = shape.text_frame
    text_frame.word_wrap = True
    if not text_frame.paragraphs:
        return
    paragraph = text_frame.paragraphs[0]
    if paragraph.runs:
        paragraph.runs[0].text = text
        paragraph.runs[0].font.name = FONT_NAME
        if font_size_pt is not None:
            paragraph.runs[0].font.size = Pt(font_size_pt)
        if force_color is not None:
            paragraph.runs[0].font.color.rgb = RGBColor(*force_color)
        for run in paragraph.runs[1:]:
            run.text = ""
    else:
        run = paragraph.add_run()
        run.text = text
        run.font.name = FONT_NAME
        if font_size_pt is not None:
            run.font.size = Pt(font_size_pt)
        if force_color is not None:
            run.font.color.rgb = RGBColor(*force_color)
    for extra_paragraph in text_frame.paragraphs[1:]:
        for run in extra_paragraph.runs:
            run.text = ""


def set_shape_text_with_color(shape, text: str, color, size_pt=None, bold=None):
    if not getattr(shape, "has_text_frame", False):
        return
    text_frame = shape.text_frame
    text_frame.text = text
    text_frame.word_wrap = True
    for paragraph in text_frame.paragraphs:
        paragraph.alignment = PP_ALIGN.LEFT
        for run in paragraph.runs:
            run.font.name = FONT_NAME
            run.font.color.rgb = RGBColor(*color)
            if size_pt is not None:
                run.font.size = Pt(size_pt)
            if bold is not None:
                run.font.bold = bold


def pick_text_shapes(slide):
    return [shape for shape in slide.shapes if getattr(shape, "has_text_frame", False)]


def clone_slide_after(prs: Presentation, source_idx: int, insert_after_idx: int, keep_rel_ids: bool = True):
    source = prs.slides[source_idx]
    new_slide = prs.slides.add_slide(source.slide_layout)
    for shape in list(new_slide.shapes):
        element = shape._element
        element.getparent().remove(element)
    for shape in source.shapes:
        new_element = deepcopy(shape.element)
        new_slide.shapes._spTree.insert_element_before(new_element, "p:extLst")
    for rel in source.part.rels.values():
        if "notesSlide" in rel.reltype:
            continue
        try:
            if keep_rel_ids:
                new_slide.part.rels.add_relationship(rel.reltype, rel._target, rel.rId)
            else:
                new_slide.part.rels.add_relationship(rel.reltype, rel._target)
        except Exception:
            pass
    slide_id_list = prs.slides._sldIdLst
    new_id = slide_id_list[-1]
    del slide_id_list[-1]
    slide_id_list.insert(insert_after_idx + 1, new_id)
    return prs.slides[insert_after_idx + 1]


def ensure_last_slide_is_thanks(prs: Presentation, thanks_slide_id: int):
    slide_id_list = prs.slides._sldIdLst
    target = None
    for item in slide_id_list:
        if int(item.id) == int(thanks_slide_id):
            target = item
            break
    if target is None:
        return
    slide_id_list.remove(target)
    slide_id_list.append(target)


def fill_directory_slide(slide, chapter_lines, active_chapter_index: int):
    texts = sorted(pick_text_shapes(slide), key=lambda shape: (shape.top, shape.left))
    title_boxes = [shape for shape in texts if shape.width > 3000000 and 1800000 < shape.top < 5200000]
    title_boxes = sorted(title_boxes, key=lambda shape: (shape.top, shape.left))
    safe_active_index = max(0, min(active_chapter_index, len(chapter_lines) - 1))
    for i, shape in enumerate(title_boxes[: len(chapter_lines)]):
        color = COLOR_ACTIVE if i == safe_active_index else COLOR_INACTIVE
        replace_text_preserve_runs(
            shape,
            chapter_lines[i],
            force_color=color,
            font_size_pt=DIRECTORY_TITLE_FONT_PT,
        )


def repair_directory_slides_with_com(pptx_path: Path, source_idx: int, target_indices: list[int]) -> bool:
    if win32com is None:
        return False
    helper = Path(__file__).resolve().parents[1] / "repair_directory_slides.py"
    command = [
        sys.executable,
        str(helper),
        str(pptx_path.resolve()),
        "--source-idx",
        str(source_idx),
        "--targets",
        *[str(target) for target in target_indices],
    ]
    for _ in range(5):
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode == 0:
            return True
        time.sleep(1.0)
    return False


def apply_reference_body_slides_with_com(pptx_path: Path, reference_body_path: Path | None, body_pages: list[BodyPageSpec]) -> bool:
    import_plan = build_reference_import_plan(body_pages)
    if not import_plan:
        return True
    if win32com is None or reference_body_path is None or not reference_body_path.exists():
        return False
    helper = Path(__file__).resolve().parents[1] / "apply_reference_body_slides.py"
    command = [
        sys.executable,
        str(helper),
        str(pptx_path.resolve()),
        str(reference_body_path.resolve()),
        "--mapping",
        *[f"{target}={source}" for target, source in import_plan],
    ]
    for _ in range(5):
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode == 0:
            return True
        time.sleep(1.0)
    return False


def _slide_image_targets(pptx_path: Path, slide_no: int) -> set[str]:
    rel_path = f"ppt/slides/_rels/slide{slide_no}.xml.rels"
    targets: set[str] = set()
    with zipfile.ZipFile(pptx_path) as package:
        try:
            root = ElementTree.fromstring(package.read(rel_path))
        except KeyError:
            return targets
    for rel in root:
        rel_type = rel.attrib.get("Type", "")
        if rel_type.endswith("/image"):
            target = rel.attrib.get("Target", "")
            if target:
                targets.add(target)
    return targets


def directory_assets_preserved(pptx_path: Path, source_idx: int, target_indices: list[int]) -> bool:
    source_targets = _slide_image_targets(pptx_path, source_idx)
    if not source_targets:
        return True
    for slide_no in target_indices:
        target_assets = _slide_image_targets(pptx_path, slide_no)
        if not source_targets.issubset(target_assets):
            return False
    return True


def _render_cards_2x2(slide, bullets: list[str]):
    x0, y0 = 576088, 1450000
    card_w, card_h = 5000000, 1200000
    gap_x, gap_y = 350000, 260000
    for i, text in enumerate(bullets[:4]):
        row, col = divmod(i, 2)
        left = x0 + col * (card_w + gap_x)
        top = y0 + row * (card_h + gap_y)
        card = slide.shapes.add_shape(1, left, top, card_w, card_h)
        card.fill.solid()
        card.fill.fore_color.rgb = RGBColor(248, 250, 252)
        card.line.color.rgb = RGBColor(220, 223, 230)
        textbox = slide.shapes.add_textbox(left + 180000, top + 180000, card_w - 360000, card_h - 360000)
        safe_text = normalize_text_for_box(text, 38)
        font_size = choose_font_size_by_length(safe_text, 13)
        set_shape_text(textbox, safe_text, size_pt=font_size, bold=False)


def _render_process_flow(slide, bullets: list[str]):
    start_x, y = 620000, 2050000
    step_w, step_h, gap = 2500000, 1200000, 220000
    for i, text in enumerate(bullets[:4]):
        left = start_x + i * (step_w + gap)
        box = slide.shapes.add_shape(1, left, y, step_w, step_h)
        box.fill.solid()
        box.fill.fore_color.rgb = RGBColor(246, 249, 252)
        box.line.color.rgb = RGBColor(210, 218, 226)
        number = slide.shapes.add_textbox(left + 100000, y + 90000, 260000, 220000)
        set_shape_text(number, f"{i + 1:02d}", size_pt=12, bold=True)
        textbox = slide.shapes.add_textbox(left + 100000, y + 360000, step_w - 200000, step_h - 460000)
        safe_text = normalize_text_for_box(text, 24)
        set_shape_text(textbox, safe_text, size_pt=11, bold=False)


def _render_architecture_two_column(slide, bullets: list[str]):
    left_x, right_x = 700000, 6200000
    y0, row_h = 1850000, 900000
    for i, text in enumerate(bullets[:4]):
        y = y0 + i * row_h
        left_box = slide.shapes.add_shape(1, left_x, y, 5000000, 680000)
        left_box.fill.solid()
        left_box.fill.fore_color.rgb = RGBColor(245, 247, 250)
        left_box.line.color.rgb = RGBColor(215, 222, 230)
        left_text = slide.shapes.add_textbox(left_x + 160000, y + 180000, 4680000, 360000)
        set_shape_text(left_text, f"\u6a21\u5757{i + 1}", size_pt=12, bold=True)

        right_box = slide.shapes.add_shape(1, right_x, y, 5000000, 680000)
        right_box.fill.solid()
        right_box.fill.fore_color.rgb = RGBColor(250, 252, 255)
        right_box.line.color.rgb = RGBColor(220, 226, 233)
        right_text = slide.shapes.add_textbox(right_x + 160000, y + 140000, 4680000, 420000)
        safe_text = normalize_text_for_box(text, 34)
        set_shape_text(right_text, safe_text, size_pt=11, bold=False)


PATTERN_RENDERERS = {
    "process_flow": _render_process_flow,
    "solution_architecture": _render_architecture_two_column,
    "general_business": _render_cards_2x2,
}


def _clear_body_render_area(slide, protected_shapes=None):
    protected_shapes = list(protected_shapes or [])
    removable = []
    for shape in slide.shapes:
        if any(shape is protected for protected in protected_shapes):
            continue
        if 1200000 < shape.top < 6200000:
            removable.append(shape)
    for shape in removable:
        element = shape._element
        element.getparent().remove(element)


def fill_body_slide(slide, page: BodyPageSpec):
    texts = sorted(pick_text_shapes(slide), key=lambda shape: (shape.top, shape.left))
    title_candidates = [shape for shape in texts if shape.top < 300000 and shape.width > 7000000]
    if title_candidates:
        replace_text_preserve_runs(
            title_candidates[0],
            page.title,
            force_color=COLOR_ACTIVE,
            font_size_pt=choose_title_font_size(page.title),
        )
    else:
        textbox = slide.shapes.add_textbox(166370, 36830, 10034086, 480060)
        set_shape_text_with_color(
            textbox,
            page.title,
            COLOR_ACTIVE,
            size_pt=choose_title_font_size(page.title),
            bold=True,
        )

    subtitle_candidates = [
        shape
        for shape in texts
        if 300000 < shape.top < 1600000 and shape.width > 7000000 and shape not in title_candidates
    ]
    if subtitle_candidates:
        replace_text_preserve_runs(subtitle_candidates[0], page.subtitle)

    protected_shapes = title_candidates + subtitle_candidates[:1]
    _clear_body_render_area(slide, protected_shapes=protected_shapes)
    renderer = PATTERN_RENDERERS.get(page.pattern_id, _render_cards_2x2)
    renderer(slide, page.bullets)


def build_output_path(output_dir: Path, output_prefix: str) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    safe_prefix = re.sub(r'[<>:"/\\\\|?*]+', "_", output_prefix).strip(" ._") or "SIE_AutoPPT"
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
    return output_dir / f"{safe_prefix}_{timestamp}.pptx"


def apply_theme_title(prs: Presentation, title: str):
    theme_texts = pick_text_shapes(prs.slides[IDX_THEME])
    title_candidates = [shape for shape in theme_texts if 1500000 < shape.top < 2300000 and shape.width > 5000000]
    if title_candidates:
        main_title = max(title_candidates, key=lambda shape: shape.width)
        set_shape_text_with_color(main_title, title, COLOR_ACTIVE, size_pt=THEME_TITLE_FONT_PT)


def render_body_pages(prs: Presentation, body_pages: list[BodyPageSpec], chapter_lines: list[str], active_start: int):
    directory_slides = [prs.slides[IDX_DIRECTORY]]
    body_slides = [prs.slides[IDX_BODY_TEMPLATE]]
    insert_after = IDX_BODY_TEMPLATE
    for _ in body_pages[1:]:
        new_directory = clone_slide_after(prs, IDX_DIRECTORY, insert_after, keep_rel_ids=True)
        directory_slides.append(new_directory)
        insert_after += 1

        new_body = clone_slide_after(prs, IDX_BODY_TEMPLATE, insert_after, keep_rel_ids=False)
        body_slides.append(new_body)
        insert_after += 1

    for chapter_idx, directory_slide in enumerate(directory_slides):
        fill_directory_slide(directory_slide, chapter_lines, active_start + chapter_idx)
    for page, body_slide in zip(body_pages, body_slides):
        if page.reference_style_id:
            continue
        fill_body_slide(body_slide, page)


def refresh_directory_clones(pptx_path: Path, chapter_lines: list[str], active_start: int, body_page_count: int):
    targets = [IDX_DIRECTORY + 1 + i * 2 for i in range(1, body_page_count)]
    if not targets:
        return True

    source_idx = IDX_DIRECTORY + 1
    for _ in range(3):
        if not repair_directory_slides_with_com(pptx_path, source_idx=source_idx, target_indices=targets):
            continue

        prs_reloaded = Presentation(str(pptx_path))
        fill_directory_slide(prs_reloaded.slides[IDX_DIRECTORY], chapter_lines, active_start)
        for offset, directory_slide_no in enumerate(targets, start=1):
            slide_index = directory_slide_no - 1
            if slide_index < len(prs_reloaded.slides):
                fill_directory_slide(prs_reloaded.slides[slide_index], chapter_lines, active_start + offset)
        prs_reloaded.save(str(pptx_path))
        prs_reloaded = None
        gc.collect()

        if directory_assets_preserved(pptx_path, source_idx=source_idx, target_indices=targets):
            return True
        time.sleep(1.0)

    return False


def generate_ppt(
    template_path: Path,
    html_path: Path,
    reference_body_path: Path | None,
    output_prefix: str,
    chapters: int,
    active_start: int,
    output_dir: Path | None = None,
):
    if not template_path.exists():
        raise FileNotFoundError(f"Template not found: {template_path}")
    if not html_path.exists():
        raise FileNotFoundError(f"HTML not found: {html_path}")

    html = html_path.read_text(encoding="utf-8")
    specialized_deck = build_card_analysis_page_specs(html, chapters)
    if specialized_deck:
        deck = specialized_deck
    else:
        payload = parse_html_payload(html)
        validate_payload(payload)
        deck = build_page_specs(payload, chapters)
    body_pages = deck.body_pages
    chapter_lines = build_directory_lines(body_pages)
    pattern_ids = [page.pattern_id for page in body_pages]

    final_output_dir = output_dir or DEFAULT_OUTPUT_DIR
    out = build_output_path(final_output_dir, output_prefix)
    shutil.copy2(template_path, out)

    prs = Presentation(str(out))
    if len(prs.slides) < DEFAULT_MIN_TEMPLATE_SLIDES:
        raise ValueError(
            f"\u6a21\u677f\u9875\u6570\u4e0d\u8db3\uff0c\u81f3\u5c11\u9700\u8981 {DEFAULT_MIN_TEMPLATE_SLIDES} \u9875\uff0c\u5b9e\u9645\u4e3a {len(prs.slides)} \u9875\u3002"
        )

    apply_theme_title(prs, deck.cover_title)
    thanks_slide_id = int(prs.slides._sldIdLst[len(prs.slides) - 1].id)
    render_body_pages(prs, body_pages, chapter_lines, active_start)
    ensure_last_slide_is_thanks(prs, thanks_slide_id)
    prs.save(str(out))
    prs = None
    gc.collect()

    if not apply_reference_body_slides_with_com(out, reference_body_path, body_pages):
        raise RuntimeError("Reference body slide import failed: could not apply reference PPT styles.")
    if not refresh_directory_clones(out, chapter_lines, active_start, len(body_pages)):
        raise RuntimeError("Directory slide clone repair failed: template image assets were not preserved.")
    populate_reference_body_pages(out, body_pages)
    return out, pattern_ids, chapter_lines
