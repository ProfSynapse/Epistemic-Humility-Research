#!/usr/bin/env python3
"""PAR sensor refit — fit the reward sensor on the training-start checkpoint.

Lab-notebook work feeding Amendment AI (probe-as-reward) launch conditions 2
and 3. Branch par-mining-recalibration. Rationale: par_recalibration.json
showed the frozen raw-base AF-600 probe is BLIND on the trained lineage
(p_unanswerable ~= 1.0 on 99.9% of GRPO-v2 states), so the reward sensor must
be refit on the checkpoint PAR training starts from (clean-SFT merged base)
and the design constants re-derived from the refit distribution.

Inputs (extracted overnight on the local 3090, runner task):
  analysis/par_sensor_refit/union_pregen/    18,496 union-surface pre-gen
      states on the clean-SFT merged base (gold labels known/unknown)
  analysis/par_sensor_refit/mining_pregen/   9,397 mining-candidate pre-gen
      states on the same checkpoint (all candidates gold-unanswerable);
      scored only when its rows.jsonl is complete (auto-detected)

Recipe (byte-matches amendment_ah_stage0_fit_probes.py = the AF-600 lineage):
  StandardScaler + LogisticRegression(C=1.0, max_iter=5000), label known=1,
  decision_function > 0 => probe-says-known; p_unanswerable = sigmoid(-score).
  Held-out AUROC = 5-fold StratifiedKFold(shuffle, random_state=0) OOF.

Distribution hygiene: every union-row statistic (p summary, saturation, flip
curves, divergent classification, mixture math) uses the OOF score — the row
is scored by a fold model that never trained on it — so the derived constants
are not inflated by in-sample saturation. The persisted full-fit probes are
the frozen train-time sensor. Mining rows are disjoint from the union surface,
so the full-fit probe is out-of-sample for them.

Derived constants (Amendment AI section 1.2-1.3 rules, locked pre-launch):
  w_c  = largest w in {0.05..0.50 step 0.05} with answer-side flip fraction
         <= 2% on the GOLD-UNANSWERABLE stratum (the original D1 rule that
         produced the raw-base 0.20 cap), flip condition |2p-1| < w.
  w_a  = symmetric (= w_c) unless the gold-ANSWERABLE stratum curve binds at
         a smaller w, then the same largest-w rule on that stratum.
  mixture = smallest divergent fraction m with divergent advantage-mass share
         m*mu_d / (m*mu_d + (1-m)*mu_c) >= 0.25 (mu = mean |2p-1| margin).

Writes analysis/par_sensor_refit/:
  probes/probe_{L20,L24,L28}_cleansft.joblib   frozen refit sensors
  union_refit_rows.jsonl                       per-row OOF scores (gitignored)
  mining_refit_rows.jsonl                      per-row full-fit scores (when B done)
  refit_result.json                            full result
and a committed copy under experiments/probe-as-reward/artifacts/.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from safetensors import safe_open
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import roc_auc_score
import joblib

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from path_compat import artifact_dir, repo_root  # noqa: E402

ARTIFACT_DIR = artifact_dir()
CANONICAL = repo_root()
REFIT_ROOT = CANONICAL / "experiment/phase1/probe/analysis/par_sensor_refit"
# v2 defaults: training-configuration (4-bit) states; --variant v1 restores
VARIANTS = {
    "v1": {"union": "union_pregen", "mining": "mining_pregen",
            "probes": "probes", "result": "refit_result.json",
            "copy": "par_sensor_refit.json", "suffix": "cleansft"},
    "v2": {"union": "union_pregen_4bit", "mining": "mining_pregen_4bit",
            "probes": "probes_v2", "result": "refit_result_v2.json",
            "copy": "par_sensor_refit_v2.json", "suffix": "cleansft4bit"},
}

LAYERS = ["L20", "L24", "L28"]
SENSOR_LAYER = "L24"
N_FOLDS = 5
CV_RANDOM_STATE = 0
W_GRID = [0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50]
AUROC_FLOOR = 0.9          # Amendment AI launch condition 2
FLIP_BUDGET = 0.02
MASS_TARGET = 0.25
MINING_EXPECTED = 9397


def sigmoid(x):
    return 1.0 / (1.0 + np.exp(-x))


def load_surface(d: Path, layers):
    rows = []
    with (d / "rows.jsonl").open() as fh:
        for line in fh:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    X = {l: [] for l in layers}
    kept = []
    for r in rows:
        fp = d / f"{r['safe_key']}__pre.safetensors"
        if not fp.exists():
            continue
        with safe_open(str(fp), "pt") as st:
            for l in layers:
                X[l].append(st.get_tensor(l).float().numpy())
        kept.append(r)
    return kept, {l: np.asarray(v) for l, v in X.items()}


def fit_full(X, y):
    sc = StandardScaler().fit(X)
    clf = LogisticRegression(max_iter=5000, C=1.0).fit(sc.transform(X), y)
    return sc, clf


def oof_scores(X, y):
    skf = StratifiedKFold(n_splits=N_FOLDS, shuffle=True,
                          random_state=CV_RANDOM_STATE)
    oof = np.zeros(len(y))
    for tr, te in skf.split(X, y):
        sc = StandardScaler().fit(X[tr])
        clf = LogisticRegression(max_iter=5000, C=1.0).fit(
            sc.transform(X[tr]), y[tr])
        oof[te] = clf.decision_function(sc.transform(X[te]))
    return oof


def flip_curve(p, w_grid):
    margin = np.abs(2 * p - 1)
    return {f"{w:.2f}": round(float(np.mean(margin < w)), 4) for w in w_grid}


def largest_w_within_budget(p, w_grid, budget):
    margin = np.abs(2 * p - 1)
    ok = [w for w in w_grid if float(np.mean(margin < w)) <= budget]
    return max(ok) if ok else None


def run(args) -> int:
    v = VARIANTS[args.variant]
    global UNION_DIR, MINING_DIR, PROBES_OUT, RESULT, RESULT_COPY, SUFFIX
    UNION_DIR = REFIT_ROOT / v["union"]
    MINING_DIR = REFIT_ROOT / v["mining"]
    PROBES_OUT = REFIT_ROOT / v["probes"]
    RESULT = REFIT_ROOT / v["result"]
    RESULT_COPY = ARTIFACT_DIR / v["copy"]
    SUFFIX = v["suffix"]
    PROBES_OUT.mkdir(parents=True, exist_ok=True)

    print("[refit] loading union surface ...", flush=True)
    rows, X = load_surface(UNION_DIR, LAYERS)
    y = np.asarray([1 if r["label"] == "known" else 0 for r in rows])
    n = len(rows)
    print(f"[refit] union rows={n} known={int(y.sum())} "
          f"unknown={int((1 - y).sum())}", flush=True)

    result = {
        "stage": "par_sensor_refit",
        "checkpoint": "clean-SFT merged base (PAR training start)",
        "recipe": "StandardScaler+LogisticRegression(C=1.0,max_iter=5000); "
                  "OOF=StratifiedKFold(5,shuffle,rs=0); known=1; "
                  "p_unans=sigmoid(-score); stats on OOF scores",
        "n_union": n, "n_known": int(y.sum()), "n_unknown": int((1 - y).sum()),
        "layers": {}, "sensor_layer": SENSOR_LAYER,
    }

    oof = {}
    for l in LAYERS:
        oof[l] = oof_scores(X[l], y)
        auroc = roc_auc_score(y, oof[l])
        sc, clf = fit_full(X[l], y)
        train_auroc = roc_auc_score(y, clf.decision_function(sc.transform(X[l])))
        joblib.dump({"scaler": sc, "clf": clf, "layer": l,
                     "fit_surface": "par_sensor_refit/union_pregen",
                     "checkpoint": f"clean-sft-merged-base-{SUFFIX}"},
                    PROBES_OUT / f"probe_{l}_{SUFFIX}.joblib")
        result["layers"][l] = {
            "oof_auroc": round(float(auroc), 4),
            "train_auroc": round(float(train_auroc), 4),
        }
        print(f"[refit] {l}: oof_auroc={auroc:.4f} train={train_auroc:.4f}",
              flush=True)

    sensor_auroc = result["layers"][SENSOR_LAYER]["oof_auroc"]
    result["launch_condition_2"] = {
        "rule": f"{SENSOR_LAYER} held-out (OOF) AUROC >= {AUROC_FLOOR}",
        "value": sensor_auroc,
        "pass": bool(sensor_auroc >= AUROC_FLOOR),
    }

    # --- distribution + constants from the SENSOR layer OOF scores ---
    p = sigmoid(-oof[SENSOR_LAYER])          # P(unanswerable)
    margin = np.abs(2 * p - 1)
    gold_unans = (y == 0)
    gold_ans = (y == 1)

    with (REFIT_ROOT / f"union_refit_rows_{SUFFIX}.jsonl").open("w") as fh:
        for i, r in enumerate(rows):
            fh.write(json.dumps({
                "row_key": r["row_key"], "source": r.get("source"),
                "label": r["label"],
                "oof_score_L24": float(oof[SENSOR_LAYER][i]),
                "p_unanswerable": float(p[i]),
                "abs_2p_minus_1": float(margin[i]),
                "oof_score_L20": float(oof["L20"][i]),
                "oof_score_L28": float(oof["L28"][i]),
            }) + "\n")

    result["p_distribution_oof"] = {
        "mean": round(float(p.mean()), 4),
        "median": round(float(np.median(p)), 4),
        "frac_lt_0.1": round(float(np.mean(p < 0.1)), 4),
        "frac_gt_0.9": round(float(np.mean(p > 0.9)), 4),
        "saturation_bimodal_frac": round(float(np.mean((p < 0.1) | (p > 0.9))), 4),
        "mean_abs_2p_minus_1": round(float(margin.mean()), 4),
    }
    result["flip_curves"] = {
        "overall": flip_curve(p, W_GRID),
        "gold_unanswerable_stratum": flip_curve(p[gold_unans], W_GRID),
        "gold_answerable_stratum": flip_curve(p[gold_ans], W_GRID),
    }
    w_c = largest_w_within_budget(p[gold_unans], W_GRID, FLIP_BUDGET)
    w_a_cand = largest_w_within_budget(p[gold_ans], W_GRID, FLIP_BUDGET)
    w_a = None if w_c is None else (w_c if (w_a_cand is None or w_a_cand >= w_c)
                                    else w_a_cand)
    result["derived_constants"] = {
        "w_c": w_c,
        "w_c_rule": "largest grid w with flip<=2% on gold-unanswerable stratum",
        "w_a": w_a,
        "w_a_rule": "symmetric with w_c unless gold-answerable stratum binds",
        "flip_budget": FLIP_BUDGET, "w_grid": W_GRID,
    }

    # --- divergent classification under the refit sensor (union) ---
    # probe-preferred action: p>0.5 -> abstain; gold-preferred: unknown -> abstain
    probe_abstain = p > 0.5
    gold_abstain = (y == 0)
    divergent = probe_abstain != gold_abstain
    d_over = divergent & gold_abstain            # probe answers, gold abstains
    d_under = divergent & gold_ans               # probe abstains, gold answers
    mu_d = float(margin[divergent].mean()) if divergent.any() else 0.0
    mu_c = float(margin[~divergent].mean())
    mix = None
    for m in np.arange(0.05, 0.755, 0.005):
        share = m * mu_d / (m * mu_d + (1 - m) * mu_c)
        if share >= MASS_TARGET:
            mix = round(float(m), 3)
            break
    result["divergent_union_refit"] = {
        "n_divergent": int(divergent.sum()),
        "n_d_over": int(d_over.sum()), "n_d_under": int(d_under.sum()),
        "divergent_frac": round(float(divergent.mean()), 4),
        "mean_margin_divergent": round(mu_d, 4),
        "mean_margin_concordant": round(mu_c, 4),
        "mixture_for_25pct_mass": mix,
        "mixture_rule": "smallest m with m*mu_d/(m*mu_d+(1-m)*mu_c) >= 0.25",
    }

    # --- mining re-classification (only when extraction B is complete) ---
    mining_rows_file = MINING_DIR / "rows.jsonl"
    n_mining_done = 0
    if mining_rows_file.exists():
        n_mining_done = sum(1 for l in mining_rows_file.open() if l.strip())
    if n_mining_done >= MINING_EXPECTED:
        print(f"[refit] scoring mining surface ({n_mining_done} rows) ...",
              flush=True)
        mrows, MX = load_surface(MINING_DIR, LAYERS)
        probes = {l: joblib.load(PROBES_OUT / f"probe_{l}_{SUFFIX}.joblib")
                  for l in LAYERS}
        ms = {l: probes[l]["clf"].decision_function(
                  probes[l]["scaler"].transform(MX[l])) for l in LAYERS}
        mp = sigmoid(-ms[SENSOR_LAYER])
        # all mining candidates are gold-unanswerable; D-over under the refit
        # sensor = the L24 reward sensor reads the row as answerable (p<0.5).
        sensor_dover = mp < 0.5
        # consensus variant (matches the historical mining D-over rule shape)
        consensus_dover = ((ms["L20"] > 0) & (ms["L24"] > 0) & (ms["L28"] > 0))
        with (REFIT_ROOT / f"mining_refit_rows_{SUFFIX}.jsonl").open("w") as fh:
            for i, r in enumerate(mrows):
                fh.write(json.dumps({
                    "row_key": r["row_key"], "source": r.get("source"),
                    "p_unanswerable": float(mp[i]),
                    "sensor_dover": bool(sensor_dover[i]),
                    "consensus_dover": bool(consensus_dover[i]),
                }) + "\n")
        by_source = {}
        for i, r in enumerate(mrows):
            src = r.get("source", "unknown")
            e = by_source.setdefault(src, {"n": 0, "sensor_dover": 0,
                                           "consensus_dover": 0})
            e["n"] += 1
            e["sensor_dover"] += int(sensor_dover[i])
            e["consensus_dover"] += int(consensus_dover[i])
        result["mining_reclassification_refit"] = {
            "n_scored": len(mrows),
            "sensor_dover_total": int(sensor_dover.sum()),
            "consensus_dover_total": int(consensus_dover.sum()),
            "note": "sensor_dover (refit-L24 p<0.5) is the operative count "
                    "for the training mixture; consensus is sensitivity.",
            "by_source": by_source,
            "mean_margin_sensor_dover": (
                round(float(np.abs(2 * mp[sensor_dover] - 1).mean()), 4)
                if sensor_dover.any() else None),
        }
    else:
        result["mining_reclassification_refit"] = {
            "status": f"PENDING extraction B ({n_mining_done}/{MINING_EXPECTED} "
                      "rows on disk) — rerun this script when complete",
        }

    RESULT.write_text(json.dumps(result, indent=2) + "\n")
    RESULT_COPY.parent.mkdir(parents=True, exist_ok=True)
    RESULT_COPY.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({k: result[k] for k in
                      ("layers", "launch_condition_2", "p_distribution_oof",
                       "derived_constants", "divergent_union_refit")},
                     indent=2), flush=True)
    print(f"[refit] wrote {RESULT} and {RESULT_COPY}", flush=True)
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--variant", choices=["v1", "v2"], default="v2")
    sys.exit(run(ap.parse_args()))
