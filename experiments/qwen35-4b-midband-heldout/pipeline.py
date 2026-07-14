#!/usr/bin/env python3
"""Top-level CLI for qwen35-4b-midband-heldout: capture -> four-arm held-out
scoring -> gates -> outcome-shape report.

Per AMENDMENT.md "Design"/"Arms", this is a SINGLE frozen operating point
(hs20, dose 8 x sigma_c) scored once on the untouched 1,692-row held-out
pool -- not a dose ladder, not a fit. Every direction, scalar, and threshold
below is loaded verbatim from the resolved qwen35-4b-midband-doubt-snap
ladder's committed artifacts (see cell.yaml `frozen_operating_point`); this
script refits nothing.

Arms (cell.yaml `arms`), all evaluated against the SAME frozen doubt gate
(fire decisions computed once by `capture_anchors.py`, reused by every arm):

  baseline           no hook; every held-out row (confab + known), once.
  gated               real instrument: fired rows get the c_hat erase-write
                       at dose_abs 12.6082 anchor_onward; non-fired rows
                       reuse the shared baseline pass.
  random_direction    the SAME fired rows as gated; frozen random_direction
                       placebo, magnitude matched to the gated arm's
                       realized projection (gain = dose_abs / 1.0, since
                       random_direction.json's own convention is sigma=1.0).
  permuted_gate        the SAME total fire count as gated, but the fired
                       rows are chosen uniformly at random over the
                       combined held-out pool under
                       cell.yaml's `heldout_permute_seed` (20260713),
                       written with the real c_hat snap at the same dose as
                       gated.

`--mode smoke` is instrument validation ONLY (never a result): a handful of
rows through every arm, checking dosed-smoke realized-projection readback
against the target (G0 `readback_within_tolerance`). `--mode run` is the
full 1,692-row confirmatory sweep; it refuses without
`--i-know-this-runs-on-gpu` (the lead launches this after this draft is
signed -- this build task does not run it as evidence).

GPU scripts for this experiment run under
`/home/profsynapse/miniconda3/bin/python3` (base conda), NOT the project's
pinned `unsloth_env` -- AMENDMENT.md/cell.yaml `surface.loader_note`: the
`qwen3_5` architecture needs transformers >= 5.x, which `unsloth_env`
(transformers 4.57.1) does not recognize.
"""

from __future__ import annotations

import argparse
import gc
import hashlib
import json
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[1]
LADDER_COMMITTED = REPO_ROOT / "experiments" / "qwen35-4b-midband-doubt-snap" / "analysis-committed"
for _p in (str(REPO_ROOT / "synaptic-tuner"), str(HERE)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import gate_lib  # noqa: E402
import steer_lib  # noqa: E402
from capture_anchors import gate_decision  # noqa: E402  (reused, not reimplemented)

ANALYSIS = HERE / "analysis"
COMMITTED = HERE / "analysis-committed"
ROWS_PATH = ANALYSIS / "heldout_rows_for_steer.jsonl"
FIRE_PATH = ANALYSIS / "fire_decisions_heldout.jsonl"

HS_INDEX = 20
DECODER_BLOCK_INDEX = 19
MAX_NEW = 200
BATCH_SIZE = 8
HELDOUT_PERMUTE_SEED = 20260713

DOSE_ABS = 12.608187917799976  # frozen; cell.yaml frozen_operating_point.snap.dose_abs

FROZEN_HASHES_PATH = HERE / "frozen_operating_point_hashes.json"
HASH_PLACEHOLDER = "FILLED-AT-SIGN"


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return steer_lib.load_jsonl(path)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str), encoding="utf-8")


def runlog_path(tag: str) -> Path:
    return ANALYSIS / "runlog" / f"{tag}.jsonl"


def _run_log(tag: str, run_config: dict[str, Any]):
    from shared.utilities.run_log import RunLog

    return RunLog(runlog_path(tag), run_config=run_config)


def load_rows_and_fire() -> tuple[list[dict], dict[str, dict]]:
    if not ROWS_PATH.is_file():
        raise SystemExit(f"missing {ROWS_PATH}; run materialize_rows.py first")
    if not FIRE_PATH.is_file():
        raise SystemExit(f"missing {FIRE_PATH}; run capture_anchors.py first")
    rows = load_jsonl(ROWS_PATH)
    fire_by_key = {r["row_key"]: r for r in load_jsonl(FIRE_PATH)}
    missing = [r["row_key"] for r in rows if r["row_key"] not in fire_by_key]
    if missing:
        raise SystemExit(f"{len(missing)} rows have no fire decision (first: {missing[:5]})")
    return rows, fire_by_key


