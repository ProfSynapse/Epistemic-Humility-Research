#!/usr/bin/env python3
"""SC0 (provenance and staging) stage-in for susceptibility-as-probe (M2).

CPU-only, no model, no GPU. Per gates.yaml `SC0_provenance_staging` and the
task directive: stages the FOUR pinned inputs (margin dataset, subsample id
list, c_hat direction, split manifest) as LOCAL COPIES (never symlinks, no
cross-worktree links) under this experiment's own gitignored
`analysis/staged_inputs/`, verifies each staged copy's sha256 against the
`cell.yaml`-pinned value (via `config.py`'s literal transcription), and
re-runs the leakage check in code: zero row_key intersection between the 760
M2 population rows (400 confab_subsample + 360 known_full from the staged
subsample-ids file) and the doubt-snap FIT split (split in {"fit",
"fit_only"} in the staged split manifest) that fit the hs20 c_hat direction.

Also copies the auxiliary (unpinned) question-text source
(`heldout_rows_for_steer.jsonl`, reused read-only from margin-mapping's own
staged inputs) so every later step reads only from THIS experiment's own
`analysis/staged_inputs/`, never reaching across into a sibling experiment's
directory at run time. No question/answer text, row_key, or category_canon
value ever enters the COMMITTED manifest -- only paths, sha256, and counts;
the manifest itself is written to `analysis/staging_manifest.json` (this
experiment's `.gitignore` excludes the whole `analysis/` tree, so this is
never accidentally committed).
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import config  # noqa: E402
import common  # noqa: E402

STAGED = config.EXPERIMENT_DIR / "analysis" / "staged_inputs" / config.FAMILY


def _copy_local(src: Path, dest: Path) -> None:
    """Local COPY, never a symlink -- explicit task directive ("local copies
    only, no cross-worktree symlinks")."""
    if not src.is_file():
        raise SystemExit(f"SC0 FAILED: missing source file: {src}")
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.is_symlink():
        raise SystemExit(f"SC0 FAILED: destination {dest} is an existing symlink; refusing to overwrite with a copy in place of a stale link.")
    shutil.copy2(src, dest)


PINNED_ENTRIES: list[dict[str, Any]] = [
    {"name": "margin_dataset", "source": config.MARGIN_DATASET_PATH,
     "sha256_pinned": config.MARGIN_DATASET_SHA256_PINNED,
     "dest": STAGED / "margin_dataset" / "qwen35_4b_margin_rows.jsonl", "kind": "jsonl"},
    {"name": "subsample_ids", "source": config.SUBSAMPLE_IDS_PATH,
     "sha256_pinned": config.SUBSAMPLE_IDS_SHA256_PINNED,
     "dest": STAGED / "subsample_ids_qwen35_4b.json", "kind": "json"},
    {"name": "c_hat_direction", "source": config.C_HAT_PATH,
     "sha256_pinned": config.C_HAT_SHA256_PINNED,
     "dest": STAGED / "directions" / "hs20" / "c_hat.json", "kind": "json"},
    {"name": "split_manifest", "source": config.SPLIT_MANIFEST_PATH,
     "sha256_pinned": config.SPLIT_MANIFEST_SHA256_PINNED,
     "dest": STAGED / "split_manifest.json", "kind": "json"},
]

AUXILIARY_ENTRIES: list[dict[str, Any]] = [
    {"name": "heldout_rows_for_steer", "source": config.HELDOUT_ROWS_FOR_STEER_PATH,
     "dest": STAGED / "heldout_rows_for_steer.jsonl", "kind": "jsonl",
     "note": "unpinned; question-text source, reused read-only from margin-mapping's own staged inputs"},
]


def _jsonl_row_count(path: Path) -> int:
    n = 0
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                n += 1
    return n


def stage_pinned(entry: dict[str, Any]) -> dict[str, Any]:
    src: Path = entry["source"]
    dest: Path = entry["dest"]
    _copy_local(src, dest)
    sha = common.sha256_of_file(dest)
    src_sha = common.sha256_of_file(src)
    if src_sha != entry["sha256_pinned"]:
        raise SystemExit(
            f"SC0 FAILED: {entry['name']!r} source sha256 {src_sha} does NOT "
            f"match the cell.yaml pin {entry['sha256_pinned']}. Source has "
            f"drifted since sign; do not proceed."
        )
    if sha != entry["sha256_pinned"]:
        raise SystemExit(
            f"SC0 FAILED: {entry['name']!r} staged-copy sha256 {sha} != "
            f"pinned {entry['sha256_pinned']} (copy corruption?)."
        )
    count = _jsonl_row_count(dest) if entry["kind"] == "jsonl" else None
    return {
        "name": entry["name"], "kind": entry["kind"], "pinned": True,
        "source_path": str(src), "dest_path": str(dest.relative_to(config.EXPERIMENT_DIR)),
        "sha256": sha, "count": count, "matches_cell_yaml_pin": True,
    }


def stage_auxiliary(entry: dict[str, Any]) -> dict[str, Any]:
    src: Path = entry["source"]
    dest: Path = entry["dest"]
    _copy_local(src, dest)
    sha = common.sha256_of_file(dest)
    count = _jsonl_row_count(dest) if entry["kind"] == "jsonl" else None
    return {
        "name": entry["name"], "kind": entry["kind"], "pinned": False,
        "source_path": str(src), "dest_path": str(dest.relative_to(config.EXPERIMENT_DIR)),
        "sha256": sha, "count": count, "note": entry.get("note"),
    }


def population_row_keys() -> dict[str, str]:
    """row_key -> role for the 760 M2 population rows, from the staged
    subsample-ids file: 400 confab_subsample.row_keys + 360
    known_full.row_keys."""
    ids = common.load_json(STAGED / "subsample_ids_qwen35_4b.json")
    confab = ids["confab_subsample"]["row_keys"]
    known = ids["known_full"]["row_keys"]
    if len(confab) != config.N_CONFAB:
        raise SystemExit(f"SC0 FAILED: confab_subsample has {len(confab)} row_keys, expected {config.N_CONFAB}")
    if len(known) != config.N_KNOWN:
        raise SystemExit(f"SC0 FAILED: known_full has {len(known)} row_keys, expected {config.N_KNOWN}")
    out = {rk: "confab" for rk in confab}
    for rk in known:
        out[rk] = "known_correct_answered"
    if len(out) != config.N_POPULATION:
        raise SystemExit(
            f"SC0 FAILED: confab/known row_key sets overlap "
            f"({len(confab) + len(known)} raw vs {len(out)} unique); "
            f"expected exactly {config.N_POPULATION} disjoint row_keys."
        )
    return out


def fit_split_row_keys() -> set[str]:
    """row_keys with split in {'fit','fit_only'} in the staged doubt-snap
    split manifest -- every row that participated in fitting u_d/u_p/
    caution/c_hat."""
    manifest = common.load_json(STAGED / "split_manifest.json")
    return {r["row_key"] for r in manifest["rows"] if r.get("split") in config.FIT_SPLIT_VALUES}


def leakage_check() -> dict[str, Any]:
    pop = set(population_row_keys().keys())
    fit = fit_split_row_keys()
    intersection = sorted(pop & fit)
    return {
        "rule": "zero row_key intersection between the 760 population rows and the doubt-snap FIT split",
        "n_population": len(pop),
        "n_fit_split": len(fit),
        "n_intersection": len(intersection),
        "intersection_sample": intersection[:10],
        "passed": len(intersection) == 0,
    }


def margin_dataset_covers_population() -> dict[str, Any]:
    """Sanity: the staged margin dataset's 760 row_keys are EXACTLY the
    population row_keys (no drift between M1's own margin-dataset row set
    and the subsample-ids row_key lists it was drawn from)."""
    pop = set(population_row_keys().keys())
    rows = common.load_jsonl(STAGED / "margin_dataset" / "qwen35_4b_margin_rows.jsonl")
    margin_keys = {r["row_key"] for r in rows}
    return {
        "n_margin_rows": len(rows),
        "n_population": len(pop),
        "sets_equal": margin_keys == pop,
        "margin_minus_population": sorted(margin_keys - pop)[:10],
        "population_minus_margin": sorted(pop - margin_keys)[:10],
    }


def main() -> int:
    hashes = config.verify_pinned_hashes()
    if not all(hashes.values()):
        raise SystemExit(f"SC0 FAILED: cell.yaml/gates.yaml sha256 mismatch vs experiment.yaml pins: {hashes}")

    pinned_records = [stage_pinned(e) for e in PINNED_ENTRIES]
    aux_records = [stage_auxiliary(e) for e in AUXILIARY_ENTRIES]

    leak = leakage_check()
    if not leak["passed"]:
        raise SystemExit(f"SC0 FAILED: leakage check failed: {json.dumps(leak, indent=2)}")

    margin_check = margin_dataset_covers_population()
    if not margin_check["sets_equal"]:
        raise SystemExit(f"SC0 FAILED: margin dataset row_keys != population row_keys: {json.dumps(margin_check, indent=2)}")

    manifest = {
        "config_hashes_verified": hashes,
        "n_pinned_files": len(pinned_records),
        "n_auxiliary_files": len(aux_records),
        "pinned_files": pinned_records,
        "auxiliary_files": aux_records,
        "leakage_check": leak,
        "margin_dataset_covers_population": margin_check,
    }
    common.write_json(config.EXPERIMENT_DIR / "analysis" / "staging_manifest.json", manifest)

    print(json.dumps({k: v for k, v in manifest.items() if k not in ("pinned_files", "auxiliary_files")}, indent=2), flush=True)
    for r in pinned_records:
        print(f"  PIN  {r['name']:25s} count={r['count']!s:8s} sha256={r['sha256'][:16]} matches_pin=OK", flush=True)
    for r in aux_records:
        print(f"  AUX  {r['name']:25s} count={r['count']!s:8s} sha256={r['sha256'][:16]}", flush=True)
    print(f"[staging] leakage check: PASSED (n_population={leak['n_population']}, n_fit_split={leak['n_fit_split']}, n_intersection=0)", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
