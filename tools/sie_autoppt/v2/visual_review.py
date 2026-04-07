from __future__ import annotations

import json
import os
import platform
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..llm_openai import OpenAIResponsesClient, load_openai_responses_config
from .io import load_deck_document, write_deck_document
from .ppt_engine import RenderArtifacts, generate_ppt
from .schema import DeckDocument, validate_deck_payload


@dataclass(frozen=True)
class VisualReviewArtifacts:
    review_path: Path
    patch_path: Path
    deck_path: Path
    pptx_path: Path
    preview_dir: Path
    final_review_path: Path
    final_patch_path: Path


@dataclass(frozen=True)
class SingleReviewArtifacts:
    review_path: Path
    patch_path: Path
    deck_path: Path
    pptx_path: Path
    preview_dir: Path


def build_visual_review_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "scores": {
                "type": "object",
                "properties": {
                    "structure": {"type": "integer", "minimum": 1, "maximum": 5},
                    "title_quality": {"type": "integer", "minimum": 1, "maximum": 5},
                    "content_density": {"type": "integer", "minimum": 1, "maximum": 5},
                    "layout_stability": {"type": "integer", "minimum": 1, "maximum": 5},
                    "deliverability": {"type": "integer", "minimum": 1, "maximum": 5},
                },
                "required": ["structure", "title_quality", "content_density", "layout_stability", "deliverability"],
                "additionalProperties": False,
            },
            "total": {"type": "integer", "minimum": 5, "maximum": 25},
            "rating": {"type": "string", "enum": ["优秀", "合格", "可用初稿", "质量偏弱", "不合格"]},
            "page_issues": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "page": {"type": "integer", "minimum": 1, "maximum": 50},
                        "level": {"type": "string", "enum": ["blocker", "warning"]},
                        "dimension": {"type": "string", "enum": ["structure", "title", "content", "layout", "delivery"]},
                        "issue": {"type": "string", "minLength": 2, "maxLength": 120},
                        "suggestion": {"type": "string", "minLength": 2, "maxLength": 120},
                    },
                    "required": ["page", "level", "dimension", "issue", "suggestion"],
                    "additionalProperties": False,
                },
            },
            "summary": {"type": "string", "minLength": 8, "maxLength": 240},
        },
        "required": ["scores", "total", "rating", "page_issues", "summary"],
        "additionalProperties": False,
    }


def build_patch_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "patches": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "page": {"type": "integer", "minimum": 1, "maximum": 50},
                        "field": {"type": "string", "minLength": 4, "maxLength": 80},
                        "old_value": {"type": ["string", "number", "boolean", "null"]},
                        "new_value": {"type": ["string", "number", "boolean", "null"]},
                        "reason": {"type": "string", "minLength": 4, "maxLength": 160},
                    },
                    "required": ["page", "field", "old_value", "new_value", "reason"],
                    "additionalProperties": False,
                },
            }
        },
        "required": ["patches"],
        "additionalProperties": False,
    }


def _review_developer_prompt() -> str:
    return (
        "You are a strict PPT visual QA reviewer. "
        "You will receive DeckSpec JSON plus slide PNG previews in page order. "
        "Score the deck on 5 dimensions using integers 1-5, identify specific page issues, "
        "and return only JSON that matches the schema. "
        "Be conservative: only give 5 when the quality is clearly strong. "
        "Focus especially on overflow, overlap, tiny text, weak contrast, and repetitive structure. "
        "Use the slide images as the primary source for layout_stability."
    )


def _patch_developer_prompt() -> str:
    return (
        "You are a PPT repair planner. "
        "Given a DeckSpec JSON plus a visual review result JSON, output minimal JSON patches only for blocker-level issues. "
        "Prefer content shortening, title rewriting, bullet trimming, and layout field changes that can be applied directly to the deck JSON. "
        "Use field paths like slides[2].title, slides[2].content[1], slides[2].left.items[0]. "
        "Do not emit patches for warnings. Return only JSON matching the schema."
    )


def _score_rating(total: int) -> str:
    if total >= 21:
        return "优秀"
    if total >= 16:
        return "合格"
    if total >= 11:
        return "可用初稿"
    if total >= 6:
        return "质量偏弱"
    return "不合格"


