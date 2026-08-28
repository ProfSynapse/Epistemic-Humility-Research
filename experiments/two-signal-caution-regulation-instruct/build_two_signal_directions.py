#!/usr/bin/env python3
"""Two-signal caution regulation -- CPU offline build (step 2/2, after
extract_l34_anchor.py). BF16 SUBSTRATE (2026-07-07 pivot from 4-bit).

Fits u_d, pos_ctrl (caution write direction), and neg_ctrl (confab-propensity)
ALL FRESH on this experiment's own bf16 L34 extraction (the prior 4-bit build
copied pos_ctrl/neg_ctrl from the dark-actuator-screen's 4-bit fit; that fit is
not reusable under bf16, so this build refits both, mirroring the
dark-actuator-screen's own fitting method EXACTLY -- see
`_raw_refuse_and_propensity` below, ported verbatim from
/home/profsynapse/code/ehr-worktrees/dark-screen/experiments/dark-actuator-screen/
build_directions.py:149-165, read in full before writing this). Computes the
2-D orthogonalized write direction c_hat, and materializes the per-example gain
for the both-tail eval pool. All computation is offline / one-shot, per
AMENDMENT.md section 2 (the couple math is read-only at inference time; only
the write is live).

Inputs
------
  AH A0 pool          experiment/phase1/probe/analysis/ah_main/gen_A0/rows.jsonl
                       (1,662 rows; canonical checkout only, gitignored)
  AK Stage-1 pool      experiment/phase1/probe/analysis/ak_stage1/ak_stage1_pool.jsonl
                       (1,338-row unanswerable-only subset with confab labels)
  fresh bf16 extraction analysis/l34_anchor_extract.safetensors (this
                       experiment's own extract_l34_anchor.py output, 1,576
                       rows: 89 known_correct_answered + 1,029 unknown_refused
                       + 309 confab + 149 answerable_refused, ALL bf16,
                       unsloth/Qwen3-4B, no adapter)

Computation (AMENDMENT.md "Design", the two-signal control law)
-----------------------------------------------------------------
  1. u_d = unit(mean(H[known_correct_answered]) - mean(H[unknown_refused]))
     at L34 -- a fresh mean-diff refit (mirrors AK/dark-screen's own
     refuse_dir formula: mean(class0) - mean(class1), unit-normalized).
  2. pos_ctrl / neg_ctrl refit at L34 on the full 1,338-row AK Stage-1
     population (309 confab + 1,029 refuse), verbatim
     dark-actuator-screen build_directions.py method:
       refuse_dir  = unit(mean(H[refuse]) - mean(H[confab]))        (mass-mean)
       prop_dir    = unit(LogisticRegression(saga, C=1.0, tol=1e-3,
                     max_iter=5000).fit(StandardScaler-transformed H, y_confab)
                     .coef_ / scaler.scale_)                        (standardized logistic)
     caution_dir := refuse_dir (pos_ctrl); u_p := prop_dir (neg_ctrl).
  3. c_hat = unit(caution_dir orthogonalized against BOTH u_d and u_p), a 2-D
     Gram-Schmidt erase: build an orthonormal basis Q of span(u_d, u_p) via
     QR, then c_hat = unit(caution_dir - Q @ (Q.T @ caution_dir)).
  4. Both-tail eval pool (458 rows: 309 confab "tighten" + 149
     answerable_refused "release"). For each row, compute raw projections
     proj_d = H.u_d, proj_p = H.u_p, proj_c = H.c_hat. Standardize proj_d and
     proj_p over THIS eval population (mu/sigma), clip each z to [-2, +2]
     (mirrors AC/AO's per-sensor clip). sigma_c = std(proj_c) over the same
     population (AC's "row-population std of the projection onto c_hat").
  5. g_i = -alpha_d * z_d,i + alpha_p * z_p,i. This build uses a single shared
     alpha_d == alpha_p == ALPHA, retuned to the bf16 coherent window (~100,
     see NOTEBOOK.md's bf16 dose-calibration entry) -- see ALPHA/
     MARGINAL_WRITE_CLIP below and NOTEBOOK.md for the calibration sweep.

Outputs (committed, tracked -- NOT the gitignored analysis/ or directions/):
  analysis-committed/source_directions/pos_ctrl_L34.json  (fresh bf16 fit,
                                          NOT copied from dark-screen -- see
                                          provenance.method)
  analysis-committed/source_directions/neg_ctrl_L34.json  (fresh bf16 fit)
  analysis-committed/u_d_L34.json         fitted doubt axis (mechinterp-direction/v1)
  analysis-committed/c_hat_L34.json       the write direction the cell.yaml reads;
                                          "sigma" field = sigma_c so the tuner's
                                          own erase_write formula
                                          (gain*sigma*c_hat) reproduces
                                          g_i*sigma_c*c_hat with gain_field=g_row
                                          and arm strength=ALPHA.
  analysis-committed/eval_pool_manifest.jsonl   458-row DERIVED-COLUMNS-ONLY
                                          manifest (row_key/cell/gold_class/
                                          projections/gains -- NO question
                                          text, NO aliases; see PROVENANCE.md
                                          and materialize_eval_pool.py, which
                                          joins this back to question text
                                          fetched from the private HF staging
                                          repo at run time to produce the
                                          gitignored local
                                          analysis/eval_pool_both_tail.jsonl
                                          cell.yaml's surface.rows_path reads).
  analysis-committed/build_manifest.json   full fit provenance + report numbers
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np

REPO_ROOT = Path("/home/profsynapse/code/Epistemic-Humility-Research")
PROBE_DIR = REPO_ROOT / "experiment" / "phase1" / "probe"
sys.path.insert(0, str(PROBE_DIR))
from amendment_ah_stage0_extract import safe_key_for  # noqa: E402

HERE = Path(__file__).resolve().parent
ANALYSIS = HERE / "analysis"
COMMITTED = HERE / "analysis-committed"

AH_A0_ROWS = PROBE_DIR / "analysis" / "ah_main" / "gen_A0" / "rows.jsonl"
AK_STAGE1_POOL = PROBE_DIR / "analysis" / "ak_stage1" / "ak_stage1_pool.jsonl"

EXTRACT_TENSORS = ANALYSIS / "l34_anchor_extract.safetensors"
EXTRACT_MANIFEST = ANALYSIS / "l34_anchor_extract_manifest.json"

LAYER_BLOCK = 33  # tuner 0-indexed decoder block for "L34"
HIDDEN_DIM = 2560
Z_CLIP = 2.0

# Shared alpha_d == alpha_p (single pre-registered scalar, no per-sensor
# sweep). BF16 DOSE-UNITS FIX (2026-07-07, red-team-confirmed bug, see
# NOTEBOOK.md's bf16 dose-calibration-fix entry for the full derivation).
#
# THE BUG (now fixed): the tuner's erase_write law writes gain*sigma as the
# realized projection (synaptic-tuner/MechInterp/intervention/hooks.py
# docstring lines 7-12) -- the commanded setpoint is gain*sigma, NOT gain.
# analysis/dose_escalation_bf16_ambient_relative.py constructs the REAL
# tuner InterventionHook with this experiment's own sigma_c=21.36 and passes
# `strength = k * ambient_mean` as the GAIN argument, so the sweep's printed
# "strength" column (and the "median first-coherent-move strength ~20-27 /
# median first-garbage-collapse strength ~40-43" language in the prior
# version of this comment and in NOTEBOOK.md's superseded bf16-pivot entry)
# was a GAIN, not a realized write. The PRIOR ALPHA=2.0/CLIP=40.0 build
# treated those gain numbers as if they were setpoints and calibrated
# directly against them -- an ~sigma_c-factor (~21x) unit conflation that
# left the real run ~20x under-dosed (realized median write ~25-31, nowhere
# near the real coherent window).
#
# THE FIX: the sweep script was extended to record `hook.last_readback`
# (the GPU-measured, POST-write projection onto c_hat_L34 -- the ground-truth
# unit) per k, then rerun (24 rows, same method, same c_hat_L34.json,
# 21/24 usable). In REALIZED-READBACK units the coherent window is:
#   first-coherent-move |readback|: n=21, median=531.9 (confab median=456.0,
#     answerable_refused median=546.0), p25=452.0, p75=587.9.
#   first-garbage-collapse |readback|: n=21, median=952.0 (confab
#     median=808.0, answerable_refused median=997.9), p25=743.8, p90=1112.0.
# (Order-of-hundreds, consistent with the dark-screen's own bf16
# un-orthogonalized pos_ctrl_L34 prior of coherent~100/collapse>=500 scaled by
# this direction's own sigma_c, and with the hand-computed 530/843 estimate
# from the same strength*sigma_c arithmetic.) One row
# (ahx::kuq_ku_unknown_x::000518) shows a non-monotonic garbage flag around
# readback ~-374 to -588 (recovers to non-garbage at a HIGHER dose before
# re-collapsing at -800) -- a per-row heuristic-detector fragility, not a
# real early collapse; per the same convention as the prior build's
# discussion of its own low-collapse outlier, this is flagged as an open
# per-row-fragility finding (NOTEBOOK.md), NOT used to set the clip floor
# (doing so would suppress the whole effect).
#
# ALPHA retuned from 2.0 to 40.0 (z_d/z_p and their [-2,+2] clip are
# unchanged; only this scalar and MARGINAL_WRITE_CLIP move). At ALPHA=40.0 /
# MARGINAL_WRITE_CLIP=750.0, this eval pool's own abs_median REALIZED write
# (== marginal_write, since the tuner writes gain*sigma == marginal_write
# exactly) is 506.5 (confab, n=309, 23.0% clipped) / 624.7 (answerable_refused,
# n=149, 44.3% clipped) / 541.1 overall -- both cell medians land inside the
# confirmed coherent-move-to-collapse window (above each cell's own median
# move readback, below each cell's own median collapse readback) and no row
# in the pool reaches 998 (answerable_refused's own median collapse floor).
ALPHA = 40.0

# Hard collapse-safety clip on the FINAL marginal write (post gain-sum,
# post-sigma_c; this quantity IS the realized readback the tuner's erase_write
# law will write, per hooks.py's gain*sigma law -- see the ALPHA comment
# above for the full readback-unit derivation), applied unconditionally
# regardless of ALPHA: no row may command a write at or above this
# experiment's own confirmed bf16 collapse floor
# (analysis/dose_ladder_bf16_readback_results.jsonl: median
# first-garbage-collapse |readback|=808.0 on the confab cell, the LOWER of
# the two cells' medians; 997.9 on answerable_refused). 750.0 sits below BOTH
# cells' median collapse floors (margin ~58 below confab's, the tighter
# constraint; ~248 below answerable_refused's) -- the single fragility
# outlier discussed above (readback ~-374 to -588, non-monotonic) is NOT
# used as the clip floor, mirroring the prior build's own convention (an
# outlier-driven clip would suppress the whole effect; it is reported as an
# open finding in NOTEBOOK.md instead). The clip is applied to marginal_write
# and then divided back through sigma_c to get the CLIPPED g_two_signal value
# actually stored in the eval pool / read by the tuner's gain_field -- the
# write the model receives always respects this clip; it is not merely a
# post-hoc reporting clip.
MARGINAL_WRITE_CLIP = 750.0


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def unit(v: np.ndarray) -> np.ndarray:
    n = float(np.linalg.norm(v))
    return v / n if n else v


def load_jsonl(p: Path) -> list[dict]:
    return [json.loads(ln) for ln in p.open(encoding="utf-8") if ln.strip()]


def _sanitize_key(row_key: str) -> str:
    return row_key.replace(":", "_")


# ---------------------------------------------------------------------------
# pos_ctrl / neg_ctrl fit -- VERBATIM the dark-actuator-screen's
# build_directions.py:_raw_refuse_and_propensity (pre-QR refuse/propensity
# directions, before that screen's own QR mix). Same formulas, this
# experiment's own bf16 activations + AK Stage-1 confab_on_unanswerable
# labels (not a re-derivation of a different method).
# ---------------------------------------------------------------------------

def _raw_refuse_and_propensity(H_anchor: np.ndarray, y_confab: np.ndarray
                               ) -> tuple[np.ndarray, np.ndarray, dict]:
    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import StandardScaler

    refuse_mean = H_anchor[y_confab == 0].mean(0)
    confab_mean = H_anchor[y_confab == 1].mean(0)
    refuse_dir = unit(refuse_mean - confab_mean)

    sc = StandardScaler().fit(H_anchor)
    Z = sc.transform(H_anchor)
    clf = LogisticRegression(solver="saga", tol=1e-3, max_iter=5000, C=1.0).fit(Z, y_confab)
    prop_raw = clf.coef_.ravel() / sc.scale_
    prop_dir = unit(prop_raw)
    fit_info = {
        "n_confab": int(y_confab.sum()), "n_refuse": int((1 - y_confab).sum()),
        "logreg": {"solver": "saga", "tol": 1e-3, "max_iter": 5000, "C": 1.0},
    }
    return refuse_dir, prop_dir, fit_info


# ---------------------------------------------------------------------------
# Load activations
# ---------------------------------------------------------------------------

def load_fresh_extract() -> dict[str, np.ndarray]:
    from safetensors.numpy import load_file
    t = load_file(str(EXTRACT_TENSORS))
    return {k: np.asarray(v, dtype=np.float64) for k, v in t.items()}


def main() -> int:
    COMMITTED.mkdir(parents=True, exist_ok=True)
    (COMMITTED / "source_directions").mkdir(parents=True, exist_ok=True)

    # -- 0. load pools -------------------------------------------------
    ah_a0 = load_jsonl(AH_A0_ROWS)
    ah_a0_by_key = {r["row_key"]: r for r in ah_a0}
    ak_pool = load_jsonl(AK_STAGE1_POOL)
    ak_by_key = {r["row_key"]: r for r in ak_pool}

    fresh = load_fresh_extract()
    extract_manifest = json.loads(EXTRACT_MANIFEST.read_text())
    assert extract_manifest["substrate"] == "bf16"
    assert extract_manifest["base_model"] == "unsloth/Qwen3-4B"
    role_by_key = {rm["row_key"]: rm["role"] for rm in extract_manifest["rows"]}

    known_correct_answered = [
        rk for rk, role in role_by_key.items() if role == "known_correct_answered"
    ]
    answerable_refused = [
        rk for rk, role in role_by_key.items() if role == "answerable_refused"
    ]
    unknown_refused = [rk for rk, role in role_by_key.items() if role == "unknown_refused"]
    confab = [rk for rk, role in role_by_key.items() if role == "confab"]

    print(f"[build] known_correct_answered={len(known_correct_answered)} "
          f"unknown_refused={len(unknown_refused)} confab={len(confab)} "
          f"answerable_refused={len(answerable_refused)}")
    assert len(known_correct_answered) == 89
    assert len(unknown_refused) == 1029
    assert len(confab) == 309
    assert len(answerable_refused) == 149

    # -- 1. fit u_d ------------------------------------------------------
    H_known = np.stack([fresh[_sanitize_key(rk)] for rk in known_correct_answered])
    H_unknown_refused = np.stack([fresh[_sanitize_key(rk)] for rk in unknown_refused])
    u_d = unit(H_known.mean(0) - H_unknown_refused.mean(0))

    # -- 2. fit pos_ctrl (caution_dir) / neg_ctrl (u_p) on the FULL AK
    #    Stage-1 population (1,338 = 309 confab + 1,029 refuse), fresh bf16 --
    #    order matters only for the row<->label pairing, not the math.
    ak_rows_in_order = unknown_refused + confab
    H_ak = np.stack([fresh[_sanitize_key(rk)] for rk in ak_rows_in_order])
    y_confab = np.array(
        [0] * len(unknown_refused) + [1] * len(confab), dtype=int
    )
    caution_dir, u_p, ctrl_fit_info = _raw_refuse_and_propensity(H_ak, y_confab)

    # -- 3. 2-D Gram-Schmidt: c_hat = caution_dir orthogonalized vs {u_d, u_p} --
    M = np.stack([u_d, u_p], axis=1)  # dim x 2
    Q, _ = np.linalg.qr(M)
    c_perp = caution_dir - Q @ (Q.T @ caution_dir)
    c_hat = unit(c_perp)

    cos_ud_up = float(np.dot(u_d, u_p))
    cos_caution_chat = float(np.dot(caution_dir, c_hat))

    # -- 4. both-tail eval pool: gather activations + projections ---------
    eval_rows = []
    for rk in confab:
        H = fresh[_sanitize_key(rk)]
        eval_rows.append((rk, "confab", H, ak_by_key[rk]))
    for rk in answerable_refused:
        H = fresh[_sanitize_key(rk)]
        eval_rows.append((rk, "answerable_refused", H, ah_a0_by_key[rk]))

    Hmat = np.stack([r[2] for r in eval_rows])
    proj_d = Hmat @ u_d
    proj_p = Hmat @ u_p
    proj_c = Hmat @ c_hat

    mu_d, sigma_d = float(proj_d.mean()), float(proj_d.std())
    mu_p, sigma_p = float(proj_p.mean()), float(proj_p.std())
    mu_c, sigma_c = float(proj_c.mean()), float(proj_c.std())

    z_d = np.clip((proj_d - mu_d) / sigma_d, -Z_CLIP, Z_CLIP)
    z_p = np.clip((proj_p - mu_p) / sigma_p, -Z_CLIP, Z_CLIP)
    g_row_unclipped = -ALPHA * z_d + ALPHA * z_p  # = ALPHA * (z_p - z_d)
    marginal_write_unclipped = g_row_unclipped * sigma_c
    marginal_write = np.clip(marginal_write_unclipped, -MARGINAL_WRITE_CLIP, MARGINAL_WRITE_CLIP)
    g_row = marginal_write / sigma_c

    # -- 5. write eval_pool_manifest.jsonl (COMMITTED, derived columns ONLY --
    #    no question text, no aliases; see PROVENANCE.md) ------------------
    out_path = COMMITTED / "eval_pool_manifest.jsonl"
    with out_path.open("w", encoding="utf-8") as fh:
        for i, (rk, cell, H, src_row) in enumerate(eval_rows):
            rec = {
                "row_key": rk,
                "safe_key": safe_key_for(rk),
                "cell": cell,
                "gold_class": "unanswerable" if cell == "confab" else "answerable",
                "category_canon": src_row.get("category_canon"),
                "source": src_row.get("source"),
                "proj_d": float(proj_d[i]), "proj_p": float(proj_p[i]),
                "proj_c": float(proj_c[i]),
                "z_d": float(z_d[i]), "z_p": float(z_p[i]),
                "g_two_signal": float(g_row[i]),
                "marginal_write": float(marginal_write[i]),
                "g_two_signal_unclipped": float(g_row_unclipped[i]),
                "marginal_write_unclipped": float(marginal_write_unclipped[i]),
                "clipped": bool(abs(marginal_write_unclipped[i]) > MARGINAL_WRITE_CLIP),
            }
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")

    # -- 6. write direction JSONs ------------------------------------------
    def direction_json(vector: np.ndarray, sigma: float, role: str, extra_prov: dict) -> dict:
        return {
            "schema_version": "mechinterp-direction/v1",
            "layer": LAYER_BLOCK,
            "hidden_dim": HIDDEN_DIM,
            "normalized": True,
            "vector": [float(x) for x in vector],
            "raw_norm": 1.0,
            "intercept": 0.0,
            "mu": [0.0] * HIDDEN_DIM,
            "sigma": sigma,
            "calibration": {},
            "recipe": {"source": "build_two_signal_directions.py"},
            "provenance": {"role": role, "amendment": "two-signal-caution-regulation-instruct",
                          "substrate": "bf16", "base_model": "unsloth/Qwen3-4B",
                          **extra_prov},
        }

    u_d_json = direction_json(
        u_d, 1.0, "doubt_sensor_u_d",
        {"method": "mean(H[known_correct_answered]) - mean(H[unknown_refused]), unit-normalized",
         "n_known_correct_answered": len(known_correct_answered),
         "n_unknown_refused": len(unknown_refused),
         "layer_label": "L34", "fit_pool": "AH A0 (known) / AK Stage-1 (unknown), bf16 refit",
         "fit_pool_sha256": {
             "ah_a0_rows": _sha256_file(AH_A0_ROWS),
             "ak_stage1_pool": _sha256_file(AK_STAGE1_POOL),
         },
         "mu_d_over_eval_pool": mu_d, "sigma_d_over_eval_pool": sigma_d,
         "cos_u_d_u_p": cos_ud_up},
    )
    (COMMITTED / "u_d_L34.json").write_text(json.dumps(u_d_json, indent=2))

    pos_ctrl_json = direction_json(
        caution_dir, 1.0, "positive_control",
        {"signal": "refuse_vs_confab_mass_mean",
         "method": "dark-actuator-screen build_directions.py:_raw_refuse_and_propensity "
                    "(pre-QR refuse direction), verbatim, refit on this experiment's own "
                    "bf16 AK Stage-1 extraction (NOT copied from the dark-screen's 4-bit fit)",
         "layer_label": "L34", "fit_pool": "AK Stage-1 (1,338 rows: 309 confab + 1,029 refuse)",
         "fit_pool_sha256": _sha256_file(AK_STAGE1_POOL),
         **ctrl_fit_info},
    )
    (COMMITTED / "source_directions" / "pos_ctrl_L34.json").write_text(
        json.dumps(pos_ctrl_json, indent=2))

    neg_ctrl_json = direction_json(
        u_p, 1.0, "negative_control",
        {"signal": "confab_propensity_logistic",
         "method": "dark-actuator-screen build_directions.py:_raw_refuse_and_propensity "
                    "(pre-QR propensity direction), verbatim, refit on this experiment's own "
                    "bf16 AK Stage-1 extraction (NOT copied from the dark-screen's 4-bit fit)",
         "layer_label": "L34", "fit_pool": "AK Stage-1 (1,338 rows: 309 confab + 1,029 refuse)",
         "fit_pool_sha256": _sha256_file(AK_STAGE1_POOL),
         **ctrl_fit_info},
    )
    (COMMITTED / "source_directions" / "neg_ctrl_L34.json").write_text(
        json.dumps(neg_ctrl_json, indent=2))

    c_hat_json = direction_json(
        c_hat, sigma_c, "caution_write_c_hat",
        {"orthogonalized_against": ["u_d_L34.json", "source_directions/neg_ctrl_L34.json"],
         "source_caution_dir": "source_directions/pos_ctrl_L34.json",
         "cos_caution_dir_c_hat": cos_caution_chat,
         "mu_c_over_eval_pool": mu_c, "sigma_c_over_eval_pool": sigma_c,
         "eval_pool_manifest": "analysis-committed/eval_pool_manifest.jsonl",
         "n_eval_pool": len(eval_rows)},
    )
    (COMMITTED / "c_hat_L34.json").write_text(json.dumps(c_hat_json, indent=2))

    # -- 7. report + manifest ----------------------------------------------
    cell_arr = np.array([r[1] for r in eval_rows])

    def _dist(mask: np.ndarray, mw_arr: np.ndarray, mw_unclipped_arr: np.ndarray) -> dict:
        sub = mw_arr[mask]
        sub_unclipped = mw_unclipped_arr[mask]
        return {
            "n": int(mask.sum()),
            "min": float(sub.min()), "p10": float(np.percentile(sub, 10)),
            "p25": float(np.percentile(sub, 25)), "median": float(np.median(sub)),
            "p75": float(np.percentile(sub, 75)), "p90": float(np.percentile(sub, 90)),
            "max": float(sub.max()),
            "mean": float(sub.mean()),
            "abs_median": float(np.median(np.abs(sub))),
            "abs_mean": float(np.abs(sub).mean()),
            "frac_positive": float((sub > 0).mean()),
            # Readback-unit coherent window (corrected 2026-07-07, see the
            # ALPHA/MARGINAL_WRITE_CLIP comments above for the full
            # dose_ladder_bf16_readback_results.jsonl derivation): move
            # readback median 531.9 (p25=452.0), collapse readback median
            # 952.0 (confab cell's own, lower, collapse median is 808.0).
            # These bounds replace the STALE [15,40]/[>=45] gain-unit
            # thresholds from the pre-fix build (that window was itself the
            # bug this fix corrects; keeping the old numbers here would be
            # silently re-committing the unit error into the report).
            "frac_abs_in_bf16_readback_window_ge_452_le_808": float(
                np.mean((np.abs(sub) >= 452) & (np.abs(sub) <= 808))),
            "frac_abs_ge_808": float(np.mean(np.abs(sub) >= 808)),
            "frac_clipped": float(np.mean(np.abs(sub_unclipped) > MARGINAL_WRITE_CLIP)),
        }

    report = {
        "substrate": "bf16", "base_model": "unsloth/Qwen3-4B",
        "n_known_correct_answered": len(known_correct_answered),
        "n_unknown_refused": len(unknown_refused),
        "n_confab_tighten_tail": len(confab),
        "n_answerable_refused_release_tail": len(answerable_refused),
        "n_eval_pool_total": len(eval_rows),
        "cos_u_d_u_p": cos_ud_up,
        "cos_caution_dir_c_hat": cos_caution_chat,
        "mu_d": mu_d, "sigma_d": sigma_d,
        "mu_p": mu_p, "sigma_p": sigma_p,
        "mu_c": mu_c, "sigma_c": sigma_c,
        "alpha_d": ALPHA, "alpha_p": ALPHA,
        "marginal_write_clip": MARGINAL_WRITE_CLIP,
        "marginal_write_distribution": {
            "overall": _dist(np.ones(len(eval_rows), dtype=bool), marginal_write, marginal_write_unclipped),
            "confab": _dist(cell_arr == "confab", marginal_write, marginal_write_unclipped),
            "answerable_refused": _dist(cell_arr == "answerable_refused", marginal_write, marginal_write_unclipped),
        },
        "extract_manifest_sha256": _sha256_file(EXTRACT_MANIFEST),
        "ah_a0_rows_sha256": _sha256_file(AH_A0_ROWS),
        "ak_stage1_pool_sha256": _sha256_file(AK_STAGE1_POOL),
    }
    (COMMITTED / "build_manifest.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
