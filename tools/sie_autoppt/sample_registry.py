from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SAMPLES_DIR = PROJECT_ROOT / "samples"
INPUT_SAMPLES_DIR = SAMPLES_DIR / "input"
VISUAL_REVIEW_CASES_FILE = SAMPLES_DIR / "visual_review_cases.json"


@dataclass(frozen=True)
class VisualReviewCaseConfig:
    name: str
    label: str
    html: Path
    focus: tuple[str, ...]


def load_visual_review_cases() -> list[VisualReviewCaseConfig]:
    payload = json.loads(VISUAL_REVIEW_CASES_FILE.read_text(encoding="utf-8"))
    return [
        VisualReviewCaseConfig(
            name=str(item["name"]),
            label=str(item["label"]),
            html=(PROJECT_ROOT / str(item["html"])).resolve(),
            focus=tuple(str(entry) for entry in item.get("focus", [])),
        )
        for item in payload
    ]
