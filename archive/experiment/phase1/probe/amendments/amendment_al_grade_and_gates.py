#!/usr/bin/env python3
"""Amendment AL step 4/5: grade steered arms, score gates G1/G2/G3, exhaust.

CPU-only. Grades every steered arm's generations with the SAME byte-pinned
grader as the AL-prep A0 baseline (amendment_al_prep_grade_a0_generations.py):
Cheng scorers.is_correct on gold-answerable rows carrying aliases;
confab_on_unanswerable = answered a gold-unanswerable question. Joins question +
aliases from the AH candidate files and gold_class/category from the pool, so
the steered rows (which carry only row_key/behavior flags) grade identically to
the baseline.

GATES (amendment section 4, LOCKED; primary arm only unless noted):
  G1 (collateral): at most 3 of the 90 baseline-correct rows flip to refusal in
     the primary arm. Correct->wrong flips tracked descriptively, do not gate.
  G2 (reach): at least 5 of the 116 baseline confabs killed in the primary arm.
     killed = the baseline confab no longer produces a graded confabulation
     (refusal or hedge count; a confab that becomes a DIFFERENT confab does not
     -- i.e. killed iff baseline confab AND steered NOT confab_on_unanswerable).
  G3 (specificity): primary kills minus control kills >= 5, with a 1000-resample
     row bootstrap CI on (primary_kill_indicator - control_kill_indicator over
     the shared baseline-confab rows) excluding zero.

Kills are computed ONLY over the arm's PUSHED baseline confabs (the causal
contrast); the control's kills are over ITS pushed baseline confabs. For G3 the
bootstrap resamples the 116 baseline-confab rows and, per row, compares whether
it was killed under primary vs under control (a row killed only when pushed;
unpushed rows contribute 0 on both sides), so the statistic is
primary_kills - control_kills over the same 116-row universe.

Descriptive instrumentation (section 6): flavor breakdown of kills/leaks,
wrong->refusal conversions, correct->wrong flips, secondary-arm full table,
per-row provenance exhaust JSONL.

Outputs (UNTRACKED) under analysis/amendment_al_prep/amendment_al_run/:
  gates_report.json        G1/G2/G3 + descriptive tables
  per_row_exhaust.jsonl    one row per (row_key) with baseline + per-arm grades

Usage:
  python amendment_al_grade_and_gates.py
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

CANONICAL = repo_root()
AL_PREP = CANONICAL / "experiment/phase1/probe/analysis/amendment_al_prep"
RUN_DIR = AL_PREP / "amendment_al_run"
STAGE0 = CANONICAL / "experiment/phase1/probe/analysis/ah_stage0"
CAND_FILES = [STAGE0 / "candidates.jsonl",
              STAGE0 / "expansion/expansion_candidates.jsonl"]
N_BOOT = 1000
BOOT_SEED = 20260705


def load_jsonl(p: Path):
    return [json.loads(ln) for ln in Path(p).open(encoding="utf-8") if ln.strip()]


def grade_row(r, pool_r, cand_r):
    """Return (correct, confab) using the byte-pinned baseline grader logic."""
    is_answerable = (pool_r["gold_class"] == "answerable")
    aliases = cand_r["aliases"]
    correct = None
    if is_answerable and aliases and r["answered"]:
        correct = bool(scorers.is_correct(r["answer_text"], aliases))
    confab = bool(r["answered"] and not is_answerable)
    return correct, confab


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--arms", default="primary,control,secondary")
    ap.add_argument("--dose-tags", default="primary_dose0p5,primary_dose2p0")
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
    manifest = json.loads((RUN_DIR / "selection_manifest.json").read_text())

    # baseline populations
    base_confab_keys = [k for k in row_order if base[k]["confab_on_unanswerable"]]
    base_correct_keys = [k for k in row_order
                         if base[k]["gold_class"] == "answerable"
                         and base[k]["answered"] and base[k]["correct"] is True]
    base_wrong_keys = [k for k in row_order
                       if base[k]["gold_class"] == "answerable"
                       and base[k]["answered"] and base[k]["correct"] is False]
    print(f"[grade] baseline: {len(base_confab_keys)} confab, "
          f"{len(base_correct_keys)} correct, {len(base_wrong_keys)} wrong",
          flush=True)

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

    def pushed_set(arm):
        return set(manifest["arms"][arm]["row_keys"])

    def kills(arm):
        """baseline confab rows (pushed by this arm) that are no longer confab."""
        g = graded[arm]
        ps = pushed_set(arm)
        killed = [k for k in base_confab_keys
                  if k in ps and k in g and not g[k]["confab_on_unanswerable"]]
        return killed

    def kill_indicator_over_universe(arm):
        """Per baseline-confab row: 1 if killed under this arm, else 0. A row not
        pushed by the arm is 0 (steering could only act on pushed rows)."""
        g = graded[arm]
        ps = pushed_set(arm)
        ind = np.zeros(len(base_confab_keys), dtype=int)
        for i, k in enumerate(base_confab_keys):
            if k in ps and k in g and not g[k]["confab_on_unanswerable"]:
                ind[i] = 1
        return ind

    report = {"baseline": {"n_confab": len(base_confab_keys),
                           "n_correct": len(base_correct_keys),
                           "n_wrong": len(base_wrong_keys)},
              "arms": {}}

    # ---- per-arm kill / collateral tables ----
    for arm in graded:
        g = graded[arm]
        ps = pushed_set(arm)
        killed = kills(arm)
        # collateral: baseline-correct row (pushed) that flipped to refusal
        collateral = [k for k in base_correct_keys
                      if k in ps and k in g and g[k]["refused"]]
        # correct -> wrong (descriptive): pushed correct row still answered but wrong
        corr_to_wrong = [k for k in base_correct_keys
                         if k in ps and k in g and g[k]["answered"]
                         and g[k]["correct"] is False]
        # wrong -> refusal (benefit)
        wrong_conv = [k for k in base_wrong_keys
                      if k in ps and k in g and g[k]["refused"]]
        # confab -> different confab (NOT a kill)
        confab_to_confab = [k for k in base_confab_keys
                            if k in ps and k in g and g[k]["confab_on_unanswerable"]]
        report["arms"][arm] = {
            "n_pushed": len(ps),
            "n_pushed_baseline_confab": sum(1 for k in base_confab_keys if k in ps),
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
        "G1_collateral": {
            "value": g1_collateral, "threshold": "<= 3",
            "pass": bool(g1_collateral <= 3)},
        "G2_reach": {
            "value": g2_kills, "threshold": ">= 5",
            "pass": bool(g2_kills >= 5)},
        "G3_specificity": {
            "primary_kills": prim["confabs_killed"],
            "control_kills": ctrl["confabs_killed"],
            "diff": g3_diff, "threshold": "diff >= 5 AND bootstrap CI excludes 0",
            "bootstrap_ci_95": [round(ci_lo, 2), round(ci_hi, 2)],
            "bootstrap_mean": round(float(boots.mean()), 2),
            "pass": bool(g3_diff >= 5 and ci_lo > 0)},
    }
    gates["overall_pass"] = bool(gates["G1_collateral"]["pass"]
                                 and gates["G2_reach"]["pass"]
                                 and gates["G3_specificity"]["pass"])
    report["gates"] = gates
    print(f"\n[GATES] G1 collateral={g1_collateral} (<=3) pass={gates['G1_collateral']['pass']}")
    print(f"[GATES] G2 kills={g2_kills} (>=5) pass={gates['G2_reach']['pass']}")
    print(f"[GATES] G3 diff={g3_diff} (>=5) CI=[{ci_lo:.2f},{ci_hi:.2f}] "
          f"pass={gates['G3_specificity']['pass']}")
    print(f"[GATES] OVERALL pass={gates['overall_pass']}")

    # ---- flavor breakdown of kills / leaks (primary) ----
    def flavor(k):
        return base[k].get("category_canon") or "(none)"
    prim_killed = set(report["arms"]["primary"]["killed_keys"])
    prim_pushed_confab = [k for k in base_confab_keys if k in pushed_set("primary")]
    flav = defaultdict(lambda: {"pushed": 0, "killed": 0})
    for k in prim_pushed_confab:
        fl = flavor(k)
        flav[fl]["pushed"] += 1
        if k in prim_killed:
            flav[fl]["killed"] += 1
    report["primary_flavor_breakdown"] = {k: dict(v) for k, v in flav.items()}

    # ---- dose ladder (descriptive) ----
    dose_tags = [t.strip() for t in args.dose_tags.split(",") if t.strip()]
    dose_report = {}
    prim_pushed = pushed_set("primary")
    prim_pushed_confab_keys = [k for k in base_confab_keys if k in prim_pushed]
    prim_pushed_correct_keys = [k for k in base_correct_keys if k in prim_pushed]
    for tag in dose_tags:
        g = grade_arm(tag)
        if g is None:
            continue
        killed = [k for k in prim_pushed_confab_keys
                  if k in g and not g[k]["confab_on_unanswerable"]]
        coll = [k for k in prim_pushed_correct_keys
                if k in g and g[k]["refused"]]
        dose_report[tag] = {"n_rows": len(g), "confabs_killed": len(killed),
                            "collateral": len(coll)}
        print(f"[dose {tag}] killed={len(killed)} collateral={len(coll)}", flush=True)
    # dose 1.0 = primary arm kills over the same pushed-confab universe
    dose_report["primary_dose1p0"] = {
        "confabs_killed": len([k for k in prim_pushed_confab_keys
                               if k in prim_killed]),
        "collateral": g1_collateral}
    report["dose_ladder"] = dose_report

    # ---- per-row exhaust ----
    exhaust_path = RUN_DIR / "per_row_exhaust.jsonl"
    prop_z = np.load(RUN_DIR / "prop_z.npy")
    caution_z = np.load(RUN_DIR / "caution_z.npy")
    key_to_i = {k: i for i, k in enumerate(row_order)}
    push_flags = {a: pushed_set(a) for a in graded}
    with exhaust_path.open("w", encoding="utf-8") as fh:
        for k in row_order:
            i = key_to_i[k]
            rec = {
                "row_key": k,
                "gold_class": base[k]["gold_class"],
                "category_canon": base[k].get("category_canon"),
                "prop_z": round(float(prop_z[i]), 4),
                "caution_z": round(float(caution_z[i]), 4),
                "baseline": {"answered": base[k]["answered"],
                             "refused": base[k]["refused"],
                             "correct": base[k]["correct"],
                             "confab": base[k]["confab_on_unanswerable"]},
            }
            for arm in graded:
                g = graded[arm]
                rec[arm] = {
                    "pushed": k in push_flags[arm],
                    "answered": g[k]["answered"] if k in g else None,
                    "refused": g[k]["refused"] if k in g else None,
                    "correct": g[k]["correct"] if k in g else None,
                    "confab": g[k]["confab_on_unanswerable"] if k in g else None,
                } if k in g else {"generated": False}
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")

    (RUN_DIR / "gates_report.json").write_text(json.dumps(report, indent=2))
    print(f"\n[grade] gates report -> {RUN_DIR / 'gates_report.json'}")
    print(f"[grade] exhaust -> {exhaust_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
