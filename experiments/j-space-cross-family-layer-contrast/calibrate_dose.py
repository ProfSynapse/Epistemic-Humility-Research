#!/usr/bin/env python3
"""Cross-family J-space layer contrast -- per-family, per-layer dose
calibration on FIT rows.

Ported from `j-space-midband-dose-calibration-qwen3-4b/calibrate_dose.py`,
generalized to a `--family` flag and this experiment's own `pipeline.py`
instead of importing the Qwen3-4B predecessor's modules. Method is
IDENTICAL across families: same usability rule (readback within tolerance,
zero collapse, FIT confab clean_tighten >= min rate), same selection rule
(highest confab clean_tighten, then lower known-correct cost, then lower
ratio). Does NOT assume Qwen3-4B's own selected setpoints (hs23=25, hs26=75,
hs29=125, hs34=175) transfer -- each family calibrates its own ladder on its
own FIT rows at its own resolved layers.

v2 (mid-run revision R2, user-ratified 2026-07-24, AFTER llama/mistral both
stopped at G0 dose-viability under the original absolute ladder): the dose
ladder is NORMALIZED
-- RATIO_LADDER is a fixed set of fractions of each layer's OWN median anchor
L2 norm (computed at runtime from that family's `anchor_extract.safetensors`),
not a fixed absolute-unit ladder. This applies to the llama/mistral
re-calibration and gemma's first calibration alike. The absolute dose for a
(layer, rung) cell is `ratio * median_norm(layer)`. `--doses` remains as an
ABSOLUTE escape hatch: pass it explicitly to reproduce v1 behavior exactly
(no median-norm scaling, resumes from the original v1 checkpoint file). The
default (no `--doses`) path is always the normalized ladder.
"""

from __future__ import annotations

import argparse
import gc
import json
import sys
from pathlib import Path

import numpy as np
import torch
from safetensors.numpy import load_file

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

# Ratified 2026-07-24 (revision R2): 8 geometric rungs, fractions of each layer's median
# anchor L2 norm. Replaces the old fixed-absolute-unit DEFAULT_DOSES ladder
# as the default path; applies uniformly to every family/layer (mid-band AND
# the late-reference arm alike).
RATIO_LADDER = [0.100, 0.153, 0.235, 0.361, 0.554, 0.850, 1.304, 2.000]


def compute_median_norms(family: str, hs_list: list[int]) -> dict[int, float]:
    """Per-layer median anchor L2 norm, over every row this family's
    `anchor_extract.safetensors` holds for that layer (keys are
    `hs<layer>__<safe_row_key>`, per `pipeline.compute_gate_decisions`'s own
    lookup convention). Used to translate the normalized RATIO_LADDER into
    each layer's own absolute dose units."""
    extract_path = HERE / "analysis" / family / "anchor_extract.safetensors"
    tensors = load_file(str(extract_path))
    medians: dict[int, float] = {}
    for hs_index in hs_list:
        prefix = f"hs{hs_index}__"
        norms = [
            float(np.linalg.norm(np.asarray(v, dtype=np.float64)))
            for k, v in tensors.items() if k.startswith(prefix)
        ]
        if not norms:
            raise ValueError(
                f"{family}: no anchor vectors found for hs{hs_index} in {extract_path}"
            )
        medians[hs_index] = float(np.median(norms))
    return medians


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
            -r["confab_tighten"]["rate"], r["known_correct_cost_control"]["rate"],
            # Tie-break on lower RATIO in normalized mode (ratified selection
            # rule); falls back to lower absolute dose in the --doses escape
            # hatch, where there is no ratio. Equivalent within one layer
            # either way since dose = ratio * (that layer's fixed median
            # norm) is monotonic in ratio.
            r["ratio"] if r.get("ratio") is not None else r["dose_target"],
        ),
    )[0]


def _dose_key(layer_name: str, ratio: float | None, dose: float) -> str:
    """Resume key for one (layer, rung) cell. Ratio-mode and absolute-mode
    keys are namespaced apart (distinct prefixes) as defense in depth; the
    primary v1/v2 isolation is the separate checkpoint FILENAME chosen in
    `run()` (see its docstring)."""
    if ratio is not None:
        return f"{layer_name}::ratio={ratio}"
    return f"{layer_name}::abs={dose}"


