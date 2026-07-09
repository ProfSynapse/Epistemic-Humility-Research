"""Radial-steering controller ceiling audit (Amendment AL pre-registration).

Offline, CPU-only, probe-as-oracle (Amendment O pattern) applied to a
three-goal composite pre-generation controller. We do NOT run the model; we
ask: given four confirmed near-orthogonal anchor readouts, what is the CEILING
of a per-row conditional steering controller, and what does an honest
half-effect version deliver? These numbers become AL's gate-threshold table.

Control law (per row), from anchor readouts:
  g  answerability gate  = frozen L24 answerability probe log-odds (score_L24;
       HIGH = answerable/known). Known weakness on the ambiguous flavor.
  c  caution distance    = caution_dist_z (z-scored boundary distance).
  m  commitment proj.    = confab-vs-refuse direction at L24, OUT-OF-FOLD
       (fit per CV fold, residualised vs caution+flavor; no row scores itself).
  f  flavor              = category_canon.

  Region 1: g >= gate_cut (ANSWERABLE)  -> no intervention (protect answers;
            over-refusal is near-irreversible per the AG asymmetry).
  Region 2: g <  gate_cut (UNANSWERABLE) AND c below the flavor-specific
            refusal threshold -> caution injection (goal: make it say IDK).
  Region 3: g <  gate_cut AND m >= m_cut -> additionally anti-commitment steer
            (goal: kill confabs that leak past caution). Overlaps Region 2.

Oracle assumption: each region's intervention achieves its intended flip.
  R2 flip: a row that WOULD confab is turned into a refusal.
  R3 flip: a row that WOULD confab is turned into a refusal (commit killed).
Half-effect: each intervention flips only 50% of its targets (Bernoulli 0.5).

Goal metrics:
  G1 correct-retained : answerable rows answered-correctly at baseline that the
     controller does NOT touch (Region-1 protection). Gate false positives
     (answerable rows that fall UNANSWERABLE and get steered) = collateral.
  G2 unknowns-refused : refusal count on unanswerable rows, baseline vs after
     region-2 flips.
  G3 confab-count     : confabs on unanswerable rows, baseline vs after
     region-2/3 flips; plus confabs OUTSIDE all regions (unreachable).

CPU discipline: BLAS threads capped; L24 loaded once; commitment direction is a
mean-difference (no per-fold heavy fit), residualised leak-free per fold.
Seed 20260704.
"""
import warnings
warnings.filterwarnings("ignore")
import os
from pathlib import Path
os.environ.setdefault("OMP_NUM_THREADS", "8")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "8")
os.environ.setdefault("MKL_NUM_THREADS", "8")
os.environ.setdefault("NUMEXPR_NUM_THREADS", "8")
import json
import numpy as np
from collections import Counter, defaultdict
from sklearn.linear_model import LogisticRegression, LinearRegression
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import StratifiedKFold

SEED = 20260704
rng_global = np.random.default_rng(SEED)
BASE = os.path.dirname(os.path.abspath(__file__))
REPO = Path(__file__).resolve().parents[4]
# Historical gitignored inputs remain in the legacy probe analysis tree. Keep
# this dependency explicit until the AH/MI data clusters migrate together.
AN = str(REPO / "experiment" / "phase1" / "probe" / "analysis")
GEOM = os.path.join(AN, "mi_category_geometry_20260704")
CACHE = os.path.join(GEOM, "cache")
A0 = os.path.join(AN, "ah_main", "gen_A0", "rows.jsonl")
L_COMMIT = 24
N_SPLITS = 5
N_REPEAT = 4        # repeated CV for the out-of-fold m score (averaged)
N_BOOT = 1000
N_PERM = 200

findings = {"seed": SEED, "layer_commitment": L_COMMIT,
            "config": {"cv": f"{N_REPEAT}x{N_SPLITS}", "n_boot": N_BOOT,
                       "n_perm": N_PERM}}

