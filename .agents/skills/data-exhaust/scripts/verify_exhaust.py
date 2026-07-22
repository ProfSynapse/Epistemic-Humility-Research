#!/usr/bin/env python3
"""Gate a built exhaust dataset directory before it is allowed near an upload.

Six checks, all must pass:

1. Schema check: PROVENANCE.json and README.md exist; for the aggregate
   shape, PROVENANCE.json's `files` sha256 entries match the files on disk
   and every on-disk file is listed; for the row shape, every cell
   PROVENANCE.json lists actually has a directory.
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
6. Completeness check (aggregate shape, needs --experiment-dir): the staged
   file set (PROVENANCE.json's `files`) plus the recorded `excluded` list
   must equal the file set freshly re-scanned from the source
   analysis-committed/ tree on disk right now. This is independent of
   whatever the builder itself claims -- it re-walks the source tree rather
   than trusting the manifest -- so a builder bug that silently drops an
   artifact shape (the exact defect this check was added to catch; see
   build_exhaust_dataset.py's build_aggregate docstring) fails loudly here
   even if the builder's own bookkeeping looked internally consistent.
   Skipped with a FAIL (not a silent pass) if --experiment-dir is omitted,
   since completeness cannot be claimed without checking it.

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
    # documentation, which is not a leak. PROVENANCE.json's own aggregate
    # 'excluded' list legitimately names the relative PATH of every file the
    # builder skipped (that is the whole point of recording it, so a human
    # can audit what was left out and why) -- it never carries that file's
    # CONTENT, since a content-level hard-exclusion hit aborts the build
    # entirely at build time (build_exhaust_dataset.py's build_aggregate).
    # Naming a path is not a leak; both files are exempt. Content-scan every
    # other file.
    for path in sorted(out_dir.rglob("*")):
        if not path.is_file():
            continue
        if is_hard_excluded(str(path.relative_to(out_dir))):
            errors.append(f"CONTAINMENT: hard-excluded path component in {path}")
            continue
        if path.name in ("README.md", "PROVENANCE.json"):
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
    if shape not in ("aggregate", "rows"):
        errors.append(f"PROVENANCE.json shape must be 'aggregate' or 'rows', got '{shape}'")
        return

    if shape == "aggregate":
        files = provenance.get("files") or {}
        for rel, expected_hash in files.items():
            fpath = out_dir / rel
            if not fpath.is_file():
                errors.append(f"PROVENANCE.json 'files' references '{rel}' but {fpath} is missing")
                continue
            actual_hash = sha256_bytes(fpath.read_bytes())
            if actual_hash != expected_hash:
                errors.append(f"{fpath}: sha256 mismatch (PROVENANCE.json says {expected_hash}, actual {actual_hash})")
        reserved = {provenance_path, readme_path}
        on_disk = {p for p in out_dir.rglob("*") if p.is_file() and p not in reserved}
        listed = {out_dir / rel for rel in files}
        extra = on_disk - listed
        if extra:
            errors.append(
                f"{out_dir}: files on disk not listed in PROVENANCE.json 'files': "
                f"{sorted(str(p.relative_to(out_dir)) for p in extra)}"
            )
    elif shape == "rows":
        cells = provenance.get("cells") or {}
        for cell_id, info in cells.items():
            cell_dir = out_dir / cell_id
            if not cell_dir.is_dir():
                errors.append(f"PROVENANCE.json lists cell '{cell_id}' but {cell_dir} does not exist")
                continue
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


def check_completeness(out_dir: Path, experiment_dir: Path | None, errors: list[str]) -> None:
    """Aggregate shape only: re-walk the SOURCE analysis-committed/ tree right
    now (independent of anything the builder recorded) and require the staged
    file set plus the recorded exclusions to equal it exactly. See module
    docstring check 6."""
    provenance_path = out_dir / "PROVENANCE.json"
    if not provenance_path.is_file():
        return  # already reported by check_schema_and_counts
    provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
    if provenance.get("shape") != "aggregate":
        return
    if experiment_dir is None:
        errors.append(
            "COMPLETENESS: --experiment-dir not provided; cannot verify the staged files "
            "against the source analysis-committed/ tree (this check is mandatory before publication)"
        )
        return
    committed_root = experiment_dir / "analysis-committed"
    if not committed_root.is_dir():
        errors.append(f"COMPLETENESS: {committed_root} does not exist; cannot verify")
        return

    source_files = {p.relative_to(committed_root).as_posix() for p in committed_root.rglob("*") if p.is_file()}
    staged_files = set((provenance.get("files") or {}).keys())
    excluded_entries = provenance.get("excluded") or []
    excluded_paths = {e.get("path") for e in excluded_entries}

    for entry in excluded_entries:
        if not entry.get("reason"):
            errors.append(f"COMPLETENESS: excluded entry {entry} has no 'reason'")

    expected_staged = source_files - excluded_paths
    missing = expected_staged - staged_files
    unexpected = staged_files - expected_staged
    excluded_not_in_source = excluded_paths - source_files

    if missing:
        errors.append(
            f"COMPLETENESS: {len(missing)} source file(s) present in {committed_root} but "
            f"missing from the staged output and not recorded as excluded: {sorted(missing)}"
        )
    if unexpected:
        errors.append(
            f"COMPLETENESS: {len(unexpected)} staged file(s) do not correspond to a source "
            f"file (and are not explained by an exclusion): {sorted(unexpected)}"
        )
    if excluded_not_in_source:
        errors.append(
            f"COMPLETENESS: 'excluded' list references path(s) not found in the current "
            f"source tree: {sorted(excluded_not_in_source)}"
        )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dataset-dir", required=True, help="dataset dir produced by build_exhaust_dataset.py")
    parser.add_argument(
        "--experiment-dir",
        default=None,
        help="path to experiments/<slug>/ (the same --experiment-dir the builder was pointed at); "
        "required for the aggregate-shape completeness check (see module docstring check 6)",
    )
    parser.add_argument("--license-gates", default=str(DEFAULT_LICENSE_GATES))
    args = parser.parse_args(argv)

    out_dir = Path(args.dataset_dir).resolve()
    if not out_dir.is_dir():
        print(f"[verify-exhaust] FATAL: {out_dir} is not a directory", file=sys.stderr)
        return 2
    experiment_dir = Path(args.experiment_dir).resolve() if args.experiment_dir else None

    errors: list[str] = []
    sources = load_license_gates(Path(args.license_gates).resolve(), errors)
    check_license_gate_wellformed(sources, errors)
    check_schema_and_counts(out_dir, errors)
    check_containment_lint(out_dir, sources, errors)
    check_disclosure(out_dir, sources, errors)
    check_completeness(out_dir, experiment_dir, errors)

    if errors:
        print(f"[verify-exhaust] FAIL: {len(errors)} problem(s) in {out_dir}", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        return 1

    print(f"[verify-exhaust] PASS: {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
