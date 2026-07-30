#!/usr/bin/env python3
"""write-direction-naming-battery -- materialize question/alias text for the
three committed ID-only populations. CPU-only, no GPU.

Per AMENDMENT.md "Populations", the ID manifests
(`analysis-committed/populations/p_{confab,refuse,known}_ids.json`) are
row_key-only and were committed BEFORE this script runs (G0). This script
joins each row_key to its actual question/aliases text and writes a single
gitignored working file (`analysis/naming_battery_rows.jsonl`, contains
question text -- never committed), analogous to every prior cell's own
materialize_rows.py in this lineage:

  - P_CONFAB (kuq_unknowns_all rows): joined from
    `qwen35-4b-midband-heldout`'s own already-verified, gitignored working
    file (`analysis/heldout_rows_for_steer.jsonl`), which covers the FULL
    1,332-row confab_held_out pool P_CONFAB's 400 rows are a subset of
    (verified: P_CONFAB's row_key set is a strict subset of that file's
    row_key set). That file is itself sha256-chained back to the ladder's
    Modal-pulled source (see heldout's own materialize_rows.py docstring);
    reusing it here avoids re-deriving a row_key -> raw-dataset-line mapping
    (the raw `datasets/kuq/unknowns_all.jsonl` file's row order does NOT
    match the "kuq_unknowns_all:<N>" numeric suffix -- confirmed by direct
    spot check during harness build, so it is not a safe join key on its
    own).
  - P_REFUSE / P_KNOWN (popqa rows): joined directly from
    `datasets/popqa/test.jsonl` by numeric id (the row_key's own numeric
    suffix), aliases from that file's `possible_answers` (a JSON-encoded
    string list).

Also re-verifies (belt-and-suspenders, cheap) that the three committed ID
manifests are still pairwise disjoint and that every row_key resolves to
non-empty question text, before writing anything.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[1]
ANALYSIS = HERE / "analysis"
COMMITTED = HERE / "analysis-committed"
POPULATIONS_DIR = COMMITTED / "populations"

OUT_ROWS = ANALYSIS / "naming_battery_rows.jsonl"

# Reused, not re-derived (see module docstring): the heldout cell's own
# already-verified working file, which covers the full 1,332-row confab_held_out
# pool P_CONFAB is a strict subset of. Path is main-checkout-local (gitignored
# data, not a git artifact); override with --heldout-rows-path if unavailable.
DEFAULT_HELDOUT_ROWS_PATH = Path(
    "/home/profsynapse/code/Epistemic-Humility-Research/experiments/qwen35-4b-midband-heldout/analysis/heldout_rows_for_steer.jsonl"
)
POPQA_PATH = REPO_ROOT / "datasets" / "popqa" / "test.jsonl"


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


def load_population(name: str) -> list[str]:
    payload = json.loads((POPULATIONS_DIR / f"p_{name}_ids.json").read_text())
    return payload["row_keys"]


def main(argv: list[str] | None = None) -> int:
    import argparse

    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--heldout-rows-path", default=str(DEFAULT_HELDOUT_ROWS_PATH))
    args = ap.parse_args(argv)

    p_confab = load_population("confab")
    p_refuse = load_population("refuse")
    p_known = load_population("known")

    assert len(p_confab) == 400, f"P_CONFAB expected 400, got {len(p_confab)}"
    assert len(p_refuse) == 421, f"P_REFUSE expected 421, got {len(p_refuse)}"
    assert len(p_known) == 600, f"P_KNOWN expected 600, got {len(p_known)}"

    s_confab, s_refuse, s_known = set(p_confab), set(p_refuse), set(p_known)
    overlaps = {
        "confab_x_refuse": s_confab & s_refuse,
        "confab_x_known": s_confab & s_known,
        "refuse_x_known": s_refuse & s_known,
    }
    bad = {k: sorted(v) for k, v in overlaps.items() if v}
    if bad:
        raise SystemExit(f"[materialize] committed populations are NOT pairwise disjoint: {bad}")

    heldout_path = Path(args.heldout_rows_path)
    if not heldout_path.is_file():
        raise SystemExit(
            f"[materialize] {heldout_path} not found; pass --heldout-rows-path "
            "pointing at qwen35-4b-midband-heldout's own materialized "
            "analysis/heldout_rows_for_steer.jsonl (gitignored working file)"
        )
    heldout_rows = {r["row_key"]: r for r in load_jsonl(heldout_path)}
    missing_confab = [k for k in p_confab if k not in heldout_rows]
    if missing_confab:
        raise SystemExit(
            f"[materialize] {len(missing_confab)} P_CONFAB row_keys not found in "
            f"{heldout_path} (first: {missing_confab[:5]})"
        )

    popqa_rows = {str(r["id"]): r for r in load_jsonl(POPQA_PATH)}

    def popqa_row(row_key: str, role: str, population: str) -> dict:
        numeric_id = row_key.split(":", 1)[1]
        src = popqa_rows.get(numeric_id)
        if src is None:
            raise SystemExit(f"[materialize] {row_key} not found in {POPQA_PATH} by numeric id")
        aliases = json.loads(src["possible_answers"])
        return {
            "row_key": row_key, "role": role, "population": population,
            "source": "popqa", "category_canon": "popqa",
            "question": src["question"], "aliases": aliases,
        }

    out_rows: list[dict] = []
    for rk in p_confab:
        hr = heldout_rows[rk]
        out_rows.append({
            "row_key": rk, "role": "confab", "population": "P_CONFAB",
            "source": hr.get("source", "kuq_unknowns_all"),
            "category_canon": hr.get("category_canon"),
            "question": hr["question"], "aliases": hr.get("aliases") or [],
        })
    for rk in p_refuse:
        out_rows.append(popqa_row(rk, "refused_on_answerable", "P_REFUSE"))
    for rk in p_known:
        out_rows.append(popqa_row(rk, "correct_on_answerable", "P_KNOWN"))

    n_empty_q = sum(1 for r in out_rows if not r.get("question"))
    if n_empty_q:
        raise SystemExit(f"[materialize] {n_empty_q} rows resolved to empty question text")

    out_rows.sort(key=lambda r: (r["population"], r["row_key"]))
    write_jsonl(OUT_ROWS, out_rows)
    print(f"[materialize] wrote {OUT_ROWS} ({len(out_rows)} rows: "
          f"{len(p_confab)} P_CONFAB + {len(p_refuse)} P_REFUSE + {len(p_known)} P_KNOWN)", flush=True)
    print(f"[materialize] source: P_CONFAB<-{heldout_path}, P_REFUSE/P_KNOWN<-{POPQA_PATH}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
