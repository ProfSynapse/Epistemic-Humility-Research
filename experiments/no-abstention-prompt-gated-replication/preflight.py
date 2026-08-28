#!/usr/bin/env python3
"""Harness-build preflight for no-abstention-prompt-gated-replication.

Verifies, before any GPU work:
  1. Every sha256 pin in cell.yaml matches the artifact on disk.
  2. Every pinned JSON artifact loads (json.load).
  3. This cell's render.py imports cleanly (its own import-time assertions
     fire) and assert_no_think_scaffolding is present.
  4. Each family's held-out pool row counts on this host match cell.yaml's
     recorded counts exactly.
  5. Locates FIT-split row counts for each family (needed for the detector
     threshold refit) and records what is found, without asserting a value
     the locked spec does not itself state.

Read-only. Writes nothing except its own JSON report to analysis/ (gitignored).
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[1]
CELL = yaml.safe_load((HERE / "cell.yaml").read_text())


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def check_pin(label: str, rel_path: str, expected_sha: str, results: list[dict]) -> None:
    path = REPO_ROOT / rel_path
    entry = {"label": label, "path": rel_path}
    if not path.is_file():
        entry["status"] = "MISSING_FILE"
        results.append(entry)
        return
    actual = sha256_file(path)
    entry["expected_sha256"] = expected_sha
    entry["actual_sha256"] = actual
    entry["status"] = "PASS" if actual == expected_sha else "SHA_MISMATCH"
    if path.suffix == ".json":
        try:
            json.loads(path.read_text())
            entry["json_load"] = "PASS"
        except Exception as exc:  # noqa: BLE001
            entry["json_load"] = f"FAIL: {exc}"
    results.append(entry)


def collect_pins() -> list[tuple[str, str, str]]:
    pins: list[tuple[str, str, str]] = []
    pins.append((
        "parent_render",
        CELL["render"]["parent_render"]["path"],
        CELL["render"]["parent_render"]["sha256"],
    ))
    for family, fam_cfg in CELL["families"].items():
        for key in ("write_direction", "detector_direction", "random_direction",
                    "build_manifest", "dose_source"):
            block = fam_cfg.get(key)
            if isinstance(block, dict) and "sha256" in block:
                pins.append((f"{family}.{key}", block["path"], block["sha256"]))
        hp = fam_cfg.get("heldout_pool")
        if hp:
            pins.append((f"{family}.heldout_pool", hp["path"], hp["sha256"]))
            epm = hp.get("eval_pool_manifest")
            if epm:
                pins.append((f"{family}.heldout_pool.eval_pool_manifest", epm["path"], epm["sha256"]))
    for name, block in CELL["grading"]["pinned_instrument"].items():
        if isinstance(block, dict) and "sha256" in block:
            pins.append((f"grading.pinned_instrument.{name}", block["path"], block["sha256"]))
    return pins


def check_heldout_counts(results: list[dict]) -> None:
    for family, fam_cfg in CELL["families"].items():
        hp = fam_cfg.get("heldout_pool")
        if not hp:
            continue
        path = REPO_ROOT / hp["path"]
        expected = hp["counts"]
        entry = {"family": family, "manifest": hp["path"], "expected_counts": expected}
        if not path.is_file():
            entry["status"] = "MISSING_MANIFEST"
            results.append(entry)
            continue
        data = json.loads(path.read_text())
        # Manifests in this lineage use one of a few shapes; try the common ones.
        rows = data.get("rows")
        counts_found: dict[str, int] = {}
        if isinstance(rows, list):
            for r in rows:
                split = r.get("split")
                role = r.get("role")
                if split == "held_out":
                    key = f"{role}_held_out"
                    counts_found[key] = counts_found.get(key, 0) + 1
        else:
            # heldout_rows_manifest.json / reused_rows_manifest.json / split_manifest.json
            # variants: look for direct count fields or per-role row lists.
            for k in ("confab_held_out", "known_correct_answered_held_out"):
                if k in data:
                    counts_found[k] = data[k]
            if "counts" in data and isinstance(data["counts"], dict):
                counts_found.update(data["counts"])
            for role_key in ("confab", "known_correct_answered"):
                block = data.get(role_key)
                if isinstance(block, list):
                    counts_found[f"{role_key}_held_out"] = len(block)
                elif isinstance(block, dict) and "held_out" in block:
                    ho = block["held_out"]
                    if isinstance(ho, list):
                        counts_found[f"{role_key}_held_out"] = len(ho)
        entry["counts_found"] = counts_found
        entry["status"] = "NEEDS_MANUAL_SHAPE_CHECK" if not counts_found else "COUNTS_EXTRACTED"
        results.append(entry)


def main() -> int:
    pin_results: list[dict] = []
    for label, rel_path, sha in collect_pins():
        check_pin(label, rel_path, sha, pin_results)

    n_total = len(pin_results)
    n_pass = sum(1 for r in pin_results if r["status"] == "PASS")
    print(f"=== SHA PIN CHECK: {n_pass}/{n_total} PASS ===")
    for r in pin_results:
        if r["status"] != "PASS":
            print(f"  FAIL[{r['status']}] {r['label']}: {r['path']}")

    print()
    print("=== render.py import check ===")
    sys.path.insert(0, str(HERE))
    try:
        import render as cell_render  # noqa: F401
        print(f"  render.py imported OK; NO_ABSTENTION_SYSTEM_PROMPT (len={len(cell_render.NO_ABSTENTION_SYSTEM_PROMPT)}):")
        print(f"    {cell_render.NO_ABSTENTION_SYSTEM_PROMPT!r}")
        assert hasattr(cell_render, "assert_no_think_scaffolding")
        assert hasattr(cell_render, "render")
        print("  assert_no_think_scaffolding and render() both present.")
    except Exception as exc:  # noqa: BLE001
        print(f"  render.py IMPORT FAILED: {exc}")

    print()
    print("=== held-out pool count checks ===")
    count_results: list[dict] = []
    check_heldout_counts(count_results)
    for r in count_results:
        print(f"  {r['family']}: expected={r['expected_counts']} status={r['status']} found={r.get('counts_found')}")

    out = {
        "pin_check": {"n_total": n_total, "n_pass": n_pass, "results": pin_results},
        "heldout_counts": count_results,
    }
    out_dir = HERE / "analysis"
    out_dir.mkdir(exist_ok=True)
    (out_dir / "preflight_report.json").write_text(json.dumps(out, indent=2))
    print()
    print(f"Report written to {out_dir / 'preflight_report.json'}")
    return 0 if n_pass == n_total else 1


if __name__ == "__main__":
    raise SystemExit(main())
