#!/usr/bin/env python3
"""Amendment AH Stage-0 EXPANSION (script 2/2) — score + cell counts (CPU).

Team-lead task 2026-07-03 step 3. Scores the expansion pregen states with the
FROZEN AF-600 probes (L20/L24/L28 + 5-fold L24 ensemble) — do NOT refit — and
applies the FROZEN AG caution axis (reconstructed exactly per the redesign
check). Reports new cell counts at consensus@band0:

  - probe-certain gold-unanswerable (D-over) broken down by KUQ category
    (canonicalized across the two KUQ category vocabularies);
  - probe-uncertain gold-answerable (the muzzle-rescue number) total and by
    source (triviaqa / popqa).

Category is re-joined from the expansion candidate file by row_key (the frozen
extractor does not carry it, so the AG-exact surface stays untouched).

Consensus rule (matches the mining pass): L20 AND L24 AND L28 agree on the
divergent side, beyond band*z where z = per-probe SD on the ORIGINAL mined pool
(read from score/divergence_grid.json — the frozen mining z, so bands are
comparable across passes).

Writes analysis/ah_stage0/expansion/score/:
  scored_rows.jsonl      (per-row doubt + caution + category)
  expansion_cells.json   (cell counts + breakdowns)
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
sys.path.insert(0, str(PROBE_DIR))
from amendment_ah_redesign_collinearity import load_af_caution  # noqa: E402

CANONICAL = Path("/home/profsynapse/code/Epistemic-Humility-Research")
STAGE0 = CANONICAL / "experiment/phase1/probe/analysis/ah_stage0"
EXP = STAGE0 / "expansion"
PREGEN = EXP / "pregen"
CANDIDATES = EXP / "expansion_candidates.jsonl"
PROBES = STAGE0 / "probes"
GRID = STAGE0 / "score" / "divergence_grid.json"
OUT = EXP / "score"

LAYERS = ["L20", "L24", "L28"]

# Canonicalize the two KUQ category vocabularies into a shared set + a crisp flag.
CATEGORY_CANON = {
    "controversial": "controversial",
    "controversial/debatable question": "controversial",
    "ambiguous": "ambiguous",
    "underspecified question": "ambiguous",
    "unsolved problem": "unsolved_problem",
    "unsolved problem/mistery": "unsolved_problem",
    "future unknown": "future_unknown",
    "false assumption": "false_assumption",
    "question with false assumption": "false_assumption",
    "counterfactual": "counterfactual",
    "counterfactual questions": "counterfactual",
}
# crisp flag for pool composition (false assumption | counterfactual | selfaware)
CRISP_FLAG = {
    "false_assumption": "false_assumption",
    "counterfactual": "counterfactual",
}


def canon_category(raw: str) -> str:
    if not raw:
        return "(none)"
    return CATEGORY_CANON.get(raw.strip().lower(), raw.strip().lower())


def load_jsonl(p):
    return [json.loads(l) for l in p.open() if l.strip()]


def load_probes():
    probes = {ly: joblib.load(PROBES / f"probe_{ly}.joblib") for ly in LAYERS}
    ensemble = joblib.load(PROBES / "ensemble_L24.joblib")
    return probes, ensemble


def score_layer(probe, X):
    return probe["clf"].decision_function(probe["scaler"].transform(X))


def run(args) -> int:
    OUT.mkdir(parents=True, exist_ok=True)

    rows = load_jsonl(PREGEN / "rows.jsonl")
    print(f"[ahx/score] expansion pregen rows: {len(rows)}", flush=True)

    # re-join category (+ source truth) from the candidate file by row_key
    cand = {r["row_key"]: r for r in load_jsonl(CANDIDATES)}

    # frozen mining z (comparable bands across passes)
    z = json.loads(GRID.read_text())["score_sd"]

    # feature matrices per layer
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

    probes, ensemble = load_probes()
    scores = {ly: score_layer(probes[ly], feats[ly]) for ly in LAYERS}
    fold_scores = np.stack(
        [f["clf"].decision_function(f["scaler"].transform(feats["L24"]))
         for f in ensemble["folds"]], axis=1)

    # frozen AG caution axis (identical recipe to redesign check)
    clf_c, sign, base_sd, cv_auroc = load_af_caution()
    caution = sign * clf_c.decision_function(caution_X)
    print(f"[ahx/score] caution axis CV AUROC={cv_auroc:.4f} base_sd={base_sd:.3f} "
          f"sign={sign}", flush=True)

    gold_known = np.array([1 if r["label"] == "known" else 0 for r in rows])
    n = len(rows)

    def consensus_certain(band):
        return ((scores["L20"] > band * z["L20"]) &
                (scores["L24"] > band * z["L24"]) &
                (scores["L28"] > band * z["L28"]))

    def consensus_uncertain(band):
        return ((scores["L20"] < -band * z["L20"]) &
                (scores["L24"] < -band * z["L24"]) &
                (scores["L28"] < -band * z["L28"]))

    # ---- cells at consensus@band0 ----
    m_dover = consensus_certain(0.0) & (gold_known == 0)   # probe-certain unanswerable
    m_muz = consensus_uncertain(0.0) & (gold_known == 1)   # probe-uncertain answerable (rescue)

    # D-over by KUQ category
    dover_cat = Counter()
    dover_source = Counter()
    for i in range(n):
        if m_dover[i]:
            c = cand.get(rows[i]["row_key"], {})
            dover_cat[canon_category(c.get("category", ""))] += 1
            dover_source[rows[i]["source"]] += 1

    # muzzle-rescue by source
    muz_source = Counter()
    for i in range(n):
        if m_muz[i]:
            muz_source[rows[i]["source"]] += 1

    # also L24-alone counts for reference
    dover_L24 = int(((scores["L24"] > 0) & (gold_known == 0)).sum())
    muz_L24 = int(((scores["L24"] < 0) & (gold_known == 1)).sum())

    cells = {
        "mined_pool_z_used": z,
        "caution_axis": {"cv_auroc": round(cv_auroc, 4), "base_sd": round(base_sd, 3),
                         "sign": sign},
        "n_expansion": n,
        "n_gold_answerable": int(gold_known.sum()),
        "n_gold_unanswerable": int((gold_known == 0).sum()),
        "D_over_consensus_0z": {
            "total": int(m_dover.sum()),
            "by_kuq_category": dict(dover_cat.most_common()),
            "by_source": dict(dover_source.most_common()),
        },
        "muzzle_rescue_consensus_0z": {
            "total": int(m_muz.sum()),
            "by_source": dict(muz_source.most_common()),
        },
        "reference_L24_alone": {"D_over": dover_L24, "muzzle_rescue": muz_L24},
    }

    # persist per-row scores (+ caution + category) for pool v2.1
    with (OUT / "scored_rows.jsonl").open("w", encoding="utf-8") as fh:
        for i, r in enumerate(rows):
            c = cand.get(r["row_key"], {})
            fh.write(json.dumps({
                "row_key": r["row_key"], "safe_key": r["safe_key"],
                "label": r["label"], "source": r["source"],
                "question": r["question"], "aliases": r.get("aliases", []),
                "category": c.get("category", ""),
                "category_raw": c.get("category", ""),
                "category_canon": canon_category(c.get("category", "")),
                "score_L20": float(scores["L20"][i]),
                "score_L24": float(scores["L24"][i]),
                "score_L28": float(scores["L28"][i]),
                "fold_scores": [float(x) for x in fold_scores[i]],
                "caution_dist": float(caution[i]),
                "caution_dist_z": float(caution[i] / base_sd),
            }, ensure_ascii=False) + "\n")

    (OUT / "expansion_cells.json").write_text(json.dumps(cells, indent=2),
                                             encoding="utf-8")
    print(json.dumps(cells, indent=2), flush=True)
    print(f"[ahx/score] DONE -> {OUT}", flush=True)
    return 0


def parse_args(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    return ap.parse_args(argv)


if __name__ == "__main__":
    sys.exit(run(parse_args()))
