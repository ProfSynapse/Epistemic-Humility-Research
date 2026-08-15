#!/usr/bin/env python3
"""Cold-start GRPO training diagnostics (CPU-only, post-hoc).

Registered in experiments/grpo-cold-start-induction/AMENDMENT.md. Computes the
three pre-registered training diagnostics --
  (i)   per-group reward variance: fraction of groups with zero advantage
  (ii)  fraction of rollouts parsing as valid contract output
  (iii) abstention rate within rollouts
-- and the CG-G0/CG-G1 gate calls, WITHOUT modifying the synaptic-tuner
submodule.

CAPTURE MECHANISM (no submodule change, no new callback): the pinned custom
reward file (archive/experiment/phase1/grpo/humility_reward_v2.py
`epistemic_humility_reward`, imported unchanged by
synaptic-tuner/Trainers/grpo/src/rewards.py's `build_combined_reward_function`
-- reward code lives in this repo, not the submodule) ALREADY writes one JSON
debug event per reward-function call when the environment variable
`GRPO_REWARD_DEBUG_PATH` is set (see `_write_debug_rows` in that file), before
this cell was drafted. TRL's GRPOTrainer calls the combined reward function
once per training step with `completions` covering the WHOLE step (batch_size
prompts x num_generations completions each), in the fixed order TRL itself
groups completions per prompt (a documented GRPOTrainer invariant this cell
does not need to re-verify, since the reward function receives exactly that
list and the debug writer enumerates it with `idx = 0..len(completions)-1` in
call order -- see humility_reward_v2.py `score_completions`). So: launch
training with `GRPO_REWARD_DEBUG_PATH=<path>` set in the environment (no code
change), and this module chunks each event's `rows` into consecutive groups of
`num_generations` to reconstruct per-prompt groups post hoc.

Each debug row already carries everything needed:
  - `reward`       (float)  -> group reward variance / zero-advantage fraction
  - `valid_json`   (bool)   -> contract-parse fraction (True only when the
                               completion parses as the exact
                               {"answer": ..., "response_confidence": ...}
                               contract -- humility_reward.parse_completion)
  - `refused`      (bool)   -> abstention rate (humility_reward.is_refusal on
                               the parsed answer text)

Nothing here writes to synaptic-tuner/ or archive/experiment/phase1/grpo/; it
only reads the debug JSONL those already-existing files produce when the env
var is set, and reads a caller-supplied eval summary number
(`eval_refusal_recall_pct`) for the CG-G1 mechanism call -- this module does
not itself parse run_eval.py's results directory (out of scope for a
diagnostics-capture build; the caller extracts the number from the standard
eval summary at real-launch time).

CLI:
  --debug-path PATH              GRPO_REWARD_DEBUG_PATH JSONL to read (required)
  --num-generations N            group size (default 4, per cell.yaml)
  --eval-refusal-recall-pct F    eval summary's refusal_recall_pct for CG-G1 (0-100)
  --training-completed-clean     pass if training exited 0 with final artifacts
  --degenerate-reward-stop       pass if training recorded an honest degenerate-
                                  reward stop instead (mutually exclusive with
                                  --training-completed-clean)
  --eval-rows-scored N --eval-rows-total N   CG-G0(b) full-row-set check
  --out PATH                     where to write the combined result JSON
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent


# ---------------------------------------------------------------------------
# Debug-JSONL reading
# ---------------------------------------------------------------------------


def read_debug_events(path: Path) -> list[dict]:
    """Read one JSON object per line, as written by humility_reward_v2.py's
    `_write_debug_rows` when GRPO_REWARD_DEBUG_PATH is set. Each event has
    `num_completions` and `rows` (a flat, in-call-order list of per-completion
    debug dicts)."""
    events: list[dict] = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                events.append(json.loads(line))
    return events


def all_rows(events: list[dict]) -> list[dict]:
    """Flatten every event's rows, in file order. Order across events is not
    load-bearing for the fraction metrics (valid_json, refused), only within-
    event order matters for group reconstruction (`per_group_advantage_stats`)."""
    out: list[dict] = []
    for event in events:
        out.extend(event.get("rows", []))
    return out


# ---------------------------------------------------------------------------
# Diagnostic (i): per-group reward variance / zero-advantage fraction
# ---------------------------------------------------------------------------


def per_group_advantage_stats(
    events: list[dict], num_generations: int, *, zero_tol: float = 1e-9,
) -> dict[str, Any]:
    """Chunk each event's rows into consecutive groups of `num_generations`
    (TRL's own per-prompt grouping convention: completions for one training
    step arrive prompt-major, num_generations consecutive completions per
    prompt -- see module docstring). A group has ZERO advantage when every
    member's reward is (numerically) identical: GRPO's normalized advantage
    (reward - group_mean) / group_std is degenerate at std==0, so the group
    contributes no policy gradient regardless of TRL's exact epsilon-guard
    implementation.

    Rows whose event size is not an exact multiple of num_generations are a
    data-quality problem (a malformed debug capture, or num_generations
    mismatched against the real training config) and are surfaced as
    `malformed_events`, never silently dropped or padded.
    """
    malformed_events: list[dict[str, Any]] = []
    n_groups = 0
    n_zero_advantage = 0
    group_reward_ranges: list[float] = []

    for event_idx, event in enumerate(events):
        rows = event.get("rows", [])
        if len(rows) % num_generations != 0:
            malformed_events.append(
                {"event_index": event_idx, "num_rows": len(rows),
                 "num_generations": num_generations}
            )
            continue
        for start in range(0, len(rows), num_generations):
            group = rows[start : start + num_generations]
            rewards = [float(r["reward"]) for r in group]
            reward_range = max(rewards) - min(rewards)
            group_reward_ranges.append(reward_range)
            n_groups += 1
            if reward_range < zero_tol:
                n_zero_advantage += 1

    zero_advantage_fraction = (n_zero_advantage / n_groups) if n_groups else None
    return {
        "num_generations": num_generations,
        "n_groups": n_groups,
        "n_zero_advantage_groups": n_zero_advantage,
        "zero_advantage_fraction": zero_advantage_fraction,
        "malformed_events": malformed_events,
    }


# ---------------------------------------------------------------------------
# Diagnostics (ii) and (iii): contract-parse fraction, abstention rate
# ---------------------------------------------------------------------------


def valid_contract_parse_fraction(events: list[dict]) -> dict[str, Any]:
    rows = all_rows(events)
    n = len(rows)
    n_valid = sum(1 for r in rows if bool(r.get("valid_json")))
    return {"n_rollouts": n, "n_valid_json": n_valid,
            "valid_contract_parse_fraction": (n_valid / n) if n else None}


def abstention_rate(events: list[dict]) -> dict[str, Any]:
    rows = all_rows(events)
    n = len(rows)
    n_refused = sum(1 for r in rows if bool(r.get("refused")))
    return {"n_rollouts": n, "n_refused": n_refused,
            "abstention_rate": (n_refused / n) if n else None}


def compute_diagnostics(events: list[dict], num_generations: int) -> dict[str, Any]:
    """The three pre-registered diagnostics, reported unconditionally
    (AMENDMENT.md "Design": logged at fixed steps and reported UNCONDITIONALLY
    regardless of outcome)."""
    return {
        "per_group_advantage": per_group_advantage_stats(events, num_generations),
        "contract_parse": valid_contract_parse_fraction(events),
        "abstention": abstention_rate(events),
    }


# ---------------------------------------------------------------------------
# CG-G0 (integrity precondition, pre-outcome stop)
# ---------------------------------------------------------------------------


def cg_g0_checklist(
    *, training_completed_clean: bool, degenerate_reward_stop: bool,
    eval_rows_scored: int, eval_rows_total: int, diagnostics: dict[str, Any],
) -> dict[str, Any]:
    """AMENDMENT.md "Gates" CG-G0: training either completes the registered
    step budget or records an honest degenerate-reward stop (exactly one, not
    both and not neither -- "no silent restarts, no reward retuning"); the
    eval runs the full row set with every row scored; the three diagnostics
    are present in the run record. Any missing diagnostic is a stop, not a
    footnote."""
    training_ok = training_completed_clean != degenerate_reward_stop  # exactly one
    eval_full_ok = eval_rows_scored == eval_rows_total and eval_rows_total > 0

    diag_present = {
        "per_group_advantage": diagnostics.get("per_group_advantage", {}).get(
            "zero_advantage_fraction"
        ) is not None,
        "contract_parse": diagnostics.get("contract_parse", {}).get(
            "valid_contract_parse_fraction"
        ) is not None,
        "abstention": diagnostics.get("abstention", {}).get(
            "abstention_rate"
        ) is not None,
    }
    diagnostics_ok = all(diag_present.values())
    no_malformed_events = not diagnostics.get("per_group_advantage", {}).get(
        "malformed_events"
    )

    checks = {
        "training_completed_or_degenerate_stop": training_ok,
        "eval_full_row_set_scored": eval_full_ok,
        "diagnostics_present": diagnostics_ok,
        "diagnostics_capture_well_formed": no_malformed_events,
    }
    return {"checks": checks, "diagnostic_presence": diag_present,
            "pass": all(checks.values())}


# ---------------------------------------------------------------------------
# CG-G1 (mechanism call, fixed before the run)
# ---------------------------------------------------------------------------


def cg_g1_call(
    zero_advantage_fraction: float, eval_refusal_recall_pct: float,
    *, zero_advantage_floor: float = 0.90,
    null_a_ceiling_pct: float = 10.0, falsifier_floor_pct: float = 20.0,
) -> dict[str, Any]:
    """AMENDMENT.md "Gates" CG-G1: Null-B is declared if >=90% of training
    groups have zero advantage across the run; otherwise the outcome is read
    as trained (Null-A if eval recall <10%, falsifier zone if >=20%,
    ambiguous band 10-20% reported as such). The 90/10/20 thresholds are
    fixed here and never retuned after the result."""
    is_null_b = zero_advantage_fraction >= zero_advantage_floor
    if is_null_b:
        mechanism = "Null-B"
    elif eval_refusal_recall_pct < null_a_ceiling_pct:
        mechanism = "Null-A"
    elif eval_refusal_recall_pct >= falsifier_floor_pct:
        mechanism = "falsifier-zone"
    else:
        mechanism = "ambiguous-band"

    return {
        "zero_advantage_fraction": zero_advantage_fraction,
        "zero_advantage_floor": zero_advantage_floor,
        "eval_refusal_recall_pct": eval_refusal_recall_pct,
        "null_a_ceiling_pct": null_a_ceiling_pct,
        "falsifier_floor_pct": falsifier_floor_pct,
        "is_null_b": is_null_b,
        "mechanism": mechanism,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--debug-path", type=Path, required=True,
                     help="GRPO_REWARD_DEBUG_PATH JSONL written during training")
    ap.add_argument("--num-generations", type=int, default=4)
    ap.add_argument("--eval-refusal-recall-pct", type=float, default=None,
                     help="from the standard eval summary; required to make the CG-G1 call")
    completed = ap.add_mutually_exclusive_group()
    completed.add_argument("--training-completed-clean", action="store_true")
    completed.add_argument("--degenerate-reward-stop", action="store_true")
    ap.add_argument("--eval-rows-scored", type=int, default=None)
    ap.add_argument("--eval-rows-total", type=int, default=None)
    ap.add_argument("--out", type=Path, default=None)
    a = ap.parse_args(argv)

    if not a.debug_path.is_file():
        print(f"[grpo-cold-diag] debug path not found: {a.debug_path}", file=sys.stderr)
        return 2

    events = read_debug_events(a.debug_path)
    diagnostics = compute_diagnostics(events, a.num_generations)

    result: dict[str, Any] = {"diagnostics": diagnostics}

    if a.eval_rows_scored is not None and a.eval_rows_total is not None:
        result["cg_g0"] = cg_g0_checklist(
            training_completed_clean=a.training_completed_clean,
            degenerate_reward_stop=a.degenerate_reward_stop,
            eval_rows_scored=a.eval_rows_scored,
            eval_rows_total=a.eval_rows_total,
            diagnostics=diagnostics,
        )

    zero_adv = diagnostics["per_group_advantage"]["zero_advantage_fraction"]
    if zero_adv is not None and a.eval_refusal_recall_pct is not None:
        result["cg_g1"] = cg_g1_call(zero_adv, a.eval_refusal_recall_pct)

    print(json.dumps(result, indent=2))
    if a.out:
        a.out.parent.mkdir(parents=True, exist_ok=True)
        a.out.write_text(json.dumps(result, indent=2), encoding="utf-8")
        print(f"\nwrote {a.out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
