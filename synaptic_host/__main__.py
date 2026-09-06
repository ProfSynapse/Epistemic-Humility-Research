"""Prepare neutral ingress before entering the isolated provider launcher."""

from __future__ import annotations

import sys
from pathlib import Path

from .cli import (
    TrainingRunCommandCodeV2,
    TrainingRunIngressV1,
    bootstrap_unavailable_result_v2,
    dispatch_validated_training_run_v1,
    emit_training_run_result_v2,
    prepare_training_run_ingress_v1,
)


def main(argv: list[str] | None = None) -> int:
    arguments = list(sys.argv[1:] if argv is None else argv)
    project_root = Path(__file__).resolve().parents[1]
    engine_root = project_root / "synaptic-tuner"
    prepared = prepare_training_run_ingress_v1(
        arguments, project_root=project_root, engine_root=engine_root
    )
    if type(prepared) is not TrainingRunIngressV1:
        return emit_training_run_result_v2(prepared)
    if prepared.provider_ref == "docker":
        return emit_training_run_result_v2(
            dispatch_validated_training_run_v1(
                prepared, isolated_child_authority=None,
                project_root=project_root, engine_root=engine_root,
            )
        )
    try:
        from .launcher import ensure_and_reexec

        child = ensure_and_reexec(
            project_root=project_root,
            engine_root=engine_root,
            argv=arguments,
            ingress_digest=prepared.envelope_digest,
            contract_identity_digest=prepared.contract_identity_digest,
        )
    except BaseException as error:
        # B-18 fourth site (section 29.5(b)).  This catch used to leave the
        # exception unbound, unchained and unlogged, so a launcher refusal --
        # `launcher._closed_child_environment` raises "child environment value
        # is invalid" when `launcher._validated_child_environment_value`
        # refuses a value over its 4096-byte bound, which a long operator PATH
        # produces (#432) -- reached the operator as a bare
        # BOOTSTRAP_UNAVAILABLE that named nothing.  Gate G6 requires a
        # refusal to name its own cause.
        #
        # Cited by SYMBOL, not by line.  The section 29 paragraph and #432
        # both cite `launcher.py:628` for this bound; measured here, the byte
        # test is at `:113` inside `_validated_child_environment_value`
        # (`:104-:120`), the raise is at `:143` inside
        # `_closed_child_environment` (`:123-:145`), and `:628` is
        # `python = launcher_python(project_root)`.  Lines move; the symbols
        # are what this comment is about.
        #
        # The result contract does NOT widen: the envelope is what the run
        # driver parses, so the code, the exit status and stdout stay
        # byte-identical and the cause goes to stderr on the mechanism 20.11
        # ruled and 24.4 already uses at `cli.py`'s own bare catch.
        #
        # Imported inside the handler and guarded, by that same convention: a
        # diagnostic that can fail the path it diagnoses is worse than none.
        try:
            from .cause_line import report_cause_line_v1

            report_cause_line_v1(
                error, TrainingRunCommandCodeV2.BOOTSTRAP_UNAVAILABLE,
            )
        except BaseException:
            pass
        return emit_training_run_result_v2(
            bootstrap_unavailable_result_v2(prepared)
        )
    if type(child) is int:
        return child
    return emit_training_run_result_v2(
        dispatch_validated_training_run_v1(
            prepared, isolated_child_authority=child
        )
    )


if __name__ == "__main__":
    raise SystemExit(main())
