#!/usr/bin/env python3
"""AL prep: UNGATED anti-propensity ceiling on the AI-TRUE A0 surface (CPU-only).

The two gated ceiling sims (amendment_al_prep_radial_ceiling_true.py, findings
under radial_ceiling_true/ and radial_ceiling_true_gate_meandiff/) exposed a
structural blind spot: any answerability gate that protects the 90 correct
answers also shelters most of the 116 residual confabs. In both gated laws the
gate-permutation null returned p=1.0 (the gate channel has no real reach into
the confabs) and only the anti-propensity push carried signal (p=0.005 in the
meandiff variant). The commitment scope check
(amendment_al_prep_commitment_scope_check.py) then showed WHY an ungated push
should work: the propensity direction is anti-aligned with the answer-vs-refuse
direction (cos -0.35) and transfers to answer-vs-refuse only at chance once
caution is matched (0.46/0.51), i.e. the correct answers do NOT sit high on
propensity. So a push keyed directly on propensity, with NO answerability gate,
should reach the confabs at low collateral.

This script quantifies that ungated ceiling. It drops the gate entirely and the
caution-injection region: every row whose propensity projection exceeds a
threshold t receives the single anti-propensity push.

Readouts (leak-free where a row would otherwise score itself):
  c    caution distance z : logistic refused-vs-answered on PCA-128 of L35,
         5-fold OOF decision function, z-scored. HIGH = refuse side. Identical
         construction to the gated sim.
  prop propensity proj    : d_confab from the scope check. Features are
         StandardScaler(PCA-128) of L24, caution-residualized (each PCA column
         regressed on c, residuals kept). Direction = mean(confab) minus
         mean(unanswerable-refused) on those residuals. OOF over the two
         defining cells (confab, un_refused); full-fit projection for all other
         rows. z-scored.

Control law (ungated):
  push = prop >= t. NO answerability gate, NO caution region.
Kill accounting mirrors the gated sim:
  - a pushed baseline confab flips to refusal (oracle) or with p=0.5
    (Bernoulli half-effect) -> confab killed.
  - a pushed correct answer that flips to refusal is collateral. The gated sim
    counts EVERY steered correct answer as collateral (deterministic, oracle
    convention g1_correct_collateral = correct AND steered); mirrored here: a
    pushed correct answer is collateral with certainty under oracle, and with
    p=0.5 under half-effect.
  - a pushed honest refusal stays a refusal (harmless) -> tracked as
    extra_honest_refusals_pushed.
  - a pushed WRONG answer that flips to refusal is a BENEFIT ->
    wrong_answers_converted.

Operating points by oracle collateral: conservative = max reach at 0
collateral, balanced = max reach at <=1 collateral, aggressive = max reach at
<=3 collateral. Each reports threshold, confabs killed (oracle + half-effect
1000-boot CI), collateral, wrong converted, extra honest refusals, and the
fraction of all 1662 rows pushed. Permutation null shuffles prop (200 perms)
and recomputes oracle kills at each point. Aim-small gate derivation per point
mirrors the gated sim (gate_feasible flag, suggested gates from 0.7*CI-lo,
G1 collateral max from oracle collateral CI-hi).

Comparison target: gated logistic balanced = 46/116 at 1 collateral, gated
meandiff balanced = 31/116 at 1 collateral. The headline question is whether
ungated balanced beats 46, and whether ungated CONSERVATIVE beats the gated
law's infeasible reach at 0 collateral (gated meandiff conservative was 111 but
sat on p=1.0 permutation, i.e. that reach was gate-permutation-indistinguishable
from chance; here we want a conservative point with real permutation signal).

Output: analysis/amendment_al_prep/radial_ceiling_ungated/findings.json plus a
printed summary. Analysis outputs stay untracked.

Usage:
  python amendment_al_prep_radial_ceiling_ungated.py [--arm true_a0]
"""

import warnings
warnings.filterwarnings("ignore")
import os
os.environ.setdefault("OMP_NUM_THREADS", "8")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "8")
os.environ.setdefault("MKL_NUM_THREADS", "8")

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from sklearn.decomposition import PCA
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import StratifiedKFold
from sklearn.preprocessing import StandardScaler

ARCHIVE_AMENDMENTS_DIR = Path(__file__).resolve().parent
if str(ARCHIVE_AMENDMENTS_DIR) not in sys.path:
    sys.path.insert(0, str(ARCHIVE_AMENDMENTS_DIR))

