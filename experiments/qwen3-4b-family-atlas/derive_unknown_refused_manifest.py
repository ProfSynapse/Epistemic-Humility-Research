#!/usr/bin/env python3
"""Derive the `unknown_refused` row-key list this atlas cell's read panel
needs and promote it as an ID-ONLY manifest fragment, WITHOUT touching the
existing promoted manifest at
`experiments/common/doubt-gated-caution-tighten-heldout-split/` (that file
is another cell's committed artifact and is not edited by this script).

Background (see AMENDMENT.md "Design" -> "Row pool" and cell.yaml's KNOWN
GAP comment): `doubt-gated-caution-tighten`'s own
`split_fit_heldout.py` never wrote `unknown_refused` row_keys into its
committed `split_manifest.json` -- that role is fit-only scaffold, never
split, so it never entered the manifest's `rows` list. The row-key list
existed only in a gitignored local file
(`experiments/doubt-gated-caution-tighten/analysis/l34_anchor_extract_manifest.json`)
that is not present anywhere this scaffold could reach.

This script re-derives that list DETERMINISTICALLY from the same private
source pool `extract_l34_anchor.py:99` reads, applying its exact filter
rule (`not r["confab_on_unanswerable"]`), and self-checks the result two
ways before writing anything:

1. Count check: unknown_refused count must equal 1029 (the count already
   recorded in the promoted split_manifest.json's
   `n_unknown_refused_fit_only` field).
2. Cross-check: the SAME source pool's `confab_on_unanswerable == True`
   subset (this script's own row-key set) must equal EXACTLY the `confab`
   row_key set already committed in the promoted split_manifest.json. This
   proves the source pool this script fetched is the same pool
   `doubt-gated-caution-tighten` originally extracted from, not a
   similar-looking coincidence.

Containment: the source pool's `question` field (and every other row field
except `row_key` and `confab_on_unanswerable`) is read into memory
transiently to compute the filter and cross-check, and is NEVER written to
this script's output. The output manifest carries `row_key`, `role`,
`split` only -- the same minimal schema the promoted split_manifest.json
already uses.

Usage:
  python derive_unknown_refused_manifest.py
    (writes unknown_refused_manifest.json in this experiment directory)
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROMOTED_MANIFEST_PATH = (
    HERE.parent / "common" / "doubt-gated-caution-tighten-heldout-split"
    / "split_manifest.json"
)
OUT_PATH = HERE / "unknown_refused_manifest.json"

STAGING_REPO = "professorsynapse/eh-al-prep-staging"
POOL_IN_REPO = "pools/ak_stage1_pool.jsonl"

EXPECTED_UNKNOWN_REFUSED_COUNT = 1029


def load_jsonl(p: Path) -> list[dict]:
    return [json.loads(ln) for ln in p.open(encoding="utf-8") if ln.strip()]


def fetch_pool() -> Path:
    from huggingface_hub import hf_hub_download

    p = hf_hub_download(repo_id=STAGING_REPO, filename=POOL_IN_REPO, repo_type="dataset")
    return Path(p)


def main() -> int:
    if not PROMOTED_MANIFEST_PATH.is_file():
        print(f"[derive] ERROR: promoted manifest not found at {PROMOTED_MANIFEST_PATH}",
              file=sys.stderr)
        return 1
    promoted = json.loads(PROMOTED_MANIFEST_PATH.read_text())
    promoted_confab_keys = {
        r["row_key"] for r in promoted["rows"] if r["role"] == "confab"
    }
    print(f"[derive] promoted manifest confab count: {len(promoted_confab_keys)}")
    print(f"[derive] promoted manifest n_unknown_refused_fit_only: "
          f"{promoted.get('n_unknown_refused_fit_only')}")

    pool_path = fetch_pool()
    print(f"[derive] fetched source pool -> {pool_path}")
    pool_sha256 = hashlib.sha256(pool_path.read_bytes()).hexdigest()
    pool_rows = load_jsonl(pool_path)
    print(f"[derive] source pool rows: {len(pool_rows)}")

    # Exact filter rule from extract_l34_anchor.py:99-100 (doubt-gated-caution-tighten).
    unknown_refused_rows = [r for r in pool_rows if not r["confab_on_unanswerable"]]
    confab_rows = [r for r in pool_rows if r["confab_on_unanswerable"]]
    unknown_refused_keys = [r["row_key"] for r in unknown_refused_rows]
    pool_confab_keys = {r["row_key"] for r in confab_rows}

    print(f"[derive] derived unknown_refused count: {len(unknown_refused_keys)}")
    print(f"[derive] derived confab count: {len(pool_confab_keys)}")

    # Integrity check 1: unique row_keys, no duplicates.
    assert len(set(unknown_refused_keys)) == len(unknown_refused_keys), (
        "unknown_refused row_keys are not unique"
    )

    # Integrity check 2: count matches the promoted manifest's own recorded count.
    assert len(unknown_refused_keys) == EXPECTED_UNKNOWN_REFUSED_COUNT, (
        f"derived unknown_refused count {len(unknown_refused_keys)} != "
        f"expected {EXPECTED_UNKNOWN_REFUSED_COUNT} (promoted manifest's "
        f"n_unknown_refused_fit_only)"
    )
    assert len(unknown_refused_keys) == promoted.get("n_unknown_refused_fit_only"), (
        "derived unknown_refused count does not match promoted manifest's "
        "own n_unknown_refused_fit_only field"
    )

    # Integrity check 3 (the real proof this is the SAME source pool
    # doubt-gated-caution-tighten originally extracted from): the pool's own
    # confab_on_unanswerable==True row-key set must equal EXACTLY the confab
    # row-key set already committed in the promoted split_manifest.json.
    assert pool_confab_keys == promoted_confab_keys, (
        "derived confab row_key set does NOT match the promoted manifest's "
        "confab row_key set -- this pool snapshot is not the same source "
        "doubt-gated-caution-tighten used; refusing to write unknown_refused_manifest.json"
    )
    print("[derive] cross-check PASSED: derived confab row_key set is byte-identical "
          "(as a set) to the promoted manifest's committed confab row_key set.")

    rows_out = [
        {"row_key": rk, "role": "unknown_refused", "split": "fit_only"}
        for rk in sorted(unknown_refused_keys)
    ]

    out = {
        "schema": "row_key/role/split only -- no question text, no answers, no aliases",
        "role": "unknown_refused",
        "split": "fit_only",
        "n_rows": len(rows_out),
        "derivation": {
            "source_repo": STAGING_REPO,
            "source_file_in_repo": POOL_IN_REPO,
            "source_file_local_path": str(pool_path),
            "source_file_sha256": pool_sha256,
            "rule": "unknown_refused = [r for r in ak_stage1_pool if not r['confab_on_unanswerable']]",
            "rule_citation": "experiments/doubt-gated-caution-tighten/extract_l34_anchor.py:99",
            "cross_check": (
                "derived confab_on_unanswerable==True row_key set (n="
                f"{len(pool_confab_keys)}) verified byte-identical (as a set) to "
                "the promoted split_manifest.json's committed confab row_key set "
                f"(n={len(promoted_confab_keys)}), proving this is the same source "
                "pool snapshot doubt-gated-caution-tighten originally extracted from."
            ),
            "promoted_manifest_path": str(
                PROMOTED_MANIFEST_PATH.relative_to(HERE.parent.parent)
            ),
            "promoted_manifest_n_unknown_refused_fit_only": promoted.get(
                "n_unknown_refused_fit_only"
            ),
        },
        "rows": rows_out,
    }
    OUT_PATH.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"[derive] WROTE {OUT_PATH} ({len(rows_out)} rows)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
