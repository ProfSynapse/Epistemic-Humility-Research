#!/usr/bin/env python3
"""AL prep: radial-steering ceiling table on the AI-TRUE A0 surface (CPU-only).

Adapts the PR #204 offline ceiling audit (analysis/radial_ceiling_sim_20260704)
from the GRPO-v2 surface to the checkpoint Amendment AL will actually steer:
the AI-TRUE arm's A0 pool (1,662 rows, graded generations + full-stack pre-gen
extracts). Same probe-as-oracle logic (Amendment O pattern), same three-region
control law, same operating-point selection and half-effect accounting; the
per-row anchor readouts are refit ON THIS surface because directions do not
transfer across checkpoints (Amendment T; confirmed again by the AL-prep
doubt-axis check, ref-axis cos ~0.17).

Per-row readouts, all leak-free out-of-fold (no row scores itself):
  g  answerability log-odds : logistic answerable-vs-unanswerable on PCA-128 of
       L24, 5-fold OOF decision function.
  c  caution distance z     : logistic refused-vs-answered on PCA-128 of L35
       (where the local caution axis reads refusal at 0.93), 5-fold OOF
       decision function, z-scored. HIGH = refuse side.
  m  commitment projection  : mean(confab)-mean(refuse) direction within
       unanswerables on PCA-128 of L24, residualised vs caution+flavor per
       train fold, OOF projection averaged over repeats.
  f  flavor                 : category_canon.

Control law (identical to PR #204):
  Region 1: g >= gate_cut  -> untouched (protect answers; AG asymmetry).
  Region 2: g < gate_cut AND c below the flavor refusal threshold -> caution
            injection (goal: say IDK).
  Region 3: g < gate_cut AND m >= m_cut -> anti-commitment steer.
Oracle = every reached baseline confab flips to refusal; half-effect = each
flips with p=0.5. Candidate operating points: conservative (zero G1
collateral), balanced (kills minus 10x collateral), aggressive (collateral<=3).

Output: analysis/amendment_al_prep/radial_ceiling_true/findings.json plus an
aim-small gate-threshold block derived from the HALF-EFFECT CIs at the
conservative point (the user-preferred AL primary).

Usage:
  python amendment_al_prep_radial_ceiling_true.py [--arm true_a0]
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

PROBE_DIR = Path(__file__).resolve().parent
if str(PROBE_DIR) not in sys.path:
    sys.path.insert(0, str(PROBE_DIR))
from amendment_al_prep_doubt_axis_check import load_a0_stack, load_jsonl  # noqa: E402

CANONICAL = Path("/home/profsynapse/code/Epistemic-Humility-Research")
DEFAULT_AL_PREP = CANONICAL / "experiment/phase1/probe/analysis/amendment_al_prep"
SEED = 20260705
L_GATE = 24
L_CAUTION = 35
N_PCA = 128
N_SPLITS = 5
N_REPEAT = 4
N_BOOT = 1000
N_PERM = 200


def oof_logistic(P: np.ndarray, y: np.ndarray, seed: int) -> np.ndarray:
    """5-fold OOF decision-function scores (leak-free log-odds)."""
    out = np.zeros(len(y))
    skf = StratifiedKFold(n_splits=N_SPLITS, shuffle=True, random_state=seed)
    for tr, te in skf.split(P, y):
        sc = StandardScaler().fit(P[tr])
        clf = LogisticRegression(solver="saga", tol=1e-3, max_iter=2000,
                                 random_state=seed).fit(sc.transform(P[tr]), y[tr])
        out[te] = clf.decision_function(sc.transform(P[te]))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--arm", default="true_a0")
    ap.add_argument("--al-prep-dir", default=str(DEFAULT_AL_PREP))
    ap.add_argument("--gate", default="logistic", choices=["logistic", "meandiff"],
                    help="gate score construction. 'logistic' trains on the raw "
                         "answerable/unanswerable label over ALL rows, which "
                         "pulls confabs (unanswerable rows that look answerable) "
                         "onto the answerable side -- the blind spot found in "
                         "the first run. 'meandiff' projects onto the OOF "
                         "correct-answered minus refused-unanswerable cell-mean "
                         "direction, fit only on behaviorally clean cells "
                         "(ans_correct-vs-confab AUROC 0.926 in the "
                         "familiarity_vs_knowing report vs 0.34-above-refusals "
                         "for confabs).")
    args = ap.parse_args()
    al_prep = Path(args.al_prep_dir)
    rng_global = np.random.default_rng(SEED)

    rows = load_jsonl(al_prep / args.arm / "gen/data/rows_graded.jsonl")
    row_keys = [r["row_key"] for r in rows]
    stack = load_a0_stack(al_prep / args.arm / "extract/data", row_keys)
    X24 = stack[:, L_GATE, :].astype(np.float64)
    X35 = stack[:, L_CAUTION, :].astype(np.float64)
    del stack

    findings = {"seed": SEED, "arm": args.arm, "surface": "AL-prep A0 (1662 rows)",
                "layers": {"gate": L_GATE, "caution": L_CAUTION, "commitment": L_GATE},
                "config": {"pca": N_PCA, "cv": f"{N_REPEAT}x{N_SPLITS}",
                           "n_boot": N_BOOT, "n_perm": N_PERM}}

    # ---------------- per-row readouts (all OOF)
    print("[readouts] PCA + OOF fits ...", flush=True)
    P24 = PCA(N_PCA, svd_solver="randomized", random_state=SEED).fit_transform(X24)
    P35 = PCA(N_PCA, svd_solver="randomized", random_state=SEED).fit_transform(X35)

    y_ans = np.array([1 if r["gold_class"] == "answerable" else 0 for r in rows])
    y_ref = np.array([1 if r["refused"] else 0 for r in rows])

    if args.gate == "logistic":
        g_all = oof_logistic(P24, y_ans, SEED)
    else:
        from amendment_al_prep_familiarity_vs_knowing import oof_meandiff_proj
        P24s = StandardScaler().fit_transform(P24)
        ka_idx = np.array([i for i, r in enumerate(rows)
                           if r["gold_class"] == "answerable" and r["answered"]
                           and r["correct"] is True])
        ur_idx = np.array([i for i, r in enumerate(rows)
                           if r["gold_class"] == "unanswerable" and r["refused"]])
        g_all = oof_meandiff_proj(P24s, ka_idx, ur_idx, SEED)
    c_raw = oof_logistic(P35, y_ref, SEED + 1)
    c_all = (c_raw - c_raw.mean()) / c_raw.std()

    confab_idx = np.array([i for i, r in enumerate(rows)
                           if r["gold_class"] == "unanswerable" and r["answered"]])
    kacorr_idx = np.array([i for i, r in enumerate(rows)
                           if r["gold_class"] == "answerable" and r["answered"]
                           and r["correct"] is True])
    findings["gate_kind"] = args.gate
    findings["readout_quality"] = {
        "g_oof_auroc_answerable": round(float(roc_auc_score(y_ans, g_all)), 4),
        "g_auroc_anscorrect_vs_confab": round(float(roc_auc_score(
            np.r_[np.ones(len(kacorr_idx)), np.zeros(len(confab_idx))],
            np.r_[g_all[kacorr_idx], g_all[confab_idx]])), 4),
        "c_oof_auroc_refused": round(float(roc_auc_score(y_ref, c_raw)), 4),
    }

    for r, gv, cv in zip(rows, g_all, c_all):
        r["g"] = float(gv)
        r["c"] = float(cv)
        r["flavor"] = r["category_canon"]

    un = [r for r in rows if r["gold_class"] == "unanswerable" and not r["degenerate"]]
    an = [r for r in rows if r["gold_class"] == "answerable"]
    un_pidx = np.array([i for i, r in enumerate(rows)
                        if r["gold_class"] == "unanswerable" and not r["degenerate"]])

    # ---------------- m: OOF commitment projection at L24 within unanswerables
    Pun = P24[un_pidx]
    y_confab = np.array([1 if r["confab_on_unanswerable"] else 0 for r in un])
    c_un = np.array([r["c"] for r in un])
    flav_un = np.array([r["flavor"] for r in un])
    FLAVORS = sorted(set(flav_un))
    FREF = FLAVORS[1:]

    def onehot(catv, ref):
        return np.hstack([(catv == c).astype(float).reshape(-1, 1) for c in ref])

    def confounds(idx):
        return np.hstack([c_un[idx].reshape(-1, 1), onehot(flav_un[idx], FREF)])

    m_oof = np.zeros(len(un))
    n_seen = np.zeros(len(un))
    for rep in range(N_REPEAT):
        skf = StratifiedKFold(n_splits=N_SPLITS, shuffle=True, random_state=SEED + rep)
        for tr, te in skf.split(np.arange(len(un)), y_confab):
            lr = LinearRegression().fit(confounds(tr), Pun[tr])
            Rtr = Pun[tr] - lr.predict(confounds(tr))
            Rte = Pun[te] - lr.predict(confounds(te))
            sc = StandardScaler().fit(Rtr)
            Rtr = sc.transform(Rtr)
            Rte = sc.transform(Rte)
            ytr = y_confab[tr]
            d = Rtr[ytr == 1].mean(0) - Rtr[ytr == 0].mean(0)
            d = d / (np.linalg.norm(d) + 1e-12)
            m_oof[te] += Rte @ d
            n_seen[te] += 1
    m_oof = m_oof / n_seen
    m_auroc = roc_auc_score(y_confab, m_oof)
    findings["commitment_m"] = {
        "oof_auroc_confab_vs_refuse": round(float(m_auroc), 4),
        "construction": "mean(confab)-mean(refuse) on PCA-128(L24) residualised "
                        "vs caution+flavor, per-fold train-only, OOF avg over repeats."}
    print(f"g AUROC={findings['readout_quality']['g_oof_auroc_answerable']} "
          f"c AUROC={findings['readout_quality']['c_oof_auroc_refused']} "
          f"m AUROC={m_auroc:.4f}", flush=True)
    for r, mv in zip(un, m_oof):
        r["m"] = float(mv)

    # ---------------- per-flavor refusal threshold in caution distance
    flavor_thresh = {}
    for fl in FLAVORS:
        sub = [r for r in un if r["flavor"] == fl]
        cc = np.array([r["c"] for r in sub])
        yy = np.array([r["refused"] for r in sub]).astype(int)
        if len(set(yy)) < 2:
            flavor_thresh[fl] = {"threshold_z": float(cc.mean()),
                                 "method": "mean(only-one-class)", "n": len(sub)}
            continue
        lr = LogisticRegression(max_iter=2000).fit(cc.reshape(-1, 1), yy)
        b0, b1 = lr.intercept_[0], lr.coef_[0][0]
        thr = float(-b0 / b1) if abs(b1) > 1e-9 else float(cc.mean())
        flavor_thresh[fl] = {"threshold_z": round(thr, 4), "slope": round(float(b1), 4),
                             "n": len(sub), "refuse_rate": round(float(yy.mean()), 4)}
    findings["flavor_refusal_thresholds"] = flavor_thresh
    for r in un:
        r["_shortfall"] = flavor_thresh[r["flavor"]]["threshold_z"] - r["c"]

    # ---------------- region classification + goal metrics (PR #204 logic)
    an_g = np.array([r["g"] for r in an])
    un_g = np.array([r["g"] for r in un])
    short = np.array([r["_shortfall"] for r in un])
    mm = np.array([r["m"] for r in un])
    an_correct = np.array([1 if (r["answered"] and r["correct"] is True) else 0 for r in an])
    un_refused = np.array([r["refused"] for r in un]).astype(int)
    un_confab = np.array([1 if r["confab_on_unanswerable"] else 0 for r in un]).astype(int)

    def classify(gate_cut, m_cut):
        an_unans_side = an_g < gate_cut
        un_unans_side = un_g < gate_cut
        r2 = un_unans_side & (short > 0.0)
        r3 = un_unans_side & (mm >= m_cut)
        return {"an_unans_side": an_unans_side, "un_ans_side": ~un_unans_side,
                "r2": r2, "r3": r3, "reached": r2 | r3}

    def goal_metrics(cls, effect=1.0, rng=None):
        reached = cls["reached"]
        confab_reached = un_confab.astype(bool) & reached
        if effect >= 1.0:
            flipped = confab_reached.copy()
        else:
            draw = (rng if rng is not None else rng_global).random(len(un)) < effect
            flipped = confab_reached & draw
        refused_after = un_refused.copy(); refused_after[flipped] = 1
        confab_after = un_confab.copy(); confab_after[flipped] = 0
        an_steered = cls["an_unans_side"]
        return {"g2_refused": int(refused_after.sum()),
                "g3_confab": int(confab_after.sum()),
                "g1_correct_retained": int((an_correct.astype(bool) & ~an_steered).sum()),
                "g1_correct_collateral": int((an_correct.astype(bool) & an_steered).sum()),
                "unreachable_confab": int((un_confab.astype(bool) & ~reached).sum()),
                "n_flipped": int(flipped.sum())}

    base = {"g1_correct_answerable": int(an_correct.sum()),
            "g2_refused": int(un_refused.sum()), "g3_confab": int(un_confab.sum()),
            "n_answerable": len(an), "n_unanswerable": len(un)}
    findings["baseline"] = base
    print("BASELINE", base, flush=True)

    gate_grid = [float(x) for x in np.quantile(np.concatenate([an_g, un_g]),
                                               np.linspace(0.02, 0.75, 18))]
    gate_grid = sorted(set([round(x, 3) for x in gate_grid] + [-2.0, 0.0, 2.0, 5.0, 8.0]))
    m_grid = sorted(set(round(float(x), 3) for x in
                        np.quantile(m_oof, [0.5, 0.6, 0.7, 0.75, 0.8, 0.85, 0.9, 0.95])))

    sweep = []
    for gcut in gate_grid:
        for mcut in m_grid:
            cls = classify(gcut, mcut)
            sweep.append({"gate_cut": gcut, "m_cut": mcut,
                          "r2_n": int(cls["r2"].sum()), "r3_n": int(cls["r3"].sum()),
                          "reached_n": int(cls["reached"].sum()),
                          "an_gate_fp": int(cls["an_unans_side"].sum()),
                          "un_gate_fn": int(cls["un_ans_side"].sum()),
                          **goal_metrics(cls, 1.0)})
    findings["sweep"] = sweep

    def killed(rec):
        return base["g3_confab"] - rec["g3_confab"]

    zero_coll = [r for r in sweep if r["g1_correct_collateral"] == 0]
    conservative = max(zero_coll if zero_coll else sweep, key=killed)
    balanced = max(sweep, key=lambda r: killed(r) - 10 * r["g1_correct_collateral"])
    aggressive = max([r for r in sweep if r["g1_correct_collateral"] <= 3], key=killed)
    candidates = {"conservative": conservative, "balanced": balanced,
                  "aggressive": aggressive}
    findings["candidate_operating_points"] = {
        k: {"gate_cut": v["gate_cut"], "m_cut": v["m_cut"]} for k, v in candidates.items()}

    # ---------------- bootstrap CIs
    def bootstrap_point(gcut, mcut, effect):
        cls = classify(gcut, mcut)
        confab_reached = un_confab.astype(bool) & cls["reached"]
        an_steered = cls["an_unans_side"]
        rng = np.random.default_rng(SEED + 7)
        acc = {k: [] for k in ("g1r", "g1c", "g2", "g3", "unreach")}
        for _ in range(N_BOOT):
            ai = rng.choice(len(an), len(an), replace=True)
            ui = rng.choice(len(un), len(un), replace=True)
            acc["g1r"].append(int((an_correct[ai].astype(bool) & ~an_steered[ai]).sum()))
            acc["g1c"].append(int((an_correct[ai].astype(bool) & an_steered[ai]).sum()))
            cr = confab_reached[ui]
            flip = cr if effect >= 1.0 else cr & (rng.random(len(ui)) < effect)
            ra = un_refused[ui].copy(); ra[flip] = 1
            ca = un_confab[ui].copy(); ca[flip] = 0
            acc["g2"].append(int(ra.sum()))
            acc["g3"].append(int(ca.sum()))
            acc["unreach"].append(int((un_confab[ui].astype(bool) & ~cls["reached"][ui]).sum()))

        def ci(a):
            a = np.array(a)
            return {"mean": round(float(a.mean()), 2),
                    "lo": round(float(np.quantile(a, 0.025)), 2),
                    "hi": round(float(np.quantile(a, 0.975)), 2)}
        return {"g1_correct_retained": ci(acc["g1r"]),
                "g1_correct_collateral": ci(acc["g1c"]),
                "g2_refused": ci(acc["g2"]), "g3_confab": ci(acc["g3"]),
                "unreachable_confab": ci(acc["unreach"])}

    op_table = {}
    for label, rec in candidates.items():
        gcut, mcut = rec["gate_cut"], rec["m_cut"]
        cls = classify(gcut, mcut)
        op_table[label] = {
            "gate_cut": gcut, "m_cut": mcut,
            "region_census": {"r2_n": int(cls["r2"].sum()), "r3_n": int(cls["r3"].sum()),
                              "reached_n": int(cls["reached"].sum()),
                              "an_gate_fp_steered": int(cls["an_unans_side"].sum()),
                              "un_gate_fn_toR1": int(cls["un_ans_side"].sum())},
            "baseline": {"g1": base["g1_correct_answerable"],
                         "g2": base["g2_refused"], "g3": base["g3_confab"]},
            "oracle": bootstrap_point(gcut, mcut, 1.0),
            "half_effect": bootstrap_point(gcut, mcut, 0.5)}
        print(f"[{label}] gate={gcut} m={mcut} "
              f"killed(oracle)={base['g3_confab']-op_table[label]['oracle']['g3_confab']['mean']:.0f} "
              f"collateral={op_table[label]['oracle']['g1_correct_collateral']['mean']:.1f}",
              flush=True)
    findings["operating_point_table"] = op_table

    # ---------------- Region-3 ablation
    r3_ablation = {}
    for label, rec in candidates.items():
        cls = classify(rec["gate_cut"], rec["m_cut"])
        k2 = int((un_confab.astype(bool) & cls["r2"]).sum())
        k23 = int((un_confab.astype(bool) & (cls["r2"] | cls["r3"])).sum())
        r3_ablation[label] = {"confabs_killed_R2_only": k2,
                              "confabs_killed_R2plusR3": k23,
                              "R3_marginal_gain": k23 - k2}
        print(f"[{label}] R2-only={k2} R2+R3={k23} (+{k23-k2})", flush=True)
    findings["region3_ablation"] = r3_ablation

    # ---------------- per-flavor gate leak
    def per_flavor_gate(gcut):
        out = {}
        for fl in FLAVORS:
            sub_i = np.array([i for i, r in enumerate(un) if r["flavor"] == fl])
            slips = un_g[sub_i] >= gcut
            conf = un_confab[sub_i].astype(bool)
            out[fl] = {"n": int(len(sub_i)), "n_slip_to_R1": int(slips.sum()),
                       "confabs_slipping": int((conf & slips).sum()),
                       "confabs_total": int(conf.sum())}
        return out
    findings["per_flavor_gate_leak"] = {
        label: per_flavor_gate(candidates[label]["gate_cut"]) for label in candidates}

    # ---------------- permutation nulls, per candidate operating point
    findings["permutation_nulls"] = {}
    for label, rec in candidates.items():
        gcut, mcut = rec["gate_cut"], rec["m_cut"]
        cls = classify(gcut, mcut)
        r3_only = cls["r3"] & ~cls["r2"]
        obs_r3only = int((un_confab.astype(bool) & r3_only).sum())
        obs_reached = int((un_confab.astype(bool) & cls["reached"]).sum())
        un_unans_side = un_g < gcut
        r2_fixed = un_unans_side & (short > 0.0)

        rng = np.random.default_rng(SEED + 101)
        perm_r3 = []
        for _ in range(N_PERM):
            mp = mm.copy()
            for fl in FLAVORS:
                idx = np.where(flav_un == fl)[0]
                mp[idx] = rng.permutation(mm[idx])
            r3p = un_unans_side & (mp >= mcut)
            perm_r3.append(int((un_confab.astype(bool) & r3p & ~r2_fixed).sum()))
        perm_r3 = np.array(perm_r3)
        p_m = float((np.sum(perm_r3 >= obs_r3only) + 1) / (N_PERM + 1))

        rng = np.random.default_rng(SEED + 202)
        perm_reach = []
        for _ in range(N_PERM):
            gp = rng.permutation(un_g)
            uns = gp < gcut
            reach = (uns & (short > 0.0)) | (uns & (mm >= mcut))
            perm_reach.append(int((un_confab.astype(bool) & reach).sum()))
        perm_reach = np.array(perm_reach)
        p_g = float((np.sum(perm_reach >= obs_reached) + 1) / (N_PERM + 1))

        findings["permutation_nulls"][label] = {
            "permute_m_within_flavor": {"obs_r3only_reachable_confab": obs_r3only,
                                        "perm_mean": round(float(perm_r3.mean()), 2),
                                        "p": round(p_m, 4)},
            "permute_g": {"obs_reached_confab": obs_reached,
                          "perm_mean": round(float(perm_reach.mean()), 2),
                          "p": round(p_g, 4)}}
        print(f"PERM[{label}] m: obs={obs_r3only} mean={perm_r3.mean():.1f} p={p_m:.3f} | "
              f"g: obs={obs_reached} mean={perm_reach.mean():.1f} p={p_g:.3f}", flush=True)

    # ---------------- aim-small gate derivation (half-effect, per candidate)
    # The gate math follows the aim-small directive: thresholds derive from the
    # expected effect size and its uncertainty (below the half-effect CI lower
    # bound with margin), never from round defaults. Points whose half-effect CI
    # lower bound is non-positive CANNOT support a gate (no detectable room).
    findings["aim_small_gate_derivation"] = {}
    for label in candidates:
        he = op_table[label]["half_effect"]
        d_refusal = {k: he["g2_refused"][k] - base["g2_refused"]
                     for k in ("mean", "lo", "hi")}
        d_confab = {"mean": base["g3_confab"] - he["g3_confab"]["mean"],
                    "lo": base["g3_confab"] - he["g3_confab"]["hi"],
                    "hi": base["g3_confab"] - he["g3_confab"]["lo"]}
        feasible = d_confab["lo"] > 0
        findings["aim_small_gate_derivation"][label] = {
            "delta_refusals_half_effect": d_refusal,
            "delta_confabs_killed_half_effect": d_confab,
            "gate_feasible": bool(feasible),
            "suggested_gates": ({
                "G1_collateral_max": int(op_table[label]["oracle"]
                                         ["g1_correct_collateral"]["hi"]),
                "G2_min_extra_refusals_on_unanswerable": max(1, int(0.7 * d_refusal["lo"])),
                "G3_min_confabs_killed": max(1, int(0.7 * d_confab["lo"])),
            } if feasible else None)}
        print(f"aim-small[{label}] feasible={feasible} "
              f"{json.dumps(findings['aim_small_gate_derivation'][label]['suggested_gates'])}",
              flush=True)

    out_dir = al_prep / ("radial_ceiling_true" if args.gate == "logistic"
                         else f"radial_ceiling_true_gate_{args.gate}")
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "findings.json").write_text(json.dumps(findings, indent=2))
    print(f"WROTE {out_dir / 'findings.json'}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
