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
    FAMILY_SLUGS, layer_dir_name, is_late_reference,
    midband_hs_indices as family_midband_hs_indices,
    late_reference_hs as family_late_reference_hs,
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
    fam_cfg = load_family(family)
    # MID-BAND candidates are the calibration's gating target. The late-reference
    # arm is calibrated here TOO (option B, AMENDMENT.md "Open questions at
    # sign" #2, RESOLVED 2026-07-23 lead+user): doubt-snap selected NO late-site
    # dose for any family (all G0 dose-viability stops), so rather than reuse a
    # non-existent dose we recalibrate the late-site scalar dose FRESH here on
    # the reused FIT rows with the SAME ladder as the mid-band arm. The frozen
    # late-site direction/gate are still reused VERBATIM -- pipeline.py branches
    # on the late site to load them; only the scalar dose is recalibrated. A
    # dead late arm (no usable dose) is EXPECTED and non-gating: it does NOT
    # fail calibration; only the mid-band layers gate the exit status.
    midband_hs = family_midband_hs_indices(fam_cfg)
    late_hs = family_late_reference_hs(fam_cfg)
    hs_list = midband_hs + [late_hs]
    midband_names = [layer_dir_name(hs) for hs in midband_hs]
    late_name = layer_dir_name(late_hs)
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
            is_late = is_late_reference(fam_cfg, hs_index)
            role = "late_reference_descriptive" if is_late else "midband"
            gate_rows = pl.compute_gate_decisions(family, base_rows, hs_index)
            results = []
            for dose in args.doses:
                print(f"[calibrate:{family}] layer={layer_name} role={role} dose={dose}", flush=True)
                rec = pl.run_layer(family, model, tokenizer, hs_index, gate_rows, dose)
                rec["dose_target"] = dose
                rec["usable"] = dose_is_usable(rec, args.min_confab_rate)
                results.append(rec)
            selected = choose_dose(results, args.min_confab_rate)
            layers[layer_name] = {
                "hs_index": hs_index, "role": role,
                "n_confab_fit_rows": len(confab_fit),
                "n_known_fit_rows": len(known_fit), "doses": results,
                "selected_dose": selected["dose_target"] if selected else None,
                "selected": selected, "has_usable_dose": selected is not None,
            }
    finally:
        del model
        gc.collect()
        torch.cuda.empty_cache()

    selected_all = {name: rec["selected_dose"] for name, rec in layers.items()
                    if rec["selected_dose"] is not None}
    midband_selected = {name: layers[name]["selected_dose"] for name in midband_names
                        if layers[name]["selected_dose"] is not None}
    late_selected_dose = layers[late_name]["selected_dose"]
    summary = {
        "family": family, "mode": "fit_dose_calibration", "calibration_split": "fit",
        "doses": args.doses, "min_confab_rate_for_usable": args.min_confab_rate,
        "midband_hs_indices": midband_hs, "late_reference_hs": late_hs,
        "layers": layers,
        "selected_doses": selected_all,
        "midband_selected_doses": midband_selected,
        "late_reference_selected_dose": {
            "layer": late_name, "hs_index": late_hs,
            "selected_dose": late_selected_dose,
            "note": ("late arm calibrated fresh with the mid-band ladder (option B, "
                     "non-gating descriptive); frozen late-site direction/gate reused "
                     "verbatim. A null selected_dose means no usable late-site dose was "
                     "found -- expected per doubt-snap's late-site null -- and the late "
                     "arm is then SKIPPED without affecting the primary."),
        },
        # Calibration SUCCESS is defined on the mid-band arm only; the late arm
        # is non-gating and a dead late dose is expected, not a failure.
        "all_midband_have_usable_dose": len(midband_selected) == len(midband_hs),
        "all_layers_have_usable_dose": len(selected_all) == len(hs_list),
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
    # Exit status gates on the MID-BAND arm only. The late-reference arm is
    # non-gating/descriptive; a null late dose is an expected outcome, not a
    # calibration failure.
    return 0 if summary["all_midband_have_usable_dose"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
