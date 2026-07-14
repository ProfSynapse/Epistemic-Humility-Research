"""Shared source registry, staged-row loading, and normalization for
abstention-wide-instrument-calibration.

Per cell.yaml, four registered cells (QH, QL, LB, MC). MC is cited-only (no
staging, no rows). QH/QL/LB source runlogs live on disk in sibling worktrees
in two different upstream schemas:

  "runlog"           QH and QL: prior harness generation runlogs. Text field
                      `answer_text`. Already carries `well_formed_correct`
                      (v1-derived) per row, used only as one half of the
                      clear_negative decoy AND-filter (never as a refusal
                      verdict on its own -- see build_adjudication_pool.py).
  "rr_staged_split"   LB: rr-cross-family-raw-refusal's staged split-rows
                      file. Text field `baseline_text`. `well_formed` lives
                      at `row["baseline_clean"]["well_formed"]`;
                      `well_formed_correct` at
                      `row["baseline_old_grade"]["well_formed_correct"]`.

Per cell.yaml `instrument.adjudication.text_field_by_source`.

Population scope (resolved ambiguity, recorded in the build report): the two
populations tracked throughout this experiment are `confab` (benefit) and
`known_correct_answered` (cost), mirroring AMENDMENT.md's "both populations"
language used for QH. LB's staged split_rows_private.jsonl carries a third
role, `unknown_refused` (rows the model already refused at undosed baseline
by RR's own role-assignment criterion) -- these are NOT one of the two
tracked populations, are excluded from the core adjudication pool and from
`llama_wide_baseline`'s primary reading, and are reported separately, purely
informationally, clearly labeled. This reading is forced by the Prediction
and Falsifier text, which name "llama's wide-instrument baseline confab
abstention" specifically (not a role-blended number), and by consistency
with every other cell's confab/known framing.

QL layer scope (resolved ambiguity, recorded in the build report):
AMENDMENT.md's prose says "three layers"; the actual doubt-snap runlog
directory holds four hs-index strata (hs20, hs23, hs26, hs30), each with a
`hs{N}__random_direction.jsonl` file matching cell.yaml's literal
`hs*__random_direction.jsonl` glob. cell.yaml (the machine-readable,
authoritative source) does not hard-code a layer count. Per CG2 ("every
registered cell scored over its full staged... population") the more
complete reading -- score every layer the glob matches -- is used; the
AMENDMENT's "three layers" is treated as descriptive prose that undercounts
the real directory, not a registered restriction.
"""

from __future__ import annotations

import hashlib
import json
import random
from pathlib import Path
from typing import Any, Iterable, Optional

HERE = Path(__file__).resolve().parent
ANALYSIS = HERE / "analysis"
COMMITTED = HERE / "analysis-committed"
STAGED = ANALYSIS / "staged_inputs"

TRACKED_ROLES = ("confab", "known_correct_answered")

# ---------------------------------------------------------------------------
# Source registry. Absolute paths into sibling worktrees, per the task brief.
# Staging (stage_inputs.py) copies these into STAGED before anything else
# reads them; every other module in this experiment reads ONLY the staged
# copies (AMENDMENT.md: "Scoring runs only against the staged copies").
# ---------------------------------------------------------------------------

_QH_SRC_DIR = Path("/home/profsynapse/code/ehr-worktrees/qwen35-midband-heldout/experiments/qwen35-4b-midband-heldout/analysis/runlog")
_QL_SRC_DIR = Path("/home/profsynapse/code/ehr-worktrees/qwen35-midband/experiments/qwen35-4b-midband-doubt-snap/analysis/runlog")
_LB_SRC_DIR = Path("/home/profsynapse/code/ehr-worktrees/rr-raw-refusal/experiments/rr-cross-family-raw-refusal/analysis/staged_inputs/llama")

QL_HS_INDICES = (20, 23, 26, 30)  # every hs*__random_direction.jsonl found at build time; see module docstring


def source_manifest() -> list[dict[str, Any]]:
    """Every (cell, arm, source_path) this experiment stages. `dest_name` is
    the file name under analysis/staged_inputs/<cell>/."""
    entries = [
        {"cell": "QH", "arm": "baseline", "source_path": _QH_SRC_DIR / "baseline.jsonl", "dest_name": "baseline.jsonl", "schema": "runlog"},
        {"cell": "QH", "arm": "random_direction", "source_path": _QH_SRC_DIR / "random_direction.jsonl", "dest_name": "random_direction.jsonl", "schema": "runlog"},
        {"cell": "QL", "arm": "baseline", "source_path": _QL_SRC_DIR / "baseline.jsonl", "dest_name": "baseline.jsonl", "schema": "runlog"},
        {"cell": "LB", "arm": "baseline", "source_path": _LB_SRC_DIR / "split_rows_private.jsonl", "dest_name": "split_rows_private.jsonl", "schema": "rr_staged_split"},
    ]
    for hs in QL_HS_INDICES:
        entries.append({
            "cell": "QL", "arm": "random_direction", "hs_index": hs,
            "source_path": _QL_SRC_DIR / f"hs{hs}__random_direction.jsonl",
            "dest_name": f"hs{hs}__random_direction.jsonl", "schema": "runlog",
        })
    return entries


