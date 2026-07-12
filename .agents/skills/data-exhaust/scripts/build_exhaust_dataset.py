#!/usr/bin/env python3
"""Build an HF-ready dataset directory from one experiment's data exhaust.

Two shapes, one script:

- Aggregate (default): copies analysis-committed/<cell_id>/*.json artifacts
  (dose-response tables, direction fits, gate AUROCs, manifests) into
  <out-dir>/<cell_id>/. Always publishable: no source question text, no
  aliases, no per-row generation text.
- Row-level (pass --rows-dir): reads locally staged per-cell JSONL (row text
  usually lives on a Modal volume or a results repo, not in this git
  checkout) and keeps only rows whose `source` field resolves to a
  `permitted` verdict in reference/license-gates.md. Everything else is
  dropped, counted, and recorded in PROVENANCE.json -- never included with
  text blanked out.

See reference/dataset-schema.md for the exact on-disk shape and
reference/license-gates.md for the gate table this script reads.

This script only ever writes into --out-dir. It never touches the
experiment's own analysis/ or analysis-committed/ directories, and it never
uploads anything (see scripts/upload_exhaust.py for that, separately gated).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

HERE = Path(__file__).resolve().parent
SKILL_ROOT = HERE.parent
DEFAULT_LICENSE_GATES = SKILL_ROOT / "reference" / "license-gates.md"

# Structural hard exclusions, independent of the license-gates.md table so an
# accidental table edit can never reopen them. Substring match on lowercased
# source keys, aliases, cell ids, and file contents.
HARD_EXCLUDED_PATTERNS = ("openmoss", "cheng_idk", "cheng-idk", "bridge_llama2_7b_chat")

# Aggregate artifact filenames this builder knows about, in the order the
# doubt-snap-cross-family-confirmatory prep_tuner_cell.py / materialize_tuner_cells.py
# pipeline writes them. summary.json is optional (only terminal/scored cells
# have it); everything else is expected but tolerated as missing.
AGGREGATE_ARTIFACT_FILES = [
    "g0_prep_summary.json",
    "build_manifest.json",
    "split_manifest.json",
    "u_d.json",
    "c_hat.json",
    "random_direction.json",
    "gate_fit.json",
    "dose_fit.json",
    "summary.json",
]
OPTIONAL_AGGREGATE_FILES = {"summary.json"}


def is_hard_excluded(text: str) -> bool:
    t = text.lower()
    return any(p in t for p in HARD_EXCLUDED_PATTERNS)


def hard_exclusion_scan(payload: Any, src_path: Path) -> None:
    blob = json.dumps(payload, ensure_ascii=False).lower()
    for pattern in HARD_EXCLUDED_PATTERNS:
        if pattern in blob:
            raise SystemExit(
                f"CONTAINMENT: hard-excluded pattern '{pattern}' found in {src_path}; refusing to build"
            )


def load_license_gates(path: Path) -> list[dict[str, Any]]:
    text = path.read_text(encoding="utf-8")
    match = re.search(r"```yaml\n(.*?)\n```", text, re.S)
    if not match:
        raise SystemExit(f"{path}: no fenced yaml block found")
    data = yaml.safe_load(match.group(1))
    sources = data.get("sources") if isinstance(data, dict) else None
    if not isinstance(sources, list):
        raise SystemExit(f"{path}: yaml block missing a 'sources' list")
    return sources


def gate_verdict(source: str, sources: list[dict[str, Any]]) -> str:
    s = source.lower().strip()
    if is_hard_excluded(s):
        return "forbidden"
    for entry in sources:
        keys = [str(entry.get("key", "")).lower()]
        keys += [str(a).lower() for a in (entry.get("aliases") or [])]
        if s in keys:
            return str(entry.get("verdict", "pending-audit"))
    return "pending-audit"  # fail closed: unknown source is never permitted


def sha256_bytes(data: bytes) -> str:
    h = hashlib.sha256()
    h.update(data)
    return h.hexdigest()


def git_commit_sha(cwd: Path) -> str:
    result = subprocess.run(
        ["git", "-C", str(cwd), "rev-parse", "HEAD"],
        capture_output=True, text=True,
    )
    return result.stdout.strip() if result.returncode == 0 else "unknown"


def load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise SystemExit(f"{path} did not parse as a mapping")
    return data


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def build_aggregate(exp_dir: Path, out_dir: Path) -> dict[str, Any]:
    committed_root = exp_dir / "analysis-committed"
    cells_report: dict[str, Any] = {}
    if not committed_root.is_dir():
        print(f"[build-exhaust] no analysis-committed/ under {exp_dir}; 0 cells", file=sys.stderr)
        return cells_report
    for cell_dir in sorted(p for p in committed_root.iterdir() if p.is_dir()):
        cell_id = cell_dir.name
        out_cell = out_dir / cell_id
        found: list[str] = []
        missing: list[str] = []
        file_hashes: dict[str, str] = {}
        for fname in AGGREGATE_ARTIFACT_FILES:
            src = cell_dir / fname
            if not src.is_file():
                if fname not in OPTIONAL_AGGREGATE_FILES:
                    missing.append(fname)
                continue
            payload = json.loads(src.read_text(encoding="utf-8"))
            hard_exclusion_scan(payload, src)
            dst = out_cell / fname
            write_json(dst, payload)
            found.append(fname)
            file_hashes[fname] = sha256_bytes(dst.read_bytes())
        write_json(out_cell / "manifest.json", {"cell_id": cell_id, "files": found, "sha256": file_hashes})
        cells_report[cell_id] = {"files": found, "missing_expected": missing}
    return cells_report


def build_rows(rows_dir: Path, out_dir: Path, sources: list[dict[str, Any]]) -> tuple[dict[str, Any], dict[str, int]]:
    cells_report: dict[str, Any] = {}
    excluded_counts: dict[str, int] = {}
    jsonl_files = sorted(rows_dir.glob("*.jsonl"))
    if not jsonl_files:
        print(f"[build-exhaust] no *.jsonl files under {rows_dir}; 0 cells", file=sys.stderr)
    for src_file in jsonl_files:
        cell_id = src_file.stem
        if is_hard_excluded(cell_id):
            raise SystemExit(f"CONTAINMENT: hard-excluded cell id '{cell_id}' in {src_file}; refusing to build")
        kept: list[dict[str, Any]] = []
        for lineno, line in enumerate(src_file.read_text(encoding="utf-8").splitlines(), start=1):
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            source = str(row.get("source", ""))
            if is_hard_excluded(source):
                raise SystemExit(
                    f"CONTAINMENT: hard-excluded source '{source}' at {src_file}:{lineno}; refusing to build"
                )
            verdict = gate_verdict(source, sources)
            if verdict != "permitted":
                excluded_counts[source] = excluded_counts.get(source, 0) + 1
                continue
            kept.append(row)
        out_cell = out_dir / cell_id
        out_cell.mkdir(parents=True, exist_ok=True)
        with (out_cell / "rows.jsonl").open("w", encoding="utf-8") as fh:
            for row in kept:
                fh.write(json.dumps(row, ensure_ascii=False) + "\n")
        cells_report[cell_id] = {"n_rows_kept": len(kept)}
    return cells_report, excluded_counts


def readme_text(*, shape: str, manifest: dict[str, Any], provenance: dict[str, Any], repo_id: str) -> str:
    slug = manifest["slug"]
    cells = provenance["cells"]
    excluded = provenance.get("license_gate_excluded") or {}
    lines_cells = "\n".join(
        f"- `{cid}`: {', '.join(info.get('files', [])) or '(none)'}"
        + (f" -- n_rows_kept={info['n_rows_kept']}" if "n_rows_kept" in info else "")
        + (f" -- missing_expected: {', '.join(info['missing_expected'])}" if info.get("missing_expected") else "")
        for cid, info in sorted(cells.items())
    ) or "(no cells found)"
    excluded_lines = "\n".join(f"- `{src}`: {n} rows dropped (gate verdict not permitted)" for src, n in sorted(excluded.items())) or "(none)"
    shape_desc = (
        "Aggregate-only: dose-response tables, direction fits, gate AUROCs, and "
        "manifests. No source question text, aliases, or per-row generation text."
        if shape == "aggregate"
        else "Row-level generation text, gated per reference/license-gates.md; "
        "rows whose source is not `permitted` are dropped entirely, not redacted."
    )
    return f"""---
