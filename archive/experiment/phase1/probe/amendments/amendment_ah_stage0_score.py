#!/usr/bin/env python3
"""Amendment AH Stage-0 (script 4/4) — score + flag divergence grid (CPU).

Pre-registered in
experiments/divergent-pool-own-readout/AMENDMENT.md (§4 step 4).

Scores every extracted candidate with the three frozen layer-probes (L20/L24/
L28) and the 5-fold L24 ensemble, then reports the divergence yield GRID. Does
NOT pick a rule -- emits the full grid for the orchestrator to lock.

Divergence cells (label "known"==answerable==gold y=1; decision_function>0 =>
probe-certain):
  D-over : probe-certain (>+margin) AND gold-unanswerable (label unknown)
  D-under: probe-uncertain (<-margin) AND gold-answerable  (label known)

Rules:
  (a) L24-alone       : the L24 probe decides.
  (b) consensus(3)    : ALL of L20/L24/L28 agree on the divergent side.
  (c) ensemble-unanim : all 5 fold-models (L24) agree on the divergent side.

Margin bands (z = per-probe SD of decision_function on the MINED pool):
  0, 0.5z, 1z, 2z. A row qualifies at band b if the deciding score(s) sit
  beyond b*z on the wrong side of threshold 0. For consensus/ensemble, EACH
  contributing score must clear the band.

Writes:
  ah_stage0/score/divergence_grid.json  (the full grid)
  ah_stage0/score/scored_rows.jsonl     (per-row scores + labels, for later use)
  ah_stage0/score/dunder_candidates.jsonl (loosest rule, band 0 -> GPU verify)
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from safetensors import safe_open
import joblib

from path_compat import repo_root

CANONICAL = repo_root()
DEFAULT_ROOT = CANONICAL / "experiment/phase1/probe/analysis/ah_stage0"

LAYERS = ["L20", "L24", "L28"]
BANDS = [0.0, 0.5, 1.0, 2.0]


def load_probes(probes_dir: Path):
    probes = {}
    for layer in LAYERS:
        probes[layer] = joblib.load(probes_dir / f"probe_{layer}.joblib")
    ensemble = joblib.load(probes_dir / "ensemble_L24.joblib")
    return probes, ensemble


def score_layer(probe, X):
    sc, clf = probe["scaler"], probe["clf"]
    return clf.decision_function(sc.transform(X))


def run(args) -> int:
    root = Path(args.root).resolve()
    pregen = root / "pregen"
    probes_dir = root / "probes"
    out_dir = root / "score"
    out_dir.mkdir(parents=True, exist_ok=True)

    # Load extracted rows.
    rows = []
    with (pregen / "rows.jsonl").open() as fh:
        for line in fh:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    print(f"[ah/score] extracted rows: {len(rows)}", flush=True)

    # Load per-layer feature matrices.
    feats = {ly: [] for ly in LAYERS}
    for r in rows:
        fp = pregen / f"{r['safe_key']}__pre.safetensors"
        with safe_open(str(fp), "pt") as st:
            for ly in LAYERS:
                feats[ly].append(st.get_tensor(ly).float().numpy())
    for ly in LAYERS:
        feats[ly] = np.asarray(feats[ly])

    probes, ensemble = load_probes(probes_dir)

    # Per-layer decision scores.
    scores = {ly: score_layer(probes[ly], feats[ly]) for ly in LAYERS}
    # Ensemble fold scores at L24.
    fold_scores = np.stack(
        [f["clf"].decision_function(f["scaler"].transform(feats["L24"]))
         for f in ensemble["folds"]], axis=1)  # (n, 5)

    gold_known = np.array([1 if r["label"] == "known" else 0 for r in rows])
    n = len(rows)

    # z per probe = SD of decision_function on the MINED pool.
    z = {ly: float(scores[ly].std()) for ly in LAYERS}
    z_fold = float(fold_scores.std())  # pooled SD across all fold scores
    print(f"[ah/score] mined-pool score SD: "
          f"{{'L20': {z['L20']:.3f}, 'L24': {z['L24']:.3f}, "
          f"'L28': {z['L28']:.3f}, 'fold': {z_fold:.3f}}}", flush=True)

    def cell_counts(over_mask, under_mask):
        # restrict to the correct gold class
        d_over = int((over_mask & (gold_known == 0)).sum())
        d_under = int((under_mask & (gold_known == 1)).sum())
        return d_over, d_under

    grid = {"n_total": n,
            "n_gold_answerable": int(gold_known.sum()),
            "n_gold_unanswerable": int((gold_known == 0).sum()),
            "score_sd": {"L20": z["L20"], "L24": z["L24"], "L28": z["L28"],
                         "fold": z_fold},
            "rules": {}}

    # Rule (a): L24 alone.
    rule_a = {}
    for b in BANDS:
        m = b * z["L24"]
        over = scores["L24"] > m
        under = scores["L24"] < -m
        do, du = cell_counts(over, under)
        rule_a[f"{b}z"] = {"D_over": do, "D_under": du}
    grid["rules"]["L24_alone"] = rule_a

    # Rule (b): consensus of L20/L24/L28 (all three beyond band on same side).
    rule_b = {}
    for b in BANDS:
        over = np.ones(n, dtype=bool)
        under = np.ones(n, dtype=bool)
        for ly in LAYERS:
            m = b * z[ly]
            over &= scores[ly] > m
            under &= scores[ly] < -m
        do, du = cell_counts(over, under)
        rule_b[f"{b}z"] = {"D_over": do, "D_under": du}
    grid["rules"]["consensus_L20_L24_L28"] = rule_b

    # Rule (c): ensemble unanimity (all 5 fold-models beyond band on same side).
    rule_c = {}
    for b in BANDS:
        m = b * z_fold
        over = np.all(fold_scores > m, axis=1)
        under = np.all(fold_scores < -m, axis=1)
        do, du = cell_counts(over, under)
        rule_c[f"{b}z"] = {"D_over": do, "D_under": du}
    grid["rules"]["ensemble_unanimity_L24"] = rule_c

    (out_dir / "divergence_grid.json").write_text(json.dumps(grid, indent=2),
                                                  encoding="utf-8")

    # Persist per-row scores for downstream use.
    with (out_dir / "scored_rows.jsonl").open("w", encoding="utf-8") as fh:
        for i, r in enumerate(rows):
            fh.write(json.dumps({
                "row_key": r["row_key"], "label": r["label"],
                "question": r["question"], "aliases": r.get("aliases", []),
                "source": r["source"], "safe_key": r["safe_key"],
                "score_L20": float(scores["L20"][i]),
                "score_L24": float(scores["L24"][i]),
                "score_L28": float(scores["L28"][i]),
                "fold_scores": [float(x) for x in fold_scores[i]],
            }, ensure_ascii=False) + "\n")

    # D-under candidates under the LOOSEST rule (L24 alone, band 0) -> GPU verify.
    loosest_under = (scores["L24"] < 0) & (gold_known == 1)
    n_du = int(loosest_under.sum())
    with (out_dir / "dunder_candidates.jsonl").open("w", encoding="utf-8") as fh:
        for i, r in enumerate(rows):
            if loosest_under[i]:
                fh.write(json.dumps({
                    "row_key": r["row_key"], "label": r["label"],
                    "question": r["question"], "aliases": r.get("aliases", []),
                    "source": r["source"], "safe_key": r["safe_key"],
                    "score_L24": float(scores["L24"][i]),
                    "score_L20": float(scores["L20"][i]),
                    "score_L28": float(scores["L28"][i]),
                    "fold_scores": [float(x) for x in fold_scores[i]],
                }, ensure_ascii=False) + "\n")

    print(json.dumps(grid, indent=2), flush=True)
    print(f"[ah/score] D-under candidates (loosest, L24<0): {n_du} "
          f"-> {out_dir/'dunder_candidates.jsonl'}", flush=True)
    print(f"[ah/score] DONE -> {out_dir}", flush=True)
    return 0


def parse_args(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", default=str(DEFAULT_ROOT))
    return ap.parse_args(argv)


if __name__ == "__main__":
    sys.exit(run(parse_args()))
