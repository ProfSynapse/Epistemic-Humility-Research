#!/usr/bin/env python3
"""idk-switch-naming-confirmatory -- materialize question/alias text for the
400 registered P_CONFAB rows this cell reuses. CPU-only, no GPU.

Per AMENDMENT.md "Design": "Rows: the same 400 registered P_CONFAB rows
(source kuq_unknowns_all), disclosed as spent for exploratory purposes; the
fresh generations have never been sampled, screened, or graded." The row_key
population is NOT re-drawn here -- it is read verbatim from the naming
battery's own committed, disjointness-checked ID manifest:
`experiments/write-direction-naming-battery/analysis-committed/populations/p_confab_ids.json`
(400 row_keys, no question/alias text -- safe to read, committed).

This script only joins those 400 row_keys to their question/alias text and
writes a single gitignored working file (`analysis/isnc_rows.jsonl`, contains
question text -- never committed). Two text sources are tried in order, ported
from `write-direction-naming-battery/materialize_rows.py` (source sha256
fcf1c7be1a30fc836d80fbe1d2d48abc118f3a49103c978c968910a79f898538, matching
that file's own pin):

  1. PREFERRED: the naming battery's own already-materialized working file
     (`experiments/write-direction-naming-battery/analysis/naming_battery_rows.jsonl`,
     gitignored), filtered to `population == "P_CONFAB"`. This is the most
     direct join available -- it reuses the naming battery's own already-
     verified text rather than re-deriving the row_key -> raw-dataset-line
     mapping a second time.
  2. FALLBACK (used only if source 1's file is not present on this machine,
     e.g. the naming battery's worktree scratch was cleaned up): the same
     heldout-rows join the naming battery itself used --
     `qwen35-4b-midband-heldout`'s own materialized
     `analysis/heldout_rows_for_steer.jsonl`, which covers the full 1,332-row
     confab_held_out pool P_CONFAB's 400 rows are a verified subset of.

Also re-verifies (belt-and-suspenders, cheap) that the loaded row_key set
matches the committed manifest exactly (count and set-equality) and that
every row_key resolves to non-empty question text, before writing anything.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[1]
ANALYSIS = HERE / "analysis"

NAMING_BATTERY_DIR = REPO_ROOT / "experiments" / "write-direction-naming-battery"
P_CONFAB_IDS_PATH = NAMING_BATTERY_DIR / "analysis-committed" / "populations" / "p_confab_ids.json"

# Source 1 (preferred): the naming battery's own already-materialized working
# file. Gitignored, main-checkout-local; may not exist in a fresh worktree.
DEFAULT_NAMING_BATTERY_ROWS_PATH = NAMING_BATTERY_DIR / "analysis" / "naming_battery_rows.jsonl"

# Source 2 (fallback): same join the naming battery's own materialize_rows.py
# uses for P_CONFAB. Path is main-checkout-local (gitignored data, not a git
# artifact); override with --heldout-rows-path if unavailable.
DEFAULT_HELDOUT_ROWS_PATH = Path(
    "/home/profsynapse/code/Epistemic-Humility-Research/experiments/qwen35-4b-midband-heldout/analysis/heldout_rows_for_steer.jsonl"
)

OUT_ROWS = ANALYSIS / "isnc_rows.jsonl"


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


def load_p_confab_ids() -> list[str]:
    payload = json.loads(P_CONFAB_IDS_PATH.read_text())
    return payload["row_keys"]


def try_source_1(row_keys: set[str], path: Path) -> dict[str, dict] | None:
    if not path.is_file():
        return None
    rows = load_jsonl(path)
    by_key = {r["row_key"]: r for r in rows if r.get("population") == "P_CONFAB"}
    if not row_keys.issubset(by_key.keys()):
        missing = sorted(row_keys - by_key.keys())
        print(
            f"[materialize] source 1 ({path}) is missing {len(missing)} of the "
            f"400 registered P_CONFAB row_keys (first: {missing[:5]}); falling "
            "back to source 2.",
            file=sys.stderr,
        )
        return None
    return by_key


def try_source_2(row_keys: set[str], path: Path) -> dict[str, dict]:
    if not path.is_file():
        raise SystemExit(
            f"[materialize] neither source is available: source 1 "
            f"({DEFAULT_NAMING_BATTERY_ROWS_PATH}) missing or incomplete, and "
            f"source 2 fallback ({path}) not found. Pass "
            "--heldout-rows-path pointing at qwen35-4b-midband-heldout's own "
            "materialized analysis/heldout_rows_for_steer.jsonl (gitignored "
            "working file)."
        )
    heldout_rows = {r["row_key"]: r for r in load_jsonl(path)}
    missing = sorted(row_keys - heldout_rows.keys())
    if missing:
        raise SystemExit(
            f"[materialize] {len(missing)} P_CONFAB row_keys not found in "
            f"{path} (first: {missing[:5]})"
        )
    return heldout_rows


def main(argv: list[str] | None = None) -> int:
    import argparse

    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--naming-battery-rows-path", default=str(DEFAULT_NAMING_BATTERY_ROWS_PATH))
    ap.add_argument("--heldout-rows-path", default=str(DEFAULT_HELDOUT_ROWS_PATH))
    args = ap.parse_args(argv)

    p_confab = load_p_confab_ids()
    assert len(p_confab) == 400, f"P_CONFAB expected 400 row_keys in the committed manifest, got {len(p_confab)}"
    row_keys = set(p_confab)
    assert len(row_keys) == 400, "P_CONFAB committed manifest row_keys are not unique"

    source_1_path = Path(args.naming_battery_rows_path)
    by_key = try_source_1(row_keys, source_1_path)
    source_used = "naming_battery_materialized_rows"
    if by_key is None:
        by_key = try_source_2(row_keys, Path(args.heldout_rows_path))
        source_used = "heldout_rows_for_steer_fallback"

    out_rows: list[dict] = []
    for rk in p_confab:
        hr = by_key[rk]
        out_rows.append({
            "row_key": rk,
            "role": "confab",
            "population": "P_CONFAB",
            "source": hr.get("source", "kuq_unknowns_all"),
            "category_canon": hr.get("category_canon"),
            "question": hr["question"],
            "aliases": hr.get("aliases") or [],
        })

    n_empty_q = sum(1 for r in out_rows if not r.get("question"))
    if n_empty_q:
        raise SystemExit(f"[materialize] {n_empty_q} rows resolved to empty question text")

    out_rows.sort(key=lambda r: r["row_key"])
    write_jsonl(OUT_ROWS, out_rows)
    print(f"[materialize] wrote {OUT_ROWS} ({len(out_rows)} rows, source={source_used})", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