def verify_frozen_operating_point_hashes() -> None:
    """G0 `directions_byte_identical` / `scalars_frozen_match` (gates.yaml):
    both are stated as an explicit sha256/byte-for-byte match against the
    ladder's committed artifacts, not an assumption. Recomputes sha256 of
    every file this experiment's frozen operating point is loaded from and
    compares against `frozen_operating_point_hashes.json`, raising on any
    mismatch, missing file, or unfilled placeholder. The pin VALUES are lead
    work (recorded at sign, same boundary as experiment.yaml pins); this is
    only the verification mechanism."""
    if not FROZEN_HASHES_PATH.is_file():
        raise SystemExit(
            f"[pipeline] G0 FAILED: missing {FROZEN_HASHES_PATH}; "
            "directions_byte_identical/scalars_frozen_match cannot be verified"
        )
    spec = json.loads(FROZEN_HASHES_PATH.read_text())
    files = spec.get("files") or {}
    if not files:
        raise SystemExit(f"[pipeline] G0 FAILED: {FROZEN_HASHES_PATH} has no 'files' entries to verify")

    unfilled = [rel for rel, expected in files.items() if expected == HASH_PLACEHOLDER]
    if unfilled:
        raise SystemExit(
            f"[pipeline] G0 FAILED: {FROZEN_HASHES_PATH} still has the placeholder hash "
            f"for {unfilled}; refusing to run with an unfilled provenance pin. "
            "Fill the real sha256 values at sign."
        )

    mismatches = []
    for rel_path, expected in files.items():
        target = (HERE / rel_path).resolve()
        if not target.is_file():
            raise SystemExit(f"[pipeline] G0 FAILED: {target} (from {rel_path!r}) does not exist")
        actual = hashlib.sha256(target.read_bytes()).hexdigest()
        if actual != expected:
            mismatches.append((rel_path, expected, actual))
    if mismatches:
        detail = "; ".join(f"{p}: expected {e}, got {a}" for p, e, a in mismatches)
        raise SystemExit(
            f"[pipeline] G0 FAILED directions_byte_identical/scalars_frozen_match: {detail}. "
            "The ladder's committed frozen-operating-point files have drifted from the "
            "pinned hashes; refusing to score held-out against an unverified operating point."
        )
    print(f"[pipeline] G0 hash verification passed for {len(files)} frozen-operating-point files", flush=True)


def verify_smoke_readback_tolerance(readback_dicts: list[dict[str, Any]], arm: str) -> None:
    """G0 `readback_within_tolerance` (gates.yaml: "dosed-smoke realized
    projection is within tolerance of target ... on the gated and
    random_direction arms"). Reuses the project-wide smoke-tolerance
    convention every mechinterp cell in this repo already defers to
    (`synaptic-tuner/MechInterp/config.py:SmokeConfig` +
    `MechInterp/cell.py:evaluate_smoke_readback`) rather than inventing a
    tolerance for this build -- gates.yaml names "within tolerance" without
    restating a number because this IS that shared number."""
    from MechInterp.cell import evaluate_smoke_readback
    from MechInterp.config import SmokeConfig

    if not readback_dicts:
        raise SystemExit(f"[pipeline] G0 FAILED readback_within_tolerance: no readback captured for arm {arm!r}")
    smoke_cfg = SmokeConfig()
    for i, rb in enumerate(readback_dicts):
        verdict = evaluate_smoke_readback(rb, smoke_cfg)
        if not verdict["passed"]:
            raise SystemExit(
                f"[pipeline] G0 FAILED readback_within_tolerance for arm {arm!r}, batch {i}: {verdict}"
            )
    print(f"[pipeline] G0 readback_within_tolerance passed for arm {arm!r} ({len(readback_dicts)} batches)", flush=True)


