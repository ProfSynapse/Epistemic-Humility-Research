#!/usr/bin/env python3
"""Amendment AH Addendum A1 (script 3/3) — A1-G1 scoring + quintile table (CPU).

Locked spec §10.2:
  Eligibility = baseline-answered at A0 (main-run rule). Sanity floor >= 40.
  A1-G1: induced refusal (A0-answered -> A-doubt-refused) >= +20pt among
         eligible rows -> PASS certifies the instrument on a fair population.
  Secondary (non-gating): induced refusal per caution quintile.

Induced refusal is measured on the SAME eligible rows in both arms (paired by
row_key): among rows answered at A0, the fraction that flip to refused under
A-doubt. This is the +Npt figure the +20pt floor is stated against, identical to
the main-run AH-G1 definition.

Writes analysis/ah_addendum_a1/gates_result.json and a committed result copy
under experiments/divergent-pool-own-readout/artifacts/.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

PROBE_DIR = Path(__file__).resolve().parent
CANONICAL = Path("/home/profsynapse/code/Epistemic-Humility-Research")
DEFAULT_DIR = CANONICAL / "experiment/phase1/probe/analysis/ah_addendum_a1"
RESULT_COPY = CANONICAL / "experiments/divergent-pool-own-readout/artifacts/amendment_ah_addendum_a1_result.json"

G1_FLOOR_PT = 20.0
G0_FLOOR_N = 40
N_BOOT = 10000
BOOT_SEED = 20260703


def load_jsonl(p: Path):
    return [json.loads(l) for l in p.open() if l.strip()]


def bootstrap_pt_ci(flips, n_boot=N_BOOT, seed=BOOT_SEED):
    """CI on the induced-refusal percentage over the paired eligible rows.
    flips: 0/1 array (1 = A0-answered row flipped to refused under A-doubt)."""
    if len(flips) == 0:
        return None, None
    rng = np.random.default_rng(seed)
    flips = np.asarray(flips, dtype=float)
    n = len(flips)
    stats = np.empty(n_boot)
    for b in range(n_boot):
        idx = rng.integers(0, n, n)
        stats[b] = flips[idx].mean() * 100.0
    return float(np.percentile(stats, 2.5)), float(np.percentile(stats, 97.5))


def run(args) -> int:
    d = Path(args.dir).resolve()
    a0 = {r["row_key"]: r for r in load_jsonl(d / "gen_A0" / "rows.jsonl")}
    ad = {r["row_key"]: r for r in load_jsonl(d / "gen_Adoubt" / "rows.jsonl")}
    manifest = json.loads((d / "manifest.json").read_text())
    strat_manifest = json.loads((d / "stratum_manifest.json").read_text())

    keys = [k for k in a0 if k in ad]
    n_pool = len(keys)

    # Eligibility = A0-answered.
    eligible = [k for k in keys if a0[k].get("answered")]
    n_elig = len(eligible)
    g0_pass = n_elig >= G0_FLOOR_N

    # Induced refusal among eligible: A0-answered -> A-doubt-refused.
    flips = np.array([1 if ad[k].get("refused") else 0 for k in eligible],
                     dtype=int)
    n_flip = int(flips.sum())
    induced_pt = (100.0 * n_flip / n_elig) if n_elig else 0.0
    lo, hi = bootstrap_pt_ci(flips)
    g1_pass = bool(induced_pt >= G1_FLOOR_PT) if g0_pass else False

    # A0 refusal baseline on the eligible set is 0 by construction (all answered);
    # report the whole-stratum A0 refusal rate for context.
    a0_refused_all = sum(1 for k in keys if a0[k].get("refused"))
    a0_answered_all = sum(1 for k in keys if a0[k].get("answered"))

    # --- secondary: induced refusal per caution quintile (non-gating) ---
    by_q = defaultdict(lambda: {"eligible": 0, "flipped": 0,
                                "caution_z": [], "n_pool": 0})
    for k in keys:
        q = a0[k].get("quintile") or ad[k].get("quintile")
        by_q[q]["n_pool"] += 1
    for k in eligible:
        q = a0[k].get("quintile")
        by_q[q]["eligible"] += 1
        by_q[q]["caution_z"].append(a0[k].get("caution_dist_z"))
        if ad[k].get("refused"):
            by_q[q]["flipped"] += 1
    quintile_table = {}
    for q in sorted(by_q):
        c = by_q[q]
        quintile_table[f"Q{q}"] = {
            "n_pool": c["n_pool"], "eligible": c["eligible"],
            "flipped": c["flipped"],
            "induced_refusal_pt": (round(100.0 * c["flipped"] / c["eligible"], 2)
                                   if c["eligible"] else None),
            "mean_caution_z": (round(float(np.mean(c["caution_z"])), 3)
                               if c["caution_z"] else None),
        }

    # per-source induced refusal (descriptive)
    by_src = defaultdict(lambda: {"eligible": 0, "flipped": 0})
    for k in eligible:
        s = a0[k].get("source_group") or a0[k].get("source", "")
        by_src[s]["eligible"] += 1
        if ad[k].get("refused"):
            by_src[s]["flipped"] += 1
    source_table = {
        s: {"eligible": v["eligible"], "flipped": v["flipped"],
            "induced_refusal_pt": (round(100.0 * v["flipped"] / v["eligible"], 2)
                                   if v["eligible"] else None)}
        for s, v in sorted(by_src.items())
    }

    verdict = ("A1-G1 PASS -> AH upgrades to H-COMPLIANCE (scoreboard TIE/TIE -> "
               "WIN/WIN); original three-tier rule applies to the already-"
               "collected G2 precise null with a live release-direction "
               "instrument." if g1_pass else
               "A1-G1 FAIL -> AH stays AMBIGUOUS permanently (no second "
               "recalibration); descriptive finding = doubt-prime muzzle "
               "authority on this pool is genuinely weaker than AG's TriviaQA-era "
               "+34pt calibration. No goalpost moved.")
    if not g0_pass:
        verdict = (f"A1-G0 FAIL: only {n_elig} eligible (< {G0_FLOOR_N}) -> gate "
                   "uninterpretable; A1-G1 not scored.")

    result = {
        "amendment": "AH", "stage": "addendum_a1_score",
        "spec": "AMENDMENT-AH-divergent-pool-own-readout.md §10.2",
        "n_stratum_rows": n_pool,
        "config_sha": {
            "A0": manifest["arms"]["A0"]["config_sha"],
            "A-doubt": manifest["arms"]["A-doubt"]["config_sha"],
        },
        "stratum_mean_caution_z": strat_manifest.get("selected_mean_caution_z"),
        "orig_pos_control_mean_caution_z":
            strat_manifest.get("orig_pos_control_mean_caution_z"),
        "a0_census": {"answered": a0_answered_all, "refused": a0_refused_all,
                      "total": n_pool},
        "A1_G0_eligibility": {
            "eligible_A0_answered": n_elig, "floor": G0_FLOOR_N,
            "pass": g0_pass,
        },
        "A1_G1": {
            "definition": "induced refusal (A0-answered -> A-doubt-refused) "
                          "among eligible",
            "n_eligible": n_elig, "n_flipped_to_refused": n_flip,
            "induced_refusal_pt": round(induced_pt, 2),
            "bootstrap_ci_pt": ([round(lo, 2), round(hi, 2)]
                                if lo is not None else None),
            "floor_pt": G1_FLOOR_PT, "pass": g1_pass,
            "main_run_g1_pt": 15.65, "main_run_g1_pass": False,
        },
        "quintile_table": quintile_table,
        "source_table": source_table,
        "verdict": verdict,
    }

    (d / "gates_result.json").write_text(json.dumps(result, indent=2),
                                        encoding="utf-8")
    RESULT_COPY.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2), flush=True)
    print(f"[a1/score] DONE -> {d/'gates_result.json'} + {RESULT_COPY}",
          flush=True)
    return 0


def parse_args(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dir", default=str(DEFAULT_DIR))
    return ap.parse_args(argv)


if __name__ == "__main__":
    sys.exit(run(parse_args()))
