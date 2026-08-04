#!/usr/bin/env python3
"""Standalone driver: write-direction-naming-battery Arm A form-pass
regeneration.

Governed by NOTEBOOK.md "port-fidelity audit adjudicated; harness pinned;
Arm A form-pass regeneration authorized" (2026-07-30, LEAD). cell.yaml
registers a three-grader chain (`execution.graders`: grader:grade,
detector_v2:grade_one_v2, form_taxonomy:classify); the phase 2 run wired only
the first two, so no runlog row carries form_class. This driver regenerates
ARM A ONLY (7 sub-arms, P_CONFAB, 400 rows each = 2800) with the full
three-grader chain, on the exact same surface (checkpoint revision, seeds,
population order, batch_size, greedy decode) as phase 2, so every row must
reproduce phase 2's grading fields exactly.

Every pinned module this file touches (pipeline, steer_lib, gen_lib,
form_taxonomy -- all sha256-verified against experiment.yaml before this
driver runs) is imported UNMODIFIED; nothing here reimplements generation,
rendering, or grading logic. This file's only new code is: (1) the row loop
that calls form_taxonomy.classify on the merged grader fields before
redaction, mirroring steer_lib.run_rows's own record-then-redact structure;
(2) the private sidecar writer; (3) the row-by-row acceptance gate against
the phase 2 runlogs.

Output namespaces (never analysis/runlog/, the phase 2 evidence):
  - analysis/runlog_form/<arm>.jsonl          full pass, phase 2 fields
    plus form_class/form_matched_pattern_ids, same redact_fields applied.
  - analysis/runlog_form_smoke/<arm>.jsonl    smoke only (8 rows, a_baseline).
  - analysis/form_sidecar/<arm>.jsonl         PRIVATE: {row_key, answer_value,
    answer_text} only, for the registered blinded calibration slice.
    Gitignored under analysis/; never committed.

Acceptance gate (halt-on-fail, checked after every arm): row-by-row compare
against analysis/runlog/<arm>.jsonl on semantic_refuse, refused_v2,
degenerate, well_formed, terminated_naturally, readback_measured (abs tol
1e-6; both-null counts as match). Any mismatch stops the pass immediately;
the next arm is never started.
"""

from __future__ import annotations