def load_frozen_operating_point() -> dict[str, Any]:
    build = json.loads((LADDER_COMMITTED / "build_manifest.json").read_text())["layers"]["hs20"]
    directions_dir = LADDER_COMMITTED / "directions" / "hs20"
    c_hat = np.asarray(json.loads((directions_dir / "c_hat.json").read_text())["vector"], dtype=np.float64)
    random_dir = np.asarray(json.loads((directions_dir / "random_direction.json").read_text())["vector"], dtype=np.float64)
    u_d = np.asarray(json.loads((directions_dir / "u_d.json").read_text())["vector"], dtype=np.float64)
    return {
        "sigma_c": build["sigma_c"], "mu_d": build["mu_d"], "sigma_d": build["sigma_d"],
        "tau_frozen": build["tau_frozen"], "c_hat": c_hat, "random_direction": random_dir, "u_d": u_d,
    }


def draw_permuted_gate_indices(pool_size: int, n_fired: int, seed: int) -> list[int]:
    """Fresh permuted-gate assignment: n_fired indices chosen uniformly at
    random (without replacement) over range(pool_size), matching the
    ladder's own run_dose_ladder.py permuted_gate convention
    (`np.random.default_rng(seed).choice(len(rows), size=n_fired,
    replace=False)`, sorted)."""
    rng = np.random.default_rng(seed)
    return sorted(rng.choice(pool_size, size=n_fired, replace=False).tolist())


def combine_active_and_baseline(all_rows: list[dict], active_by_key: dict[str, dict], baseline_by_key: dict[str, dict]) -> list[dict]:
    return [active_by_key.get(r["row_key"]) or baseline_by_key[r["row_key"]] for r in all_rows]


def _assert_runlog_growth(tag: str, records: dict[str, dict], expected_n: int) -> None:
    """G0 `runlog_growth`: rather than a human eyeballing the log file
    growing during a >15 min run, assert the persisted row count for this
    phase equals the expected row count for that phase."""
    if len(records) != expected_n:
        raise SystemExit(
            f"[pipeline] G0 FAILED runlog_growth for {tag!r}: expected {expected_n} "
            f"rows, runlog has {len(records)}"
        )


def run_baseline_pass(model, tokenizer, device, rows: list[dict], batch_size: int) -> dict[str, dict]:
    log = _run_log("baseline", {"stage": "heldout_baseline", "n_rows": len(rows)})
    steer_lib.run_rows(model, tokenizer, device, None, "off", rows, 0.0, MAX_NEW, batch_size, log)
    log.finalize({"n_rows": len(rows)})
    log.close()
    records = {r["row_key"]: r for r in load_jsonl(runlog_path("baseline"))}
    _assert_runlog_growth("baseline", records, len(rows))
    return records


def run_active_pass(
    model, tokenizer, device, controller, layer_module, tag: str, active_rows: list[dict], gain: float,
    batch_size: int, readback_collector: list[dict[str, Any]] | None = None,
) -> dict[str, dict]:
    handle = layer_module.register_forward_hook(controller)
    try:
        log = _run_log(tag, {"stage": "heldout", "tag": tag, "gain": gain, "n_active": len(active_rows)})
        steer_lib.run_rows(
            model, tokenizer, device, controller, "gen_stream", active_rows, gain, MAX_NEW, batch_size, log,
            readback_collector=readback_collector,
        )
        log.finalize({"n_rows": len(active_rows), "gain": gain})
        log.close()
    finally:
        handle.remove()
        controller.reset()
    if not active_rows:
        return {}
    records = {r["row_key"]: r for r in load_jsonl(runlog_path(tag))}
    _assert_runlog_growth(tag, records, len(active_rows))
    return records


def _report_no_text_leak(all_rows: list[dict]) -> None:
    """G0 `no_row_text_committed`: no question text, aliases, or answer text
    appear anywhere under analysis-committed/."""
    if not COMMITTED.is_dir():
        return
    texts = {r["question"] for r in all_rows if r.get("question")}
    for path in COMMITTED.rglob("*"):
        if not path.is_file():
            continue
        blob = path.read_text(encoding="utf-8", errors="ignore")
        for t in texts:
            if t and t in blob:
                raise SystemExit(f"[report] question text leaked into {path} -- aborting")


