import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import TypeAlias, TypedDict, cast

from pydantic import BaseModel, ConfigDict, Field


class PayloadModel(BaseModel):
    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)


class ProcessStepPayload(TypedDict):
    number: str
    title: str
    detail: str


class ProcessFlowPagePayload(TypedDict):
    steps: list[ProcessStepPayload]


class ArchitectureLayerPayload(TypedDict):
    label: str
    title: str
    detail: str


class SolutionArchitecturePagePayload(TypedDict, total=False):
    layers: list[ArchitectureLayerPayload]
    banner_text: str


class GovernanceCardPayload(TypedDict):
    label: str
    detail: str


class GovernancePagePayload(TypedDict, total=False):
    cards: list[GovernanceCardPayload]
    label_prefix: str
    footer_text: str


class ComparisonCardPayload(TypedDict):
    title: str
    detail: str


class ComparisonUpgradePagePayload(TypedDict, total=False):
    headline: str
    left_label: str
    right_label: str
    left_cards: list[ComparisonCardPayload]
    right_cards: list[ComparisonCardPayload]
    center_kicker: str
    center_title: str
    center_subtitle: str
    center_top_label: str
    center_section_title: str
    center_row1_left: str
    center_row1_right: str
    center_row2_left: str
    center_row2_right: str
    center_divider: str
    center_bottom_label: str
    center_bottom_title: str
    center_bottom_left: str
    center_bottom_right: str
    center_bottom_footer: str
    bottom_left_caption: str
    bottom_right_caption: str


class CapabilityRingItemPayload(TypedDict):
    title: str
    detail: str


class CapabilityRingPagePayload(TypedDict, total=False):
    items: list[CapabilityRingItemPayload]
    headline: str


class FivePhaseStagePayload(TypedDict):
    header: str
    tasks: list[str]


class FivePhasePathPagePayload(TypedDict):
    intro: str
    stages: list[FivePhaseStagePayload]
    legend: list[str]


class PainCardPayload(TypedDict, total=False):
    title: str
    detail: str
    points: list[str]


class PainCardsPagePayload(TypedDict, total=False):
    lead: str
    bottom_banner: str
    cards: list[PainCardPayload]


class RoadmapStagePayload(TypedDict, total=False):
    period: str
    title: str
    detail: str


class RoadmapTimelinePagePayload(TypedDict, total=False):
    headline: str
    footer: str
    stages: list[RoadmapStagePayload]


class KpiMetricPayload(TypedDict, total=False):
    label: str
    value: str
    detail: str


class KpiDashboardPagePayload(TypedDict, total=False):
    headline: str
    footer: str
    metrics: list[KpiMetricPayload]
    insights: list[str]


class RiskItemPayload(TypedDict, total=False):
    title: str
    detail: str
    quadrant: str


class RiskMatrixPagePayload(TypedDict, total=False):
    headline: str
    footer: str
    items: list[RiskItemPayload]


class ClaimItemPayload(TypedDict, total=False):
    label: str
    value: str
    detail: str


class ClaimBreakdownPagePayload(TypedDict, total=False):
    headline: str
    footer: str
    claims: list[ClaimItemPayload]
    summary: str


class ProcessStepModel(PayloadModel):
    number: str = Field(min_length=1, max_length=20)
    title: str = Field(min_length=1, max_length=80)
    detail: str = Field(min_length=1, max_length=240)


class ProcessFlowPageModel(PayloadModel):
    steps: list[ProcessStepModel] = Field(min_length=1, max_length=10)


class ArchitectureLayerModel(PayloadModel):
    label: str = Field(min_length=1, max_length=20)
    title: str = Field(min_length=1, max_length=80)
    detail: str = Field(min_length=1, max_length=240)


class SolutionArchitecturePageModel(PayloadModel):
    layers: list[ArchitectureLayerModel] = Field(default_factory=list, max_length=10)
    banner_text: str | None = Field(default=None, max_length=120)


class GovernanceCardModel(PayloadModel):
    label: str = Field(min_length=1, max_length=40)
    detail: str = Field(min_length=1, max_length=240)


class GovernancePageModel(PayloadModel):
    cards: list[GovernanceCardModel] = Field(default_factory=list, max_length=10)
    label_prefix: str | None = Field(default=None, max_length=20)
    footer_text: str | None = Field(default=None, max_length=120)


class ComparisonCardModel(PayloadModel):
    title: str = Field(min_length=1, max_length=80)
    detail: str = Field(min_length=1, max_length=240)


