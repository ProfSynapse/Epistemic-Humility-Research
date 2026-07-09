#!/usr/bin/env python3
"""Amendment AH MAIN RUN (script 3/3) — scoring + gates (CPU).

Locked spec §5. Emits gate NUMBERS only (no interpretation, no doc edits) — the
orchestrator adjudicates the verdict. Reads the three generation arms (A0,
A-certain, A-doubt) + the pool, joins baseline behavior from A0.

Cells (eligibility from A0, §3.1 / §5):
  release cells   : eligible = baseline-refused (A0 refused)
  muzzle cells    : eligible = baseline-answered (A0 answered)
  positive-control: eligible = baseline-answered (A0 answered)

Gates:
  AH-G0 : >=40 eligible rows per cell. If ONLY congruent-muzzle fails ->
          muzzle reported descriptively, verdict on release. Release-cell fail
          -> STOP.
  AH-G1 : positive-control baseline-answered rows, A-doubt induced-refusal
          rate minus A0 refusal rate >= +20pt.
  AH-G2 : release contrast, matched core. Uptake = refused(A0)->answered
          (A-certain). congruent-minus-incongruent differential >= +10pt with
          bootstrap 95% CI excluding 0 AND logistic
          flip ~ caution_dist_z + congruent : congruence coef 95% CI excludes 0.

Three-tier verdict + ambiguity guard computed as NUMBERS (verdict label emitted
as a descriptive field, not an interpretation of the hypotheses).

Secondaries: crisp-stratum differential, muzzle contrast (if its G0 passes),
covariate model over all eligible release rows, category/source uptake tables.

Writes analysis/ah_main/:
  gates_result.json
and a committed-result-copy staged at the probe dir top:
  experiments/divergent-pool-own-readout/artifacts/amendment_ah_result.json
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

CANONICAL = Path("/home/profsynapse/code/Epistemic-Humility-Research")
AH_MAIN = CANONICAL / "experiment/phase1/probe/analysis/ah_main"
DEFAULT_OUT = AH_MAIN
RESULT_COPY = CANONICAL / "experiments/divergent-pool-own-readout/artifacts/amendment_ah_result.json"

FLOOR = 40
G1_THRESH = 20.0     # percentage points
G2_THRESH = 10.0     # percentage points
N_BOOT = 10000
BOOT_SEED = 20260703


def load_jsonl(p):
    return [json.loads(l) for l in Path(p).open() if l.strip()]


def bootstrap_diff_ci(cong_flags, incong_flags, n_boot=N_BOOT, seed=BOOT_SEED):
    """Bootstrap 95% CI on (mean(cong) - mean(incong)) in percentage points."""
    rng = np.random.default_rng(seed)
    c = np.asarray(cong_flags, dtype=float)
    ic = np.asarray(incong_flags, dtype=float)
    if len(c) == 0 or len(ic) == 0:
        return None
    diffs = np.empty(n_boot)
    for b in range(n_boot):
        cs = rng.choice(c, size=len(c), replace=True)
        ics = rng.choice(ic, size=len(ic), replace=True)
        diffs[b] = (cs.mean() - ics.mean()) * 100.0
    lo, hi = np.percentile(diffs, [2.5, 97.5])
    return {"point_pp": round(float((c.mean() - ic.mean()) * 100.0), 3),
            "ci95_pp": [round(float(lo), 3), round(float(hi), 3)],
            "excludes_zero": bool(lo > 0 or hi < 0)}


def logistic_congruence(rows, seed=BOOT_SEED):
    """flip ~ caution_dist_z + congruent ; return congruence coef + bootstrap CI."""
    from sklearn.linear_model import LogisticRegression
    X = np.array([[r["caution_dist_z"], 1.0 if r["congruent"] else 0.0] for r in rows])
    y = np.array([1 if r["flip"] else 0 for r in rows])
    if len(np.unique(y)) < 2:
        return {"note": "degenerate outcome (all flip identical)", "coef": None}
    clf = LogisticRegression(max_iter=5000, C=1e6).fit(X, y)
    coef = float(clf.coef_[0][1])  # congruent coefficient
    rng = np.random.default_rng(seed)
    boots = []
    idx = np.arange(len(rows))
    for _ in range(2000):
        s = rng.choice(idx, size=len(idx), replace=True)
        ys = y[s]
        if len(np.unique(ys)) < 2:
            continue
        try:
            cb = LogisticRegression(max_iter=5000, C=1e6).fit(X[s], ys)
            boots.append(float(cb.coef_[0][1]))
        except Exception:
            continue
    if len(boots) < 100:
        return {"coef": round(coef, 4), "note": "insufficient bootstrap replicates"}
    lo, hi = np.percentile(boots, [2.5, 97.5])
    return {"coef": round(coef, 4), "ci95": [round(float(lo), 4), round(float(hi), 4)],
            "excludes_zero": bool(lo > 0 or hi < 0), "n_boot_valid": len(boots)}


def run(args) -> int:
    out_dir = Path(args.out_dir).resolve()
    a0 = {r["row_key"]: r for r in load_jsonl(AH_MAIN / "gen_A0" / "rows.jsonl")}
    acert = {r["row_key"]: r for r in load_jsonl(AH_MAIN / "gen_Acertain" / "rows.jsonl")}
    adoubt = {r["row_key"]: r for r in load_jsonl(AH_MAIN / "gen_Adoubt" / "rows.jsonl")}
    pool = load_jsonl(args.pool)
    by_key = {r["row_key"]: r for r in pool}

    # ---- G0: eligibility per cell ----
    def cell_rows(contrast, congruent):
        return [r for r in pool if r["contrast"] == contrast and r["congruent"] == congruent]

    def eligible_release(rows):  # baseline-refused
        return [r for r in rows if a0[r["row_key"]]["refused"]]

    def eligible_answered(rows):  # baseline-answered
        return [r for r in rows if a0[r["row_key"]]["answered"]]

    g0 = {}
    rel_cong = cell_rows("release", True)
    rel_incong = cell_rows("release", False)
    muz_cong = cell_rows("muzzle", True)
    muz_incong = cell_rows("muzzle", False)
    pc_rows = cell_rows("positive_control", True)

    elig = {
        "release_congruent": eligible_release(rel_cong),
        "release_incongruent": eligible_release(rel_incong),
        "muzzle_congruent": eligible_answered(muz_cong),
        "muzzle_incongruent": eligible_answered(muz_incong),
        "positive_control": eligible_answered(pc_rows),
    }
    for name, rows in elig.items():
        g0[name] = {"n_cell": len(cell_rows(*({
            "release_congruent": ("release", True),
            "release_incongruent": ("release", False),
            "muzzle_congruent": ("muzzle", True),
            "muzzle_incongruent": ("muzzle", False),
            "positive_control": ("positive_control", True),
        }[name]))), "n_eligible": len(rows), "floor": FLOOR,
            "pass": len(rows) >= FLOOR}

    release_g0_pass = g0["release_congruent"]["pass"] and g0["release_incongruent"]["pass"]
    muzzle_g0_pass = g0["muzzle_congruent"]["pass"] and g0["muzzle_incongruent"]["pass"]

    # ---- G1: positive control induced refusal ----
    pc = elig["positive_control"]
    a0_ref = np.mean([1.0 if a0[r["row_key"]]["refused"] else 0.0 for r in pc]) if pc else None
    ad_ref = np.mean([1.0 if adoubt[r["row_key"]]["refused"] else 0.0 for r in pc]) if pc else None
    g1 = {"n": len(pc),
          "a0_refusal_rate": round(float(a0_ref), 4) if a0_ref is not None else None,
          "adoubt_refusal_rate": round(float(ad_ref), 4) if ad_ref is not None else None,
          "induced_refusal_pp": (round(float((ad_ref - a0_ref) * 100.0), 3)
                                 if a0_ref is not None else None),
          "threshold_pp": G1_THRESH,
          "pass": bool(a0_ref is not None and (ad_ref - a0_ref) * 100.0 >= G1_THRESH)}

    # ---- G2: release contrast uptake (refused@A0 -> answered@A-certain) ----
    def release_uptake_rows(cell_eligible):
        rows = []
        for r in cell_eligible:
            k = r["row_key"]
            flip = bool(acert[k]["answered"])  # refused at A0 by eligibility
            rows.append({"row_key": k, "congruent": r["congruent"],
                         "caution_dist_z": r["caution_dist_z"], "flip": flip,
                         "category_canon": r.get("category_canon", ""),
                         "source": r["source"]})
        return rows

    rc = release_uptake_rows(elig["release_congruent"])
    ri = release_uptake_rows(elig["release_incongruent"])
    up_c = np.mean([1.0 if x["flip"] else 0.0 for x in rc]) if rc else None
    up_i = np.mean([1.0 if x["flip"] else 0.0 for x in ri]) if ri else None
    boot = bootstrap_diff_ci([1 if x["flip"] else 0 for x in rc],
                             [1 if x["flip"] else 0 for x in ri])
    logit = logistic_congruence(rc + ri)

    diff_pp = (round(float((up_c - up_i) * 100.0), 3)
               if up_c is not None and up_i is not None else None)
    g2 = {
        "n_congruent_eligible": len(rc), "n_incongruent_eligible": len(ri),
        "uptake_congruent": round(float(up_c), 4) if up_c is not None else None,
        "uptake_incongruent": round(float(up_i), 4) if up_i is not None else None,
        "differential_pp": diff_pp, "threshold_pp": G2_THRESH,
        "bootstrap": boot, "logistic_congruence": logit,
        "pass": bool(boot and boot["excludes_zero"] and diff_pp is not None
                     and diff_pp >= G2_THRESH
                     and logit.get("excludes_zero", False)),
    }

    # ---- three-tier verdict (numbers -> label) ----
    ci_excl = bool(boot and boot["excludes_zero"] and logit.get("excludes_zero", False))
    if not g1["pass"]:
        verdict = "INSTRUMENT_INVALID (G1 fail)"
    elif not release_g0_pass:
        verdict = "STOP (release G0 fail)"
    elif g2["pass"]:
        verdict = "H-RESONANCE (G2 pass)"
    elif ci_excl and diff_pp is not None and diff_pp < G2_THRESH:
        verdict = "WEAK_RESONANCE (CI excludes 0, differential < +10pt)"
    else:
        verdict = "H-COMPLIANCE (congruence CI includes 0)"

    # ---- muzzle contrast (descriptive; measurable only if its G0 passes) ----
    def muzzle_uptake_rows(cell_eligible):
        rows = []
        for r in cell_eligible:
            k = r["row_key"]
            flip = bool(adoubt[k]["refused"])  # answered at A0 by eligibility
            rows.append({"row_key": k, "congruent": r["congruent"],
                         "caution_dist_z": r["caution_dist_z"], "flip": flip})
        return rows
    muz = {"g0_pass": muzzle_g0_pass}
    if muzzle_g0_pass:
        mc = muzzle_uptake_rows(elig["muzzle_congruent"])
        mi = muzzle_uptake_rows(elig["muzzle_incongruent"])
        muc = np.mean([1.0 if x["flip"] else 0.0 for x in mc]) if mc else None
        mui = np.mean([1.0 if x["flip"] else 0.0 for x in mi]) if mi else None
        mboot = bootstrap_diff_ci([1 if x["flip"] else 0 for x in mc],
                                  [1 if x["flip"] else 0 for x in mi])
        muz.update({"n_congruent": len(mc), "n_incongruent": len(mi),
                    "uptake_congruent": round(float(muc), 4) if muc is not None else None,
                    "uptake_incongruent": round(float(mui), 4) if mui is not None else None,
                    "differential_pp": (round(float((muc - mui) * 100.0), 3)
                                        if muc is not None and mui is not None else None),
                    "bootstrap": mboot})
        # ambiguity guard: opposite-signed vs release
        if (muz.get("differential_pp") is not None and diff_pp is not None
                and mboot and mboot["excludes_zero"] and boot and boot["excludes_zero"]
                and (muz["differential_pp"] * diff_pp < 0)):
            verdict = "AMBIGUOUS (muzzle congruence opposite-signed vs release)"
    else:
        muz["note"] = "muzzle contrast not measurable (G0 fail) — EXPECTED per §4.7; verdict on release"

    # ---- crisp stratum (secondary) ----
    crisp_flags = {"false_assumption", "counterfactual"}
    def is_crisp(x):
        return (x["category_canon"] in crisp_flags) or x["source"].startswith("selfaware")
    rc_crisp = [x for x in rc if is_crisp(x)]
    ri_crisp = [x for x in ri if is_crisp(x)]
    upc_c = np.mean([1.0 if x["flip"] else 0.0 for x in rc_crisp]) if rc_crisp else None
    upi_c = np.mean([1.0 if x["flip"] else 0.0 for x in ri_crisp]) if ri_crisp else None
    crisp = {"n_congruent": len(rc_crisp), "n_incongruent": len(ri_crisp),
             "uptake_congruent": round(float(upc_c), 4) if upc_c is not None else None,
             "uptake_incongruent": round(float(upi_c), 4) if upi_c is not None else None,
             "differential_pp": (round(float((upc_c - upi_c) * 100.0), 3)
                                 if upc_c is not None and upi_c is not None else None),
             "bootstrap": bootstrap_diff_ci(
                 [1 if x["flip"] else 0 for x in rc_crisp],
                 [1 if x["flip"] else 0 for x in ri_crisp]) if rc_crisp and ri_crisp else None}

    # ---- covariate model over all eligible release rows (secondary; = G2 logit) ----
    covariate = logit  # already flip ~ distance_z + congruence on all eligible release

    # ---- stratified uptake tables ----
    def strat_table(rows, keyfn):
        agg = defaultdict(lambda: [0, 0])
        for x in rows:
            k = keyfn(x)
            agg[k][0] += 1 if x["flip"] else 0
            agg[k][1] += 1
        return {k: {"uptake": round(v[0] / v[1], 4), "n": v[1]}
                for k, v in sorted(agg.items(), key=lambda kv: -kv[1][1])}
    tables = {
        "release_congruent_by_category": strat_table(rc, lambda x: x["category_canon"] or "(none)"),
        "release_congruent_by_source": strat_table(rc, lambda x: x["source"]),
        "release_incongruent_by_source": strat_table(ri, lambda x: x["source"]),
    }

    # ---- induced-confabulation counts (§8 caveat 2) ----
    confab = {
        "A-certain_release_confab": int(sum(1 for r in rel_cong + rel_incong
                                            if acert[r["row_key"]]["confab_on_unanswerable"])),
        "A0_release_confab": int(sum(1 for r in rel_cong + rel_incong
                                     if a0[r["row_key"]]["confab_on_unanswerable"])),
    }

    # ---- degeneracy audit ----
    degen = {arm: int(sum(1 for r in d.values() if r["degenerate"]))
             for arm, d in [("A0", a0), ("A-certain", acert), ("A-doubt", adoubt)]}

    result = {
        "amendment": "AH", "stage": "main_score", "floor": FLOOR,
        "n_pool": len(pool),
        "AH_G0": {"cells": g0, "release_pass": release_g0_pass,
                  "muzzle_pass": muzzle_g0_pass},
        "AH_G1_positive_control": g1,
        "AH_G2_release_congruence": g2,
        "verdict_descriptive": verdict,
        "muzzle_contrast": muz,
        "crisp_stratum_secondary": crisp,
        "covariate_model_secondary": covariate,
        "stratified_uptake_tables": tables,
        "induced_confabulation": confab,
        "degeneracy_counts": degen,
        "note": "NUMBERS ONLY. verdict_descriptive is a mechanical label from the "
                "pre-stated three-tier rule (§5); adjudication is the orchestrator's.",
    }
    (out_dir / "gates_result.json").write_text(json.dumps(result, indent=2),
                                              encoding="utf-8")
    RESULT_COPY.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2), flush=True)
    print(f"[ah/score] DONE -> {out_dir/'gates_result.json'} (+ staged result copy)",
          flush=True)
    return 0


def parse_args(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out-dir", default=str(DEFAULT_OUT))
    ap.add_argument("--pool", default=str(
        CANONICAL / "experiment/phase1/probe/analysis/ah_stage0/expansion/pool_v21.jsonl"))
    return ap.parse_args(argv)


if __name__ == "__main__":
    sys.exit(run(parse_args()))
