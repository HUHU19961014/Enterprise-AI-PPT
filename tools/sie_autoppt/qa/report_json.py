import json
from pathlib import Path


def write_qa_json_report(result: dict[str, object], pptx_path: Path) -> Path:
    report = pptx_path.with_name(pptx_path.stem + "_QA.json")
    report.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return report
