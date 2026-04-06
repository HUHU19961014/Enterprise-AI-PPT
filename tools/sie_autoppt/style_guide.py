from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


_NUMBER_RE = re.compile(r"-?\d+(\.\d+)?")


def _strip_inline_comment(value: str) -> str:
    in_single_quote = False
    in_double_quote = False
    escaped = False

    for index, char in enumerate(value):
        if escaped:
            escaped = False
            continue
        if char == "\\":
            escaped = True
            continue
        if char == "'" and not in_double_quote:
            in_single_quote = not in_single_quote
            continue
        if char == '"' and not in_single_quote:
            in_double_quote = not in_double_quote
            continue
        if char == "#" and not in_single_quote and not in_double_quote:
            if index > 0 and value[index - 1].isspace():
                return value[:index].rstrip()
    return value.strip()


def _coerce_scalar(value: str) -> object:
    text = _strip_inline_comment(value.strip())
    if not text:
        return ""

    lowered = text.lower()
    if lowered in {"true", "false"}:
        return lowered == "true"
    if lowered in {"null", "none"}:
        return None

    if (text.startswith("{") and text.endswith("}")) or (text.startswith("[") and text.endswith("]")):
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

    if len(text) >= 2 and text[0] == text[-1] and text[0] in {"'", '"'}:
        return text[1:-1]

    if "," in text:
        parts = [part.strip() for part in text.split(",") if part.strip()]
        if len(parts) > 1:
            return [_coerce_scalar(part) for part in parts]

    if re.fullmatch(r"-?\d+", text):
        return int(text)
    if _NUMBER_RE.fullmatch(text):
        return float(text)
    return text


def _assign_nested(target: dict[str, Any], dotted_key: str, value: object) -> None:
    parts = [part.strip() for part in dotted_key.split(".") if part.strip()]
    if not parts:
        return
    cursor = target
    for part in parts[:-1]:
        next_value = cursor.get(part)
        if not isinstance(next_value, dict):
            next_value = {}
            cursor[part] = next_value
        cursor = next_value
    cursor[parts[-1]] = value


def _indentation(raw_line: str) -> int:
    return len(raw_line) - len(raw_line.lstrip(" "))


def _dedent_block_lines(lines: list[str]) -> list[str]:
    meaningful = [line for line in lines if line.strip()]
    if not meaningful:
        return []
    min_indent = min(_indentation(line) for line in meaningful)
    return [line[min_indent:] if len(line) >= min_indent else "" for line in lines]


def _collect_indented_block(lines: list[str], start_index: int, parent_indent: int) -> tuple[list[str], int]:
    collected: list[str] = []
    index = start_index
    while index < len(lines):
        raw_line = lines[index]
        stripped = raw_line.strip()
        if not stripped:
            collected.append(raw_line)
            index += 1
            continue
        if stripped.startswith("#"):
            collected.append(raw_line)
            index += 1
            continue
        current_indent = _indentation(raw_line)
        if current_indent <= parent_indent and not stripped.startswith("- "):
            break
        collected.append(raw_line)
        index += 1
    return _dedent_block_lines(collected), index


def _coerce_block_text(lines: list[str], *, folded: bool) -> str:
    cleaned: list[str] = []
    for raw_line in lines:
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#"):
            cleaned.append("")
            continue
        cleaned.append(_strip_inline_comment(raw_line.rstrip()))

    while cleaned and not cleaned[0]:
        cleaned.pop(0)
    while cleaned and not cleaned[-1]:
        cleaned.pop()

    if not cleaned:
        return ""
    if not folded:
        return "\n".join(cleaned)

    paragraphs: list[str] = []
    current: list[str] = []
    for line in cleaned:
        if not line:
            if current:
                paragraphs.append(" ".join(current))
                current = []
            continue
        current.append(line.strip())
    if current:
        paragraphs.append(" ".join(current))
    return "\n\n".join(paragraphs)


def _parse_list_block(lines: list[str]) -> list[object]:
    items: list[object] = []
    for raw_line in lines:
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith("- "):
            items.append(_coerce_scalar(stripped[2:]))
    return items


def _parse_child_block(lines: list[str]) -> object:
    meaningful = [line.strip() for line in lines if line.strip() and not line.strip().startswith("#")]
    if not meaningful:
        return []
    if all(line.startswith("- ") for line in meaningful):
        return _parse_list_block(lines)
    if any(":" in line and not line.startswith("- ") for line in meaningful):
        return _parse_style_guide_lines(lines)
    return _coerce_block_text(lines, folded=False)


def _parse_style_guide_lines(lines: list[str]) -> dict[str, Any]:
    data: dict[str, Any] = {}
    index = 0
    in_code_fence = False

    while index < len(lines):
        raw_line = lines[index]
        stripped = raw_line.strip()

        if stripped.startswith("```"):
            in_code_fence = not in_code_fence
            index += 1
            continue
        if in_code_fence or not stripped or stripped.startswith("#"):
            index += 1
            continue
        if stripped.startswith("- ") or ":" not in stripped:
            index += 1
            continue

        key, value = stripped.split(":", 1)
        normalized_key = key.strip()
        normalized_value = _strip_inline_comment(value.strip())
        if not normalized_key:
            index += 1
            continue

        if normalized_value in {"|", ">"}:
            block_lines, next_index = _collect_indented_block(lines, index + 1, _indentation(raw_line))
            _assign_nested(data, normalized_key, _coerce_block_text(block_lines, folded=normalized_value == ">"))
            index = next_index
            continue

        if normalized_value:
            _assign_nested(data, normalized_key, _coerce_scalar(normalized_value))
            index += 1
            continue

        block_lines, next_index = _collect_indented_block(lines, index + 1, _indentation(raw_line))
        _assign_nested(data, normalized_key, _parse_child_block(block_lines))
        index = next_index

    return data


def parse_style_guide_markdown(style_guide_path: Path) -> dict[str, Any]:
    text = style_guide_path.read_text(encoding="utf-8")
    data = _parse_style_guide_lines(text.splitlines())
    data["raw_text"] = text.strip()
    data["source_path"] = str(style_guide_path)
    return data


def deep_merge_dict(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = deep_merge_dict(merged[key], value)
        else:
            merged[key] = value
    return merged