# ---------------------------------------------------------------- load rows
rows = [json.loads(l) for l in open(A0)]
findings["n_total_A0"] = len(rows)

man = [json.loads(l) for l in open(os.path.join(CACHE, "manifest.jsonl"))]
man_idx = {m["row_key"]: i for i, m in enumerate(man)}

# Behavioral fields present on every row. g and c present on every row.
# m requires an activation row (cache join). All unanswerable rows join;
# the 189 answerable rows missing from the cache are Region-1 protected and
# never need m, so this is not a gap for the controller.
for r in rows:
    r["_in_cache"] = r["row_key"] in man_idx
    r["g"] = float(r["score_L24"])            # answerability log-odds (high=answerable)
    r["c"] = float(r["caution_dist_z"])       # caution distance z
    r["flavor"] = r["category_canon"]

un = [r for r in rows if r["gold_class"] == "unanswerable"
      and not r["degenerate"] and not r["ungradeable"]]
an = [r for r in rows if r["gold_class"] == "answerable"]

assert all(r["_in_cache"] for r in un), "some unanswerable rows lack activations"
findings["cache_join"] = {
    "unanswerable_joined": f"{sum(r['_in_cache'] for r in un)}/{len(un)}",
    "answerable_joined": f"{sum(r['_in_cache'] for r in an)}/{len(an)}",
    "note": "unanswerable fully joined; missing answerable rows are Region-1 "
            "protected and never require m."}

# ---------------------------------------------------------------- m: OOF commitment proj at L24
# Direction = mean(confab) - mean(refuse) within unanswerable, at L24,
# residualised vs caution+flavor. Built per CV-fold on TRAIN rows only; the
# held-out rows are projected onto the train-fold direction => no row scores
# itself. Averaged over repeats for a stable OOF scalar.
X24 = np.load(os.path.join(CACHE, f"L{L_COMMIT}.npy")).astype(np.float32)
un_cidx = np.array([man_idx[r["row_key"]] for r in un])
Xun = X24[un_cidx].astype(np.float64)
del X24
y_confab = np.array([1 if r["confab_on_unanswerable"] else 0 for r in un])
c_un = np.array([r["c"] for r in un])
flav_un = np.array([r["flavor"] for r in un])
FLAVORS = sorted(set(flav_un))
FREF = FLAVORS[1:]  # drop-one dummy coding reference


def onehot(catv, ref):
    return np.hstack([(catv == c).astype(float).reshape(-1, 1) for c in ref])


def confounds(idx):
    return np.hstack([c_un[idx].reshape(-1, 1), onehot(flav_un[idx], FREF)])


def residualise_fit(Xtr, tr):
    """Fit LinearRegression(X ~ caution+flavor) on train, return residualiser."""
    C = confounds(tr)
    lr = LinearRegression().fit(C, Xtr)
    return lr


m_oof = np.zeros(len(un))
n_seen = np.zeros(len(un))
for rep in range(N_REPEAT):
    skf = StratifiedKFold(n_splits=N_SPLITS, shuffle=True, random_state=SEED + rep)
    for tr, te in skf.split(np.arange(len(un)), y_confab):
        # residualise activations vs confounds using TRAIN fit
        lr = residualise_fit(Xun[tr], tr)
        Rtr = Xun[tr] - lr.predict(confounds(tr))
        Rte = Xun[te] - lr.predict(confounds(te))
        # standardise on train
        sc = StandardScaler().fit(Rtr)
        Rtr = sc.transform(Rtr)
        Rte = sc.transform(Rte)
        # direction = confab-mean minus refuse-mean on TRAIN residuals
        ytr = y_confab[tr]
        d = Rtr[ytr == 1].mean(0) - Rtr[ytr == 0].mean(0)
        d = d / (np.linalg.norm(d) + 1e-12)
        # project held-out rows
        m_oof[te] += Rte @ d
        n_seen[te] += 1
m_oof = m_oof / n_seen  # average over repeats (each row held out once per repeat)

