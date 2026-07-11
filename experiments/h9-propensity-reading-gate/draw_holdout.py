#!/usr/bin/env python3
"""H9 step 2 (CPU, no GPU): draw the stratified held-out row population.

DRAFT SKELETON. Reconstructs the 16,834-row complement (AH union pool minus AL's
1,662-row fit surface) by pure set arithmetic on two on-disk JSONL files, then
draws a fixed-seed stratified sample matching the fit surface's per-source mix.

Recovery is verified in docs/review/h9-holdout-candidate-inventory-2026-07-10.md:
  union = row_keys(orig_rows) U row_keys(expansion_rows)  == 18,496 (disjoint
    namespaces ah::... / ahx::...)
  complement = union - row_keys(fit_surface)              == 16,834
No classifier refit, no GPU. Stratification targets come from cell.yaml
(holdout.stratify_targets), which sum to draw_size (500).

CONTAINMENT: the committed ID-manifest carries ONLY row_key + source + gold
answerability label. Question text, aliases, and any other row content stay out
of the committed file (they live only in the gitignored source JSONLs). See
AMENDMENT.md section 4 and .gitignore.

Output:
  analysis-committed/holdout_draw/holdout_ids.jsonl  (row_key, source, gold_label)
  analysis-committed/holdout_draw/draw_manifest.json (seed, per-source counts,
    complement census, sha256 of the two source files, zero-collision assertion)

Usage:
  python draw_holdout.py --cell cell.yaml
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml


def load_row_keys(path: Path) -> dict[str, dict]:
    """row_key -> {source, label} for every row in a JSONL. TODO(sign): wire."""
    raise NotImplementedError


def draw(cell: dict) -> dict:
    """Reconstruct the complement and draw the stratified sample.

    TODO(sign): concrete steps, verified against the holdout inventory memo:
      1. orig = load_row_keys(orig_rows); exp = load_row_keys(expansion_rows)
         assert keys(orig) & keys(exp) == empty  (disjoint namespaces)
         union = {**orig, **exp}; assert len(union) == 18496
      2. fit = row_keys(fit_surface); assert fit <= keys(union) (zero orphans)
         complement = {k: v for k, v in union.items() if k not in fit}
         assert len(complement) == 16834
      3. group complement by source; for each source draw the cell.yaml target
         count with numpy default_rng(cell['seed']), without replacement; assert
         every target <= available supply.
      4. write holdout_ids.jsonl (row_key + source + gold label ONLY) and
         draw_manifest.json (seed, per-source counts, sha256 of both source
         files, complement census, and the exact-text zero-collision assertion
         restated from the memo).
    """
    raise NotImplementedError(
        "draw_holdout draft skeleton: wire the set arithmetic + stratified draw "
        "per the TODO(sign) block; recovery is specified in "
        "docs/review/h9-holdout-candidate-inventory-2026-07-10.md."
    )


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cell", default="cell.yaml")
    args = ap.parse_args()
    cell = yaml.safe_load(Path(args.cell).read_text())
    manifest = draw(cell)
    print(json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