def staged_path(cell: str, dest_name: str) -> Path:
    return STAGED / cell / dest_name


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def sha256_of_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


# ---------------------------------------------------------------------------
# Normalization: every row, regardless of upstream schema, reduces to one
# shape carrying only what the pool builder and scorer need. `text` is the
# one field the containment rule forbids from ever reaching a committed file.
# ---------------------------------------------------------------------------

def normalize_row(raw: dict[str, Any], *, cell: str, arm: str, schema: str, hs_index: Optional[int] = None, dose_multiplier: Optional[int] = None) -> dict[str, Any]:
    if schema == "runlog":
        text = raw.get("answer_text", "")
        well_formed = bool(raw.get("well_formed", False))
        well_formed_correct = bool(raw.get("well_formed_correct", False))
        row_hs_index = raw.get("hs_index", hs_index)
        row_dose = raw.get("dose_multiplier", dose_multiplier)
    elif schema == "rr_staged_split":
        text = raw.get("baseline_text", "")
        well_formed = bool((raw.get("baseline_clean") or {}).get("well_formed", False))
        well_formed_correct = bool((raw.get("baseline_old_grade") or {}).get("well_formed_correct", False))
        row_hs_index = hs_index
        row_dose = dose_multiplier
    else:
        raise ValueError(f"unknown schema {schema!r}")
    return {
        "cell": cell,
        "arm": arm,
        "hs_index": row_hs_index,
        "dose_multiplier": row_dose,
        "row_key": raw["row_key"],
        "role": raw.get("role"),
        "text": text,
        "well_formed": well_formed,
        "well_formed_correct": well_formed_correct,
    }


def load_staged_cell_arm(cell: str, arm: str, *, hs_index: Optional[int] = None) -> list[dict[str, Any]]:
    """Loads and normalizes one staged (cell, arm[, hs_index]) file."""
    matches = [e for e in source_manifest() if e["cell"] == cell and e["arm"] == arm and e.get("hs_index") == hs_index]
    if not matches:
        raise KeyError(f"no registered source for cell={cell} arm={arm} hs_index={hs_index}")
    entry = matches[0]
    path = staged_path(cell, entry["dest_name"])
    raw_rows = load_jsonl(path)
    return [
        normalize_row(r, cell=cell, arm=arm, schema=entry["schema"], hs_index=hs_index)
        for r in raw_rows
    ]


def load_qh() -> dict[str, list[dict[str, Any]]]:
    return {
        "baseline": load_staged_cell_arm("QH", "baseline"),
        "random_direction": load_staged_cell_arm("QH", "random_direction"),
    }


def load_ql_baseline() -> list[dict[str, Any]]:
    return load_staged_cell_arm("QL", "baseline")


def load_ql_random_direction_all() -> dict[int, list[dict[str, Any]]]:
    """{hs_index: normalized rows}, full population (pre-subsample)."""
    return {hs: load_staged_cell_arm("QL", "random_direction", hs_index=hs) for hs in QL_HS_INDICES}


def load_lb() -> list[dict[str, Any]]:
    return load_staged_cell_arm("LB", "baseline")


# ---------------------------------------------------------------------------
# QL deterministic dose-response subsample. Registered: 250 confab rows per
# (layer, dose) cell, seed 20260714, seeded permutation, drawn before any
# grading (cell.yaml `QL.subsample`).
# ---------------------------------------------------------------------------

QL_SUBSAMPLE_SEED = 20260714
QL_SUBSAMPLE_N = 250


def ql_subsample(rows_by_hs: dict[int, list[dict[str, Any]]], seed: int = QL_SUBSAMPLE_SEED, n: int = QL_SUBSAMPLE_N) -> dict[tuple[int, int], list[dict[str, Any]]]:
    """Returns {(hs_index, dose_multiplier): subsampled confab rows}.

    Deterministic: ONE random.Random(seed) instance is advanced sequentially
    across strata in a fixed order (hs_index ascending, then dose_multiplier
    ascending), and each stratum's input rows are sorted by row_key before
    shuffling, so the result depends only on (seed, the registered stratum
    order, the staged file contents) -- never on process/OS iteration order.
    """
    rng = random.Random(seed)
    out: dict[tuple[int, int], list[dict[str, Any]]] = {}
    strata: dict[tuple[int, int], list[dict[str, Any]]] = {}
    for hs, rows in rows_by_hs.items():
        for r in rows:
            if r["role"] != "confab":
                continue
            key = (r["hs_index"], r["dose_multiplier"])
            strata.setdefault(key, []).append(r)
    for key in sorted(strata.keys()):
        pool = sorted(strata[key], key=lambda r: r["row_key"])
        rng.shuffle(pool)
        out[key] = pool[:n]
    return out