from sklearn.metrics import roc_auc_score
m_auroc = roc_auc_score(y_confab, m_oof)
findings["commitment_m"] = {
    "layer": L_COMMIT,
    "oof_auroc_confab_vs_refuse": round(float(m_auroc), 4),
    "construction": "mean(confab)-mean(refuse) residualised vs caution+flavor, "
                    "per-fold on train only, averaged over repeats (OOF).",
    "note": "positive m = looks like a row that WILL confab (commitment); this "
            "is the anti-commitment steering target signal."}
print(f"m OOF AUROC (confab vs refuse) = {m_auroc:.4f}", flush=True)

# attach m to the un rows
for r, mv in zip(un, m_oof):
    r["m"] = float(mv)

# ---------------------------------------------------------------- per-flavor refusal threshold in caution
# Refusal is one curve in caution distance with per-flavor offsets. Fit a
# per-flavor logistic (refused vs confab) on caution_dist_z; the threshold is
# the caution_dist_z at which P(refuse)=0.5. A row is "below threshold"
# (will-confab side) when its c is under that boundary. We fit on A0 itself
# (descriptive decision boundary), reported explicitly.
flavor_thresh = {}
for fl in FLAVORS:
    sub = [r for r in un if r["flavor"] == fl]
    cc = np.array([r["c"] for r in sub])
    yy = np.array([r["refused"] for r in sub]).astype(int)  # 1=refused
    if len(set(yy)) < 2:
        # degenerate flavor: use the midpoint between class means
        thr = float(cc.mean())
        flavor_thresh[fl] = {"threshold_z": thr, "method": "mean(only-one-class)"}
        continue
    lr = LogisticRegression(max_iter=2000).fit(cc.reshape(-1, 1), yy)
    b0 = lr.intercept_[0]; b1 = lr.coef_[0][0]
    thr = float(-b0 / b1) if abs(b1) > 1e-9 else float(cc.mean())
    flavor_thresh[fl] = {"threshold_z": round(thr, 4),
                         "slope": round(float(b1), 4),
                         "n": len(sub),
                         "refuse_rate": round(float(yy.mean()), 4)}
findings["flavor_refusal_thresholds"] = flavor_thresh
print("flavor thresholds:", {k: v.get("threshold_z") for k, v in flavor_thresh.items()}, flush=True)

# shortfall for each unanswerable row: how far below its flavor threshold (>=0 means below)
for r in un:
    thr = flavor_thresh[r["flavor"]]["threshold_z"]
    r["_shortfall"] = thr - r["c"]   # positive => below threshold => at risk of confab

# ---------------------------------------------------------------- region classification + sweep
# gate operating point: g >= gate_cut => ANSWERABLE (Region 1).
# Region 2: unanswerable-side (g < gate_cut) AND shortfall > 0 (below flavor thr).
# Region 3: unanswerable-side AND m >= m_cut.

def classify(gate_cut, m_cut):
    """Return per-population region membership and the controller outcome sets.
    Returns dict of index arrays / counts used by the metric functions."""
    # answerable population
    an_g = np.array([r["g"] for r in an])
    an_answerable_side = an_g >= gate_cut          # correctly left alone (Region 1)
    an_unans_side = ~an_answerable_side            # gate false positive -> steered = collateral
    # unanswerable population
    un_g = np.array([r["g"] for r in un])
    un_unans_side = un_g < gate_cut                # gate says unanswerable (correct)
    un_ans_side = ~un_unans_side                   # gate false negative: unanswerable slips to Region 1
    short = np.array([r["_shortfall"] for r in un])
    mm = np.array([r["m"] for r in un])
    r2 = un_unans_side & (short > 0.0)             # caution injection target
    r3 = un_unans_side & (mm >= m_cut)             # anti-commitment target
    reached = r2 | r3                              # any intervention on unanswerable side
    return {
        "an_answerable_side": an_answerable_side, "an_unans_side": an_unans_side,
        "un_unans_side": un_unans_side, "un_ans_side": un_ans_side,
        "r2": r2, "r3": r3, "reached": reached,
    }


