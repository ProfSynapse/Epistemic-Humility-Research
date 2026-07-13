#!/usr/bin/env python3
"""H9 (CPU, no GPU): deterministic held-out question-pool builder (C3/C4).

Reads the committed ID-manifest (analysis-committed/holdout_draw/holdout_ids.jsonl,
row_key + source + gold_label + qhash, NO text) and the gitignored AH source
JSONLs (via --data-root), and emits holdout_pool.jsonl (question text keyed by
row_key) reproducibly, so the staged pool the Modal harness consumes is built
from committed files rather than a manual step. Question text stays gitignored;
this file is uploaded to the private staging dataset repo by hand pre-launch.

Guarantees (closing the review's C3/C4):
  - per-row binding: recomputes qhash = sha256(row_key \x00 question_text) for
    each row and asserts it equals the committed manifest's qhash, so a
    right-key/wrong-text pool cannot pass.
  - schema pin (C4): emits `label` in the SOURCE domain {known, unknown} (NOT the
    manifest's mapped gold_label), which is what extract_gen.load_pool and the
    Modal gold-join expect; asserts every emitted label is in {known, unknown}.

Usage:
  python build_holdout_pool.py --cell cell.yaml \
    [--data-root /home/profsynapse/code/Epistemic-Humility-Research] [--smoke]

--smoke reads the smoke ID-manifest (analysis/holdout_draw_smoke/) and writes to
the gitignored analysis/ tree.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path


def load_jsonl(p: Path):
    return [json.loads(l) for l in p.open() if l.strip()]


def build(cell: dict, data_root: Path, exp_dir: Path, smoke: bool) -> dict:
    ho = cell["holdout"]
    label_domain = set(cell["pool_builder"]["label_domain"])   # {known, unknown}

    ids_path = (exp_dir / "analysis/holdout_draw_smoke/holdout_ids.jsonl" if smoke
                else exp_dir / ho["id_manifest_out"])
    ids = load_jsonl(ids_path)
    want = {r["row_key"]: r for r in ids}

    # source rows carry question text + source-domain label
    src = {}
    for rel in (ho["complement_sources"]["orig_rows"],
                ho["complement_sources"]["expansion_rows"]):
        for r in load_jsonl(data_root / rel):
            if r["row_key"] in want:
                src[r["row_key"]] = r

    missing = set(want) - set(src)
    assert not missing, f"{len(missing)} manifest row_keys absent from source JSONLs"

    out_rows = []
    for rk, m in want.items():
        r = src[rk]
        q = r["question"]
        qhash = hashlib.sha256((rk + "\x00" + q).encode("utf-8")).hexdigest()
        assert qhash == m["qhash"], \
            f"qhash mismatch for {rk}: manifest {m['qhash'][:12]} != rebuilt {qhash[:12]}"
        assert r["label"] in label_domain, \
            f"row {rk} label {r['label']!r} not in {sorted(label_domain)}"
        out_rows.append({"row_key": rk, "question": q, "label": r["label"],
                         "aliases": r.get("aliases", []), "qhash": qhash})

    out_path = (exp_dir / "analysis/holdout_pool/holdout_pool.jsonl" if smoke
                else exp_dir / cell["pool_builder"]["out"])
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w") as fh:
        for row in out_rows:
            fh.write(json.dumps(row, sort_keys=True) + "\n")

    return {"tier": "smoke" if smoke else "registered", "n_rows": len(out_rows),
            "label_breakdown": {lab: sum(1 for r in out_rows if r["label"] == lab)
                                for lab in sorted(label_domain)},
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
