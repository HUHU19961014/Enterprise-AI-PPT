from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path

from tools.scenario_generators.sie_onepage_designer import build_onepage_brief_from_structure, build_onepage_slide

from .clarifier import DEFAULT_AUDIENCE_HINT, clarify_user_input, derive_planning_context, load_clarifier_session
from .clarify_web import serve_clarifier_web
from .cli_parser import build_main_parser
from .cli_sie import handle_pre_v2_command
from .cli_utils import (
    build_template_output_stem,
    emit_progress,
    load_brief_text,
    validate_slide_args,
    write_json_artifact,
)
from .cli_v2_commands import V2CommandContext, handle_v2_and_health_command
from . import cli_routing
from .config import (
    DEFAULT_OUTPUT_DIR,
)
from .deck_spec_io import load_deck_spec
from .exceptions import (
    CliExecutionError,
)
from .healthcheck import run_ai_healthcheck
from .llm_openai import (
    OpenAIConfigurationError,
    OpenAIResponsesError,
)
from .models import StructureSpec
from .structure_service import StructureGenerationRequest, generate_structure_with_ai
from .v2 import (
    build_log_output_path,
    build_ppt_output_path,
    compile_semantic_deck_payload,
    default_deck_output_path,
    default_log_output_path,
    default_outline_output_path,
    default_ppt_output_path,
    default_semantic_output_path,
    generate_outline_with_ai,
    generate_semantic_deck_with_ai,
    generate_semantic_decks_with_ai_batch,
    load_deck_document,
    load_outline_document,
    make_v2_ppt,
    write_deck_document,
    write_outline_document,
    write_semantic_document,
)
from .v2 import (
    generate_ppt as generate_v2_ppt,
)
from .v2.io import DEFAULT_V2_OUTPUT_DIR
from .v2.services import ensure_generation_context
from .v2.visual_review import apply_patch_set, iterate_visual_review, review_deck_once
from .visual_service import generate_visual_draft_artifacts

LOGGER = logging.getLogger(__name__)

WORKFLOW_COMMANDS = (
    "make",
    "onepage",
    "ai-check",
    "clarify",
    "clarify-web",
    "v2-outline",
    "v2-plan",
    "v2-compile",
    "v2-patch",
    "v2-render",
    "v2-make",
    "v2-review",
    "v2-iterate",
    "review",
    "iterate",
    "visual-draft",
)
PRIMARY_COMMANDS = ("make", "review", "iterate")
ADVANCED_COMMANDS = (
    "onepage",
    "v2-plan",
    "v2-render",
    "v2-compile",
    "v2-patch",
    "v2-outline",
    "v2-make",
    "v2-review",
    "v2-iterate",
    "clarify",
    "clarify-web",
    "ai-check",
    "visual-draft",
)
COMMAND_ALIASES = {
    "review": "v2-review",
    "iterate": "v2-iterate",
}
def command_was_explicit(argv: list[str]) -> bool:
    return cli_routing.command_was_explicit(argv, WORKFLOW_COMMANDS)


def normalize_command_alias(command_name: str) -> str:
    return cli_routing.normalize_command_alias(command_name, COMMAND_ALIASES)


def validate_command_name(command_name: str, parser: argparse.ArgumentParser) -> None:
    cli_routing.validate_command_name(
        command_name,
        parser,
        workflow_commands=WORKFLOW_COMMANDS,
        command_aliases=COMMAND_ALIASES,
        primary_commands=PRIMARY_COMMANDS,
        advanced_commands=ADVANCED_COMMANDS,
    )


def resolve_effective_command(argv: list[str], args) -> tuple[str, bool]:
    return cli_routing.resolve_effective_command(
        argv,
        args,
        workflow_commands=WORKFLOW_COMMANDS,
        command_aliases=COMMAND_ALIASES,
    )


def emit_command_notice(explicit: bool, parsed_command: str, effective_command: str) -> None:
    message = cli_routing.emit_command_notice(explicit, parsed_command, effective_command, COMMAND_ALIASES)
    if message:
        print(message, file=sys.stderr)


