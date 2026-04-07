"""Batch-catalog external PPTX templates for fusion planning."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

try:
    from .import_external_pptx_template import build_import_manifest
except ImportError:  # pragma: no cover - direct script execution
    from import_external_pptx_template import build_import_manifest


def _safe_slug(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9._-]+", "_", value.strip())
    return slug.strip("._") or "template"


def _build_import_dir_name(index: int, pptx_path: Path, source_dir: Path) -> str:
    relative = pptx_path.relative_to(source_dir)
    slug = _safe_slug(relative.stem)
    digest = hashlib.sha1(str(relative).encode("utf-8")).hexdigest()[:8]
    return f"{index:02d}_{slug}_{digest}"


def discover_pptx_files(root: Path) -> list[Path]:
    files = sorted(
        path
        for path in root.rglob("*.pptx")
        if path.is_file() and not path.name.startswith("~$")
    )
    return files


def summarize_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    fusion_hints = manifest["fusionHints"]
    recommended_actions = [item["action"] for item in fusion_hints["recommendedActions"]]
    score = 0
    if fusion_hints["themeReady"]:
        score += 3
    score += len(fusion_hints["referenceStyleCandidates"])
    score += len(manifest["assets"]["commonAssets"])
    score += min(len(manifest["slides"]), 20) // 5
    return {
        "source_name": manifest["source"]["name"],
        "slide_count": len(manifest["slides"]),
        "asset_count": len(manifest["assets"]["allAssets"]),
        "common_asset_count": len(manifest["assets"]["commonAssets"]),
        "theme_ready": fusion_hints["themeReady"],
        "reference_style_candidate_count": len(fusion_hints["referenceStyleCandidates"]),
        "case_library_candidate_count": len(fusion_hints["caseLibraryCandidates"]),
        "recommended_actions": recommended_actions,
        "score": score,
    }


def write_catalog_report(output_path: Path, entries: list[dict[str, Any]]) -> None:
    lines = [
        "# External Template Catalog",
        "",
        "## Summary",
        f"- Templates scanned: {len(entries)}",
        "",
        "## Ranking",
    ]
    for index, entry in enumerate(entries, 1):
        actions = ", ".join(entry["recommended_actions"]) or "none"
        lines.extend(
            [
                f"{index}. {entry['template_name']}",
                f"   - score: {entry['score']}",
                f"   - slides: {entry['slide_count']}, assets: {entry['asset_count']}, common_assets: {entry['common_asset_count']}",
                f"   - theme_ready: {entry['theme_ready']}, reference_candidates: {entry['reference_style_candidate_count']}",
                f"   - actions: {actions}",
                f"   - source: {entry['source_path']}",
                f"   - import_dir: {entry['import_dir']}",
            ]
        )
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_catalog(source_dir: Path, output_dir: Path) -> dict[str, Any]:
    templates = discover_pptx_files(source_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    entries: list[dict[str, Any]] = []
    for index, pptx_path in enumerate(templates, 1):
        import_dir = output_dir / _build_import_dir_name(index, pptx_path, source_dir)
        manifest = build_import_manifest(pptx_path, import_dir)
        (import_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        summary = summarize_manifest(manifest)
        entries.append(
            {
                "template_name": pptx_path.stem,
                "source_path": str(pptx_path),
                "import_dir": str(import_dir),
                **summary,
            }
        )

    entries.sort(
        key=lambda item: (
            -int(item["score"]),
            -int(item["reference_style_candidate_count"]),
            str(item["template_name"]).lower(),
        )
    )

    catalog = {
        "source_dir": str(source_dir),
        "template_count": len(entries),
        "entries": entries,
    }
    (output_dir / "catalog.json").write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_catalog_report(output_dir / "catalog.md", entries)
    return catalog


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Batch-scan external PPTX templates and rank fusion potential.")
    parser.add_argument("source_dir", help="Directory to scan recursively for .pptx files")
    parser.add_argument(
        "-o",
        "--output",
        help="Output directory (default: <source_dir>/template_catalog beside the source dir)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    source_dir = Path(args.source_dir).expanduser().resolve()
    if not source_dir.exists():
        print(f"Error: directory does not exist: {source_dir}")
        return 1
    if not source_dir.is_dir():
        print(f"Error: expected a directory, got: {source_dir}")
        return 1

    output_dir = (
        Path(args.output).expanduser().resolve()
        if args.output
        else source_dir.with_name(f"{source_dir.name}_template_catalog")
    )

    try:
        catalog = build_catalog(source_dir, output_dir)
    except Exception as exc:
        print(f"Error: failed to catalog external templates: {exc}")
        return 1

    print(f"Cataloged templates: {catalog['template_count']}")
    print(f"Output directory: {output_dir}")
    print(f"Catalog files: catalog.json, catalog.md")
    if catalog["entries"]:
        top = catalog["entries"][0]
        print(f"Top candidate: {top['template_name']} (score={top['score']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
