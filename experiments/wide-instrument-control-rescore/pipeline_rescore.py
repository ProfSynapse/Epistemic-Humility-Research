#!/usr/bin/env python3
"""Stage 0 driver for wide-instrument-control-rescore: regenerates the arms
of the two source cells from their OWN committed pipeline scripts, at their
pinned shas, seeds, and committed direction artifacts -- AMENDMENT.md
"Design", Stage 0. GPU, local 3090, no cloud spend, not launched by the
harness-build task (see main()'s confirmatory guard).

PIN GAP (report this to the lead; do not resolve it here): the 4.5 cell's
own `doubt-gated-caution-tighten/experiment.yaml` `instrument.pins` covers
only cell.yaml, gates.yaml, gen_lib.py, grader.py, model_lib.py -- NOT
pipeline.py, build_directions.py, gate_fit.py, build_random_direction.py,
extract_l34_anchor.py, materialize_rows.py, split_fit_heldout.py, even
though pipeline.py is the load-bearing generation entry point this driver
invokes. `verify_pins` verifies exactly what IS pinned (fails loudly on any
mismatch there); `record_unpinned` records current sha256 of the rest for
provenance without fabricating a comparison the source cell never
registered. The 4.6 cell (j-space-calibrated-layer-contrast-qwen3-4b) and
its predecessor (j-space-midband-write-sweep-qwen3-4b, which supplies the
`pipeline` module run_contrast.py imports) have NO such gap: every module
either invokes is pinned in one of their two experiment.yaml files.

ROW-TEXT CAPTURE (a build-time engineering necessity, flagged for the
lead's sanity-check before real launch -- see this build's final report):
neither source cell's own CLI entry point (`pipeline.py --mode full`,
`run_contrast.py --mode full`) persists per-row generation text to disk --
both discard the per-row records after computing the aggregate
`full_summary.json` (confirmed by reading run_full()/run_layer() in both
pipelines: only run_smoke() writes row text). Stage 1 (wide re-score)
structurally requires that text. This driver captures it WITHOUT editing
either pinned script's bytes on disk (which would break the pin
verification above and would be reimplementing generation code, forbidden
by the build task):

  - 4.5 cell: `pipeline.run_one_row` already RETURNS `baseline_text`/
    `out_text` in its record dict (source read, lines ~179-188). This
    driver monkeypatches the imported module's `run_one_row` name to a
    thin tee that appends the unmodified return value to a JSONL sink
    before returning it unchanged, then calls the module's own unmodified
    `run_full()` -- one GPU pass, byte-identical aggregate output to what
    `run_full()` would produce standalone.
  - 4.6 predecessor cell: `pipeline.run_one_row` does NOT return text at
    all (source read, lines 126-165) -- only grades. There is no
    return-value tee available. This driver instead wraps the loaded
    tokenizer's bound `.decode` method to record every call's output text
    in call order. `run_one_row` makes exactly 1 decode call (base_text)
    normally, or 2 (base_text then out_text) when `row["fire"]` is True --
    a fact already knowable per row from `compute_gate_decisions`'s output,
    which this driver replicates ahead of the run via the SAME pinned
    function to predict the per-row call count and pair decode calls back
    to rows in order. Single-threaded, sequential row processing (confirmed
    in both pipelines' list-comprehension row loops) makes this ordering
    reconstruction exact, not heuristic.

Neither capture technique changes a single gate, threshold, seed, or
generation call; both are purely an I/O side-channel around otherwise
unmodified, pinned functions.
"""

from __future__ import annotations

import argparse
import contextlib
import importlib
import importlib.util
import sys
from pathlib import Path
from typing import Any

import provenance as prov

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parent.parent
CELL_45_DIR = REPO_ROOT / "experiments" / "doubt-gated-caution-tighten"
CELL_46_DIR = REPO_ROOT / "experiments" / "j-space-calibrated-layer-contrast-qwen3-4b"
CELL_46_PRED_DIR = REPO_ROOT / "experiments" / "j-space-midband-write-sweep-qwen3-4b"

ANALYSIS = HERE / "analysis"
REGEN_DIR = ANALYSIS / "regenerated"

# Load-bearing 4.5-cell scripts NOT covered by doubt-gated-caution-tighten's
# own instrument.pins (see module docstring PIN GAP).
CELL_45_UNPINNED_LOAD_BEARING = [
    "pipeline.py", "build_directions.py", "gate_fit.py",
    "build_random_direction.py", "extract_l34_anchor.py",
    "materialize_rows.py", "split_fit_heldout.py",
]


