#!/usr/bin/env python3
"""Top-level CLI for idk-switch-naming-confirmatory: smoke -> 4-arm generation
-> deterministic F4/F5 screen -> HARD HALT before the blinded judge lane.

Adapted from `write-direction-naming-battery/pipeline.py` (source sha256
cce96d9df75877e791e61c115b2028fe359871c77d2a6ec4769a227ce6078614, matching
that file's own pin; read in full before writing this). Every direction,
scalar, and dose is loaded verbatim from cell.yaml, which itself transcribes
the naming battery's own pinned operating point; this script refits nothing.

Convention (this lineage, read in full before writing this): multiplier ==
0.0 is a TRUE no-hook baseline pass (controller=None), never a zero-gain hook
call -- baseline means untouched generation.

GOVERNANCE HALT (binding, per the harness-build assignment and
AMENDMENT.md "One stability regrade shard" / "Lead spot-check n=30 before any
gate adjudication"): this driver's `screen` stage is the LAST automated
stage. Building the judge pool, dispatching judge-subagent grading, and
running the axis arithmetic are separate, LEAD-RUN steps
(`build_judge_pool.py`, `apply_judge_grades.py`,
`axis_n1n2n3_arithmetic.py`) -- never chained automatically here, per the
mechinterp-cells skill's "Long GPU stage launch discipline" rule that a
pipeline chain must hard-halt (never auto-continue) at the blinded-grading
boundary.

This cell is DRAFT and NOT authorized to run on GPU (see AMENDMENT.md
"Status: draft"). No command in this script executes without the caller
explicitly passing `--i-know-this-runs-on-gpu` to a GPU subcommand; the CPU
subcommands (`screen`) never touch a GPU. Nothing in this harness build
passes that flag.

LOCAL-RUNTIME INVARIANT (.skills/mechinterp-cells/reference/modal-launch.md
"Local GPU runs execute in a pinned container"): every GPU subcommand here
must run inside the pinned mechinterp-runner image. This script does not
hard-code a bare conda python path (unlike the naming battery's own
pipeline.py); it is invoked with whatever `python3` the container provides.
At GPU-subcommand start it captures the container's provenance JSON line by
re-invoking the runner image's own `print_provenance.py` (the documented
downstream pattern) and HARD-FAILS unless the reported image digest is a real
sha256 that matches experiment.yaml's `instrument.runtime_image_digest`
pinned at sign -- see `read_container_provenance` below (lead-corrected
2026-07-31 against the real entrypoint contract).
"""

from __future__ import annotations

import argparse
import gc
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np
import yaml

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[1]
NAMING_BATTERY_COMMITTED = REPO_ROOT / "experiments" / "write-direction-naming-battery" / "analysis-committed"
# Directions live in the cell that actually committed them (build-time ruling
# 5 in AMENDMENT.md: the naming battery never committed a directions/ tree;
# registered paths in cell.yaml direction_readout and experiment.yaml inputs).
DOUBT_SNAP_COMMITTED = REPO_ROOT / "experiments" / "qwen35-4b-midband-doubt-snap" / "analysis-committed"
for _p in (str(REPO_ROOT / "synaptic-tuner"), str(HERE)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import screen_lib  # noqa: E402
import steer_lib  # noqa: E402

ANALYSIS = HERE / "analysis"
COMMITTED = HERE / "analysis-committed"
ROWS_PATH = ANALYSIS / "isnc_rows.jsonl"
CELL_YAML_PATH = HERE / "cell.yaml"

HS_INDEX = 20
DECODER_BLOCK_INDEX = 19
MAX_NEW = 200
BATCH_SIZE = 8

REFERENCE_DOSE_ABS = 12.608187917799976  # cell.yaml law.reference_dose_abs
SIGMA_C = 1.576023489724997               # cell.yaml law.standardization.sigma_c
SIGMA_RANDOM = 1.0                         # random_direction.json's own convention

# cell.yaml `arms` block, transcribed literally.
ARMS: list[dict[str, Any]] = [
    {"name": "a_baseline",    "population": "P_CONFAB", "readout": "c_hat",            "multiplier": 0.0},
    {"name": "a_dose_0p5",    "population": "P_CONFAB", "readout": "c_hat",            "multiplier": 0.5},
    {"name": "a_dose_1",      "population": "P_CONFAB", "readout": "c_hat",            "multiplier": 1.0},
    {"name": "a_placebo_1",   "population": "P_CONFAB", "readout": "random_direction", "multiplier": 1.0},
]
BASELINE_ARMS = {"a_baseline"}

# AMENDMENT.md "Design": "the naming battery's own cell.yaml `surface.seeds`
# block ... population_permutation 48260730, bootstrap 48260731,
# calibration_slice 48260732" (write-direction-naming-battery/cell.yaml
# lines 26-29). Every one of the naming battery's own registered seeds, not
# just its generation seeds (it registered none, since it generated
# greedily). See cell.yaml's own comment for the scoping note on form-judge's
# seeds (a different instrument, not included here).
NAMING_BATTERY_EXCLUDED_SEEDS = frozenset({48260730, 48260731, 48260732})


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return steer_lib.load_jsonl(path)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str), encoding="utf-8")


