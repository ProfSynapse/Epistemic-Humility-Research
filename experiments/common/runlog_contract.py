"""Structural guard: a generation harness cannot silently drop row text.

The data-exhaust build-time rule (`.skills/data-exhaust/SKILL.md`, "Build-time
requirement") says every generation harness MUST persist raw generation text
per row/sample. That rule was procedural only until a booleans-only run log
made a resolved amendment's failure mechanism undiagnosable from committed
artifacts. ``open_generation_runlog`` makes the rule structural: by default it
opens a `RunLog` (`synaptic-tuner/shared/utilities/run_log.py`) that refuses
to accept any record missing non-empty generation text. The only sanctioned
opt-out is an explicit, non-empty `textless_reason` for a harness that
genuinely produces no generation text (e.g. an analysis-only or probe-fit
pass) -- the reason is folded into the log's own run_config so it lands in
the meta fingerprint and stays auditable on disk, never a silent skip.

This module works against the CURRENT synaptic-tuner pin even before that
submodule's `RunLog` gains a native `required_fields` parameter: it
feature-detects the parameter via `inspect.signature` and falls back to an
equivalent client-side check when absent, so the guard is live immediately.
"""

from __future__ import annotations

import inspect
import sys
from pathlib import Path
from typing import Any, Callable

HERE = Path(__file__).resolve().parent            # experiments/common/
REPO_ROOT = HERE.parents[1]                         # repo root
TUNER_DIR = REPO_ROOT / "synaptic-tuner"


class RunlogContractError(RuntimeError):
    """Raised when open_generation_runlog is misused, or (on a tuner
    checkout that predates RunLog.required_fields) when a record is missing
    required generation text."""


def _default_run_log_class() -> type:
    """Import the tuner's RunLog at call time, mirroring the
    ``load_run_log_class`` convention used across experiment ``model_lib.py``
    modules (e.g. ``experiments/gemma4-e4b-kv-seam-quarantine/model_lib.py``)."""
    tuner_str = str(TUNER_DIR)
    if tuner_str not in sys.path:
        sys.path.insert(0, tuner_str)
    try:
        from shared.utilities.run_log import RunLog
    except ImportError as exc:
        raise ImportError(
            "shared.utilities.run_log.RunLog is not available in this "
            "synaptic-tuner checkout. See experiments/common/README-runlog.md "
            "for the consumption convention."
        ) from exc
    return RunLog


def _supports_required_fields(run_log_cls: type) -> bool:
    try:
        sig = inspect.signature(run_log_cls.__init__)
    except (TypeError, ValueError):
        return False
    return "required_fields" in sig.parameters


class _ClientSideRequiredFieldsRunLog:
    """Wraps a RunLog class that does not yet accept ``required_fields`` and
    enforces the same non-empty-string-per-record contract before delegating
    to it, so the guard does not have to wait on the tuner submodule pin to
    advance. Delegates every other attribute/method to the wrapped instance."""

    def __init__(
        self,
        path: Any,
        run_config: dict,
        *,
        required_fields: tuple[str, ...],
        run_log_cls: type,
        **kwargs: Any,
    ) -> None:
        self._required_fields = tuple(required_fields)
        self._inner = run_log_cls(path, run_config, **kwargs)

    def record(self, key: Any, payload: dict) -> None:
        missing = [
            field
            for field in self._required_fields
            if not isinstance(payload.get(field), str) or not payload.get(field)
        ]
        if missing:
            raise RunlogContractError(
                f"record for key {key!r} is missing required field(s) "
                f"{missing}: every record on this run log must carry "
                "non-empty generation text per the data-exhaust build-time "
                "rule (.skills/data-exhaust/SKILL.md); pass a non-empty "
                "textless_reason to open_generation_runlog if this harness "
                "genuinely produces no generation text"
            )
        self._inner.record(key, payload)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._inner, name)

    def __enter__(self) -> "_ClientSideRequiredFieldsRunLog":
        self._inner.__enter__()
        return self

    def __exit__(self, *exc_info: Any) -> None:
        self._inner.__exit__(*exc_info)


def open_generation_runlog(
    path: Any,
    run_config: dict,
    *,
    text_field: str = "out_text",
    textless_reason: str | None = None,
    run_log_cls: Callable[..., Any] | None = None,
) -> Any:
    """Open a RunLog with the data-exhaust text-capture rule enforced.

    ``textless_reason=None`` (the default) requires every record to carry a
    non-empty string at ``text_field``; a missing, non-string, or empty value
    raises. Pass a non-empty ``textless_reason`` string to permit text-free
    records for a harness that genuinely produces no generation text -- the
    reason is folded into ``run_config`` so it is durably recorded in the
    log's own meta fingerprint, never a silent opt-out. Passing an explicit
    empty (or whitespace-only) string for ``textless_reason`` is refused: a
    caller that wants the opt-out must give a real reason, not an empty one.

    ``run_log_cls`` overrides the resolved RunLog class -- used by tests to
    inject a stub without requiring a synaptic-tuner checkout.
    """
    if run_log_cls is None:
        run_log_cls = _default_run_log_class()

    if textless_reason is not None and not textless_reason.strip():
        raise RunlogContractError(
            "textless_reason must be a non-empty, non-whitespace string "
            "when given; pass textless_reason=None (the default) to require "
            "generation text, not an empty string to silently opt out"
        )

    if textless_reason is not None:
        cfg = dict(run_config)
        cfg["textless_reason"] = textless_reason
        return run_log_cls(path, cfg)

    required_fields = (text_field,)
    if _supports_required_fields(run_log_cls):
        return run_log_cls(path, run_config, required_fields=required_fields)
    return _ClientSideRequiredFieldsRunLog(
        path, run_config, required_fields=required_fields, run_log_cls=run_log_cls
    )
