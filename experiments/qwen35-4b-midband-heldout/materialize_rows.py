#!/usr/bin/env python3
"""qwen35-4b-midband-heldout -- materialize the held-out row pool.
CPU-only, no GPU, no fresh mining.

Per AMENDMENT.md "Population": the held-out rows are materialized the same
way the ladder materialized its FIT rows -- a read-only, sha256-verified
pull of the source file from the Modal volume `eh-doubt-snap-cross-family`
(`doubt-snap-cross-family-r1/qwen35_4b/analysis/heldout_rows_for_steer.jsonl`),
which is the SAME file the ladder's own `materialize_reused_rows.py` already
downloaded and sha256-verified at ladder build time (its
`EXPECTED_SHA256["heldout_rows_for_steer.jsonl"]`, read in full before
writing this) -- reused here byte-for-byte, no second network pull needed
when that download already exists on disk somewhere reachable via
--source-path.

This script:
  1. Resolves the source file: --source-path if given, else attempts
     `modal volume get` (network) into this experiment's own gitignored
     `analysis/from_modal/`.
  2. sha256-verifies it against the pinned hash (fails loudly on drift --
     this is a frozen source file, never re-derived).
  3. Asserts role/split counts equal 1,332 confab held_out + 360
     known_correct_answered held_out = 1,692 exactly, matching the ladder's
     `reused_rows_manifest.json` counts block and the fleet's registered
     qwen35_4b held-out counts.
  4. Writes this experiment's own local private working file
     (`analysis/heldout_rows_for_steer.jsonl`, gitignored, contains question
     text -- never committed), STRIPPED of the source file's own stale
     fire-decision fields (score_neg_z_d/z_d/tau/fire/baseline_terminated_
     naturally): those are a DIFFERENT instrument's artifacts (the fleet's
     own gate, fit at a different layer with a different tau) and this
     experiment computes its OWN fresh fire decision at hs20 via
     `capture_anchors.py`, never inherited from the source file.
  5. Writes the public, ID-only provenance manifest
     (`analysis-committed/heldout_rows_manifest.json`): row_key + role +
     split + source + category_canon only -- no question text, no aliases,
     no answer text, per this repo's containment convention.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ANALYSIS = HERE / "analysis"
COMMITTED = HERE / "analysis-committed"
FROM_MODAL = ANALYSIS / "from_modal"

SOURCE_VOLUME = "eh-doubt-snap-cross-family"
SOURCE_PATH = "doubt-snap-cross-family-r1/qwen35_4b/analysis/heldout_rows_for_steer.jsonl"
# Recorded by the ladder's own materialize_reused_rows.py at its 2026-07-10
# download; this is the SAME source file, reused verbatim, not re-derived.
EXPECTED_SHA256 = "aa9c52949e468bbc3af63cffd2d80466cfd7f237659406f49cd6bcd8a4324745"

EXPECTED_COUNTS = {
    "confab": 1332,
    "known_correct_answered": 360,
    "total": 1692,
}

OUT_ROWS = ANALYSIS / "heldout_rows_for_steer.jsonl"
OUT_MANIFEST = COMMITTED / "heldout_rows_manifest.json"

STALE_FLEET_FIELDS = ("score_neg_z_d", "z_d", "tau", "fire", "baseline_terminated_naturally")


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")


def resolve_source(source_path: str | None) -> Path:
    if source_path:
        p = Path(source_path)
        if not p.is_file():
            raise SystemExit(f"--source-path {p} does not exist")
        return p

    default_dest = FROM_MODAL / "heldout_rows_for_steer.jsonl"
    if default_dest.is_file():
        return default_dest

    print(
        f"[materialize] {default_dest} not found locally; attempting "
        f"`modal volume get {SOURCE_VOLUME} {SOURCE_PATH}` (network)...",
        file=sys.stderr,
    )
    FROM_MODAL.mkdir(parents=True, exist_ok=True)
    try:
        subprocess.run(
            ["modal", "volume", "get", SOURCE_VOLUME, SOURCE_PATH, str(default_dest)],
            check=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError) as exc:
        raise SystemExit(
            f"[materialize] could not fetch {SOURCE_PATH!r} from Modal volume "
            f"{SOURCE_VOLUME!r} ({exc}). Pass --source-path pointing at an "
            "already-downloaded copy of heldout_rows_for_steer.jsonl (e.g. the "
            "ladder's own analysis/from_modal/ copy from its "
            "materialize_reused_rows.py run), or run `modal volume get` "
            "manually first."
        ) from exc
    if not default_dest.is_file():
        raise SystemExit(f"[materialize] modal volume get did not produce {default_dest}")
    return default_dest


def strip_stale_fleet_fields(row: dict) -> dict:
    return {k: v for k, v in row.items() if k not in STALE_FLEET_FIELDS}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument(
        "--source-path", default=None,
        help="path to an already-downloaded heldout_rows_for_steer.jsonl "
             "(same sha256 as the ladder's own download); skips the Modal pull",
    )
    args = ap.parse_args(argv)

    source = resolve_source(args.source_path)
    actual_sha = _sha256_file(source)
    if actual_sha != EXPECTED_SHA256:
        raise SystemExit(
            f"[materialize] sha256 MISMATCH for {source}: expected "
            f"{EXPECTED_SHA256}, got {actual_sha}. Refusing to proceed on a "
            "source file that has drifted from the ladder's recorded download."
        )
    print(f"[materialize] verified sha256 {source} = {actual_sha}", flush=True)

    rows = load_jsonl(source)
    held_confab = [r for r in rows if r.get("role") == "confab" and r.get("split") == "held_out"]
    held_known = [r for r in rows if r.get("role") == "known_correct_answered" and r.get("split") == "held_out"]
    other = [r for r in rows if r not in held_confab and r not in held_known]
    counts = {"confab": len(held_confab), "known_correct_answered": len(held_known), "total": len(held_confab) + len(held_known)}
    print(f"[materialize] counts: {counts} (source file also had {len(other)} non-held-out/other rows, ignored)", flush=True)

    if counts != EXPECTED_COUNTS:
        raise SystemExit(
            f"[materialize] row-count mismatch vs the ladder's reused_rows_manifest.json "
            f"and the fleet's registered qwen35_4b held-out counts: got {counts}, "
            f"expected {EXPECTED_COUNTS}"
        )

    n_missing_q = sum(1 for r in held_confab + held_known if not r.get("question"))
    n_missing_alias_known = sum(1 for r in held_known if not r.get("aliases"))
    if n_missing_q:
        raise SystemExit(f"[materialize] {n_missing_q} held-out rows have no question text")
    if n_missing_alias_known:
        raise SystemExit(
            f"[materialize] {n_missing_alias_known} known_correct_answered held-out rows "
            "have empty aliases; correctness/refusal grading on those rows would be unreliable"
        )

    held_all = held_confab + held_known
    held_all.sort(key=lambda r: (r["role"], r["row_key"]))
    working_rows = [strip_stale_fleet_fields(r) for r in held_all]

    ANALYSIS.mkdir(parents=True, exist_ok=True)
    write_jsonl(OUT_ROWS, working_rows)
    print(f"[materialize] wrote {OUT_ROWS} ({len(working_rows)} rows, question text NOT committed)", flush=True)

    def id_only(rs: list[dict]) -> list[dict]:
        return [
            {
                "row_key": r["row_key"], "role": r["role"], "split": r.get("split"),
                "source": r.get("source"), "category_canon": r.get("category_canon"),
            }
            for r in rs
        ]

    manifest = {
        "amendment": "qwen35-4b-midband-heldout",
        "reused_from": {
            "experiment": "doubt-snap-cross-family-confirmatory",
            "cell_id": "qwen35_4b",
            "modal_volume": SOURCE_VOLUME,
            "modal_path": SOURCE_PATH,
            "download_method": "modal volume get (read-only) or reuse of the ladder's own prior download",
            "source_file_sha256": EXPECTED_SHA256,
        },
        "reuse_scope": (
            "Held-out rows and role assignments reused VERBATIM from the fleet's "
            "qwen35_4b cell (via the ladder's own materialize_reused_rows.py "
            "provenance chain). This experiment strips the source file's stale "
            "fleet-instrument fire-decision fields (score_neg_z_d/z_d/tau/fire) "
            "and computes its OWN fresh fire decision at hs20 (capture_anchors.py "
            "+ pipeline.py), never inheriting the fleet's gate decision."
        ),
        "counts": counts,
        "rows": {
            "confab_held_out": id_only(held_confab),
            "known_correct_answered_held_out": id_only(held_known),
        },
    }
    COMMITTED.mkdir(parents=True, exist_ok=True)
    OUT_MANIFEST.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"[materialize] wrote {OUT_MANIFEST} (ID-only, public-safe)", flush=True)

    # No question text, aliases, or answer text anywhere under analysis-committed/.
    committed_blob = OUT_MANIFEST.read_text(encoding="utf-8")
    for r in held_all:
        if r.get("question") and r["question"] in committed_blob:
            raise SystemExit("[materialize] question text leaked into the committed manifest -- aborting")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