def option_was_explicit(argv: list[str], option_name: str) -> bool:
    return cli_routing.option_was_explicit(argv, option_name)


def is_v2_command(command_name: str) -> bool:
    return cli_routing.is_v2_command(command_name)


def validate_v2_option_compatibility(
    argv: list[str],
    *,
    effective_command: str,
    parser: argparse.ArgumentParser,
) -> None:
    cli_routing.validate_v2_option_compatibility(argv, effective_command=effective_command, parser=parser)


def validate_delivery_target_compatibility(
    *,
    args,
    explicit_command: bool,
    effective_command: str,
    parser: argparse.ArgumentParser,
) -> None:
    cli_routing.validate_delivery_target_compatibility(
        args=args,
        explicit_command=explicit_command,
        effective_command=effective_command,
        parser=parser,
    )


def resolve_v2_output_dir(*, output_dir: Path, args) -> Path:
    return cli_routing.resolve_v2_output_dir(output_dir=output_dir, args=args)


def resolve_v2_clarified_context(
    args,
    *,
    brief_text: str,
    effective_command: str,
    parser: argparse.ArgumentParser,
) -> tuple[str, str, str, int | None, int | None, int | None, str]:
    if not args.topic.strip():
        return (
            "",
            brief_text,
            args.audience,
            args.chapters,
            args.min_slides,
            args.max_slides,
            args.theme.strip() or "business_red",
        )

    context = derive_planning_context(
        topic=args.topic,
        brief=brief_text,
        audience=args.audience,
        theme=args.theme.strip(),
        chapters=args.chapters,
        min_slides=args.min_slides,
        max_slides=args.max_slides,
        prefer_llm=True,
    )

    if context.requirements.template:
        parser.exit(
            status=1,
            message=(
                "V2 workflows do not support PPTX templates. "
                f"Requested template: {context.requirements.template}. "
                "Use --theme instead.\n"
            ),
        )

    if context.status == "needs_clarification" and not context.skipped:
        parser.exit(
            status=1,
            message=f"Clarification required before '{effective_command}':\n{context.message}\n",
        )

    return (
        context.topic,
        context.brief or brief_text,
        context.audience.strip() or DEFAULT_AUDIENCE_HINT,
        context.chapters,
        context.min_slides,
        context.max_slides,
        args.theme.strip() or context.requirements.theme or "business_red",
    )


