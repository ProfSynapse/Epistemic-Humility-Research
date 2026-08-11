#!/usr/bin/env python3
"""G1-G6 gate scoring for ood-breadth-beyond-selfaware (gates.yaml). Stage 8
(aggregate_bootstrap_adjudicate), CPU-only.

G0 is scored by `screen_ood_surfaces.py` (pre-generation). G7 is scored by
`internal_panel_probe_gate.py` (needs the stage-6 extraction). This script
covers the rest, reading gates.yaml AT RUNTIME for every threshold so the
scoring can never silently drift from the locked file -- only path/schema
knowledge (which metrics.json goes with which arm) is hardcoded, the same
posture as screen_ood_surfaces.py's duplicated cell.yaml pins.

Reuses, rather than reimplements:
  - `archive/experiment/phase1/eval/analysis/calibration_gap_report.py`'s
    `spearman()` for G4 (arm-rank correlation) and `analysis_a()` /
    `auroc()` for G5 (emitted-to-appropriateness AUROC + std on AmbigQA).
  - `scorers.metrics_from_quadrants`' field names, read directly out of each
    arm x surface's `metrics.json` (written by run_eval.py) rather than
    recomputed from scored_rows.jsonl.

All integrity gates (G0-G3, G_docker) are read and must pass before any
evidential gate (G4-G7) is read, per gates.yaml's own discipline block. This
script enforces that ordering: it computes everything, but the printed/written
verdict marks evidential gates "NOT_READ (integrity gate failed)" if any
integrity gate failed, rather than reporting a number that gates.yaml says
must not be adjudicated.

Usage (run from the canonical checkout once stage 5/6 have produced real
metrics.json / scored_rows.jsonl for all 8 arms):

    python3 experiments/ood-breadth-beyond-selfaware/gate_score.py \
        --docker-digest sha256:f21629b9ae4ed11231768edfaed0f40d41d85d6ea9a71e8096a3d96ea0311772 \
        --g1-rerun-metrics <path to the re-run A2 SelfAware metrics.json> \
        --out experiments/ood-breadth-beyond-selfaware/analysis/gate/gate_report.json

Every --<arm>-results-dir flag defaults to the results_dir each arm's config
under archive/experiment/phase1/eval/config/eval_ood_breadth_*_local_4b.yaml
declares; override only for a non-default run location.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
EVAL_DIR = REPO_ROOT / "archive" / "experiment" / "phase1" / "eval"
EXP_DIR = Path(__file__).resolve().parent
GATES_PATH = EXP_DIR / "gates.yaml"

sys.path.insert(0, str(EVAL_DIR / "analysis"))

ARM_NAMES = {
    "A1": "clean_schema_sft_merged_seed1",
    "A2": "contrastive_schema_sft_merged_seed1",
    "A3": "contrastive_masked_schema_sft_merged_seed1",
    "A4": "clean_schema_sft_grpo_v2_seed1_corrected_base",
    "A5": "clean_schema_sft_grpo_v3_seed1",
    "A6": "grpo_v3_on_contrastive_sft_seed1",
    "A7": "grpo_v3_beta005_on_contrastive_sft_seed1",
    "A8": "probe_factual_schema_sft_merged_seed1",
}
G1_GATED_ARMS = {"A2", "A6", "A7"}

# Committed SelfAware metrics.json per arm (cell.yaml frozen_inputs.
# reference_selfaware_artifacts; same 8 paths as papers/paper-3-knows-but-
# doesnt-say/analysis/clean_subset_sensitivity_p3.py RUNS, verified present
# and readable at build time). G4's SelfAware reference side.
SELFAWARE_METRICS_PATHS = {
    "A1": "experiments/probe-scaled-response-confidence/analysis/phase1-migrated/eval/results_amendment_e_response_confidence_selfaware_clean_sft_seed1_merged_full_4b/clean_schema_sft_merged_seed1__selfaware/metrics.json",
    "A2": "experiments/contrastive-sft-behavior-conditional-confidence/analysis/phase1-migrated/eval/results_amendment_k_response_confidence_selfaware_contrastive_sft_seed1_merged_full_4b/contrastive_schema_sft_merged_seed1__selfaware/metrics.json",
    "A3": "experiments/answer-subspan-masked-contrastive-sft/analysis/phase1-migrated/eval/results_amendment_l_response_confidence_selfaware_contrastive_masked_sft_seed1_merged_full_4b/contrastive_masked_schema_sft_merged_seed1__selfaware/metrics.json",
    "A4": "experiments/probe-scaled-response-confidence/analysis/phase1-migrated/eval/results_amendment_e_response_confidence_selfaware_clean_sft_grpo_v2_seed1_corrected_base_full_4b/clean_schema_sft_grpo_v2_seed1_corrected_base__selfaware/metrics.json",
    "A5": "experiments/grpo-v3-proper-scoring-confidence/analysis/phase1-migrated/eval/results_amendment_j_response_confidence_selfaware_clean_sft_grpo_v3_seed1_full_4b/clean_schema_sft_grpo_v3_seed1__selfaware/metrics.json",
    "A6": "experiments/grpo-v3-on-contrastive-sft-base/analysis/phase1-migrated/eval/results_amendment_n_response_confidence_selfaware_grpo_on_contrastive_sft_seed1_full_4b/grpo_v3_on_contrastive_sft_seed1__selfaware/metrics.json",
    "A7": "experiments/grpo-v3-on-contrastive-sft-base/analysis/phase1-migrated/eval/results_amendment_n_beta005_selfaware_grpo_on_contrastive_sft_seed1_full_4b/grpo_v3_beta005_on_contrastive_sft_seed1__selfaware/metrics.json",
    "A8": "experiments/quantile-balanced-probe-distilled-sft/analysis/phase1-migrated/eval/results_amendment_m_response_confidence_selfaware_probe_factual_sft_seed1_merged_full_4b/probe_factual_schema_sft_merged_seed1__selfaware/metrics.json",
}

BEHAVIOR_METRIC_FIELDS = [
    "n", "n_unknown_labeled", "n_known_labeled", "refusal_recall_pct",
    "answer_on_unknown_pct", "over_refusal_pct", "refusal_rate_pct",
    "correct_on_known_pct", "correct_on_unknown_pct", "truthful_pct",
]


def load_gates() -> dict:
    return yaml.safe_load(GATES_PATH.read_text(encoding="utf-8"))


def results_dir_for_arm(arm_id: str) -> Path:
    name = ARM_NAMES[arm_id]
    return EVAL_DIR / f"results_ood_breadth_{name}_full_4b"


def load_metrics(path: Path) -> dict | None:
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# G1: re-merge parity (A2 vs its committed SelfAware metrics.json).
# ---------------------------------------------------------------------------


def score_g1(gates: dict, rerun_metrics_path: Path | None) -> dict:
    g = gates["g1_remerge_parity"]
    committed_path = REPO_ROOT / SELFAWARE_METRICS_PATHS["A2"]
    committed = load_metrics(committed_path)
    if committed is None:
        return {"gate": "G1", "status": "ERROR", "detail": f"committed A2 metrics missing: {committed_path}"}
    if rerun_metrics_path is None:
        return {"gate": "G1", "status": "NOT_RUN", "detail": "no --g1-rerun-metrics supplied (needs stage 3 GPU output)"}
    rerun = load_metrics(rerun_metrics_path)
    if rerun is None:
        return {"gate": "G1", "status": "ERROR", "detail": f"rerun metrics missing: {rerun_metrics_path}"}

    cm, rm = committed["metrics"], rerun["metrics"]
    max_delta_pp = g["thresholds"]["behavior_metric_abs_delta_max_pp"]
    deltas = {}
    all_within = True
    for field_name in BEHAVIOR_METRIC_FIELDS:
        c, r = cm.get(field_name), rm.get(field_name)
        if c is None or r is None:
            continue
        d = round(abs(r - c), 4)
        deltas[field_name] = {"committed": c, "rerun": r, "abs_delta": d}
        if field_name.endswith("_pct") and d > max_delta_pp:
            all_within = False

    n_exact = rm.get("n") == cm.get("n")
    nk_exact = rm.get("n_known_labeled") == cm.get("n_known_labeled")
    nu_exact = rm.get("n_unknown_labeled") == cm.get("n_unknown_labeled")
    passed = all_within and n_exact and nk_exact and nu_exact

    return {
        "gate": "G1",
        "status": "PASS" if passed else "FAIL",
        "threshold_pp": max_delta_pp,
        "n_exact_match": n_exact,
        "n_known_exact_match": nk_exact,
        "n_unknown_exact_match": nu_exact,
        "deltas": deltas,
        "on_fail": g["on_failure"] if not passed else None,
    }


# ---------------------------------------------------------------------------
# G2: surface construction (retained n, label_from_target, JSON coverage).
# ---------------------------------------------------------------------------


def score_g2(gates: dict) -> dict:
    g = gates["g2_surface_construction"]
    expected = g["thresholds"]["retained_n_must_equal"]
    coverage_min = g["thresholds"]["json_coverage_pct_min"]

    per_arm = {}
    all_pass = True
    any_data = False
    for arm_id, name in ARM_NAMES.items():
        rd = results_dir_for_arm(arm_id)
        surfaces = {}
        for surface_key, loader_key in (("S_KUQ", "kuq"), ("S_AMBIGQA", "ambigqa"), ("S_BIGBENCH", "bigbench_known_unknowns")):
            mpath = rd / f"{name}__{loader_key}" / "metrics.json"
            m = load_metrics(mpath)
            if m is None:
                surfaces[surface_key] = {"status": "NOT_RUN"}
                continue
            any_data = True
            metrics = m["metrics"]
            exp = expected[surface_key]
            n_ok = metrics["n"] == exp["total"]
            k_ok = metrics["n_known_labeled"] == exp["known"]
            u_ok = metrics["n_unknown_labeled"] == exp["unknown"]
            coverage = m.get("stated_confidence", {}).get("coverage_pct")
            cov_ok = coverage is not None and coverage >= coverage_min
            ok = n_ok and k_ok and u_ok and cov_ok
            if not ok:
                all_pass = False
            surfaces[surface_key] = {
                "n": metrics["n"], "n_known": metrics["n_known_labeled"], "n_unknown": metrics["n_unknown_labeled"],
                "expected": exp, "n_match": n_ok and k_ok and u_ok,
                "json_coverage_pct": coverage, "coverage_pass": cov_ok, "pass": ok,
            }
        per_arm[arm_id] = surfaces

    return {
        "gate": "G2", "status": ("PASS" if (any_data and all_pass) else ("NOT_RUN" if not any_data else "FAIL")),
        "coverage_min": coverage_min, "per_arm": per_arm,
    }


# ---------------------------------------------------------------------------
# G3: no thinking contamination. Static config check (real) + optional
# post-hoc scan of scored_rows.jsonl for literal think markers (real once
# GPU data exists).
# ---------------------------------------------------------------------------


def score_g3(gates: dict) -> dict:
    config_dir = EVAL_DIR / "config"
    configs = sorted(config_dir.glob("eval_ood_breadth_*_local_4b.yaml"))
    per_config = {}
    all_ok = True
    for cfg_path in configs:
        cfg = yaml.safe_load(cfg_path.read_text())
        enable_thinking = cfg.get("generation", {}).get("enable_thinking")
        ok = enable_thinking is False
        if not ok:
            all_ok = False
        per_config[cfg_path.name] = {"enable_thinking": enable_thinking, "pass": ok}

    think_scan = {}
    any_generated = False
    for arm_id, name in ARM_NAMES.items():
        rd = results_dir_for_arm(arm_id)
        for loader_key in ("kuq", "ambigqa", "bigbench_known_unknowns"):
            sr_path = rd / f"{name}__{loader_key}" / "scored_rows.jsonl"
            if not sr_path.is_file():
                continue
            any_generated = True
            hits = 0
            with sr_path.open(encoding="utf-8") as fh:
                for line in fh:
                    if not line.strip():
                        continue
                    r = json.loads(line)
                    if "<think>" in r.get("generated_answer", "") or "</think>" in r.get("generated_answer", ""):
                        hits += 1
            think_scan[f"{arm_id}__{loader_key}"] = hits
            if hits:
                all_ok = False

    return {
        "gate": "G3",
        "status": "PASS" if all_ok else "FAIL",
        "config_enable_thinking_false": per_config,
        "post_hoc_think_marker_scan": think_scan if any_generated else "NOT_RUN (no scored_rows.jsonl yet)",
        "note": (
            "run_eval.py's assert_no_think_scaffolding/assert_no_generated_thinking "
            "raise RuntimeError DURING generation if violated (VLLMGenerator._render_"
            "prompt / .generate), so a completed run already enforced this in-harness; "
            "the scan above is a post-hoc confirmation, not the sole enforcement."
        ),
    }


# ---------------------------------------------------------------------------
# G_docker_digest: string comparison against the pinned digest.
# ---------------------------------------------------------------------------


def score_g_docker(gates: dict, live_digest: str | None) -> dict:
    g = gates["g_docker_digest"]
    pinned = g["thresholds"]["image_digest_must_equal"]
    if live_digest is None:
        return {"gate": "G_docker_digest", "status": "NOT_CHECKED", "pinned": pinned,
                "detail": "no --docker-digest supplied; operator must run `docker inspect` before each GPU stage"}
    match = live_digest == pinned
    return {"gate": "G_docker_digest", "status": "PASS" if match else "FAIL", "pinned": pinned, "live": live_digest}


# ---------------------------------------------------------------------------
# G4: unknown-side behavior transfer (Spearman rho, arm rank by
# refusal_recall_pct, KUQ and AmbigQA vs SelfAware).
# ---------------------------------------------------------------------------


def score_g4(gates: dict) -> dict:
    from calibration_gap_report import spearman

    g = gates["g4_unknown_side_behavior_transfer"]
    threshold = g["threshold"]

    selfaware_rr = {}
    for arm_id in ARM_NAMES:
        m = load_metrics(REPO_ROOT / SELFAWARE_METRICS_PATHS[arm_id])
        if m is None:
            return {"gate": "G4", "status": "ERROR", "detail": f"missing committed SelfAware metrics for {arm_id}"}
        selfaware_rr[arm_id] = m["metrics"]["refusal_recall_pct"]

    per_surface = {}
    any_data = False
    for surface_key, loader_key in (("S_KUQ", "kuq"), ("S_AMBIGQA", "ambigqa")):
        arm_rr = {}
        for arm_id, name in ARM_NAMES.items():
            mpath = results_dir_for_arm(arm_id) / f"{name}__{loader_key}" / "metrics.json"
            m = load_metrics(mpath)
            if m is not None:
                arm_rr[arm_id] = m["metrics"]["refusal_recall_pct"]
        if len(arm_rr) < 8:
            per_surface[surface_key] = {"status": "NOT_RUN", "n_arms_with_data": len(arm_rr)}
            continue
        any_data = True
        arms_ordered = sorted(arm_rr)
        a = np.array([selfaware_rr[a_] for a_ in arms_ordered])
        b = np.array([arm_rr[a_] for a_ in arms_ordered])
        rho = spearman(a, b)
        per_surface[surface_key] = {
            "status": "PASS" if rho >= threshold else "FAIL",
            "spearman_rho": round(float(rho), 4),
            "threshold": threshold,
            "selfaware_refusal_recall_pct": {a_: selfaware_rr[a_] for a_ in arms_ordered},
            "surface_refusal_recall_pct": {a_: arm_rr[a_] for a_ in arms_ordered},
        }

    overall = "NOT_RUN"
    if any_data:
        overall = "PASS" if all(v.get("status") == "PASS" for v in per_surface.values() if "status" in v and v["status"] != "NOT_RUN") else "FAIL"
    return {"gate": "G4", "status": overall, "per_surface": per_surface}


# ---------------------------------------------------------------------------
# G5: stated-confidence collapse transfer (AmbigQA, all 8 arms).
# ---------------------------------------------------------------------------


def score_g5(gates: dict) -> dict:
    from calibration_gap_report import analysis_a, load_scored

    g = gates["g5_stated_confidence_collapse_transfer"]
    auroc_max = g["thresholds"]["emitted_auroc_vs_appropriateness_max"]
    std_max = g["thresholds"]["emitted_std_max"]

    per_arm = {}
    any_data = False
    all_pass = True
    for arm_id, name in ARM_NAMES.items():
        sr_path = results_dir_for_arm(arm_id) / f"{name}__ambigqa" / "scored_rows.jsonl"
        if not sr_path.is_file():
            per_arm[arm_id] = {"status": "NOT_RUN"}
            continue
        any_data = True
        rows = load_scored(sr_path)
        a = analysis_a(rows)
        auroc_ok = a["auroc_emitted_to_appropriateness"] <= auroc_max
        std_ok = a["emitted_std"] <= std_max
        ok = auroc_ok and std_ok
        if not ok:
            all_pass = False
        per_arm[arm_id] = {
            "status": "PASS" if ok else "FAIL",
            "auroc_emitted_to_appropriateness": round(a["auroc_emitted_to_appropriateness"], 4),
            "auroc_max": auroc_max, "auroc_pass": auroc_ok,
            "emitted_std": round(a["emitted_std"], 4),
            "std_max": std_max, "std_pass": std_ok,
        }

    return {"gate": "G5", "status": ("PASS" if (any_data and all_pass) else ("NOT_RUN" if not any_data else "FAIL")), "per_arm": per_arm}


# ---------------------------------------------------------------------------
# G6: BIG-bench labeling gate (Wilson 95% CI on every rate, n=23/side).
# ---------------------------------------------------------------------------


def wilson_ci(k: int, n: int, z: float = 1.959963984540054) -> tuple[float, float]:
    """Standard Wilson score interval for a binomial proportion."""
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    denom = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    half = (z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5)) / denom
    return (max(0.0, center - half), min(1.0, center + half))


def score_g6() -> dict:
    per_arm = {}
    any_data = False
    for arm_id, name in ARM_NAMES.items():
        mpath = results_dir_for_arm(arm_id) / f"{name}__bigbench_known_unknowns" / "metrics.json"
        m = load_metrics(mpath)
        if m is None:
            per_arm[arm_id] = {"status": "NOT_RUN"}
            continue
        any_data = True
        counts = m["counts"]
        n_known, n_unknown = counts["n_known_labeled"], counts["n_unknown_labeled"]
        refuse_unknown = counts["refuse_on_unknown"]
        refuse_known = counts["refuse_on_known"]
        rr_lo, rr_hi = wilson_ci(refuse_unknown, n_unknown)
        or_lo, or_hi = wilson_ci(refuse_known, n_known)
        per_arm[arm_id] = {
            "n_known": n_known, "n_unknown": n_unknown,
            "refusal_recall_pct": m["metrics"]["refusal_recall_pct"],
            "refusal_recall_wilson_95ci": [round(rr_lo * 100, 2), round(rr_hi * 100, 2)],
            "over_refusal_pct": m["metrics"]["over_refusal_pct"],
            "over_refusal_wilson_95ci": [round(or_lo * 100, 2), round(or_hi * 100, 2)],
            "labeled_spot_check": True,
            "read_by_evidential_gate": False,
        }
    return {
        "gate": "G6", "type": "labeling_gate_not_outcome_gate",
        "status": "LABELED" if any_data else "NOT_RUN",
        "per_arm": per_arm,
    }


# ---------------------------------------------------------------------------
# Orchestration.
# ---------------------------------------------------------------------------


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--docker-digest", default=None, help="live digest from `docker inspect`, for G_docker_digest")
    ap.add_argument("--g1-rerun-metrics", type=Path, default=None, help="stage-3 re-run A2 SelfAware metrics.json")
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()

    gates = load_gates()

    integrity = {
        "G1": score_g1(gates, args.g1_rerun_metrics),
        "G2": score_g2(gates),
        "G3": score_g3(gates),
        "G_docker_digest": score_g_docker(gates, args.docker_digest),
    }
    integrity_statuses = [g["status"] for g in integrity.values()]
    integrity_all_pass = all(s == "PASS" for s in integrity_statuses)
    integrity_any_not_run = any(s in ("NOT_RUN", "NOT_CHECKED") for s in integrity_statuses)

    evidential = {}
    if integrity_all_pass:
        evidential["G4"] = score_g4(gates)
        evidential["G5"] = score_g5(gates)
        evidential["G6"] = score_g6()
    else:
        reason = "integrity gate(s) not yet run" if integrity_any_not_run else "integrity gate(s) FAILED"
        evidential = {
            "G4": {"gate": "G4", "status": f"NOT_READ ({reason})"},
            "G5": {"gate": "G5", "status": f"NOT_READ ({reason})"},
            "G6": {"gate": "G6", "status": f"NOT_READ ({reason})"},
        }
    # G0 and G7 are scored by their own scripts; noted here for completeness.
    note = (
        "G0 is scored by screen_ood_surfaces.py (run before any generation). "
        "G7 is scored by internal_panel_probe_gate.py (needs stage-6 extraction). "
        "Neither is recomputed here."
    )

    report = {
        "integrity_gates": integrity,
        "integrity_all_pass": integrity_all_pass,
        "evidential_gates": evidential,
        "note": note,
    }
    text = json.dumps(report, indent=2)
    print(text)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text + "\n", encoding="utf-8")
        print(f"\nwrote {args.out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
