import json
from pathlib import Path
from typing import cast

from .models import BodyPageSpec, DeckSpec, validate_body_page_payload

DECK_SPEC_SCHEMA_VERSION = "1.0"


def body_page_spec_to_dict(page: BodyPageSpec) -> dict[str, object]:
    payload = page.payload
    payload_value = cast(dict[str, object], dict(payload))
    return {
        "page_key": page.page_key,
        "title": page.title,
        "subtitle": page.subtitle,
        "bullets": list(page.bullets),
        "pattern_id": page.pattern_id,
        "nav_title": page.nav_title,
        "reference_style_id": page.reference_style_id,
        "payload": payload_value,
    }


def body_page_spec_from_dict(data: dict[str, object]) -> BodyPageSpec:
    pattern_id = str(data["pattern_id"])
    validated_payload = validate_body_page_payload(pattern_id, data.get("payload", {}))
    if hasattr(validated_payload, "model_dump"):
        payload = validated_payload.model_dump(mode="json")
    else:
        payload = dict(validated_payload)
    bullets_raw = data.get("bullets", [])
    bullets: list[str] = []
    if isinstance(bullets_raw, list):
        bullets = [str(item) for item in bullets_raw]
    return BodyPageSpec(
        page_key=str(data["page_key"]),
        title=str(data["title"]),
        subtitle=str(data.get("subtitle", "")),
        bullets=bullets,
        pattern_id=pattern_id,
        nav_title=str(data.get("nav_title", "")),
        reference_style_id=str(data["reference_style_id"]) if data.get("reference_style_id") else None,
        payload=payload,
    )


def deck_spec_to_dict(deck: DeckSpec) -> dict[str, object]:
    return {
        "schema_version": DECK_SPEC_SCHEMA_VERSION,
        "cover_title": deck.cover_title,
        "body_pages": [body_page_spec_to_dict(page) for page in deck.body_pages],
    }


def deck_spec_from_dict(data: dict[str, object]) -> DeckSpec:
    body_pages_data = data.get("body_pages", [])
    if not isinstance(body_pages_data, list):
        raise ValueError("Deck spec body_pages must be a list.")
    return DeckSpec(
        cover_title=str(data["cover_title"]),
        body_pages=[body_page_spec_from_dict(page) for page in body_pages_data],
    )


def load_deck_spec(deck_spec_path: Path) -> DeckSpec:
    data = json.loads(deck_spec_path.read_text(encoding="utf-8-sig"))
    return deck_spec_from_dict(data)


def write_deck_spec(deck: DeckSpec, deck_spec_path: Path) -> Path:
    deck_spec_path.parent.mkdir(parents=True, exist_ok=True)
    deck_spec_path.write_text(
        json.dumps(deck_spec_to_dict(deck), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return deck_spec_path