def export_slide_previews(pptx_path: Path, output_dir: Path) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    system = platform.system().lower()
    if system == "windows":
        script = (
            "$pptPath = Resolve-Path $args[0];"
            "$outDir = $args[1];"
            "New-Item -ItemType Directory -Path $outDir -Force | Out-Null;"
            "$ppt = New-Object -ComObject PowerPoint.Application;"
            "$ppt.Visible = -1;"
            "$pres = $ppt.Presentations.Open($pptPath.Path, $false, $false, $false);"
            "$idx = 1;"
            "foreach ($slide in $pres.Slides) {"
            "  $target = Join-Path $outDir ('slide' + $idx + '.png');"
            "  $slide.Export($target, 'PNG', 1920, 1080);"
            "  $idx += 1"
            "};"
            "$pres.Close();"
            "$ppt.Quit();"
        )
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", script, str(pptx_path), str(output_dir)],
            text=True,
            capture_output=True,
            check=False,
        )
        if result.returncode != 0:
            raise RuntimeError(f"Failed to export slide previews: {(result.stderr or result.stdout).strip()}")
    else:
        result = subprocess.run(
            ["soffice", "--headless", "--convert-to", "png", "--outdir", str(output_dir), str(pptx_path)],
            text=True,
            capture_output=True,
            check=False,
        )
        if result.returncode != 0:
            raise RuntimeError(f"Failed to export slide previews: {(result.stderr or result.stdout).strip()}")

    previews = sorted(output_dir.glob("slide*.png"))
    if not previews:
        raise RuntimeError(f"No slide previews were generated for {pptx_path}")
    return previews


