#!/usr/bin/env python3
"""Standalone paired-outcomes analysis over the tuner RunLogs written by
`run_contrast.py`.

Reads the per-row RunLog JSONL files under `analysis/runlog/<mode>/<layer>.jsonl`
directly (does not require re-running the contrast), reconstructs each
layer's per-row `clean_tighten` outcome on the confab rows, and reports:

  - the discordant-pair table (both-tighten / late-only-failure /
    mid-only-failure / neither) for best-mid vs hs34,
  - the exact binomial McNemar test on the discordant pairs,
  - the failure-ratio (late-only-failure / mid-only-failure),

for EVERY mid-band layer vs hs34, not just the one `run_contrast.py`
auto-selects as best-mid -- useful for auditing the selection call and for
the amendment's "direction survives, non-uniformly" style qualitative read
(see rep1's Outcome item 3 for the precedent this generalizes).

This script is read-only: it does not write summaries into analysis-committed/,
does not select doses, and does not decide gate pass/fail on its own (that
stays `run_contrast.py`'s job, using the SAME `mcnemar_exact` /
`paired_confab_outcomes` functions imported from it, so the two never drift).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / "j-space-midband-write-sweep-qwen3-4b"
for p in (str(SOURCE), str(HERE)):
    if p not in sys.path:
        sys.path.insert(0, p)

# `layers` is pure stdlib; `run_contrast`'s module-level surface is also
# torch-free (see its own docstring note) so this stays a CPU-only import.
from layers import HS_INDICES, LATE_REFERENCE_HS, layer_dir_name  # noqa: E402
from run_contrast import mcnemar_exact, paired_confab_outcomes  # noqa: E402

ANALYSIS = HERE / "analysis"


def load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.open(encoding="utf-8") if line.strip()]


def load_layer_records(mode: str, layer_name: str) -> list[dict]:
    """RunLog rows carry the recorded key plus the full `run_one_row` output
    fields at the top level (matching the convention documented in
    `experiments/common/README-runlog.md` and used by
    `pipeline_multisource.py:run_layer`'s on-disk reconstruction)."""
    path = ANALYSIS / "runlog" / mode / f"{layer_name}.jsonl"
    return load_jsonl(path)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=["smoke", "full"], default="full")
    parser.add_argument("--out", default=None, help="optional path to write JSON report")
    args = parser.parse_args(argv)

    late_name = layer_dir_name(LATE_REFERENCE_HS)
    late_records = load_layer_records(args.mode, late_name)
    if not late_records:
        print(
            f"[analyze-paired] no RunLog rows found for {late_name} at "
            f"analysis/runlog/{args.mode}/{late_name}.jsonl -- run run_contrast.py first",
            file=sys.stderr,
        )
        return 1

    report = {"mode": args.mode, "late_reference_layer": late_name, "vs_mid_band": {}}
    mid_names = [layer_dir_name(h) for h in HS_INDICES if h != LATE_REFERENCE_HS]
    for mid_name in mid_names:
        mid_records = load_layer_records(args.mode, mid_name)
        if not mid_records:
            print(f"[analyze-paired] WARNING: no RunLog rows for {mid_name}, skipping", file=sys.stderr)
            continue
        pairing = paired_confab_outcomes(mid_records, late_records)
        report["vs_mid_band"][mid_name] = pairing
        print(
            f"[analyze-paired] {mid_name} vs {late_name}: "
            f"n_paired={pairing['n_paired']} late_only_failure={pairing['late_only_failure']} "
            f"mid_only_failure={pairing['mid_only_failure']} "
            f"ratio={pairing['failure_ratio_late_over_mid']} "
            f"mcnemar_p={pairing['mcnemar_exact_p']:.4g}",
            flush=True,
        )

    if args.out:
        Path(args.out).write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(f"[analyze-paired] wrote {args.out}", flush=True)
    else:
        print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
