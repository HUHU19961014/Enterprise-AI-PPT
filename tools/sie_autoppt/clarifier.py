from __future__ import annotations

"""
Backward-compatible facade for the clarifier workflow.

The implementation is split across:
- clarifier_models.py: constants, session/result models, serialization helpers
- clarifier_parsing.py: heuristic parsing, pending-question generation, response templates
- clarifier_flow.py: LLM extraction and end-to-end clarification orchestration
"""

from .clarifier_flow import clarify_user_input, derive_planning_context
from .clarifier_models import DEFAULT_AUDIENCE_HINT, ClarifierResult, ClarifierSession, load_clarifier_session

__all__ = [
    "DEFAULT_AUDIENCE_HINT",
    "ClarifierResult",
    "ClarifierSession",
    "clarify_user_input",
    "derive_planning_context",
    "load_clarifier_session",
]
