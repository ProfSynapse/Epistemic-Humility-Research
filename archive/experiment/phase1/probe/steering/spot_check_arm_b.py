#!/usr/bin/env python3
"""Aggregate-level equivalence spot check: sequential vs tuner-batched Arm B.

WHY AGGREGATE, NOT PER-ROW: the tuner `batch-generate` verb accepts ONE GLOBAL
--seed (no per-row seeds; the hf-batched engine calls torch.manual_seed once
per micro-batch chunk — verified at the db4f9a3 pin), so batched sampling does
NOT reproduce the sequential per-item RNG streams. Per-row generations are not
expected to match under sampled decode; this script checks the surfaces that
MUST match plus metric-level agreement within binomial noise.

RECIPE (~40-item slice; any GPU run needs explicit user launch approval):

  # 1) sequential reference (small slice via the pool-size knobs)
  python run_arm_b.py --model <M> --direction <direction_gate.json> \\
      --signal gate --position early --eval-pool gate \\
      --n-unknown 20 --n-known 20 --gate-rows <rows.jsonl> \\
      --seed 20260701 --device cuda \\
      --emit-prompts seq_prompts.jsonl --out seq.json
  # 2) batched — SAME args, plus the engine flags
  python run_arm_b.py --model <M> --direction <direction_gate.json> \\
      --signal gate --position early --eval-pool gate \\
      --n-unknown 20 --n-known 20 --gate-rows <rows.jsonl> \\
      --seed 20260701 \\
      --engine tuner-batched --batch-size 16 \\
      --emit-prompts bat_prompts.jsonl --out bat.json
  # 3) compare
  python spot_check_arm_b.py --sequential seq.json --batched bat.json \\
      --emit-sequential seq_prompts.jsonl --emit-batched bat_prompts.jsonl

  (dial cells: --eval-pool dial --n-answerable 40 --position late; add
   --greedy to BOTH runs to also gate revision prompts via
   --gate-revision-prompts.)

CHECKS
  (a) injected notes byte-identical per (variant, row_key) [from cell JSONs].
      Notes embed the probe score at 2 decimals; the batched capture's float
      reduction order can flip a knife-edge rounding, so any waiver must be
      explicit via --max-note-mismatch-rate (default 0.0 = strict).
  (b) prompt token ids byte-identical [from --emit-prompts JSONLs], gated on
      DETERMINISTIC surfaces only: plain initial prompts (late 'shared') must
      always match; injected initial prompts (early) must match wherever the
      note matched. Revision prompts embed generated text and are reported but
      NOT gated under sampled decode (--gate-revision-prompts opts in, for
      greedy runs).
  (c) metric-level agreement within binomial noise: two-proportion z-test
      (|z| <= --z-crit, default 1.96) per variant on abstention (unknown rows),
      answer rate (known rows), accuracy (answerable rows), and revision rate;
      the real-placebo deltas are also compared with a combined-SE z.

Exit 0 = all evaluated gates pass; exit 1 otherwise. CPU-only.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Optional


def _load_cell(path: Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _read_jsonl(path: Path) -> list[dict]:
    rows = []
    with Path(path).open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def _records_by_key(cell: dict, variant: str) -> dict[str, dict]:
    return {r["row_key"]: r for r in cell["items"][variant]}


# ---------------------------------------------------------------------------
# (a) injected notes
# ---------------------------------------------------------------------------

def compare_notes(seq_cell: dict, bat_cell: dict) -> dict:
    n_total = 0
    mismatches: list[dict] = []
    for variant in ("real", "placebo"):
        seq = _records_by_key(seq_cell, variant)
        bat = _records_by_key(bat_cell, variant)
        if set(seq) != set(bat):
            raise ValueError(
                f"{variant} item sets differ between the two cells "
                f"(seq-only={sorted(set(seq) - set(bat))[:3]}, "
                f"bat-only={sorted(set(bat) - set(seq))[:3]}); "
                "the spot check requires the SAME slice under both engines.")
        for key, sr in seq.items():
            n_total += 1
            if sr["injection_note"] != bat[key]["injection_note"]:
                mismatches.append({
                    "variant": variant, "row_key": key,
                    "sequential": sr["injection_note"],
                    "batched": bat[key]["injection_note"],
                })
    rate = (len(mismatches) / n_total) if n_total else 0.0
    return {"n_notes": n_total, "n_mismatched": len(mismatches),
            "mismatch_rate": round(rate, 4), "mismatches": mismatches[:10]}


# ---------------------------------------------------------------------------
# (b) prompt token ids (from --emit-prompts JSONLs)
# ---------------------------------------------------------------------------

def compare_prompt_ids(seq_rows: list[dict], bat_rows: list[dict],
                       gate_revision: bool) -> dict:
    seq_by_id = {r["pass_id"]: r for r in seq_rows}
    bat_by_id = {r["pass_id"]: r for r in bat_rows}
    if set(seq_by_id) != set(bat_by_id):
        raise ValueError(
            "emit-prompts pass_id sets differ between engines "
            f"(seq={len(seq_by_id)}, bat={len(bat_by_id)}); the spot check "
            "requires the same slice, seed, signal, and position.")
    cats = {
        "initial_plain": {"n": 0, "n_mismatched": 0, "gated": True},
        "initial_injected": {"n": 0, "n_mismatched": 0, "gated": True},
        "initial_injected_note_differs": {"n": 0, "n_mismatched": 0,
                                          "gated": False},
        "revision": {"n": 0, "n_mismatched": 0, "gated": gate_revision},
    }
    examples: list[str] = []
    for pid, sr in seq_by_id.items():
        br = bat_by_id[pid]
        if sr["pass_name"] == "initial":
            if sr["note"] is None:
                cat = "initial_plain"
            elif sr["note"] == br["note"]:
                cat = "initial_injected"
            else:
                # The note itself differs (a check-(a) finding); the prompt
                # necessarily differs too — don't double-count it here.
                cat = "initial_injected_note_differs"
        else:
            cat = "revision"
        cats[cat]["n"] += 1
        if sr["prompt_token_ids"] != br["prompt_token_ids"]:
            cats[cat]["n_mismatched"] += 1
            if len(examples) < 5 and cats[cat]["gated"]:
                examples.append(pid)
    gated_mismatches = sum(c["n_mismatched"] for c in cats.values() if c["gated"])
    return {"categories": cats, "gated_mismatches": gated_mismatches,
            "example_gated_mismatches": examples}


# ---------------------------------------------------------------------------
# (c) metric-level agreement within binomial noise
# ---------------------------------------------------------------------------

def _clean(records: list[dict]) -> list[dict]:
    return [r for r in records if not r["final_grade"]["degenerate"]]


def _prop(records: list[dict], select, value) -> tuple[int, Optional[float]]:
    sub = [r for r in records if select(r)]
    if not sub:
        return 0, None
    return len(sub), sum(1 for r in sub if value(r)) / len(sub)


_METRIC_DEFS = {
    "abstention_unknown": (
        lambda r: r["source"] == "selfaware_unknown",
        lambda r: bool(r["final_grade"]["abstained"])),
    "answer_rate_known": (
        lambda r: r["source"] == "selfaware_known",
        lambda r: bool(r["final_grade"]["answered"])),
    "accuracy_answerable": (
        lambda r: r["source"] == "answerable",
        lambda r: bool(r["final_grade"]["correct"])),
    "revision_rate": (
        lambda r: True,
        lambda r: bool(r["revised"])),
}


def _two_prop_z(p1: float, n1: int, p2: float, n2: int) -> float:
    """Pooled two-proportion z statistic (0 when both SE and diff are 0)."""
    pooled = (p1 * n1 + p2 * n2) / (n1 + n2)
    se = math.sqrt(max(pooled * (1.0 - pooled), 0.0) * (1.0 / n1 + 1.0 / n2))
    if se == 0.0:
        return 0.0 if p1 == p2 else float("inf")
    return (p1 - p2) / se


def _binomial_se(p: float, n: int) -> float:
    return math.sqrt(max(p * (1.0 - p), 0.0) / n) if n else 0.0


def compare_metrics(seq_cell: dict, bat_cell: dict, z_crit: float) -> dict:
    out: dict = {"conditions": {}, "deltas": {}, "n_outside_noise": 0}
    per_engine_se: dict = {}
    for metric, (select, value) in _METRIC_DEFS.items():
        for variant in ("real", "placebo"):
            n1, p1 = _prop(_clean(seq_cell["items"][variant]), select, value)
            n2, p2 = _prop(_clean(bat_cell["items"][variant]), select, value)
            key = f"{metric}[{variant}]"
            if p1 is None or p2 is None:
                out["conditions"][key] = {"defined": False}
                continue
            z = _two_prop_z(p1, n1, p2, n2)
            within = abs(z) <= z_crit
            out["conditions"][key] = {
                "defined": True,
                "sequential": round(p1, 4), "n_sequential": n1,
                "batched": round(p2, 4), "n_batched": n2,
                "z": round(z, 3) if math.isfinite(z) else "inf",
                "within_noise": within,
            }
            if not within:
                out["n_outside_noise"] += 1
            per_engine_se.setdefault(metric, {})[variant] = (
                (p1, n1, p2, n2))
        # Real-vs-placebo DELTA agreement (the actual Arm B readout):
        # combined-SE z on (delta_seq - delta_bat).
        if set(per_engine_se.get(metric, {})) == {"real", "placebo"}:
            (p1r, n1r, p2r, n2r) = per_engine_se[metric]["real"]
            (p1p, n1p, p2p, n2p) = per_engine_se[metric]["placebo"]
            d_seq = p1r - p1p
            d_bat = p2r - p2p
            se = math.sqrt(
                _binomial_se(p1r, n1r) ** 2 + _binomial_se(p1p, n1p) ** 2
                + _binomial_se(p2r, n2r) ** 2 + _binomial_se(p2p, n2p) ** 2)
            if se == 0.0:
                z = 0.0 if d_seq == d_bat else float("inf")
            else:
                z = (d_seq - d_bat) / se
            within = abs(z) <= z_crit
            out["deltas"][metric] = {
                "delta_sequential": round(d_seq, 4),
                "delta_batched": round(d_bat, 4),
                "z": round(z, 3) if math.isfinite(z) else "inf",
                "within_noise": within,
            }
            if not within:
                out["n_outside_noise"] += 1
    return out


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args(argv=None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--sequential", required=True, type=Path,
                    help="cell JSON from the sequential-engine slice run")
    ap.add_argument("--batched", required=True, type=Path,
                    help="cell JSON from the tuner-batched slice run")
    ap.add_argument("--emit-sequential", type=Path, default=None,
                    help="--emit-prompts JSONL from the sequential run "
                         "(enables check (b))")
    ap.add_argument("--emit-batched", type=Path, default=None,
                    help="--emit-prompts JSONL from the batched run")
    ap.add_argument("--max-note-mismatch-rate", type=float, default=0.0,
                    help="check (a) gate: allowed fraction of note mismatches "
                         "(knife-edge score-rounding waiver; default 0.0)")
    ap.add_argument("--gate-revision-prompts", action="store_true",
                    help="check (b): also gate revision-pass prompt ids "
                         "(only meaningful for --greedy runs)")
    ap.add_argument("--z-crit", type=float, default=1.96,
                    help="check (c) two-proportion z threshold (default 1.96)")
    ap.add_argument("--out", type=Path, default=None,
                    help="optional path to write the verdict JSON")
    return ap.parse_args(argv)


def main(argv=None) -> int:
    a = parse_args(argv)
    seq_cell = _load_cell(a.sequential)
    bat_cell = _load_cell(a.batched)

    for field in ("signal", "position", "seed", "model", "eval_pool"):
        if seq_cell.get(field) != bat_cell.get(field):
            print(f"[spot_check] FATAL: cells differ on {field!r}: "
                  f"{seq_cell.get(field)!r} vs {bat_cell.get(field)!r}",
                  flush=True)
            return 1

    verdict: dict = {
        "sequential": str(a.sequential),
        "batched": str(a.batched),
        "n_items": seq_cell.get("n_items"),
        "gates": {},
    }

    # (a) notes
    notes = compare_notes(seq_cell, bat_cell)
    gate_a = notes["mismatch_rate"] <= a.max_note_mismatch_rate
    verdict["notes"] = notes
    verdict["gates"]["a_notes_byte_identical"] = gate_a

    # (b) prompt token ids (only when both emit files are supplied)
    if a.emit_sequential and a.emit_batched:
        prompts = compare_prompt_ids(
            _read_jsonl(a.emit_sequential), _read_jsonl(a.emit_batched),
            gate_revision=a.gate_revision_prompts)
        gate_b = prompts["gated_mismatches"] == 0
        verdict["prompt_ids"] = prompts
        verdict["gates"]["b_prompt_ids_deterministic_surfaces"] = gate_b
    else:
        verdict["prompt_ids"] = "SKIPPED (pass --emit-sequential/--emit-batched)"

    # (c) metric-level agreement
    metrics = compare_metrics(seq_cell, bat_cell, a.z_crit)
    gate_c = metrics["n_outside_noise"] == 0
    verdict["metrics"] = metrics
    verdict["gates"]["c_metrics_within_binomial_noise"] = gate_c

    verdict["verdict"] = ("PASS" if all(verdict["gates"].values()) else "FAIL")
    print(json.dumps(verdict, indent=2, ensure_ascii=False), flush=True)
    if a.out:
        a.out.parent.mkdir(parents=True, exist_ok=True)
        a.out.write_text(json.dumps(verdict, indent=2, ensure_ascii=False),
                         encoding="utf-8")
    return 0 if verdict["verdict"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
