"""Amendment Y descriptive control: text-only baseline for gate and dial.

Bounds how much of the hidden-state readout AUROC is attributable to question
SURFACE alone. TF-IDF logistic regression, stratified 5-fold CV, seed matches
the Y extraction seed. Purely descriptive (lab-notebook instrument); feeds the
Y roll-up table, changes no gate.

- GATE baseline: known-vs-unknown on the exact frozen SelfAware pool every Y
  cell uses (experiments/common/artifacts/selfaware_gate_pool/selfaware_gate_rows_frozen.jsonl).
- DIAL baseline: question-text -> correct-vs-wrong per model, using local
  Amendment Z row surfaces (gitignored local data; section skips silently if
  a family's rows are absent).

Run: python3 archive/experiment/phase1/probe/amendments/amendment_y_text_baseline.py \
       [--out experiments/pretrain-only-base-readout/artifacts/amendment_y_text_baseline_result.json]
"""
import argparse
import json
from pathlib import Path

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import StratifiedKFold
from sklearn.pipeline import make_pipeline

from path_compat import phase1_probe_dir, repo_root

PROBE_DIR = phase1_probe_dir()
REPO = repo_root()
DEFAULT_OUT = REPO / "experiments" / "pretrain-only-base-readout" / "artifacts" / "amendment_y_text_baseline_result.json"
DEFAULT_GATE_POOL = REPO / "experiments" / "common" / "artifacts" / "selfaware_gate_pool" / "selfaware_gate_rows_frozen.jsonl"
SEED = 20260630

WORD = dict(analyzer="word", ngram_range=(1, 2), min_df=2)
CHAR = dict(analyzer="char_wb", ngram_range=(3, 5), min_df=2)


def cv_auroc(texts, y, vec_kwargs, n_splits=5, seed=SEED):
    y = np.asarray(y)
    aucs = []
    skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=seed)
    for tr, te in skf.split(texts, y):
        pipe = make_pipeline(
            TfidfVectorizer(**vec_kwargs),
            LogisticRegression(max_iter=2000, C=1.0),
        )
        pipe.fit([texts[i] for i in tr], y[tr])
        p = pipe.predict_proba([texts[i] for i in te])[:, 1]
        aucs.append(roc_auc_score(y[te], p))
    return float(np.mean(aucs)), float(np.std(aucs))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    ap.add_argument("--z-rows-root", default=str(PROBE_DIR),
                    help="dir containing local z_<family>/rows.jsonl surfaces")
    args = ap.parse_args()

    result = {"seed": SEED, "cv": "stratified 5-fold",
              "model": "TF-IDF + LogisticRegression(C=1.0)"}

    pool_path = DEFAULT_GATE_POOL
    pool = [json.loads(l) for l in open(pool_path, encoding="utf-8")]
    texts = [r["question"] for r in pool]
    y = [1 if r["label"] == "known" else 0 for r in pool]
    gate = {"n": len(pool), "n_known": int(sum(y)), "n_unknown": int(len(y) - sum(y))}
    for name, kw in [("tfidf_word_1_2", WORD), ("tfidf_char_3_5", CHAR)]:
        mu, sd = cv_auroc(texts, y, kw)
        gate[name] = {"auroc_mean": round(mu, 4), "auroc_std": round(sd, 4)}
        print(f"GATE {name}: {mu:.4f} +/- {sd:.4f}")
    result["gate_baseline_frozen_pool"] = gate

    dial = {}
    z_root = Path(args.z_rows_root)
    for fam in ["qwen3.5-4b", "gemma-4-e4b", "llama-3.2-3b", "ministral-3-3b"]:
        rows_path = z_root / f"z_{fam}" / "rows.jsonl"
        if not rows_path.exists():
            dial[fam] = {"status": "rows-absent (local gitignored data)"}
            continue
        rows = [json.loads(l) for l in open(rows_path, encoding="utf-8")]
        ans = [r for r in rows if r.get("source") == "answerable" and r.get("answered")]
        t = [r["question"] for r in ans]
        yy = [1 if r["correct"] else 0 for r in ans]
        mu, sd = cv_auroc(t, yy, WORD)
        dial[fam] = {"n": len(ans), "n_correct": int(sum(yy)),
                     "auroc_mean": round(mu, 4), "auroc_std": round(sd, 4)}
        print(f"DIAL {fam}: {mu:.4f} +/- {sd:.4f} (n={len(ans)})")
    result["dial_baseline_question_surface_z_rows"] = dial

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, indent=1), encoding="utf-8")
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