def run_four_arms(
    rows: list[dict], fire_by_key: dict[str, dict], batch_size: int, smoke_mode: bool = False,
) -> dict[str, Any]:
    from MechInterp.intervention import get_decoder_layer

    verify_frozen_operating_point_hashes()  # G0, unconditional, both smoke and run

    held_confab = [r for r in rows if r["role"] == "confab"]
    held_known = [r for r in rows if r["role"] == "known_correct_answered"]
    fired = [r for r in rows if fire_by_key[r["row_key"]]["fire"]]
    fired_confab = [r for r in fired if r["role"] == "confab"]
    fired_known = [r for r in fired if r["role"] == "known_correct_answered"]
    n_fired = len(fired)

    fop = load_frozen_operating_point()
    gain_gated = float(DOSE_ABS / fop["sigma_c"])
    gain_random = float(DOSE_ABS / 1.0)  # random_direction.json's own convention: sigma=1.0

    permuted_idx = draw_permuted_gate_indices(len(rows), n_fired, HELDOUT_PERMUTE_SEED)
    permuted_rows = [rows[i] for i in permuted_idx]
    permuted_confab = [r for r in permuted_rows if r["role"] == "confab"]
    permuted_known = [r for r in permuted_rows if r["role"] == "known_correct_answered"]

    model, tokenizer, device = steer_lib.load_model()
    layer_module = get_decoder_layer(model, DECODER_BLOCK_INDEX)

    import torch

    gated_readbacks: list[dict[str, Any]] | None = [] if smoke_mode else None
    random_readbacks: list[dict[str, Any]] | None = [] if smoke_mode else None

    try:
        baseline_by_key = run_baseline_pass(model, tokenizer, device, rows, batch_size)

        hook_c, ctrl_c = steer_lib.build_hook_and_controller(torch.tensor(fop["c_hat"], dtype=torch.float32), fop["sigma_c"])
        gated_active_by_key = run_active_pass(
            model, tokenizer, device, ctrl_c, layer_module, "gated", fired, gain_gated, batch_size,
            readback_collector=gated_readbacks,
        )
        gated_confab = [gated_active_by_key[r["row_key"]] for r in fired_confab] if fired_confab else []
        gated_known_full = combine_active_and_baseline(held_known, gated_active_by_key, baseline_by_key)
        gated_known_fired_only = [gated_active_by_key[r["row_key"]] for r in fired_known] if fired_known else []

        hook_r, ctrl_r = steer_lib.build_hook_and_controller(torch.tensor(fop["random_direction"], dtype=torch.float32), 1.0)
        rand_active_by_key = run_active_pass(
            model, tokenizer, device, ctrl_r, layer_module, "random_direction", fired, gain_random, batch_size,
            readback_collector=random_readbacks,
        )
        rand_confab_full = combine_active_and_baseline(held_confab, rand_active_by_key, baseline_by_key)
        rand_known_full = combine_active_and_baseline(held_known, rand_active_by_key, baseline_by_key)

        if smoke_mode:
            # G0 readback_within_tolerance: gates.yaml names only the gated
            # and random_direction arms (permuted_gate reuses the gated
            # arm's own already-verified c_hat snap, so it is not named
            # separately). Checked before proceeding to permuted_gate so a
            # dosing fault stops here, not after the full smoke completes.
            verify_smoke_readback_tolerance(gated_readbacks, "gated")
            verify_smoke_readback_tolerance(random_readbacks, "random_direction")

        permuted_active_by_key = run_active_pass(model, tokenizer, device, ctrl_c, layer_module, "permuted_gate", permuted_rows, gain_gated, batch_size)
        permuted_known_full = combine_active_and_baseline(held_known, permuted_active_by_key, baseline_by_key)

        baseline_confab = [baseline_by_key[r["row_key"]] for r in held_confab]
        baseline_known = [baseline_by_key[r["row_key"]] for r in held_known]
    finally:
        del model
        gc.collect()
        torch.cuda.empty_cache()

    _report_no_text_leak(rows)

    summary: dict[str, Any] = {
        "hs_index": HS_INDEX, "dose_abs": DOSE_ABS, "gain_gated": gain_gated, "gain_random": gain_random,
        "heldout_permute_seed": HELDOUT_PERMUTE_SEED,
        "n_held_out_confab": len(held_confab), "n_held_out_known": len(held_known),
        "n_fired_confab": len(fired_confab), "n_fired_known": len(fired_known), "n_fired_total": n_fired,
        "n_permuted_confab": len(permuted_confab), "n_permuted_known": len(permuted_known),
        "baseline": {"confab": gate_lib.rate_summary(baseline_confab), "known": gate_lib.rate_summary(baseline_known)},
        "gated": {
            "fired_confab": gate_lib.rate_summary(gated_confab),
            "known_full_population": gate_lib.rate_summary(gated_known_full),
            "known_fired_conditional": gate_lib.rate_summary(gated_known_fired_only),
        },
        "random_direction": {"confab": gate_lib.rate_summary(rand_confab_full), "known": gate_lib.rate_summary(rand_known_full)},
        "permuted_gate": {"known_full_population": gate_lib.rate_summary(permuted_known_full)},
    }

    g1_refused = summary["gated"]["fired_confab"]["refused"]
    g1_well_formed = summary["gated"]["fired_confab"]["well_formed"]
    g1_cost = summary["gated"]["known_full_population"]["refused"]
    g3i = gate_lib.g3i_pass(
        summary["random_direction"]["confab"]["refused"], summary["baseline"]["confab"]["refused"],
        summary["random_direction"]["known"]["refused"], summary["baseline"]["known"]["refused"],
    )
    g3ii = gate_lib.g3ii_pass(summary["permuted_gate"]["known_full_population"]["refused"], g1_cost)

    gates = {
        "g1_refused_transfer_pass": gate_lib.g1_refused_transfer_pass(g1_refused),
        "g1_well_formed_pass": gate_lib.g1_well_formed_pass(g1_well_formed),
        "g1_cost_pass": gate_lib.g1_cost_pass(g1_cost),
        "g3i": g3i, "g3ii": g3ii,
    }
    summary["gates"] = gates
    summary["outcome_shape"] = gate_lib.classify_outcome_shape(
        refused_transfer_pass=gates["g1_refused_transfer_pass"],
        well_formed_pass=gates["g1_well_formed_pass"],
        cost_pass=gates["g1_cost_pass"],
        g3i_passed=g3i["passed"], g3ii_passed=g3ii["passed"],
    )

    return summary


