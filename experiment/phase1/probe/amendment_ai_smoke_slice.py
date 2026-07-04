#!/usr/bin/env python3
"""Amendment AI smoke — build the ~64-prompt reward-plumbing slice (CPU).

Team-lead smoke order (Amendment AI condition 1). Assembles a mixed
concordant+divergent prompt slice under the REFIT L24 sensor for the
probe-in-loop GRPO micro-run. Membership is decided by the refit sensor's
p_unanswerable (analysis/par_sensor_refit/union_refit_rows.jsonl), the sensor the
reward actually reads:

  concordant : probe agrees with gold (known ∧ p<0.5, or unknown ∧ p>=0.5)
  D-over     : gold-answerable (known) but probe says unanswerable (p>=0.5)
  D-under    : gold-unanswerable (unknown) but probe says answerable (p<0.5)

Target composition (spec): ~40 concordant, ~24 divergent including BOTH D-over
and D-under. Seed 0, deterministic. The union surface carries NO FalseQA rows
(FalseQA lives only in the mining pool), so this slice is license-clean; still,
we assert it and refuse to emit any falseqa-sourced row.

Question text joined from the union pre-gen rows (analysis/par_sensor_refit/
union_pregen/rows.jsonl); gold label from the refit rows; aliases (for the
correctness bonus) from the AH scored rows keyed by row_key. p_unanswerable is
carried through so the micro-run can cross-check its in-loop read against this
offline value.

Writes analysis/par_sensor_refit/ai_smoke_slice.jsonl (gitignored; carries
question text). The committed smoke result references only counts / row_keys.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

CANONICAL = Path("/home/profsynapse/code/Epistemic-Humility-Research")
PROBE_ROOT = CANONICAL / "experiment/phase1/probe"
REFIT = PROBE_ROOT / "analysis/par_sensor_refit"
AH_SCORED = PROBE_ROOT / "analysis/ah_stage0/score/scored_rows.jsonl"

# Variant selects the sensor whose p decides cell membership + the offline value
# carried for C3's integrity audit. v2 = the 4-bit serving sensor the reward
# reads (union_refit_rows_cleansft4bit.jsonl + union_pregen_4bit states).
VARIANTS = {
    "v1": {"refit_rows": REFIT / "union_refit_rows.jsonl",
           "union_pregen_rows": REFIT / "union_pregen/rows.jsonl",
           "out": REFIT / "ai_smoke_slice.jsonl"},
    "v2": {"refit_rows": REFIT / "union_refit_rows_cleansft4bit.jsonl",
           "union_pregen_rows": REFIT / "union_pregen_4bit/rows.jsonl",
           "out": REFIT / "ai_smoke_slice.jsonl"},
}

SEED = 0
N_CONCORDANT = 40
N_DOVER = 12
N_DUNDER = 12


def load_jsonl(p: Path):
    return [json.loads(l) for l in p.open(encoding="utf-8") if l.strip()]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--variant", choices=list(VARIANTS), default="v2")
    v = VARIANTS[ap.parse_args().variant]
    OUT = v["out"]
    rng = np.random.default_rng(SEED)
    refit = load_jsonl(v["refit_rows"])
    q_by_key = {r["row_key"]: r["question"]
                for r in load_jsonl(v["union_pregen_rows"])}
    aliases_by_key = {}
    for r in load_jsonl(AH_SCORED):
        aliases_by_key[r["row_key"]] = r.get("aliases", []) or []

    for r in refit:
        r["question"] = q_by_key.get(r["row_key"])
        r["aliases"] = aliases_by_key.get(r["row_key"], [])
        r["gold_answerable"] = (r["label"] == "known")
        p = float(r["p_unanswerable"])
        known = r["gold_answerable"]
        if known and p < 0.5:
            r["cell"] = "concordant"       # known, probe-answerable
        elif (not known) and p >= 0.5:
            r["cell"] = "concordant"       # unknown, probe-unanswerable
        elif known and p >= 0.5:
            r["cell"] = "D-over"           # known but probe says unanswerable
        else:
            r["cell"] = "D-under"          # unknown but probe says answerable

    # license guard + must have question text
    usable = [r for r in refit
              if r["question"] and "falseqa" not in r["source"].lower()]
    assert not any("falseqa" in r["source"].lower() for r in usable)

    def pick(cell, n, prefer_answerable_with_aliases=False):
        pool = [r for r in usable if r["cell"] == cell]
        if prefer_answerable_with_aliases:
            # for concordant, bias toward gold-answerable rows that HAVE aliases
            # (so the correctness bonus can actually fire in the smoke) but keep a
            # mix of unknown-concordant too.
            with_al = [r for r in pool if r["gold_answerable"] and r["aliases"]]
            unk = [r for r in pool if not r["gold_answerable"]]
            rng.shuffle(with_al); rng.shuffle(unk)
            half = n // 2
            sel = with_al[:half] + unk[: n - len(with_al[:half])]
            if len(sel) < n:
                rest = [r for r in pool if r not in sel]
                rng.shuffle(rest)
                sel += rest[: n - len(sel)]
            return sel[:n]
        idx = list(range(len(pool)))
        rng.shuffle(idx)
        return [pool[i] for i in idx[:n]]

    concordant = pick("concordant", N_CONCORDANT, prefer_answerable_with_aliases=True)
    dover = pick("D-over", N_DOVER)
    dunder = pick("D-under", N_DUNDER)
    slice_rows = concordant + dover + dunder

    with OUT.open("w", encoding="utf-8") as fh:
        for r in slice_rows:
            fh.write(json.dumps({
                "row_key": r["row_key"], "source": r["source"],
                "question": r["question"], "label": r["label"],
                "gold_answerable": r["gold_answerable"], "aliases": r["aliases"],
                "cell": r["cell"], "p_unanswerable_offline": float(r["p_unanswerable"]),
            }, ensure_ascii=False) + "\n")

    from collections import Counter
    comp = Counter(r["cell"] for r in slice_rows)
    n_alias = sum(1 for r in slice_rows if r["gold_answerable"] and r["aliases"])
    print(json.dumps({
        "n_total": len(slice_rows), "composition": dict(comp),
        "n_gold_answerable_with_aliases": n_alias, "seed": SEED,
        "out": str(OUT),
    }, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
