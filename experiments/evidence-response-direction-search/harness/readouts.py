#!/usr/bin/env python3
"""CPU readouts for evidence-response-direction-search (M4c). Step 5 of the
execution sequence: rung (a) primary, rung (c) primary companion (both null
flavors + native/KUQ comparators), the ungated KUQ transfer readout, and the
refused-row auxiliary construct-context reading. Rung (b) (GPU, conditional)
is explicitly OUT OF SCOPE and never touched here.

No model loading, no GPU. Writes `analysis-committed/results/m4c_results.json`
(aggregates only) and `analysis-committed/results/heldout_projections.jsonl`
(row_key, role, baseline__d_ev_z -- no text, per the reusable-artifact
manifest).
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import config  # noqa: E402
import common  # noqa: E402
import tensors  # noqa: E402
import stats  # noqa: E402

COMMITTED = config.EXPERIMENT_DIR / "analysis-committed"
SELECTION_DIR = COMMITTED / "selection"
DIRECTIONS_DIR = COMMITTED / "directions" / "hs20"
RESULTS_DIR = COMMITTED / "results"


def _load_row_keys() -> dict:
    split = common.load_json(SELECTION_DIR / "fit_heldout_split.json")
    test_pop = common.load_json(config.TEST_POPULATION_PATH)
    fit_confab = sorted(split["fit_row_keys"])
    held_out_confab = sorted(split["held_out_row_keys"])
    correct = sorted(test_pop["row_keys"]["correct"])
    refused = sorted(test_pop["row_keys"]["refused"])

    # SC3: fit/held-out disjointness re-asserted against committed id-lists.
    if set(fit_confab) & set(held_out_confab):
        raise SystemExit("readouts FAIL (SC3): fit/held-out confab overlap detected")
    if len(fit_confab) != config.N_FIT or len(held_out_confab) != config.N_HELD_OUT:
        raise SystemExit(f"readouts FAIL (SC3): fit={len(fit_confab)} held_out={len(held_out_confab)} != {config.N_FIT}/{config.N_HELD_OUT}")
    if len(correct) != 360:
        raise SystemExit(f"readouts FAIL (SC3): correct-control n={len(correct)} != 360")
    if len(refused) != 241:
        raise SystemExit(f"readouts FAIL (SC3): refused n={len(refused)} != 241")
    # correct-control never in fit (decision record item 3)
    if set(correct) & set(fit_confab):
        raise SystemExit("readouts FAIL (SC3): correct-control rows found in the FIT split")

    return {"fit_confab": fit_confab, "held_out_confab": held_out_confab, "correct": correct, "refused": refused}


def _load_d_ev() -> np.ndarray:
    record = common.load_json(DIRECTIONS_DIR / "d_ev.json")
    return np.asarray(record["vector"], dtype=np.float64)


def _load_top_pc() -> np.ndarray:
    record = common.load_json(DIRECTIONS_DIR / "d_ev_topPC.json")
    return np.asarray(record["vector"], dtype=np.float64)


def _load_native_vector() -> np.ndarray:
    record = common.load_json(config.C_HAT_WORLDKNOWN_PATH)
    return np.asarray(record["vector"], dtype=np.float64)


def _load_kuq_vector() -> np.ndarray:
    record = common.load_json(config.KUQ_CHAT_PATH)
    return np.asarray(record["vector"], dtype=np.float64)


def _score(anchors: np.ndarray, direction: np.ndarray) -> np.ndarray:
    """Registered confab-positive score: -(h . direction)."""
    return -(anchors @ direction)


def rung_a_and_native_kuq(row_keys: dict, d_ev: np.ndarray, top_pc: np.ndarray) -> dict:
    held_out_confab = row_keys["held_out_confab"]
    correct = row_keys["correct"]
    all_keys = held_out_confab + correct
    labels = np.array([1] * len(held_out_confab) + [0] * len(correct), dtype=int)

    h_baseline = tensors.load_anchors("no_answer_baseline", all_keys)  # (560, 2560)

    score_d_ev = _score(h_baseline, d_ev)
    score_top_pc = _score(h_baseline, top_pc)
    native_vec = _load_native_vector()
    score_native = _score(h_baseline, native_vec)
    kuq_vec = _load_kuq_vector()
    score_kuq = _score(h_baseline, kuq_vec)

    rung_a_d_ev = stats.bootstrap_ci_covers_point5(score_d_ev, labels, n_boot=config.N_BOOT, seed=config.BOOTSTRAP_SEED)
    rung_a_top_pc = stats.bootstrap_ci_covers_point5(score_top_pc, labels, n_boot=config.N_BOOT, seed=config.BOOTSTRAP_SEED)
    native_recomputed = stats.bootstrap_auroc_ci(score_native, labels, n_boot=config.N_BOOT, seed=config.BOOTSTRAP_SEED)
    kuq_recomputed = stats.bootstrap_auroc_ci(score_kuq, labels, n_boot=config.N_BOOT, seed=config.BOOTSTRAP_SEED)

    paired_diff_native = stats.bootstrap_paired_auroc_diff_ci(score_d_ev, score_native, labels, n_boot=config.N_BOOT, seed=config.BOOTSTRAP_SEED)
    paired_diff_kuq = stats.bootstrap_paired_auroc_diff_ci(score_d_ev, score_kuq, labels, n_boot=config.N_BOOT, seed=config.BOOTSTRAP_SEED)
    paired_diff_topPC_vs_dev = stats.bootstrap_paired_auroc_diff_ci(score_top_pc, score_d_ev, labels, n_boot=config.N_BOOT, seed=config.BOOTSTRAP_SEED)

    d_a_pass = rung_a_d_ev["point"] >= config.RUNG_A_AUROC_FLOOR
    strong_pass_native = paired_diff_native["bootstrap_ci_95"][0] >= config.NATIVE_COMPARATOR_STRONG_BAR_LOWER_CI

    return {
        "rung_a_primary": {
            "auroc": rung_a_d_ev,
            "floor": config.RUNG_A_AUROC_FLOOR,
            "point_estimate_ge_floor": bool(d_a_pass),
            "falsifier_branch": {
                "a1_ci_covers_0p5_no_baseline_content": rung_a_d_ev["ci_covers_0p5"] if not d_a_pass else None,
                "a2_ci_excludes_0p5_from_below_reversed_orientation": rung_a_d_ev["ci_excludes_0p5_from_below"] if not d_a_pass else None,
                "applicable": not d_a_pass,
            },
        },
        "rung_a_secondary_top_pc_report_only": {
            "auroc": rung_a_top_pc,
            "floor_reference_only": config.RUNG_A_AUROC_FLOOR,
            "point_estimate_ge_floor": bool(rung_a_top_pc["point"] >= config.RUNG_A_AUROC_FLOOR),
        },
        "native_comparator": {
            "recomputed_on_identical_heldout_rows": native_recomputed,
            "full_population_reference_anchor_only": config.C_HAT_WORLDKNOWN_BASELINE_AUROC_REFERENCE,
            "paired_auroc_diff_d_ev_minus_native": paired_diff_native,
            "strong_bar_lower_ci_floor": config.NATIVE_COMPARATOR_STRONG_BAR_LOWER_CI,
            "strong_bar_pass": bool(strong_pass_native),
        },
        "kuq_comparator_lower_ungated": {
            "recomputed_on_identical_heldout_rows": kuq_recomputed,
            "amendment_cited_population_reference": config.KUQ_CHAT_BASELINE_AUROC_REFERENCE,
            "paired_auroc_diff_d_ev_minus_kuq": paired_diff_kuq,
            "note": "ungated; reported for context per AMENDMENT rung-c lower comparator",
        },
        "top_pc_vs_primary_paired_auroc_diff": paired_diff_topPC_vs_dev,
        "n_held_out_confab": len(held_out_confab),
        "n_correct_control": len(correct),
        "_row_level": {
            "row_keys": all_keys,
            "roles": (["confab"] * len(held_out_confab)) + (["correct_on_answerable"] * len(correct)),
            "score_d_ev": score_d_ev,
            "score_top_pc": score_top_pc,
        },
    }


def rung_c_null(row_keys: dict, d_ev: np.ndarray, rung_a_auroc_point: float, top_pc_auroc_point: float) -> dict:
    held_out_confab = row_keys["held_out_confab"]
    correct = row_keys["correct"]
    all_keys = held_out_confab + correct
    labels = np.array([1] * len(held_out_confab) + [0] * len(correct), dtype=int)
    h_baseline = tensors.load_anchors("no_answer_baseline", all_keys)  # (560, 2560)

    n, d = h_baseline.shape
    centered = h_baseline - h_baseline.mean(axis=0)

    def _null_aurocs(directions: np.ndarray) -> np.ndarray:
        # directions: (K, hidden_dim) unit vectors
        scores_all = -(h_baseline @ directions.T)  # (n, K)
        aurocs = np.empty(directions.shape[0], dtype=np.float64)
        for k in range(directions.shape[0]):
            aurocs[k] = stats.auroc(scores_all[:, k], labels)
        return aurocs

    # Covariance-shaped null: draw z ~ N(0, I_n), project v = centered.T @ z
    # (equivalent to drawing from N(0, Sigma_hat) with Sigma_hat = centered.T
    # @ centered / (n-1), up to an irrelevant scalar that cancels under unit
    # normalization). Disclosed conservative (m-1): carries between-class
    # structure.
    rng_cov = np.random.default_rng(config.RANDOM_NULL_SEED)
    z = rng_cov.standard_normal(size=(config.K_NULL, n))
    raw_dirs_cov = z @ centered  # (K, hidden_dim)
    norms = np.linalg.norm(raw_dirs_cov, axis=1, keepdims=True)
    unit_dirs_cov = raw_dirs_cov / norms
    null_aurocs_cov = _null_aurocs(unit_dirs_cov)

    # Isotropic null companion (ungated): draw directly from N(0, I_d).
    rng_iso = np.random.default_rng(config.RANDOM_NULL_SEED)
    raw_dirs_iso = rng_iso.standard_normal(size=(config.K_NULL, d))
    unit_dirs_iso = raw_dirs_iso / np.linalg.norm(raw_dirs_iso, axis=1, keepdims=True)
    null_aurocs_iso = _null_aurocs(unit_dirs_iso)

    def _null_summary(null_aurocs: np.ndarray, point_auroc: float) -> dict:
        p95 = float(np.percentile(null_aurocs, 95))
        p_value = float(np.mean(null_aurocs >= point_auroc))
        return {
            "k": len(null_aurocs),
            "null_auroc_mean": float(null_aurocs.mean()),
            "null_auroc_std": float(null_aurocs.std()),
            "null_95th_percentile": p95,
            "point_auroc": point_auroc,
            "point_exceeds_95th_percentile": bool(point_auroc > p95),
            "empirical_p_value_ge": p_value,
            "p_lt_0p05_pass": bool(p_value < config.NULL_PERCENTILE_ALPHA),
        }

    return {
        "covariance_shaped_null_D_c_gated": {
            "seed": config.RANDOM_NULL_SEED,
            "method": "z ~ N(0, I_n), v = centered_baseline_anchors.T @ z, unit-normalized (equivalent to N(0, empirical covariance) up to a scalar); n=560 (200 held-out confab + 360 correct-control), K=1000",
            **_null_summary(null_aurocs_cov, rung_a_auroc_point),
        },
        "isotropic_null_ungated_companion": {
            "seed": config.RANDOM_NULL_SEED,
            "method": "v ~ N(0, I_2560), unit-normalized, K=1000, independent generator instance from the covariance-shaped draw",
            **_null_summary(null_aurocs_iso, rung_a_auroc_point),
        },
        "top_pc_secondary_vs_covariance_null_report_only": _null_summary(null_aurocs_cov, top_pc_auroc_point),
    }


def refused_auxiliary(row_keys: dict, d_ev: np.ndarray) -> dict:
    refused = row_keys["refused"]
    correct = row_keys["correct"]
    held_out_confab = row_keys["held_out_confab"]
    h_refused = tensors.load_anchors("no_answer_baseline", refused)
    h_correct = tensors.load_anchors("no_answer_baseline", correct)
    h_confab = tensors.load_anchors("no_answer_baseline", held_out_confab)

    score_refused = _score(h_refused, d_ev)
    score_correct = _score(h_correct, d_ev)
    score_confab = _score(h_confab, d_ev)

    labels_refused_vs_correct = np.array([1] * len(refused) + [0] * len(correct), dtype=int)
    scores_refused_vs_correct = np.concatenate([score_refused, score_correct])
    labels_confab_vs_refused = np.array([1] * len(held_out_confab) + [0] * len(refused), dtype=int)
    scores_confab_vs_refused = np.concatenate([score_confab, score_refused])

    return {
        "n_refused": len(refused),
        "score_distribution": {
            "mean": float(score_refused.mean()), "std": float(score_refused.std()), "median": float(np.median(score_refused)),
        },
        "auroc_refused_vs_correct": stats.auroc(scores_refused_vs_correct, labels_refused_vs_correct),
        "auroc_confab_vs_refused": stats.auroc(scores_confab_vs_refused, labels_confab_vs_refused),
        "note": "construct context only, not gated (AMENDMENT: refused rows reported as auxiliary readout)",
    }


def kuq_transfer(d_ev: np.ndarray) -> dict:
    if not config.KUQ_ANCHOR_EXTRACT_PATH.is_file() or not config.KUQ_ANCHOR_MANIFEST_PATH.is_file():
        raise SystemExit("readouts FAIL: KUQ doubt-snap anchor_extract inputs missing at readout time")
    from safetensors import safe_open

    manifest = common.load_json(config.KUQ_ANCHOR_MANIFEST_PATH)
    rows_by_role: dict[str, list[str]] = {}
    key_by_row: dict[str, str] = {}
    for r in manifest["rows"]:
        rows_by_role.setdefault(r["role"], []).append(r["row_key"])
        key_by_row[r["row_key"]] = config.KUQ_ANCHOR_HS_KEY_PREFIX + r["safetensors_key"]

    confab_keys = sorted(rows_by_role.get(config.KUQ_ROLE_CONFAB, []))
    correct_keys = sorted(rows_by_role.get(config.KUQ_ROLE_CORRECT, []))
    if not confab_keys or not correct_keys:
        raise SystemExit(f"readouts FAIL: KUQ transfer readout has empty role population (confab={len(confab_keys)}, correct={len(correct_keys)})")

    with safe_open(str(config.KUQ_ANCHOR_EXTRACT_PATH), framework="numpy") as f:
        h_confab = np.stack([np.asarray(f.get_tensor(key_by_row[rk]), dtype=np.float64) for rk in confab_keys])
        h_correct = np.stack([np.asarray(f.get_tensor(key_by_row[rk]), dtype=np.float64) for rk in correct_keys])

    score_confab = _score(h_confab, d_ev)
    score_correct = _score(h_correct, d_ev)
    labels = np.array([1] * len(confab_keys) + [0] * len(correct_keys), dtype=int)
    scores = np.concatenate([score_confab, score_correct])
    result = stats.bootstrap_auroc_ci(scores, labels, n_boot=config.N_BOOT, seed=config.BOOTSTRAP_SEED)
    return {
        "n_confab": len(confab_keys), "n_correct": len(correct_keys),
        "auroc": result,
        "note": "ungated exploratory readout; a positive result is a bonus cross-population transfer, a null is expected given the population shift",
    }


def main() -> int:
    config.assert_pinned_hashes()

    row_keys = _load_row_keys()
    print(f"[readouts] SC3 coverage check PASS: fit={len(row_keys['fit_confab'])} held_out_confab={len(row_keys['held_out_confab'])} correct={len(row_keys['correct'])} refused={len(row_keys['refused'])}", flush=True)

    d_ev = _load_d_ev()
    top_pc = _load_top_pc()

    print("[readouts] rung (a) + native/KUQ comparators (recomputed on identical held-out rows)...", flush=True)
    rung_a = rung_a_and_native_kuq(row_keys, d_ev, top_pc)
    row_level = rung_a.pop("_row_level")
    print(f"[readouts] rung (a) D_a point AUROC={rung_a['rung_a_primary']['auroc']['point']:.6f} CI={rung_a['rung_a_primary']['auroc']['bootstrap_ci_95']}", flush=True)

    print("[readouts] rung (c) covariance-shaped + isotropic null...", flush=True)
    rung_c = rung_c_null(
        row_keys, d_ev,
        rung_a_auroc_point=rung_a["rung_a_primary"]["auroc"]["point"],
        top_pc_auroc_point=rung_a["rung_a_secondary_top_pc_report_only"]["auroc"]["point"],
    )
    print(f"[readouts] rung (c) covariance-null 95th pct={rung_c['covariance_shaped_null_D_c_gated']['null_95th_percentile']:.6f} point_exceeds={rung_c['covariance_shaped_null_D_c_gated']['point_exceeds_95th_percentile']}", flush=True)

    print("[readouts] refused-row auxiliary readout...", flush=True)
    refused_aux = refused_auxiliary(row_keys, d_ev)

    print("[readouts] KUQ transfer readout (ungated)...", flush=True)
    kuq = kuq_transfer(d_ev)
    print(f"[readouts] KUQ transfer AUROC={kuq['auroc']['point']:.6f} CI={kuq['auroc']['bootstrap_ci_95']}", flush=True)

    results = {
        "provenance": {
            "d_ev_sha256": common.sha256_of_file(DIRECTIONS_DIR / "d_ev.json"),
            "d_ev_topPC_sha256": common.sha256_of_file(DIRECTIONS_DIR / "d_ev_topPC.json"),
            "fit_heldout_split_sha256": common.sha256_of_file(SELECTION_DIR / "fit_heldout_split.json"),
            "sc0_enforcement_sha256": common.sha256_of_file(COMMITTED / "sc0_enforcement.json"),
        },
        "rung_a": rung_a,
        "rung_c": rung_c,
        "refused_auxiliary": refused_aux,
        "kuq_transfer_ungated": kuq,
        "sc3_coverage": {
            "n_fit_confab": len(row_keys["fit_confab"]),
            "n_held_out_confab": len(row_keys["held_out_confab"]),
            "n_correct_control": len(row_keys["correct"]),
            "n_refused": len(row_keys["refused"]),
            "zero_silent_drops": True,
            "fit_heldout_disjoint": True,
            "correct_never_in_fit": True,
        },
        "rung_b_conditional_secondary": {"status": "NOT RUN", "reason": "GPU rung, out of scope for this harness pass; conditional on a rung-(a) pass plus fresh explicit launch approval (PI ruling 2026-07-18)"},
    }
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    common.write_json(RESULTS_DIR / "m4c_results.json", results)

    per_row_rows = [
        {"row_key": rk, "role": role, "baseline__d_ev_z": float(s)}
        for rk, role, s in zip(row_level["row_keys"], row_level["roles"], row_level["score_d_ev"])
    ]
    common.write_jsonl(RESULTS_DIR / "heldout_projections.jsonl", per_row_rows)

    print(f"[readouts] wrote {RESULTS_DIR / 'm4c_results.json'} and {RESULTS_DIR / 'heldout_projections.jsonl'} ({len(per_row_rows)} rows)", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