# baseline behavioral arrays
an_correct = np.array([1 if (r["answered"] and r["correct"] is True) else 0 for r in an])
an_answered = np.array([r["answered"] for r in an]).astype(int)
un_refused = np.array([r["refused"] for r in un]).astype(int)
un_confab = np.array([1 if r["confab_on_unanswerable"] else 0 for r in un]).astype(int)
un_flav = flav_un


def goal_metrics(cls, effect=1.0, rng=None):
    """Compute the three goal metrics under a given per-target flip prob (effect).
    effect=1.0 = oracle; 0.5 = half-effect (Bernoulli). Returns a dict of counts."""
    reached = cls["reached"]
    r2 = cls["r2"]; r3 = cls["r3"]
    # which unanswerable-side reached rows are baseline confabs (the flippable ones)
    confab_reached = un_confab.astype(bool) & reached
    # apply effect: each reached confab flips to refuse w.p. effect
    if effect >= 1.0:
        flipped = confab_reached.copy()
    else:
        draw = (rng if rng is not None else rng_global).random(len(un)) < effect
        flipped = confab_reached & draw

    # G2: unknowns refused = baseline refusals + newly flipped confabs
    #     (rows already refused stay refused; caution injection only helps.)
    refused_after = un_refused.copy()
    refused_after[flipped] = 1
    g2_after = int(refused_after.sum())

    # G3: confabs remaining = baseline confabs minus flipped
    confab_after = un_confab.copy()
    confab_after[flipped] = 0
    g3_after = int(confab_after.sum())

    # unreachable confabs = baseline confabs not in any region (independent of effect)
    unreachable_confab = int((un_confab.astype(bool) & ~reached).sum())

    # G1: correct answers retained. An answerable correct row is retained iff it
    # is NOT steered. It is steered only if it falls on the unanswerable side
    # (gate false positive). Region-1 rows are protected. Oracle-safe assumption:
    # steering an answerable-correct row is collateral (worst case: it may refuse).
    an_steered = cls["an_unans_side"]
    g1_retained = int((an_correct.astype(bool) & ~an_steered).sum())
    g1_collateral = int((an_correct.astype(bool) & an_steered).sum())

    return {"g2_refused": g2_after, "g3_confab": g3_after,
            "g1_correct_retained": g1_retained, "g1_correct_collateral": g1_collateral,
            "unreachable_confab": unreachable_confab,
            "n_flipped": int(flipped.sum())}


# baselines (no controller)
base = {
    "g1_correct_answerable": int(an_correct.sum()),
    "g2_refused": int(un_refused.sum()),
    "g3_confab": int(un_confab.sum()),
    "n_answerable": len(an), "n_unanswerable": len(un),
}
findings["baseline"] = base
print("BASELINE", base, flush=True)

# ---------------------------------------------------------------- cutoff sweep (operating curves)
# Gate grid spans the g range densely so the collateral/coverage curve is fully
# traced. The AG asymmetry (over-refusal near-irreversible) means we care about
# the low-collateral end: raising gate_cut admits more rows to the unanswerable
# side (more confab coverage) but eventually starts catching answerable rows.
gate_grid = [float(x) for x in np.quantile([r["g"] for r in an + un], np.linspace(0.02, 0.75, 18))]
gate_grid = sorted(set([round(x, 3) for x in gate_grid] + [-2.0, 0.0, 2.0, 5.0, 8.0]))
m_grid = [float(x) for x in np.quantile(m_oof, [0.5, 0.6, 0.7, 0.75, 0.8, 0.85, 0.9, 0.95])]
m_grid = sorted(set(round(x, 3) for x in m_grid))

