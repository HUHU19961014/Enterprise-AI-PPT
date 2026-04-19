from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Callable

LOGGER = logging.getLogger(__name__)


def handle_pre_v2_command(
    *,
    effective_command: str,
    args: Any,
    parser: Any,
    output_dir: Path,
    brief_text: str,
    load_clarifier_session: Callable[[str], Any],
    clarify_user_input: Callable[..., Any],
    serve_clarifier_web: Callable[..., Any],
    build_template_output_stem: Callable[[str], str],
    emit_progress: Callable[[bool, str, str], None],
    structure_spec_cls: Any,
    openai_configuration_error_cls: type[Exception],
    openai_responses_error_cls: type[Exception],
    build_onepage_brief_from_structure: Callable[..., Any],
    build_onepage_slide: Callable[..., tuple[Path, Path, Path, Any]],
    write_json_artifact: Callable[[Path, dict[str, Any]], Path],
    load_deck_spec: Callable[[Path], Any],
    generate_visual_draft_artifacts: Callable[..., Any],
    cli_execution_error_cls: type[Exception],
) -> bool:

    if effective_command == "clarify":
        if not args.topic.strip():
            parser.error("--topic is required when command is 'clarify'.")
        existing_session = None
        if args.clarifier_state_file:
            state_path = Path(args.clarifier_state_file)
            if state_path.exists():
                existing_session = load_clarifier_session(state_path.read_text(encoding="utf-8"))
        result = clarify_user_input(
            args.topic,
            session=existing_session,
            original_brief=brief_text,
            model=args.llm_model or None,
        )
        if args.clarifier_state_file:
            Path(args.clarifier_state_file).write_text(result.session.to_json(), encoding="utf-8")
        print(result.to_json())
        return True

    if effective_command == "clarify-web":
        serve_clarifier_web(host=args.host, port=args.port)
        return True

    if effective_command == "onepage":
        parser.error(
            "command 'onepage' has been removed to avoid fixed-template delivery. "
            "Use AI workflows instead: make / v2-plan / v2-make."
        )

    if effective_command == "visual-draft":
        if not args.deck_spec_json.strip():
            parser.error("--deck-spec-json is required when command is 'visual-draft'.")
        try:
            artifacts = generate_visual_draft_artifacts(
                deck_spec=load_deck_spec(Path(args.deck_spec_json)),
                output_dir=output_dir,
                output_name=build_template_output_stem(args.output_name),
                browser_path=args.browser.strip(),
                model=args.llm_model.strip(),
                page_index=max(0, int(args.page_index)),
                layout_hint=args.layout_hint.strip() or "auto",
                with_ai_review=bool(args.with_ai_review),
                visual_rules_path=args.visual_rules_path.strip(),
            )
        except cli_execution_error_cls as exc:
            exit_code = getattr(exc, "exit_code", 1)
            parser.exit(status=exit_code, message=f"visual-draft failed: {exc}\n")
        except Exception as exc:  # pragma: no cover
            parser.exit(status=1, message=f"visual-draft failed: {exc}\n")
        print(str(artifacts.visual_spec_path))
        print(str(artifacts.preview_html_path))
        print(str(artifacts.preview_png_path))
        print(str(artifacts.visual_score_path))
        print(str(artifacts.ai_review_path))
        return True

    return False