def _build_review_user_items(deck: DeckDocument, previews: list[Path]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = [
        {
            "type": "text",
            "text": (
                "请按既定 5 个维度严格评分。下面先给出 DeckSpec JSON：\n"
                + json.dumps(deck.model_dump(mode="json"), ensure_ascii=False, indent=2)
                + "\n\n下面将按页码顺序提供 PNG 预览图。"
            ),
        }
    ]
    for index, preview in enumerate(previews, start=1):
        items.append({"type": "text", "text": f"第 {index} 页预览"})
        items.append({"type": "image_path", "path": str(preview)})
    return items


def review_rendered_deck(
    deck: DeckDocument,
    previews: list[Path],
    *,
    model: str | None = None,
) -> dict[str, Any]:
    client = OpenAIResponsesClient(load_openai_responses_config(model=model))
    result = client.create_structured_json_with_user_items(
        developer_prompt=_review_developer_prompt(),
        user_items=_build_review_user_items(deck, previews),
        schema_name="ppt_visual_review",
        schema=build_visual_review_schema(),
    )
    scores = result["scores"]
    total = sum(int(scores[key]) for key in ("structure", "title_quality", "content_density", "layout_stability", "deliverability"))
    result["total"] = total
    result["rating"] = _score_rating(total)
    return result


def generate_blocker_patches(
    deck: DeckDocument,
    review_result: dict[str, Any],
    *,
    model: str | None = None,
) -> dict[str, Any]:
    blockers = [issue for issue in review_result.get("page_issues", []) if issue.get("level") == "blocker"]
    if not blockers:
        return {"patches": []}

    client = OpenAIResponsesClient(load_openai_responses_config(model=model))
    user_items = [
        {
            "type": "text",
            "text": (
                "DeckSpec JSON:\n"
                + json.dumps(deck.model_dump(mode="json"), ensure_ascii=False, indent=2)
                + "\n\nVisual review JSON:\n"
                + json.dumps(review_result, ensure_ascii=False, indent=2)
                + "\n\n只针对 blocker 输出最小 patch 集合。"
            ),
        }
    ]
    return client.create_structured_json_with_user_items(
        developer_prompt=_patch_developer_prompt(),
        user_items=user_items,
        schema_name="ppt_repair_patches",
        schema=build_patch_schema(),
    )


def _parse_field_path(path: str) -> list[str | int]:
    tokens: list[str | int] = []
    buffer = ""
    index_buffer = ""
    in_index = False
    for char in path:
        if char == "." and not in_index:
            if buffer:
                tokens.append(buffer)
                buffer = ""
            continue
        if char == "[":
            if buffer:
                tokens.append(buffer)
                buffer = ""
            in_index = True
            index_buffer = ""
            continue
        if char == "]":
            if not in_index:
                raise ValueError(f"Invalid field path: {path}")
            tokens.append(int(index_buffer))
            in_index = False
            continue
        if in_index:
            index_buffer += char
        else:
            buffer += char
    if buffer:
        tokens.append(buffer)
    return tokens


def apply_patch_set(deck: DeckDocument, patch_set: dict[str, Any]) -> DeckDocument:
    payload = deck.model_dump(mode="json")
    for patch in patch_set.get("patches", []):
        path = str(patch["field"]).strip()
        tokens = _parse_field_path(path)
        cursor: Any = payload
        for token in tokens[:-1]:
            cursor = cursor[token]
        final_token = tokens[-1]
        cursor[final_token] = patch["new_value"]
    return validate_deck_payload(payload).deck


def _write_json(payload: dict[str, Any], path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def iterate_visual_review(
    *,
    deck_path: Path,
    output_dir: Path,
    model: str | None = None,
    max_rounds: int = 2,
    theme_name: str | None = None,
) -> VisualReviewArtifacts:
    output_dir.mkdir(parents=True, exist_ok=True)
    current_deck = load_deck_document(deck_path)
    current_deck_path = deck_path
    final_review_path = output_dir / "review_round_0.json"
    final_patch_path = output_dir / "patches_round_0.json"
    final_pptx_path = output_dir / "review_round_0.pptx"
    final_preview_dir = output_dir / "previews_round_0"

    for round_index in range(1, max_rounds + 1):
        pptx_path = output_dir / f"review_round_{round_index}.pptx"
        log_path = output_dir / f"review_round_{round_index}.log.txt"
        deck_out_path = output_dir / f"review_round_{round_index}.deck.json"
        render_artifacts: RenderArtifacts = generate_ppt(
            current_deck,
            output_path=pptx_path,
            theme_name=theme_name,
            log_path=log_path,
            deck_output_path=deck_out_path,
        )
        if not deck_out_path.exists():
            write_deck_document(render_artifacts.final_deck, deck_out_path)
        preview_dir = output_dir / f"previews_round_{round_index}"
        previews = export_slide_previews(render_artifacts.output_path, preview_dir)
        review_result = review_rendered_deck(render_artifacts.final_deck, previews, model=model)
        review_path = _write_json(review_result, output_dir / f"review_round_{round_index}.json")
        patch_set = generate_blocker_patches(render_artifacts.final_deck, review_result, model=model)
        patch_path = _write_json(patch_set, output_dir / f"patches_round_{round_index}.json")

        final_review_path = review_path
        final_patch_path = patch_path
        final_pptx_path = render_artifacts.output_path
        final_preview_dir = preview_dir

        if not patch_set.get("patches"):
            current_deck = render_artifacts.final_deck
            current_deck_path = deck_out_path
            break

        current_deck = apply_patch_set(render_artifacts.final_deck, patch_set)
        current_deck_path = write_deck_document(current_deck, output_dir / f"review_round_{round_index}_patched.deck.json")

    return VisualReviewArtifacts(
        review_path=final_review_path,
        patch_path=final_patch_path,
        deck_path=current_deck_path,
        pptx_path=final_pptx_path,
        preview_dir=final_preview_dir,
        final_review_path=final_review_path,
        final_patch_path=final_patch_path,
    )


def review_deck_once(
    *,
    deck_path: Path,
    output_dir: Path,
    model: str | None = None,
    theme_name: str | None = None,
) -> SingleReviewArtifacts:
    output_dir.mkdir(parents=True, exist_ok=True)
    deck = load_deck_document(deck_path)
    pptx_path = output_dir / "review_once.pptx"
    log_path = output_dir / "review_once.log.txt"
    deck_out_path = output_dir / "review_once.deck.json"
    render_artifacts = generate_ppt(
        deck,
        output_path=pptx_path,
        theme_name=theme_name,
        log_path=log_path,
        deck_output_path=deck_out_path,
    )
    if not deck_out_path.exists():
        write_deck_document(render_artifacts.final_deck, deck_out_path)
    preview_dir = output_dir / "previews_review_once"
    previews = export_slide_previews(render_artifacts.output_path, preview_dir)
    review_result = review_rendered_deck(render_artifacts.final_deck, previews, model=model)
    review_path = _write_json(review_result, output_dir / "review_once.json")
    patch_set = generate_blocker_patches(render_artifacts.final_deck, review_result, model=model)
    patch_path = _write_json(patch_set, output_dir / "patches_review_once.json")
    return SingleReviewArtifacts(
        review_path=review_path,
        patch_path=patch_path,
        deck_path=deck_out_path,
        pptx_path=render_artifacts.output_path,
        preview_dir=preview_dir,
    )
