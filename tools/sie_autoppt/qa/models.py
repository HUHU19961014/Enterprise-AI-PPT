from dataclasses import asdict, dataclass, field

from ..models import DeckRenderTrace


@dataclass(frozen=True)
class QaChecks:
    ending_last: str
    theme_title_font: str
    directory_title_font: str
    directory_assets_preserved: str
    template_pool_mode: str
    reference_style_coverage: str
    preflight: str
    content_density: str
    title_uniqueness: str


@dataclass(frozen=True)
class QaMetrics:
    overflow_risk_boxes: int
    long_text_shape_count: int
    sparse_bullet_pages: int
    repeated_title_count: int
    fallback_render_pages: int
    low_confidence_pattern_pages: int
    reference_style_pages: int
    preflight_note_count: int


@dataclass(frozen=True)
class QaResult:
    file: str
    slides: int
    expected_directory_pages: list[int]
    actual_directory_pages: list[int]
    template_name: str
    template_manifest_path: str
    template_manifest_version: str
    expected_theme_title_font_pt: float
    expected_directory_title_font_pt: float
    checks: QaChecks
    metrics: QaMetrics
    semantic_patterns: list[str] = field(default_factory=list)
    chapter_lines: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    render_trace: DeckRenderTrace | None = None
    schema_version: str = "1.4"

    def to_dict(self) -> dict[str, object]:
        return asdict(self)
