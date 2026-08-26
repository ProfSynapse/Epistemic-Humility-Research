#!/usr/bin/env python3
"""Orchestrator for qwen3-4b-l34-placebo-seed-census.

`--smoke` (CPU-only, no GPU, no model load -- the only mode this build task
is authorized to actually RUN) exercises, in order:
  1. frozen-reuse sha256 verification (provenance_l34.verify_frozen_reuse,
     against the REAL cell.yaml -- not a stub);
  2. fresh-direction generation for all 15 registered seeds (shape/norm/
     uniqueness/reproducibility checks, pure CPU, direction_draw.py);
  3. the REAL 185-row confab/held_out population load through
     pipeline_census_l34.load_pipeline_module()/load_confab_held_out() --
     this imports doubt-gated-caution-tighten's pipeline.py (verified by
     direct AST inspection to make no module-level GPU/model call: model
     load only happens inside run_full_census(), never called here) and
     reads only rows_with_text.jsonl + the L34 anchor extract, no GPU;
  4. score plumbing end-to-end (build-pool -> mock-grade -> apply ->
     QG-G1/QG-G2 arithmetic) over STUBBED per-seed generation rows
     (fabricated placeholder out_text tagged onto the REAL 185 row_keys
     from step 3 -- never real model output, never committed; written only
     under gitignored analysis/smoke/) combined with the REAL wicr decoy
     source at analysis/wicr_decoy_source/rows_with_generation.jsonl. This
     validates the pool-build/grading-join/gate-arithmetic code path
     without asserting anything about real gate outcomes -- stub rates are
     synthetic by construction and are NOT reported as a result.

Real generation (`--real`, not implemented in this build task) would call
pipeline_census_l34.run_full_census() directly, which is itself gated
behind `--i-know-this-is-the-real-generation-run` and requires the lead's
explicit GPU GO per this build's binding invariants. This orchestrator does
NOT add a second path to that function; it is invoked directly, not
wrapped, when the lead authorizes the real run.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import direction_draw  # noqa: E402
import pipeline_census_l34  # noqa: E402
import provenance_l34  # noqa: E402
import score_census_l34  # noqa: E402

SMOKE_ROOT = HERE / "analysis" / "smoke"
SMOKE_ROWS_DIR = SMOKE_ROOT / "rows"
SMOKE_ANALYSIS_DIR = SMOKE_ROOT / "score_analysis"
SMOKE_COMMITTED_DIR = SMOKE_ROOT / "score_committed"


def check_directions() -> dict[str, Any]:
    """Pure-CPU check over all 15 registered seeds: correct shape/hidden_dim,
    unit norm (within float tolerance), pairwise distinctness (no two seeds
    collide), and reproducibility (same seed -> byte-identical vector across
    two independent calls, i.e. the draw is a pure function of seed, not of
    call order or hidden global state)."""
    import numpy as np

    vectors = {}
    for seed in pipeline_census_l34.SEEDS:
        v1 = direction_draw.fresh_random_direction(seed)
        v2 = direction_draw.fresh_random_direction(seed)
        if v1.shape != (direction_draw.HIDDEN_DIM,):
            raise SystemExit(f"[smoke] seed {seed}: wrong shape {v1.shape}")
        norm = float(np.linalg.norm(v1))
        if abs(norm - 1.0) > 1e-9:
            raise SystemExit(f"[smoke] seed {seed}: not unit-norm ({norm})")
        if not np.array_equal(v1, v2):
            raise SystemExit(f"[smoke] seed {seed}: draw is not reproducible across calls")
        vectors[seed] = v1

    seeds = list(vectors.keys())
    for i, s1 in enumerate(seeds):
        for s2 in seeds[i + 1:]:
            if np.array_equal(vectors[s1], vectors[s2]):
                raise SystemExit(f"[smoke] seeds {s1} and {s2} produced IDENTICAL directions")

    return {
        "n_seeds": len(seeds), "hidden_dim": direction_draw.HIDDEN_DIM,
        "all_unit_norm": True, "all_pairwise_distinct": True, "reproducible": True,
    }


def check_row_population() -> dict[str, Any]:
    """Loads pipeline.py + the real 185-row confab/held_out population.
    No model load (pipeline_mod.ml is imported but never invoked here)."""
    pipeline_mod, pin_report = pipeline_census_l34.load_pipeline_module()
    confab_rows = pipeline_census_l34.load_confab_held_out(pipeline_mod)
    return {
        "n_rows": len(confab_rows),
        "row_keys_sample": sorted(r["row_key"] for r in confab_rows)[:3],
        "pins": {
            "doubt_gated_caution_tighten_verified": len(pin_report["pins"]["verified"]),
            "unpinned_load_bearing_flagged": len(pin_report["unpinned"]["unpinned_load_bearing_files"]),
        },
    }, confab_rows


def write_stub_generation_rows(confab_rows: list[dict[str, Any]], *, out_dir: Path = SMOKE_ROWS_DIR) -> dict[str, int]:
    """Fabricated placeholder generation rows for all 15 seeds over the REAL
    row_keys -- never real model output, written only under gitignored
    analysis/smoke/. Deterministic per-seed RNG marks ~15% of rows
    'refused' (detector-v2-matching boilerplate refusal text) so the
    downstream detector/pool/gate plumbing sees non-degenerate variation;
    this fraction is an arbitrary smoke-test choice, not a claim about real
    model behavior."""
    out_dir.mkdir(parents=True, exist_ok=True)
    counts = {}
    for seed in pipeline_census_l34.SEEDS:
        rng = random.Random(seed)
        rows = []
        for r in confab_rows:
            refused = rng.random() < 0.15
            out_text = (
                "I'm not able to help with that request."
                if refused else
                f"[SMOKE STUB seed={seed}] placeholder generated text, not real model output."
            )
            rows.append({
                "row_key": r["row_key"], "role": "confab", "seed": seed, "arm": "random_direction",
                "out_text": out_text,
                "old_grade": {"well_formed_correct": not refused},
            })
        path = out_dir / f"seed_{seed}.jsonl"
        with path.open("w", encoding="utf-8") as fh:
            for row in rows:
                fh.write(json.dumps(row, ensure_ascii=False) + "\n")
        counts[seed] = len(rows)
    return counts


def run_smoke() -> int:
    report: dict[str, Any] = {}

    print("[smoke] step 1: frozen-reuse sha256 verification", flush=True)
    report["frozen_reuse"] = provenance_l34.verify_frozen_reuse()
    print(f"[smoke]   verified {len(report['frozen_reuse']['verified'])}/6 pinned artifacts", flush=True)

    print("[smoke] step 2: direction generation (15 seeds)", flush=True)
    report["directions"] = check_directions()
    print(f"[smoke]   {report['directions']}", flush=True)

    print("[smoke] step 3: row-population load (no GPU)", flush=True)
    row_report, confab_rows = check_row_population()
    report["row_population"] = row_report
    print(f"[smoke]   {row_report}", flush=True)

    print("[smoke] step 4: stub generation rows + score plumbing", flush=True)
    stub_counts = write_stub_generation_rows(confab_rows)
    report["stub_rows_written"] = stub_counts

    manifest = score_census_l34.build_pool(
        seed=13, rows_dir=SMOKE_ROWS_DIR, analysis_dir=SMOKE_ANALYSIS_DIR, committed_dir=SMOKE_COMMITTED_DIR,
    )
    report["pool_manifest_summary"] = {k: v for k, v in manifest.items() if k != "shards"}
    report["pool_manifest_summary"]["n_shards"] = manifest["n_shards"]

    grading_manifest = score_census_l34.mock_grade_all_shards(
        manifest, analysis_dir=SMOKE_ANALYSIS_DIR, committed_dir=SMOKE_COMMITTED_DIR,
    )
    gm_path = SMOKE_ANALYSIS_DIR / "mock_grading_manifest.json"
    gm_path.parent.mkdir(parents=True, exist_ok=True)
    gm_path.write_text(json.dumps({k: v for k, v in grading_manifest.items()}, indent=2), encoding="utf-8")

    applied_report = score_census_l34.apply_grading(
        gm_path, analysis_dir=SMOKE_ANALYSIS_DIR, committed_dir=SMOKE_COMMITTED_DIR,
    )
    report["applied_summary"] = {
        "n_applied_rows": applied_report["n_applied_rows"],
        "voided_cells": applied_report["voided_cells"],
        "pooled_clear_positive_passed": applied_report["pooled_clear_positive"]["passed"],
    }

    census_rows_all = score_census_l34.load_census_rows(SMOKE_ROWS_DIR)
    applied_rows_path = SMOKE_ANALYSIS_DIR / "adjudication_applied.jsonl"
    applied_rows = []
    if applied_rows_path.is_file():
        with applied_rows_path.open(encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    applied_rows.append(json.loads(line))

    gates_report = score_census_l34.compute_seed_gates(
        census_rows_all, applied_rows,
        frozen_baseline_rate=0.11351351351351352, frozen_gated_lift=0.6270270270270271,
    )
    report["gate_plumbing"] = {
        "n_seeds_scored": len(gates_report["per_seed"]),
        "QG_G1_ran": "QG_G1_distributional_specificity" in gates_report,
        "QG_G2_ran": "QG_G2_sign_consistency" in gates_report,
        "note": "STUB rates -- fabricated placeholder text, NOT a real result.",
    }

    print("[smoke] SMOKE PASS: all four plumbing stages executed without error.", flush=True)
    print(json.dumps(report, indent=2), flush=True)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--smoke", action="store_true", help="CPU-only plumbing smoke; no GPU, no model load.")
    args = ap.parse_args()

    if args.smoke:
        return run_smoke()

    print(
        "[run_census_l34] No mode selected other than --smoke. Real generation "
        "is invoked directly via `python pipeline_census_l34.py "
        "--i-know-this-is-the-real-generation-run` once the lead gives GPU GO "
        "-- this orchestrator does not wrap or duplicate that gate.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
