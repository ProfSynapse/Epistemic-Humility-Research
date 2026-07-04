#!/usr/bin/env python3
"""PAR mining PASS 1 — probe-score external candidates + D-over yield (CPU).

Lab-notebook work (no amendment letter). Team-lead task #63, branch
par-mining-recalibration, user-approved ("Mine away").

Scores the mining candidates (mining_candidates_v1 300 local + v2 9,097 external:
ambigqa 5,920 / falseqa 2,365 / truthfulqa 789 construct-flagged / bigbench 23)
with the FROZEN consensus(L20/L24/L28) readout at the raw-base pre-gen anchor —
identical extraction lineage and probe recipe as the AH pool (frozen AF-600
probes, NO refit; caution axis reconstructed exactly). Consensus @ margin band 0.

D-over = probe-confident (consensus certain) x gold-unanswerable. Every mining
candidate here is gold-unanswerable (label=unknown / gold_class=unanswerable),
so D-over = consensus-certain rows. Deduped alias-aware (scorers.norm_question)
against BOTH pool_v21 AND the 672 previously-mined unique D-over (base 253 +
expansion 419), reconstructed here by re-applying the D-over rule to the two AH
scored_rows files.

Deliverables (par_mining/):
  scored_rows.jsonl      per-row scores + caution + D-over flag + dedupe flag
                         (row_key + source + numbers; question text INCLUDED here
                         since this dir is gitignored — NOT the committed JSON)
  mining_yield.json      committed result copy (probe-dir top): per-source yield
                         (scored / D-over / new-after-dedupe), total new D-over vs
                         the 782-1,021 estimate, repetition factor at 30% mixture
                         for the 1,861-step GRPO run. TruthfulQA kept separate
                         (construct-flagged). FalseQA: COUNTS/KEYS ONLY, no text.

NO-LICENSE guard: FalseQA question text must never enter a committed file. The
committed mining_yield.json carries only counts and row_keys; the per-row
scored_rows.jsonl (which does carry question text) stays under gitignored
analysis/.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np
from safetensors import safe_open
import joblib

PROBE_DIR = Path(__file__).resolve().parent
EVAL_DIR = PROBE_DIR.parent / "eval"
for p in (str(PROBE_DIR), str(EVAL_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)

import scorers  # noqa: E402
from amendment_ah_redesign_collinearity import load_af_caution  # noqa: E402

CANONICAL = Path("/home/profsynapse/code/Epistemic-Humility-Research")
STAGE0 = CANONICAL / "experiment/phase1/probe/analysis/ah_stage0"
PAR_MINING = CANONICAL / "experiment/phase1/probe/analysis/par_mining"
PREGEN = PAR_MINING / "pregen"
PROBES = STAGE0 / "probes"
GRID = STAGE0 / "score" / "divergence_grid.json"
POOL_V21 = STAGE0 / "expansion" / "pool_v21.jsonl"
AH_BASE_SCORED = STAGE0 / "score" / "scored_rows.jsonl"
AH_EXP_SCORED = STAGE0 / "expansion" / "score" / "scored_rows.jsonl"
RESULT_COPY = PROBE_DIR / "par_mining_yield.json"

LAYERS = ["L20", "L24", "L28"]

# GRPO run scale (session-0026 cp011) for the repetition-factor calc.
GRPO_STEPS = 1861
PROMPTS_PER_STEP = 8
DIVERGENT_MIX = 0.30
DOVER_ESTIMATE_LO = 782
DOVER_ESTIMATE_HI = 1021

# canonical source-group labels for the yield table
def source_group(src: str) -> str:
    s = src.lower()
    if s.startswith("kuq"):
        return "kuq_v1_local"
    if s.startswith("ambigqa"):
        return "ambigqa"
    if s.startswith("falseqa"):
        return "falseqa"
    if s.startswith("truthfulqa"):
        return "truthfulqa"
    if s.startswith("bigbench"):
        return "bigbench_known_unknowns"
    return s


def load_jsonl(p):
    return [json.loads(l) for l in p.open() if l.strip()]


def load_probes():
    probes = {ly: joblib.load(PROBES / f"probe_{ly}.joblib") for ly in LAYERS}
    return probes


def score_layer(probe, X):
    return probe["clf"].decision_function(probe["scaler"].transform(X))


def build_dedupe_reference():
    """Union of pool_v21 questions + the 672 previously-mined unique D-over,
    as a set of normalized questions (scorers.norm_question)."""
    ref = set()
    # pool_v21 does not carry question text; join via the AH candidate files.
    # But the 672 mined D-over (below) already superset pool_v21's 669, so the
    # 672 set is the operative reference. We still union pool_v21 keys defensively
    # through the scored files, which DO carry question text.
    def add_dover(path):
        for l in path.open():
            if not l.strip():
                continue
            r = json.loads(l)
            if (r["score_L20"] > 0 and r["score_L24"] > 0 and r["score_L28"] > 0
                    and r["label"] != "known"):
                ref.add(scorers.norm_question(r["question"]))
    add_dover(AH_BASE_SCORED)
    add_dover(AH_EXP_SCORED)
    return ref


def run(args) -> int:
    PAR_MINING.mkdir(parents=True, exist_ok=True)

    rows = load_jsonl(PREGEN / "rows.jsonl")
    print(f"[par/score] mining pregen rows: {len(rows)}", flush=True)

    z = json.loads(GRID.read_text())["score_sd"]

    feats = {ly: [] for ly in LAYERS}
    caution_X = []
    for r in rows:
        with safe_open(str(PREGEN / f"{r['safe_key']}__pre.safetensors"), "pt") as st:
            for ly in LAYERS:
                feats[ly].append(st.get_tensor(ly).float().numpy())
            caution_X.append(st.get_tensor("L24").float().numpy().astype(np.float64))
    for ly in LAYERS:
        feats[ly] = np.asarray(feats[ly])
    caution_X = np.vstack(caution_X)

    probes = load_probes()
    scores = {ly: score_layer(probes[ly], feats[ly]) for ly in LAYERS}
    clf_c, sign, base_sd, cv_auroc = load_af_caution()
    caution = sign * clf_c.decision_function(caution_X)
    print(f"[par/score] caution axis CV AUROC={cv_auroc:.4f} base_sd={base_sd:.3f} "
          f"sign={sign}", flush=True)

    # every mining candidate is gold-unanswerable; consensus-certain => D-over
    cons_certain = ((scores["L20"] > 0) & (scores["L24"] > 0) & (scores["L28"] > 0))

    dedupe_ref = build_dedupe_reference()
    print(f"[par/score] dedupe reference (672 mined D-over norm_questions): "
          f"{len(dedupe_ref)}", flush=True)

    # per-source tallies
    scored_by_src = Counter()
    dover_by_src = Counter()
    new_dover_by_src = Counter()
    new_dover_keys_by_src = {}   # source_group -> [row_key,...] (for committed JSON)
    seen_new = set()             # dedupe within this pass too (norm_question)

    per_row = []
    for i, r in enumerate(rows):
        sg = source_group(r["source"])
        scored_by_src[sg] += 1
        is_dover = bool(cons_certain[i])
        nq = scorers.norm_question(r["question"])
        is_dup = nq in dedupe_ref
        is_new_dover = is_dover and (not is_dup) and (nq not in seen_new)
        if is_dover:
            dover_by_src[sg] += 1
        if is_new_dover:
            seen_new.add(nq)
            new_dover_by_src[sg] += 1
            new_dover_keys_by_src.setdefault(sg, []).append(r["row_key"])
        per_row.append({
            "row_key": r["row_key"], "safe_key": r["safe_key"],
            "source": r["source"], "source_group": sg,
            "question": r["question"],  # gitignored dir only
            "label": r["label"],
            "score_L20": float(scores["L20"][i]),
            "score_L24": float(scores["L24"][i]),
            "score_L28": float(scores["L28"][i]),
            "caution_dist": float(caution[i]),
            "caution_dist_z": float(caution[i] / base_sd),
            "consensus_certain": is_dover, "is_dover": is_dover,
            "dup_vs_mined": is_dup, "new_dover": is_new_dover,
        })

    # write per-row (gitignored) — includes question text (incl. FalseQA), OK here
    with (PAR_MINING / "scored_rows.jsonl").open("w", encoding="utf-8") as fh:
        for row in per_row:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")

    # ---- yields ----
    # TruthfulQA is construct-flagged/exploratory: report it but EXCLUDE from the
    # headline new-D-over total (matches REPORT.md's estimate exclusion).
    def clean_total(counter):
        return int(sum(v for k, v in counter.items() if k != "truthfulqa"))

    total_new_dover_clean = clean_total(new_dover_by_src)
    total_new_dover_incl_tqa = int(sum(new_dover_by_src.values()))
    tqa_new_dover = int(new_dover_by_src.get("truthfulqa", 0))

    # repetition factor at 30% mixture over the GRPO run
    exposures = GRPO_STEPS * PROMPTS_PER_STEP
    divergent_exposures = DIVERGENT_MIX * exposures
    supply = total_new_dover_clean + 672  # new + already-mined available pool
    rep_new_only = (divergent_exposures / total_new_dover_clean
                    if total_new_dover_clean else None)
    rep_full_supply = (divergent_exposures / supply) if supply else None

    yield_table = {}
    for sg in sorted(scored_by_src):
        yield_table[sg] = {
            "scored": int(scored_by_src[sg]),
            "d_over": int(dover_by_src.get(sg, 0)),
            "d_over_rate_pct": (round(100.0 * dover_by_src.get(sg, 0)
                                      / scored_by_src[sg], 2)
                                if scored_by_src[sg] else None),
            "new_after_dedupe": int(new_dover_by_src.get(sg, 0)),
        }

    result = {
        "stage": "par_mining_pass1",
        "branch": "par-mining-recalibration",
        "readout": "frozen consensus(L20/L24/L28) @ band 0, raw-base pre-gen anchor",
        "probe_recipe": "frozen AF-600 probes (no refit); AG caution axis reconstructed",
        "caution_axis": {"cv_auroc": round(cv_auroc, 4),
                         "base_sd": round(base_sd, 3), "sign": sign},
        "mined_pool_z": z,
        "n_scored": len(rows),
        "dedupe_reference_n_mined_dover": len(dedupe_ref),
        "yield_by_source": yield_table,
        "totals": {
            "new_dover_excl_truthfulqa": total_new_dover_clean,
            "new_dover_incl_truthfulqa": total_new_dover_incl_tqa,
            "truthfulqa_new_dover_exploratory": tqa_new_dover,
            "estimate_range": [DOVER_ESTIMATE_LO, DOVER_ESTIMATE_HI],
            "within_estimate": bool(DOVER_ESTIMATE_LO <= total_new_dover_clean
                                    <= DOVER_ESTIMATE_HI),
        },
        "repetition_at_30pct_mixture": {
            "grpo_steps": GRPO_STEPS, "prompts_per_step": PROMPTS_PER_STEP,
            "total_exposures": int(exposures),
            "divergent_exposures": int(divergent_exposures),
            "supply_new_only": total_new_dover_clean,
            "supply_new_plus_mined": supply,
            "repetition_factor_new_only": (round(rep_new_only, 1)
                                           if rep_new_only else None),
            "repetition_factor_full_supply": (round(rep_full_supply, 1)
                                              if rep_full_supply else None),
            "note": "prior wall was ~1,489x on 3 remaining D-over; lower is better",
        },
        # committed keys for the new D-over (row_key only; NO question text -> safe
        # for the NO-LICENSE FalseQA rows).
        "new_dover_row_keys_by_source": new_dover_keys_by_src,
        "no_license_note": "FalseQA is use-only (no redistribution); this JSON "
                           "carries FalseQA row_keys/counts only, never text. "
                           "Question text lives solely in the gitignored "
                           "par_mining/scored_rows.jsonl.",
    }

    (PAR_MINING / "mining_yield.json").write_text(json.dumps(result, indent=2),
                                                 encoding="utf-8")
    RESULT_COPY.write_text(json.dumps(result, indent=2), encoding="utf-8")
    # print a compact summary (keys elided)
    summary = {k: v for k, v in result.items()
               if k != "new_dover_row_keys_by_source"}
    print(json.dumps(summary, indent=2), flush=True)
    print(f"[par/score] DONE -> {PAR_MINING/'mining_yield.json'} + {RESULT_COPY}",
          flush=True)
    return 0


def parse_args(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    return ap.parse_args(argv)


if __name__ == "__main__":
    sys.exit(run(parse_args()))
