#!/usr/bin/env python3
"""Two-signal caution regulation -- CPU offline build (step 2/2, after
extract_l34_anchor.py). Fits u_d, loads u_p + caution_dir, computes the 2-D
orthogonalized write direction c_hat, and materializes the per-example gain
for the both-tail eval pool. All computation is offline / one-shot, per
AMENDMENT.md section 2 (the couple math is read-only at inference time; only
the write is live).

Inputs
------
  AH A0 pool          experiment/phase1/probe/analysis/ah_main/gen_A0/rows.jsonl
                       (1,662 rows; canonical checkout only, gitignored)
  AK Stage-1 pool      experiment/phase1/probe/analysis/ak_stage1/ak_stage1_pool.jsonl
                       (1,338-row unanswerable-only subset with confab labels)
  AK Stage-1 tensors   $HOME/ak_census_data/ak-stage1-raw-base-r1/tensors/extracted/
                       *.safetensors, key "L34@anchor" (cached, 1,338 rows)
  fresh extraction     analysis/l34_anchor_extract.safetensors (this experiment's
                       extract_l34_anchor.py output, 238 rows: 89
                       known_correct_answered + 149 answerable_refused)
  dark-actuator-screen directions (fitted, null-result experiment; copied here
                       for provenance -- NOT re-fit): pos_ctrl_L34.json
                       (caution_dir, refuse_vs_confab mass-mean) and
                       neg_ctrl_L34.json (u_p, confab-propensity logistic),
                       both fit on the SAME 1,338-row AK Stage-1 pool. Source:
                       /home/profsynapse/code/ehr-worktrees/dark-screen/
                       experiments/dark-actuator-screen/directions/ (gitignored
                       worktree output of that experiment's build_directions.py).

Computation (AMENDMENT.md "Design", the two-signal control law)
-----------------------------------------------------------------
  1. u_d = unit(mean(H[known_correct_answered]) - mean(H[unknown_refused]))
     at L34 -- a fresh mean-diff refit (mirrors AK/dark-screen's own
     refuse_dir formula: mean(class0) - mean(class1), unit-normalized).
  2. u_p = neg_ctrl_L34's vector (confab-propensity logistic direction),
     caution_dir = pos_ctrl_L34's vector (refuse_vs_confab mass-mean).
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
     alpha_d == alpha_p == ALPHA (see ALPHA below) -- see this script's
     printed report / the build manifest for the reasoning and the resulting
     marginal-write distribution (g_i * sigma_c along c_hat).

Outputs (committed, tracked -- NOT the gitignored analysis/ or directions/):
  analysis-committed/source_directions/pos_ctrl_L34.json   (copied, sha recorded)
  analysis-committed/source_directions/neg_ctrl_L34.json   (copied, sha recorded)
  analysis-committed/u_d_L34.json         fitted doubt axis (mechinterp-direction/v1)
  analysis-committed/c_hat_L34.json       the write direction the cell.yaml reads;
                                          "sigma" field = sigma_c so the tuner's
                                          own erase_write formula
                                          (gain*sigma*c_hat) reproduces
                                          g_i*sigma_c*c_hat with gain_field=g_row
                                          and arm strength=ALPHA.
  analysis-committed/eval_pool_both_tail.jsonl   458-row surface.rows_path pool
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
AK_TENSORS_DIR = Path.home() / "ak_census_data" / "ak-stage1-raw-base-r1" / "tensors" / "extracted"

DARK_SCREEN_DIRECTIONS = Path(
    "/home/profsynapse/code/ehr-worktrees/dark-screen/experiments/"
    "dark-actuator-screen/directions"
)

EXTRACT_TENSORS = ANALYSIS / "l34_anchor_extract.safetensors"
EXTRACT_MANIFEST = ANALYSIS / "l34_anchor_extract_manifest.json"

LAYER_BLOCK = 33  # tuner 0-indexed decoder block for "L34"
HIDDEN_DIM = 2560
Z_CLIP = 2.0

# Shared alpha_d == alpha_p (single pre-registered scalar, no per-sensor
# sweep). REVISED (2026-07-07, lead-directed dose-fix -- see NOTEBOOK.md):
# the first pass (ALPHA=5.0, no hard clip) put only ~24% of the both-tail
# pool's |marginal_write| inside the dark-screen's validated 150-300 coherent
# window, with a 553-magnitude outlier well past the 400 collapse floor.
# ALPHA is retuned upward (per-cell median |write| ~150-300, targeting the
# 200-225 middle) and a HARD CLIP is added (see MARGINAL_WRITE_CLIP) so no
# row's commanded write can enter the collapse regime regardless of how
# extreme its (z_p, z_d) pair is. Calibration sweep (this script's own
# printed report at each candidate ALPHA, on the FIXED z_d/z_p columns --
# not a gate sweep, no gates were evaluated while choosing this):
#   ALPHA= 8: confab median|write|=140  (just under window) 9%  clipped
#   ALPHA= 9: confab median|write|=158, release median=244, 15%/32% clipped
#   ALPHA=10: confab median|write|=175, release median=272, 18%/37% clipped
#   ALPHA=12: confab median|write|=210, release median=326 (drifts ABOVE the
#             300 window edge, into the un-validated 300-400 gray zone)
# ALPHA=10.0 is picked: both cells' medians land inside [150, 300] (175 / 272)
# without either drifting above the window, and a MAJORITY of each cell
# (81.6% confab / 63.1% release) stays below the hard clip, i.e. still
# z-proportional rather than pinned -- the clip caps only the extreme tail,
# it does not flatten the bulk of the distribution. See build_manifest.json
# "marginal_write_distribution" for the realized numbers this run.
ALPHA = 10.0

# Hard collapse-safety clip on the FINAL marginal write (post gain-sum,
# post-sigma_c), applied unconditionally regardless of ALPHA: no row may
# command a write at or above the dark-screen's observed collapse floor
# (>=400). 350 keeps a documented margin below that floor. The clip is
# applied to marginal_write and then divided back through sigma_c to get the
# CLIPPED g_two_signal value actually stored in the eval pool / read by the
# tuner's gain_field -- the write the model receives always respects this
# clip; it is not merely a post-hoc reporting clip.
MARGINAL_WRITE_CLIP = 350.0


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def unit(v: np.ndarray) -> np.ndarray:
    n = float(np.linalg.norm(v))
    return v / n if n else v


def load_jsonl(p: Path) -> list[dict]:
    return [json.loads(ln) for ln in p.open(encoding="utf-8") if ln.strip()]


# ---------------------------------------------------------------------------
# Load activations
# ---------------------------------------------------------------------------

def load_fresh_extract() -> dict[str, np.ndarray]:
    from safetensors.numpy import load_file
    t = load_file(str(EXTRACT_TENSORS))
    return {k: np.asarray(v, dtype=np.float64) for k, v in t.items()}


def load_ak_cached_anchor(row_key: str) -> np.ndarray | None:
    skey = safe_key_for(row_key)
    path = AK_TENSORS_DIR / f"{skey}.safetensors"
    if not path.is_file():
        return None
    from safetensors.numpy import load_file
    t = load_file(str(path))
    key = "L34@anchor"
    if key not in t:
        return None
    return np.asarray(t[key], dtype=np.float64)


def _sanitize_key(row_key: str) -> str:
    return row_key.replace(":", "_")


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
    role_by_key = {rm["row_key"]: rm["role"] for rm in extract_manifest["rows"]}

    known_correct_answered = [
        rk for rk, role in role_by_key.items() if role == "known_correct_answered"
    ]
    answerable_refused = [
        rk for rk, role in role_by_key.items() if role == "answerable_refused"
    ]
    unknown_refused = [r["row_key"] for r in ak_pool if not r["confab_on_unanswerable"]]
    confab = [r["row_key"] for r in ak_pool if r["confab_on_unanswerable"]]

    print(f"[build] known_correct_answered={len(known_correct_answered)} "
          f"unknown_refused={len(unknown_refused)} confab={len(confab)} "
          f"answerable_refused={len(answerable_refused)}")
    assert len(known_correct_answered) == 89
    assert len(unknown_refused) == 1029
    assert len(confab) == 309
    assert len(answerable_refused) == 149

    # -- 1. fit u_d ------------------------------------------------------
    H_known = np.stack([fresh[_sanitize_key(rk)] for rk in known_correct_answered])
    H_unknown = np.stack([load_ak_cached_anchor(rk) for rk in unknown_refused])
    assert not any(v is None for v in H_unknown), "missing cached AK anchor tensor"
    u_d = unit(H_known.mean(0) - H_unknown.mean(0))

    # -- 2. load u_p / caution_dir, copy for provenance -------------------
    pos_ctrl_src = DARK_SCREEN_DIRECTIONS / "pos_ctrl_L34.json"
    neg_ctrl_src = DARK_SCREEN_DIRECTIONS / "neg_ctrl_L34.json"
    pos_ctrl = json.loads(pos_ctrl_src.read_text())
    neg_ctrl = json.loads(neg_ctrl_src.read_text())
    assert pos_ctrl["layer"] == LAYER_BLOCK and neg_ctrl["layer"] == LAYER_BLOCK
    caution_dir = np.asarray(pos_ctrl["vector"], dtype=np.float64)
    u_p = np.asarray(neg_ctrl["vector"], dtype=np.float64)

    for src, name in ((pos_ctrl_src, "pos_ctrl_L34.json"), (neg_ctrl_src, "neg_ctrl_L34.json")):
        dst = COMMITTED / "source_directions" / name
        dst.write_text(src.read_text())

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
        H = load_ak_cached_anchor(rk)
        assert H is not None
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
    # Hard collapse-safety clip on the WRITE the model actually receives:
    # clip marginal_write to +/- MARGINAL_WRITE_CLIP, then divide back through
    # sigma_c to get the gain value stored in g_two_signal (the field the
    # tuner's gain_field reads) -- the clip binds the real write, not just a
    # reported number.
    marginal_write = np.clip(marginal_write_unclipped, -MARGINAL_WRITE_CLIP, MARGINAL_WRITE_CLIP)
    g_row = marginal_write / sigma_c

    # -- 5. write eval_pool_both_tail.jsonl --------------------------------
    out_path = COMMITTED / "eval_pool_both_tail.jsonl"
    with out_path.open("w", encoding="utf-8") as fh:
        for i, (rk, cell, H, src_row) in enumerate(eval_rows):
            rec = {
                "row_key": rk,
                "safe_key": safe_key_for(rk),
                "cell": cell,
                "question": (
                    src_row.get("question")
                    if cell == "answerable_refused"
                    else ah_a0_by_key.get(rk, {}).get("question")
                ),
                "aliases": (
                    ah_a0_by_key.get(rk, {}).get("aliases", [])
                    if cell == "answerable_refused" else []
                ),
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
    # every question must be present (answerable_refused rows carry it
    # directly on the AH A0 row; confab rows join it back from the AH A0 pool
    # by row_key -- AK Stage-1 itself excludes question text, AH A0 does not).
    missing_q = sum(1 for r in load_jsonl(out_path) if not r.get("question"))
    assert missing_q == 0, f"{missing_q} eval-pool rows missing question text"

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
                          **extra_prov},
        }

    u_d_json = direction_json(
        u_d, 1.0, "doubt_sensor_u_d",
        {"method": "mean(H[known_correct_answered]) - mean(H[unknown_refused]), unit-normalized",
         "n_known_correct_answered": len(known_correct_answered),
         "n_unknown_refused": len(unknown_refused),
         "layer_label": "L34", "fit_pool": "AH A0 (known) / AK Stage-1 (unknown)",
         "fit_pool_sha256": {
             "ah_a0_rows": _sha256_file(AH_A0_ROWS),
             "ak_stage1_pool": _sha256_file(AK_STAGE1_POOL),
         },
         "mu_d_over_eval_pool": mu_d, "sigma_d_over_eval_pool": sigma_d,
         "cos_u_d_u_p": cos_ud_up},
    )
    (COMMITTED / "u_d_L34.json").write_text(json.dumps(u_d_json, indent=2))

    c_hat_json = direction_json(
        c_hat, sigma_c, "caution_write_c_hat",
        {"orthogonalized_against": ["u_d_L34.json", "source_directions/neg_ctrl_L34.json"],
         "source_caution_dir": "source_directions/pos_ctrl_L34.json",
         "cos_caution_dir_c_hat": cos_caution_chat,
         "mu_c_over_eval_pool": mu_c, "sigma_c_over_eval_pool": sigma_c,
         "eval_pool": "analysis-committed/eval_pool_both_tail.jsonl",
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
            "frac_abs_in_150_300": float(np.mean((np.abs(sub) >= 150) & (np.abs(sub) <= 300))),
            "frac_abs_ge_400": float(np.mean(np.abs(sub) >= 400)),
            "frac_clipped": float(np.mean(np.abs(sub_unclipped) > MARGINAL_WRITE_CLIP)),
        }

    report = {
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
        "fresh_extract_manifest_sha256": _sha256_file(EXTRACT_MANIFEST),
        "pos_ctrl_src_sha256": _sha256_file(pos_ctrl_src),
        "neg_ctrl_src_sha256": _sha256_file(neg_ctrl_src),
        "ah_a0_rows_sha256": _sha256_file(AH_A0_ROWS),
        "ak_stage1_pool_sha256": _sha256_file(AK_STAGE1_POOL),
    }
    (COMMITTED / "build_manifest.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
