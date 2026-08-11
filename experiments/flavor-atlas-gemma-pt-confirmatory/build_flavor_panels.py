#!/usr/bin/env python3
"""Panel reuse for flavor-atlas-gemma-pt-confirmatory (AMENDMENT.md "Panels").

Byte-identical to flavor-atlas-rawbase: this cell does NOT rebuild, resample,
or filter anything. It verifies the three already-built panel jsonls under
`experiments/flavor-atlas-rawbase/analysis/panels/` against the pinned
sha256 values in gates.yaml (fixed before any Gemma flavor number existed),
then copies them unchanged into this cell's own `analysis/panels/`. A sha256
mismatch is a hard stop, not a silent rebuild -- the same discipline
flavor-atlas-rawbase's own build_flavor_panels.py applies to ITS upstream
sources, one level up.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from collections import Counter
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
EXP_DIR = Path(__file__).resolve().parent
GATES_PATH = EXP_DIR / "gates.yaml"

DEFAULT_SOURCE_DIR = REPO_ROOT / "experiments" / "flavor-atlas-rawbase" / "analysis" / "panels"

KUQ_CATEGORIES = [
    "ambiguous",
    "controversial",
    "counterfactual",
    "false assumption",
    "future unknown",
    "unsolved problem",
]


class Gg0Violation(SystemExit):
    pass


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def load_gates() -> dict:
    with GATES_PATH.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def verify_and_copy(source_path: Path, expected_sha256: str, dest_path: Path) -> dict:
    """Pure reuse-and-verify mechanism, exercised directly by the CPU smoke
    (with a self-computed expected sha) so its pass/fail logic is tested
    without needing the real 5540/2748/3369-row upstream panels, which are
    gitignored and may not be present in every checkout.
    """
    if not source_path.is_file():
        raise Gg0Violation(f"GG0 STOP: source panel missing: {source_path}")
    got_sha = sha256_of(source_path)
    if got_sha != expected_sha256:
        raise Gg0Violation(
            f"GG0 STOP: {source_path} sha256 mismatch: got {got_sha}, "
            f"expected {expected_sha256}. A changed panel silently changes "
            "which flavor is being read; refusing to reuse it."
        )
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source_path, dest_path)
    return {"source": str(source_path), "sha256": got_sha, "dest": str(dest_path)}


def counts_summary(kuq_rows, ambigqa_rows, selfaware_rows) -> dict:
    def lc(rows):
        return dict(Counter(r["label"] for r in rows))

    def fc(rows):
        return dict(Counter(r["flavor"] for r in rows))

    return {
        "kuq": {"n": len(kuq_rows), "by_label": lc(kuq_rows), "by_flavor": fc(kuq_rows)},
        "ambigqa": {"n": len(ambigqa_rows), "by_label": lc(ambigqa_rows)},
        "selfaware": {"n": len(selfaware_rows), "by_label": lc(selfaware_rows)},
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--source-dir", type=Path, default=DEFAULT_SOURCE_DIR,
                     help="flavor-atlas-rawbase's already-built panels dir")
    ap.add_argument("--panels-dir", type=Path, default=EXP_DIR / "analysis" / "panels")
    args = ap.parse_args()

    gates = load_gates()
    checks = gates["gg0_substrate_and_input_integrity"]["checks"]

    try:
        kuq_info = verify_and_copy(
            args.source_dir / "kuq_panel.jsonl",
            checks["kuq_panel_sha256_must_equal"],
            args.panels_dir / "kuq_panel.jsonl",
        )
        ambigqa_info = verify_and_copy(
            args.source_dir / "ambigqa_panel.jsonl",
            checks["ambigqa_panel_sha256_must_equal"],
            args.panels_dir / "ambigqa_panel.jsonl",
        )
        selfaware_info = verify_and_copy(
            args.source_dir / "selfaware_panel.jsonl",
            checks["selfaware_panel_sha256_must_equal"],
            args.panels_dir / "selfaware_panel.jsonl",
        )
    except Gg0Violation as exc:
        print(str(exc), file=sys.stderr)
        return 1

    kuq_rows = load_jsonl(args.panels_dir / "kuq_panel.jsonl")
    ambigqa_rows = load_jsonl(args.panels_dir / "ambigqa_panel.jsonl")
    selfaware_rows = load_jsonl(args.panels_dir / "selfaware_panel.jsonl")

    problems: list[str] = []
    if len(kuq_rows) != checks["kuq_rows_must_equal"]:
        problems.append(f"kuq rows {len(kuq_rows)} != {checks['kuq_rows_must_equal']}")
    kuq_known = sum(1 for r in kuq_rows if r["label"] == "known")
    kuq_unknown = sum(1 for r in kuq_rows if r["label"] == "unknown")
    if kuq_known != checks["kuq_known_must_equal"]:
        problems.append(f"kuq known {kuq_known} != {checks['kuq_known_must_equal']}")
    if kuq_unknown != checks["kuq_unknown_must_equal"]:
        problems.append(f"kuq unknown {kuq_unknown} != {checks['kuq_unknown_must_equal']}")
    kuq_flavor_counts = Counter(r["flavor"] for r in kuq_rows if r["label"] == "unknown")
    for cat, expected in checks["kuq_flavor_counts_must_equal"].items():
        got = kuq_flavor_counts.get(cat, 0)
        if got != expected:
            problems.append(f"kuq flavor '{cat}' {got} != {expected}")
    if len(ambigqa_rows) != checks["ambigqa_rows_must_equal"]:
        problems.append(f"ambigqa rows {len(ambigqa_rows)} != {checks['ambigqa_rows_must_equal']}")
    if len(selfaware_rows) != checks["selfaware_rows_must_equal"]:
        problems.append(f"selfaware rows {len(selfaware_rows)} != {checks['selfaware_rows_must_equal']}")

    if problems:
        detail = "\n  - ".join(problems)
        print(f"GG0 panel integrity STOP ({len(problems)} mismatch(es)):\n  - {detail}", file=sys.stderr)
        return 1

    summary = counts_summary(kuq_rows, ambigqa_rows, selfaware_rows)
    manifest = {
        "gg0_status": "PASS",
        "reused_from": {"kuq": kuq_info, "ambigqa": ambigqa_info, "selfaware": selfaware_info},
        "counts": summary,
    }
    manifest_path = args.panels_dir / "panels_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"gg0_status": "PASS", "counts": summary, "manifest": str(manifest_path)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
