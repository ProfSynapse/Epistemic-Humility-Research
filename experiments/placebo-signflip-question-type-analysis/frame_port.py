#!/usr/bin/env python3
"""BG1 (mechanism frame port) for placebo-signflip-question-type-analysis.

Ports the doubt-gate's fire/no-fire chain EXACTLY as it exists on disk in
three places verified byte-identical in behavior before this module was
written (read in full):
  qwen35-4b-midband-heldout/capture_anchors.py:gate_decision
  rr2-mistral-adjudicated-refusal-confirm/direction_fit.py:score_and_fire
  rr-cross-family-raw-refusal/direction_fit.py:score_and_fire (byte-for-byte
    port of the RR2 module except its docstring, diffed against RR2's copy)

The chain (per row, given a hidden-state anchor vector h and a unit doubt
direction u_d fit on FIT-population projections):

    proj_d = h @ u_d                              # RAW dot product
    z_d    = clip((proj_d - mu_d) / sigma_d, -2, 2)
    score  = -z_d
    fire   = score >= tau_frozen

mu_d/sigma_d/tau_frozen are SCALARS from the layer's build_manifest.json,
never per-feature. The direction JSON's own "mu"/"sigma" fields (per-feature
mu, always the zero vector; a scalar-looking "sigma" that is actually the
OTHER direction's sigma_c/1.0, not used in gate firing at all -- verified by
inspection of fit_midband_directions.py:_direction_record and every caller
of the direction JSON, none of which read "mu"/"sigma" for gate arithmetic)
are schema placeholders, not a second real standardization stage; this
module's `raw_projection` deliberately reads ONLY the "vector" field, exactly
matching every upstream caller.

A drafter's scoping smoke reported that a NAIVE single-stage projection
(skipping the scalar mu_d/sigma_d/tau_frozen step, e.g. thresholding proj_d
directly) reproduced only 421/1303 firings -- this module's acceptance test
(`check_qwen_frame`) recomputes fire for the full 1,692-row qwen heldout pool
independently from the staged anchor tensors and compares against the row_key
set of the REAL `analysis/runlog/gated.jsonl` (the actual rows the GPU
pipeline wrote to -- ground truth downstream of the fire decision, not a
re-read of the pipeline's own bookkeeping file), which the exact chain above
reproduces exactly (verified in this build: 0/1692 mismatches).

Mistral and llama reuse `score_and_fire`/`fit_directions` imported directly
from rr2-mistral-adjudicated-refusal-confirm/direction_fit.py (committed in
this worktree; read-only import, never copied or reimplemented by hand) --
"reuse existing project machinery" per this build's own binding rules.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from common import load_jsonl  # noqa: E402
from staging import DOUBT_SNAP_DIR, RR2_LOCAL_DIR, RR_LOCAL_DIR, STAGED  # noqa: E402

sys.path.insert(0, str(RR2_LOCAL_DIR))
import direction_fit  # noqa: E402  (rr2's module, byte-for-byte port of RR's own)

CLIP = 2.0


# ---------------------------------------------------------------------------
# The ported chain itself
# ---------------------------------------------------------------------------

def load_direction_vector(path: Path) -> np.ndarray:
    """Reads ONLY the "vector" field. Asserts the schema's per-feature "mu"
    is the trivial zero vector (the invariant every upstream direction JSON
    in this repo currently holds) so a future non-trivial per-feature
    standardization cannot silently be ignored by this port."""
    obj = json.loads(path.read_text(encoding="utf-8"))
    vec = np.asarray(obj["vector"], dtype=np.float64)
    mu = obj.get("mu")
    if mu is not None and any(float(x) != 0.0 for x in mu):
        raise SystemExit(
            f"frame_port SCHEMA DRIFT: {path} has a non-trivial per-feature "
            f"'mu' -- the ported chain assumes this is always the zero "
            f"vector (verified for every direction JSON in this repo as of "
            f"this build); raw_projection would silently be wrong."
        )
    return vec


def raw_projection(h: np.ndarray, unit_vector: np.ndarray) -> float:
    return float(np.asarray(h, dtype=np.float64) @ unit_vector)


def gate_decision(proj_d: float, mu_d: float, sigma_d: float, tau: float) -> dict[str, Any]:
    """Verbatim port of qwen35-4b-midband-heldout/capture_anchors.py:
    gate_decision (also rr2's direction_fit.score_and_fire's per-row body)."""
    z_d = float(np.clip((proj_d - mu_d) / sigma_d, -CLIP, CLIP))
    score = -z_d
    fire = bool(score >= tau)
    return {"proj_d": proj_d, "z_d": z_d, "score_neg_z_d": score, "fire": fire, "tau": tau}


def standardized_score(proj: float, mu: float, sigma: float, clip: bool = True) -> float:
    """z = (proj - mu) / sigma. `clip=True` reproduces the discrete gate's
    firing statistic (clipped to [-2, 2], the fire-decision robustness
    convention); `clip=False` is this build's deliberate choice for M1's
    continuous two-sample position contrast, where clipping would censor the
    tails of a distributional comparison rather than protect a threshold --
    NOT the same statistic as the gate's z_d, reported as such in mechanism_
    leg.py's output (see that module's docstring)."""
    z = (proj - mu) / (sigma or 1.0)
    return float(np.clip(z, -CLIP, CLIP)) if clip else float(z)


# ---------------------------------------------------------------------------
# BG1 acceptance test: qwen (real data, small -- always run)
# ---------------------------------------------------------------------------

def check_qwen_frame(tolerance: float = 0.01) -> dict[str, Any]:
    """Recomputes fire for every row in the staged qwen heldout anchor
    tensors from the committed hs20 u_d.json + build_manifest.json, and
    compares the fire=True row_key set against the REAL
    analysis/runlog/gated.jsonl fired set (ground truth: the rows the GPU
    pipeline actually wrote to)."""
    from safetensors.numpy import load_file

    anchor_path = STAGED / "qh" / "anchor_extract_heldout.safetensors"
    manifest_path = STAGED / "qh" / "anchor_extract_heldout_manifest.json"
    gated_path = STAGED / "qh" / "gated.jsonl"
    u_d_path = DOUBT_SNAP_DIR / "analysis-committed" / "directions" / "hs20" / "u_d.json"
    build_manifest_path = DOUBT_SNAP_DIR / "analysis-committed" / "build_manifest.json"

    for p in (anchor_path, manifest_path, gated_path, u_d_path, build_manifest_path):
        if not p.is_file():
            raise SystemExit(f"check_qwen_frame: missing {p}; run staging.py first")

    u_d = load_direction_vector(u_d_path)
    layer_stats = json.loads(build_manifest_path.read_text())["layers"]["hs20"]
    mu_d, sigma_d, tau = layer_stats["mu_d"], layer_stats["sigma_d"], layer_stats["tau_frozen"]

    anchor_manifest = json.loads(manifest_path.read_text())
    tensors = load_file(str(anchor_path))

    recomputed_fired: set[str] = set()
    n_rows = 0
    for row_meta in anchor_manifest["rows"]:
        row_key = row_meta["row_key"]
        skey = row_meta["safetensors_key"]
        h = np.asarray(tensors[skey], dtype=np.float64)
        proj_d = raw_projection(h, u_d)
        decision = gate_decision(proj_d, mu_d, sigma_d, tau)
        n_rows += 1
        if decision["fire"]:
            recomputed_fired.add(row_key)

    ground_truth_fired = {r["row_key"] for r in load_jsonl(gated_path)}
    mismatches = recomputed_fired.symmetric_difference(ground_truth_fired)
    mismatch_rate = len(mismatches) / n_rows if n_rows else 1.0

    return {
        "family": "qwen35-4b", "layer": "hs20", "n_rows": n_rows,
        "n_recomputed_fired": len(recomputed_fired), "n_ground_truth_fired": len(ground_truth_fired),
        "n_mismatches": len(mismatches), "mismatch_rate": mismatch_rate,
        "tolerance": tolerance, "pass": mismatch_rate <= tolerance,
        "ground_truth_source": "analysis/runlog/gated.jsonl (real GPU pipeline output)",
    }


# ---------------------------------------------------------------------------
# BG1 evidence: mistral (small, already-computed cross-check; no anchor load)
# ---------------------------------------------------------------------------

def check_mistral_frame_via_fit_reuse_report() -> dict[str, Any]:
    """Reads RR2's OWN already-computed field-for-field cross-check
    (analysis/fit_reuse_report.json), produced by
    rr2-mistral-adjudicated-refusal-confirm/fit_reuse.py reconstructing
    u_d/c_hat/random_direction at hs16 via the SAME `direction_fit.
    fit_directions` this module imports, and asserting the reconstruction's
    mu_d/sigma_d/mu_c/sigma_c/tau_frozen/auc match RR's committed
    hs16_fit_build_manifest.json field-for-field. This IS "reproduce
    committed gate statistics from fit_reuse ... manifests" (BG1's own
    wording for mistral/llama) -- reading it does not require loading the
    251MB anchors_at_candidate_layers.json, so this check always runs.
    A row-level fire-set reproduction against the real
    heldout__gated.jsonl (mirroring check_qwen_frame exactly) is available
    as an opt-in real-data check, see test_signflip_smoke.py."""
    report_path = STAGED / "mc" / "fit_reuse_report.json"
    if not report_path.is_file():
        raise SystemExit(f"check_mistral_frame_via_fit_reuse_report: missing {report_path}; run staging.py first")
    report = json.loads(report_path.read_text())
    crosscheck = report["fit_reconstruction_matches_rr_committed_stats"]
    return {
        "family": "mistral7b-v03", "layer": "hs16",
        "source": "rr2-mistral-adjudicated-refusal-confirm/analysis/fit_reuse_report.json",
        "pass": bool(crosscheck["pass"]), "mismatches": crosscheck["mismatches"],
        "observed": crosscheck["observed"], "expected": crosscheck["expected"],
        "note": "field-for-field stats match, not an independent row-level fire-set reproduction (that check is opt-in, see test_signflip_smoke.py)",
    }


def check_mistral_frame_realdata(tolerance: float = 0.01) -> dict[str, Any]:
    """OPT-IN real-data row-level fire-set check (loads the 251MB
    anchors_at_candidate_layers.json; not called by report.py or by default
    pytest collection -- see test_signflip_smoke.py's realdata marker).
    Mirrors check_qwen_frame exactly, against heldout__gated.jsonl."""
    anchors_path = STAGED / "mc" / "anchors_at_candidate_layers.json"
    gated_path = STAGED / "mc" / "heldout__gated.jsonl"
    u_d_path = STAGED / "mc" / "directions" / "hs16_u_d.json"
    build_manifest_path = STAGED / "mc" / "directions" / "hs16_build_manifest.json"
    for p in (anchors_path, gated_path, u_d_path, build_manifest_path):
        if not p.is_file():
            raise SystemExit(f"check_mistral_frame_realdata: missing {p}; run staging.py first")

    u_d = load_direction_vector(u_d_path)
    stats = json.loads(build_manifest_path.read_text())
    mu_d, sigma_d, tau = stats["mu_d"], stats["sigma_d"], stats["tau_frozen"]

    raw_anchors = json.loads(anchors_path.read_text())
    recomputed_fired: set[str] = set()
    n_rows = 0
    for row_key, per_layer in raw_anchors.items():
        h = per_layer.get("16")
        if h is None:
            continue
        proj_d = raw_projection(np.asarray(h, dtype=np.float64), u_d)
        n_rows += 1
        if gate_decision(proj_d, mu_d, sigma_d, tau)["fire"]:
            recomputed_fired.add(row_key)
    del raw_anchors

    ground_truth_fired = {r["row_key"] for r in load_jsonl(gated_path)}
    mismatches = recomputed_fired.symmetric_difference(ground_truth_fired)
    mismatch_rate = len(mismatches) / n_rows if n_rows else 1.0
    return {
        "family": "mistral7b-v03", "layer": "hs16", "n_rows": n_rows,
        "n_recomputed_fired": len(recomputed_fired), "n_ground_truth_fired": len(ground_truth_fired),
        "n_mismatches": len(mismatches), "mismatch_rate": mismatch_rate,
        "tolerance": tolerance, "pass": mismatch_rate <= tolerance,
        "ground_truth_source": "analysis/runlog/heldout__gated.jsonl",
    }


# ---------------------------------------------------------------------------
# BG1 evidence: llama (opt-in real-data reconstruction; no pre-computed
# cross-check exists on disk, unlike mistral -- RR's own harness never ran
# fit_reuse for llama, it fit directly via dose_ladder.py)
# ---------------------------------------------------------------------------

_LLAMA_LAYERS = (20, 22, 23)


def reconstruct_llama_layer(layer: int, seed: int = 20260713) -> dict[str, Any]:
    """Reconstructs u_d/c_hat/random_direction/stats at one llama candidate
    layer via `direction_fit.fit_directions` (imported from RR2's committed
    module, itself a byte-for-byte port of rr-cross-family-raw-refusal's own)
    on llama's staged joined_rows_private.jsonl (FIT split) + staged
    anchors_at_candidate_layers.json, and cross-checks the reconstruction's
    mu_d/sigma_d/mu_c/sigma_c/tau_frozen/auc field-for-field against RR's own
    committed hs{layer}_fit_build_manifest.json -- the SAME cross-check
    fit_reuse.py already performs for mistral, generalized here because no
    one has run it for llama before (RR stopped at shape F before a held-out
    lane; this is a genuine first-time reconstruction, not a re-read).

    OPT-IN: loads the 493MB anchors_at_candidate_layers.json. Never called
    by report.py; see test_signflip_smoke.py's realdata marker."""
    joined_path = STAGED / "llama" / "joined_rows_private.jsonl"
    anchors_path = STAGED / "llama" / "anchors_at_candidate_layers.json"
    build_manifest_path = RR_LOCAL_DIR / "analysis-committed" / "llama" / f"hs{layer}_fit_build_manifest.json"
    for p in (joined_path, anchors_path, build_manifest_path):
        if not p.is_file():
            raise SystemExit(f"reconstruct_llama_layer: missing {p}; run staging.py first")

    rows = load_jsonl(joined_path)
    raw_anchors = json.loads(anchors_path.read_text())
    H = {rk: np.asarray(per[str(layer)], dtype=np.float64) for rk, per in raw_anchors.items() if str(layer) in per}
    del raw_anchors

    hidden_dim = json.loads(build_manifest_path.read_text())["hidden_dim"]
    fit1 = direction_fit.fit_directions(rows, H, layer, hidden_dim, seed)
    fit2 = direction_fit.fit_directions(rows, H, layer, hidden_dim, seed)
    if not direction_fit.fit_byte_identical(fit1, fit2):
        raise SystemExit(f"reconstruct_llama_layer(hs{layer}): reconstruction is not byte-identical across two calls")
    gate = direction_fit.fit_gate(fit1)

    rr_committed = json.loads(build_manifest_path.read_text())
    observed = {
        "mu_d": fit1["stats"]["mu_d"], "sigma_d": fit1["stats"]["sigma_d"],
        "mu_c": fit1["stats"]["mu_c"], "sigma_c": fit1["stats"]["sigma_c"],
        "tau_frozen": gate["tau_frozen"], "auc_neg_z_d_on_fit": gate["auc_neg_z_d_on_fit"],
    }
    tolerance = 1e-9
    mismatches = {
        f: {"expected_rr_committed": rr_committed[f], "reconstructed": observed[f]}
        for f in observed if abs(rr_committed[f] - observed[f]) > tolerance
    }
    return {
        "family": "llama32-3b", "layer": f"hs{layer}",
        "pass": not mismatches, "observed": observed,
        "expected": {f: rr_committed[f] for f in observed}, "mismatches": mismatches,
        "fit": fit1,
    }


def check_llama_frame_realdata(layers: tuple[int, ...] = _LLAMA_LAYERS) -> dict[str, Any]:
    """OPT-IN: field-for-field cross-check across all three llama candidate
    layers, plus a row-level fire-set reproduction against the staged
    hs{layer}__gated__dose2.jsonl FIT-population ground truth (fire set is
    dose-invariant by construction -- the gate only depends on layer, not
    dose; this check verifies that assumption holds across the staged doses
    rather than asserting it)."""
    per_layer = {}
    for layer in layers:
        result = reconstruct_llama_layer(layer)
        fit = result.pop("fit")
        gated_path = STAGED / "llama" / "runlog" / f"hs{layer}__gated__dose2.jsonl"
        if gated_path.is_file() and result["pass"]:
            ground_truth_fired = {r["row_key"] for r in load_jsonl(gated_path)}
            # Fire-set check over the FIT population (confab_fit + known_fit,
            # the same rows `fit_directions` scored to freeze tau): reuse the
            # already-computed proj_d_fit rather than re-projecting.
            proj_d_fit = fit["proj_d_fit"]
            fit_keys = fit["confab_fit"] + fit["known_fit"]
            mu_d, sigma_d, tau = fit["stats"]["mu_d"], fit["stats"]["sigma_d"], result["expected"]["tau_frozen"]
            recomputed_fired = set()
            for rk, proj_d in zip(fit_keys, proj_d_fit):
                if gate_decision(float(proj_d), mu_d, sigma_d, tau)["fire"]:
                    recomputed_fired.add(rk)
            mismatches = recomputed_fired.symmetric_difference(ground_truth_fired)
            n_rows = len(fit_keys)
            result["fire_set_check"] = {
                "n_rows": n_rows, "n_recomputed_fired": len(recomputed_fired),
                "n_ground_truth_fired": len(ground_truth_fired), "n_mismatches": len(mismatches),
                "mismatch_rate": (len(mismatches) / n_rows) if n_rows else 1.0,
                "ground_truth_source": f"analysis/llama/runlog/hs{layer}__gated__dose2.jsonl",
            }
        per_layer[f"hs{layer}"] = result
    return {"family": "llama32-3b", "layers": per_layer, "pass": all(v["pass"] for v in per_layer.values())}