def runlog_path(tag: str, namespace: str = "runlog") -> Path:
    return ANALYSIS / namespace / f"{tag}.jsonl"


def _run_log(tag: str, run_config: dict[str, Any], namespace: str = "runlog"):
    from shared.utilities.run_log import RunLog

    return RunLog(runlog_path(tag, namespace), run_config=run_config)


def load_cell_config() -> dict[str, Any]:
    return yaml.safe_load(CELL_YAML_PATH.read_text(encoding="utf-8"))


def resolve_generation_config(cell_cfg: dict[str, Any]) -> dict[str, Any]:
    """Fail-closed resolution of cell.yaml `surface.generation` /
    `surface.seeds`. Refuses to return a usable config while any
    REGISTERED_AT_SIGN placeholder remains, or if the resolved
    `generation_sampling_seed` collides with a naming-battery seed. This is
    the single gate every GPU subcommand routes through before touching the
    model."""
    gen = cell_cfg["surface"]["generation"]
    seeds = cell_cfg["surface"]["seeds"]

    # decode_mode/do_sample/generation_sampling_seed are ALWAYS required
    # (they gate every arm, including the greedy baseline). temperature/
    # top_p are checked separately, below, ONLY once do_sample is known to
    # be True -- under greedy decode they are unused and may legitimately
    # stay REGISTERED_AT_SIGN forever.
    placeholders = [k for k in ("decode_mode", "do_sample") if gen.get(k) == "REGISTERED_AT_SIGN"]
    seed = seeds.get("generation_sampling_seed")
    if seed == "REGISTERED_AT_SIGN" or seed is None:
        placeholders.append("generation_sampling_seed")

    if placeholders:
        raise SystemExit(
            f"[pipeline] REFUSING to run: cell.yaml still carries unresolved "
            f"REGISTERED_AT_SIGN placeholder(s) {placeholders}. These are pinned "
            f"by the lead/PI at sign (see cell.yaml 'AMBIGUITY FLAGGED FOR SIGN' "
            f"comment); this harness will not guess a value."
        )

    seed_int = int(seed)
    if seed_int in NAMING_BATTERY_EXCLUDED_SEEDS:
        raise SystemExit(
            f"[pipeline] REFUSING to run: generation_sampling_seed {seed_int} is "
            f"one of the naming battery's own registered seeds "
            f"{sorted(NAMING_BATTERY_EXCLUDED_SEEDS)} "
            f"(write-direction-naming-battery/cell.yaml surface.seeds). "
            f"AMENDMENT.md requires a seed 'distinct from every seed the naming "
            f"battery used'."
        )

    decode_mode = gen["decode_mode"]
    do_sample = bool(gen["do_sample"])
    if decode_mode == "greedy" and do_sample:
        raise SystemExit("[pipeline] REFUSING to run: decode_mode == 'greedy' but do_sample == true (inconsistent).")
    if decode_mode == "sampled" and not do_sample:
        raise SystemExit("[pipeline] REFUSING to run: decode_mode == 'sampled' but do_sample == false (inconsistent).")
    if decode_mode not in ("greedy", "sampled"):
        raise SystemExit(f"[pipeline] REFUSING to run: unrecognized decode_mode {decode_mode!r} (must be 'greedy' or 'sampled').")
    if do_sample:
        for field in ("temperature", "top_p"):
            val = gen.get(field)
            if val == "REGISTERED_AT_SIGN" or not isinstance(val, (int, float)):
                raise SystemExit(
                    f"[pipeline] REFUSING to run: do_sample=true but {field!r} is "
                    f"REGISTERED_AT_SIGN or not a number ({val!r}); pinned by the "
                    f"lead/PI at sign."
                )

    return {
        "decode_mode": decode_mode,
        "do_sample": do_sample,
        "temperature": gen.get("temperature") if do_sample else None,
        "top_p": gen.get("top_p") if do_sample else None,
        "generation_sampling_seed": seed_int,
    }


