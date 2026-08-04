"""Shared priority-screen logic for form-judge-axis-g-rescore.

AMENDMENT.md "Design" / "Priority screen": each row of the naming battery's
7 Arm A sub-arms (a_baseline, a_dose_0p25, a_dose_0p5, a_dose_0p75, a_dose_1,
a_placebo_0p5, a_placebo_1) is classed F5 if `degenerate` fires, else F4 if
`semantic_refuse` or `refused_v2` fires, using the fields already present in
the naming battery's merged phase-2 runlogs. Only the remainder (neither
degenerate nor explicit-IDK) is "screened_in" -- eligible for the judge
lane's F1/F2/F3 call. This module never assigns F1/F2/F3 itself; that is the
judge's job (AMENDMENT.md "Judge lane").

This module is deliberately the SINGLE place the screen logic lives.
`screen_rows.py` (reports screen counts + writes the screened-in remainder)
and `build_judge_pool.py` (needs F4 rows as clear-positive decoy candidates,
and screened-in rows as core candidates) both import from here rather than
each re-deriving the classification, so the two scripts cannot silently
drift apart on what "screened in" means.

FIELD PROVENANCE (do not recompute, only read): `degenerate`,
`semantic_refuse`, `refused_v2` are validated fields already present on every
row of the naming battery's merged runlogs (its own grader.py / gen_lib.py /
detector_v2.py pipeline). `answer_value` / `answer_text` carry the
generation text, same field-preference convention as the naming battery's
`form_taxonomy._scan_text` (prefer the parsed answer value; fall back to the
raw generation text when no parsed value is present).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

# The 7 Arm A sub-arms this cell rescoring covers (AMENDMENT.md "Design":
# "Substrate: ... 7 sub-arms x 400 rows"). Unlike the naming battery's own
# pool builder, this cell does NOT split dosed-vs-placebo for screening
# purposes: screen counts and the payload rescore both cover all 7 uniformly.
ALL_ARM_KEYS: tuple[str, ...] = (
    "a_baseline",
    "a_dose_0p25",
    "a_dose_0p5",
    "a_dose_0p75",
    "a_dose_1",
    "a_placebo_0p5",
    "a_placebo_1",
)

# AMENDMENT.md "Axis-G rescore": the three intermediate doses the G3 share
# threshold is evaluated at.
INTERMEDIATE_DOSE_ARMS: tuple[str, ...] = ("a_dose_0p25", "a_dose_0p5", "a_dose_0p75")
BASELINE_ARM = "a_baseline"

F5_DEGENERATE = "F5_degenerate"
F4_EXPLICIT_IDK = "F4_explicit_idk"
SCREENED_IN = "screened_in"


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str), encoding="utf-8")


def scan_text(row: dict[str, Any]) -> str:
    """Same field-preference convention as form_taxonomy.py's `_scan_text`:
    prefer the parsed `answer_value`, fall back to raw `answer_text`."""
    answer_value = row.get("answer_value")
    if answer_value:
        return str(answer_value)
    return str(row.get("answer_text") or "")


def classify_screen(row: dict[str, Any]) -> str:
    """Priority screen, F5 > F4 > screened_in, per AMENDMENT.md "Design".
    Field checks only -- no pattern matching, no recomputation of the
    upstream validated fields."""
    if bool(row.get("degenerate", False)):
        return F5_DEGENERATE
    if bool(row.get("semantic_refuse", False)) or bool(row.get("refused_v2", False)):
        return F4_EXPLICIT_IDK
    return SCREENED_IN


def discover_runlogs(runlog_dir: Path, arm_keys: tuple[str, ...]) -> dict[str, Path]:
    """Maps arm_key -> path for every arm whose runlog file is found.
    Primary convention: `<arm_key>.jsonl`. Falls back to a glob match so a
    minor naming variation does not silently drop an arm; missing arms are
    reported in `coverage["arms_missing"]`, not raised, so this tooling can
    run cleanly against a partial or still-in-progress runlog directory."""
    found: dict[str, Path] = {}
    for arm in arm_keys:
        direct = runlog_dir / f"{arm}.jsonl"
        if direct.is_file():
            found[arm] = direct
            continue
        matches = sorted(runlog_dir.glob(f"*{arm}*.jsonl")) if runlog_dir.is_dir() else []
        if matches:
            found[arm] = matches[0]
    return found


def load_and_screen(runlog_dir: Path, arm_keys: tuple[str, ...] = ALL_ARM_KEYS) -> tuple[dict[str, dict[str, list[dict[str, Any]]]], dict[str, Any]]:
    """Returns (screened, coverage).

    `screened[arm]` = {"F5_degenerate": [...], "F4_explicit_idk": [...],
    "screened_in": [...]}, each a list of {"row_key", "arm", "text"} dicts.

    `coverage` records which runlog files were found and per-arm row counts,
    same shape convention as the naming battery's `load_core_and_decoy_
    candidates` coverage dict.
    """
    paths = discover_runlogs(runlog_dir, arm_keys)
    coverage: dict[str, Any] = {"arms_found": {}, "arms_missing": [], "n_rows_by_arm": {}}
    screened: dict[str, dict[str, list[dict[str, Any]]]] = {}

    for arm in arm_keys:
        path = paths.get(arm)
        if path is None:
            coverage["arms_missing"].append(arm)
            screened[arm] = {F5_DEGENERATE: [], F4_EXPLICIT_IDK: [], SCREENED_IN: []}
            continue
        coverage["arms_found"][arm] = str(path)
        rows = load_jsonl(path)
        coverage["n_rows_by_arm"][arm] = len(rows)
        buckets: dict[str, list[dict[str, Any]]] = {F5_DEGENERATE: [], F4_EXPLICIT_IDK: [], SCREENED_IN: []}
        for raw in rows:
            label = classify_screen(raw)
            buckets[label].append({
                "row_key": raw["row_key"],
                "arm": raw.get("arm", arm),
                "text": scan_text(raw),
            })
        screened[arm] = buckets

    return screened, coverage
