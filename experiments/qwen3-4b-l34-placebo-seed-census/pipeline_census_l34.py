#!/usr/bin/env python3
"""Generation driver for qwen3-4b-l34-placebo-seed-census.

Reuse, not reinvention: imports doubt-gated-caution-tighten's OWN
`pipeline.py` module (unmodified; loaded from THIS worktree's copy of that
cell directory, sys.path-scoped exactly like
wide-instrument-control-rescore/pipeline_rescore.py's `_import_from_dir`
helper -- ported here verbatim, same generic 15-line loader, not
reimplemented) and calls its own `load_rows` / `compute_gate_decisions` /
`run_one_row` functions DIRECTLY, unmodified. Unlike pipeline_rescore.py this
driver does NOT need a monkeypatch/tee around `run_full()`: it does not call
`run_full()` at all -- it orchestrates its OWN loop over confab-only held-out
rows (cell.yaml `arms[0].rows`: "the wicr 185-row confab wide-instrument
population"), swapping in a FRESH random direction per seed via
`model_lib.setup_hook_from_vector` (dgct's own function, already built for
exactly this "not a committed direction JSON" use case), so `run_one_row`'s
return dict already carries full per-row text with no capture trick needed.

OFFLINE PREP DEPENDENCY (same gap wide-instrument-control-rescore's
pipeline_rescore.py flagged for doubt-gated-caution-tighten): `pipeline.py`'s
`load_rows`/`compute_gate_decisions` read `analysis/rows_with_text.jsonl` and
`analysis/l34_anchor_extract.safetensors` relative to WHEREVER pipeline.py is
loaded from -- i.e. THIS worktree's `experiments/doubt-gated-caution-tighten/
analysis/` (gitignored, not shared across git worktrees). Those two files
plus their manifest were copied byte-for-byte from the canonical checkout
(`/home/profsynapse/code/Epistemic-Humility-Research/experiments/
doubt-gated-caution-tighten/analysis/`) into this worktree's mirror path,
sha256-verified identical before and after copy (see this build's report);
they are the FROZEN, already-generated (real GPU + private-repo materialize
step run once, historically) offline-prep artifacts dgct's own cell.yaml
"OFFLINE PREP" comment documents -- this driver does not regenerate them and
never will (no GPU/private-repo access needed for that regeneration here).

Dose: cell.yaml pins dose_target 200.0 (doubt-gated-caution-tighten's own
late-site dose). Random-direction strength convention matches
pipeline.py's own random_direction arm: sigma=1.0 on every generated
direction (direction_draw.py), so strength == dose_target exactly (no
population-derived scale, per random_direction_L34.json's own schema note).

Engine: tuner mechinterp InterventionHook path via dgct's `model_lib.py`
(`InterventionHook`, `GenerationInterventionController`, `get_decoder_layer`)
-- unmodified, imported through pipeline_mod's own `ml` binding, never
touched directly by this driver.

Scope: confab role, held_out split ONLY (185 rows) -- cell.yaml/gates.yaml
register no known_correct_answered population for this cell ("No cost gate:
the random arms run on confab rows only"), unlike dgct's own run_full()
which doses both roles for every arm.
"""

from __future__ import annotations

import argparse
import gc
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np
import torch

import direction_draw
import provenance_l34

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parent.parent
CELL_45_DIR = REPO_ROOT / "experiments" / "doubt-gated-caution-tighten"
WICR_DIR = REPO_ROOT / "experiments" / "wide-instrument-control-rescore"

ANALYSIS = HERE / "analysis"
COMMITTED = HERE / "analysis-committed"
DIRECTIONS_DIR = ANALYSIS / "directions"
ROWS_DIR = ANALYSIS / "rows"

DOSE_TARGET = 200.0  # cell.yaml dose.dose_target / gates.yaml dose.dose_target
LAYER_BLOCK = 33     # hs34
SEEDS = [920001, 920002, 920003, 920004, 920005, 920006, 920007, 920008, 920009,
         920010, 920011, 920012, 920013, 920014, 920015]  # gates.yaml seeds.random_census