def read_container_provenance() -> dict[str, Any]:
    """Capture the pinned mechinterp-runner container's provenance JSON line
    by re-invoking its provenance script, per the ACTUAL entrypoint contract
    (lead-verified against synaptic-tuner/docker/mechinterp-runner/
    {entrypoint.sh,print_provenance.py}, 2026-07-31): the entrypoint prints
    one JSON line with `"event": "mechinterp_runner_provenance"` to stdout at
    container start, and print_provenance.py is documented as directly
    invokable by downstream projects "to append its output to a run log". The
    image digest arrives via the IMAGE_DIGEST env var passed at `docker run`;
    absent that, the script emits an "unknown ..." placeholder, which this
    harness treats as NOT inside the pinned lane.

    HARD-FAIL (lead ruling; the modal-launch invariant says the line MUST
    appear in the run log): raises SystemExit unless (a) a provenance script
    is found and runs, (b) its image_digest starts with "sha256:", and (c)
    that digest equals experiment.yaml's instrument.runtime_image_digest
    (set at sign; unset means the cell is unsigned and must not run)."""
    import subprocess

    candidates = [
        Path("/usr/local/bin/print_provenance.py"),  # in-container location (entrypoint.sh)
        REPO_ROOT / "synaptic-tuner" / "docker" / "mechinterp-runner" / "print_provenance.py",
    ]
    script = next((p for p in candidates if p.is_file()), None)
    if script is None:
        raise SystemExit(
            "[pipeline] REFUSING to run: no mechinterp-runner provenance script "
            f"found (checked {[str(p) for p in candidates]}). GPU verbs must run "
            "inside the pinned mechinterp-runner container."
        )
    proc = subprocess.run([sys.executable, str(script)], capture_output=True, text=True)
    if proc.returncode != 0:
        raise SystemExit(f"[pipeline] REFUSING to run: provenance script failed: {proc.stderr.strip()}")
    line = proc.stdout.strip().splitlines()[-1]
    prov = json.loads(line)
    digest = str(prov.get("image_digest", ""))
    if not digest.startswith("sha256:"):
        raise SystemExit(
            "[pipeline] REFUSING to run: provenance image_digest is "
            f"{digest!r}, not a sha256 digest. Pass IMAGE_DIGEST at `docker run` "
            "(see docker/mechinterp-runner/README.md); a missing digest means "
            "this process is not in the pinned launch lane."
        )
    exp_yaml = yaml.safe_load((HERE / "experiment.yaml").read_text(encoding="utf-8"))
    pinned = (exp_yaml.get("instrument") or {}).get("runtime_image_digest")
    if pinned != digest:
        raise SystemExit(
            f"[pipeline] REFUSING to run: running image digest {digest} does not "
            f"match experiment.yaml instrument.runtime_image_digest ({pinned!r}; "
            "unset means the cell is not signed for launch)."
        )
    # Echo the line so it lands in the teed run log, per the invariant.
    print(line, flush=True)
    return prov


