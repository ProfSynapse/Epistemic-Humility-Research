#!/usr/bin/env python3
"""Build an HF-ready dataset directory from one experiment's data exhaust.

Two shapes, one script:

- Aggregate (default): recursively copies EVERY file under
  analysis-committed/ (any depth, flat or celled layout) into <out-dir>/,
  preserving relative paths, byte-for-byte. Always publishable: the
  experiment's own analysis-committed/ tree is already the repo's containment
  boundary for question text, aliases, and per-row generation text, so this
  builder trusts that boundary rather than re-filtering by filename.
  The only filter applied here is the hard-exclusion deny-list below.
- Row-level (pass --rows-dir): reads locally staged per-cell JSONL (row text
  usually lives on a Modal volume or a results repo, not in this git
  checkout) and gives each row one of three dispositions per
  reference/license-gates.md's per-source verdict: kept with text
  (`permitted` / `permitted-with-conditions`), kept with text-bearing fields
  stripped (`text-free-only`), or dropped entirely (`forbidden` /
  `pending-audit`). Dispositions are counted and recorded in PROVENANCE.json;
  a dropped row never appears in any form.

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
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

HERE = Path(__file__).resolve().parent
SKILL_ROOT = HERE.parent
DEFAULT_LICENSE_GATES = SKILL_ROOT / "reference" / "license-gates.md"

sys.path.insert(0, str(HERE))
from _license_gate import (  # noqa: E402
    TEXT_PERMITTED_VERDICTS,
    gate_verdict,
    is_hard_excluded,
    load_license_gates,
    strip_text_bearing,
)

def _content_hard_exclusion_hit(text: str) -> str | None:
    from _license_gate import HARD_EXCLUDED_PATTERNS

    t = text.lower()
    for pattern in HARD_EXCLUDED_PATTERNS:
        if pattern in t:
            return pattern
    return None


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


def build_aggregate(exp_dir: Path, out_dir: Path) -> tuple[dict[str, str], list[dict[str, str]]]:
    """Recursively copy every file under analysis-committed/ into out_dir,
    preserving relative paths, byte-for-byte.

    analysis-committed/ is the repo's own containment lane: everything under
    it already cleared the boundary that keeps question text, aliases, and
    per-row generation text out of the public git repo (see SKILL.md). A
    second filename allowlist layered on top of that boundary is a redundant
    gatekeeper -- it does not add safety, it just silently drops whatever
    artifact shape the allowlist's author had not seen yet (this is exactly
    how every non-doubt-snap-cross-family-confirmatory experiment's
    analysis-committed/ vocabulary -- final_report.json, atlas_summary.json,
    flat top-level files, three-level nesting, non-JSON files -- went
    missing from every prior exhaust build). The hard-exclusion deny-list is
    the only filter this builder applies, exactly the same two structural
    exclusions (OpenMOSS/Cheng IDK, bridge_llama2_7b_chat) enforced
    elsewhere in this file and in verify_exhaust.py.

    Returns (files, excluded):
      files    -- {relative_path: sha256} for every file actually copied.
      excluded -- [{"path": relative_path, "reason": ...}] for every file
                  skipped because its own relative path matched a
                  hard-exclusion pattern. A pattern match found inside a
                  file's CONTENT (as opposed to its path) is not a skip; it
                  aborts the whole build via SystemExit, since content-level
                  containment inside a directory meant to already be
                  public-safe is an anomaly that needs a human, not a
                  silent drop.
    """
    committed_root = exp_dir / "analysis-committed"
    files: dict[str, str] = {}
    excluded: list[dict[str, str]] = []
    if not committed_root.is_dir():
        print(f"[build-exhaust] no analysis-committed/ under {exp_dir}; 0 files", file=sys.stderr)
        return files, excluded

    for src in sorted(p for p in committed_root.rglob("*") if p.is_file()):
        rel = src.relative_to(committed_root).as_posix()
        if is_hard_excluded(rel):
            excluded.append({"path": rel, "reason": "hard-exclusion: relative path matches a structural pattern"})
            continue
        data = src.read_bytes()
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            text = None
        if text is not None:
            hit = _content_hard_exclusion_hit(text)
            if hit:
                raise SystemExit(
                    f"CONTAINMENT: hard-excluded pattern '{hit}' found in {src}; refusing to build"
                )
        dst = out_dir / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(data)
        files[rel] = sha256_bytes(data)
    return files, excluded


def build_rows(
    rows_dir: Path, out_dir: Path, sources: list[dict[str, Any]]
) -> tuple[dict[str, Any], dict[str, int], dict[str, str]]:
    """Returns (cells_report, excluded_counts, sources_present).

    sources_present maps every source that appears in at least one KEPT row
    (with text or text-free) to its verdict, so the README can render the
    license-and-attribution section and verify_exhaust.py can check the
    permitted-with-conditions disclosure landed.
    """
    cells_report: dict[str, Any] = {}
    excluded_counts: dict[str, int] = {}
    sources_present: dict[str, str] = {}
    jsonl_files = sorted(rows_dir.glob("*.jsonl"))
    if not jsonl_files:
        print(f"[build-exhaust] no *.jsonl files under {rows_dir}; 0 cells", file=sys.stderr)
    for src_file in jsonl_files:
        cell_id = src_file.stem
        if is_hard_excluded(cell_id):
            raise SystemExit(f"CONTAINMENT: hard-excluded cell id '{cell_id}' in {src_file}; refusing to build")
        kept: list[dict[str, Any]] = []
        n_kept_with_text = 0
        n_kept_text_free = 0
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
            if verdict in TEXT_PERMITTED_VERDICTS:
                kept.append(row)
                n_kept_with_text += 1
                sources_present[source] = verdict
            elif verdict == "text-free-only":
                kept.append(strip_text_bearing(row))
                n_kept_text_free += 1
                sources_present[source] = verdict
            else:  # forbidden, pending-audit
                excluded_counts[source] = excluded_counts.get(source, 0) + 1
        out_cell = out_dir / cell_id
        out_cell.mkdir(parents=True, exist_ok=True)
        with (out_cell / "rows.jsonl").open("w", encoding="utf-8") as fh:
            for row in kept:
                fh.write(json.dumps(row, ensure_ascii=False) + "\n")
        cells_report[cell_id] = {
            "n_rows_kept_with_text": n_kept_with_text,
            "n_rows_kept_text_free": n_kept_text_free,
        }
    return cells_report, excluded_counts, sources_present


def readme_text(
    *, shape: str, manifest: dict[str, Any], provenance: dict[str, Any], repo_id: str, sources: list[dict[str, Any]]
) -> str:
    slug = manifest["slug"]
    license_gate_excluded = provenance.get("license_gate_excluded") or {}
    sources_present = provenance.get("sources_present") or {}

    if shape == "aggregate":
        files = provenance.get("files") or {}
        hard_excluded = provenance.get("excluded") or []
        by_top: dict[str, int] = {}
        for rel in files:
            top = rel.split("/", 1)[0]
            by_top[top] = by_top.get(top, 0) + 1
        lines_cells = (
            "\n".join(f"- `{top}`: {n} file(s)" for top, n in sorted(by_top.items()))
            or "(no files found)"
        )
        lines_cells = f"{len(files)} file(s) total, by top-level path:\n\n{lines_cells}"
        hard_excluded_lines = "\n".join(
            f"- `{e['path']}`: {e['reason']}" for e in hard_excluded
        ) or "(none)"
        cells_heading = "File inventory"
    else:
        cells = provenance.get("cells") or {}

        def cell_line(cid: str, info: dict[str, Any]) -> str:
            return f"- `{cid}`: kept_with_text={info.get('n_rows_kept_with_text', 0)}, kept_text_free={info.get('n_rows_kept_text_free', 0)}"

        lines_cells = "\n".join(cell_line(cid, info) for cid, info in sorted(cells.items())) or "(no cells found)"
        hard_excluded_lines = ""
        cells_heading = "Cells"

    excluded_lines = "\n".join(
        f"- `{src}`: {n} rows dropped entirely (gate verdict forbidden or pending-audit)"
        for src, n in sorted(license_gate_excluded.items())
    ) or "(none)"

    attribution_lines = []
    for source, verdict in sorted(sources_present.items()):
        entry = None
        for e in sources:
            keys = [str(e.get("key", "")).lower()] + [str(a).lower() for a in (e.get("aliases") or [])]
            if source.lower() in keys:
                entry = e
                break
        license_str = entry.get("license", "unknown") if entry else "unknown"
        conditions = entry.get("conditions", "").strip() if entry else ""
        attribution_lines.append(f"### `{source}` ({verdict})\n\n- License: {license_str}\n- Conditions: {conditions}\n")
    attribution_block = "\n".join(attribution_lines) or "(no row-level sources present in this build)"

    shape_desc = (
        "Aggregate-only: every file committed under this experiment's "
        "analysis-committed/ tree (dose-response tables, direction fits, gate "
        "AUROCs, manifests, and any other analysis artifact), copied byte-for-byte. "
        "No source question text, aliases, or per-row generation text -- "
        "analysis-committed/ never carries those."
        if shape == "aggregate"
        else "Row-level generation output, gated per reference/license-gates.md per source: "
        "some rows carry text (permitted sources), some are text-free (text-free-only "
        "sources), and forbidden or unaudited sources are dropped entirely, not redacted."
    )
    attribution_section = f"\n## License and Attribution\n\n{attribution_block}\n" if shape == "rows" else ""
    hard_exclusion_section = (
        f"\n## Hard-exclusion skips\n\nFiles whose relative path under `analysis-committed/` "
        f"matched a structural hard-exclusion pattern and were skipped (not copied):\n\n{hard_excluded_lines}\n"
        if shape == "aggregate"
        else ""
    )
    files_note = (
        "See `PROVENANCE.json` for the full machine-readable file list (relative path "
        "-> sha256) and the hard-exclusion skip list with reasons."
        if shape == "aggregate"
        else "See `PROVENANCE.json` for the full machine-readable provenance block. Each "
        "`<cell_id>/rows.jsonl` (row shape) holds the kept rows for that cell."
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

## {cells_heading}

{lines_cells}

## License-gate exclusions

{excluded_lines}
{attribution_section}{hard_exclusion_section}
## Files

{files_note}

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

    sources_present: dict[str, str] = {}
    files_report: dict[str, str] = {}
    hard_excluded: list[dict[str, str]] = []
    cells_report: dict[str, Any] = {}
    if shape == "aggregate":
        files_report, hard_excluded = build_aggregate(exp_dir, out_dir)
        excluded_counts: dict[str, int] = {}
    else:
        rows_dir = Path(args.rows_dir).resolve()
        if not rows_dir.is_dir():
            raise SystemExit(f"--rows-dir {rows_dir} is not a directory")
        cells_report, excluded_counts, sources_present = build_rows(rows_dir, out_dir, sources)

    generation_date = args.generation_date or datetime.now(timezone.utc).isoformat()
    repo_root = Path(
        subprocess.run(["git", "-C", str(exp_dir), "rev-parse", "--show-toplevel"], capture_output=True, text=True).stdout.strip()
        or exp_dir.parents[1]
    )
    provenance: dict[str, Any] = {
        "experiment_slug": slug,
        "amendment_path": str(amendment_path.relative_to(repo_root)) if repo_root in amendment_path.parents else str(amendment_path),
        "repo_commit_sha": git_commit_sha(exp_dir),
        "instrument_config_sha256": (manifest.get("instrument") or {}).get("pins") or {},
        "generation_date": generation_date,
        "shape": shape,
        "license_gate_excluded": excluded_counts,
        "sources_present": sources_present,
    }
    if shape == "aggregate":
        provenance["files"] = files_report
        provenance["excluded"] = hard_excluded
    else:
        provenance["cells"] = cells_report
    write_json(out_dir / "PROVENANCE.json", provenance)

    repo_id = args.repo_id or f"professorsynapse/eh-{slug}" + ("-rows" if shape == "rows" else "")
    (out_dir / "README.md").write_text(
        readme_text(shape=shape, manifest=manifest, provenance=provenance, repo_id=repo_id, sources=sources),
        encoding="utf-8",
    )

    if shape == "aggregate":
        print(f"[build-exhaust] shape={shape} slug={slug} files={len(files_report)} excluded={len(hard_excluded)} out_dir={out_dir}")
    else:
        print(f"[build-exhaust] shape={shape} slug={slug} cells={len(cells_report)} out_dir={out_dir}")
    if excluded_counts:
        print(f"[build-exhaust] license-gate excluded (dropped entirely): {excluded_counts}")
    if sources_present:
        print(f"[build-exhaust] license-gate sources present: {sources_present}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
