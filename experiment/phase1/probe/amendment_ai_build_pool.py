#!/usr/bin/env python3
"""Amendment AI — build the PAR training pool + verdict-eval holdout (CPU).

Implements prereg section 1.3 (AMENDMENT-AI-probe-as-reward.md) mechanically
from the refit artifacts (PR #178):

  divergent supply = mining sensor-D-over rows (refit L24 p<0.5 on
      gold-unanswerable candidates) EXCLUDING truthfulqa_misconception
      (quarantined pending construct audit) and the v1 local remnant sources
      (kuq_ku_unknown_mine, selfaware_unanswerable_mine — duplicates of the
      locked AH pool), PLUS union divergent rows (refit OOF p disagrees with
      gold), EXCLUDING every row_key in the locked AH eval pool (pool_v21)
      and the Addendum A1 stratum.
  categories: ambiguous (ambigqa_ambiguous), false_premise
      (falseqa_false_premise), unsolved_other (everything else).
  holdout: 400 divergent rows, category-stratified (proportional, largest
      remainder), seed 0, drawn BEFORE the cap.
  cap: no category may exceed 60% of training-divergent mass; oversized
      categories are down-sampled (seed 0). The cap binds on ambiguous.
  concordant supply = union concordant rows (same exclusions).
  mixture: 30.5% divergent per training batch (recorded for the trainer;
      the pool file carries split labels, the trainer does the sampling).

Outputs:
  analysis/amendment_ai/pool/ (gitignored — FalseQA question text lives here)
      train_divergent.jsonl, train_concordant.jsonl, holdout_eval.jsonl
      rows: row_key, source, category, question, gold_label, p_unanswerable
  experiments/probe-as-reward/artifacts/amendment_ai_pool_manifest.json (committed —
      counts, category masses, exclusions, config; row_keys only, NO text)
"""

from __future__ import annotations

import json
import random
import sys
from collections import Counter
from pathlib import Path

CANONICAL = Path("/home/profsynapse/code/Epistemic-Humility-Research")
PROBE_ROOT = CANONICAL / "experiment/phase1/probe"
REPO = Path(__file__).resolve().parents[3]
ARTIFACT_DIR = REPO / "experiments" / "probe-as-reward" / "artifacts"
REFIT = PROBE_ROOT / "analysis/par_sensor_refit"
AH_POOL = PROBE_ROOT / "analysis/ah_stage0/expansion/pool_v21.jsonl"
A1_STRATUM = PROBE_ROOT / "analysis/ah_addendum_a1/stratum.jsonl"
OUT_DIR = PROBE_ROOT / "analysis/amendment_ai/pool"
MANIFEST = ARTIFACT_DIR / "amendment_ai_pool_manifest.json"

import argparse

VARIANTS = {
    "v1": {"union_dir": "union_pregen", "mining_dir": "mining_pregen",
            "union_rows": "union_refit_rows_cleansft.jsonl",
            "mining_rows": "mining_refit_rows_cleansft.jsonl",
            "mixture": 0.305},
    "v2": {"union_dir": "union_pregen_4bit", "mining_dir": "mining_pregen_4bit",
            "union_rows": "union_refit_rows_cleansft4bit.jsonl",
            "union_inloop": "union_inloop_rows_cleansft4bit.jsonl",
            "mining_rows": "mining_refit_rows_cleansft4bit.jsonl",
            "mixture": 0.290},
}

SEED = 0
HOLDOUT_N = 400
CATEGORY_CAP = 0.60
EXCLUDE_MINING_SOURCES = {
    "truthfulqa_misconception",          # quarantined pending construct audit
    "kuq_ku_unknown_mine",               # v1 remnants: dupes of locked AH pool
    "selfaware_unanswerable_mine",
}


def load_jsonl(p: Path):
    return [json.loads(l) for l in p.open() if l.strip()]


def category_of(source: str) -> str:
    if source == "ambigqa_ambiguous":
        return "ambiguous"
    if source == "falseqa_false_premise":
        return "false_premise"
    return "unsolved_other"


