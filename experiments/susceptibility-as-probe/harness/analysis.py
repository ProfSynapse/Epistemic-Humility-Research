#!/usr/bin/env python3
"""M2 analysis: joins the three channels (susceptibility, readout,
verbalized confidence) against the role label and computes exactly the
registered quantities (AMENDMENT.md "Analyses", gates.yaml `criteria`).

Order (per AMENDMENT.md Decision record item 5 / gates.yaml S1): readout
sanity FIRST; halt for diagnosis if it fails, before any other criterion is
read. All bootstrap CIs use gates.yaml's ONE registered seed (48260717,
10000 resamples, resampling row indices within role groups); the
cross-fitted combination uses the registered fold seed (48260718, 5 folds).

SC3 coverage: every row's channel coverage enumerated; pairwise-complete
sets recorded (a row with a missing/unparseable confidence value is
excluded from confidence-involving comparisons only, never imputed, per
cell.yaml `channels.verbalized_confidence.unparseable`).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import config  # noqa: E402
import common  # noqa: E402
import stats  # noqa: E402

CAPTURE_DIR = config.EXPERIMENT_DIR / "analysis" / "capture"
ELICIT_DIR = config.EXPERIMENT_DIR / "analysis" / "elicit"
STAGED_MARGIN = config.EXPERIMENT_DIR / "analysis" / "staged_inputs" / config.FAMILY / "margin_dataset" / "qwen35_4b_margin_rows.jsonl"
RESULTS_DIR = config.EXPERIMENT_DIR / "analysis" / "results"


def load_channels() -> dict[str, dict[str, Any]]:
    """row_key -> {role, susceptibility, susceptibility_censored, readout_z,
    confidence, confidence_reason}."""
    margin_rows = common.load_jsonl(STAGED_MARGIN)
    readout_rows = common.load_jsonl(CAPTURE_DIR / "readout_scores.jsonl")
    confidence_rows = common.load_jsonl(ELICIT_DIR / "confidence_scores.jsonl")

    by_key: dict[str, dict[str, Any]] = {}
    for r in margin_rows:
        by_key[r["row_key"]] = {
            "role": r["role"],
            "susceptibility": -float(r["tipping_dose_abs"]),
            "tipping_censored": bool(r["tipping_censored"]),
        }
    for r in readout_rows:
        d = by_key.setdefault(r["row_key"], {"role": r["role"]})
        # Amended cell.yaml (repin 4dc5722c, PI-approved 2026-07-17): readout
        # score is the NEGATIVE z-projection (confab-positive orientation).
        # capture.py persists raw z; the registered score is applied here.
        d["readout_z"] = -float(r["readout_z"])
    for r in confidence_rows:
        d = by_key.setdefault(r["row_key"], {"role": r["role"]})
        d["confidence"] = r["confidence"]
        d["confidence_reason"] = r["parse_reason"]
    return by_key


def coverage_report(by_key: dict[str, dict[str, Any]]) -> dict[str, Any]:
    n = len(by_key)
    has_susc = sum(1 for d in by_key.values() if "susceptibility" in d)
    has_readout = sum(1 for d in by_key.values() if "readout_z" in d)
    has_conf = sum(1 for d in by_key.values() if d.get("confidence") is not None)
    missing_susc = sorted(k for k, d in by_key.items() if "susceptibility" not in d)
    missing_readout = sorted(k for k, d in by_key.items() if "readout_z" not in d)
    missing_conf = sorted(k for k, d in by_key.items() if d.get("confidence") is None)
    all_three = sum(1 for d in by_key.values() if "susceptibility" in d and "readout_z" in d and d.get("confidence") is not None)
    return {
        "n_rows": n,
        "n_with_susceptibility": has_susc, "missing_susceptibility": missing_susc,
        "n_with_readout": has_readout, "missing_readout": missing_readout,
        "n_with_confidence_parsed": has_conf, "missing_or_unparseable_confidence": missing_conf,
        "n_all_three_channels": all_three,
        "pairwise_complete": {
            "susceptibility_vs_readout": sum(1 for d in by_key.values() if "susceptibility" in d and "readout_z" in d),
            "susceptibility_vs_confidence": sum(1 for d in by_key.values() if "susceptibility" in d and d.get("confidence") is not None),
            "readout_vs_confidence": sum(1 for d in by_key.values() if "readout_z" in d and d.get("confidence") is not None),
        },
    }


def _arrays(by_key: dict[str, dict[str, Any]], fields: list[str]) -> tuple[np.ndarray, ...]:
    """Pairwise-complete extraction: rows must have every field in `fields`
    non-missing. labels: role=='confab' -> 1."""
    row_keys = sorted(
        k for k, d in by_key.items()
        if all((d.get(f) is not None if f != "susceptibility" else "susceptibility" in d) for f in fields)
    )
    out = []
    for f in fields:
        out.append(np.array([by_key[k][f] for k in row_keys], dtype=np.float64))
    labels = np.array([1 if by_key[k]["role"] == "confab" else 0 for k in row_keys], dtype=np.int64)
    return row_keys, labels, *out


def main() -> int:
    hashes = config.verify_pinned_hashes()
    if not all(hashes.values()):
        raise SystemExit(f"analysis FAIL: cell.yaml/gates.yaml sha256 mismatch: {hashes}")

    by_key = load_channels()
    if len(by_key) != config.N_POPULATION:
        raise SystemExit(f"analysis FAIL: joined {len(by_key)} rows, expected {config.N_POPULATION}")

    coverage = coverage_report(by_key)
    print(json.dumps({"SC3_coverage": coverage}, indent=2), flush=True)

    elicit_manifest = common.load_json(ELICIT_DIR / "elicitation_manifest.json")
    sc2_parse_rate = elicit_manifest["parse_rate"]
    sc2_pass = elicit_manifest["parse_rate_pass"]
    print(json.dumps({
        "SC2_confidence_parse_rate": sc2_parse_rate,
        "SC2_floor": config.SC2_CONFIDENCE_PARSE_RATE_FLOOR,
        "SC2_pass": sc2_pass,
    }, indent=2), flush=True)

    # ---- S1 readout sanity (FIRST; halt for diagnosis if it fails) --------
    # Sign convention resolved by the PI-approved pre-analysis clarification
    # (cell.yaml repin 4dc5722c, 2026-07-17): the registered readout score is
    # the NEGATIVE z-projection (confab-positive, the lineage's own neg_z
    # convention), applied at load in load_channels(). The raw-polarity AUROC
    # is reported alongside as a diagnostic record of the original halt.
    rk_ro, labels_ro, readout_z = _arrays(by_key, ["readout_z"])
    readout_auroc_ci = stats.bootstrap_auroc_ci(readout_z, labels_ro, n_boot=config.BOOTSTRAP_N_RESAMPLES, seed=config.BOOTSTRAP_SEED)
    readout_auroc_ci_raw_polarity = stats.bootstrap_auroc_ci(-readout_z, labels_ro, n_boot=config.BOOTSTRAP_N_RESAMPLES, seed=config.BOOTSTRAP_SEED)
    s1_pass = readout_auroc_ci["point"] >= config.S1_READOUT_SANITY_FLOOR
    print(json.dumps({
        "S1_readout_sanity": {
            "auroc_point_as_registered": readout_auroc_ci["point"],
            "bootstrap_ci_95_as_registered": readout_auroc_ci["bootstrap_ci_95"],
            "auroc_point_raw_polarity_diagnostic": readout_auroc_ci_raw_polarity["point"],
            "floor": config.S1_READOUT_SANITY_FLOOR, "pass": s1_pass, "n": len(rk_ro),
            "sign_convention_note": (
                "Registered score = negative z per the PI-approved cell.yaml "
                "repin 4dc5722c (2026-07-17), after the original as-drafted "
                "polarity halted S1 at AUROC 0.0179; see NOTEBOOK entries."
            ),
        }
    }, indent=2), flush=True)

    results: dict[str, Any] = {
        "config_hashes_verified": hashes,
        "n_population": config.N_POPULATION,
        "SC3_coverage": coverage,
        "SC2_confidence": {"parse_rate": sc2_parse_rate, "floor": config.SC2_CONFIDENCE_PARSE_RATE_FLOOR, "pass": sc2_pass},
        "S1_readout_sanity": {
            "auroc_as_registered": readout_auroc_ci,
            "auroc_raw_polarity_diagnostic": readout_auroc_ci_raw_polarity,
            "floor": config.S1_READOUT_SANITY_FLOOR, "pass": s1_pass,
            "sign_convention_note": "registered score = negative z per PI-approved cell.yaml repin 4dc5722c (2026-07-17); original as-drafted polarity halted S1 at 0.0179, see NOTEBOOK.",
        },
    }

    if not s1_pass:
        results["halted_after_S1_failure"] = True
        RESULTS_DIR.mkdir(parents=True, exist_ok=True)
        out_path = RESULTS_DIR / "m2_results.json"
        common.write_json(out_path, results)
        print(f"S1 READOUT SANITY FAILED (AUROC {readout_auroc_ci['point']:.4f} < floor {config.S1_READOUT_SANITY_FLOOR}); "
              f"HALTING before any criterion is read, per Decision record item 5 / gates.yaml S1. "
              f"Results written to {out_path} with halted_after_S1_failure=true.", flush=True)
        return 1

    # ---- Per-channel AUROCs (all three) ------------------------------------
    rk_su, labels_su, susceptibility = _arrays(by_key, ["susceptibility"])
    rk_co, labels_co, confidence = _arrays(by_key, ["confidence"])

    susceptibility_auroc = stats.bootstrap_auroc_ci(susceptibility, labels_su, n_boot=config.BOOTSTRAP_N_RESAMPLES, seed=config.BOOTSTRAP_SEED)
    confidence_auroc = stats.bootstrap_auroc_ci(confidence, labels_co, n_boot=config.BOOTSTRAP_N_RESAMPLES, seed=config.BOOTSTRAP_SEED)

    results["channel_aurocs"] = {
        "susceptibility": {**susceptibility_auroc, "n_rows": len(rk_su)},
        "readout": {**readout_auroc_ci, "n_rows": len(rk_ro)},
        "confidence": {**confidence_auroc, "n_rows": len(rk_co)},
    }

    # ---- Sensitivity: susceptibility AUROC excluding tipping-censored -----
    uncensored_keys = [k for k in rk_su if not by_key[k]["tipping_censored"]]
    if uncensored_keys:
        s_unc = np.array([by_key[k]["susceptibility"] for k in uncensored_keys], dtype=np.float64)
        l_unc = np.array([1 if by_key[k]["role"] == "confab" else 0 for k in uncensored_keys], dtype=np.int64)
        sensitivity_auroc = stats.bootstrap_auroc_ci(s_unc, l_unc, n_boot=config.BOOTSTRAP_N_RESAMPLES, seed=config.BOOTSTRAP_SEED)
    else:
        sensitivity_auroc = None
    n_censored = sum(1 for k in rk_su if by_key[k]["tipping_censored"])
    results["susceptibility_censored_excluded_sensitivity"] = {
        "n_censored_excluded": n_censored, "n_uncensored": len(uncensored_keys),
        "auroc": sensitivity_auroc, "descriptive_only": True,
    }

    # ---- Paired differences (pairwise-complete for each pair) --------------
    rk_sr, labels_sr, susc_sr, ro_sr = _arrays(by_key, ["susceptibility", "readout_z"])
    rk_sc, labels_sc, susc_sc, co_sc = _arrays(by_key, ["susceptibility", "confidence"])
    rk_rc, labels_rc, ro_rc, co_rc = _arrays(by_key, ["readout_z", "confidence"])

    margin_vs_readout = stats.bootstrap_paired_diff_ci(susc_sr, ro_sr, labels_sr, n_boot=config.BOOTSTRAP_N_RESAMPLES, seed=config.BOOTSTRAP_SEED)
    margin_vs_confidence = stats.bootstrap_paired_diff_ci(susc_sc, co_sc, labels_sc, n_boot=config.BOOTSTRAP_N_RESAMPLES, seed=config.BOOTSTRAP_SEED)
    readout_vs_confidence = stats.bootstrap_paired_diff_ci(ro_rc, co_rc, labels_rc, n_boot=config.BOOTSTRAP_N_RESAMPLES, seed=config.BOOTSTRAP_SEED)

    results["paired_differences"] = {
        "margin_vs_readout": {**margin_vs_readout, "n_rows": len(rk_sr)},
        "margin_vs_confidence": {**margin_vs_confidence, "n_rows": len(rk_sc)},
        "readout_vs_confidence": {**readout_vs_confidence, "n_rows": len(rk_rc)},
    }

    # ---- P1 complementarity: cross-fitted incremental AUROC ---------------
    incremental = stats.incremental_auroc_ci(
        ro_sr, susc_sr, labels_sr,
        n_folds=config.CROSS_FIT_N_FOLDS, fold_seed=config.CROSS_FIT_FOLD_SEED,
        n_boot=config.BOOTSTRAP_N_RESAMPLES, seed=config.BOOTSTRAP_SEED,
    )
    p1_pass = incremental["incremental_point"] >= config.P1_INCREMENTAL_AUROC_FLOOR
    results["P1_complementarity"] = {
        "incremental": incremental, "floor": config.P1_INCREMENTAL_AUROC_FLOOR,
        "pass": p1_pass, "n_rows": len(rk_sr),
    }

    # ---- P2 channel head-to-heads (convention: excludes zero => wins) -----
    results["P2_channel_head_to_heads"] = {
        "margin_vs_readout": {"winner": "margin" if margin_vs_readout["a_beats_b"] else ("readout" if margin_vs_readout["b_beats_a"] else "no_winner_ci_includes_zero")},
        "margin_vs_confidence": {"winner": "margin" if margin_vs_confidence["a_beats_b"] else ("confidence" if margin_vs_confidence["b_beats_a"] else "no_winner_ci_includes_zero")},
        "readout_vs_confidence": {"winner": "readout" if readout_vs_confidence["a_beats_b"] else ("confidence" if readout_vs_confidence["b_beats_a"] else "no_winner_ci_includes_zero")},
    }

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = RESULTS_DIR / "m2_results.json"
    input_shas = {
        "margin_dataset": common.sha256_of_file(STAGED_MARGIN),
        "readout_scores": common.sha256_of_file(CAPTURE_DIR / "readout_scores.jsonl"),
        "confidence_scores": common.sha256_of_file(ELICIT_DIR / "confidence_scores.jsonl"),
    }
    results["input_file_sha256"] = input_shas
    common.write_json(out_path, results)

    print(json.dumps({k: v for k, v in results.items() if k not in ("SC3_coverage",)}, indent=2, default=str), flush=True)
    print(f"[analysis] results written to {out_path} (sha256={common.sha256_of_file(out_path)})", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