sweep = []
for gcut in gate_grid:
    for mcut in m_grid:
        cls = classify(gcut, mcut)
        gm = goal_metrics(cls, effect=1.0)
        # collateral coverage bookkeeping
        rec = {
            "gate_cut": gcut, "m_cut": mcut,
            "r2_n": int(cls["r2"].sum()), "r3_n": int(cls["r3"].sum()),
            "r2r3_overlap": int((cls["r2"] & cls["r3"]).sum()),
            "reached_n": int(cls["reached"].sum()),
            "an_gate_fp": int(cls["an_unans_side"].sum()),          # answerable steered
            "un_gate_fn": int(cls["un_ans_side"].sum()),            # unanswerable slips to R1
            **gm,
        }
        sweep.append(rec)
findings["sweep"] = sweep

# ---------------------------------------------------------------- pick candidate operating points
# Selection respects the AG asymmetry: over-refusal of a correct answerable row
# is near-irreversible, so G1 collateral is weighted heavily. We surface three
# points spanning the tradeoff:
#   conservative : zero G1 collateral, then max confabs killed.
#   balanced     : max (confabs killed) minus a heavy collateral penalty.
#   aggressive   : max confabs killed with collateral <= a small tolerance.
def killed(rec):
    return base["g3_confab"] - rec["g3_confab"]

zero_coll = [r for r in sweep if r["g1_correct_collateral"] == 0]
pool = zero_coll if zero_coll else sweep
conservative = max(pool, key=killed)
# balanced: killed minus heavy penalty (each irreversible correct loss costs 10 confabs)
balanced = max(sweep, key=lambda r: killed(r) - 10 * r["g1_correct_collateral"])
# aggressive: allow small collateral (<=3 correct rows), maximise killed
agg_pool = [r for r in sweep if r["g1_correct_collateral"] <= 3]
aggressive = max(agg_pool, key=killed)

candidates = {"conservative": conservative, "balanced": balanced, "aggressive": aggressive}
# de-dup identical points but keep labels
findings["candidate_operating_points"] = {
    k: {"gate_cut": v["gate_cut"], "m_cut": v["m_cut"]} for k, v in candidates.items()}

# ---------------------------------------------------------------- bootstrap CIs for candidates
def bootstrap_point(gcut, mcut, effect, n_boot=N_BOOT):
    """Resample rows (answerable and unanswerable independently) and recompute
    goal metrics. For half-effect, redraw the Bernoulli flips each resample."""
    cls = classify(gcut, mcut)
    reached = cls["reached"]; r2 = cls["r2"]; r3 = cls["r3"]
    confab_reached = un_confab.astype(bool) & reached
    an_steered = cls["an_unans_side"]
    an_idx = np.arange(len(an)); un_idx = np.arange(len(un))
    rng = np.random.default_rng(SEED + 7)
    g1r = []; g2r = []; g3r = []; g1c = []; unreach = []
    for _ in range(n_boot):
        ai = rng.choice(an_idx, len(an_idx), replace=True)
        ui = rng.choice(un_idx, len(un_idx), replace=True)
        # G1
        g1r.append(int((an_correct[ai].astype(bool) & ~an_steered[ai]).sum()))
        g1c.append(int((an_correct[ai].astype(bool) & an_steered[ai]).sum()))
        # flips
        cr = confab_reached[ui]
        if effect >= 1.0:
            flip = cr
        else:
            flip = cr & (rng.random(len(ui)) < effect)
        ref_after = un_refused[ui].copy(); ref_after[flip] = 1
        con_after = un_confab[ui].copy(); con_after[flip] = 0
        g2r.append(int(ref_after.sum()))
        g3r.append(int(con_after.sum()))
        unreach.append(int((un_confab[ui].astype(bool) & ~reached[ui]).sum()))

    def ci(a):
        a = np.array(a)
        return {"mean": round(float(a.mean()), 2),
                "lo": round(float(np.quantile(a, 0.025)), 2),
                "hi": round(float(np.quantile(a, 0.975)), 2)}
    return {"g1_correct_retained": ci(g1r), "g1_correct_collateral": ci(g1c),
            "g2_refused": ci(g2r), "g3_confab": ci(g3r),
            "unreachable_confab": ci(unreach)}


