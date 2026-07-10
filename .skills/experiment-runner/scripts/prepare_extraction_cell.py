#!/usr/bin/env python3
"""Prepare ONE hidden-state extraction behind a fail-closed gate (architecture §4).

Location: .skills/experiment-runner/scripts/prepare_extraction_cell.py (canonical
    source; synced to .claude/ and .agents/ via sync_skills.py).
Sibling of prepare_local_cell.py, but for the OFF-MATRIX extraction capability:
    it operates on a single extraction config and NEVER touches expand_matrix or
    the locked 19/9/2 count assertions (extraction is exploratory, §4.1).

GPU-FREE / GPU-REQUIRED boundary (§10), made explicit by the --run-extraction flag:
  * default (no --run-extraction): GPU-FREE. Parse the config, run the resolver,
    run the E1..E4 gate, write a temp EFFECTIVE config with the resolved
    aligned_run_record_id, and print a PASS/SKIP report. Launch NOTHING. This is
    the CI-testable path.
  * --run-extraction: GPU-REQUIRED. After the gate PASSes, shell out to the merged
    harness `hidden_state_probe.py --config <effective-config>`. On a SKIP, the
    harness is NOT invoked: print the skip reason and exit 0 (exploratory degrade,
    NOT an error).

Link-never-mutate (§5.5 / §9): the resolver writes the id into a TEMP effective
    config, NEVER into the committed hidden_state_probe.yaml (which keeps
    aligned_run_record_id: null as the placeholder + loud-fail contract). This
    script never writes into experiment/phase1/run_records/.

Usage:
    python3 prepare_extraction_cell.py --config <extraction.yaml>
    python3 prepare_extraction_cell.py --config <extraction.yaml> --run-extraction
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import check_prereqs  # noqa: E402
import resolve_run_record  # noqa: E402

# Default extraction config + the merged harness, relative to the research repo.
_DEFAULT_CONFIG_REL = "experiments/common/configs/knowledge-probe/hidden_state_probe.yaml"
_HARNESS_REL = "experiments/common/knowledge_probe/hidden_state_probe.py"


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Prepare one hidden-state extraction (gate + resolve; "
        "GPU-free by default).")
    parser.add_argument(
        "--config", default=None,
        help=f"Extraction config YAML (default: <repo>/{_DEFAULT_CONFIG_REL}).")
    parser.add_argument(
        "--run-extraction", action="store_true",
        help="GPU-REQUIRED: invoke the harness after the gate PASSes. Default OFF "
        "(gate + report only, GPU-free).")
    parser.add_argument(
        "--research-repo-root", default=None,
        help="Research repo root (default: inferred from this script's location).")
    parser.add_argument(
        "--allow-unverified", action="store_true",
        help="Opt-in escape hatch (§5.4): link a run record whose outcome is not "
        "verified (e.g. the dpo arm). Default OFF (fail-closed).")
    return parser


def _infer_repo_root() -> Path:
    """Walk up to the repo root (the first ancestor with experiment/phase1/).

    The walk-up is location-robust across the canonical tree
    (.skills/<skill>/scripts, 3 deep) and the generated mirrors
    (.{claude,agents}/skills/<skill>/scripts, 4 deep), so no fixed parent index is
    assumed. The fallback only guards a detached/synthetic layout where the
    sentinel is absent; it walks up to the first ancestor that has a sibling
    bin/sync_skills.py (the repo-root marker) and finally degrades to the parent that
    is correct for the canonical 3-deep layout.
    """
    here = SCRIPT_DIR.resolve()
    for parent in here.parents:
        if (parent / "experiment" / "phase1").is_dir():
            return parent
    for parent in here.parents:
        if (parent / "bin" / "sync_skills.py").is_file():
            return parent
    return here.parents[3]


def _write_effective_config(config: dict, resolved_ids: dict[str, str]) -> Path:
    """Write a TEMP effective config with the resolved aligned_run_record_id.

    The committed YAML is never mutated (§5.5). When exactly one active arm is
    resolved, its id populates manifest_provenance.aligned_run_record_id so the
    harness's D-bis finalize gate sees a populated link. The temp file path is
    returned for the harness invocation.
    """
    effective = json.loads(json.dumps(config))  # deep copy via round-trip
    prov = effective.setdefault("manifest_provenance", {})
    # The MVP config has a single active arm; if multiple resolve, they must
    # agree (the gate already fail-closes on disagreement), so any value is the
    # shared id. Take the first deterministically.
    if resolved_ids:
        prov["aligned_run_record_id"] = sorted(resolved_ids.values())[0]
    fd, tmp_name = tempfile.mkstemp(prefix="extraction_effective_", suffix=".yaml")
    with open(fd, "w", encoding="utf-8") as handle:
        yaml.safe_dump(effective, handle, sort_keys=False)
    return Path(tmp_name)


def _report(payload: dict) -> None:
    print(json.dumps(payload, indent=2, default=str))


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    repo_root = (Path(args.research_repo_root).resolve()
                 if args.research_repo_root else _infer_repo_root())
    config_path = (Path(args.config).resolve() if args.config
                   else (repo_root / _DEFAULT_CONFIG_REL).resolve())

    if not config_path.is_file():
        _report({"status": "error", "reason": f"config not found: {config_path}"})
        return 1

    with config_path.open(encoding="utf-8") as handle:
        config = yaml.safe_load(handle) or {}

    # GPU-free gate (E1..E4 + revision-pin WARN). SKIP-not-abort by design.
    gate = check_prereqs.check_extraction_cell(
        config=config,
        config_path=config_path,
        research_repo_root=repo_root,
        require_verified=not args.allow_unverified,
    )

    warnings = (gate.details or {}).get("warnings", [])
    if gate.skip:
        _report({
            "status": "SKIP",
            "config": str(config_path),
            "skip_reason": gate.skip_reason,
            "warnings": warnings,
            "note": "exploratory degrade — harness NOT invoked, exit 0",
        })
        return 0  # SKIP is a clean degrade, not an error.

    resolved_ids = (gate.details or {}).get("resolved_run_record_ids", {})
    effective_path = _write_effective_config(config, resolved_ids)

    report = {
        "status": "PASS",
        "config": str(config_path),
        "effective_config": str(effective_path),
        "resolved_run_record_ids": resolved_ids,
        "warnings": warnings,
        "gpu_required_next_step": "--run-extraction invokes the harness (GPU)",
    }

    if not args.run_extraction:
        report["note"] = "GPU-free gate PASSED; pass --run-extraction to launch the harness (GPU)."
        _report(report)
        return 0

    # GPU-REQUIRED path: invoke the merged harness with the effective config.
    harness_path = repo_root / _HARNESS_REL
    cmd = [sys.executable, str(harness_path), "--config", str(effective_path)]
    report["command"] = cmd
    _report(report)
    completed = subprocess.run(cmd)
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