def load_dose_checkpoint(path: Path) -> dict[str, dict]:
    """Load the per-(layer,dose) checkpoint records: {key -> dose record}."""
    if not path.is_file():
        return {}
    out: dict[str, dict] = {}
    for ln in path.open(encoding="utf-8"):
        if ln.strip():
            obj = json.loads(ln)
            out[obj["key"]] = obj["rec"]
    return out


def append_dose_checkpoint(path: Path, key: str, rec: dict) -> None:
    """Durably append one completed (layer,dose) record before moving on, so a
    kill mid dose-ladder loses at most the in-flight cell, not the whole sweep."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps({"key": key, "rec": rec}, ensure_ascii=False) + "\n")


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

    # v2 normalized ladder (default) vs v1 absolute escape hatch: `--doses`
    # explicitly passed means ABSOLUTE mode (bypasses median-norm scaling
    # entirely, ratio=None everywhere, reproduces v1 byte-for-byte including
    # its checkpoint file). Otherwise NORMALIZED mode: each layer's own
    # median anchor L2 norm (over every row in that family's
    # anchor_extract.safetensors for that layer -- mid-band AND the late arm
    # alike) scales the same RATIO_LADDER (or a caller-supplied --ratios) into
    # that layer's absolute dose units.
    ratio_mode = args.doses is None
    ratios_used = list(args.ratios) if ratio_mode else None
    median_norms = compute_median_norms(family, hs_list) if ratio_mode else {}
    if ratio_mode:
        print(f"[calibrate:{family}] normalized ladder mode: ratios={ratios_used} "
              f"median_norms={{ {', '.join(f'{layer_dir_name(h)}: {median_norms[h]:.4f}' for h in hs_list)} }}",
              flush=True)
    else:
        print(f"[calibrate:{family}] ABSOLUTE dose escape hatch (v1 mode): "
              f"doses={args.doses}", flush=True)

    # layer_ladder[layer_name] = ordered [(absolute_dose, ratio_or_None), ...]
    # -- the single source of truth for both the work queue below and the
    # reconstruction-from-checkpoint pass, so the two can never drift apart.
    layer_ladder: dict[str, list[tuple[float, float | None]]] = {}
    for hs_index in hs_list:
        layer_name = layer_dir_name(hs_index)
        if ratio_mode:
            mn = median_norms[hs_index]
            layer_ladder[layer_name] = [(ratio * mn, ratio) for ratio in ratios_used]
        else:
            layer_ladder[layer_name] = [(dose, None) for dose in args.doses]

    # Kill-resume: the dose ladder is a long per-(layer,dose) GPU generation
    # sweep. Each completed (layer,dose) cell is appended durably to a JSONL
    # checkpoint the moment it finishes, and a resumed run skips cells already
    # recorded (own-JSONL resume, the mine_eval_pool.py pattern). It is keyed by
    # (layer,dose), NOT per-row, because the ladder runs the SAME rows under
    # DIFFERENT doses -- a per-row key would collide across doses (this is the
    # exact reason calibrate_dose was left out of run_contrast.py's per-row
    # RunLog wiring). Resume assumes the same ladder (ratio or absolute,
    # matching the mode that produced the checkpoint); use --fresh to restart.
    # See experiment.yaml instrument.persistence.
    #
    # v1/v2 checkpoint isolation (deliberate choice, not just the key
    # namespacing above): NORMALIZED-mode runs write to a FRESH filename,
    # `calibrate_dose_records_v2.jsonl`. llama/mistral already have a
    # populated `calibrate_dose_records.jsonl` from the old absolute ladder;
    # a fresh filename means that old v1 resume state can never be mistaken
    # for v2 state (or vice versa) even if the per-key namespacing above were
    # ever bypassed. The ABSOLUTE escape hatch intentionally keeps using the
    # original `calibrate_dose_records.jsonl` filename so it still resumes
    # true v1 runs exactly as before.
    ckpt_name = "calibrate_dose_records.jsonl" if not ratio_mode else "calibrate_dose_records_v2.jsonl"
    ckpt_path = analysis / "runlog" / ckpt_name
    if args.fresh and ckpt_path.is_file():
        ckpt_path.unlink()
    done = load_dose_checkpoint(ckpt_path)
    work = [
        (hs, layer_dir_name(hs), dose, ratio)
        for hs in hs_list for dose, ratio in layer_ladder[layer_dir_name(hs)]
    ]
    pending = [w for w in work if _dose_key(w[1], w[3], w[2]) not in done]
    print(f"[calibrate:{family}] {len(done)} (layer,dose) cells done, "
          f"{len(pending)} pending", flush=True)

    model = None
    try:
        gate_cache: dict[int, list] = {}
        for hs_index, layer_name, dose, ratio in pending:
            if model is None:  # load lazily -- a fully-resumed run needs no GPU
                model, tokenizer, _hidden_size, _n_layers = ml.load_model_and_tokenizer(family)
            role = "late_reference_descriptive" if is_late_reference(fam_cfg, hs_index) else "midband"
            if hs_index not in gate_cache:
                gate_cache[hs_index] = pl.compute_gate_decisions(family, base_rows, hs_index)
            print(f"[calibrate:{family}] layer={layer_name} role={role} "
                  f"ratio={ratio} dose={dose}", flush=True)
            rec = pl.run_layer(family, model, tokenizer, hs_index, gate_cache[hs_index], dose)
            rec["dose_target"] = dose
            rec["ratio"] = ratio
            rec["median_norm"] = median_norms.get(hs_index)
            rec["usable"] = dose_is_usable(rec, args.min_confab_rate)
            key = _dose_key(layer_name, ratio, dose)
            append_dose_checkpoint(ckpt_path, key, rec)  # durable before next cell
            done[key] = rec
    finally:
        if model is not None:
            del model
        gc.collect()
        torch.cuda.empty_cache()

    # Reconstruct per-layer results from the checkpoint (the resumable source of
    # truth), then select each layer's dose.
    layers = {}
    for hs_index in hs_list:
        layer_name = layer_dir_name(hs_index)
        is_late = is_late_reference(fam_cfg, hs_index)
        role = "late_reference_descriptive" if is_late else "midband"
        results = [
            done[_dose_key(layer_name, ratio, dose)]
            for dose, ratio in layer_ladder[layer_name]
        ]
        selected = choose_dose(results, args.min_confab_rate)
        layers[layer_name] = {
            "hs_index": hs_index, "role": role,
            "n_confab_fit_rows": len(confab_fit),
            "n_known_fit_rows": len(known_fit),
            "median_norm": median_norms.get(hs_index),
            "doses": results,
            "selected_dose": selected["dose_target"] if selected else None,
            "selected_ratio": (selected.get("ratio") if selected else None),
            "selected": selected, "has_usable_dose": selected is not None,
        }

    selected_all = {name: rec["selected_dose"] for name, rec in layers.items()
                    if rec["selected_dose"] is not None}
    midband_selected = {name: layers[name]["selected_dose"] for name in midband_names
                        if layers[name]["selected_dose"] is not None}
    late_selected_dose = layers[late_name]["selected_dose"]
    summary = {
        "family": family, "mode": "fit_dose_calibration", "calibration_split": "fit",
        "dose_mode": "ratio_normalized" if ratio_mode else "absolute_v1_escape_hatch",
        "ratio_ladder": ratios_used,
        "absolute_doses_arg": args.doses,
        "median_norms": {layer_dir_name(hs): median_norms.get(hs) for hs in hs_list},
        "min_confab_rate_for_usable": args.min_confab_rate,
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
    parser.add_argument(
        "--ratios", type=float, nargs="+", default=RATIO_LADDER,
        help="Normalized dose ladder: fractions of each layer's own median "
             "anchor L2 norm. Ignored if --doses is explicitly given. "
             "Default is the ratified RATIO_LADDER -- do not override for a "
             "signed/confirmatory run.",
    )
    parser.add_argument(
        "--doses", type=float, nargs="+", default=None,
        help="ABSOLUTE dose ladder -- v1 escape hatch. If given, bypasses "
             "ratio/median-norm scaling entirely (ratio=None on every "
             "record) and reproduces v1 behavior exactly, including resuming "
             "from the original calibrate_dose_records.jsonl. Omit this flag "
             "(the default) to use the normalized ladder.",
    )
    parser.add_argument("--min-confab-rate", type=float, default=0.5)
    parser.add_argument("--fresh", action="store_true",
                        help="delete existing dose checkpoint and restart from scratch")
    return parser.parse_args(argv)


def main(argv=None) -> int:
    summary = run(parse_args(argv))
    # Exit status gates on the MID-BAND arm only. The late-reference arm is
    # non-gating/descriptive; a null late dose is an expected outcome, not a
    # calibration failure.
    return 0 if summary["all_midband_have_usable_dose"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
