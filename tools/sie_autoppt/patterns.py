import json

from .config import PATTERN_FILE


def load_patterns():
    data = json.loads(PATTERN_FILE.read_text(encoding="utf-8"))
    return data.get("patterns", [])


def infer_pattern(title: str, bullets: list[str]) -> str:
    text = f"{title} {' '.join(bullets)}".lower()
    patterns = load_patterns()
    best_id = "general_business"
    best_score = 0
    for p in patterns:
        score = 0
        for kw in p.get("keywords", []):
            if kw.lower() in text:
                score += 1
        if score > best_score:
            best_score = score
            best_id = p.get("id", "general_business")
    return best_id