# Load-bearing dgct scripts NOT covered by doubt-gated-caution-tighten's own
# experiment.yaml instrument.pins -- same PIN GAP wide-instrument-control-
# rescore's pipeline_rescore.py already disclosed for this exact cell
# (pipeline.py IS the load-bearing generation entry point this driver
# invokes; it and its sibling build/extract scripts are not individually
# pinned by dgct's own experiment.yaml).
CELL_45_UNPINNED_LOAD_BEARING = [
    "pipeline.py", "build_directions.py", "gate_fit.py",
    "build_random_direction.py", "extract_l34_anchor.py",
    "materialize_rows.py", "split_fit_heldout.py",
]

if str(WICR_DIR) not in sys.path:
    sys.path.insert(0, str(WICR_DIR))
import provenance as prov  # noqa: E402


def _import_from_dir(module_name: str, module_dir: Path, file_name: str):
    """Imports `file_name` from `module_dir` as `module_name`, with
    `module_dir` (and only it, for the duration of the import) prepended to
    sys.path so the module's own internal `import gen_lib`/`import grader`/
    etc. resolve exactly as they do when the source cell runs its own CLI.
    Ported verbatim (same 15 lines) from wide-instrument-control-rescore/
    pipeline_rescore.py's own `_import_from_dir` -- a generic importlib
    loader helper, not experiment-specific logic, reused rather than
    re-typed a third time in this repo."""
    added = str(module_dir) not in sys.path
    if added:
        sys.path.insert(0, str(module_dir))
    try:
        spec = importlib.util.spec_from_file_location(module_name, module_dir / file_name)
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        return module
    finally:
        if added:
            sys.path.remove(str(module_dir))


def check_offline_prep() -> list[str]:
    """Returns the list of MISSING offline-prep artifacts pipeline.py's
    load_rows/compute_gate_decisions need (rows_with_text.jsonl, the L34
    anchor extract + manifest), relative to THIS worktree's copy of
    doubt-gated-caution-tighten/analysis/. Does not raise -- callers decide
    whether to proceed."""
    required = [
        "analysis/rows_with_text.jsonl",
        "analysis/l34_anchor_extract.safetensors",
        "analysis/l34_anchor_extract_manifest.json",
    ]
    return [rel for rel in required if not (CELL_45_DIR / rel).is_file()]


def load_pipeline_module():
    """Verifies dgct's pinned files (fails loudly on drift, exactly as
    pipeline_rescore.py does for the same cell), records the known-unpinned
    load-bearing files for provenance, then imports pipeline.py from THIS
    worktree's dgct directory."""
    pin_report = prov.verify_pins(CELL_45_DIR, label="doubt-gated-caution-tighten")
    unpinned_report = prov.record_unpinned(CELL_45_DIR, CELL_45_UNPINNED_LOAD_BEARING, label="doubt-gated-caution-tighten")
    pipeline_mod = _import_from_dir("census_l34_pipeline", CELL_45_DIR, "pipeline.py")
    return pipeline_mod, {"pins": pin_report, "unpinned": unpinned_report}


def load_confab_held_out(pipeline_mod) -> list[dict[str, Any]]:
    """Reuses pipeline.py's OWN load_rows/compute_gate_decisions, unmodified,
    restricted to role=confab, split=held_out -- cell.yaml's registered
    185-row population. Asserts the count matches (185) rather than silently
    proceeding on a drifted population."""
    rows = pipeline_mod.compute_gate_decisions(pipeline_mod.load_rows("confab", "held_out"))
    if len(rows) != 185:
        raise SystemExit(
            f"[pipeline_census_l34] confab/held_out population is {len(rows)} rows, "
            "cell.yaml/AMENDMENT.md register 185 (the wicr wide-instrument confab "
            "population). Refusing to proceed against a drifted population."
        )
    return rows


