#!/usr/bin/env python3
"""Cross-family J-space layer contrast -- per-family, per-layer dose
calibration on FIT rows.

Ported from `j-space-midband-dose-calibration-qwen3-4b/calibrate_dose.py`,
generalized to a `--family` flag and this experiment's own `pipeline.py`
instead of importing the Qwen3-4B predecessor's modules. Method is
IDENTICAL across families: same dose ladder, same usability rule (readback
within tolerance, zero collapse, FIT confab clean_tighten >= min rate),
same selection rule (highest confab clean_tighten, then lower known-correct
cost, then lower dose). Does NOT assume Qwen3-4B's own selected setpoints
(hs23=25, hs26=75, hs29=125, hs34=175) transfer -- each family calibrates
its own ladder on its own FIT rows at its own resolved layers.
"""

from __future__ import annotations

import argparse
import gc
import json
import sys
from pathlib import Path

import torch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from family_config import (  # noqa: E402
    FAMILY_SLUGS, layer_dir_name,
    midband_hs_indices as family_midband_hs_indices,
)
import model_lib as ml  # noqa: E402
import pipeline as pl  # noqa: E402
from family_config import load_family  # noqa: E402

DEFAULT_DOSES = [25.0, 50.0, 75.0, 100.0, 125.0, 150.0, 175.0, 200.0]


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
        key=lambda r: (-r["confab_tighten"]["rate"], r["known_correct_cost_control"]["rate"],
                       r["dose_target"]),
    )[0]


def run(args: argparse.Namespace) -> dict:
    family = args.family
    # MID-BAND candidates only. The late reference arm reuses doubt-snap's
    # frozen direction/gate, but doubt-snap selected NO late-site dose for any
    # family (all G0 dose-viability stops); resolving the late-arm dose is an
    # open question for the lead at sign (see AMENDMENT.md "Open questions at
    # sign" #2). This calibration therefore covers mid-band candidates only.
    hs_list = family_midband_hs_indices(load_family(family))
    analysis = HERE / "analysis" / family
    committed = HERE / "analysis-committed" / family
    analysis.mkdir(parents=True, exist_ok=True)
    committed.mkdir(parents=True, exist_ok=True)

    confab_fit = pl.stratified_subset(pl.load_rows(family, "confab", "fit"), args.n_confab)
    known_fit = pl.stratified_subset(
        pl.load_rows(family, "known_correct_answered", "fit"), args.n_known
    )
    base_rows = confab_fit + known_fit

    model, tokenizer, _hidden_size, _n_layers = ml.load_model_and_tokenizer(family)
    try:
        layers = {}
        for hs_index in hs_list:
            layer_name = layer_dir_name(hs_index)
            gate_rows = pl.compute_gate_decisions(family, base_rows, hs_index)
            results = []
            for dose in args.doses:
                print(f"[calibrate:{family}] layer={layer_name} dose={dose}", flush=True)
                rec = pl.run_layer(family, model, tokenizer, hs_index, gate_rows, dose)
                rec["dose_target"] = dose
                rec["usable"] = dose_is_usable(rec, args.min_confab_rate)
                results.append(rec)
            selected = choose_dose(results, args.min_confab_rate)
            layers[layer_name] = {
                "hs_index": hs_index, "n_confab_fit_rows": len(confab_fit),
                "n_known_fit_rows": len(known_fit), "doses": results,
                "selected_dose": selected["dose_target"] if selected else None,
                "selected": selected, "has_usable_dose": selected is not None,
            }
    finally:
        del model
        gc.collect()
        torch.cuda.empty_cache()

    selected = {name: rec["selected_dose"] for name, rec in layers.items()
                if rec["selected_dose"] is not None}
    summary = {
        "family": family, "mode": "fit_dose_calibration", "calibration_split": "fit",
        "doses": args.doses, "min_confab_rate_for_usable": args.min_confab_rate,
        "layers": layers, "selected_doses": selected,
        "all_layers_have_usable_dose": len(selected) == len(hs_list),
    }

    (analysis / "dose_calibration_summary.json").write_text(json.dumps(summary, indent=2))
    (committed / "dose_calibration_summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))
    return summary


def parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--family", required=True, choices=FAMILY_SLUGS)
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
