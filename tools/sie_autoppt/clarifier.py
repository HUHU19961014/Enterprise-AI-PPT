from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field, replace
from pathlib import Path
from typing import Any

from .config import DEFAULT_TEMPLATE, MAX_BODY_CHAPTERS, TEMPLATES_DIR
from .llm_openai import (
    OpenAIConfigurationError,
    OpenAIResponsesClient,
    OpenAIResponsesError,
    load_openai_responses_config,
)
from .prompting import render_prompt_template


DEFAULT_AUDIENCE_HINT = "管理层 + 业务负责人"
CLARIFIER_PROMPT_PATH = "prompts/system/clarifier.md"
DIMENSION_ORDER = ("topic", "purpose", "audience", "slides", "style", "template_theme", "core_content")
DIMENSION_LABELS = {
    "template_theme": "Template/Theme",
    "topic": "主题",
    "purpose": "用途",
    "audience": "受众",
    "slides": "页数",
    "style": "风格",
    "core_content": "核心内容",
}
DIMENSION_OPTIONS = {
    "topic": (),
    "purpose": ("工作汇报", "教学课件", "产品提案", "会议演讲"),
    "audience": ("公司领导", "客户", "同事", "学生", "通用"),
    "slides": ("3-5页", "10页左右", "20页以上"),
    "style": ("商务专业", "科技现代", "简约清晰", "活泼有趣"),
    "core_content": ("现状/问题/建议", "痛点/方案/价值", "进展/风险/下一步", "背景/目标/路径"),
}
DIMENSION_OPTION_DESCRIPTIONS = {
    "purpose": {
        "工作汇报": "强调进展、问题和决策建议，适合经营复盘或阶段汇报",
        "教学课件": "强调知识点结构和案例解释，适合培训或授课",
        "产品提案": "强调痛点、方案和收益，适合售前或对外沟通",
        "会议演讲": "强调观点表达和节奏，适合主题分享或发言",
    },
    "audience": {
        "公司领导": "结论先行，细节适中，突出关键决策信息",
        "客户": "强调价值、案例和差异化，减少内部术语",
        "同事": "可保留更多执行细节、分工和协同信息",
        "学生": "需要更多解释、示例和层层展开",
        "通用": "保持中性表达，适合未明确受众时的默认场景",
    },
    "slides": {
        "3-5页": "适合高层快报、过会材料或电梯汇报",
        "10页左右": "最常见的完整汇报长度，兼顾结论和支撑",
        "20页以上": "适合培训、详案或复杂方案说明",
    },
    "style": {
        "商务专业": "最稳妥，适合管理汇报和方案提报",
        "科技现代": "适合技术、产品、数字化主题",
        "简约清晰": "适合说明、教学、方法论表达",
        "活泼有趣": "适合培训、分享、传播型内容",
    },
    "core_content": {
        "现状/问题/建议": "适合经营复盘、管理汇报、问题诊断",
        "痛点/方案/价值": "适合客户提案、售前方案、价值说明",
        "进展/风险/下一步": "适合项目周报、阶段汇报、推进沟通",
        "背景/目标/路径": "适合主题分享、转型方案、方法论说明",
    },
}
SKIP_KEYWORDS = (
    "直接生成",
    "直接开始",
    "跳过引导",
    "跳过澄清",
    "先生成",
    "skip",
)
GENERIC_REQUEST_PATTERNS = (
    r"^帮我(?:做|生成|写|整理)?(?:一份|一个|个)?ppt$",
    r"^做(?:一份|一个|个)?ppt$",
    r"^生成(?:一份|一个|个)?ppt$",
    r"^ppt$",
    r"^presentation$",
)
PURPOSE_PATTERNS = (
    (r"(工作汇报|业绩汇报|经营汇报|季度汇报|年度汇报|汇报)", "工作汇报"),
    (r"(教学课件|培训课件|培训材料|课程讲义|教学)", "教学课件"),
    (r"(产品提案|产品方案|提案|解决方案|方案汇报|招投标)", "产品提案"),
    (r"(会议演讲|主题演讲|分享会|路演|演讲)", "会议演讲"),
)
AUDIENCE_PATTERNS = (
    (r"(公司领导|管理层|老板|高层)", "公司领导"),
    (r"(客户|甲方|合作伙伴)", "客户"),
    (r"(同事|内部团队|项目组)", "同事"),
    (r"(学生|学员)", "学生"),
    (r"(通用|泛用|大众)", "通用"),
)
STYLE_PATTERNS = (
    (r"(商务专业|商务风|正式商务|高管汇报风)", "商务专业"),
    (r"(科技现代|科技风|未来感|科技感)", "科技现代"),
    (r"(简约清晰|极简|简洁|简约风)", "简约清晰"),
    (r"(活泼有趣|年轻化|轻松|趣味)", "活泼有趣"),
)
CONTENT_PATTERNS = (
    r"(?:核心内容|主要内容|重点|关键内容|内容重点)\s*(?:是|为|包括|围绕)?\s*[:：]?\s*(.+)$",
    r"(?:内容|包括|围绕|聚焦|重点讲|主要讲)\s*[:：]?\s*(.+)$",
)
DEFAULT_V2_THEME = "business_red"
V2_THEMES_DIR = Path(__file__).resolve().parent / "v2" / "themes"