op_table = {}
for label, rec in candidates.items():
    gcut, mcut = rec["gate_cut"], rec["m_cut"]
    cls = classify(gcut, mcut)
    entry = {
        "gate_cut": gcut, "m_cut": mcut,
        "region_census": {
            "r2_n": int(cls["r2"].sum()), "r3_n": int(cls["r3"].sum()),
            "r2r3_overlap": int((cls["r2"] & cls["r3"]).sum()),
            "reached_n": int(cls["reached"].sum()),
            "an_gate_fp_steered": int(cls["an_unans_side"].sum()),
            "un_gate_fn_toR1": int(cls["un_ans_side"].sum()),
        },
        "baseline": {"g1": base["g1_correct_answerable"], "g2": base["g2_refused"],
                     "g3": base["g3_confab"]},
        "oracle": bootstrap_point(gcut, mcut, 1.0),
        "half_effect": bootstrap_point(gcut, mcut, 0.5),
    }
    op_table[label] = entry
    print(f"[{label}] gate={gcut} m={mcut} killed(oracle)={base['g3_confab']-entry['oracle']['g3_confab']['mean']:.0f} "
          f"collateral={entry['oracle']['g1_correct_collateral']['mean']:.1f}", flush=True)
findings["operating_point_table"] = op_table

# ---------------------------------------------------------------- Region-3 ablation
# Does anti-commitment steering (Region 3, driven by m) add confab kills beyond
# caution injection alone (Region 2)? For each candidate we compute the oracle
# confabs killed with Region 2 ONLY vs Region 2+3, and the number of confabs
# UNIQUELY reachable via Region 3 (in r3, not in r2).
r3_ablation = {}
for label, rec in candidates.items():
    gcut, mcut = rec["gate_cut"], rec["m_cut"]
    cls = classify(gcut, mcut)
    r2 = cls["r2"]; r3 = cls["r3"]
    killed_r2only = int((un_confab.astype(bool) & r2).sum())
    killed_r2r3 = int((un_confab.astype(bool) & (r2 | r3)).sum())
    r3_unique_confab = int((un_confab.astype(bool) & r3 & ~r2).sum())
    # collateral is identical (both use the same gate); R3 only adds unanswerable-side reach
    r3_ablation[label] = {
        "confabs_killed_R2_only": killed_r2only,
        "confabs_killed_R2plusR3": killed_r2r3,
        "R3_unique_confabs": r3_unique_confab,
        "R3_marginal_gain": killed_r2r3 - killed_r2only,
        "note": "oracle counts; R3 adds reach on the unanswerable side only, so "
                "G1 collateral is unchanged between R2-only and R2+R3."}
    print(f"[{label}] R2-only killed={killed_r2only} R2+R3 killed={killed_r2r3} "
          f"(R3 marginal +{killed_r2r3-killed_r2only})", flush=True)
findings["region3_ablation"] = r3_ablation

# ---------------------------------------------------------------- per-flavor collateral (ambiguous focus)
# Answerable rows are all category "(none)"; the flavor-collateral concern from
# the brief is about the ambiguous UNANSWERABLE rows where the gate is weak and
# g may read high enough to slip to Region 1 (a missed confab), OR low enough to
# over-steer. Report the gate's per-flavor behaviour on unanswerable rows.
def per_flavor_gate(gcut):
    out = {}
    for fl in FLAVORS:
        sub = [r for r in un if r["flavor"] == fl]
        g = np.array([r["g"] for r in sub])
        conf = np.array([1 if r["confab_on_unanswerable"] else 0 for r in sub])
        slips = (g >= gcut)  # slips to Region 1 = untouched
        out[fl] = {"n": len(sub),
                   "n_slip_to_R1": int(slips.sum()),
                   "confabs_slipping": int((conf.astype(bool) & slips).sum()),
                   "confabs_total": int(conf.sum())}
    return out
