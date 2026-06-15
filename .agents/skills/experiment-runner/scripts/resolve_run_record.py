#!/usr/bin/env python3
"""Q3 auto-resolver: aligned_run_record_id from an active-arm adapter path.

Location: .skills/experiment-runner/scripts/resolve_run_record.py (canonical
    source; synced to .claude/ and .agents/ via sync_skills.py).
Purpose (architecture §5): derive the `aligned_run_record_id` a hidden-state
    extraction must link, by reverse-looking-up the active arm's adapter path
    against `experiment/phase1/run_records/<id>.json`'s `outcome.adapter_path`.
    Lives in the RUNNER, not the merged PR #28 harness: the run-record schema is
    a runner concept, and the harness already consumes `aligned_run_record_id`
    FROM its config. So the runner resolves the id and writes it into an
    effective config; the harness stays unchanged (link-never-mutate).

FAIL-CLOSED is the whole point (§5.4, verified against the real 2026-06-14
    records): the two adapter-resolution paths (run record vs eval-config mirror)
    DISAGREE — sft has different timestamps (zero-match), dpo agrees but
    verified=False, kto is absent from the eval config. The resolver NEVER
    guesses: zero-match / ambiguous (multiple) / unverified-only all return
    id=None with a reason, so the gate (E3) SKIPs the cell rather than silently
    linking the wrong or unverified record.

Path normalization (§5.3): run records store `outcome.adapter_path` as a Windows
    ABSOLUTE path (F:\\Code\\...\\final_model). The resolver compares the
    repo-relative POSIX SUFFIX from `synaptic-tuner/toolset-training-artifacts/`
    onward, INCLUDING the timestamp dir, so F:\\ vs /mnt/f host differences are
    sidestepped AND the sft different-timestamp case correctly zero-matches
    (linking the older eval-config adapter to the latest run record would be the
    silent-wrong-link bug this resolver exists to prevent).

This module is pure (stdlib only, no torch/transformers/peft) and GPU-free.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

# The repo-relative anchor that both the run record's adapter_path and the eval
# config's adapter point at. Comparing the suffix FROM this segment onward makes
# the resolver host-agnostic (Windows F:\ vs WSL /mnt/f) — §5.3.
_ARTIFACT_ANCHOR = "synaptic-tuner/toolset-training-artifacts/"


@dataclass
class ResolveResult:
    """Outcome of an adapter -> run-record-id reverse lookup.

    id is None on every fail-closed path (zero-match / ambiguous / unverified);
    `reason` always explains the outcome so the gate can surface a clear SKIP.
    """

    id: Optional[str]
    run_record_path: Optional[Path] = None
    normalized_adapter_path: Optional[str] = None
    reason: str = ""


def normalize_adapter_suffix(adapter_path: str | Path) -> Optional[str]:
    """Return the repo-relative POSIX suffix from the artifact anchor onward.

    - backslashes -> forward slashes (Windows -> POSIX);
    - keep everything from `synaptic-tuner/toolset-training-artifacts/` onward,
      INCLUDING the timestamp dir and the trailing `final_model` (host-agnostic,
      timestamp-exact — §5.3);
    - returns None if the path does not contain the anchor (an unrecognized
      adapter layout cannot be reverse-matched, so the caller fails closed).
    """
    if adapter_path is None:
        return None
    posix = str(adapter_path).replace("\\", "/")
    idx = posix.find(_ARTIFACT_ANCHOR)
    if idx == -1:
        return None
    return posix[idx:]


def _iter_run_records(run_records_dir: Path):
    """Yield (run_record_path, parsed_json) for each *.json directly in the dir.

    Subdirectories (e.g. materialized_recipes/) are intentionally skipped: only
    top-level <id>.json files are run records. Unparseable files are skipped
    (a malformed file must not crash the resolver — it just cannot match).
    """
    if not run_records_dir.is_dir():
        return
    for path in sorted(run_records_dir.glob("*.json")):
        try:
            yield path, json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue


def resolve_aligned_run_record_id(
    *,
    adapter_path: str | Path,
    run_records_dir: Path,
    research_repo_root: Path | None = None,  # deprecated; ignored (see docstring)
    require_verified: bool = True,
) -> ResolveResult:
    """Reverse-lookup the run-record id whose adapter the extraction will load.

    Matching is on the normalized repo-relative suffix (timestamp-exact). Policy:
      * zero matches               -> id=None, reason="no run record ..."  (SKIP)
      * multiple matches           -> id=None, reason="ambiguous: ..."     (SKIP)
      * exactly one match, but
        require_verified and that match's outcome.verified is not True
        or outcome.status != completed
                                   -> id=None, reason="matched <id> but ..." (SKIP)
      * exactly one verified match -> id=<id>                              (LINK)

    `research_repo_root` is DEPRECATED and ignored: the suffix-anchored comparison
    needs only run_records_dir. The parameter is retained as an optional no-op so
    existing callers that still pass it do not break; new callers should omit it.
    """
    target_suffix = normalize_adapter_suffix(adapter_path)
    if target_suffix is None:
        return ResolveResult(
            id=None,
            reason=(
                f"adapter path {adapter_path!r} does not contain the artifact "
                f"anchor {_ARTIFACT_ANCHOR!r}; cannot reverse-match to a run record"
            ),
        )

    matches: list[tuple[str, Path, dict]] = []
    for record_path, record in _iter_run_records(run_records_dir):
        outcome = record.get("outcome") or {}
        record_suffix = normalize_adapter_suffix(outcome.get("adapter_path"))
        if record_suffix is not None and record_suffix == target_suffix:
            run_id = record.get("run_id") or record_path.stem
            matches.append((run_id, record_path, outcome))

    if not matches:
        return ResolveResult(
            id=None,
            normalized_adapter_path=target_suffix,
            reason=(
                f"no run record's outcome.adapter_path matches {target_suffix} "
                f"(the eval-config mirror and run records may have drifted; "
                f"fail-closed rather than link a different-timestamp record)"
            ),
        )

    if len(matches) > 1:
        ids = ", ".join(sorted(m[0] for m in matches))
        return ResolveResult(
            id=None,
            normalized_adapter_path=target_suffix,
            reason=f"ambiguous: {len(matches)} run records match this adapter ({ids})",
        )

    run_id, record_path, outcome = matches[0]
    if require_verified:
        is_verified = outcome.get("verified") is True
        is_completed = outcome.get("status") == "completed"
        if not (is_verified and is_completed):
            return ResolveResult(
                id=None,
                run_record_path=record_path,
                normalized_adapter_path=target_suffix,
                reason=(
                    f"matched {run_id} but outcome is not verified+completed "
                    f"(verified={outcome.get('verified')!r}, "
                    f"status={outcome.get('status')!r}); pass require_verified=False "
                    f"to opt in to an unverified link"
                ),
            )

    return ResolveResult(
        id=run_id,
        run_record_path=record_path,
        normalized_adapter_path=target_suffix,
        reason=f"resolved {run_id} (verified+completed)",
    )