def _available_v2_themes() -> tuple[str, ...]:
    if not V2_THEMES_DIR.exists():
        return (DEFAULT_V2_THEME,)
    names = sorted(path.stem for path in V2_THEMES_DIR.glob("*.json"))
    if DEFAULT_V2_THEME in names:
        names.remove(DEFAULT_V2_THEME)
        names.insert(0, DEFAULT_V2_THEME)
    elif not names:
        names = [DEFAULT_V2_THEME]
    return tuple(names)


def _available_template_names() -> tuple[str, ...]:
    names: list[str] = []
    if DEFAULT_TEMPLATE.exists():
        names.append(DEFAULT_TEMPLATE.stem)
    if TEMPLATES_DIR.exists():
        for path in sorted(TEMPLATES_DIR.glob("*/template.pptx")):
            names.append(path.parent.name)
    unique: list[str] = []
    seen: set[str] = set()
    for name in names:
        normalized = str(name).strip()
        if normalized and normalized not in seen:
            seen.add(normalized)
            unique.append(normalized)
    return tuple(unique)


def _normalize_template_name(value: str) -> str:
    normalized = _normalize_text(value).strip("\"'")
    if not normalized:
        return ""
    lowered = normalized.lower()
    if lowered.endswith(".pptx"):
        return Path(normalized).stem
    if lowered in {"default", "default template", "sietemplate", "sie template", "default_template"}:
        return DEFAULT_TEMPLATE.stem
    if lowered in {"默认模板", "默认", "sieppt", "sie模板"}:
        return DEFAULT_TEMPLATE.stem
    for name in _available_template_names():
        if lowered == name.lower():
            return name
    return normalized


def _extract_theme(text: str) -> str:
    normalized = _normalize_text(text)
    for theme_name in _available_v2_themes():
        if re.search(rf"(?<![A-Za-z0-9_]){re.escape(theme_name)}(?![A-Za-z0-9_])", normalized, flags=re.IGNORECASE):
            return theme_name
    return ""


def _extract_template(text: str) -> str:
    normalized = _normalize_text(text)
    for template_name in _available_template_names():
        if re.search(rf"(?<![A-Za-z0-9_]){re.escape(template_name)}(?![A-Za-z0-9_])", normalized, flags=re.IGNORECASE):
            return template_name

    if "模板" not in normalized and ".pptx" not in normalized.lower():
        return ""

    explicit_path = re.search(r"([^\s]+\.pptx)", normalized, flags=re.IGNORECASE)
    if explicit_path:
        return _normalize_template_name(explicit_path.group(1))
    return _normalize_template_name(normalized)


def _template_theme_summary(requirements: "ClarifierRequirements") -> str:
    if requirements.theme:
        return f"theme:{requirements.theme}"
    if requirements.template:
        return f"template:{requirements.template}"
    return ""


@dataclass(frozen=True)
class ClarifierOption:
    key: str
    value: str
    description: str = ""
    recommended: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "value": self.value,
            "description": self.description,
            "recommended": self.recommended,
        }


@dataclass(frozen=True)
class ClarifierQuestion:
    dimension: str
    prompt: str
    options: tuple[ClarifierOption, ...] = ()
    allow_custom: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "dimension": self.dimension,
            "label": DIMENSION_LABELS.get(self.dimension, self.dimension),
            "prompt": self.prompt,
            "options": [option.to_dict() for option in self.options],
            "option_labels": [option.value for option in self.options],
            "allow_custom": self.allow_custom,
        }


