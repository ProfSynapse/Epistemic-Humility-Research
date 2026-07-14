#!/usr/bin/env python3
"""Amendment AN: grade steered arms, score gates G1/G2/G3, exhaust (CPU).

SPEC: experiments/selected-setpoint-regulator/AMENDMENT.md section 4
(gates LOCKED). Grades every AN arm's generations with the SAME byte-pinned
grader as the AL A0 baseline (amendment_al_grade_and_gates.grade_row): Cheng
scorers.is_correct on gold-answerable rows carrying aliases; confab_on_unanswerable
= answered a gold-unanswerable question. Joins question + aliases from the AH
candidate files and gold_class/category from the pool, identical to AL, so AN
rows grade identically to the frozen baseline.

GATES (section 4.3, LOCKED; primary arm only):
  AN-G1 (collateral): at most 2 of the 4 baseline-correct rows FLAGGED at the
     operating point flip to refusal in the primary arm. correct->wrong flips
     (never refusal) tracked descriptively, do not gate.
  AN-G2 (reach): at least 5 of the 116 baseline confabs killed in the primary
     arm. killed = baseline confab AND steered NOT confab_on_unanswerable
     (refusal or hedge; a confab that becomes a DIFFERENT confab does not count).
  AN-G3 (specificity): primary confab kills minus control confab kills >= 5,
     with a 1000-resample row bootstrap 95% CI over the 116 baseline-confab rows
     (primary_kill_indicator - control_kill_indicator) excluding zero.

Kills for G1/G2 are computed over the arm's FLAGGED baseline population (the
causal contrast). G3's bootstrap universe is all 116 baseline confabs; a row
killed only when flagged, unflagged rows contribute 0 on both sides.

Descriptive (section 8, gate-free): flavor breakdown of kills/leaks,
wrong->refusal conversions, correct->wrong flips, dose ladder {g=+1,+3}, the
bidirectional over-refusal-repair arm (de-refusal rate + post-de-refusal
correctness on the 114 answerable-refused rows), per-row exhaust JSONL.

Outputs (UNTRACKED) under analysis/amendment_an_prep/amendment_an_run/:
  gates_report.json        AN-G1/G2/G3 + descriptive tables
  per_row_exhaust.jsonl    one row per row_key with baseline + per-arm grades

Usage:
  python amendment_an_grade_and_gates.py
"""

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

ARCHIVE_AMENDMENTS_DIR = Path(__file__).resolve().parent
if str(ARCHIVE_AMENDMENTS_DIR) not in sys.path:
    sys.path.insert(0, str(ARCHIVE_AMENDMENTS_DIR))

from path_compat import phase1_eval_dir, phase1_probe_dir, repo_root  # noqa: E402