def write_container_provenance(namespace: str = "runlog") -> None:
    prov = read_container_provenance()  # raises SystemExit outside the pinned lane
    out = ANALYSIS / namespace / "container_provenance.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    write_json(out, {"found": True, "provenance": prov})


def load_rows() -> dict[str, list[dict]]:
    if not ROWS_PATH.is_file():
        raise SystemExit(f"missing {ROWS_PATH}; run materialize_rows.py first")
    rows = load_jsonl(ROWS_PATH)
    by_pop: dict[str, list[dict]] = {"P_CONFAB": []}
    for r in rows:
        by_pop.setdefault(r["population"], []).append(r)
    if len(by_pop.get("P_CONFAB", [])) != 400:
        raise SystemExit(f"P_CONFAB: expected 400 rows, got {len(by_pop.get('P_CONFAB', []))}")
    return by_pop


def load_directions() -> dict[str, Any]:
    directions_dir = DOUBT_SNAP_COMMITTED / "directions" / "hs20"
    c_hat = np.asarray(json.loads((directions_dir / "c_hat.json").read_text())["vector"], dtype=np.float64)
    random_dir = np.asarray(json.loads((directions_dir / "random_direction.json").read_text())["vector"], dtype=np.float64)
    return {"c_hat": c_hat, "random_direction": random_dir}


def rate(records: list[dict], field: str) -> dict[str, Any]:
    n = len(records)
    successes = sum(1 for r in records if bool(r.get(field)))
    return {"n": n, "successes": successes, "rate": (successes / n) if n else None}


def summarize_arm(records: list[dict]) -> dict[str, Any]:
    return {
        "n": len(records),
        "refused_v2": rate(records, "refused_v2"),
        "correct_v2": rate([r for r in records if r.get("correct_v2") is not None], "correct_v2") if any(r.get("correct_v2") is not None for r in records) else {"n": 0, "successes": 0, "rate": None},
        "well_formed": rate(records, "well_formed"),
        "degenerate": rate(records, "degenerate"),
        "semantic_refuse": rate(records, "semantic_refuse"),
        "terminated_naturally": rate(records, "terminated_naturally"),
        "mean_new_tokens": (sum(r.get("n_new_tokens", 0) for r in records) / len(records)) if records else None,
    }


def readback_stats(records: list[dict], target: float) -> dict[str, Any]:
    measured = [r["readback_measured"] for r in records if r.get("readback_measured") is not None]
    if not measured:
        return {"n": 0, "target": target, "mean_measured": None, "max_abs_err": None}
    errs = [abs(m - target) for m in measured]
    return {
        "n": len(measured), "target": target,
        "mean_measured": sum(measured) / len(measured),
        "max_abs_err": max(errs),
    }


def gain_for(readout: str, multiplier: float) -> tuple[float, float]:
    dose_abs = REFERENCE_DOSE_ABS * multiplier
    sigma = SIGMA_C if readout == "c_hat" else SIGMA_RANDOM
    gain = dose_abs / sigma if sigma else 0.0
    return dose_abs, gain