findings["per_flavor_gate_leak"] = {label: per_flavor_gate(candidates[label]["gate_cut"])
                                    for label in candidates}

# ---------------------------------------------------------------- permutation nulls (balanced point)
# On the balanced operating point:
#  (a) permute m within flavor -> does Region 3's reachable-confab count collapse
#      toward what random m would reach?
#  (b) permute g -> does the gate's protective structure collapse?
bal = candidates["balanced"]
gcut, mcut = bal["gate_cut"], bal["m_cut"]

# observed: confabs uniquely reachable via Region 3 (in r3, NOT already in r2)
cls = classify(gcut, mcut)
r2 = cls["r2"]; r3 = cls["r3"]
r3_only = r3 & ~r2
obs_r3only_confab = int((un_confab.astype(bool) & r3_only).sum())
obs_reached_confab = int((un_confab.astype(bool) & cls["reached"]).sum())

# (a) permute m within flavor
rng = np.random.default_rng(SEED + 101)
perm_r3only = []
m_arr = np.array([r["m"] for r in un])
un_g = np.array([r["g"] for r in un])
un_unans_side = un_g < gcut
short = np.array([r["_shortfall"] for r in un])
r2_fixed = un_unans_side & (short > 0.0)
for _ in range(N_PERM):
    mp = m_arr.copy()
    for fl in FLAVORS:
        mask = (flav_un == fl)
        idx = np.where(mask)[0]
        mp[idx] = rng.permutation(m_arr[idx])
    r3p = un_unans_side & (mp >= mcut)
    r3p_only = r3p & ~r2_fixed
    perm_r3only.append(int((un_confab.astype(bool) & r3p_only).sum()))
perm_r3only = np.array(perm_r3only)
p_m = float((np.sum(perm_r3only >= obs_r3only_confab) + 1) / (N_PERM + 1))

# (b) permute g -> reached confab count (does gate structure matter?)
rng = np.random.default_rng(SEED + 202)
perm_reached = []
g_all_un = un_g.copy()
for _ in range(N_PERM):
    gp = rng.permutation(g_all_un)
    uns = gp < gcut
    r2p = uns & (short > 0.0)
    r3p = uns & (m_arr >= mcut)
    reachedp = r2p | r3p
    perm_reached.append(int((un_confab.astype(bool) & reachedp).sum()))
perm_reached = np.array(perm_reached)
p_g = float((np.sum(perm_reached >= obs_reached_confab) + 1) / (N_PERM + 1))

findings["permutation_nulls"] = {
    "operating_point": "balanced",
    "permute_m_within_flavor": {
        "obs_r3only_reachable_confab": obs_r3only_confab,
        "perm_mean": round(float(perm_r3only.mean()), 2),
        "perm_p95": round(float(np.quantile(perm_r3only, 0.95)), 2),
        "p": round(p_m, 4),
        "interp": "if m carries confab-specific structure, observed Region-3-only "
                  "reachable confabs exceed the within-flavor-permuted null."},
    "permute_g": {
        "obs_reached_confab": obs_reached_confab,
        "perm_mean": round(float(perm_reached.mean()), 2),
        "perm_p95": round(float(np.quantile(perm_reached, 0.95)), 2),
        "p": round(p_g, 4),
        "interp": "permuting g breaks the gate's targeting of the unanswerable "
                  "population; reached-confab count should shift."},
}
print(f"PERM m-within-flavor: obs={obs_r3only_confab} perm_mean={perm_r3only.mean():.1f} p={p_m:.3f}", flush=True)
print(f"PERM g: obs={obs_reached_confab} perm_mean={perm_reached.mean():.1f} p={p_g:.3f}", flush=True)

# ---------------------------------------------------------------- write findings
with open(os.path.join(BASE, "findings.json"), "w") as f:
    json.dump(findings, f, indent=2)
print("WROTE findings.json", flush=True)