license: other
task_categories:
- text-classification
language:
- en
pretty_name: {slug} data exhaust ({shape})
tags:
- epistemic-humility
- mechanistic-interpretability
- data-exhaust
---

# {slug} -- {shape} exhaust

{shape_desc}

HF repo: `{repo_id}`

## Provenance

- Experiment: `experiments/{slug}`
- Amendment: `{provenance['amendment_path']}`
- Repo commit SHA: `{provenance['repo_commit_sha']}`
- Generated: `{provenance['generation_date']}`
- Pinned instrument config sha256:
{chr(10).join(f"  - `{k}`: `{v}`" for k, v in sorted(provenance.get('instrument_config_sha256', {}).items())) or "  (none recorded)"}

## Cells

{lines_cells}

## License-gate exclusions

{excluded_lines}

## Files

See `PROVENANCE.json` for the full machine-readable provenance block. Each
`<cell_id>/manifest.json` (aggregate shape) lists the artifact files present
for that cell and their sha256.

## Release Boundary

Built by `.skills/data-exhaust/scripts/build_exhaust_dataset.py`, gated by
`.skills/data-exhaust/reference/license-gates.md`, and verified by
`.skills/data-exhaust/scripts/verify_exhaust.py` before any upload. Hard
exclusions (OpenMOSS/Cheng IDK, `bridge_llama2_7b_chat`) are enforced
structurally in code, not only by this table.
"""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--experiment-dir", required=True, help="path to experiments/<slug>/")
    parser.add_argument("--out-dir", required=True, help="destination dataset dir (never committed to git)")
    parser.add_argument("--rows-dir", default=None, help="dir of locally staged <cell_id>.jsonl row files (row-level shape)")
    parser.add_argument("--license-gates", default=str(DEFAULT_LICENSE_GATES))
    parser.add_argument("--repo-id", default=None, help="HF repo id to record in the dataset card (informational only; upload_exhaust.py derives its own default)")
    parser.add_argument("--generation-date", default=None, help="override provenance generation_date (ISO 8601); defaults to now (UTC)")
    args = parser.parse_args(argv)

    exp_dir = Path(args.experiment_dir).resolve()
    out_dir = Path(args.out_dir).resolve()
    exp_yaml_path = exp_dir / "experiment.yaml"
    if not exp_yaml_path.is_file():
        raise SystemExit(f"missing {exp_yaml_path}; is --experiment-dir a valid experiments/<slug>/ directory?")
    manifest = load_yaml(exp_yaml_path)
    slug = manifest.get("slug")
    if slug != exp_dir.name:
        raise SystemExit(f"experiment.yaml slug '{slug}' does not match directory name '{exp_dir.name}'")

    amendment_path = exp_dir / "AMENDMENT.md"
    if not amendment_path.is_file():
        raise SystemExit(f"missing {amendment_path}")

    license_gates_path = Path(args.license_gates).resolve()
    sources = load_license_gates(license_gates_path)

    shape = "rows" if args.rows_dir else "aggregate"
    out_dir.mkdir(parents=True, exist_ok=True)

    if shape == "aggregate":
        cells_report = build_aggregate(exp_dir, out_dir)
        excluded_counts: dict[str, int] = {}
    else:
        rows_dir = Path(args.rows_dir).resolve()
        if not rows_dir.is_dir():
            raise SystemExit(f"--rows-dir {rows_dir} is not a directory")
        cells_report, excluded_counts = build_rows(rows_dir, out_dir, sources)

    generation_date = args.generation_date or datetime.now(timezone.utc).isoformat()
    repo_root = Path(
        subprocess.run(["git", "-C", str(exp_dir), "rev-parse", "--show-toplevel"], capture_output=True, text=True).stdout.strip()
        or exp_dir.parents[1]
    )
    provenance = {
        "experiment_slug": slug,
        "amendment_path": str(amendment_path.relative_to(repo_root)) if repo_root in amendment_path.parents else str(amendment_path),
        "repo_commit_sha": git_commit_sha(exp_dir),
        "instrument_config_sha256": (manifest.get("instrument") or {}).get("pins") or {},
        "generation_date": generation_date,
        "shape": shape,
        "cells": cells_report,
        "license_gate_excluded": excluded_counts,
    }
    write_json(out_dir / "PROVENANCE.json", provenance)

    repo_id = args.repo_id or f"professorsynapse/eh-{slug}" + ("-rows" if shape == "rows" else "")
    (out_dir / "README.md").write_text(
        readme_text(shape=shape, manifest=manifest, provenance=provenance, repo_id=repo_id),
        encoding="utf-8",
    )

    print(f"[build-exhaust] shape={shape} slug={slug} cells={len(cells_report)} out_dir={out_dir}")
    if excluded_counts:
        print(f"[build-exhaust] license-gate excluded: {excluded_counts}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