def run_arm(
    model, tokenizer, device, controllers: dict[str, Any], layer_module,
    arm: dict[str, Any], rows_by_pop: dict[str, list[dict]], batch_size: int,
    gen_cfg: dict[str, Any],
    namespace: str = "runlog", readback_collector: list[dict] | None = None,
) -> list[dict]:
    name = arm["name"]
    population = arm["population"]
    readout = arm["readout"]
    multiplier = arm["multiplier"]
    rows = rows_by_pop[population]
    dose_abs, gain = gain_for(readout, multiplier)

    log = _run_log(name, {"stage": "isnc", "arm": name, "population": population, "readout": readout, "multiplier": multiplier, "generation": gen_cfg}, namespace)
    common_kwargs = dict(
        do_sample=gen_cfg["do_sample"], temperature=gen_cfg["temperature"], top_p=gen_cfg["top_p"],
        generation_sampling_seed=gen_cfg["generation_sampling_seed"],
    )
    if multiplier == 0.0:
        steer_lib.run_rows(
            model, tokenizer, device, None, "off", rows, 0.0, MAX_NEW, batch_size, log,
            arm=name, multiplier=multiplier, dose_abs=0.0, readout=readout, **common_kwargs,
        )
    else:
        ctrl = controllers[readout]
        handle = layer_module.register_forward_hook(ctrl)
        try:
            steer_lib.run_rows(
                model, tokenizer, device, ctrl, "gen_stream", rows, gain, MAX_NEW, batch_size, log,
                arm=name, multiplier=multiplier, dose_abs=dose_abs, readout=readout,
                readback_collector=readback_collector, **common_kwargs,
            )
        finally:
            handle.remove()
            ctrl.reset()
    log.finalize({"n_rows": len(rows), "gain": gain, "dose_abs": dose_abs})
    log.close()
    records = load_jsonl(runlog_path(name, namespace))
    if len(records) != len(rows):
        raise SystemExit(f"[pipeline] runlog_growth FAILED for arm {name!r}: expected {len(rows)} rows, got {len(records)}")
    return records


def build_controllers(directions: dict[str, Any]) -> dict[str, Any]:
    import torch

    hook_c, ctrl_c = steer_lib.build_hook_and_controller(torch.tensor(directions["c_hat"], dtype=torch.float32), SIGMA_C)
    hook_r, ctrl_r = steer_lib.build_hook_and_controller(torch.tensor(directions["random_direction"], dtype=torch.float32), SIGMA_RANDOM)
    return {"c_hat": ctrl_c, "random_direction": ctrl_r}


def cmd_smoke(args: argparse.Namespace) -> int:
    if not args.i_know_this_runs_on_gpu:
        print("[pipeline] smoke loads the model and generates on GPU; refusing without --i-know-this-runs-on-gpu.", file=sys.stderr)
        return 2
    cell_cfg = load_cell_config()
    gen_cfg = resolve_generation_config(cell_cfg)
    write_container_provenance(namespace="runlog_smoke")

    from MechInterp.cell import evaluate_smoke_readback
    from MechInterp.config import SmokeConfig
    from MechInterp.intervention import get_decoder_layer

    rows_by_pop = load_rows()
    directions = load_directions()

    smoke_cfg = SmokeConfig(n_rows=8, write_rel_tol=0.02, write_abs_floor=0.05)
    n_each = 8
    confab_sample = rows_by_pop["P_CONFAB"][:n_each]

    model, tokenizer, device = steer_lib.load_model()
    layer_module = get_decoder_layer(model, DECODER_BLOCK_INDEX)
    controllers = build_controllers(directions)

    import torch

    results: dict[str, Any] = {}
    try:
        pos_collector: list[dict] = []
        pos_records = run_arm(
            model, tokenizer, device, controllers, layer_module,
            {"name": "smoke_pos", "population": "__smoke_confab__", "readout": "c_hat", "multiplier": 1.0},
            {"__smoke_confab__": confab_sample}, min(n_each, len(confab_sample)), gen_cfg,
            namespace="runlog_smoke", readback_collector=pos_collector,
        )
        for rb in pos_collector:
            verdict = evaluate_smoke_readback(rb, smoke_cfg)
            if not verdict["passed"]:
                raise SystemExit(f"[pipeline] G0 FAILED readback (positive, +{REFERENCE_DOSE_ABS}): {verdict}")
        results["positive"] = {"n": len(pos_records), "readback": readback_stats(pos_records, REFERENCE_DOSE_ABS), "verdicts": [evaluate_smoke_readback(rb, smoke_cfg) for rb in pos_collector]}
    finally:
        del model
        gc.collect()
        torch.cuda.empty_cache()

    write_json(ANALYSIS / "smoke_summary.json", results)
    print(json.dumps(results, indent=2, default=str), flush=True)
    print("[pipeline] SMOKE PASSED (readback within tolerance)", flush=True)
    return 0