import argparse
import gc
import json
import sys
import time
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[1]
for _p in (str(REPO_ROOT / "synaptic-tuner"), str(HERE)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import pipeline  # noqa: E402  (unmodified: ARMS, load_rows, load_directions, build_controllers, gain_for, DECODER_BLOCK_INDEX, MAX_NEW, BATCH_SIZE)
import steer_lib  # noqa: E402  (unmodified: load_model, render_prompt, run_batch_fixed, redact, load_jsonl)
import gen_lib  # noqa: E402  (unmodified: grade_row)
import form_taxonomy  # noqa: E402  (unmodified: classify, FORM_CLASSES)

ANALYSIS = HERE / "analysis"
FORM_NAMESPACE = "runlog_form"
FORM_SMOKE_NAMESPACE = "runlog_form_smoke"
SIDECAR_DIRNAME = "form_sidecar"

ACCEPTANCE_FIELDS = (
    "semantic_refuse", "refused_v2", "degenerate", "well_formed",
    "terminated_naturally", "readback_measured",
)
FLOAT_FIELDS = {"readback_measured"}
ABS_TOL = 1e-6

ARM_A_NAMES = [
    "a_baseline", "a_dose_0p25", "a_dose_0p5", "a_dose_0p75",
    "a_dose_1", "a_placebo_0p5", "a_placebo_1",
]
ARM_A = [a for a in pipeline.ARMS if a["name"] in ARM_A_NAMES]
assert [a["name"] for a in ARM_A] == ARM_A_NAMES, "Arm A order drifted from pipeline.ARMS"


def _runlog_path(arm_name: str, namespace: str) -> Path:
    return ANALYSIS / namespace / f"{arm_name}.jsonl"


def _sidecar_path(arm_name: str) -> Path:
    return ANALYSIS / SIDECAR_DIRNAME / f"{arm_name}.jsonl"


def _run_log(arm_name: str, run_config: dict, namespace: str):
    from shared.utilities.run_log import RunLog

    return RunLog(_runlog_path(arm_name, namespace), run_config=run_config)


def _existing_sidecar_keys(path: Path) -> set[str]:
    keys: set[str] = set()
    if path.exists():
        for row in steer_lib.load_jsonl(path):
            k = row.get("row_key")
            if k is not None:
                keys.add(str(k))
    return keys


def _append_sidecar(path: Path, row_key: str, answer_value: Any, answer_text: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(
            json.dumps(
                {"row_key": row_key, "answer_value": answer_value, "answer_text": answer_text},
                ensure_ascii=False, default=str,
            ) + "\n"
        )


def _validate_form_classes(records: list[dict]) -> None:
    bad = [r.get("row_key") for r in records if r.get("form_class") not in form_taxonomy.FORM_CLASSES]
    if bad:
        raise SystemExit(f"[run_arm_a_form_pass] form_class missing/invalid for {len(bad)} rows (e.g. {bad[:5]})")


def run_arm_form(
    model, tokenizer, device, controllers: dict[str, Any], layer_module,
    arm: dict[str, Any], rows_by_pop: dict[str, list[dict]], batch_size: int, namespace: str,
) -> list[dict]:
    name = arm["name"]
    population = arm["population"]
    readout = arm["readout"]
    multiplier = arm["multiplier"]
    rows = rows_by_pop[population]
    dose_abs, gain = pipeline.gain_for(readout, multiplier)

    log = _run_log(name, {"stage": "wdnb_form", "arm": name, "population": population, "readout": readout, "multiplier": multiplier}, namespace)
    sidecar_path = _sidecar_path(name)
    sidecar_keys = _existing_sidecar_keys(sidecar_path)

    controller = None
    handle = None
    if multiplier != 0.0:
        controller = controllers[readout]
        handle = layer_module.register_forward_hook(controller)

    try:
        done = log.done_keys()
        pending = [r for r in rows if r["row_key"] not in done]
        t0 = time.time()
        mode = "off" if multiplier == 0.0 else "gen_stream"
        strength = 0.0 if multiplier == 0.0 else gain
        for i in range(0, len(pending), batch_size):
            batch = pending[i:i + batch_size]
            prompts = [steer_lib.render_prompt(r) for r in batch]
            gen, _raw_rb = steer_lib.run_batch_fixed(model, tokenizer, device, controller, prompts, mode, strength, pipeline.MAX_NEW)
            for row, res in zip(batch, gen):
                grade = gen_lib.grade_row(res["text"], res["terminated_naturally"], row.get("aliases"))
                base_record = {
                    "row_key": row["row_key"], "role": row["role"], "population": row.get("population"),
                    "arm": name, "readout": readout, "multiplier": multiplier, "dose_abs": dose_abs,
                    "n_new_tokens": res["n_new_tokens"], "terminated_naturally": res["terminated_naturally"],
                    "readback_measured": res["readback_measured"], "answer_text": res["text"], **grade,
                }
                form = form_taxonomy.classify(base_record)
                full_record = {**base_record, **form}
                rk = row["row_key"]
                if rk not in sidecar_keys:
                    _append_sidecar(sidecar_path, rk, base_record.get("answer_value"), base_record.get("answer_text"))
                    sidecar_keys.add(rk)
                log.record(rk, steer_lib.redact(full_record))
            print(f"[run_arm_a_form_pass] {name}: {min(i + batch_size, len(pending))}/{len(pending)} ({time.time() - t0:.0f}s)", flush=True)
    finally:
        if handle is not None:
            handle.remove()
        if controller is not None:
            controller.reset()

    log.finalize({"n_rows": len(rows)})
    log.close()
    records = steer_lib.load_jsonl(_runlog_path(name, namespace))
    if len(records) != len(rows):
        raise SystemExit(f"[run_arm_a_form_pass] runlog_growth FAILED for arm {name!r}: expected {len(rows)} rows, got {len(records)}")
    _validate_form_classes(records)
    return records


def _fields_match(a: dict, b: dict, field: str) -> tuple[bool, Any, Any]:
    va, vb = a.get(field), b.get(field)
    if field in FLOAT_FIELDS:
        if va is None and vb is None:
            return True, va, vb
        if va is None or vb is None:
            return False, va, vb
        return abs(float(va) - float(vb)) <= ABS_TOL, va, vb
    return va == vb, va, vb


def acceptance_check(arm_name: str, phase2_path: Path, form_path: Path) -> dict:
    """Every row THIS PASS generated (`form_path`) must have a phase 2
    counterpart with matching field values. `phase2_only_keys` (rows phase 2
    has that this pass doesn't) is informational, not a failure condition --
    for the 8-row smoke that set is the other 392 a_baseline rows by design;
    for a full 400-row arm it is empty because run_arm_form's own
    runlog_growth check already enforces full-population coverage before
    this function is ever called. `form_only_keys` (rows this pass produced
    with no phase 2 counterpart) and any field-level mismatch are hard
    failures either way -- they mean this pass generated something phase 2
    never scored, which the deterministic-decode acceptance premise cannot
    explain innocently.
    """
    phase2_rows = {r["row_key"]: r for r in steer_lib.load_jsonl(phase2_path)}
    form_rows = {r["row_key"]: r for r in steer_lib.load_jsonl(form_path)}
    phase2_keys = set(phase2_rows)
    form_keys = set(form_rows)
    form_only_keys = sorted(form_keys - phase2_keys)
    mismatches = []
    for rk in sorted(phase2_keys & form_keys):
        p2 = phase2_rows[rk]
        f = form_rows[rk]
        for field in ACCEPTANCE_FIELDS:
            ok, va, vb = _fields_match(p2, f, field)
            if not ok:
                mismatches.append({"row_key": rk, "field": field, "phase2_value": va, "form_value": vb})
    return {
        "arm": arm_name,
        "rows_compared": len(phase2_keys & form_keys),
        "phase2_only_keys": sorted(phase2_keys - form_keys),
        "form_only_keys": form_only_keys,
        "mismatches": mismatches,
        "passed": (not form_only_keys) and (not mismatches) and (len(phase2_keys & form_keys) == len(form_keys)),
    }


def cmd_smoke(args: argparse.Namespace) -> int:
    if not args.i_know_this_runs_on_gpu:
        print("[run_arm_a_form_pass] smoke loads the model and generates on GPU; refusing without --i-know-this-runs-on-gpu.", file=sys.stderr)
        return 2

    rows_by_pop = pipeline.load_rows()
    directions = pipeline.load_directions()
    model, tokenizer, device = steer_lib.load_model()
    from MechInterp.intervention import get_decoder_layer

    layer_module = get_decoder_layer(model, pipeline.DECODER_BLOCK_INDEX)
    controllers = pipeline.build_controllers(directions)

    import torch

    try:
        smoke_rows = {"P_CONFAB": rows_by_pop["P_CONFAB"][:8]}
        arm = {"name": "a_baseline", "population": "P_CONFAB", "readout": "c_hat", "multiplier": 0.0}
        records = run_arm_form(model, tokenizer, device, controllers, layer_module, arm, smoke_rows, 8, FORM_SMOKE_NAMESPACE)
    finally:
        del model
        gc.collect()
        torch.cuda.empty_cache()

    result = acceptance_check("a_baseline_smoke", ANALYSIS / "runlog" / "a_baseline.jsonl", _runlog_path("a_baseline", FORM_SMOKE_NAMESPACE))
    form_classes = sorted({r["form_class"] for r in records})
    out = {"n_records": len(records), "form_classes_seen": form_classes, "acceptance": result}
    print(json.dumps(out, indent=2, default=str), flush=True)
    (ANALYSIS / "arm_a_form_smoke_summary.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    if not result["passed"]:
        print("[run_arm_a_form_pass] SMOKE ACCEPTANCE FAILED", file=sys.stderr)
        return 3
    print("[run_arm_a_form_pass] SMOKE PASSED (form_class present on all 8 rows, acceptance gate clean)", flush=True)
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    if not args.i_know_this_runs_on_gpu:
        print("[run_arm_a_form_pass] run is the full 2800-generation Arm A regeneration; refusing without --i-know-this-runs-on-gpu.", file=sys.stderr)
        return 2

    t0 = time.time()
    rows_by_pop = pipeline.load_rows()
    directions = pipeline.load_directions()
    model, tokenizer, device = steer_lib.load_model()
    from MechInterp.intervention import get_decoder_layer

    layer_module = get_decoder_layer(model, pipeline.DECODER_BLOCK_INDEX)
    controllers = pipeline.build_controllers(directions)

    import torch

    all_results: dict[str, Any] = {}
    halted = None
    try:
        for arm in ARM_A:
            name = arm["name"]
            print(f"[run_arm_a_form_pass] running arm {name!r} (population={arm['population']}, readout={arm['readout']}, multiplier={arm['multiplier']})", flush=True)
            records = run_arm_form(model, tokenizer, device, controllers, layer_module, arm, rows_by_pop, pipeline.BATCH_SIZE, FORM_NAMESPACE)
            acceptance = acceptance_check(name, ANALYSIS / "runlog" / f"{name}.jsonl", _runlog_path(name, FORM_NAMESPACE))
            form_counts: dict[str, int] = {}
            for r in records:
                fc = r.get("form_class")
                form_counts[fc] = form_counts.get(fc, 0) + 1
            sidecar_n = len(steer_lib.load_jsonl(_sidecar_path(name)))
            all_results[name] = {
                "n": len(records), "form_class_counts": form_counts,
                "sidecar_n": sidecar_n, "acceptance": acceptance,
            }
            print(json.dumps(all_results[name], indent=2, default=str), flush=True)
            if not acceptance["passed"]:
                halted = name
                print(f"[run_arm_a_form_pass] ACCEPTANCE GATE FAILED at arm {name!r}; HALTING, not continuing to next arm.", file=sys.stderr)
                break
    finally:
        del model
        gc.collect()
        torch.cuda.empty_cache()

    out = {
        "arms": all_results,
        "halted_at": halted,
        "elapsed_s": time.time() - t0,
    }
    (ANALYSIS / "arm_a_form_pass_summary.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    print(json.dumps(out, indent=2, default=str), flush=True)
    return 1 if halted else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_smoke = sub.add_parser("smoke", help="8-row a_baseline smoke into analysis/runlog_form_smoke/, checks form_class + acceptance gate")
    p_smoke.add_argument("--i-know-this-runs-on-gpu", action="store_true")
    p_smoke.set_defaults(func=cmd_smoke)

    p_run = sub.add_parser("run", help="full Arm A regeneration (7 sub-arms, 2800 rows) into analysis/runlog_form/")
    p_run.add_argument("--i-know-this-runs-on-gpu", action="store_true")
    p_run.set_defaults(func=cmd_run)

    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