@dataclass(frozen=True)
class ClarifierRequirements:
    topic: str = ""
    purpose: str = ""
    audience: str = ""
    style: str = ""
    template: str = ""
    theme: str = ""
    core_content: str = ""
    chapters: int | None = None
    min_slides: int | None = None
    max_slides: int | None = None
    slide_hint: str = ""
    raw_request: str = ""

    def slide_summary(self) -> str:
        if self.slide_hint:
            return self.slide_hint
        if self.chapters is not None:
            return f"{self.chapters}页"
        if self.min_slides is not None and self.max_slides is not None:
            return f"{self.min_slides}-{self.max_slides}页"
        if self.min_slides is not None:
            return f"{self.min_slides}页以上"
        return ""

    def known_dimensions(self) -> dict[str, str]:
        known: dict[str, str] = {}
        if self.topic and not _is_generic_topic(self.topic):
            known["topic"] = self.topic
        if self.purpose:
            known["purpose"] = self.purpose
        if self.audience:
            known["audience"] = self.audience
        slide_summary = self.slide_summary()
        if slide_summary:
            known["slides"] = slide_summary
        if self.style:
            known["style"] = self.style
        template_theme = _template_theme_summary(self)
        if template_theme:
            known["template_theme"] = template_theme
        if self.core_content:
            known["core_content"] = self.core_content
        return known

    def merge(self, other: "ClarifierRequirements") -> "ClarifierRequirements":
        return ClarifierRequirements(
            topic=other.topic or self.topic,
            purpose=other.purpose or self.purpose,
            audience=other.audience or self.audience,
            style=other.style or self.style,
            template=other.template or self.template,
            theme=other.theme or self.theme,
            core_content=other.core_content or self.core_content,
            chapters=other.chapters if other.chapters is not None else self.chapters,
            min_slides=other.min_slides if other.min_slides is not None else self.min_slides,
            max_slides=other.max_slides if other.max_slides is not None else self.max_slides,
            slide_hint=other.slide_hint or self.slide_hint,
            raw_request=other.raw_request or self.raw_request,
        )

    def summary_lines(self) -> list[str]:
        lines = []
        if self.theme:
            lines.append(f"Theme: {self.theme}")
        if self.template:
            lines.append(f"Template: {self.template}")
        if self.topic and not _is_generic_topic(self.topic):
            lines.append(f"主题：{self.topic}")
        for dimension, value in self.known_dimensions().items():
            if dimension in {"topic", "template_theme"}:
                continue
            lines.append(f"{DIMENSION_LABELS[dimension]}：{value}")
        return lines


@dataclass(frozen=True)
class ClarifierSession:
    requirements: ClarifierRequirements = field(default_factory=ClarifierRequirements)
    turn_count: int = 0
    pending_dimensions: tuple[str, ...] = ()
    asked_dimensions: tuple[str, ...] = ()
    skipped: bool = False
    status: str = "needs_clarification"
    history: tuple[dict[str, str], ...] = ()

    def to_json(self) -> str:
        payload = {
            "requirements": asdict(self.requirements),
            "turn_count": self.turn_count,
            "pending_dimensions": list(self.pending_dimensions),
            "asked_dimensions": list(self.asked_dimensions),
            "skipped": self.skipped,
            "status": self.status,
            "history": list(self.history),
        }
        return json.dumps(payload, ensure_ascii=False, indent=2)


@dataclass(frozen=True)
class ClarifierResult:
    session: ClarifierSession
    requirements: ClarifierRequirements
    status: str
    guide_mode: str
    missing_dimensions: tuple[str, ...]
    questions: tuple[ClarifierQuestion, ...]
    message: str
    topic: str
    audience: str
    brief: str
    chapters: int | None
    min_slides: int | None
    max_slides: int | None
    blocking: bool = False
    response_template: str = ""
    skipped: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "guide_mode": self.guide_mode,
            "blocking": self.blocking,
            "skipped": self.skipped,
            "message": self.message,
            "response_template": self.response_template,
            "topic": self.topic,
            "audience": self.audience,
            "brief": self.brief,
            "chapters": self.chapters,
            "min_slides": self.min_slides,
            "max_slides": self.max_slides,
            "missing_dimensions": list(self.missing_dimensions),
            "requirements": asdict(self.requirements),
            "questions": [question.to_dict() for question in self.questions],
            "session": json.loads(self.session.to_json()),
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)


def load_clarifier_session(payload: str) -> ClarifierSession:
    data = json.loads(payload)
    requirements = ClarifierRequirements(**data.get("requirements", {}))
    return ClarifierSession(
        requirements=requirements,
        turn_count=int(data.get("turn_count", 0)),
        pending_dimensions=tuple(data.get("pending_dimensions", ())),
        asked_dimensions=tuple(data.get("asked_dimensions", ())),
        skipped=bool(data.get("skipped", False)),
        status=str(data.get("status", "needs_clarification")),
        history=tuple(data.get("history", ())),
    )


def _normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _contains_skip_keyword(text: str) -> bool:
    lowered = text.lower()
    return any(keyword.lower() in lowered for keyword in SKIP_KEYWORDS)


def _extract_by_patterns(text: str, patterns: tuple[tuple[str, str], ...]) -> str:
    for pattern, normalized in patterns:
        if re.search(pattern, text, flags=re.IGNORECASE):
            return normalized
    return ""


def _extract_slide_preferences(text: str) -> tuple[int | None, int | None, int | None, str]:
    range_match = re.search(r"(\d+)\s*[-~到至]\s*(\d+)\s*页", text, flags=re.IGNORECASE)
    if range_match:
        min_slides = max(1, int(range_match.group(1)))
        max_slides = max(min_slides, min(int(range_match.group(2)), MAX_BODY_CHAPTERS))
        return None, min_slides, max_slides, f"{min_slides}-{max_slides}页"

    more_match = re.search(r"(\d+)\s*页\s*(?:以上|起)", text, flags=re.IGNORECASE)
    if more_match:
        lower_bound = max(1, int(more_match.group(1)))
        lower_bound = min(lower_bound, MAX_BODY_CHAPTERS)
        return None, lower_bound, MAX_BODY_CHAPTERS, f"{lower_bound}页以上"

    approx_match = re.search(r"(\d+)\s*页\s*(?:左右|上下|以内)", text, flags=re.IGNORECASE)
    if approx_match:
        chapters = max(1, min(int(approx_match.group(1)), MAX_BODY_CHAPTERS))
        return chapters, None, None, f"{chapters}页左右"

    exact_match = re.search(r"(\d+)\s*页", text, flags=re.IGNORECASE)
    if exact_match:
        chapters = max(1, min(int(exact_match.group(1)), MAX_BODY_CHAPTERS))
        return chapters, None, None, f"{chapters}页"

    return None, None, None, ""


