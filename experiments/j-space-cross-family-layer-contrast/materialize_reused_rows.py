#!/usr/bin/env python3
"""Materialize a family's REUSED doubt-snap eval pool + FIT/HELD-OUT split.

Sign-time revision (2026-07-23): this experiment consumes
`doubt-snap-cross-family-confirmatory`'s resolved per-family artifacts instead
of mining/splitting its own pool for the four reused families. This script is
the family-aware analog of
`experiments/qwen35-4b-midband-doubt-snap/materialize_reused_rows.py`.

What it does (all CPU-only; no GPU, no model load):

  1. VERIFY (always, runnable now): re-hash the doubt-snap committed
     `split_manifest.json` for this family's cell and assert it matches the
     sha256 pinned in `families/<slug>.yaml` `reuse.doubt_snap.artifacts.
     split_manifest.sha256`. Refuses to proceed on drift.
  2. COPY the verified ID-only split into this experiment's own
     `analysis-committed/<family>/split_manifest.json` -- the exact input the
     rest of the pipeline (`pipeline.load_rows`, `build_directions.py`,
     `gate_fit.py`) already expects. No re-splitting.
  3. Emit the public ID-only `analysis-committed/<family>/reused_rows_manifest.json`
     (row_key + role + split + source + category_canon only; never question
     text, aliases, or answer text) with counts and the pinned provenance.
  4. ROW TEXT: the private question/alias/generation text lives on the Modal
     volume `eh-doubt-snap-cross-family` (committed artifacts are ID-only). It
     is NOT pulled by this script by default (needs the `modal` CLI + auth); the
     script PRINTS the exact `modal volume get` command to run, and if the
     pulled file is already present under `analysis/<family>/from_doubt_snap/`
     it verifies + normalizes it into the gitignored `analysis/<family>/
     eval_rows.jsonl` the fitting/extraction scripts read.

This supersedes `mine_eval_pool.py` + `split_fit_heldout.py` for the reused
families (those are retained only as a lead-authorized fallback if a family's
Modal row text is gone).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from family_config import (  # noqa: E402
    FAMILY_SLUGS, load_family, reuse_block, reuse_artifact_path, reuse_artifact_sha256,
)


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(ln) for ln in path.open(encoding="utf-8") if ln.strip()]


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")


def verify_committed_artifacts(cfg: dict) -> dict[str, str]:
    """Re-hash every pinned doubt-snap committed artifact for this family and
    assert it matches the recorded sha256. Returns {name: sha256}."""
    rb = reuse_block(cfg)
    if not rb:
        raise SystemExit(f"[{cfg['family']}] no reuse.doubt_snap block; nothing to materialize")
    verified: dict[str, str] = {}
    for name in ("split_manifest", "build_manifest", "c_hat", "u_d",
                 "random_direction", "gate_fit", "dose_fit", "g0_prep_summary"):
        pinned = reuse_artifact_sha256(cfg, name)
        path = reuse_artifact_path(cfg, name)
        if pinned is None or path is None:
            # e.g. gemma's absent dose_fit -- recorded null, not an error.
            print(f"[materialize:{cfg['family']}] artifact {name!r}: not pinned (absent) -- skipped")
            continue
        if not path.is_file():
            raise SystemExit(f"[{cfg['family']}] pinned artifact missing on disk: {path}")
        actual = _sha256_file(path)
        if actual != pinned:
            raise SystemExit(
                f"[{cfg['family']}] sha256 MISMATCH for {name}: pinned {pinned}, got {actual}. "
                "Refusing to reuse a doubt-snap artifact that drifted from its pin."
            )
        print(f"[materialize:{cfg['family']}] verified {name} sha256 = {actual}")
        verified[name] = actual
    return verified


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--family", required=True, choices=FAMILY_SLUGS)
    args = ap.parse_args(argv)
    family = args.family
    cfg = load_family(family)
    rb = reuse_block(cfg)
    if not rb:
        raise SystemExit(f"[{family}] no reuse.doubt_snap block; use mine_eval_pool.py fallback")

    verified = verify_committed_artifacts(cfg)

    # (2) Copy the verified ID-only split into this experiment's committed dir.
    committed = HERE / "analysis-committed" / family
    committed.mkdir(parents=True, exist_ok=True)
    src_split = reuse_artifact_path(cfg, "split_manifest")
    split_data = json.loads(src_split.read_text())
    (committed / "split_manifest.json").write_text(json.dumps(split_data, indent=2))

    rows = split_data["rows"]
    role_split = Counter((r["role"], r.get("split")) for r in rows)
    counts = {f"{role}:{split}": n for (role, split), n in sorted(role_split.items())}
    print(f"[materialize:{family}] split counts: {counts}")

    # Sanity: the reused counts must match the pinned reuse.pool_counts.
    expected = rb.get("pool_counts", {})
    got = {
        "confab_fit": role_split[("confab", "fit")],
        "known_correct_answered_fit": role_split[("known_correct_answered", "fit")],
        "confab_held_out": role_split[("confab", "held_out")],
        "known_correct_answered_held_out": role_split[("known_correct_answered", "held_out")],
    }
    for k, v in expected.items():
        if k in got and got[k] != v:
            raise SystemExit(
                f"[{family}] reused split count {k}={got[k]} disagrees with pinned "
                f"reuse.pool_counts.{k}={v}; refusing to proceed on a drifted split."
            )

    # (3) Public ID-only reused-rows manifest.
    id_only = [
        {"row_key": r["row_key"], "role": r["role"], "split": r.get("split"),
         "source": r.get("source"), "category_canon": r.get("category_canon")}
        for r in rows
    ]
    manifest = {
        "family": family,
        "reused_from": {
            "experiment": rb["experiment"], "cell": rb["cell"],
            "committed_dir": rb["committed_dir"], "revision": rb["revision"],
        },
        "verified_sha256": verified,
        "counts": got,
        "rows": id_only,
        "note": "IDs only; question/alias/answer text stays on the Modal volume "
                "eh-doubt-snap-cross-family and in gitignored analysis/, never committed.",
    }
    (committed / "reused_rows_manifest.json").write_text(json.dumps(manifest, indent=2))
    print(f"[materialize:{family}] wrote reused_rows_manifest.json ({len(id_only)} rows)")

    # (4) Row text: verify+normalize if already pulled; else print the command.
    from_modal_dir = HERE / "analysis" / family / "from_doubt_snap"
    src_rows_file = from_modal_dir / "split_rows_private.jsonl"
    if src_rows_file.is_file():
        private = load_jsonl(src_rows_file)
        by_key = {r["row_key"]: r for r in private}
        missing = [r["row_key"] for r in rows if r["row_key"] not in by_key]
        if missing:
            raise SystemExit(
                f"[{family}] pulled row text is missing {len(missing)} row_keys present "
                f"in the split manifest (first: {missing[:3]}); refusing partial materialization."
            )
        # Normalize into the eval_rows.jsonl the fitting/extraction scripts read,
        # carrying the split's role/category labels alongside the private text.
        eval_rows = []
        for r in rows:
            src = by_key[r["row_key"]]
            merged = dict(src)
            merged["role"] = r["role"]
            merged["category_canon"] = r.get("category_canon")
            eval_rows.append(merged)
        write_jsonl(HERE / "analysis" / family / "eval_rows.jsonl", eval_rows)
        print(f"[materialize:{family}] normalized {len(eval_rows)} rows -> analysis/{family}/eval_rows.jsonl")
    else:
        vol = rb["modal_volume"]
        prefix = rb["modal_path_prefix"]
        print(
            f"\n[materialize:{family}] ROW TEXT NOT YET PULLED. Run (read-only):\n"
            f"  modal volume get {vol} \\\n"
            f"    {prefix}/split_rows_private.jsonl \\\n"
            f"    {from_modal_dir}/split_rows_private.jsonl\n"
            f"then re-run this script to normalize it into analysis/{family}/eval_rows.jsonl.\n"
            "(Split manifest is already verified + copied; only the private text remains.)"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
