from __future__ import annotations

from dataclasses import dataclass

from .template_index import TemplateDescriptor, TemplateIndex, build_default_template_index


@dataclass(frozen=True)
class TemplateMatchResult:
    template_id: str
    content_type: str
    confidence: float
    fallback: bool


class TemplateMatcher:
    def __init__(self, index: TemplateIndex | None = None):
        self.index = index or build_default_template_index()

    def _score(self, template: TemplateDescriptor, *, style_variant: str) -> float:
        style_score = 0.2 if style_variant in template.styles else 0.0
        keyword_bonus = 0.0
        if style_variant == "minimal" and "comparison" in template.keywords:
            keyword_bonus = 0.05
        if style_variant == "decorative" and "infographic" in template.keywords:
            keyword_bonus = 0.05
        return 0.6 + style_score + keyword_bonus

    def match(self, *, content_type: str, style_variant: str) -> TemplateMatchResult:
        candidates = self.index.filter_by_type(content_type)
        if not candidates:
            return TemplateMatchResult(template_id="", content_type=content_type, confidence=0.0, fallback=True)

        scored = sorted(
            ((self._score(template, style_variant=style_variant), template) for template in candidates),
            key=lambda item: item[0],
            reverse=True,
        )
        confidence, best = scored[0]
        return TemplateMatchResult(
            template_id=best.template_id,
            content_type=best.content_type,
            confidence=round(confidence, 3),
            fallback=confidence < 0.6,
        )