def _extract_core_content(text: str) -> str:
    normalized = _normalize_text(text)
    for pattern in CONTENT_PATTERNS:
        match = re.search(pattern, normalized, flags=re.IGNORECASE)
        if match:
            candidate = match.group(1).strip(" ：:，,。.；;")
            if candidate:
                return candidate

    if re.search(r"[、,，/]", normalized) and len(normalized) >= 16:
        fragments = [fragment.strip() for fragment in re.split(r"[。；;]", normalized) if fragment.strip()]
        if fragments:
            candidate = fragments[-1]
            if len(candidate) >= 8:
                return candidate
    return ""


def _strip_metadata_from_topic(text: str) -> str:
    candidate = text
    candidate = re.sub(r"给[^，。；;,:：]{1,12}(?:看|汇报|展示)", " ", candidate)
    candidate = re.sub(r"(面向|针对)[^，。；;,:：]{1,12}", " ", candidate)
    candidate = re.sub(r"\d+\s*[-~到至]\s*\d+\s*页", " ", candidate)
    candidate = re.sub(r"\d+\s*页\s*(?:左右|上下|以内|以上|起)?", " ", candidate)
    candidate = re.sub(r"(商务专业|科技现代|简约清晰|活泼有趣|商务风|科技风|简约风)\s*风格?", " ", candidate)
    candidate = re.sub(r"\b风格\b", " ", candidate)
    candidate = re.sub(r"(帮我|请|麻烦|想要|需要)(?:做|生成|写|整理)?", " ", candidate)
    candidate = re.sub(r"(一份|一个|个)", " ", candidate)
    candidate = re.sub(r"\bPPT\b", " ", candidate, flags=re.IGNORECASE)
    candidate = re.sub(r"(内容|重点|包括|围绕|聚焦).*$", " ", candidate)
    candidate = re.sub(r"[，,。；;：:]", " ", candidate)
    return _normalize_text(candidate)


def _is_generic_topic(text: str) -> bool:
    if not text:
        return True
    normalized = _normalize_text(text).lower()
    return any(re.fullmatch(pattern, normalized, flags=re.IGNORECASE) for pattern in GENERIC_REQUEST_PATTERNS)


def _extract_topic(text: str) -> str:
    candidate = _strip_metadata_from_topic(text)
    if _is_generic_topic(candidate):
        return ""
    return candidate[:60]


def _build_requirements_from_text(text: str) -> ClarifierRequirements:
    normalized = _normalize_text(text)
    chapters, min_slides, max_slides, slide_hint = _extract_slide_preferences(normalized)
    return ClarifierRequirements(
        topic=_extract_topic(normalized),
        purpose=_extract_by_patterns(normalized, PURPOSE_PATTERNS),
        audience=_extract_by_patterns(normalized, AUDIENCE_PATTERNS),
        style=_extract_by_patterns(normalized, STYLE_PATTERNS),
        template=_extract_template(normalized),
        theme=_extract_theme(normalized),
        core_content=_extract_core_content(normalized),
        chapters=chapters,
        min_slides=min_slides,
        max_slides=max_slides,
        slide_hint=slide_hint,
        raw_request=normalized,
    )


def _format_known_requirements(requirements: ClarifierRequirements) -> str:
    lines = requirements.summary_lines()
    return "\n".join(f"- {line}" for line in lines) if lines else "- none"


def _choice_key(index: int) -> str:
    return chr(ord("A") + index)


def _recommended_option_for_dimension(dimension: str, requirements: ClarifierRequirements) -> str:
    if dimension == "purpose":
        if requirements.purpose:
            return requirements.purpose
        normalized = requirements.raw_request
        if "方案" in normalized or "提案" in normalized:
            return "产品提案"
        if "课件" in normalized or "培训" in normalized:
            return "教学课件"
        if "演讲" in normalized or "路演" in normalized:
            return "会议演讲"
        return "工作汇报"
    if dimension == "audience":
        if requirements.audience:
            return requirements.audience
        if requirements.purpose == "教学课件":
            return "学生"
        if requirements.purpose == "产品提案":
            return "客户"
        if requirements.purpose == "会议演讲":
            return "通用"
        return "公司领导"
    if dimension == "slides":
        return requirements.slide_summary() or "10页左右"
    if dimension == "style":
        if requirements.style:
            return requirements.style
        if requirements.purpose == "教学课件":
            return "简约清晰"
        if requirements.purpose == "会议演讲":
            return "科技现代"
        return "商务专业"
    if dimension == "template_theme":
        if requirements.theme:
            return f"theme:{requirements.theme}"
        if requirements.template:
            return f"template:{requirements.template}"
        return f"theme:{DEFAULT_V2_THEME}"
    if dimension == "core_content":
        if requirements.core_content:
            return requirements.core_content
        if requirements.purpose == "产品提案":
            return "痛点/方案/价值"
        if requirements.purpose == "会议演讲":
            return "背景/目标/路径"
        return "进展/风险/下一步"
    return ""