from path_compat import repo_root  # noqa: E402

from amendment_al_prep_doubt_axis_check import load_a0_stack, load_jsonl  # noqa: E402
from amendment_al_prep_familiarity_vs_knowing import oof_meandiff_proj, unit  # noqa: E402

CANONICAL = repo_root()
DEFAULT_AL_PREP = CANONICAL / "experiment/phase1/probe/analysis/amendment_al_prep"
SEED = 20260705
L_PROP = 24
L_CAUTION = 35
N_PCA = 128
N_SPLITS = 5
N_BOOT = 1000
N_PERM = 200


def oof_caution(P35, y_ref, seed):
    """5-fold OOF caution log-odds, z-scored. Same as the gated sim."""
    out = np.zeros(len(y_ref))
    skf = StratifiedKFold(n_splits=N_SPLITS, shuffle=True, random_state=seed)
    for tr, te in skf.split(P35, y_ref):
        sc = StandardScaler().fit(P35[tr])
        clf = LogisticRegression(solver="saga", tol=1e-3, max_iter=2000,
                                 random_state=seed).fit(sc.transform(P35[tr]),
                                                        y_ref[tr])
        out[te] = clf.decision_function(sc.transform(P35[te]))
    return (out - out.mean()) / out.std()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--arm", default="true_a0")
    ap.add_argument("--al-prep-dir", default=str(DEFAULT_AL_PREP))
    args = ap.parse_args()
    al_prep = Path(args.al_prep_dir)

    rows = load_jsonl(al_prep / args.arm / "gen/data/rows_graded.jsonl")
    row_keys = [r["row_key"] for r in rows]
    stack = load_a0_stack(al_prep / args.arm / "extract/data", row_keys)
    X24 = stack[:, L_PROP, :].astype(np.float64)
    X35 = stack[:, L_CAUTION, :].astype(np.float64)
    del stack
    n = len(rows)

    findings = {"seed": SEED, "arm": args.arm,
                "surface": "AL-prep A0 (1662 rows)", "law": "ungated_anti_propensity",
                "layers": {"propensity": L_PROP, "caution": L_CAUTION},
                "config": {"pca": N_PCA, "n_boot": N_BOOT, "n_perm": N_PERM}}

    # ---------------- readouts
    print("[readouts] PCA + OOF fits ...", flush=True)
    P24 = StandardScaler().fit_transform(
        PCA(N_PCA, svd_solver="randomized", random_state=SEED).fit_transform(X24))
    P35 = PCA(N_PCA, svd_solver="randomized", random_state=SEED).fit_transform(X35)

    y_ref = np.array([1 if r["refused"] else 0 for r in rows])
    c = oof_caution(P35, y_ref, SEED + 1)

    # propensity direction (d_confab from the scope check): caution-residualize
    # the L24 PCA features, mean-diff confab-vs-unanswerable-refused, OOF over the
    # defining cells and full-fit for every other row.
    R = P24 - LinearRegression().fit(c.reshape(-1, 1), P24).predict(c.reshape(-1, 1))
    confab_idx = np.array([i for i, r in enumerate(rows)
                           if r["gold_class"] == "unanswerable" and r["answered"]])
    un_ref_idx = np.array([i for i, r in enumerate(rows)
                           if r["gold_class"] == "unanswerable" and r["refused"]])
    prop_raw = oof_meandiff_proj(R, confab_idx, un_ref_idx, SEED + 2)
    prop = (prop_raw - prop_raw.mean()) / prop_raw.std()

    # in-cell OOF AUROC sanity (should land near 0.67-0.68)
    prop_incell_auroc = float(roc_auc_score(
        np.r_[np.ones(len(confab_idx)), np.zeros(len(un_ref_idx))],
        np.r_[prop[confab_idx], prop[un_ref_idx]]))
    findings["readout_quality"] = {
        "c_oof_auroc_refused": round(float(roc_auc_score(y_ref, c)), 4),
        "prop_incell_oof_auroc_confab_vs_unrefused": round(prop_incell_auroc, 4),
    }

    # ---------------- per-row behavior labels
    is_confab = np.array([1 if (r["gold_class"] == "unanswerable" and r["answered"])
                          else 0 for r in rows]).astype(bool)
    is_un_refused = np.array([1 if (r["gold_class"] == "unanswerable" and r["refused"])
                             else 0 for r in rows]).astype(bool)
    is_ans_correct = np.array([1 if (r["gold_class"] == "answerable" and r["answered"]
                              and r["correct"] is True) else 0 for r in rows]).astype(bool)
    is_ans_wrong = np.array([1 if (r["gold_class"] == "answerable" and r["answered"]
                            and r["correct"] is False) else 0 for r in rows]).astype(bool)
    is_ans_refused = np.array([1 if (r["gold_class"] == "answerable" and r["refused"])
                              else 0 for r in rows]).astype(bool)

    pops = {"confab": int(is_confab.sum()), "un_refused": int(is_un_refused.sum()),
            "ans_correct": int(is_ans_correct.sum()), "ans_wrong": int(is_ans_wrong.sum()),
            "ans_refused": int(is_ans_refused.sum()), "total": n}
    findings["populations"] = pops
    print("populations:", pops, flush=True)
    print(f"c AUROC={findings['readout_quality']['c_oof_auroc_refused']} "
          f"prop in-cell AUROC={prop_incell_auroc:.4f}", flush=True)

    base = {"confab": int(is_confab.sum()), "ans_correct": int(is_ans_correct.sum()),
            "ans_wrong": int(is_ans_wrong.sum())}
    findings["baseline"] = base

    # ---------------- point metrics (oracle) for a threshold
    def point_metrics(t):
        push = prop >= t
        return {
            "threshold": round(float(t), 4),
            "n_pushed": int(push.sum()),
            "pushed_fraction": round(float(push.mean()), 4),
            "confabs_killed": int((is_confab & push).sum()),
            "collateral": int((is_ans_correct & push).sum()),
            "wrong_answers_converted": int((is_ans_wrong & push).sum()),
            "extra_honest_refusals_pushed": int(((is_un_refused | is_ans_refused)
                                                 & push).sum()),
            "confabs_unreached": int((is_confab & ~push).sum()),
        }

    # sweep thresholds over the prop distribution. The grid must reach into the
    # extreme upper tail: the zero-collateral (conservative) point can only live
    # ABOVE the highest-prop correct answer, which sits in a thin outlier tail a
    # 0.99-quantile grid would miss. Anchor the top of the grid on the correct
    # answers' max prop plus a small margin so the conservative region is covered.
    prop_correct_max = float(prop[is_ans_correct].max())
    grid = np.unique(np.concatenate([
        np.quantile(prop, np.linspace(0.02, 0.995, 200)),
        np.linspace(prop_correct_max - 0.05, float(prop[is_confab].max()) + 1e-6, 40),
    ]))
    findings["prop_correct_max"] = round(prop_correct_max, 4)
    sweep = [point_metrics(t) for t in grid]
    findings["sweep_n_points"] = len(sweep)

    def pick(max_coll):
        elig = [p for p in sweep if p["collateral"] <= max_coll]
        return max(elig, key=lambda p: p["confabs_killed"]) if elig else None

    candidates = {"conservative": pick(0), "balanced": pick(1), "aggressive": pick(3)}
    findings["candidate_operating_points"] = {
        k: {"threshold": v["threshold"]} for k, v in candidates.items() if v}

    # ---------------- bootstrap kills (oracle + half-effect) per point
    def bootstrap_point(t, effect):
        push = prop >= t
        cr = is_confab & push          # confabs reached by the push
        wr = is_ans_wrong & push       # wrong answers reached
        col = is_ans_correct & push    # correct answers reached (collateral)
        rng = np.random.default_rng(SEED + 7)
        acc = {"killed": [], "collateral": [], "wrong_conv": []}
        for _ in range(N_BOOT):
            bi = rng.choice(n, n, replace=True)
            crb = cr[bi]
            colb = col[bi]
            wrb = wr[bi]
            if effect >= 1.0:
                acc["killed"].append(int(crb.sum()))
                acc["collateral"].append(int(colb.sum()))
                acc["wrong_conv"].append(int(wrb.sum()))
            else:
                acc["killed"].append(int((crb & (rng.random(n) < effect)).sum()))
                acc["collateral"].append(int((colb & (rng.random(n) < effect)).sum()))
                acc["wrong_conv"].append(int((wrb & (rng.random(n) < effect)).sum()))

        def ci(a):
            a = np.array(a)
            return {"mean": round(float(a.mean()), 2),
                    "lo": round(float(np.quantile(a, 0.025)), 2),
                    "hi": round(float(np.quantile(a, 0.975)), 2)}
        return {"confabs_killed": ci(acc["killed"]),
                "collateral": ci(acc["collateral"]),
                "wrong_answers_converted": ci(acc["wrong_conv"])}

    op_table = {}
    for label, rec in candidates.items():
        if rec is None:
            op_table[label] = None
            continue
        t = rec["threshold"]
        op_table[label] = {
            "threshold": t,
            "point": rec,
            "oracle": bootstrap_point(t, 1.0),
            "half_effect": bootstrap_point(t, 0.5)}
        print(f"[{label}] t={t:.4f} killed(oracle)={rec['confabs_killed']} "
              f"coll={rec['collateral']} wrong_conv={rec['wrong_answers_converted']} "
              f"pushed={rec['n_pushed']} ({rec['pushed_fraction']:.3f}) "
              f"half={op_table[label]['half_effect']['confabs_killed']['mean']:.1f}",
              flush=True)
    findings["operating_point_table"] = op_table

    # ---------------- permutation null (shuffle prop) per point
    findings["permutation_nulls"] = {}
    rng = np.random.default_rng(SEED + 101)
    for label, rec in candidates.items():
        if rec is None:
            continue
        t = rec["threshold"]
        obs = int((is_confab & (prop >= t)).sum())
        # match the number pushed so the null is a like-for-like reach comparison
        n_push = int((prop >= t).sum())
        perm = []
        for _ in range(N_PERM):
            pp = rng.permutation(prop)
            perm.append(int((is_confab & (pp >= t)).sum()))
        perm = np.array(perm)
        p = float((np.sum(perm >= obs) + 1) / (N_PERM + 1))
        findings["permutation_nulls"][label] = {
            "obs_confabs_killed": obs, "n_pushed": n_push,
            "perm_mean": round(float(perm.mean()), 2), "p": round(p, 4)}
        print(f"PERM[{label}] obs={obs} perm_mean={perm.mean():.1f} p={p:.4f}",
              flush=True)

    # ---------------- aim-small gate derivation (half-effect, per point)
    # Thresholds derive from the expected effect and its uncertainty (below the
    # half-effect CI lower bound with margin), never round defaults. A point
    # whose half-effect kill CI lower bound is non-positive cannot support a
    # gate (no detectable room).
    findings["aim_small_gate_derivation"] = {}
    for label, rec in candidates.items():
        if rec is None:
            continue
        he = op_table[label]["half_effect"]
        orc = op_table[label]["oracle"]
        d_killed = he["confabs_killed"]
        feasible = d_killed["lo"] > 0
        findings["aim_small_gate_derivation"][label] = {
            "confabs_killed_half_effect": d_killed,
            "gate_feasible": bool(feasible),
            "suggested_gates": ({
                "G1_collateral_max": int(orc["collateral"]["hi"]),
                "G3_min_confabs_killed": max(1, int(0.7 * d_killed["lo"])),
            } if feasible else None)}
        print(f"aim-small[{label}] feasible={feasible} "
              f"{json.dumps(findings['aim_small_gate_derivation'][label]['suggested_gates'])}",
              flush=True)

    # ---------------- comparison verdict vs the gated laws
    gated = {"gated_logistic_balanced": {"killed": 46, "collateral": 1, "of": 116},
             "gated_meandiff_balanced": {"killed": 31, "collateral": 1, "of": 116},
             "gated_meandiff_conservative_note":
                 "111/116 at 0 collateral but gate-permutation p=1.0 (no real reach)"}
    ung_bal = candidates["balanced"]
    ung_con = candidates["conservative"]
    verdict = {
        "gated_reference": gated,
        "ungated_balanced": ({"killed": ung_bal["confabs_killed"],
                              "collateral": ung_bal["collateral"],
                              "beats_gated_logistic_46": ung_bal["confabs_killed"] > 46,
                              "beats_gated_meandiff_31": ung_bal["confabs_killed"] > 31}
                             if ung_bal else None),
        "ungated_conservative": ({"killed": ung_con["confabs_killed"],
                                 "collateral": ung_con["collateral"],
                                 "perm_p": findings["permutation_nulls"]
                                 .get("conservative", {}).get("p")}
                                if ung_con else None)}
    findings["comparison_verdict"] = verdict
    print("VERDICT", json.dumps(verdict), flush=True)

    out_dir = al_prep / "radial_ceiling_ungated"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "findings.json").write_text(json.dumps(findings, indent=2))
    print(f"WROTE {out_dir / 'findings.json'}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