PROBE_DIR = phase1_probe_dir()
EVAL_DIR = phase1_eval_dir()
for p in (str(PROBE_DIR), str(EVAL_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)

import scorers  # noqa: E402
from amendment_al_grade_and_gates import grade_row  # noqa: E402

CANONICAL = repo_root()
AL_PREP = CANONICAL / "experiment/phase1/probe/analysis/amendment_al_prep"
AN_PREP = CANONICAL / "experiment/phase1/probe/analysis/amendment_an_prep"
RUN_DIR = AN_PREP / "amendment_an_run"
STAGE0 = CANONICAL / "experiment/phase1/probe/analysis/ah_stage0"
CAND_FILES = [STAGE0 / "candidates.jsonl",
              STAGE0 / "expansion/expansion_candidates.jsonl"]
N_BOOT = 1000
BOOT_SEED = 20260705

G1_MAX = 2   # section 4.3 AN-G1
G2_MIN = 5   # section 4.3 AN-G2
G3_MIN = 5   # section 4.3 AN-G3


def load_jsonl(p: Path):
    return [json.loads(ln) for ln in Path(p).open(encoding="utf-8") if ln.strip()]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--arms", default="primary,control")
    ap.add_argument("--dose-tags", default="primary_gain_p1,primary_gain_p3")
    ap.add_argument("--bidirectional-tag", default="bidirectional")
    args = ap.parse_args()

    cand = {}
    for f in CAND_FILES:
        for r in load_jsonl(f):
            cand[r["row_key"]] = {"question": r["question"],
                                  "aliases": r.get("aliases", [])}
    pool = {r["row_key"]: r for r in load_jsonl(AL_PREP / "permuted_a0/pool.jsonl")}

    base = {r["row_key"]: r for r in
            load_jsonl(AL_PREP / "true_a0/gen/data/rows_graded.jsonl")}
    row_order = list(base.keys())
    manifest = json.loads((RUN_DIR / "an_selection_manifest.json").read_text())

    base_confab_keys = [k for k in row_order if base[k]["confab_on_unanswerable"]]
    base_correct_keys = [k for k in row_order
                         if base[k]["gold_class"] == "answerable"
                         and base[k]["answered"] and base[k]["correct"] is True]
    base_wrong_keys = [k for k in row_order
                       if base[k]["gold_class"] == "answerable"
                       and base[k]["answered"] and base[k]["correct"] is False]
    base_ansref_keys = [k for k in row_order
                        if base[k]["gold_class"] == "answerable"
                        and base[k]["refused"]]
    print(f"[grade] baseline: {len(base_confab_keys)} confab, "
          f"{len(base_correct_keys)} correct, {len(base_wrong_keys)} wrong, "
          f"{len(base_ansref_keys)} answerable-refused", flush=True)

    def flagged_set(arm):
        return set(manifest["arms"][arm]["flagged_keys"])

    def grade_arm(tag):
        rows_path = RUN_DIR / tag / "gen/data/rows.jsonl"
        if not rows_path.exists():
            return None
        graded = {}
        for r in load_jsonl(rows_path):
            k = r["row_key"]
            correct, confab = grade_row(r, pool[k], cand[k])
            graded[k] = {**r, "correct": correct, "confab_on_unanswerable": confab}
        return graded

    arms = [a.strip() for a in args.arms.split(",") if a.strip()]
    graded = {a: grade_arm(a) for a in arms}
    graded = {a: g for a, g in graded.items() if g is not None}

    report = {"baseline": {"n_confab": len(base_confab_keys),
                           "n_correct": len(base_correct_keys),
                           "n_wrong": len(base_wrong_keys),
                           "n_answerable_refused": len(base_ansref_keys)},
              "operating_point": {"threshold": manifest["threshold"],
                                  "primary_gain": manifest["primary_gain"]},
              "arms": {}}

    def kills(arm):
        g = graded[arm]
        fs = flagged_set(arm)
        return [k for k in base_confab_keys
                if k in fs and k in g and not g[k]["confab_on_unanswerable"]]

    def kill_indicator_over_universe(arm):
        g = graded[arm]
        fs = flagged_set(arm)
        ind = np.zeros(len(base_confab_keys), dtype=int)
        for i, k in enumerate(base_confab_keys):
            if k in fs and k in g and not g[k]["confab_on_unanswerable"]:
                ind[i] = 1
        return ind

    for arm in graded:
        g = graded[arm]
        fs = flagged_set(arm)
        killed = kills(arm)
        # collateral: FLAGGED baseline-correct row that flipped to refusal
        collateral = [k for k in base_correct_keys
                      if k in fs and k in g and g[k]["refused"]]
        corr_to_wrong = [k for k in base_correct_keys
                         if k in fs and k in g and g[k]["answered"]
                         and g[k]["correct"] is False]
        wrong_conv = [k for k in base_wrong_keys
                      if k in fs and k in g and g[k]["refused"]]
        confab_to_confab = [k for k in base_confab_keys
                            if k in fs and k in g and g[k]["confab_on_unanswerable"]]
        report["arms"][arm] = {
            "n_flagged": len(fs),
            "n_flagged_baseline_confab": sum(1 for k in base_confab_keys if k in fs),
            "n_flagged_baseline_correct": sum(1 for k in base_correct_keys if k in fs),
            "confabs_killed": len(killed),
            "collateral_correct_to_refusal": len(collateral),
            "correct_to_wrong": len(corr_to_wrong),
            "wrong_to_refusal": len(wrong_conv),
            "confab_to_different_confab": len(confab_to_confab),
            "killed_keys": killed,
            "collateral_keys": collateral,
        }
        print(f"[{arm}] killed={len(killed)} collateral={len(collateral)} "
              f"corr->wrong={len(corr_to_wrong)} wrong->refuse={len(wrong_conv)} "
              f"confab->confab={len(confab_to_confab)}", flush=True)

    # ---- GATES (primary) ----
    prim = report["arms"]["primary"]
    ctrl = report["arms"]["control"]
    g1_collateral = prim["collateral_correct_to_refusal"]
    g2_kills = prim["confabs_killed"]
    g3_diff = prim["confabs_killed"] - ctrl["confabs_killed"]

    prim_ind = kill_indicator_over_universe("primary")
    ctrl_ind = kill_indicator_over_universe("control")
    diff_per_row = prim_ind - ctrl_ind
    rng = np.random.default_rng(BOOT_SEED)
    n = len(diff_per_row)
    boots = np.empty(N_BOOT)
    for b in range(N_BOOT):
        idx = rng.integers(0, n, size=n)
        boots[b] = diff_per_row[idx].sum()
    ci_lo = float(np.quantile(boots, 0.025))
    ci_hi = float(np.quantile(boots, 0.975))

    gates = {
        "AN_G1_collateral": {
            "value": g1_collateral, "threshold": f"<= {G1_MAX}",
            "pass": bool(g1_collateral <= G1_MAX)},
        "AN_G2_reach": {
            "value": g2_kills, "threshold": f">= {G2_MIN}",
            "pass": bool(g2_kills >= G2_MIN)},
        "AN_G3_specificity": {
            "primary_kills": prim["confabs_killed"],
            "control_kills": ctrl["confabs_killed"],
            "diff": g3_diff,
            "threshold": f"diff >= {G3_MIN} AND bootstrap CI excludes 0",
            "bootstrap_ci_95": [round(ci_lo, 2), round(ci_hi, 2)],
            "bootstrap_mean": round(float(boots.mean()), 2),
            "pass": bool(g3_diff >= G3_MIN and ci_lo > 0)},
    }
    gates["overall_pass"] = bool(gates["AN_G1_collateral"]["pass"]
                                 and gates["AN_G2_reach"]["pass"]
                                 and gates["AN_G3_specificity"]["pass"])
    report["gates"] = gates
    print(f"\n[GATES] AN-G1 collateral={g1_collateral} (<={G1_MAX}) "
          f"pass={gates['AN_G1_collateral']['pass']}")
    print(f"[GATES] AN-G2 kills={g2_kills} (>={G2_MIN}) "
          f"pass={gates['AN_G2_reach']['pass']}")
    print(f"[GATES] AN-G3 diff={g3_diff} (>={G3_MIN}) CI=[{ci_lo:.2f},{ci_hi:.2f}] "
          f"pass={gates['AN_G3_specificity']['pass']}")
    print(f"[GATES] OVERALL pass={gates['overall_pass']}")

    # ---- flavor breakdown of kills (primary) ----
    def flavor(k):
        return base[k].get("category_canon") or "(none)"
    prim_killed = set(report["arms"]["primary"]["killed_keys"])
    prim_flagged_confab = [k for k in base_confab_keys if k in flagged_set("primary")]
    flav = defaultdict(lambda: {"flagged": 0, "killed": 0})
    for k in prim_flagged_confab:
        fl = flavor(k)
        flav[fl]["flagged"] += 1
        if k in prim_killed:
            flav[fl]["killed"] += 1
    report["primary_flavor_breakdown"] = {k: dict(v) for k, v in flav.items()}

    # ---- dose ladder (descriptive; flagged confabs only) ----
    dose_tags = [t.strip() for t in args.dose_tags.split(",") if t.strip()]
    dose_report = {}
    prim_flagged = flagged_set("primary")
    prim_flagged_confab_keys = [k for k in base_confab_keys if k in prim_flagged]
    for tag in dose_tags:
        g = grade_arm(tag)
        if g is None:
            continue
        killed = [k for k in prim_flagged_confab_keys
                  if k in g and not g[k]["confab_on_unanswerable"]]
        dose_report[tag] = {"n_rows": len(g), "confabs_killed": len(killed)}
        print(f"[dose {tag}] killed={len(killed)}", flush=True)
    dose_report["primary_gain_p2"] = {
        "confabs_killed": len([k for k in prim_flagged_confab_keys
                               if k in prim_killed])}
    report["dose_ladder"] = dose_report

    # ---- bidirectional (over-refusal repair; descriptive) ----
    bid = grade_arm(args.bidirectional_tag)
    if bid is not None:
        de_refused = [k for k in base_ansref_keys
                      if k in bid and bid[k]["answered"]]
        de_refused_correct = [k for k in de_refused
                              if bid[k]["correct"] is True]
        report["bidirectional"] = {
            "n_answerable_refused": len(base_ansref_keys),
            "n_de_refused": len(de_refused),
            "de_refusal_rate": round(len(de_refused) / max(len(base_ansref_keys), 1), 4),
            "n_de_refused_correct": len(de_refused_correct),
            "post_de_refusal_correctness": round(
                len(de_refused_correct) / max(len(de_refused), 1), 4),
        }
        print(f"[bidirectional] de-refused={len(de_refused)}/{len(base_ansref_keys)} "
              f"correct={len(de_refused_correct)}", flush=True)

    # ---- per-row exhaust ----
    exhaust_path = RUN_DIR / "per_row_exhaust.jsonl"
    src = {r["row_key"]: r for r in
           load_jsonl(AL_PREP / "amendment_al_run/per_row_exhaust.jsonl")}
    flag_sets = {a: flagged_set(a) for a in graded}
    with exhaust_path.open("w", encoding="utf-8") as fh:
        for k in row_order:
            s = src.get(k, {})
            rec = {
                "row_key": k,
                "gold_class": base[k]["gold_class"],
                "category_canon": base[k].get("category_canon"),
                "prop_z": s.get("prop_z"),
                "caution_z": s.get("caution_z"),
                "baseline": {"answered": base[k]["answered"],
                             "refused": base[k]["refused"],
                             "correct": base[k]["correct"],
                             "confab": base[k]["confab_on_unanswerable"]},
            }
            for arm in graded:
                g = graded[arm]
                rec[arm] = ({
                    "flagged": k in flag_sets[arm],
                    "gain": g[k].get("gain") if k in g else None,
                    "answered": g[k]["answered"] if k in g else None,
                    "refused": g[k]["refused"] if k in g else None,
                    "correct": g[k]["correct"] if k in g else None,
                    "confab": g[k]["confab_on_unanswerable"] if k in g else None,
                } if k in g else {"generated": False})
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")

    (RUN_DIR / "gates_report.json").write_text(json.dumps(report, indent=2))
    print(f"\n[grade] gates report -> {RUN_DIR / 'gates_report.json'}")
    print(f"[grade] exhaust -> {exhaust_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