def _build_options_for_dimension(dimension: str, requirements: ClarifierRequirements) -> tuple[ClarifierOption, ...]:
    if dimension == "template_theme":
        recommended_value = _recommended_option_for_dimension(dimension, requirements)
        options: list[ClarifierOption] = []
        for index, theme_name in enumerate(_available_v2_themes()):
            value = f"theme:{theme_name}"
            description = "V2 semantic theme" if theme_name != DEFAULT_V2_THEME else "V2 semantic theme (default)"
            options.append(
                ClarifierOption(
                    key=_choice_key(index),
                    value=value,
                    description=description,
                    recommended=value == recommended_value,
                )
            )
        base_index = len(options)
        for offset, template_name in enumerate(_available_template_names()):
            value = f"template:{template_name}"
            options.append(
                ClarifierOption(
                    key=_choice_key(base_index + offset),
                    value=value,
                    description="Legacy PPTX template",
                    recommended=value == recommended_value,
                )
            )
        if options and not any(option.recommended for option in options):
            first = options[0]
            options[0] = ClarifierOption(
                key=first.key,
                value=first.value,
                description=first.description,
                recommended=True,
            )
        return tuple(options)

    values = DIMENSION_OPTIONS.get(dimension, ())
    descriptions = DIMENSION_OPTION_DESCRIPTIONS.get(dimension, {})
    recommended_value = _recommended_option_for_dimension(dimension, requirements)
    options = tuple(
        ClarifierOption(
            key=_choice_key(index),
            value=value,
            description=descriptions.get(value, ""),
            recommended=value == recommended_value,
        )
        for index, value in enumerate(values)
    )
    if options and not any(option.recommended for option in options):
        first = options[0]
        return (
            ClarifierOption(
                key=first.key,
                value=first.value,
                description=first.description,
                recommended=True,
            ),
            *options[1:],
        )
    return options


def _build_pending_questions(
    missing_dimensions: tuple[str, ...],
    requirements: ClarifierRequirements,
) -> tuple[ClarifierQuestion, ...]:
    prompts = {
        "template_theme": "Choose the template/theme. Use theme:* for V2; template:* is legacy only.",
        "topic": "这份 PPT 的主题是什么？请尽量用一句话说清楚。",
        "purpose": "这份 PPT 主要用于什么场景？",
        "audience": "这份 PPT 主要给谁看？",
        "slides": "你希望大概做多少页？",
        "style": "你想要什么风格？",
        "core_content": "这次最想重点讲哪些内容？",
    }
    questions = []
    for dimension in missing_dimensions:
        questions.append(
            ClarifierQuestion(
                dimension=dimension,
                prompt=prompts[dimension],
                options=_build_options_for_dimension(dimension, requirements),
            )
        )
    return tuple(questions)


def _apply_dimension_answer(dimension: str, raw_value: str) -> ClarifierRequirements:
    value = _normalize_text(raw_value)
    if not value:
        return ClarifierRequirements()
    if dimension == "topic":
        return ClarifierRequirements(topic=value)
    if dimension == "purpose":
        return ClarifierRequirements(purpose=value)
    if dimension == "audience":
        return ClarifierRequirements(audience=value)
    if dimension == "style":
        return ClarifierRequirements(style=value)
    if dimension == "template_theme":
        if value.lower().startswith("theme:"):
            return ClarifierRequirements(theme=value.split(":", 1)[1].strip())
        if value.lower().startswith("template:"):
            return ClarifierRequirements(template=_normalize_template_name(value.split(":", 1)[1].strip()))
        detected_theme = _extract_theme(value)
        if detected_theme:
            return ClarifierRequirements(theme=detected_theme)
        detected_template = _extract_template(value)
        if detected_template:
            return ClarifierRequirements(template=detected_template)
        return ClarifierRequirements(theme=value)
    if dimension == "core_content":
        return ClarifierRequirements(core_content=value)
    if dimension == "slides":
        chapters, min_slides, max_slides, slide_hint = _extract_slide_preferences(value)
        return ClarifierRequirements(
            chapters=chapters,
            min_slides=min_slides,
            max_slides=max_slides,
            slide_hint=slide_hint,
        )
    return ClarifierRequirements()


