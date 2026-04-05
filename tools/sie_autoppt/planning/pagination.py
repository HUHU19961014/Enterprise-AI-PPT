from __future__ import annotations

from ..models import BodyPageSpec


def paginate_body_page(
    page: BodyPageSpec,
    *,
    max_items_per_page: int,
) -> list[BodyPageSpec]:
    if max_items_per_page <= 0 or len(page.bullets) <= max_items_per_page:
        return [
            BodyPageSpec(
                page_key=page.page_key,
                title=page.title,
                subtitle=page.subtitle,
                bullets=page.bullets,
                pattern_id=page.pattern_id,
                nav_title=page.nav_title,
                reference_style_id=page.reference_style_id,
                payload=page.payload,
                layout_variant=page.layout_variant,
                content_count=len(page.bullets),
                is_continuation=False,
                continuation_index=None,
                slide_role=page.slide_role,
                layout_hints=page.layout_hints,
                source_item_range=(0, len(page.bullets)) if page.bullets else None,
            )
        ]

    pages: list[BodyPageSpec] = []
    for continuation_index, start in enumerate(range(0, len(page.bullets), max_items_per_page), start=1):
        end = min(start + max_items_per_page, len(page.bullets))
        is_continuation = continuation_index > 1
        pages.append(
            BodyPageSpec(
                page_key=page.page_key if not is_continuation else f"{page.page_key}_cont_{continuation_index}",
                title=page.title,
                subtitle=page.subtitle,
                bullets=page.bullets[start:end],
                pattern_id=page.pattern_id,
                nav_title=page.nav_title,
                reference_style_id=page.reference_style_id,
                payload=page.payload,
                layout_variant=page.layout_variant,
                content_count=end - start,
                is_continuation=is_continuation,
                continuation_index=continuation_index if is_continuation else None,
                slide_role=page.slide_role,
                layout_hints=page.layout_hints,
                source_item_range=(start, end),
            )
        )
    return pages