def cmd_generate(args: argparse.Namespace) -> int:
    if not args.i_know_this_runs_on_gpu:
        print("[pipeline] generate is the full 4-arm, 1600-generation sweep; refusing without --i-know-this-runs-on-gpu.", file=sys.stderr)
        return 2

    cell_cfg = load_cell_config()
    gen_cfg = resolve_generation_config(cell_cfg)
    write_container_provenance(namespace="runlog")

    t0 = time.time()
    rows_by_pop = load_rows()
    directions = load_directions()

    model, tokenizer, device = steer_lib.load_model()
    from MechInterp.intervention import get_decoder_layer

    layer_module = get_decoder_layer(model, DECODER_BLOCK_INDEX)
    controllers = build_controllers(directions)

    import torch

    all_summaries: dict[str, Any] = {}
    try:
        for arm in ARMS:
            print(f"[pipeline] running arm {arm['name']!r} (population={arm['population']}, readout={arm['readout']}, multiplier={arm['multiplier']})", flush=True)
            records = run_arm(model, tokenizer, device, controllers, layer_module, arm, rows_by_pop, args.batch_size, gen_cfg)
            all_summaries[arm["name"]] = summarize_arm(records)
            dose_abs, _ = gain_for(arm["readout"], arm["multiplier"])
            if arm["multiplier"] != 0.0:
                all_summaries[arm["name"]]["readback"] = readback_stats(records, dose_abs)
    finally:
        del model
        gc.collect()
        torch.cuda.empty_cache()

    total_generations = sum(s["n"] for s in all_summaries.values())
    final = {
        "arms": all_summaries,
        "generation_config": gen_cfg,
        "total_generations": total_generations,
        "total_generations_planned": 1600,
        "elapsed_s": time.time() - t0,
    }
    write_json(ANALYSIS / "run_summary.json", final)
    print(f"[pipeline] done in {time.time() - t0:.0f}s, total_generations={total_generations}", flush=True)
    print(json.dumps(final, indent=2, default=str), flush=True)
    return 0


