#!/usr/bin/env python3
"""BB phase 1 step 0b (CPU, no GPU): deterministic fit-surface question-pool
builder, modelled on H9's build_holdout_pool.py (AMENDMENT.md section 5.1).

Reads the committed fit ID-manifest (analysis-committed/fit_surface/fit_ids.jsonl,
row_key + source + gold_label + qhash, NO text) and the gitignored AL source
al_source_graded (rows_graded.jsonl, which carries question text), and emits
fit_pool.jsonl (question text keyed by row_key) reproducibly, so the pool the
Modal harness consumes is built from committed files rather than a manual step.
Question text stays gitignored; this file is what gets staged to the private
dataset repo (professorsynapse/eh-bb-fit-pool per cell.yaml).

Guarantees (same C3/C4 discipline as H9's build_holdout_pool.py):
  - per-row binding: recomputes qhash = sha256(row_key \x00 question_text) for
    each row and asserts it equals the committed manifest's qhash, so a
    right-key/wrong-text pool cannot pass.
  - schema pin: emits `label` in the SOURCE domain {known, unknown} (matching
    what amendment_ai_verdict_extract_gen.py's load_pool and the Modal
    gold-join expect), taken directly from al_source_graded's own `label`
    field (already in that domain); asserts every emitted label is in
    {known, unknown}.

Usage:
  python build_fit_pool.py --cell cell.yaml \
    [--data-root /home/profsynapse/code/Epistemic-Humility-Research] [--smoke]

--smoke reads the smoke ID-manifest (analysis/fit_surface_smoke/) and writes to
the gitignored analysis/ tree.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

LABEL_DOMAIN = {"known", "unknown"}


def load_jsonl(p: Path):
    return [json.loads(l) for l in p.open() if l.strip()]


def build(cell: dict, data_root: Path, exp_dir: Path, smoke: bool) -> dict:
    fs = cell["phase1"]["fit_surface"]

    ids_path = (exp_dir / "analysis/fit_surface_smoke/fit_ids.jsonl" if smoke
                else exp_dir / "analysis-committed/fit_surface/fit_ids.jsonl")
    ids = load_jsonl(ids_path)
    want = {r["row_key"]: r for r in ids}

    src = {r["row_key"]: r for r in load_jsonl(data_root / fs["al_source_graded"])
           if r["row_key"] in want}
    missing = set(want) - set(src)
    assert not missing, f"{len(missing)} manifest row_keys absent from al_source_graded"

    out_rows = []
    for rk, m in want.items():
        r = src[rk]
        q = r["question"]
        qhash = hashlib.sha256((rk + "\x00" + q).encode("utf-8")).hexdigest()
        assert qhash == m["qhash"], \
            f"qhash mismatch for {rk}: manifest {m['qhash'][:12]} != rebuilt {qhash[:12]}"
        assert r["label"] in LABEL_DOMAIN, \
            f"row {rk} label {r['label']!r} not in {sorted(LABEL_DOMAIN)}"
        out_rows.append({"row_key": rk, "question": q, "label": r["label"],
                         "aliases": r.get("aliases", []), "qhash": qhash})

    out_path = (exp_dir / "analysis/fit_pool_smoke/fit_pool.jsonl" if smoke
                else exp_dir / "analysis/fit_pool/fit_pool.jsonl")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w") as fh:
        for row in out_rows:
            fh.write(json.dumps(row, sort_keys=True) + "\n")

    return {"tier": "smoke" if smoke else "registered", "n_rows": len(out_rows),
            "label_breakdown": {lab: sum(1 for r in out_rows if r["label"] == lab)
                                for lab in sorted(LABEL_DOMAIN)},
            "all_qhash_verified": True, "pool_out": str(out_path)}


def main() -> int:
    import yaml

    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cell", default="cell.yaml")
    ap.add_argument("--data-root",
                    default="/home/profsynapse/code/Epistemic-Humility-Research")
    ap.add_argument("--smoke", action="store_true")
    args = ap.parse_args()
    exp_dir = Path(args.cell).resolve().parent
    cell = yaml.safe_load(Path(args.cell).read_text())
    print(json.dumps(build(cell, Path(args.data_root), exp_dir, args.smoke), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
