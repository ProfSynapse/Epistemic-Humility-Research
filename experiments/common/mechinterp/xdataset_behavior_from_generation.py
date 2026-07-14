#!/usr/bin/env python3
"""Assemble cross-dataset behavior rows from a baseline generation pass (GPU-free).

Step 3 of the cross-dataset-transfer protocol. The baseline generation runner
(mechinterp_head_intervention_runner at alpha=0.0) writes per-row {refused, correct,
label, generated_answer} but no question text and no behavior_cell. This joins
those clean (no-hook) records back to the panel's questions and derives the
canonical 5-way behavior_cell the probes consume:

    known   + refused            -> known_refused          (over-refusal)
    known   + answered + correct -> known_correct_answered
    known   + answered + wrong   -> known_answered_wrong
    unknown + refused            -> unknown_refused         (correct caution)
    unknown + answered           -> unknown_answered_wrong  (hallucination)

Output behavior rows carry probe_pool_row_key + label + behavior_cell + question
(+ aliases, generated_answer, refused, correct) — everything the latent-knowledge
controls / caution-axis probes need on a second dataset.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

# Canonical cells (mirror latent_knowledge_probe constants).
KNOWN_REFUSED = "known_refused"
KNOWN_ANSWERED = "known_correct_answered"
KNOWN_WRONG = "known_answered_wrong"
UNKNOWN_REFUSED = "unknown_refused"
UNKNOWN_WRONG = "unknown_answered_wrong"

BASELINE_ARM = "no_vector_baseline"


class BehaviorAssemblyError(RuntimeError):
    pass


def derive_behavior_cell(label: str, *, refused: bool, correct: bool) -> str:
    if label == "known":
        if refused:
            return KNOWN_REFUSED
        return KNOWN_ANSWERED if correct else KNOWN_WRONG
    if label == "unknown":
        return UNKNOWN_REFUSED if refused else UNKNOWN_WRONG
    raise BehaviorAssemblyError(f"unexpected label {label!r} (want known/unknown)")


def load_panel_questions(panel_rows: Path) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for line in panel_rows.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        rk = r.get("probe_pool_row_key")
        if rk is None:
            continue
        out[rk] = {"question": r.get("question", ""), "aliases": r.get("aliases", [])}
    if not out:
        raise BehaviorAssemblyError(f"no panel rows in {panel_rows}")
    return out


def load_baseline_generation(generation_rows: Path) -> list[dict[str, Any]]:
    """The clean (alpha=0.0 / no_vector_baseline) generation records only."""
    out: list[dict[str, Any]] = []
    for line in generation_rows.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        arm = r.get("arm_id") or r.get("control")
        if arm != BASELINE_ARM:
            continue
        out.append(r)
    if not out:
        raise BehaviorAssemblyError(
            f"no {BASELINE_ARM!r} records in {generation_rows} "
            "(was the sweep run at alpha=0.0?)")
    return out


def assemble(generation_rows: Path, panel_rows: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    questions = load_panel_questions(panel_rows)
    gen = load_baseline_generation(generation_rows)
    rows: list[dict[str, Any]] = []
    missing = 0
    for g in gen:
        rk = g["probe_pool_row_key"]
        label = g["label"]
        refused = bool(g.get("refused"))
        correct = bool(g.get("correct"))
        cell = derive_behavior_cell(label, refused=refused, correct=correct)
        q = questions.get(rk)
        if q is None:
            missing += 1
            continue
        rows.append({
            "probe_pool_row_key": rk,
            "row_key": rk,
            "label": label,
            "behavior_cell": cell,
            "question": q["question"],
            "aliases": q["aliases"],
            "generated_answer": g.get("generated_answer", ""),
            "refused": refused,
            "correct": correct,
        })
    if not rows:
        raise BehaviorAssemblyError("no behavior rows assembled (panel/generation row_keys disjoint?)")
    cells = Counter(r["behavior_cell"] for r in rows)
    summary = {
        "ok": True,
        "n_behavior_rows": len(rows),
        "n_generation_baseline": len(gen),
        "n_missing_question_join": missing,
        "cells": dict(cells),
        "n_known": sum(r["label"] == "known" for r in rows),
        "n_unknown": sum(r["label"] == "unknown" for r in rows),
        "n_known_refused": cells.get(KNOWN_REFUSED, 0),
    }
    return rows, summary


def run(generation_rows: Path, panel_rows: Path, out_dir: Path) -> dict[str, Any]:
    rows, summary = assemble(generation_rows, panel_rows)
    out_dir.mkdir(parents=True, exist_ok=True)
    rows_path = out_dir / "rows.jsonl"
    rows_path.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
    summary["rows"] = str(rows_path)
    (out_dir / "behavior_summary.json").write_text(json.dumps(summary, indent=2) + "\n",
                                                   encoding="utf-8")
    return summary


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--generation", required=True, type=Path, help="generation rows.jsonl")
    p.add_argument("--panel-rows", required=True, type=Path,
                   help="panel gen_rows.jsonl (for question + aliases join)")
    p.add_argument("--out-dir", required=True, type=Path)
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    summary = run(args.generation, args.panel_rows, args.out_dir)
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
