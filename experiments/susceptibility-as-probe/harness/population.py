"""Per-row question-text join for susceptibility-as-probe (M2).

Reads ONLY the SC0-staged inputs (analysis/staged_inputs/, gitignored). No
GPU, no model. Never writes question/answer text to a committed path
(containment rule).
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import config  # noqa: E402
import common  # noqa: E402

STAGED = config.EXPERIMENT_DIR / "analysis" / "staged_inputs" / config.FAMILY


def population_role_by_row_key() -> dict[str, str]:
    ids = common.load_json(STAGED / "subsample_ids_qwen35_4b.json")
    out = {rk: "confab" for rk in ids["confab_subsample"]["row_keys"]}
    for rk in ids["known_full"]["row_keys"]:
        out[rk] = "known_correct_answered"
    return out


def question_pool() -> dict[str, dict[str, Any]]:
    """row_key -> {question, aliases, category_canon, source, role} for
    every row in the auxiliary heldout question-text source."""
    path = STAGED / "heldout_rows_for_steer.jsonl"
    out: dict[str, dict[str, Any]] = {}
    for r in common.load_jsonl(path):
        out[r["row_key"]] = {
            "question": r.get("question"), "aliases": r.get("aliases", []),
            "category_canon": r.get("category_canon"), "source": r.get("source"),
            "role": r.get("role"),
        }
    return out


def build_population() -> list[dict[str, Any]]:
    """The 760 M2 population rows: row_key, role (from subsample-ids,
    authoritative), question (joined from the auxiliary question pool).
    Hard-fails if any row_key is missing question text or if a role
    mismatches between the two sources."""
    roles = population_role_by_row_key()
    qpool = question_pool()
    rows: list[dict[str, Any]] = []
    missing: list[str] = []
    role_mismatch: list[str] = []
    for row_key, role in roles.items():
        q = qpool.get(row_key)
        if q is None or not q.get("question"):
            missing.append(row_key)
            continue
        if q.get("role") != role:
            role_mismatch.append(row_key)
            continue
        rows.append({
            "row_key": row_key, "role": role, "question": q["question"],
            "aliases": q.get("aliases", []), "category_canon": q.get("category_canon"),
            "source": q.get("source"),
        })
    if missing:
        raise SystemExit(f"population.build_population FAIL: {len(missing)} row_keys missing question text, e.g. {missing[:5]}")
    if role_mismatch:
        raise SystemExit(f"population.build_population FAIL: {len(role_mismatch)} row_keys have role mismatch between subsample-ids and question pool, e.g. {role_mismatch[:5]}")
    if len(rows) != config.N_POPULATION:
        raise SystemExit(f"population.build_population FAIL: built {len(rows)} rows, expected {config.N_POPULATION}")
    return sorted(rows, key=lambda r: r["row_key"])