def cmd_screen(args: argparse.Namespace) -> int:
    """CPU-only. Applies the deterministic F5/F4 priority screen
    (screen_lib.classify_screen) to the 4 arms' runlogs. Never touches a
    GPU; no --i-know-this-runs-on-gpu flag needed."""
    runlog_dir = ANALYSIS / "runlog"
    screened, coverage = screen_lib.load_and_screen(runlog_dir, screen_lib.ALL_ARM_KEYS)

    per_arm_counts: dict[str, dict[str, int]] = {}
    totals = {"n_total": 0, "n_f5_degenerate": 0, "n_f4_explicit_idk": 0, "n_screened_in": 0}
    for arm in screen_lib.ALL_ARM_KEYS:
        buckets = screened[arm]
        n_f5 = len(buckets[screen_lib.F5_DEGENERATE])
        n_f4 = len(buckets[screen_lib.F4_EXPLICIT_IDK])
        n_screened_in = len(buckets[screen_lib.SCREENED_IN])
        n_total = n_f5 + n_f4 + n_screened_in
        per_arm_counts[arm] = {"n_total": n_total, "n_f5_degenerate": n_f5, "n_f4_explicit_idk": n_f4, "n_screened_in": n_screened_in}
        for k, v in per_arm_counts[arm].items():
            totals[k] += v

    summary = {"cell": "idk_switch_naming_confirmatory", "runlog_dir": str(runlog_dir), "coverage": coverage, "per_arm": per_arm_counts, "totals": totals}
    write_json(ANALYSIS / "screen_counts.json", summary)

    # Text-bearing intermediates (build_judge_pool.py's core/decoy candidate
    # source; never committed, gitignored analysis/).
    screened_in_dir = ANALYSIS / "screened_in"
    for arm in screen_lib.ALL_ARM_KEYS:
        screen_lib.write_jsonl(screened_in_dir / f"{arm}.jsonl", screened[arm][screen_lib.SCREENED_IN])
    f4_dir = ANALYSIS / "f4_explicit_idk"
    for arm in screen_lib.ALL_ARM_KEYS:
        screen_lib.write_jsonl(f4_dir / f"{arm}.jsonl", screened[arm][screen_lib.F4_EXPLICIT_IDK])

    # TEXT-FREE per-row screen flags (row_key, arm, and the three booleans
    # only -- no `text` field), one row per generation across all 4 arms.
    # This is what `axis_n1n2n3_arithmetic.py` reads for the N1/N3 paired
    # bootstrap (needs row_key alignment ACROSS arms, which the aggregate
    # `screen_counts.json` cannot give it), keeping that arithmetic script on
    # the same "no raw text, no row_key-to-text mapping" data-minimization
    # discipline as axis_g_arithmetic.py (its own reference implementation)
    # even though row-level alignment is required here.
    flags_dir = ANALYSIS / "screen_flags"
    for arm in screen_lib.ALL_ARM_KEYS:
        flag_rows = []
        for label, bucket_key in (
            (screen_lib.F5_DEGENERATE, screen_lib.F5_DEGENERATE),
            (screen_lib.F4_EXPLICIT_IDK, screen_lib.F4_EXPLICIT_IDK),
            (screen_lib.SCREENED_IN, screen_lib.SCREENED_IN),
        ):
            for row in screened[arm][bucket_key]:
                flag_rows.append({
                    "row_key": row["row_key"], "arm": arm,
                    "f5_degenerate": bucket_key == screen_lib.F5_DEGENERATE,
                    "f4_explicit_idk": bucket_key == screen_lib.F4_EXPLICIT_IDK,
                    "screened_in": bucket_key == screen_lib.SCREENED_IN,
                })
        screen_lib.write_jsonl(flags_dir / f"{arm}.jsonl", flag_rows)

    print(json.dumps(summary, indent=2, default=str), flush=True)
    print(
        "\n[pipeline] SCREEN COMPLETE. This is the last automated stage.\n"
        "GOVERNANCE HALT (binding, hard, never auto-continued): the blinded\n"
        "judge lane is LEAD-RUN, not automated. Next steps, run by hand:\n"
        "  1. build_judge_pool.py   (full-pool mode + in-run clear-positive decoys)\n"
        "  2. dispatch judge-subagent grading per shard (context-free, opus-tier)\n"
        "  3. apply_judge_grades.py commit-hash / apply-full-pool\n"
        "  4. axis_n1n2n3_arithmetic.py (reports N1/N2/N3 quantities, no floors)\n"
        "See AMENDMENT.md 'Gates' for the floors the lead pins at sign, and\n"
        "cell.yaml judge_lane for the REGISTERED_AT_SIGN decoy-count/agreement\n"
        "floors this stage's downstream steps require before adjudication.",
        flush=True,
    )
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_smoke = sub.add_parser("smoke", help="instrument validation only, tiny row count, namespaced runlog_smoke path")
    p_smoke.add_argument("--i-know-this-runs-on-gpu", action="store_true")
    p_smoke.set_defaults(func=cmd_smoke)

    p_gen = sub.add_parser("generate", help="the full 4-arm, 1600-generation sweep")
    p_gen.add_argument("--batch-size", type=int, default=BATCH_SIZE)
    p_gen.add_argument("--i-know-this-runs-on-gpu", action="store_true")
    p_gen.set_defaults(func=cmd_generate)

    p_screen = sub.add_parser("screen", help="CPU-only deterministic F5/F4 priority screen over the 4 arm runlogs")
    p_screen.set_defaults(func=cmd_screen)

    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