class ComparisonUpgradePageModel(PayloadModel):
    headline: str | None = Field(default=None, max_length=120)
    left_label: str | None = Field(default=None, max_length=40)
    right_label: str | None = Field(default=None, max_length=40)
    left_cards: list[ComparisonCardModel] = Field(default_factory=list, max_length=8)
    right_cards: list[ComparisonCardModel] = Field(default_factory=list, max_length=8)
    center_kicker: str | None = Field(default=None, max_length=60)
    center_title: str | None = Field(default=None, max_length=80)
    center_subtitle: str | None = Field(default=None, max_length=120)


class CapabilityRingItemModel(PayloadModel):
    title: str = Field(min_length=1, max_length=80)
    detail: str = Field(min_length=1, max_length=240)


class CapabilityRingPageModel(PayloadModel):
    items: list[CapabilityRingItemModel] = Field(default_factory=list, max_length=10)
    headline: str | None = Field(default=None, max_length=120)


class FivePhaseStageModel(PayloadModel):
    header: str = Field(min_length=1, max_length=60)
    tasks: list[str] = Field(min_length=1, max_length=8)


class FivePhasePathPageModel(PayloadModel):
    intro: str = Field(min_length=1, max_length=240)
    stages: list[FivePhaseStageModel] = Field(min_length=1, max_length=6)
    legend: list[str] = Field(default_factory=list, max_length=6)


class PainCardModel(PayloadModel):
    title: str | None = Field(default=None, max_length=80)
    detail: str | None = Field(default=None, max_length=240)
    points: list[str] = Field(default_factory=list, max_length=8)


class PainCardsPageModel(PayloadModel):
    lead: str | None = Field(default=None, max_length=140)
    bottom_banner: str | None = Field(default=None, max_length=140)
    cards: list[PainCardModel] = Field(default_factory=list, max_length=8)


class RoadmapStageModel(PayloadModel):
    period: str | None = Field(default=None, max_length=30)
    title: str | None = Field(default=None, max_length=80)
    detail: str | None = Field(default=None, max_length=240)


class RoadmapTimelinePageModel(PayloadModel):
    headline: str | None = Field(default=None, max_length=120)
    footer: str | None = Field(default=None, max_length=140)
    stages: list[RoadmapStageModel] = Field(default_factory=list, max_length=8)


class KpiMetricModel(PayloadModel):
    label: str | None = Field(default=None, max_length=60)
    value: str | None = Field(default=None, max_length=60)
    detail: str | None = Field(default=None, max_length=140)


class KpiDashboardPageModel(PayloadModel):
    headline: str | None = Field(default=None, max_length=120)
    footer: str | None = Field(default=None, max_length=140)
    metrics: list[KpiMetricModel] = Field(default_factory=list, max_length=10)
    insights: list[str] = Field(default_factory=list, max_length=8)


class RiskItemModel(PayloadModel):
    title: str | None = Field(default=None, max_length=80)
    detail: str | None = Field(default=None, max_length=240)
    quadrant: str | None = Field(default=None, max_length=30)


class RiskMatrixPageModel(PayloadModel):
    headline: str | None = Field(default=None, max_length=120)
    footer: str | None = Field(default=None, max_length=140)
    items: list[RiskItemModel] = Field(default_factory=list, max_length=10)


class ClaimItemModel(PayloadModel):
    label: str | None = Field(default=None, max_length=80)
    value: str | None = Field(default=None, max_length=60)
    detail: str | None = Field(default=None, max_length=240)


class ClaimBreakdownPageModel(PayloadModel):
    headline: str | None = Field(default=None, max_length=120)
    footer: str | None = Field(default=None, max_length=140)
    claims: list[ClaimItemModel] = Field(default_factory=list, max_length=10)
    summary: str | None = Field(default=None, max_length=200)


LegacyBodyPagePayload: TypeAlias = (
    SolutionArchitecturePagePayload
    | ProcessFlowPagePayload
    | GovernancePagePayload
    | ComparisonUpgradePagePayload
    | CapabilityRingPagePayload
    | FivePhasePathPagePayload
    | PainCardsPagePayload
    | RoadmapTimelinePagePayload
    | KpiDashboardPagePayload
    | RiskMatrixPagePayload
    | ClaimBreakdownPagePayload
    | dict[str, object]
)

# Phase-2 migration default: treat runtime payload as dict and validate via `validate_body_page_payload`.
BodyPagePayload: TypeAlias = dict[str, object]

BodyPagePayloadModel: TypeAlias = (
    SolutionArchitecturePageModel
    | ProcessFlowPageModel
    | GovernancePageModel
    | ComparisonUpgradePageModel
    | CapabilityRingPageModel
    | FivePhasePathPageModel
    | PainCardsPageModel
    | RoadmapTimelinePageModel
    | KpiDashboardPageModel
    | RiskMatrixPageModel
    | ClaimBreakdownPageModel
)