def _extract_requirements_from_choice_answers(
    text: str,
    pending_dimensions: tuple[str, ...],
    base_requirements: ClarifierRequirements,
) -> ClarifierRequirements:
    if not pending_dimensions:
        return ClarifierRequirements()
    questions = _build_pending_questions(pending_dimensions, base_requirements)
    extracted = ClarifierRequirements()
    for index, question in enumerate(questions, start=1):
        matched = False
        if question.options:
            option_map = {option.key.upper(): option.value for option in question.options}
            patterns = (
                rf"(?:^|[\s,，;；]){index}\s*[:：=．.、-]?\s*([A-Z])\b",
                rf"(?:^|[\s,，;；]){question.dimension}\s*[:：=]?\s*([A-Z])\b",
            )
            for pattern in patterns:
                match = re.search(pattern, text, flags=re.IGNORECASE)
                if match:
                    option_key = match.group(1).upper()
                    if option_key in option_map:
                        extracted = extracted.merge(_apply_dimension_answer(question.dimension, option_map[option_key]))
                        matched = True
                        break
        if matched:
            continue
        if question.allow_custom:
            patterns = (
                rf"(?:^|[\n\r]){index}\s*[:：=．.、-]\s*(.+)",
                rf"(?:^|[\n\r]){question.dimension}\s*[:：=]\s*(.+)",
            )
            for pattern in patterns:
                match = re.search(pattern, text, flags=re.IGNORECASE)
                if match:
                    value = _normalize_text(match.group(1))
                    if value:
                        extracted = extracted.merge(_apply_dimension_answer(question.dimension, value))
                        break
    return extracted


def _build_response_template(questions: tuple[ClarifierQuestion, ...]) -> str:
    lines = []
    for index, question in enumerate(questions, start=1):
        recommended_option = next((option for option in question.options if option.recommended), None)
        if recommended_option is not None:
            lines.append(f"{index}{recommended_option.key}")
        else:
            lines.append(f"{index}. {DIMENSION_LABELS.get(question.dimension, question.dimension)}：")
    return "\n".join(lines)


def _llm_extract_requirements(
    text: str,
    *,
    existing_requirements: ClarifierRequirements | None = None,
    model: str | None = None,
) -> ClarifierRequirements | None:
    known_requirements = existing_requirements or ClarifierRequirements()
    try:
        client = OpenAIResponsesClient(load_openai_responses_config(model=model))
    except OpenAIConfigurationError:
        return None

    developer_prompt = render_prompt_template(
        CLARIFIER_PROMPT_PATH,
        known_requirements=_format_known_requirements(known_requirements),
        pending_dimensions=", ".join(known_requirements.known_dimensions().keys()) or "all",
    )
    user_prompt = f"User request:\n{text.strip()}\n"
    schema = {
        "type": "object",
        "properties": {
            "topic": {"type": "string"},
            "purpose": {"type": "string"},
            "audience": {"type": "string"},
            "style": {"type": "string"},
            "template": {"type": "string"},
            "theme": {"type": "string"},
            "core_content": {"type": "string"},
            "chapters": {"type": ["integer", "null"], "minimum": 1, "maximum": MAX_BODY_CHAPTERS},
            "min_slides": {"type": ["integer", "null"], "minimum": 1, "maximum": MAX_BODY_CHAPTERS},
            "max_slides": {"type": ["integer", "null"], "minimum": 1, "maximum": MAX_BODY_CHAPTERS},
            "slide_hint": {"type": "string"},
            "should_skip": {"type": "boolean"},
        },
        "required": [
            "topic",
            "purpose",
            "audience",
            "style",
            "template",
            "theme",
            "core_content",
            "chapters",
            "min_slides",
            "max_slides",
            "slide_hint",
            "should_skip",
        ],
        "additionalProperties": False,
    }
    try:
        payload = client.create_structured_json(
            developer_prompt=developer_prompt,
            user_prompt=user_prompt,
            schema_name="sie_autoppt_clarifier",
            schema=schema,
        )
    except OpenAIResponsesError:
        return None

    if bool(payload.get("should_skip")):
        return ClarifierRequirements(raw_request=text.strip())
    return ClarifierRequirements(
        topic=str(payload.get("topic", "")).strip(),
        purpose=str(payload.get("purpose", "")).strip(),
        audience=str(payload.get("audience", "")).strip(),
        style=str(payload.get("style", "")).strip(),
        template=str(payload.get("template", "")).strip(),
        theme=str(payload.get("theme", "")).strip(),
        core_content=str(payload.get("core_content", "")).strip(),
        chapters=payload.get("chapters"),
        min_slides=payload.get("min_slides"),
        max_slides=payload.get("max_slides"),
        slide_hint=str(payload.get("slide_hint", "")).strip(),
        raw_request=text.strip(),
    )


def _combine_requirements(
    base: ClarifierRequirements,
    extracted: ClarifierRequirements,
    llm_extracted: ClarifierRequirements | None = None,
) -> ClarifierRequirements:
    combined = base.merge(extracted)
    if llm_extracted is not None:
        combined = combined.merge(llm_extracted)
    return combined


def _missing_dimensions(requirements: ClarifierRequirements) -> tuple[str, ...]:
    known = requirements.known_dimensions()
    return tuple(dimension for dimension in DIMENSION_ORDER if dimension not in known)


