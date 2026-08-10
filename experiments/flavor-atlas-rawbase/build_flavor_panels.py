#!/usr/bin/env python3
"""Deterministic panel builder for flavor-atlas-rawbase (AMENDMENT.md Design).

Maps three source pools into the internal-panel row schema (`row_key`,
`question`, `label`, plus `flavor`), no sampling, no filtering beyond what
each named source file already contains:

  - KUQ:      experiments/ood-breadth-beyond-selfaware/analysis/screen/kuq_screened.jsonl
  - AmbigQA:  experiments/ood-breadth-beyond-selfaware/analysis/screen/internal_panel_pool.jsonl
              (row_key values REUSED unchanged so its extraction stays
              comparable with rawbase-ambigqa-boundary-readout)
  - SelfAware: datasets/selfaware/SelfAware.json

FG0 panel integrity (gates.yaml `fg0_panel_integrity`) is verified BEFORE
anything is written: sha256 of each source file and its row/label/flavor
counts must equal the locked constants. Any mismatch is a hard stop
(nonzero exit) -- a changed pool would silently change which flavor is
being read (gates.yaml derivation).

Outputs three panel jsonls under analysis/panels/ (gitignored) plus a
counts-only panels_manifest.json. No row/question text is ever printed or
written to a manifest -- counts and shas only.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
EXP_DIR = Path(__file__).resolve().parent
GATES_PATH = EXP_DIR / "gates.yaml"

KUQ_SOURCE = REPO_ROOT / "experiments/ood-breadth-beyond-selfaware/analysis/screen/kuq_screened.jsonl"
AMBIGQA_SOURCE = REPO_ROOT / "experiments/ood-breadth-beyond-selfaware/analysis/screen/internal_panel_pool.jsonl"
SELFAWARE_SOURCE = REPO_ROOT / "datasets/selfaware/SelfAware.json"

KUQ_CATEGORIES = [
    "ambiguous",
    "controversial",
    "counterfactual",
    "false assumption",
    "future unknown",
    "unsolved problem",
]


class Fg0Violation(SystemExit):
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


def verify_fg0(gates: dict) -> dict:
    """Verify all fg0_panel_integrity checks. Returns a dict of computed
    source stats (counts + shas) for reuse in the manifest. Hard-stops
    (nonzero exit) on any mismatch.
    """
    checks = gates["fg0_panel_integrity"]["checks"]
    problems: list[str] = []
    stats: dict = {}

    # --- KUQ ---
    if not KUQ_SOURCE.is_file():
        raise Fg0Violation(f"FG0 STOP: kuq source missing: {KUQ_SOURCE}")
    kuq_sha = sha256_of(KUQ_SOURCE)
    kuq_rows = load_jsonl(KUQ_SOURCE)
    kuq_known = [r for r in kuq_rows if not r.get("unknown")]
    kuq_unknown = [r for r in kuq_rows if r.get("unknown")]
    kuq_flavor_counts = Counter(r.get("category") for r in kuq_unknown)

    if kuq_sha != checks["kuq_pool_sha256_must_equal"]:
        problems.append(f"kuq sha256 mismatch: got {kuq_sha}, expected {checks['kuq_pool_sha256_must_equal']}")
    if len(kuq_rows) != checks["kuq_rows_must_equal"]:
        problems.append(f"kuq rows mismatch: got {len(kuq_rows)}, expected {checks['kuq_rows_must_equal']}")
    if len(kuq_known) != checks["kuq_known_must_equal"]:
        problems.append(f"kuq known mismatch: got {len(kuq_known)}, expected {checks['kuq_known_must_equal']}")
    if len(kuq_unknown) != checks["kuq_unknown_must_equal"]:
        problems.append(f"kuq unknown mismatch: got {len(kuq_unknown)}, expected {checks['kuq_unknown_must_equal']}")
    for cat, expected in checks["kuq_flavor_counts_must_equal"].items():
        got = kuq_flavor_counts.get(cat, 0)
        if got != expected:
            problems.append(f"kuq flavor '{cat}' mismatch: got {got}, expected {expected}")

    stats["kuq"] = {
        "sha256": kuq_sha,
        "rows": len(kuq_rows),
        "known": len(kuq_known),
        "unknown": len(kuq_unknown),
        "flavor_counts": dict(kuq_flavor_counts),
    }

    # --- AmbigQA ---
    if not AMBIGQA_SOURCE.is_file():
        raise Fg0Violation(f"FG0 STOP: ambigqa source missing: {AMBIGQA_SOURCE}")
    ambigqa_sha = sha256_of(AMBIGQA_SOURCE)
    ambigqa_rows = load_jsonl(AMBIGQA_SOURCE)
    ambigqa_known = [r for r in ambigqa_rows if r.get("label") == "known"]
    ambigqa_unknown = [r for r in ambigqa_rows if r.get("label") == "unknown"]

    if ambigqa_sha != checks["ambigqa_pool_sha256_must_equal"]:
        problems.append(f"ambigqa sha256 mismatch: got {ambigqa_sha}, expected {checks['ambigqa_pool_sha256_must_equal']}")
    if len(ambigqa_rows) != checks["ambigqa_rows_must_equal"]:
        problems.append(f"ambigqa rows mismatch: got {len(ambigqa_rows)}, expected {checks['ambigqa_rows_must_equal']}")
    if len(ambigqa_known) != checks["ambigqa_known_must_equal"]:
        problems.append(f"ambigqa known mismatch: got {len(ambigqa_known)}, expected {checks['ambigqa_known_must_equal']}")
    if len(ambigqa_unknown) != checks["ambigqa_unknown_must_equal"]:
        problems.append(f"ambigqa unknown mismatch: got {len(ambigqa_unknown)}, expected {checks['ambigqa_unknown_must_equal']}")

    stats["ambigqa"] = {
        "sha256": ambigqa_sha,
        "rows": len(ambigqa_rows),
        "known": len(ambigqa_known),
        "unknown": len(ambigqa_unknown),
    }

    # --- SelfAware ---
    if not SELFAWARE_SOURCE.is_file():
        raise Fg0Violation(f"FG0 STOP: selfaware source missing: {SELFAWARE_SOURCE}")
    selfaware_doc = json.loads(SELFAWARE_SOURCE.read_text(encoding="utf-8"))
    selfaware_rows = selfaware_doc["example"]
    selfaware_answerable = [r for r in selfaware_rows if r.get("answerable") is True]
    selfaware_unanswerable = [r for r in selfaware_rows if r.get("answerable") is False]

    if len(selfaware_rows) != checks["selfaware_rows_must_equal"]:
        problems.append(f"selfaware rows mismatch: got {len(selfaware_rows)}, expected {checks['selfaware_rows_must_equal']}")
    if len(selfaware_answerable) != checks["selfaware_answerable_must_equal"]:
        problems.append(f"selfaware answerable mismatch: got {len(selfaware_answerable)}, expected {checks['selfaware_answerable_must_equal']}")
    if len(selfaware_unanswerable) != checks["selfaware_unanswerable_must_equal"]:
        problems.append(f"selfaware unanswerable mismatch: got {len(selfaware_unanswerable)}, expected {checks['selfaware_unanswerable_must_equal']}")

    stats["selfaware"] = {
        "rows": len(selfaware_rows),
        "answerable": len(selfaware_answerable),
        "unanswerable": len(selfaware_unanswerable),
    }

    if problems:
        detail = "\n  - ".join(problems)
        raise Fg0Violation(
            f"FG0 panel integrity STOP ({len(problems)} mismatch(es)); a changed "
            f"pool silently changes which flavor is being read:\n  - {detail}"
        )

    return {
        "kuq_rows": kuq_rows,
        "kuq_known": kuq_known,
        "kuq_unknown": kuq_unknown,
        "ambigqa_rows": ambigqa_rows,
        "selfaware_rows": selfaware_rows,
        "stats": stats,
    }


def build_kuq_panel(kuq_rows: list[dict]) -> list[dict]:
    """kuq-{index:06d}, deterministic file order, no sampling/filtering.
    label: known/unknown convention. flavor: category for unknown rows,
    "known" for known rows.
    """
    out = []
    for i, r in enumerate(kuq_rows):
        is_unknown = bool(r.get("unknown"))
        out.append({
            "row_key": f"kuq-{i:06d}",
            "question": r["question"],
            "label": "unknown" if is_unknown else "known",
            "flavor": r.get("category") if is_unknown else "known",
        })
    return out


def build_ambigqa_panel(ambigqa_rows: list[dict]) -> list[dict]:
    """Reuses existing row_key values unchanged (comparability with
    rawbase-ambigqa-boundary-readout's extraction)."""
    out = []
    for r in ambigqa_rows:
        out.append({
            "row_key": r["row_key"],
            "question": r["question"],
            "label": r["label"],
            "flavor": "ambigqa",
        })
    return out


def build_selfaware_panel(selfaware_rows: list[dict]) -> list[dict]:
    """selfaware-{question_id}. answerable -> known, unanswerable -> unknown."""
    out = []
    for r in selfaware_rows:
        out.append({
            "row_key": f"selfaware-{r['question_id']}",
            "question": r["question"],
            "label": "known" if r.get("answerable") else "unknown",
            "flavor": "selfaware",
        })
    return out


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")


def counts_summary(kuq_panel, ambigqa_panel, selfaware_panel) -> dict:
    def lc(panel):
        return dict(Counter(r["label"] for r in panel))

    def fc(panel):
        return dict(Counter(r["flavor"] for r in panel))

    return {
        "kuq": {"n": len(kuq_panel), "by_label": lc(kuq_panel), "by_flavor": fc(kuq_panel)},
        "ambigqa": {"n": len(ambigqa_panel), "by_label": lc(ambigqa_panel)},
        "selfaware": {"n": len(selfaware_panel), "by_label": lc(selfaware_panel)},
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--panels-dir", type=Path, default=EXP_DIR / "analysis" / "panels")
    args = ap.parse_args()

    gates = load_gates()
    try:
        verified = verify_fg0(gates)
    except Fg0Violation as exc:
        print(str(exc), file=sys.stderr)
        return 1

    kuq_panel = build_kuq_panel(verified["kuq_rows"])
    ambigqa_panel = build_ambigqa_panel(verified["ambigqa_rows"])
    selfaware_panel = build_selfaware_panel(verified["selfaware_rows"])

    # row_key uniqueness sanity (deterministic construction should guarantee
    # this; fail closed if it does not).
    for name, panel in (("kuq", kuq_panel), ("ambigqa", ambigqa_panel), ("selfaware", selfaware_panel)):
        keys = [r["row_key"] for r in panel]
        if len(set(keys)) != len(keys):
            print(f"FG0 STOP: {name} panel row_key values are not unique ({len(keys)} rows, {len(set(keys))} unique)", file=sys.stderr)
            return 1

    args.panels_dir.mkdir(parents=True, exist_ok=True)
    write_jsonl(args.panels_dir / "kuq_panel.jsonl", kuq_panel)
    write_jsonl(args.panels_dir / "ambigqa_panel.jsonl", ambigqa_panel)
    write_jsonl(args.panels_dir / "selfaware_panel.jsonl", selfaware_panel)

    summary = counts_summary(kuq_panel, ambigqa_panel, selfaware_panel)

    manifest = {
        "fg0_status": "PASS",
        "sources": {
            "kuq": {"path": str(KUQ_SOURCE.relative_to(REPO_ROOT)), "sha256": verified["stats"]["kuq"]["sha256"]},
            "ambigqa": {"path": str(AMBIGQA_SOURCE.relative_to(REPO_ROOT)), "sha256": verified["stats"]["ambigqa"]["sha256"]},
            "selfaware": {"path": str(SELFAWARE_SOURCE.relative_to(REPO_ROOT))},
        },
        "counts": summary,
    }
    manifest_path = args.panels_dir / "panels_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    print(json.dumps({"fg0_status": "PASS", "counts": summary, "manifest": str(manifest_path)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
