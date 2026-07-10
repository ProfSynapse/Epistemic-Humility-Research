#!/usr/bin/env python3
"""Layer-wise dose calibration for J-space mid-band writes.

This consumes the fitted directions and local materialized rows from
`j-space-midband-write-sweep-qwen3-4b`. It does not write row text or
generations. The calibration surface is FIT rows only; HELD-OUT is left for a
later signed contrast that can use the selected setpoints.
"""

from __future__ import annotations

import argparse
import gc
import json
import sys
from pathlib import Path

import torch

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / "j-space-midband-write-sweep-qwen3-4b"
ANALYSIS = HERE / "analysis"
COMMITTED = HERE / "analysis-committed"

if str(SOURCE) not in sys.path:
    sys.path.insert(0, str(SOURCE))

from layers import HS_INDICES, layer_dir_name  # noqa: E402
from model_lib import load_jsonl, load_model  # noqa: E402
from pipeline import compute_gate_decisions, run_layer, stratified_subset  # noqa: E402


DEFAULT_DOSES = [25.0, 50.0, 75.0, 100.0, 125.0, 150.0, 175.0, 200.0]


def load_fit_rows(n_confab: int, n_known: int) -> list[dict]:
    rows_path = SOURCE / "analysis" / "rows_with_text.jsonl"
    if not rows_path.is_file():
        raise FileNotFoundError(
            f"{rows_path} is missing. Materialize the predecessor rows locally "
            "before calibration; row text must remain gitignored."
        )
    rows = load_jsonl(rows_path)
    confab = [r for r in rows if r["role"] == "confab" and r["split"] == "fit"]
    known = [
        r for r in rows
        if r["role"] == "known_correct_answered" and r["split"] == "fit"
    ]
    return stratified_subset(confab, n_confab) + stratified_subset(known, n_known)


def dose_is_usable(rec: dict, min_confab_rate: float) -> bool:
    return bool(
        rec["frac_readback_within_tol"] == 1.0
        and rec["collapse_rate_on_dosed"] == 0.0
        and rec["confab_tighten"]["rate"] >= min_confab_rate
    )


def choose_dose(layer_results: list[dict], min_confab_rate: float) -> dict | None:
    usable = [r for r in layer_results if dose_is_usable(r, min_confab_rate)]
    if not usable:
        return None
    return sorted(
        usable,
        key=lambda r: (
            -r["confab_tighten"]["rate"],
            r["known_correct_cost_control"]["rate"],
            r["dose_target"],
        ),
    )[0]


def run(args: argparse.Namespace) -> dict:
    ANALYSIS.mkdir(parents=True, exist_ok=True)
    COMMITTED.mkdir(parents=True, exist_ok=True)

    base_rows = load_fit_rows(args.n_confab, args.n_known)
    model, tokenizer = load_model()
    try:
        layers = {}
        for hs_index in HS_INDICES:
            layer_name = layer_dir_name(hs_index)
            gate_rows = compute_gate_decisions(base_rows, hs_index)
            results = []
            for dose in args.doses:
                print(f"[calibrate] layer={layer_name} dose={dose}", flush=True)
                rec = run_layer(model, tokenizer, hs_index, gate_rows, dose)
                rec["dose_target"] = dose
                rec["usable"] = dose_is_usable(rec, args.min_confab_rate)
                results.append(rec)
            selected = choose_dose(results, args.min_confab_rate)
            layers[layer_name] = {
                "hs_index": hs_index,
                "n_confab_fit_rows": args.n_confab,
                "n_known_fit_rows": args.n_known,
                "doses": results,
                "selected_dose": selected["dose_target"] if selected else None,
                "selected": selected,
                "has_usable_dose": selected is not None,
            }
    finally:
        del model
        gc.collect()
        torch.cuda.empty_cache()

    selected = {
        name: rec["selected_dose"] for name, rec in layers.items()
        if rec["selected_dose"] is not None
    }
    summary = {
        "mode": "fit_dose_calibration",
        "source_experiment": "j-space-midband-write-sweep-qwen3-4b",
        "calibration_split": "fit",
        "doses": args.doses,
        "min_confab_rate_for_usable": args.min_confab_rate,
        "layers": layers,
        "selected_doses": selected,
        "all_layers_have_usable_dose": len(selected) == len(HS_INDICES),
        "midband_layers_have_usable_dose": all(
            layer_dir_name(h) in selected for h in (23, 26, 29)
        ),
        "collapsed_at_200_recovered": all(
            name in selected and selected[name] < 200.0 for name in ("hs23", "hs26")
        ),
    }

    (ANALYSIS / "dose_calibration_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    (COMMITTED / "dose_calibration_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    print(json.dumps(summary, indent=2))
    return summary


def parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n-confab", type=int, default=8)
    parser.add_argument("--n-known", type=int, default=8)
    parser.add_argument("--doses", type=float, nargs="+", default=DEFAULT_DOSES)
    parser.add_argument("--min-confab-rate", type=float, default=0.5)
    return parser.parse_args(argv)


def main(argv=None) -> int:
    summary = run(parse_args(argv))
    return 0 if summary["all_layers_have_usable_dose"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
