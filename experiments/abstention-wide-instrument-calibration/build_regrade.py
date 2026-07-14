#!/usr/bin/env python3
"""Build a regrade shard for a CG1-voided shard, per gates.yaml
`on_failure: void_shard_before_unblinding_regrade_once_with_fresh_agent`.

Takes the voided shard's ORIGINAL pool file (bare text, line-aligned with its
id map), re-joins text to id-map entries by line position, and emits the SAME
underlying items (core + both decoy types, unchanged composition) under fresh
opaque ids (regrade_index folded into the id payload) and a fresh shuffle.
No grade from the failed attempt is read or revealed; the regrade shard's
manifest entry is APPENDED to the committed pool manifest, which must be
committed to git BEFORE the fresh grading pass starts.

The original pool's secret salt was never persisted (only its sha256 is
committed), so the regrade shard uses a FRESH secrets.token_hex(32) salt:
unlinkability to the failed attempt is the requirement, and a fresh secret
salt satisfies it strictly; its sha256 is recorded in the manifest entry.

Usage:
  python3 build_regrade.py --shard-id QL_shard_07 --regrade-index 1
"""

from __future__ import annotations

import argparse
import hashlib
import json
import secrets
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import build_adjudication_pool as bap  # noqa: E402

ANALYSIS = HERE / "analysis"
COMMITTED = HERE / "analysis-committed"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--shard-id", required=True)
    ap.add_argument("--regrade-index", type=int, required=True)
    ap.add_argument("--salt", default=None, help="override the fresh random salt (test hook)")
    args = ap.parse_args()

    salt = args.salt or secrets.token_hex(32)
    pool_manifest = json.loads((COMMITTED / "adjudication_pool_manifest.json").read_text(encoding="utf-8"))
    manifest_entry = next((s for s in pool_manifest["shards"] if s["shard_id"] == args.shard_id), None)
    if manifest_entry is None:
        raise SystemExit(f"{args.shard_id} not in committed pool manifest")

    seed = pool_manifest["seed"]
    pool_lines = [json.loads(l) for l in (ANALYSIS / "shards" / f"{args.shard_id}.jsonl").open(encoding="utf-8")]
    id_lines = [json.loads(l) for l in (ANALYSIS / "shards" / f"{args.shard_id}_id_map.jsonl").open(encoding="utf-8")]
    if len(pool_lines) != len(id_lines):
        raise SystemExit("pool/id-map line count mismatch")
    for i, (p, m) in enumerate(zip(pool_lines, id_lines)):
        if p["opaque_id"] != m["opaque_id"]:
            raise SystemExit(f"line {i}: pool/id-map opaque_id mismatch")

    items = [{**m, "text": p["text"]} for p, m in zip(pool_lines, id_lines)]
    # drop the old opaque ids so nothing from the failed pass carries over
    for it in items:
        it.pop("opaque_id", None)

    shard = bap.build_regrade_shard(items, salt, args.regrade_index, seed)
    shard_id = shard["shard_id"]

    pool_path = ANALYSIS / "shards" / f"{shard_id}.jsonl"
    map_path = ANALYSIS / "shards" / f"{shard_id}_id_map.jsonl"
    with pool_path.open("w", encoding="utf-8") as fh:
        for m in shard["id_map"]:
            fh.write(json.dumps({"opaque_id": m["opaque_id"], "text": m["text"]}, ensure_ascii=False) + "\n")
    with map_path.open("w", encoding="utf-8") as fh:
        for m in shard["id_map"]:
            rec = {k: v for k, v in m.items() if k != "text"}
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")

    entry = {
        "shard_id": shard_id,
        "cell": manifest_entry["cell"],
        "regrade_of": args.shard_id,
        "regrade_index": args.regrade_index,
        "regrade_id_salt_sha256": hashlib.sha256(salt.encode("utf-8")).hexdigest(),
        "pool_sha256": hashlib.sha256(pool_path.read_bytes()).hexdigest(),
        "row_count": len(shard["id_map"]),
        "n_core": manifest_entry["n_core"],
        "n_decoy_clear_negative": manifest_entry["n_decoy_clear_negative"],
        "n_decoy_clear_positive": manifest_entry["n_decoy_clear_positive"],
        "opaque_ids": sorted(m["opaque_id"] for m in shard["id_map"]),
    }
    pool_manifest["shards"].append(entry)
    (COMMITTED / "adjudication_pool_manifest.json").write_text(
        json.dumps(pool_manifest, indent=1, sort_keys=True), encoding="utf-8")
    print(f"[build_regrade] wrote {shard_id} ({entry['row_count']} rows), appended to pool manifest; "
          f"COMMIT the manifest to git before dispatching the fresh grader.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
