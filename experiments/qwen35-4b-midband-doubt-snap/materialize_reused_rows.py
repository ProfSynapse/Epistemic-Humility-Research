#!/usr/bin/env python3
"""Reuse the doubt-snap-cross-family-confirmatory qwen35_4b FIT/held-out rows
and role assignments VERBATIM. No re-mining.

Source: Modal volume `eh-doubt-snap-cross-family`, path
`doubt-snap-cross-family-r1/qwen35_4b/analysis/{fit_rows_for_dose,
heldout_rows_for_steer,split_rows_private}.jsonl`, downloaded read-only via
`modal volume get` into this experiment's own gitignored `analysis/from_modal/`
(see NOTEBOOK.md for the exact commands run and their output).

This script:
  1. Verifies the three downloaded files' sha256 against what was recorded at
     download time (fails loudly on drift -- these are frozen source files,
     never re-derived).
  2. Builds this experiment's own local FIT working file
     (`analysis/fit_rows_for_anchor.jsonl`, gitignored, contains question
     text -- never committed) covering confab FIT (887) + known_correct_
     answered FIT (240) + unknown_refused (181, role fit_only) = 1308 rows,
     matching doubt-snap-cross-family-confirmatory's AMENDMENT.md /
     g0_prep_summary.json counts exactly.
  3. Writes the public, ID-only provenance manifest
     (`analysis-committed/reused_rows_manifest.json`): row_key + role + split
     + source + category_canon only -- no question text, no aliases, no
     answer text, per this repo's containment convention.
  4. Held-out rows (1,692: 1,332 confab + 360 known_correct_answered) are
     copied byte-for-byte into `analysis/from_modal/` (already done by the
     download step) and are NOT touched by any fitting/extraction script in
     this amendment -- this is FIT-side dose-window characterization only.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
FROM_MODAL = HERE / "analysis" / "from_modal"
COMMITTED = HERE / "analysis-committed"

SOURCE_VOLUME = "eh-doubt-snap-cross-family"
SOURCE_PATH_PREFIX = "doubt-snap-cross-family-r1/qwen35_4b/analysis"

# Recorded at download time (2026-07-10); this script re-verifies against
# these pinned hashes rather than trusting whatever is on disk.
EXPECTED_SHA256 = {
    "fit_rows_for_dose.jsonl": "42db19f07d61075a2a57d0d53d23d333aa1565931cfce778b08e63f5392afe5f",
    "heldout_rows_for_steer.jsonl": "aa9c52949e468bbc3af63cffd2d80466cfd7f237659406f49cd6bcd8a4324745",
    "split_rows_private.jsonl": "42659f4019d0cbe0178bddd6a7e6323299555092ecd8da4c9ac5d58e42b15a58",
}


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


def main() -> int:
    for fname, expected in EXPECTED_SHA256.items():
        p = FROM_MODAL / fname
        if not p.exists():
            raise SystemExit(f"missing downloaded source file: {p}")
        actual = _sha256_file(p)
        if actual != expected:
            raise SystemExit(
                f"sha256 MISMATCH for {fname}: expected {expected}, got {actual}. "
                "Refusing to proceed on a source file that has drifted from the "
                "recorded download."
            )
        print(f"[materialize] verified sha256 {fname} = {actual}", flush=True)

    split_rows = load_jsonl(FROM_MODAL / "split_rows_private.jsonl")
    fit_confab = [r for r in split_rows if r["role"] == "confab" and r.get("split") == "fit"]
    fit_known = [
        r for r in split_rows
        if r["role"] == "known_correct_answered" and r.get("split") == "fit"
    ]
    unknown_refused = [r for r in split_rows if r["role"] == "unknown_refused"]
    held_confab = [r for r in split_rows if r["role"] == "confab" and r.get("split") == "held_out"]
    held_known = [
        r for r in split_rows
        if r["role"] == "known_correct_answered" and r.get("split") == "held_out"
    ]

    counts = {
        "confab_fit": len(fit_confab),
        "known_correct_answered_fit": len(fit_known),
        "unknown_refused_fit_only": len(unknown_refused),
        "confab_held_out": len(held_confab),
        "known_correct_answered_held_out": len(held_known),
        "total": len(split_rows),
    }
    print(f"[materialize] counts: {counts}", flush=True)

    expected_counts = {
        "confab_fit": 887,
        "known_correct_answered_fit": 240,
        "unknown_refused_fit_only": 181,
        "confab_held_out": 1332,
        "known_correct_answered_held_out": 360,
        "total": 3000,
    }
    if counts != expected_counts:
        raise SystemExit(
            f"row counts do not match doubt-snap-cross-family-confirmatory's "
            f"registered qwen35_4b g0_prep_summary counts: got {counts}, "
            f"expected {expected_counts}"
        )

    fit_working = fit_confab + fit_known + unknown_refused
    fit_working.sort(key=lambda r: (r["role"], r.get("split", ""), r["row_key"]))
    write_jsonl(HERE / "analysis" / "fit_rows_for_anchor.jsonl", fit_working)
    print(
        f"[materialize] wrote analysis/fit_rows_for_anchor.jsonl "
        f"({len(fit_working)} rows, question text NOT committed)",
        flush=True,
    )

    def id_only(rows: list[dict]) -> list[dict]:
        return [
            {
                "row_key": r["row_key"],
                "role": r["role"],
                "split": r.get("split"),
                "source": r.get("source"),
                "category_canon": r.get("category_canon"),
            }
            for r in rows
        ]

    manifest = {
        "amendment": "qwen35-4b-midband-doubt-snap",
        "reused_from": {
            "experiment": "doubt-snap-cross-family-confirmatory",
            "cell_id": "qwen35_4b",
            "modal_volume": SOURCE_VOLUME,
            "modal_path_prefix": SOURCE_PATH_PREFIX,
            "download_method": "modal volume get (read-only)",
            "source_file_sha256": EXPECTED_SHA256,
        },
        "reuse_scope": (
            "FIT rows and role assignments reused VERBATIM, no re-mining. "
            "Held-out rows are recorded here for provenance completeness only "
            "and are NOT used by any script in this amendment (FIT-side "
            "dose-window characterization only; held-out is reserved for a "
            "future signed held-out stage)."
        ),
        "counts": counts,
        "rows": {
            "confab_fit": id_only(fit_confab),
            "known_correct_answered_fit": id_only(fit_known),
            "unknown_refused_fit_only": id_only(unknown_refused),
            "confab_held_out": id_only(held_confab),
            "known_correct_answered_held_out": id_only(held_known),
        },
    }
    COMMITTED.mkdir(parents=True, exist_ok=True)
    out_path = COMMITTED / "reused_rows_manifest.json"
    out_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"[materialize] wrote {out_path} (ID-only, public-safe)", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
