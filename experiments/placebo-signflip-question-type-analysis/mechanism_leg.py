#!/usr/bin/env python3
"""Mechanism leg (M1/M2/M3) for placebo-signflip-question-type-analysis.

CPU-only re-read of pre-generation anchor hidden states already extracted by
upstream experiments (qwen35-4b-midband-heldout/capture_anchors.py,
rr2-mistral-adjudicated-refusal-confirm/materialize_rows.py,
rr-cross-family-raw-refusal/materialize_rows.py). No model, no GPU, no new
extraction. Every projection reuses frame_port.py's `raw_projection`/
`standardized_score` -- the SAME two-stage chain BG1 validates against the
frozen gate's firing decision -- applied here to u_d and c_hat as continuous
statistics rather than a discrete fire decision.

M1's standardized scores are UNCLIPPED (`standardized_score(..., clip=False)`):
the gate's [-2, 2] clip exists to bound leverage on a discrete fire decision,
and would censor the tails of a continuous two-sample distributional
comparison, which is what M1 is. This is a build-time judgment call, flagged
here and in the report rather than silently decided.

M1/M2/M3 against the REAL mistral/llama anchor JSONs (251MB / 493MB) are
OPT-IN (`project_family_realdata`, `m3_displacement_realdata`) and are never
invoked by report.py or default pytest collection, matching this build
task's constraint: harness code only, no result-producing run, and no giant
in-memory load without the lead's go-ahead (see staging.py's module
docstring for the host-RAM rationale). Qwen's anchors are small (17MB
safetensors) but M1/M2/M3 are still NOT executed here for the same reason:
this build produces a harness, not results.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Callable

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from common import bootstrap_smd, load_jsonl, mann_whitney_u, question_type_of  # noqa: E402
from frame_port import (  # noqa: E402
    load_direction_vector, raw_projection, reconstruct_llama_layer, standardized_score,
)
from staging import DOUBT_SNAP_DIR, RR2_LOCAL_DIR, STAGED  # noqa: E402


# ---------------------------------------------------------------------------
# Per-row projection (pure function; exercised on synthetic anchors by
# test_signflip_smoke.py)
# ---------------------------------------------------------------------------

def project_row(
    h: np.ndarray, u_d: np.ndarray, c_hat: np.ndarray,
    mu_d: float, sigma_d: float, mu_c: float, sigma_c: float,
) -> dict[str, float]:
    proj_d = raw_projection(h, u_d)
    proj_c = raw_projection(h, c_hat)
    return {
        "proj_d": proj_d, "z_d": standardized_score(proj_d, mu_d, sigma_d, clip=False),
        "proj_c": proj_c, "z_c": standardized_score(proj_c, mu_c, sigma_c, clip=False),
    }


def project_population(
    anchors: dict[str, np.ndarray], u_d: np.ndarray, c_hat: np.ndarray,
    mu_d: float, sigma_d: float, mu_c: float, sigma_c: float,
) -> list[dict[str, Any]]:
    out = []
    for row_key, h in anchors.items():
        row = {"row_key": row_key, "question_type": question_type_of(row_key)}
        row.update(project_row(np.asarray(h, dtype=np.float64), u_d, c_hat, mu_d, sigma_d, mu_c, sigma_c))
        out.append(row)
    return out


# ---------------------------------------------------------------------------
# M1: answerable vs unanswerable pre-generation position
# ---------------------------------------------------------------------------

def m1_contrast(projected: list[dict[str, Any]], score_key: str, seed: int = 20260714) -> dict[str, Any]:
    unanswerable = np.array([r[score_key] for r in projected if r["question_type"] == "unanswerable"])
    answerable = np.array([r[score_key] for r in projected if r["question_type"] == "answerable"])
    mwu = mann_whitney_u(unanswerable, answerable)
    smd = bootstrap_smd(unanswerable, answerable, seed=seed)
    return {
        "score": score_key, "n_unanswerable": int(len(unanswerable)), "n_answerable": int(len(answerable)),
        "mean_unanswerable": float(unanswerable.mean()) if len(unanswerable) else None,
        "mean_answerable": float(answerable.mean()) if len(answerable) else None,
        "mann_whitney": mwu, "bootstrap_smd": smd,
        "prediction_direction": "unanswerable_higher",
        "prediction_consistent": (
            bool(unanswerable.mean() > answerable.mean()) if len(unanswerable) and len(answerable) else None
        ),
    }


# ---------------------------------------------------------------------------
# M2: descriptive cross-family consistency (no formal test, n=2 families
# with a placebo sign; BG2 m2_underpowered)
# ---------------------------------------------------------------------------

# Certified wide baselines (AMENDMENT.md "Motivation and posture"), cited
# not recomputed here -- the calibration's own resolved numbers.
CERTIFIED_PLACEBO_SIGN = {
    "qwen35-4b": {"wide_baseline_unanswerable_rate": 0.104, "placebo_delta_pts": -5.13, "direction": "suppress"},
    "mistral7b-v03": {"wide_baseline_unanswerable_rate": 0.280, "placebo_delta_pts": 7.39, "direction": "recruit"},
    "llama32-3b": {"wide_baseline_unanswerable_rate": None, "placebo_delta_pts": None, "direction": "no_placebo_arm_ran_shape_F"},
}


def m2_summary(per_family_unanswerable_stats: dict[str, dict[str, float]]) -> dict[str, Any]:
    """per_family_unanswerable_stats: {family: {"mean_z_d": ..., "std_z_d": ...,
    "mean_z_c": ..., "std_z_c": ...}}. Descriptive only -- reports each
    family's baseline unanswerable doubt/caution position alongside its
    certified placebo sign, with the lead's working hypothesis stated as a
    consistency read, never a computed test."""
    rows = {}
    for family, stats in per_family_unanswerable_stats.items():
        rows[family] = {**stats, **CERTIFIED_PLACEBO_SIGN.get(family, {})}
    return {
        "n_families": len(rows), "underpowered": True,
        "note": "n=2 families with a placebo sign (llama never ran a placebo arm); descriptive consistency read only, never a test",
        "families": rows,
    }


# ---------------------------------------------------------------------------
# M3: analytic realized caution-axis displacement (qwen, mistral only)
# ---------------------------------------------------------------------------

def m3_row_displacement(h: np.ndarray, r_hat: np.ndarray, c_hat: np.ndarray, dose_abs: float) -> float:
    """AMENDMENT.md M3's analytic reconstruction of the erase-write-to-
    magnitude placebo's realized caution-axis displacement, without needing
    the post-write state to exist on disk:

        proj_c_hat(post) = proj_c_hat(pre) - <h, r_hat> * <r_hat, c_hat>
                                            + dose_abs * <r_hat, c_hat>
        displacement = proj_c_hat(post) - proj_c_hat(pre)
                     = <r_hat, c_hat> * (dose_abs - <h, r_hat>)

    matching the InterventionHook erase_write law: h_new = h - <h, r_hat> *
    r_hat + dose_abs * r_hat, then displacement = (h_new - h) @ c_hat."""
    dot_r_h = raw_projection(h, r_hat)
    dot_r_chat = float(np.asarray(r_hat, dtype=np.float64) @ np.asarray(c_hat, dtype=np.float64))
    return dot_r_chat * (dose_abs - dot_r_h)


def m3_contrast(
    anchors: dict[str, np.ndarray], r_hat: np.ndarray, c_hat: np.ndarray, dose_abs: float, seed: int = 20260714,
) -> dict[str, Any]:
    displacement_by_type: dict[str, list[float]] = {"unanswerable": [], "answerable": []}
    for row_key, h in anchors.items():
        qt = question_type_of(row_key)
        displacement_by_type[qt].append(
            m3_row_displacement(np.asarray(h, dtype=np.float64), r_hat, c_hat, dose_abs)
        )
    unanswerable = np.array(displacement_by_type["unanswerable"])
    answerable = np.array(displacement_by_type["answerable"])
    return {
        "dose_abs": dose_abs, "n_unanswerable": int(len(unanswerable)), "n_answerable": int(len(answerable)),
        "mean_displacement_unanswerable": float(unanswerable.mean()) if len(unanswerable) else None,
        "mean_displacement_answerable": float(answerable.mean()) if len(answerable) else None,
        "bootstrap_smd": bootstrap_smd(unanswerable, answerable, seed=seed) if len(unanswerable) and len(answerable) else None,
        "prediction": "does NOT differ by question type within a family (the row-dependent term <h,r_hat> is small and question-type-independent by construction)",
    }


# ---------------------------------------------------------------------------
# Family loaders (OPT-IN real-data; never called by report.py)
# ---------------------------------------------------------------------------

def load_qwen_family() -> dict[str, Any]:
    from safetensors.numpy import load_file

    anchor_path = STAGED / "qh" / "anchor_extract_heldout.safetensors"
    manifest_path = STAGED / "qh" / "anchor_extract_heldout_manifest.json"
    manifest = json.loads(manifest_path.read_text())
    tensors = load_file(str(anchor_path))
    anchors = {rm["row_key"]: tensors[rm["safetensors_key"]] for rm in manifest["rows"]}

    directions_dir = DOUBT_SNAP_DIR / "analysis-committed" / "directions" / "hs20"
    u_d = load_direction_vector(directions_dir / "u_d.json")
    c_hat = load_direction_vector(directions_dir / "c_hat.json")
    r_hat = load_direction_vector(directions_dir / "random_direction.json")
    stats = json.loads((DOUBT_SNAP_DIR / "analysis-committed" / "build_manifest.json").read_text())["layers"]["hs20"]
    return {
        "family": "qwen35-4b", "layer": "hs20", "anchors": anchors,
        "u_d": u_d, "c_hat": c_hat, "r_hat": r_hat,
        "mu_d": stats["mu_d"], "sigma_d": stats["sigma_d"], "mu_c": stats["mu_c"], "sigma_c": stats["sigma_c"],
        "dose_abs": 12.608187917799976,  # frozen per cell.yaml mechanism_probe.qwen35-4b.dose_abs
    }


def load_mistral_family_realdata() -> dict[str, Any]:
    """OPT-IN: loads the 251MB anchors_at_candidate_layers.json."""
    anchors_path = STAGED / "mc" / "anchors_at_candidate_layers.json"
    raw = json.loads(anchors_path.read_text())
    anchors = {rk: per["16"] for rk, per in raw.items() if "16" in per}
    del raw

    directions_dir = STAGED / "mc" / "directions"
    u_d = load_direction_vector(directions_dir / "hs16_u_d.json")
    c_hat = load_direction_vector(directions_dir / "hs16_c_hat.json")
    r_hat = load_direction_vector(directions_dir / "hs16_random_direction.json")
    stats = json.loads((directions_dir / "hs16_build_manifest.json").read_text())
    return {
        "family": "mistral7b-v03", "layer": "hs16", "anchors": anchors,
        "u_d": u_d, "c_hat": c_hat, "r_hat": r_hat,
        "mu_d": stats["mu_d"], "sigma_d": stats["sigma_d"], "mu_c": stats["mu_c"], "sigma_c": stats["sigma_c"],
        "dose_abs": 3.6653166050691756,  # 12 * sigma_c(hs16); cell.yaml mechanism_probe.mistral7b-v03.dose_abs
    }


def load_llama_family_realdata(layers: tuple[int, ...] = (20, 22, 23)) -> dict[str, Any]:
    """OPT-IN: loads the 493MB anchors_at_candidate_layers.json, once per
    layer (three separate loads -- costly, opt-in only). No M3 (no placebo
    arm ran for llama, shape F)."""
    anchors_path = STAGED / "llama" / "anchors_at_candidate_layers.json"
    out: dict[str, Any] = {"family": "llama32-3b", "layers": {}}
    for layer in layers:
        recon = reconstruct_llama_layer(layer)
        fit = recon["fit"]
        raw = json.loads(anchors_path.read_text())
        anchors = {rk: per[str(layer)] for rk, per in raw.items() if str(layer) in per}
        del raw
        out["layers"][f"hs{layer}"] = {
            "anchors": anchors, "u_d": fit["u_d"], "c_hat": fit["c_hat"],
            "mu_d": fit["stats"]["mu_d"], "sigma_d": fit["stats"]["sigma_d"],
            "mu_c": fit["stats"]["mu_c"], "sigma_c": fit["stats"]["sigma_c"],
            "crosscheck_pass": recon["pass"],
        }
    return out


def run_family_m1_m3(family_data: dict[str, Any], include_m3: bool) -> dict[str, Any]:
    """OPT-IN orchestration for one (family, layer): M1 on u_d/c_hat
    projections, M3 (if include_m3) on the analytic displacement. Never
    called by report.py in this build."""
    projected = project_population(
        family_data["anchors"], family_data["u_d"], family_data["c_hat"],
        family_data["mu_d"], family_data["sigma_d"], family_data["mu_c"], family_data["sigma_c"],
    )
    result = {
        "family": family_data["family"], "layer": family_data["layer"],
        "m1_doubt": m1_contrast(projected, "z_d"),
        "m1_caution": m1_contrast(projected, "z_c"),
    }
    if include_m3:
        result["m3"] = m3_contrast(family_data["anchors"], family_data["r_hat"], family_data["c_hat"], family_data["dose_abs"])
    return result
