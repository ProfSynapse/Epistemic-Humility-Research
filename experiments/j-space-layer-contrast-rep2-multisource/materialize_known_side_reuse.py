#!/usr/bin/env python3
"""Materialize rep1's known_correct_answered rows and anchors for verbatim
reuse in this rep2 experiment.

Locked design: "REUSE rep-1's 1,957 known_correct_answered rows and their
already-extracted anchors verbatim (pre-stated; the cost side was nowhere
near ceiling and reuse saves a full generation pass). Pin by manifest hash."

This is a CPU-only file-copy step (no GPU, no generation, no re-extraction).
It reads rep1's PRIVATE (gitignored) row and anchor files, filters to the
`known_correct_answered` role, and writes a local private copy plus a
committed ID-only provenance manifest recording the source and copy sha256
hashes.

Cross-worktree dependency (recorded, not hidden): as of this writing, rep1's
resolved private artifacts live only in the `jspace-layer-replication`
worktree (branch `agent/jspace-full-run`, PR #263), not in this worktree or
on `main`. If that worktree is deleted before this script has been run once
here, this reuse pin cannot be re-derived without re-running rep1's own
mining and extraction. Run this script (once) before that worktree is
cleaned up.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ANALYSIS = HERE / "analysis"
COMMITTED = HERE / "analysis-committed"

REP1_WORKTREE = Path("/home/profsynapse/code/ehr-worktrees/jspace-layer-replication")
REP1_EXPERIMENT = (
    REP1_WORKTREE / "experiments/j-space-layer-contrast-replication-qwen3-4b"
)
REP1_ROWS = REP1_EXPERIMENT / "analysis" / "fresh_eval_rows.jsonl"
REP1_ANCHORS = REP1_EXPERIMENT / "analysis" / "fresh_anchor_extract.safetensors"

DEFAULT_ROWS_OUT = ANALYSIS / "known_correct_answered_reused.jsonl"
DEFAULT_ANCHORS_OUT = ANALYSIS / "known_correct_answered_anchor_reused.safetensors"
DEFAULT_MANIFEST_OUT = COMMITTED / "known_side_reuse_manifest.json"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def sanitize_key(row_key: str) -> str:
    return row_key.replace(":", "_")


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.open(encoding="utf-8") if line.strip()]


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")


def run(args: argparse.Namespace) -> int:
    rep1_rows_path = Path(args.rep1_rows)
    rep1_anchors_path = Path(args.rep1_anchors)
    if not rep1_rows_path.exists():
        print(f"[materialize-known] ERROR: source rows missing: {rep1_rows_path}", file=sys.stderr)
        return 1
    if not rep1_anchors_path.exists():
        print(f"[materialize-known] ERROR: source anchors missing: {rep1_anchors_path}", file=sys.stderr)
        return 1

    all_rows = load_jsonl(rep1_rows_path)
    known_rows = [r for r in all_rows if r.get("role") == "known_correct_answered"]
    print(
        f"[materialize-known] source rows: total={len(all_rows)} "
        f"known_correct_answered={len(known_rows)}",
        flush=True,
    )

    from safetensors.numpy import load_file, save_file

    source_tensors = load_file(str(rep1_anchors_path))
    wanted_suffixes = {sanitize_key(r["row_key"]) for r in known_rows}
    kept = {
        k: v for k, v in source_tensors.items()
        if k.split("__", 1)[1] in wanted_suffixes
    }
    print(
        f"[materialize-known] source tensors={len(source_tensors)} "
        f"kept (known-side)={len(kept)} (expected {len(known_rows) * 4})",
        flush=True,
    )

    rows_out = Path(args.rows_out)
    anchors_out = Path(args.anchors_out)
    write_jsonl(rows_out, known_rows)
    anchors_out.parent.mkdir(parents=True, exist_ok=True)
    save_file(kept, str(anchors_out))

    manifest = {
        "stage": "j_space_layer_contrast_rep2_multisource_known_side_reuse",
        "reused_from_experiment": "experiments/j-space-layer-contrast-replication-qwen3-4b",
        "reused_from_worktree": str(REP1_WORKTREE),
        "reused_from_branch": "agent/jspace-full-run",
        "source_rows_path": str(rep1_rows_path),
        "source_rows_sha256": sha256_file(rep1_rows_path),
        "source_anchors_path": str(rep1_anchors_path),
        "source_anchors_sha256": sha256_file(rep1_anchors_path),
        "local_rows_path": str(rows_out),
        "local_rows_sha256": sha256_file(rows_out),
        "local_anchors_path": str(anchors_out),
        "local_anchors_sha256": sha256_file(anchors_out),
        "n_known_correct_answered": len(known_rows),
        "n_tensors_kept": len(kept),
        "policy": "ID/count/hash provenance only; no question text or aliases committed.",
    }
    Path(args.manifest_out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.manifest_out).write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps({k: manifest[k] for k in (
        "n_known_correct_answered", "n_tensors_kept",
        "local_rows_sha256", "local_anchors_sha256",
    )}, indent=2))
    return 0


def parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rep1-rows", default=str(REP1_ROWS))
    parser.add_argument("--rep1-anchors", default=str(REP1_ANCHORS))
    parser.add_argument("--rows-out", default=str(DEFAULT_ROWS_OUT))
    parser.add_argument("--anchors-out", default=str(DEFAULT_ANCHORS_OUT))
    parser.add_argument("--manifest-out", default=str(DEFAULT_MANIFEST_OUT))
    return parser.parse_args(argv)


if __name__ == "__main__":
    raise SystemExit(run(parse_args()))
