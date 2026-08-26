#!/usr/bin/env python3
"""Frozen-reuse sha256 verification for qwen3-4b-l34-placebo-seed-census.

cell.yaml `frozen_reuse` names six artifacts this cell reuses byte-for-byte
from two resolved parents (doubt-gated-caution-tighten,
wide-instrument-control-rescore) and pins their sha256 under
`frozen_reuse_sha256`. This module recomputes each file's current sha256 and
compares it against that pinned block -- FAILS CLOSED (raises SystemExit) on
any mismatch or missing file, per this build's binding invariant ("verify
each against the sha256 values in this cell's cell.yaml frozen_reuse_sha256
block before running"). Never invents a pin cell.yaml does not already carry.

Reuses `sha256_of_file`/`load_yaml` from
wide-instrument-control-rescore/provenance.py directly (sys.path insert, no
copy) rather than re-deriving the same two one-line helpers a third time in
this repo.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parent.parent
WICR_DIR = REPO_ROOT / "experiments" / "wide-instrument-control-rescore"

if str(WICR_DIR) not in sys.path:
    sys.path.insert(0, str(WICR_DIR))
import provenance as wicr_prov  # noqa: E402


# frozen_reuse_sha256 key -> cell.yaml frozen_reuse.* path (dotted; "directions.u_d"
# style keys nest under frozen_reuse.directions, the rest are direct children).
FROZEN_REUSE_PATH_KEYS: dict[str, tuple[str, ...]] = {
    "u_d": ("directions", "u_d"),
    "c_hat": ("directions", "c_hat"),
    "gate_fit": ("gate_fit",),
    "standardization": ("standardization",),
    "historical_random_draw": ("historical_random_draw",),
    "frozen_arm_results": ("frozen_arm_results",),
}


def _resolve(frozen_reuse: dict[str, Any], keys: tuple[str, ...]) -> str:
    node: Any = frozen_reuse
    for k in keys:
        node = node[k]
    return node


def verify_frozen_reuse(cell_yaml_path: Path | None = None) -> dict[str, Any]:
    """Loads cell.yaml, resolves each frozen_reuse_sha256 entry's path via
    FROZEN_REUSE_PATH_KEYS, recomputes sha256, and compares. Raises
    SystemExit on ANY mismatch or missing entry/file (fail closed). Returns
    {"verified": [{"key", "path", "sha256"}]} on full success."""
    cell_yaml_path = cell_yaml_path or (HERE / "cell.yaml")
    cell = wicr_prov.load_yaml(cell_yaml_path)
    frozen_reuse = cell.get("frozen_reuse") or {}
    pinned = cell.get("frozen_reuse_sha256") or {}
    if not pinned:
        raise SystemExit(f"[provenance_l34] no frozen_reuse_sha256 block found in {cell_yaml_path}; refusing to proceed unverified.")

    verified = []
    mismatches = []
    for key, expected_sha in pinned.items():
        path_keys = FROZEN_REUSE_PATH_KEYS.get(key)
        if path_keys is None:
            mismatches.append({"key": key, "error": f"no FROZEN_REUSE_PATH_KEYS mapping for pinned key {key!r}"})
            continue
        try:
            rel_path = _resolve(frozen_reuse, path_keys)
        except KeyError as e:
            mismatches.append({"key": key, "error": f"cell.yaml frozen_reuse missing path segment: {e}"})
            continue
        abs_path = REPO_ROOT / rel_path
        if not abs_path.is_file():
            mismatches.append({"key": key, "path": rel_path, "error": "missing", "expected": expected_sha})
            continue
        actual = wicr_prov.sha256_of_file(abs_path)
        if actual != expected_sha:
            mismatches.append({"key": key, "path": rel_path, "expected": expected_sha, "actual": actual})
        else:
            verified.append({"key": key, "path": rel_path, "sha256": actual})

    if mismatches:
        raise SystemExit(
            "[provenance_l34] FROZEN-REUSE VERIFICATION FAILED "
            f"({cell_yaml_path}): {mismatches}\n"
            "Refusing to run against drifted frozen inputs."
        )

    return {"cell_yaml": str(cell_yaml_path), "verified": verified}


def main() -> int:
    import json
    report = verify_frozen_reuse()
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