_BODY_PAYLOAD_MODEL_MAP: dict[str, type[PayloadModel]] = {
    "solution_architecture": SolutionArchitecturePageModel,
    "process_flow": ProcessFlowPageModel,
    "governance": GovernancePageModel,
    "comparison_upgrade": ComparisonUpgradePageModel,
    "capability_ring": CapabilityRingPageModel,
    "five_phase_path": FivePhasePathPageModel,
    "pain_cards": PainCardsPageModel,
    "roadmap_timeline": RoadmapTimelinePageModel,
    "kpi_dashboard": KpiDashboardPageModel,
    "risk_matrix": RiskMatrixPageModel,
    "claim_breakdown": ClaimBreakdownPageModel,
}


def validate_body_page_payload(pattern_id: str, payload: object) -> BodyPagePayloadModel | dict[str, object]:
    model_cls = _BODY_PAYLOAD_MODEL_MAP.get(str(pattern_id or "").strip())
    if model_cls is None:
        if isinstance(payload, dict):
            return payload
        return {}
    data = payload if isinstance(payload, dict) else {}
    return cast(BodyPagePayloadModel, model_cls.model_validate(data))


@dataclass(frozen=True)
class HtmlSlide:
    title: str
    subtitle: str
    bullets: list[str]
    pattern_id: str = ""


@dataclass(frozen=True)
class InputPayload:
    title: str
    subtitle: str
    scope_title: str
    scope_subtitle: str
    focus_title: str
    focus_subtitle: str
    footer: str
    phases: list[dict[str, str]]
    scenarios: list[str]
    notes: list[str]
    slides: list[HtmlSlide] = field(default_factory=list)


@dataclass(frozen=True)
class StructureArgument:
    point: str
    evidence: str = ""


@dataclass(frozen=True)
class StructureSection:
    title: str
    key_message: str
    arguments: list[StructureArgument] = field(default_factory=list)


@dataclass(frozen=True)
class StructureSpec:
    core_message: str
    structure_type: str
    sections: list[StructureSection] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return {
            "core_message": self.core_message,
            "structure_type": self.structure_type,
            "sections": [
                {
                    "title": section.title,
                    "key_message": section.key_message,
                    "arguments": [
                        {
                            "point": argument.point,
                            "evidence": argument.evidence,
                        }
                        for argument in section.arguments
                    ],
                }
                for section in self.sections
            ],
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "StructureSpec":
        raw_sections = data.get("sections", [])
        sections: list[StructureSection] = []
        if isinstance(raw_sections, list):
            for raw_section in raw_sections:
                if not isinstance(raw_section, dict):
                    continue
                raw_arguments = raw_section.get("arguments", [])
                arguments: list[StructureArgument] = []
                if isinstance(raw_arguments, list):
                    for raw_argument in raw_arguments:
                        if not isinstance(raw_argument, dict):
                            continue
                        arguments.append(
                            StructureArgument(
                                point=str(raw_argument.get("point", "")).strip(),
                                evidence=str(raw_argument.get("evidence", "")).strip(),
                            )
                        )
                sections.append(
                    StructureSection(
                        title=str(raw_section.get("title", "")).strip(),
                        key_message=str(raw_section.get("key_message", "")).strip(),
                        arguments=arguments,
                    )
                )
        return cls(
            core_message=str(data.get("core_message", "")).strip(),
            structure_type=str(data.get("structure_type", "")).strip(),
            sections=sections,
        )


@dataclass(frozen=True)
class BodyPageSpec:
    page_key: str
    title: str
    subtitle: str
    bullets: list[str]
    pattern_id: str
    nav_title: str = ""
    reference_style_id: str | None = None
    payload: BodyPagePayload = field(default_factory=dict)
    layout_variant: str | None = None
    content_count: int = 0
    is_continuation: bool = False
    continuation_index: int | None = None
    slide_role: str | None = None
    layout_hints: dict[str, object] = field(default_factory=dict)
    source_item_range: tuple[int, int] | None = None


@dataclass(frozen=True)
class DeckSpec:
    cover_title: str
    body_pages: list[BodyPageSpec]


@dataclass(frozen=True)
class DeckPlan:
    deck: DeckSpec
    chapter_lines: list[str]
    pattern_ids: list[str]


@dataclass(frozen=True)
class PageRenderTrace:
    page_key: str
    title: str
    requested_pattern_id: str
    actual_pattern_id: str
    reference_style_id: str | None = None
    render_route: str = ""
    fallback_reason: str = ""


@dataclass(frozen=True)
class DeckRenderTrace:
    input_kind: str
    body_render_mode: str
    reference_import_applied: bool
    reference_import_reason: str = ""
    preflight_notes: list[str] = field(default_factory=list)
    page_traces: list[PageRenderTrace] = field(default_factory=list)


@dataclass(frozen=True)
class GenerationArtifacts:
    output_path: Path
    deck_plan: DeckPlan
    render_trace: DeckRenderTrace
