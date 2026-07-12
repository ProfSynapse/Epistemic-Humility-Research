#!/usr/bin/env python3
"""Gate a built exhaust dataset directory before it is allowed near an upload.

Four checks, all must pass:

1. Schema check: PROVENANCE.json and README.md exist; every cell PROVENANCE.json
   lists actually has a directory, and aggregate manifest.json sha256 entries
   match the files on disk.
2. Row counts vs manifest: for the row-level shape, PROVENANCE.json's
   n_rows_kept per cell matches the actual line count in rows.jsonl.
3. Containment lint: scans every file under the dataset dir for the hard
   exclusion patterns (OpenMOSS/Cheng IDK, bridge_llama2_7b_chat) and, for the
   row-level shape, independently re-checks every row's `source` field against
   reference/license-gates.md (defense in depth against a build-script bug or
   a hand-edited output).
4. License-gate table well-formedness: the fenced YAML block in
   license-gates.md parses, every entry has key/license/verdict/conditions,
   verdict is one of permitted/forbidden/pending-audit, and both hard
   exclusions are present with verdict forbidden.

Exits 0 and prints a PASS summary only if every check passes. Exits nonzero
and prints every failure found (does not stop at the first one) otherwise.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

import yaml

HERE = Path(__file__).resolve().parent
SKILL_ROOT = HERE.parent
DEFAULT_LICENSE_GATES = SKILL_ROOT / "reference" / "license-gates.md"

HARD_EXCLUDED_PATTERNS = ("openmoss", "cheng_idk", "cheng-idk", "bridge_llama2_7b_chat")
ALLOWED_VERDICTS = {"permitted", "forbidden", "pending-audit"}
REQUIRED_HARD_EXCLUSION_KEYS = {"openmoss_cheng_idk", "bridge_llama2_7b_chat"}


def is_hard_excluded(text: str) -> bool:
    t = text.lower()
    return any(p in t for p in HARD_EXCLUDED_PATTERNS)


def sha256_bytes(data: bytes) -> str:
    h = hashlib.sha256()
    h.update(data)
    return h.hexdigest()


def load_license_gates(path: Path, errors: list[str]) -> list[dict[str, Any]]:
    if not path.is_file():
        errors.append(f"license-gates table missing: {path}")
        return []
    text = path.read_text(encoding="utf-8")
    match = re.search(r"```yaml\n(.*?)\n```", text, re.S)
    if not match:
        errors.append(f"{path}: no fenced yaml block found")
        return []
    try:
        data = yaml.safe_load(match.group(1))
    except yaml.YAMLError as exc:
        errors.append(f"{path}: yaml block failed to parse: {exc}")
        return []
    sources = data.get("sources") if isinstance(data, dict) else None
    if not isinstance(sources, list):
        errors.append(f"{path}: yaml block missing a 'sources' list")
        return []
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


def gate_verdict(source: str, sources: list[dict[str, Any]]) -> str:
    s = source.lower().strip()
    if is_hard_excluded(s):
        return "forbidden"
    for entry in sources:
        keys = [str(entry.get("key", "")).lower()]
        keys += [str(a).lower() for a in (entry.get("aliases") or [])]
        if s in keys:
            return str(entry.get("verdict", "pending-audit"))
    return "pending-audit"


def check_containment_lint(out_dir: Path, sources: list[dict[str, Any]], errors: list[str]) -> None:
    # README.md is our own generated dataset card: its "Release Boundary"
    # section legitimately names the hard-exclusion categories as policy
    # documentation (the same way reference/license-gates.md does), which is
    # not a leak. Content-scan every other file; still path-check README.md's
    # own name (which never matches) for consistency.
    for path in sorted(out_dir.rglob("*")):
        if not path.is_file():
            continue
        if is_hard_excluded(str(path.relative_to(out_dir))):
            errors.append(f"CONTAINMENT: hard-excluded path component in {path}")
            continue
        if path.name == "README.md":
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, ValueError):
            continue
        if is_hard_excluded(text):
            errors.append(f"CONTAINMENT: hard-excluded pattern found inside {path}")

    for rows_path in sorted(out_dir.glob("*/rows.jsonl")):
        cell_id = rows_path.parent.name
        for lineno, line in enumerate(rows_path.read_text(encoding="utf-8").splitlines(), start=1):
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            source = str(row.get("source", ""))
            verdict = gate_verdict(source, sources)
            if verdict != "permitted":
                errors.append(
                    f"CONTAINMENT: {rows_path}:{lineno} (cell {cell_id}) has source "
                    f"'{source}' with verdict '{verdict}', not permitted, but row text is present"
                )


def check_schema_and_counts(out_dir: Path, errors: list[str]) -> None:
    provenance_path = out_dir / "PROVENANCE.json"
    readme_path = out_dir / "README.md"
    if not provenance_path.is_file():
        errors.append(f"missing {provenance_path}")
        return
    if not readme_path.is_file():
        errors.append(f"missing {readme_path}")
    provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
    shape = provenance.get("shape")
    cells = provenance.get("cells") or {}
    if shape not in ("aggregate", "rows"):
        errors.append(f"PROVENANCE.json shape must be 'aggregate' or 'rows', got '{shape}'")

    for cell_id, info in cells.items():
        cell_dir = out_dir / cell_id
        if not cell_dir.is_dir():
            errors.append(f"PROVENANCE.json lists cell '{cell_id}' but {cell_dir} does not exist")
            continue
        if shape == "aggregate":
            manifest_path = cell_dir / "manifest.json"
            if not manifest_path.is_file():
                errors.append(f"missing {manifest_path}")
                continue
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            for fname, expected_hash in (manifest.get("sha256") or {}).items():
                fpath = cell_dir / fname
                if not fpath.is_file():
                    errors.append(f"{manifest_path} references '{fname}' but {fpath} is missing")
                    continue
                actual_hash = sha256_bytes(fpath.read_bytes())
                if actual_hash != expected_hash:
                    errors.append(f"{fpath}: sha256 mismatch (manifest says {expected_hash}, actual {actual_hash})")
            listed_files = set(manifest.get("files") or [])
            on_disk_json = {p.name for p in cell_dir.glob("*.json") if p.name != "manifest.json"}
            extra = on_disk_json - listed_files
            if extra:
                errors.append(f"{cell_dir}: files on disk not listed in manifest.json: {sorted(extra)}")
        elif shape == "rows":
            rows_path = cell_dir / "rows.jsonl"
            if not rows_path.is_file():
                errors.append(f"missing {rows_path}")
                continue
            actual_n = sum(1 for line in rows_path.read_text(encoding="utf-8").splitlines() if line.strip())
            expected_n = info.get("n_rows_kept")
            if expected_n is not None and actual_n != expected_n:
                errors.append(f"{rows_path}: PROVENANCE.json says n_rows_kept={expected_n}, actual line count={actual_n}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dataset-dir", required=True, help="dataset dir produced by build_exhaust_dataset.py")
    parser.add_argument("--license-gates", default=str(DEFAULT_LICENSE_GATES))
    args = parser.parse_args(argv)

    out_dir = Path(args.dataset_dir).resolve()
    if not out_dir.is_dir():
        print(f"[verify-exhaust] FATAL: {out_dir} is not a directory", file=sys.stderr)
        return 2

    errors: list[str] = []
    sources = load_license_gates(Path(args.license_gates).resolve(), errors)
    check_license_gate_wellformed(sources, errors)
    check_schema_and_counts(out_dir, errors)
    check_containment_lint(out_dir, sources, errors)

    if errors:
        print(f"[verify-exhaust] FAIL: {len(errors)} problem(s) in {out_dir}", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        return 1

    print(f"[verify-exhaust] PASS: {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