def _import_from_dir(module_name: str, module_dir: Path, file_name: str):
    """Imports `file_name` from `module_dir` as `module_name`, with
    `module_dir` (and only it, for the duration of the import) prepended to
    sys.path so the module's own internal `import gen_lib`/`import grader`/
    etc. (its own directory's siblings) resolve exactly as they do when the
    source cell runs its own CLI. Does not modify any file on disk."""
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


def _check_offline_prep(cell_dir: Path, required_relpaths: list[str], *, label: str) -> list[str]:
    """Returns the list of MISSING gitignored offline-prep artifacts
    (rows_with_text.jsonl, anchor extract tensors) this driver cannot
    itself produce (private HF staging repo + local never-committed alias
    checkout for materialize_rows.py; GPU anchor extraction). Does not
    raise -- the caller decides whether to proceed or report a blocked
    prerequisite, since running those prep scripts is a real-launch step
    this build task does not perform."""
    missing = []
    for rel in required_relpaths:
        if not (cell_dir / rel).is_file():
            missing.append(rel)
    return missing


# ---------------------------------------------------------------------------
# 4.5 cell: doubt-gated-caution-tighten
# ---------------------------------------------------------------------------

def regenerate_45(dose_target: float = 200.0) -> dict[str, Any]:
    pin_report = prov.verify_pins(CELL_45_DIR, label="doubt-gated-caution-tighten")
    unpinned_report = prov.record_unpinned(CELL_45_DIR, CELL_45_UNPINNED_LOAD_BEARING, label="doubt-gated-caution-tighten")

    missing = _check_offline_prep(
        CELL_45_DIR,
        ["analysis/rows_with_text.jsonl", "analysis/l34_anchor_extract.safetensors",
         "analysis/l34_anchor_extract_manifest.json"],
        label="doubt-gated-caution-tighten",
    )
    if missing:
        raise SystemExit(
            "[pipeline_rescore] doubt-gated-caution-tighten offline prep missing: "
            f"{missing}. Run (in that cell's own directory, GPU + private-repo access "
            "required, NOT performed by this build task): "
            "materialize_rows.py then extract_l34_anchor.py, per its cell.yaml "
            "'OFFLINE PREP' comment, before invoking pipeline_rescore.py --cell 45."
        )

    pipeline_mod = _import_from_dir("wicr_45_pipeline", CELL_45_DIR, "pipeline.py")

    # run_one_row's return dict carries `role` but not `arm` -- run_full()'s
    # own source (read in full) calls it in a FIXED, deterministic block
    # order: gated{confab,known}, random_direction{confab,known},
    # permuted_gate{combined pool, per-row role already resolved}. Replicate
    # the two population sizes (read-only, CPU, the SAME pinned
    # compute_gate_decisions/load_rows call run_full() makes internally) to
    # recover each captured record's arm by cumulative call position --
    # exact, not heuristic, because run_full()'s row loops are single-
    # threaded list comprehensions in this fixed order (source confirmed).
    confab_held = pipeline_mod.compute_gate_decisions(pipeline_mod.load_rows("confab", "held_out"))
    known_held = pipeline_mod.compute_gate_decisions(pipeline_mod.load_rows("known_correct_answered", "held_out"))
    n_confab, n_known = len(confab_held), len(known_held)

    rows_sink: list[dict[str, Any]] = []
    original_run_one_row = pipeline_mod.run_one_row

    def _tee_run_one_row(*args, **kwargs):
        rec = original_run_one_row(*args, **kwargs)
        rows_sink.append(rec)
        return rec

    pipeline_mod.run_one_row = _tee_run_one_row
    try:
        full_summary = pipeline_mod.run_full(dose_target)
    finally:
        pipeline_mod.run_one_row = original_run_one_row

    expected_total = 3 * (n_confab + n_known)
    if len(rows_sink) != expected_total:
        raise SystemExit(
            f"[pipeline_rescore] captured {len(rows_sink)} rows but expected "
            f"{expected_total} (3 arms x (n_confab={n_confab} + n_known={n_known})); "
            "arm-boundary slicing would be unsafe, refusing to tag arms."
        )
    boundaries = [
        ("gated", 0, n_confab + n_known),
        ("random_direction", n_confab + n_known, 2 * (n_confab + n_known)),
        ("permuted_gate", 2 * (n_confab + n_known), 3 * (n_confab + n_known)),
    ]
    for arm_name, lo, hi in boundaries:
        for rec in rows_sink[lo:hi]:
            rec["arm"] = arm_name

    out_dir = REGEN_DIR / "cell_45_doubt_gated_caution_tighten"
    prov.write_json(out_dir / "full_summary.json", full_summary)
    prov.write_jsonl(out_dir / "rows_with_generation.jsonl", rows_sink)
    prov.write_json(out_dir / "provenance.json", {"pins": pin_report, "unpinned": unpinned_report, "dose_target": dose_target})

    return {
        "cell": "doubt-gated-caution-tighten", "n_rows_captured": len(rows_sink),
        "full_summary_path": str(out_dir / "full_summary.json"),
        "rows_path": str(out_dir / "rows_with_generation.jsonl"),
    }