def run_seed(pipeline_mod, model, tokenizer, dev, confab_rows: list[dict[str, Any]], seed: int,
             *, out_path: Path) -> dict[str, Any]:
    """Runs ONE fresh-seed random-direction arm over the 185 confab rows,
    flushing each row to `out_path` (JSONL) as it completes. Direction
    construction: direction_draw.fresh_random_direction(seed) (CPU, pure
    function of seed) fed to dgct's own `model_lib.setup_hook_from_vector`
    (sigma=1.0, layer_idx=33 == hs34) -- matches pipeline.py's own
    random_direction arm's strength convention (`strength_random_dir =
    dose_target`, since sigma=1.0 makes strength == realized setpoint
    exactly)."""
    ml = pipeline_mod.ml
    vector = direction_draw.fresh_random_direction(seed)
    hook, controller, layer_idx, sigma = ml.setup_hook_from_vector(vector, sigma=1.0, layer_idx=LAYER_BLOCK)
    # pipeline.py's own module namespace already binds get_decoder_layer
    # (`from MechInterp.intervention import get_decoder_layer`, same call
    # run_full()/run_smoke() make) -- reused via that binding rather than a
    # second direct tuner import.
    layer_module = pipeline_mod.get_decoder_layer(model, layer_idx)
    h_ctrl = layer_module.register_forward_hook(controller)

    n_fired = 0
    out_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with out_path.open("w", encoding="utf-8") as out_f:
            for r in confab_rows:
                rec = pipeline_mod.run_one_row(
                    model, controller, tokenizer, dev, r, r["fire"],
                    DOSE_TARGET, "confab",
                )
                rec["seed"] = seed
                rec["arm"] = "random_direction"
                rec["fire"] = r["fire"]
                rec["score_neg_z_d"] = r["score_neg_z_d"]
                rec["tau"] = r["tau"]
                if r["fire"]:
                    n_fired += 1
                out_f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                out_f.flush()
    finally:
        h_ctrl.remove()

    return {"seed": seed, "n_rows": len(confab_rows), "n_fired": n_fired, "rows_path": str(out_path)}


def run_full_census(*, out_dir: Path = ROWS_DIR) -> dict[str, Any]:
    """Real GPU run: all 15 seeds over the 185-row confab population,
    sequential (one model load, hook swapped between seeds -- mirrors
    pipeline.py's own run_full() pattern of removing/re-registering the
    forward hook between arms within a single model session)."""
    prov_report = provenance_l34.verify_frozen_reuse()
    pipeline_mod, pin_report = load_pipeline_module()
    confab_rows = load_confab_held_out(pipeline_mod)

    ml = pipeline_mod.ml
    model, tokenizer = ml.load_model()
    dev = next(model.parameters()).device

    per_seed_summaries = []
    try:
        for seed in SEEDS:
            summary = run_seed(pipeline_mod, model, tokenizer, dev, confab_rows, seed,
                                out_path=out_dir / f"seed_{seed}.jsonl")
            per_seed_summaries.append(summary)
            print(f"[pipeline_census_l34] seed={seed} n_fired={summary['n_fired']}/{summary['n_rows']} -> {summary['rows_path']}")
    finally:
        del model
        gc.collect()
        torch.cuda.empty_cache()

    report = {
        "dose_target": DOSE_TARGET, "layer": LAYER_BLOCK, "n_rows_per_seed": len(confab_rows),
        "seeds": per_seed_summaries, "frozen_reuse_verified": prov_report, "pins": pin_report,
    }
    prov.write_json(COMMITTED / "generation_manifest.json", report)
    print(json.dumps(report, indent=2))
    return report


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--i-know-this-is-the-real-generation-run", action="store_true")
    args = ap.parse_args()

    if not args.i_know_this_is_the_real_generation_run:
        print(
            "[pipeline_census_l34] This is the real GPU generation run (local "
            "3090, model load, 15 seeds x 185 confab rows). Requires lead "
            "GPU-GO approval per this build's binding invariants. Refusing "
            "without --i-know-this-is-the-real-generation-run.",
            file=sys.stderr,
        )
        return 2

    missing = check_offline_prep()
    if missing:
        print(
            f"[pipeline_census_l34] doubt-gated-caution-tighten offline prep missing "
            f"in this worktree: {missing}. Copy from the canonical checkout's "
            "experiments/doubt-gated-caution-tighten/analysis/ (see this build's "
            "report) before launching.",
            file=sys.stderr,
        )
        return 2

    run_full_census()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
