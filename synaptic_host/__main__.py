"""Prepare neutral ingress before entering the isolated provider launcher."""

from __future__ import annotations

import sys
from pathlib import Path

from .cli import (
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
                prepared, isolated_child_authority=None
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
    except BaseException:
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
