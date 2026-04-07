# Cleanup Task List

This file keeps the active cleanup backlog small and explicit so follow-up work can continue without reloading stale context.

## Completed

- Split bundled samples and reference assets into `samples/input`
- Removed unreferenced ad-hoc HTML drafts from the old `input/` directory
- Unified visual review cases through `samples/visual_review_cases.json`
- Standardized default output to repo-local `output/`
- Split active docs from archived reports
- Added `docs/README.md` and archived April 2026 historical reports
- Split legacy HTML regression and V2 regression entrypoints
- Archived obsolete helper scripts under `tools/archive/legacy_helpers`
- Moved domain-specific generators into `tools/scenario_generators`
- Moved review scoring utility into `tools/review_scoring.py`
- Standardized active command examples on `python -m sie_autoppt` or `python main.py`
- Reframed `projects/` as runtime workspace and moved tracked demo notes to archive
- Moved template-related utilities into `tools/template_utils`

## In Progress

- Keep tool and doc indexes in sync with the current structure
- Keep recently moved template utilities healthy after regrouping

## Next

- Decide whether any remaining tiny utilities still deserve active top-level visibility
