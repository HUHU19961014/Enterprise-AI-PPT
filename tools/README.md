# Tools Index

The `tools/` directory now separates day-to-day entrypoints from archived one-off helpers.

## Primary Entry Points

- `main.py` from the repo root is the preferred no-install local entrypoint
- `run_unit_tests.ps1`: unit and light integration tests
- `legacy_html_regression_check.ps1`: legacy HTML sample regression
- `v2_regression_check.ps1`: V2 deck regression
- `prepare_visual_review.ps1`
- `prepare_visual_review.py`
- `regression_check.ps1`: deprecated compatibility wrapper for legacy HTML regression

## Compatibility Wrappers

- `sie_autoppt_cli.py`: deprecated wrapper kept for older local commands

## Template and Reference Utilities

- Template and reference utilities now live in [`tools/template_utils`](./template_utils/README.md)
- `tools/template_utils/import_external_pptx_template.py`: export assets and fusion hints from external PPTX templates
- `tools/template_utils/catalog_external_templates.py`: batch-scan a template directory and rank fusion candidates
- `review_scoring.py`

## Scenario Generators

- Domain-specific generators now live in [`tools/scenario_generators`](./scenario_generators/README.md)

## Archive

- Legacy one-off helpers live in [`tools/archive/legacy_helpers`](./archive/legacy_helpers/README.md)