def cmd_smoke(args: argparse.Namespace) -> int:
    if not args.i_know_this_runs_on_gpu:
        print(
            "[pipeline] smoke mode loads the model and generates on GPU; "
            "refusing without --i-know-this-runs-on-gpu.",
            file=sys.stderr,
        )
        return 2
    rows, fire_by_key = load_rows_and_fire()
    confab_rows = [r for r in rows if r["role"] == "confab"][: args.n_rows // 2]
    known_rows = [r for r in rows if r["role"] == "known_correct_answered"][: args.n_rows - len(confab_rows)]
    sample = confab_rows + known_rows
    sample_fire = {r["row_key"]: fire_by_key[r["row_key"]] for r in sample}
    summary = run_four_arms(sample, sample_fire, min(args.batch_size, len(sample)) or 1, smoke_mode=True)
    ANALYSIS.mkdir(parents=True, exist_ok=True)
    write_json(ANALYSIS / "smoke_heldout_summary.json", summary)
    print(json.dumps(summary, indent=2, default=str), flush=True)
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    if not args.i_know_this_runs_on_gpu:
        print(
            "[pipeline] --mode run is the CONFIRMATORY 1,692-row held-out "
            "sweep. This build task does not launch it; refusing without "
            "--i-know-this-runs-on-gpu.",
            file=sys.stderr,
        )
        return 2
    t0 = time.time()
    rows, fire_by_key = load_rows_and_fire()
    summary = run_four_arms(rows, fire_by_key, args.batch_size)
    write_json(COMMITTED / "heldout_summary.json", summary)
    print(f"[pipeline] done in {time.time() - t0:.0f}s", flush=True)
    print(json.dumps(summary, indent=2, default=str), flush=True)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_smoke = sub.add_parser("smoke", help="instrument validation only, tiny row count")
    p_smoke.add_argument("--n-rows", type=int, default=8)
    p_smoke.add_argument("--batch-size", type=int, default=BATCH_SIZE)
    p_smoke.add_argument("--i-know-this-runs-on-gpu", action="store_true")
    p_smoke.set_defaults(func=cmd_smoke)

    p_run = sub.add_parser("run", help="the signed evidence run -- not executed by this build task")
    p_run.add_argument("--batch-size", type=int, default=BATCH_SIZE)
    p_run.add_argument("--i-know-this-runs-on-gpu", action="store_true")
    p_run.set_defaults(func=cmd_run)

    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