def _is_ready(requirements: ClarifierRequirements, missing_dimensions: tuple[str, ...]) -> bool:
    known_count = len(requirements.known_dimensions())
    has_specific_topic = not _is_generic_topic(requirements.topic)
    required_dimensions = {"purpose", "audience", "slides", "style", "template_theme"}
    if not has_specific_topic:
        return False
    if any(dimension not in requirements.known_dimensions() for dimension in required_dimensions):
        return False
    if has_specific_topic and requirements.core_content and known_count >= 5:
        return True
    if has_specific_topic and known_count >= 5:
        return True
    return False


def _build_brief(requirements: ClarifierRequirements, original_brief: str = "") -> str:
    parts = []
    if original_brief.strip():
        parts.append(original_brief.strip())
    if requirements.purpose:
        parts.append(f"用途：{requirements.purpose}")
    if requirements.style:
        if requirements.theme:
            parts.append(f"Theme: {requirements.theme}")
        if requirements.template:
            parts.append(f"Template: {requirements.template}")
        parts.append(f"风格：{requirements.style}")
    if requirements.core_content:
        parts.append(f"核心内容：{requirements.core_content}")
    if requirements.slide_summary():
        parts.append(f"页数偏好：{requirements.slide_summary()}")
    return "\n".join(part for part in parts if part)


def _requires_blocking_clarification(requirements: ClarifierRequirements, guide_mode: str) -> bool:
    if guide_mode != "full":
        return False
    known = requirements.known_dimensions()
    return "topic" not in known or len(known) <= 2


def _build_message(
    requirements: ClarifierRequirements,
    *,
    status: str,
    guide_mode: str,
    questions: tuple[ClarifierQuestion, ...],
    blocking: bool,
    response_template: str,
) -> str:
    summary = requirements.summary_lines()
    if status == "skipped":
        prefix = "已按你的要求跳过澄清，后续会基于当前已知信息直接进入规划。"
    elif status == "ready":
        prefix = "需求已经足够清楚，可以直接进入 AI 规划。"
    elif blocking:
        prefix = "当前指令还不够清楚，我会先阻塞生成流程。请先回答下面的问题后，我再继续生成。"
    elif guide_mode == "full":
        prefix = "我先帮你把需求补齐。下面这些维度里，当前已知信息还不够。"
    else:
        prefix = "我已经拿到一部分信息，还差下面这些维度补齐后会更稳。"

    sections = [prefix]
    if summary:
        sections.append("已识别信息：\n" + "\n".join(f"- {line}" for line in summary))
    if questions:
        question_lines = []
        for index, question in enumerate(questions, start=1):
            question_lines.append(f"{index}. {question.prompt}")
            for option in question.options:
                recommended_tag = "（推荐）" if option.recommended else ""
                description = f" - {option.description}" if option.description else ""
                question_lines.append(f"   {option.key}. {option.value}{recommended_tag}{description}")
            if question.allow_custom:
                question_lines.append("   其他：可直接自定义输入")
        sections.append("待补充：\n" + "\n".join(question_lines))
        if response_template:
            sections.append("推荐回复模板：\n" + response_template)
        if blocking:
            sections.append("回复“直接生成”可跳过，但默认不会继续往下规划。")
        else:
            sections.append("也可以直接回复“直接生成”，跳过继续追问。")
    return "\n\n".join(sections)


