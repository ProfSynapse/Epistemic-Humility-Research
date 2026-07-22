"""PopQA row pool for margin-evidence-responsiveness-worldknown (M4-WK).

Reads ONLY the SC0-staged PopQA copy (analysis/staged_inputs/popqa_test.jsonl,
gitignored). No GPU, no model. Never writes question/answer/category text to
a committed path (containment rule).

row_key convention: "popqa:{id}" (PopQA's own integer `id` field is unique
per row, verified at load time).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import config  # noqa: E402

STAGED_POPQA = config.EXPERIMENT_DIR / "analysis" / "staged_inputs" / "popqa_test.jsonl"


def _parse_json_list(raw: Any) -> list[str]:
    if raw is None:
        return []
    if isinstance(raw, list):
        return [str(x) for x in raw]
    if isinstance(raw, str):
        try:
            v = json.loads(raw)
            return [str(x) for x in v] if isinstance(v, list) else [str(v)]
        except json.JSONDecodeError:
            return []
    return []


def row_key_of(popqa_id: int) -> str:
    return f"popqa:{popqa_id}"


def load_pool() -> dict[str, dict[str, Any]]:
    """row_key -> {question, gold, aliases (gold + possible_answers, dedup,
    gold first), category, popqa_id}. Aliases list always includes the gold
    obj value first (some PopQA rows carry it redundantly in
    possible_answers, some do not)."""
    if not STAGED_POPQA.is_file():
        raise SystemExit(f"popqa_pool FAIL: no staged PopQA at {STAGED_POPQA}; run staging.py first.")
    out: dict[str, dict[str, Any]] = {}
    seen_ids: set[int] = set()
    with STAGED_POPQA.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            pid = int(row["id"])
            if pid in seen_ids:
                raise SystemExit(f"popqa_pool FAIL: duplicate PopQA id {pid}")
            seen_ids.add(pid)
            gold = row[config.POPQA_GOLD_FIELD]
            possible = _parse_json_list(row.get(config.POPQA_ALIASES_FIELD))
            aliases = [gold] + [a for a in possible if a != gold]
            rk = row_key_of(pid)
            out[rk] = {
                "row_key": rk, "popqa_id": pid, "question": row["question"],
                "gold": gold, "aliases": aliases,
                "category": row[config.POPQA_CATEGORY_FIELD],
            }
    if len(out) != config.POPQA_N_ROWS:
        raise SystemExit(f"popqa_pool FAIL: loaded {len(out)} rows, expected {config.POPQA_N_ROWS}")
    return out
