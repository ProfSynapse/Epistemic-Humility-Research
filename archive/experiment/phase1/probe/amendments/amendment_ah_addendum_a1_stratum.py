#!/usr/bin/env python3
"""Amendment AH Addendum A1 (script 1/3) — caution-representative stratum (CPU).

Locked spec: AMENDMENT-AH-divergent-pool-own-readout.md §10.1 (SIGNED 2026-07-03,
user "Do the addendum"). Fixes the §9.2(1) population-calibration flaw: the
original positive control was drawn from the LOW-caution end (mean
caution_dist_z -1.31), understating the doubt prime's muzzle authority relative
to AG's unfiltered +34pt calibration.

Stratum (150 rows): concordant-known rows = consensus(L20/L24/L28) all > 0 at
band 0 AND gold-answerable (the §3.3 readout rule verbatim), quantile-stratified
on caution_dist_z into 5 quintiles of the FULL concordant-known population's
caution distribution, 30 rows per quintile, balanced across the four answerable
sources (TriviaQA/SelfAware/KUQ/PopQA) as available within each quintile,
seed 0, EXCLUDING the 150 original positive-control rows.

Reuses build_union() (identical caution/doubt reconstruction as the main pool).
Writes analysis/ah_addendum_a1/:
  stratum.jsonl        per-row {safe_key, row_key, pass, pregen_dir, source,
                       source_group, quintile, gold_class, label, scores,
                       caution_dist, caution_dist_z}
  stratum_manifest.json  population census, quintile edges, per-quintile x source
                       counts, exclusion count, seed.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

PROBE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(PROBE_DIR))
from path_compat import repo_root  # noqa: E402
from amendment_ah_stage0_expand_pool import build_union  # noqa: E402

CANONICAL = repo_root()
STAGE0 = CANONICAL / "experiment/phase1/probe/analysis/ah_stage0"
POOL_V21 = STAGE0 / "expansion" / "pool_v21.jsonl"
DEFAULT_OUT = CANONICAL / "experiment/phase1/probe/analysis/ah_addendum_a1"

N_TARGET = 150
N_QUINTILES = 5
PER_QUINTILE = N_TARGET // N_QUINTILES  # 30
SOURCES = ["triviaqa", "selfaware", "kuq", "popqa"]
SEED = 0


def source_group(src: str) -> str:
    if src.startswith("selfaware"):
        return "selfaware"
    if src.startswith("kuq"):
        return "kuq"
    if src == "triviaqa":
        return "triviaqa"
    if src == "popqa":
        return "popqa"
    return "other"


def load_original_pos_control() -> set:
    keys = set()
    for ln in POOL_V21.read_text(encoding="utf-8").splitlines():
        ln = ln.strip()
        if not ln:
            continue
        r = json.loads(ln)
        if r.get("stratum") == "positive_control":
            keys.add(r["safe_key"])
    return keys


def balanced_pick(idx_pool, n_want):
    """Round-robin across the four sources within a quintile until n_want picked.
    idx_pool: dict source_group -> list of union indices (already shuffled)."""
    picked = []
    cursors = {s: 0 for s in SOURCES}
    # round-robin one at a time so under-supplied sources don't starve the rest
    while len(picked) < n_want:
        progressed = False
        for s in SOURCES:
            if len(picked) >= n_want:
                break
            lst = idx_pool.get(s, [])
            c = cursors[s]
            if c < len(lst):
                picked.append(lst[c])
                cursors[s] = c + 1
                progressed = True
        if not progressed:
            break  # every source exhausted (shouldn't happen given census)
    return picked


def run(args) -> int:
    rng = np.random.default_rng(SEED)
    out_dir = Path(args.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    union, base_sd, cv_auroc, sign = build_union()
    L20 = np.array([r["score_L20"] for r in union])
    L24 = np.array([r["score_L24"] for r in union])
    L28 = np.array([r["score_L28"] for r in union])
    gold_known = np.array([1 if r["label"] == "known" else 0 for r in union])
    cz = np.array([r["caution_dist_z"] for r in union])

    # concordant-known = consensus(L20/L24/L28)>0 at band 0, gold-answerable (§3.3)
    ck_mask = (L20 > 0) & (L24 > 0) & (L28 > 0) & (gold_known == 1)
    ck_idx_all = np.where(ck_mask)[0]

    # quintile edges from the FULL concordant-known caution_dist_z distribution
    edges = np.quantile(cz[ck_idx_all], np.linspace(0, 1, N_QUINTILES + 1))

    pos_control_keys = load_original_pos_control()
    ck_idx = [int(i) for i in ck_idx_all
              if union[i]["safe_key"] not in pos_control_keys]
    n_excluded = len(ck_idx_all) - len(ck_idx)

    print(f"[a1/stratum] concordant-known population: {len(ck_idx_all)} "
          f"(excl orig pos-control: {len(ck_idx)}, removed {n_excluded})",
          flush=True)
    print(f"[a1/stratum] quintile edges (z): "
          f"{[round(float(x), 3) for x in edges]}", flush=True)

    # assign each eligible row to a quintile by its caution_dist_z
    def quintile_of(z):
        # interior edges edges[1..N-1]; clamp to [0, N-1]
        q = int(np.searchsorted(edges[1:N_QUINTILES], z, side="right"))
        return min(N_QUINTILES - 1, q)

    per_q_src = {q: defaultdict(list) for q in range(N_QUINTILES)}
    for i in ck_idx:
        q = quintile_of(union[i]["caution_dist_z"])
        per_q_src[q][source_group(union[i]["source"])].append(i)

    # shuffle within each quintile x source for reproducible sampling
    for q in range(N_QUINTILES):
        for s in SOURCES:
            lst = per_q_src[q].get(s, [])
            rng.shuffle(lst)
            per_q_src[q][s] = lst

    selected = []  # (union_idx, quintile)
    for q in range(N_QUINTILES):
        picks = balanced_pick(per_q_src[q], PER_QUINTILE)
        for idx in picks:
            selected.append((idx, q))
        if len(picks) < PER_QUINTILE:
            print(f"[a1/stratum] WARN quintile {q+1} short: "
                  f"{len(picks)}/{PER_QUINTILE}", flush=True)

    # write stratum rows
    rows_out = []
    seen = set()
    for idx, q in selected:
        r = union[idx]
        if r["safe_key"] in seen:
            continue
        seen.add(r["safe_key"])
        rows_out.append({
            "safe_key": r["safe_key"], "row_key": r["row_key"],
            "pass": r["pass"], "pregen_dir": r["pregen_dir"],
            "source": r["source"], "source_group": source_group(r["source"]),
            "quintile": int(q + 1),
            "gold_class": "answerable", "label": r["label"],
            "category_canon": r.get("category_canon", ""),
            "category_raw": r.get("category_raw", ""),
            "score_L20": round(r["score_L20"], 3),
            "score_L24": round(r["score_L24"], 3),
            "score_L28": round(r["score_L28"], 3),
            "caution_dist": round(r["caution_dist"], 3),
            "caution_dist_z": round(r["caution_dist_z"], 3),
            # main-run harness fields expected downstream
            "contrast": "addendum_a1_poscontrol",
            "congruent": True,
            "stratum": "addendum_a1_poscontrol",
        })

    with (out_dir / "stratum.jsonl").open("w", encoding="utf-8") as fh:
        for row in rows_out:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")

    # manifest
    per_q_counts = {}
    for q in range(N_QUINTILES):
        qrows = [r for r in rows_out if r["quintile"] == q + 1]
        per_q_counts[f"Q{q+1}"] = {
            "n": len(qrows),
            "sources": dict(Counter(r["source_group"] for r in qrows)),
            "caution_z_range": [round(float(edges[q]), 3),
                                round(float(edges[q + 1]), 3)],
            "mean_caution_z": (round(float(np.mean([r["caution_dist_z"]
                                                    for r in qrows])), 3)
                               if qrows else None),
        }

    manifest = {
        "amendment": "AH", "stage": "addendum_a1_stratum",
        "spec": "AMENDMENT-AH-divergent-pool-own-readout.md §10.1",
        "readout_rule": "consensus(L20&L24&L28)>0 band0 AND gold-answerable (§3.3 verbatim)",
        "caution_axis": {"cv_auroc": round(cv_auroc, 4),
                         "base_sd": round(base_sd, 3), "sign": sign},
        "concordant_known_population": int(len(ck_idx_all)),
        "concordant_known_excl_orig_pos_control": int(len(ck_idx)),
        "excluded_orig_pos_control": int(n_excluded),
        "quintile_edges_z": [round(float(x), 3) for x in edges],
        "n_target": N_TARGET, "per_quintile": PER_QUINTILE, "seed": SEED,
        "n_selected": len(rows_out),
        "selected_mean_caution_z": round(float(np.mean(
            [r["caution_dist_z"] for r in rows_out])), 3) if rows_out else None,
        "orig_pos_control_mean_caution_z": -1.31,  # from §9.2(1) / main run
        "source_split_total": dict(Counter(r["source_group"] for r in rows_out)),
        "per_quintile": per_q_counts,
        "stratum_file": str(out_dir / "stratum.jsonl"),
    }
    (out_dir / "stratum_manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2), flush=True)
    print(f"[a1/stratum] DONE {len(rows_out)} rows -> {out_dir/'stratum.jsonl'}",
          flush=True)
    return 0


def parse_args(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out-dir", default=str(DEFAULT_OUT))
    return ap.parse_args(argv)


if __name__ == "__main__":
    sys.exit(run(parse_args()))