def main():
    parser = build_main_parser()
    raw_argv = sys.argv[1:]
    args = parser.parse_args()
    validate_command_name(args.command, parser)
    validate_slide_args(args, parser)
    effective_command, explicit_command = resolve_effective_command(raw_argv, args)
    validate_v2_option_compatibility(raw_argv, effective_command=effective_command, parser=parser)
    validate_delivery_target_compatibility(
        args=args,
        explicit_command=explicit_command,
        effective_command=effective_command,
        parser=parser,
    )
    emit_command_notice(explicit_command, args.command, effective_command)

    # --- CLI AI overrides: patch env vars from --api-key / --base-url / --api-style ---
    _patched_keys: list[str] = []
    cli_api_key = getattr(args, "api_key", "").strip()
    cli_base_url = getattr(args, "base_url", "").strip()
    cli_api_style = getattr(args, "api_style", "").strip()
    if cli_api_key:
        os.environ["OPENAI_API_KEY"] = cli_api_key
        _patched_keys.append("OPENAI_API_KEY")
    if cli_base_url:
        os.environ["OPENAI_BASE_URL"] = cli_base_url
        _patched_keys.append("OPENAI_BASE_URL")
    if cli_api_style:
        os.environ["SIE_AUTOPPT_LLM_API_STYLE"] = cli_api_style
        _patched_keys.append("SIE_AUTOPPT_LLM_API_STYLE")
    if _patched_keys:
        LOGGER.info("CLI AI overrides applied: %s", ", ".join(_patched_keys))
        print(f"[config] AI overrides from CLI: {', '.join(_patched_keys)}", file=sys.stderr)

    output_dir = Path(args.output_dir)
    brief_text = load_brief_text(args.brief, args.brief_file)
    v2_theme = args.theme.strip() or "business_red"
    v2_output_dir = DEFAULT_V2_OUTPUT_DIR if output_dir == DEFAULT_OUTPUT_DIR else output_dir
    v2_output_dir = resolve_v2_output_dir(output_dir=v2_output_dir, args=args)
    resolved_topic = args.topic.strip()
    resolved_brief = brief_text
    resolved_audience = args.audience
    resolved_chapters = args.chapters
    resolved_min_slides = args.min_slides
    resolved_max_slides = args.max_slides

    if effective_command in {"v2-outline", "v2-plan", "v2-make"} and args.topic.strip():
        (
            resolved_topic,
            resolved_brief,
            resolved_audience,
            resolved_chapters,
            resolved_min_slides,
            resolved_max_slides,
            v2_theme,
        ) = resolve_v2_clarified_context(
            args,
            brief_text=brief_text,
            effective_command=effective_command,
            parser=parser,
        )

    if handle_pre_v2_command(
        effective_command=effective_command,
        args=args,
        parser=parser,
        output_dir=output_dir,
        v2_output_dir=v2_output_dir,
        brief_text=brief_text,
        load_clarifier_session=load_clarifier_session,
        clarify_user_input=clarify_user_input,
        serve_clarifier_web=serve_clarifier_web,
        build_template_output_stem=build_template_output_stem,
        emit_progress=emit_progress,
        generate_structure_with_ai=generate_structure_with_ai,
        structure_spec_cls=StructureSpec,
        structure_generation_request_cls=StructureGenerationRequest,
        openai_configuration_error_cls=OpenAIConfigurationError,
        openai_responses_error_cls=OpenAIResponsesError,
        build_onepage_brief_from_structure=build_onepage_brief_from_structure,
        build_onepage_slide=build_onepage_slide,
        write_json_artifact=write_json_artifact,
        load_deck_spec=load_deck_spec,
        generate_visual_draft_artifacts=generate_visual_draft_artifacts,
        cli_execution_error_cls=CliExecutionError,
    ):
        return

    if handle_v2_and_health_command(
        effective_command=effective_command,
        args=args,
        parser=parser,
        context=V2CommandContext(
            resolved_topic=resolved_topic,
            resolved_brief=resolved_brief,
            resolved_audience=resolved_audience,
            resolved_chapters=resolved_chapters,
            resolved_min_slides=resolved_min_slides,
            resolved_max_slides=resolved_max_slides,
            v2_theme=v2_theme,
            v2_output_dir=v2_output_dir,
            brief_text=brief_text,
            emit_progress=emit_progress,
            default_outline_output_path=default_outline_output_path,
            default_semantic_output_path=default_semantic_output_path,
            default_deck_output_path=default_deck_output_path,
            default_log_output_path=default_log_output_path,
            default_ppt_output_path=default_ppt_output_path,
            load_outline_document=load_outline_document,
            write_outline_document=write_outline_document,
            write_semantic_document=write_semantic_document,
            write_deck_document=write_deck_document,
            load_deck_document=load_deck_document,
            compile_semantic_deck_payload=compile_semantic_deck_payload,
            generate_outline_with_ai=generate_outline_with_ai,
            generate_semantic_deck_with_ai=generate_semantic_deck_with_ai,
            generate_semantic_decks_with_ai_batch=generate_semantic_decks_with_ai_batch,
            ensure_generation_context=ensure_generation_context,
            make_v2_ppt=make_v2_ppt,
            generate_v2_ppt=generate_v2_ppt,
            apply_patch_set=apply_patch_set,
            review_deck_once=review_deck_once,
            iterate_visual_review=iterate_visual_review,
            run_ai_healthcheck=run_ai_healthcheck,
        ),
    ):
        return
    parser.error(f"unsupported command '{effective_command}'.")


if __name__ == "__main__":
    main()

