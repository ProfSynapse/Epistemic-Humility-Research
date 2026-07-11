#!/usr/bin/env python3
"""H9 step 2 (CPU, no GPU): draw the stratified held-out row population.

Reconstructs the 16,834-row complement (AH union pool minus AL's 1,662-row fit
surface) by pure set arithmetic on two on-disk JSONL files, then draws a
fixed-seed stratified sample matching the fit surface's per-source mix (targets
in cell.yaml). Recovery is verified in
docs/review/h9-holdout-candidate-inventory-2026-07-10.md. No classifier refit, no
GPU.

CONTAINMENT: the committed ID-manifest carries ONLY row_key + source + gold
answerability label. Question text, aliases, and any other row content stay out
of the committed file (they live only in the gitignored source JSONLs). See
AMENDMENT.md section 4 and the experiment .gitignore.

Usage:
  python draw_holdout.py --cell cell.yaml \
    [--data-root /home/profsynapse/code/Epistemic-Humility-Research] [--smoke]

--smoke writes to the gitignored analysis/ tree and stamps tier=smoke (dry-run;
the registered draw into analysis-committed/ happens post-sign). The source
JSONLs are gitignored and live only in the canonical checkout; --data-root points
there.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path


LABEL_TO_GOLD = {"known": "answerable", "unknown": "unanswerable"}


def load_jsonl(p: Path):
    return [json.loads(l) for l in p.open() if l.strip()]


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def draw(cell: dict, data_root: Path, exp_dir: Path, smoke: bool) -> dict:
    import numpy as np

    ho = cell["holdout"]
    seed = cell["seed"]
    targets = ho["stratify_targets"]
    orig_p = data_root / ho["complement_sources"]["orig_rows"]
    exp_p = data_root / ho["complement_sources"]["expansion_rows"]
    fit_p = data_root / ho["complement_sources"]["fit_surface"]

    # ---- reconstruct the union (disjoint ah:: / ahx:: namespaces) ----
    # question text is read here only to compute the per-row binding hash (C3);
    # it is never written to the committed manifest.
    orig = {r["row_key"]: {"source": r["source"], "label": r["label"],
                           "question": r["question"]}
            for r in load_jsonl(orig_p)}
    exp = {r["row_key"]: {"source": r["source"], "label": r["label"],
                          "question": r["question"]}
           for r in load_jsonl(exp_p)}
    assert not (set(orig) & set(exp)), "orig/expansion row_key namespaces overlap"
    union = {**orig, **exp}
    assert len(union) == 18496, f"union {len(union)} != 18496"

    # ---- complement = union minus fit surface ----
    fit_keys = {r["row_key"] for r in load_jsonl(fit_p)}
    orphans = fit_keys - set(union)
    assert not orphans, f"{len(orphans)} fit-surface row_keys absent from union"
    complement = {k: v for k, v in union.items() if k not in fit_keys}
    assert len(complement) == 16834, f"complement {len(complement)} != 16834"

    # ---- per-source supply + stratified draw (fixed seed, no replacement) ----
    by_source: dict[str, list[str]] = {}
    for k, v in complement.items():
        by_source.setdefault(v["source"], []).append(k)
    for s in by_source:
        by_source[s].sort()  # deterministic order before shuffling

    assert sum(targets.values()) == ho["draw_size"], \
        f"targets sum {sum(targets.values())} != draw_size {ho['draw_size']}"

    rng = np.random.default_rng(seed)
    drawn: list[dict] = []
    per_source_drawn: dict[str, int] = {}
    # N3: draw in a fixed sorted-source order so the RNG stream is independent of
    # the YAML key order in stratify_targets.
    for source in sorted(targets):
        n_target = targets[source]
        supply = by_source.get(source, [])
        assert len(supply) >= n_target, \
            f"source {source}: target {n_target} > supply {len(supply)}"
        pick_idx = rng.choice(len(supply), size=n_target, replace=False)
        for i in sorted(pick_idx):
            rk = supply[i]
            qhash = hashlib.sha256(
                (rk + "\x00" + complement[rk]["question"]).encode("utf-8")).hexdigest()
            drawn.append({"row_key": rk, "source": source,
                          "gold_label": LABEL_TO_GOLD[complement[rk]["label"]],
                          "qhash": qhash})
        per_source_drawn[source] = n_target

    # ---- outputs ----
    if smoke:
        out_dir = exp_dir / "analysis" / "holdout_draw_smoke"
    else:
        out_dir = exp_dir / Path(ho["id_manifest_out"]).parent
    out_dir.mkdir(parents=True, exist_ok=True)
    ids_path = out_dir / "holdout_ids.jsonl"
    with ids_path.open("w") as fh:
        for row in drawn:
            fh.write(json.dumps(row, sort_keys=True) + "\n")

    complement_by_source = {s: len(ks) for s, ks in sorted(by_source.items())}
    manifest = {
        "tier": "smoke" if smoke else "registered",
        "seed": seed,
        "draw_size": len(drawn),
        "targets": targets,
        "per_source_drawn": per_source_drawn,
        "per_source_drawn_matches_targets": per_source_drawn == dict(targets),
        "complement_count": len(complement),
        "complement_by_source": complement_by_source,
        "union_count": len(union),
        "fit_surface_count": len(fit_keys),
        "source_file_sha256": {
            "orig_rows": _sha256(orig_p), "expansion_rows": _sha256(exp_p),
            "fit_surface": _sha256(fit_p)},
        "gold_label_breakdown": {
            g: sum(1 for r in drawn if r["gold_label"] == g)
            for g in ("answerable", "unanswerable")},
        "collision_provenance": (
            "exact-text zero-collision vs fit surface governed by "
            "docs/review/h9-holdout-candidate-inventory-2026-07-10.md section 4 "
            "(not recomputed here; pool_v21.jsonl carries no question text)"),
        "ids_manifest": str(ids_path),
    }
    (out_dir / "draw_manifest.json").write_text(json.dumps(manifest, indent=2))
    return manifest


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
    manifest = draw(cell, Path(args.data_root), exp_dir, args.smoke)
    print(json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
