"""Shared license-gate parsing and per-row disposition logic.

Both build_exhaust_dataset.py and verify_exhaust.py import this module rather
than each keeping their own copy, because the row-level dataset now has three
possible dispositions per row (not a binary permitted/not-permitted), and a
build/verify pair with the same three-way branching duplicated in two files
is exactly the kind of thing that drifts silently. Keep both scripts thin
wrappers around this module's functions.

Verdict vocabulary (matches reference/license-gates.md):

- permitted: row kept with all fields, including text-bearing ones.
- permitted-with-conditions: row kept with all fields; the dataset card MUST
  carry that source's `conditions` text (license notice / origin disclosure).
- text-free-only: row kept, but every field in TEXT_BEARING_FIELDS is
  stripped before the row is written. Identity, role/split, and every graded
  boolean/count field from our own graders stays, since none of that is
  source text.
- forbidden: row dropped entirely, in any form. Never appears, not even
  text-free.
- pending-audit (including any source with no table entry at all): row
  dropped entirely. Unlike text-free-only, this is NOT an audited "safe as
  metadata" finding -- it is "nobody has looked at this source yet" -- so it
  gets the most conservative treatment, not the middle one.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import yaml

# Fields that can carry source-derived or model-generated text. Stripped from
# a row when its source's verdict is text-free-only. Keep this list in sync
# with reference/dataset-schema.md's row schema.
TEXT_BEARING_FIELDS = ("generation_text", "answer_value")

ALLOWED_VERDICTS = {
    "permitted",
    "permitted-with-conditions",
    "text-free-only",
    "forbidden",
    "pending-audit",
}
# Verdicts under which a row keeps its text-bearing fields.
TEXT_PERMITTED_VERDICTS = {"permitted", "permitted-with-conditions"}

REQUIRED_HARD_EXCLUSION_KEYS = {"openmoss_cheng_idk", "bridge_llama2_7b_chat"}

# Structural hard exclusions, independent of the license-gates.md table so an
# accidental table edit can never reopen them. Substring match on lowercased
# source keys, aliases, cell ids, and file contents.
HARD_EXCLUDED_PATTERNS = ("openmoss", "cheng_idk", "cheng-idk", "bridge_llama2_7b_chat")


def is_hard_excluded(text: str) -> bool:
    t = text.lower()
    return any(p in t for p in HARD_EXCLUDED_PATTERNS)


def load_license_gates(path: Path, errors: list[str] | None = None) -> list[dict[str, Any]]:
    """Parse the fenced yaml block in license-gates.md. Appends to `errors`
    (if given) instead of raising, so a verifier can report every problem in
    one pass; raises SystemExit if `errors` is None (build-time behavior)."""
    def fail(msg: str) -> list[dict[str, Any]]:
        if errors is None:
            raise SystemExit(msg)
        errors.append(msg)
        return []

    if not path.is_file():
        return fail(f"license-gates table missing: {path}")
    text = path.read_text(encoding="utf-8")
    match = re.search(r"```yaml\n(.*?)\n```", text, re.S)
    if not match:
        return fail(f"{path}: no fenced yaml block found")
    try:
        data = yaml.safe_load(match.group(1))
    except yaml.YAMLError as exc:
        return fail(f"{path}: yaml block failed to parse: {exc}")
    sources = data.get("sources") if isinstance(data, dict) else None
    if not isinstance(sources, list):
        return fail(f"{path}: yaml block missing a 'sources' list")
    return sources


def check_license_gate_wellformed(sources: list[dict[str, Any]], errors: list[str]) -> None:
    seen_keys: set[str] = set()
    for i, entry in enumerate(sources):
        for field in ("key", "license", "verdict", "conditions"):
            if not entry.get(field):
                errors.append(f"license-gates entry #{i} missing required field '{field}': {entry}")
        verdict = entry.get("verdict")
        if verdict is not None and verdict not in ALLOWED_VERDICTS:
            errors.append(f"license-gates entry #{i} has invalid verdict '{verdict}' (allowed: {sorted(ALLOWED_VERDICTS)})")
        key = entry.get("key")
        if key:
            seen_keys.add(str(key))
    missing_hard = REQUIRED_HARD_EXCLUSION_KEYS - seen_keys
    if missing_hard:
        errors.append(f"license-gates table is missing required hard-exclusion entries: {sorted(missing_hard)}")
    for entry in sources:
        if entry.get("key") in REQUIRED_HARD_EXCLUSION_KEYS and entry.get("verdict") != "forbidden":
            errors.append(f"license-gates entry '{entry.get('key')}' must have verdict forbidden, has '{entry.get('verdict')}'")


def find_entry(source: str, sources: list[dict[str, Any]]) -> dict[str, Any] | None:
    s = source.lower().strip()
    for entry in sources:
        keys = [str(entry.get("key", "")).lower()]
        keys += [str(a).lower() for a in (entry.get("aliases") or [])]
        if s in keys:
            return entry
    return None


def gate_verdict(source: str, sources: list[dict[str, Any]]) -> str:
    s = source.lower().strip()
    if is_hard_excluded(s):
        return "forbidden"
    entry = find_entry(s, sources)
    if entry is None:
        return "pending-audit"  # fail closed: unknown source is never permitted, not even text-free
    return str(entry.get("verdict", "pending-audit"))


def strip_text_bearing(row: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in row.items() if k not in TEXT_BEARING_FIELDS}


def has_text_bearing_field(row: dict[str, Any]) -> bool:
    return any(field in row for field in TEXT_BEARING_FIELDS)