# ---------------------------------------------------------------------------
# 4.6 cell: j-space-calibrated-layer-contrast-qwen3-4b (+ predecessor)
# ---------------------------------------------------------------------------

def regenerate_46() -> dict[str, Any]:
    pin_report_contrast = prov.verify_pins(CELL_46_DIR, label="j-space-calibrated-layer-contrast-qwen3-4b")
    pin_report_pred = prov.verify_pins(CELL_46_PRED_DIR, label="j-space-midband-write-sweep-qwen3-4b")

    missing = _check_offline_prep(
        CELL_46_PRED_DIR,
        ["analysis/rows_with_text.jsonl", "analysis/layer_sweep_anchor_extract.safetensors"],
        label="j-space-midband-write-sweep-qwen3-4b",
    )
    if missing:
        raise SystemExit(
            "[pipeline_rescore] j-space-midband-write-sweep-qwen3-4b offline prep missing: "
            f"{missing}. Run (in that cell's own directory, GPU + private-repo access "
            "required, NOT performed by this build task): materialize_rows.py then "
            "extract_layer_sweep_anchor.py before invoking pipeline_rescore.py --cell 46."
        )

    # run_contrast.py inserts CELL_46_PRED_DIR onto sys.path itself and
    # imports `pipeline`/`model_lib`/`layers` from there -- importing it via
    # _import_from_dir with CELL_46_DIR (its own directory) reproduces its
    # own CLI's import shape exactly.
    run_contrast_mod = _import_from_dir("wicr_46_run_contrast", CELL_46_DIR, "run_contrast.py")
    pred_pipeline_mod = sys.modules.get("pipeline")  # imported by run_contrast_mod's own `from pipeline import ...`
    if pred_pipeline_mod is None:
        raise SystemExit("[pipeline_rescore] expected run_contrast.py to have imported the predecessor's `pipeline` module onto sys.modules; import shape drifted.")

    # Capture point: `pipeline.run_one_row` (predecessor cell) does NOT
    # return text (source read, lines 126-165) -- only grades. Rather than
    # wrap `tokenizer.decode` (which loses `terminated_naturally`, needed by
    # `grade_clean_tighten`, and forces replaying the fire-flag schedule to
    # know call arity), wrap `gl.run_pass_fixed` itself: `run_one_row` calls
    # it via `gl.run_pass_fixed(...)` (module-attribute lookup, so patching
    # `pred_pipeline_mod.gl.run_pass_fixed` intercepts every call made
    # through it) and it already returns (out, readback, terminated_naturally,
    # new_tokens) together per call, in order, with `mode` ("off" for the
    # always-made baseline pass, "gen_stream" for the dosed pass) directly
    # telling us which is which -- no fire-flag replay needed to know call
    # arity, only to know WHICH ROW consumed which call, which single-
    # threaded sequential iteration (confirmed in run_layer's source) still
    # guarantees.
    captured_calls: list[dict[str, Any]] = []
    original_run_pass_fixed = pred_pipeline_mod.gl.run_pass_fixed

    def _tee_run_pass_fixed(model, controller, enc, mode, strength, tokenizer, max_new=None):
        kwargs = {} if max_new is None else {"max_new": max_new}
        out, readback, terminated_naturally, new_tokens = original_run_pass_fixed(
            model, controller, enc, mode, strength, tokenizer, **kwargs
        )
        text = tokenizer.decode(new_tokens, skip_special_tokens=True)
        captured_calls.append({"mode": mode, "terminated_naturally": terminated_naturally, "text": text})
        return out, readback, terminated_naturally, new_tokens

    pred_pipeline_mod.gl.run_pass_fixed = _tee_run_pass_fixed
    try:
        full_summary = run_contrast_mod.run_full()
    finally:
        pred_pipeline_mod.gl.run_pass_fixed = original_run_pass_fixed

    # Reconstruct per-row (baseline_text, out_text, terminated_naturally) from
    # captured-call order. Replays the SAME selected_rows()/
    # compute_gate_decisions() calls run_contrast.run_layers() made
    # internally (pinned, deterministic, CPU-only, no GPU call) purely to
    # recover each row's `fire`/`aliases` in the exact order run_layers()'s
    # `for hs_index in HS_INDICES` / row-list iteration produced them, so
    # captured calls can be paired back to rows. `mode` is asserted per call
    # as a cross-check against the fire-flag prediction (belt-and-braces:
    # if the two disagree, this refuses rather than silently mis-pairing).
    rows_sink: list[dict[str, Any]] = []
    base_rows = run_contrast_mod.selected_rows(None)
    import random as _pyrandom
    _pyrandom.Random(20260707).shuffle(base_rows)  # mirrors run_contrast.run_full()'s own shuffle, same seed
    from layers import HS_INDICES as _HS_INDICES, layer_dir_name as _layer_dir_name  # already on sys.path via run_contrast import
    cursor = 0
    for hs_index in _HS_INDICES:
        gate_rows = run_contrast_mod.compute_gate_decisions(base_rows, hs_index)
        for r in gate_rows:
            base_call = captured_calls[cursor]
            if base_call["mode"] != "off":
                raise SystemExit(f"[pipeline_rescore] expected the first call for {r['row_key']}/hs{hs_index} to be mode='off'; got {base_call['mode']!r}; capture/row ordering drifted.")
            cursor += 1
            baseline_text = base_call["text"]
            if r["fire"]:
                dosed_call = captured_calls[cursor]
                if dosed_call["mode"] != "gen_stream":
                    raise SystemExit(f"[pipeline_rescore] expected the second call for {r['row_key']}/hs{hs_index} to be mode='gen_stream'; got {dosed_call['mode']!r}; capture/row ordering drifted.")
                cursor += 1
                out_text = dosed_call["text"]
                terminated_naturally = dosed_call["terminated_naturally"]
            else:
                out_text = baseline_text
                terminated_naturally = base_call["terminated_naturally"]
            # clean_tighten/well_formed_correct are not in run_one_row's
            # return dict for this predecessor pipeline (source read); grade
            # here using the SAME pinned grader/gen_lib functions the
            # predecessor's own run_one_row already imports at module scope
            # (pred_pipeline_mod.grader / pred_pipeline_mod.gl) -- reuse, not
            # re-derivation.
            ct = pred_pipeline_mod.gl.grade_clean_tighten(out_text, terminated_naturally)
            old_grade = pred_pipeline_mod.grader.grade_one(out_text, r.get("aliases"))
            rows_sink.append({
                "row_key": r["row_key"], "role": r["role"], "hs_index": hs_index,
                "arm": _layer_dir_name(hs_index),
                "fire": r["fire"], "baseline_text": baseline_text, "out_text": out_text,
                "terminated_naturally": terminated_naturally,
                "clean_tighten": ct["clean_tighten"],
                "well_formed_correct": old_grade["well_formed_correct"],
                "not_well_formed_correct": not old_grade["well_formed_correct"],
            })
    if cursor != len(captured_calls):
        raise SystemExit(
            f"[pipeline_rescore] call-reconstruction mismatch: consumed {cursor} of "
            f"{len(captured_calls)} captured run_pass_fixed calls; row/text pairing is "
            "unsafe, refusing to emit a rows_with_generation.jsonl that could silently "
            "misattribute text."
        )

    out_dir = REGEN_DIR / "cell_46_j_space_calibrated_layer_contrast"
    prov.write_json(out_dir / "full_summary.json", full_summary)
    prov.write_jsonl(out_dir / "rows_with_generation.jsonl", rows_sink)
    prov.write_json(out_dir / "provenance.json", {
        "pins_contrast_cell": pin_report_contrast, "pins_predecessor_cell": pin_report_pred,
    })

    return {
        "cell": "j-space-calibrated-layer-contrast-qwen3-4b", "n_rows_captured": len(rows_sink),
        "full_summary_path": str(out_dir / "full_summary.json"),
        "rows_path": str(out_dir / "rows_with_generation.jsonl"),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cell", choices=["45", "46", "both"], default="both")
    ap.add_argument("--dose", type=float, default=200.0, help="4.5 cell dose target (pinned default 200.0)")
    ap.add_argument("--i-know-this-is-the-real-regeneration-run", action="store_true")
    args = ap.parse_args()

    if not args.i_know_this_is_the_real_regeneration_run:
        print(
            "[pipeline_rescore] This is the real GPU Stage 0 regeneration run "
            "(local 3090, model load, private-repo row materialization). Not "
            "launched by the harness-build task; refusing without "
            "--i-know-this-is-the-real-regeneration-run. See RUNBOOK.md.",
            file=sys.stderr,
        )
        return 2

    results = []
    if args.cell in ("45", "both"):
        results.append(regenerate_45(args.dose))
    if args.cell in ("46", "both"):
        results.append(regenerate_46())

    import json
    print(json.dumps(results, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
