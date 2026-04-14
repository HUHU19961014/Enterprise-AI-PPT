# CODE_REVIEW v4 Follow-up Status

Updated: 2026-04-14

## Completed

- [x] Dependency cleanup and alignment
  - Removed duplicated `pytest` from `requirements.txt`
  - Raised `openai` lower bound to `>=1.30.0`
  - Added `hypothesis` into `dev` dependencies
- [x] Exception observability hardening
  - Replaced swallow-exception branches with structured logging
- [x] V2 utility deduplication
  - Introduced shared `strip_text`, `normalize_string_list`, `normalize_data_sources`
  - Rewired schema/compiler/router/theme loader to shared helpers
- [x] Pydantic config consolidation
  - Added `AutoPPTBase` with unified `ConfigDict` options
- [x] Layout maintainability improvements
  - Added coordinate-unit guidance
  - Extracted magic offset to named constant
  - Added cached `cards_grid_positions()`
- [x] Renderer signature cleanup
  - Introduced `RenderContext`
  - Unified renderer invocation via context object
- [x] Async capability
  - Added async single-call wrappers
  - Added async batch API in `OpenAIResponsesClient`
  - Added async batch entry points in `visual_score`, `structure_service`, and `v2/services`
- [x] TypedDict-to-Pydantic migration (phase 1)
  - Added pattern payload models
  - Added `validate_body_page_payload()` dispatch
  - Wired validation into `legacy/body_renderers.py`, `deck_spec_io.py`, `legacy/reference_styles.py`, `visual_service.py`
- [x] CI security gate
  - Added `pip-audit` step against `requirements.txt`
- [x] Test hardening
  - Added unit tests for utils, async APIs, renderer mock paths, payload validation dispatch

## In Progress

- [x] TypedDict-to-Pydantic migration (phase 2)
  - Marked legacy `TypedDict` union as `LegacyBodyPagePayload`
  - Switched active `BodyPagePayload` alias to runtime dict + model validation flow
- [x] Async orchestration in CLI multi-request path
  - Added `--batch-size` for `v2-plan`
  - Added async batch generation path via `generate_semantic_decks_with_ai_batch`
  - Added candidate semantic output artifacts (`*.candidate_N.json`)
- [x] Renderer branch test expansion
  - Added mock-based branch tests for section break, title-only, timeline, cards-grid, matrix-grid, title-content timeline path, and title-image placeholder branches
- [x] Normalize boundary test expansion
  - Added `normalize_list` tests for `optional_keys=None` and non-string required value coercion
- [x] Hypothesis schema fuzz tests
  - Added property-based tests for `ThemeMeta` and `OutlineDocument`
- [x] Mypy coverage refinement (phase 1 on legacy/planning)
  - Added `legacy/reference_styles.py`, `planning/deck_planner.py`, and `planning/payload_builders.py` into mypy target set

## Remaining (Optional/Iteration)

- [ ] Full mypy coverage refinement on legacy modules (`legacy/*`, `planning/*`)