def clarify_user_input(
    user_input: str,
    *,
    session: ClarifierSession | None = None,
    original_brief: str = "",
    model: str | None = None,
    prefer_llm: bool = True,
) -> ClarifierResult:
    existing_session = session or ClarifierSession()
    raw_input = user_input.strip()
    normalized_input = _normalize_text(user_input)
    skip_requested = _contains_skip_keyword(normalized_input)
    current_pending_dimensions = existing_session.pending_dimensions or _missing_dimensions(existing_session.requirements)

    choice_requirements = _extract_requirements_from_choice_answers(
        raw_input,
        current_pending_dimensions,
        existing_session.requirements,
    )
    heuristic_requirements = _build_requirements_from_text(normalized_input)
    llm_requirements = None
    if prefer_llm and normalized_input and not skip_requested:
        llm_requirements = _llm_extract_requirements(
            normalized_input,
            existing_requirements=existing_session.requirements,
            model=model,
        )
    if "topic" not in current_pending_dimensions and not choice_requirements.topic:
        heuristic_requirements = replace(heuristic_requirements, topic="")
        if llm_requirements is not None:
            llm_requirements = replace(llm_requirements, topic="")

    combined_requirements = _combine_requirements(
        existing_session.requirements,
        heuristic_requirements.merge(choice_requirements),
        llm_requirements,
    )
    if not combined_requirements.raw_request:
        combined_requirements = combined_requirements.merge(ClarifierRequirements(raw_request=normalized_input))

    missing_dimensions = _missing_dimensions(combined_requirements)
    if skip_requested:
        status = "skipped"
        guide_mode = "none"
    elif _is_ready(combined_requirements, missing_dimensions):
        status = "ready"
        guide_mode = "none"
    elif len(combined_requirements.known_dimensions()) <= 1 and _is_generic_topic(combined_requirements.topic):
        status = "needs_clarification"
        guide_mode = "full"
    else:
        status = "needs_clarification"
        guide_mode = "partial"

    questions = () if status in {"ready", "skipped"} else _build_pending_questions(missing_dimensions, combined_requirements)
    blocking = status == "needs_clarification" and _requires_blocking_clarification(combined_requirements, guide_mode)
    response_template = "" if status in {"ready", "skipped"} else _build_response_template(questions)
    message = _build_message(
        combined_requirements,
        status=status,
        guide_mode=guide_mode,
        questions=questions,
        blocking=blocking,
        response_template=response_template,
    )

    merged_history = existing_session.history + ({"role": "user", "content": normalized_input},)
    clarified_session = ClarifierSession(
        requirements=combined_requirements,
        turn_count=existing_session.turn_count + 1,
        pending_dimensions=missing_dimensions,
        asked_dimensions=tuple(dict.fromkeys((*existing_session.asked_dimensions, *missing_dimensions))),
        skipped=skip_requested,
        status=status,
        history=merged_history,
    )

    audience = combined_requirements.audience or ""
    topic = combined_requirements.topic or normalized_input
    return ClarifierResult(
        session=clarified_session,
        requirements=combined_requirements,
        status=status,
        guide_mode=guide_mode,
        missing_dimensions=missing_dimensions,
        questions=questions,
        message=message,
        topic=topic,
        audience=audience,
        brief=_build_brief(combined_requirements, original_brief=original_brief),
        chapters=combined_requirements.chapters,
        min_slides=combined_requirements.min_slides,
        max_slides=combined_requirements.max_slides,
        blocking=blocking,
        response_template=response_template,
        skipped=skip_requested,
    )


def derive_planning_context(
    *,
    topic: str,
    brief: str = "",
    audience: str = "",
    template: str = "",
    theme: str = "",
    chapters: int | None = None,
    min_slides: int | None = None,
    max_slides: int | None = None,
    model: str | None = None,
    prefer_llm: bool = False,
) -> ClarifierResult:
    explicit_requirements = ClarifierRequirements(
        audience="" if audience.strip() == DEFAULT_AUDIENCE_HINT else audience.strip(),
        template=_normalize_template_name(template.strip()) if template.strip() else "",
        theme=theme.strip(),
        core_content=brief.strip(),
        chapters=chapters,
        min_slides=min_slides,
        max_slides=max_slides,
        slide_hint=(
            f"{chapters}页"
            if chapters is not None
            else (
                f"{min_slides}-{max_slides}页"
                if min_slides is not None and max_slides is not None
                else ""
            )
        ),
    )
    seed_session = ClarifierSession(requirements=explicit_requirements)
    result = clarify_user_input(
        topic,
        session=seed_session,
        original_brief=brief,
        model=model,
        prefer_llm=prefer_llm,
    )
    merged_requirements = result.requirements.merge(explicit_requirements)
    missing_dimensions = _missing_dimensions(merged_requirements)
    if result.skipped:
        status = "skipped"
        guide_mode = "none"
    elif _is_ready(merged_requirements, missing_dimensions):
        status = "ready"
        guide_mode = "none"
    elif len(merged_requirements.known_dimensions()) <= 1 and _is_generic_topic(merged_requirements.topic):
        status = "needs_clarification"
        guide_mode = "full"
    else:
        status = "needs_clarification"
        guide_mode = "partial"

    questions = () if status in {"ready", "skipped"} else _build_pending_questions(missing_dimensions, merged_requirements)
    blocking = status == "needs_clarification" and _requires_blocking_clarification(merged_requirements, guide_mode)
    response_template = "" if status in {"ready", "skipped"} else _build_response_template(questions)
    message = _build_message(
        merged_requirements,
        status=status,
        guide_mode=guide_mode,
        questions=questions,
        blocking=blocking,
        response_template=response_template,
    )
    merged_session = ClarifierSession(
        requirements=merged_requirements,
        turn_count=result.session.turn_count,
        pending_dimensions=missing_dimensions,
        asked_dimensions=result.session.asked_dimensions,
        skipped=result.skipped,
        status=status,
        history=result.session.history,
    )
    return ClarifierResult(
        session=merged_session,
        requirements=merged_requirements,
        status=status,
        guide_mode=guide_mode,
        missing_dimensions=missing_dimensions,
        questions=questions,
        message=message,
        topic=merged_requirements.topic or topic.strip(),
        audience=merged_requirements.audience.strip(),
        brief=_build_brief(merged_requirements, original_brief=brief),
        chapters=merged_requirements.chapters,
        min_slides=merged_requirements.min_slides,
        max_slides=merged_requirements.max_slides,
        blocking=blocking,
        response_template=response_template,
        skipped=result.skipped,
    )