def stratified_take(rows, n, seed):
    """Proportional category-stratified sample (largest remainder)."""
    rng = random.Random(seed)
    by_cat = {}
    for r in rows:
        by_cat.setdefault(r["category"], []).append(r)
    total = len(rows)
    quotas = {c: n * len(v) / total for c, v in by_cat.items()}
    base = {c: int(q) for c, q in quotas.items()}
    rem = n - sum(base.values())
    for c in sorted(quotas, key=lambda c: quotas[c] - base[c], reverse=True)[:rem]:
        base[c] += 1
    taken, kept = [], []
    for c, pool in by_cat.items():
        pool = sorted(pool, key=lambda r: r["row_key"])
        rng.shuffle(pool)
        k = min(base.get(c, 0), len(pool))
        taken.extend(pool[:k])
        kept.extend(pool[k:])
    return taken, kept


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--variant", choices=["v1", "v2"], default="v2")
    ap.add_argument("--union-classify", choices=["oof", "inloop"], default="oof",
                    help="inloop = classify union membership under the FULL-FIT "
                         "frozen probe (the sensor the reward reads, prereg "
                         "section 1.3); oof = v1/v2.0 behavior")
    ap.add_argument("--pin-holdout", action="store_true",
                    help="reuse holdout_row_keys from the existing manifest "
                         "(locked holdout); holdout_eval.jsonl is not rewritten")
    args = ap.parse_args()
    v = VARIANTS[args.variant]
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rng = random.Random(SEED)

    excluded_keys = {r["row_key"] for r in load_jsonl(AH_POOL)}
    excluded_keys |= {r["row_key"] for r in load_jsonl(A1_STRATUM)}

    pinned_holdout_keys = None
    if args.pin_holdout:
        prior = json.loads(MANIFEST.read_text())
        pinned_holdout_keys = set(prior["holdout_row_keys"])
        pinned_holdout_by_cat = prior["holdout_by_category"]
        excluded_keys = excluded_keys | pinned_holdout_keys

    union_text = {r["row_key"]: r for r in load_jsonl(REFIT / v["union_dir"] / "rows.jsonl")}
    mining_text = {r["row_key"]: r for r in load_jsonl(REFIT / v["mining_dir"] / "rows.jsonl")}
    if args.union_classify == "inloop":
        union_refit = load_jsonl(REFIT / v["union_inloop"])
    else:
        union_refit = load_jsonl(REFIT / v["union_rows"])
    mining_refit = load_jsonl(REFIT / v["mining_rows"])

    n_excluded_ah = 0
    n_excluded_pinned = 0
    divergent, concordant = [], []
    for r in union_refit:
        if pinned_holdout_keys is not None and r["row_key"] in pinned_holdout_keys:
            n_excluded_pinned += 1
            continue
        if r["row_key"] in excluded_keys:
            n_excluded_ah += 1
            continue
        gold_abstain = r["label"] == "unknown"
        probe_abstain = r["p_unanswerable"] > 0.5
        row = {
            "row_key": r["row_key"], "source": r["source"],
            "category": category_of(r["source"]),
            "question": union_text[r["row_key"]]["question"],
            "gold_label": r["label"],
            "p_unanswerable": round(r["p_unanswerable"], 6),
            "origin": "union",
        }
        (divergent if probe_abstain != gold_abstain else concordant).append(row)

    n_mining_excluded_src = 0
    for r in mining_refit:
        if r["source"] in EXCLUDE_MINING_SOURCES:
            n_mining_excluded_src += 1
            continue
        if pinned_holdout_keys is not None and r["row_key"] in pinned_holdout_keys:
            n_excluded_pinned += 1
            continue
        if r["row_key"] in excluded_keys:
            n_excluded_ah += 1
            continue
        if not r["sensor_dover"]:
            continue                     # concordant mining rows are not used
        divergent.append({
            "row_key": r["row_key"], "source": r["source"],
            "category": category_of(r["source"]),
            "question": mining_text[r["row_key"]]["question"],
            "gold_label": "unknown",
            "p_unanswerable": round(r["p_unanswerable"], 6),
            "origin": "mining",
        })

    # holdout BEFORE the cap (or pinned: locked keys already excluded above)
    if pinned_holdout_keys is not None:
        holdout, remaining = [], divergent
    else:
        holdout, remaining = stratified_take(divergent, HOLDOUT_N, SEED)

    # 60% category-mass cap on training divergent (down-sample oversized cats)
    cats = Counter(r["category"] for r in remaining)
    capped = list(remaining)
    # iterate: with 3 categories a single reduction pass can shift shares
    for _ in range(5):
        cats = Counter(r["category"] for r in capped)
        total = len(capped)
        over = {c: k for c, k in cats.items() if k / total > CATEGORY_CAP}
        if not over:
            break
        others = sum(k for c, k in cats.items() if c not in over)
        # cap the largest offender so it is exactly CATEGORY_CAP of the result
        c, k = max(over.items(), key=lambda kv: kv[1])
        target = int(CATEGORY_CAP / (1 - CATEGORY_CAP) * others)
        pool = sorted([r for r in capped if r["category"] == c],
                      key=lambda r: r["row_key"])
        rng.shuffle(pool)
        keep_set = {id(r) for r in pool[:target]}
        capped = [r for r in capped
                  if r["category"] != c or id(r) in keep_set]

    dropped_by_cap = len(remaining) - len(capped)
    final_cats = Counter(r["category"] for r in capped)

    def dump(name, rows):
        with (OUT_DIR / name).open("w") as fh:
            for r in sorted(rows, key=lambda r: r["row_key"]):
                fh.write(json.dumps(r, ensure_ascii=False) + "\n")

    dump("train_divergent.jsonl", capped)
    dump("train_concordant.jsonl", concordant)
    if pinned_holdout_keys is None:
        dump("holdout_eval.jsonl", holdout)

    manifest = {
        "amendment": "AI", "stage": "build_pool", "seed": SEED,
        "sensor_variant": args.variant,
        "union_classify": args.union_classify,
        "holdout_pinned": pinned_holdout_keys is not None,
        "mixture_divergent": v["mixture"], "category_cap": CATEGORY_CAP,
        "holdout_n": (len(pinned_holdout_keys) if pinned_holdout_keys is not None
                      else len(holdout)),
        "counts": {
            "train_divergent": len(capped),
            "train_concordant": len(concordant),
            "holdout_eval": (len(pinned_holdout_keys)
                             if pinned_holdout_keys is not None else len(holdout)),
            "dropped_by_category_cap": dropped_by_cap,
            "excluded_ah_pool_or_a1": n_excluded_ah,
            "excluded_pinned_holdout": n_excluded_pinned,
            "excluded_mining_sources": n_mining_excluded_src,
        },
        "train_divergent_by_category": dict(final_cats),
        "holdout_by_category": (pinned_holdout_by_cat
                                if pinned_holdout_keys is not None
                                else dict(Counter(r["category"] for r in holdout))),
        "train_divergent_by_origin": dict(Counter(r["origin"] for r in capped)),
        "exclusion_sources": sorted(EXCLUDE_MINING_SOURCES),
        "ah_pool_file": str(AH_POOL), "a1_stratum_file": str(A1_STRATUM),
        "note": "pool jsonl files are gitignored (FalseQA text is train-only, "
                "NO LICENSE); this manifest carries counts only",
        "holdout_row_keys": (sorted(pinned_holdout_keys)
                             if pinned_holdout_keys is not None
                             else sorted(r["row_key"] for r in holdout)),
    }
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({k: manifest[k] for k in
                      ("counts", "train_divergent_by_category",
                       "holdout_by_category", "train_divergent_by_origin")},
                     indent=2))
    print(f"[pool] wrote {OUT_DIR} and {MANIFEST}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
