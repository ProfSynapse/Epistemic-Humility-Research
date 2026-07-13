#!/usr/bin/env python3
"""Gate a built exhaust dataset directory before it is allowed near an upload.

Five checks, all must pass:

1. Schema check: PROVENANCE.json and README.md exist; every cell PROVENANCE.json
   lists actually has a directory, and aggregate manifest.json sha256 entries
   match the files on disk.
2. Row counts vs manifest: for the row-level shape, PROVENANCE.json's
   n_rows_kept_with_text + n_rows_kept_text_free per cell matches the actual
   line count in rows.jsonl.
3. Containment lint: scans every file under the dataset dir for the hard
   exclusion patterns (OpenMOSS/Cheng IDK, bridge_llama2_7b_chat) and, for the
   row-level shape, independently re-checks EVERY ROW's `source` field
   against reference/license-gates.md -- per row, not per file, so a rows.jsonl
   mixing a `permitted` source with a `text-free-only` source only passes if
   each row individually matches its own source's disposition (defense in
   depth against a build-script bug or a hand-edited output).
4. License-gate table well-formedness: the fenced YAML block in
   license-gates.md parses, every entry has key/license/verdict/conditions,
   verdict is one of the allowed values, and both hard exclusions are present
   with verdict forbidden.
5. Disclosure check: for every source present in kept rows with verdict
   `permitted-with-conditions`, that source's exact `conditions` text from
   license-gates.md appears verbatim (whitespace-normalized) in the built
   README.md.

Exits 0 and prints a PASS summary only if every check passes. Exits nonzero
and prints every failure found (does not stop at the first one) otherwise.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
SKILL_ROOT = HERE.parent
DEFAULT_LICENSE_GATES = SKILL_ROOT / "reference" / "license-gates.md"

sys.path.insert(0, str(HERE))
from _license_gate import (  # noqa: E402
    TEXT_BEARING_FIELDS,
    TEXT_PERMITTED_VERDICTS,
    check_license_gate_wellformed,
    find_entry,
    gate_verdict,
    has_text_bearing_field,
    is_hard_excluded,
    load_license_gates,
)


def sha256_bytes(data: bytes) -> str:
    h = hashlib.sha256()
    h.update(data)
    return h.hexdigest()


def check_containment_lint(out_dir: Path, sources: list[dict[str, Any]], errors: list[str]) -> None:
    # README.md is our own generated dataset card: its "Release Boundary" and
    # "License and Attribution" sections legitimately name the hard-exclusion
    # categories and quote license conditions verbatim as policy
    # documentation, which is not a leak. Content-scan every other file.
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
            carries_text = has_text_bearing_field(row)
            where = f"{rows_path}:{lineno} (cell {cell_id}, source '{source}', verdict '{verdict}')"
            if verdict in TEXT_PERMITTED_VERDICTS:
                continue  # text-bearing fields may or may not be present; both are fine
            if verdict == "text-free-only":
                if carries_text:
                    errors.append(
                        f"CONTAINMENT: {where} is text-free-only but carries a text-bearing "
                        f"field ({[f for f in TEXT_BEARING_FIELDS if f in row]})"
                    )
            else:  # forbidden or pending-audit: must not appear in any form
                errors.append(
                    f"CONTAINMENT: {where} has verdict '{verdict}' (forbidden or pending-audit) "
                    f"but the row is present in the built dataset at all"
                )


def check_disclosure(out_dir: Path, sources: list[dict[str, Any]], errors: list[str]) -> None:
    provenance_path = out_dir / "PROVENANCE.json"
    if not provenance_path.is_file():
        return  # already reported by check_schema_and_counts
    provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
    sources_present = provenance.get("sources_present") or {}
    conditional_sources = [s for s, v in sources_present.items() if v == "permitted-with-conditions"]
    if not conditional_sources:
        return
    readme_path = out_dir / "README.md"
    if not readme_path.is_file():
        return
    readme_text = readme_path.read_text(encoding="utf-8")
    normalized_readme = " ".join(readme_text.split())
    for source in conditional_sources:
        entry = find_entry(source, sources)
        if entry is None:
            errors.append(
                f"DISCLOSURE: source '{source}' is present as permitted-with-conditions "
                f"but has no license-gates entry to disclose"
            )
            continue
        conditions = str(entry.get("conditions", "")).strip()
        normalized_conditions = " ".join(conditions.split())
        if normalized_conditions and normalized_conditions not in normalized_readme:
            errors.append(
                f"DISCLOSURE: source '{source}' is permitted-with-conditions but its exact "
                f"conditions text from license-gates.md was not found in {readme_path}"
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
            expected_n = None
            if "n_rows_kept_with_text" in info or "n_rows_kept_text_free" in info:
                expected_n = info.get("n_rows_kept_with_text", 0) + info.get("n_rows_kept_text_free", 0)
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
    check_disclosure(out_dir, sources, errors)

    if errors:
        print(f"[verify-exhaust] FAIL: {len(errors)} problem(s) in {out_dir}", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        return 1

    print(f"[verify-exhaust] PASS: {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
