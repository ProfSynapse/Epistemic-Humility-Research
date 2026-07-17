#!/usr/bin/env python3
"""Generation runner for margin-mapping (M1) (cell.yaml `ladder`/
`population`; gates.yaml SC0/SC1/SC3).

Structure adapted (logic ported) from `gate-contribution-factorial/
run_factorial.py` (read in full before writing this), simplified for M1's
own design: NO gate anywhere, so every row in the population is dosed at
EVERY ladder rung directly (no active/baseline combine step -- the
factorial needed that because only a gate-selected subset of rows were
dosed per arm; M1 doses the whole population every rung, so `steer_lib.
run_rows` already writes the final graded record for every row in one
pass).

Three subcommands:

  reuse-baseline    CPU-only, no GPU/model. Builds `{family}__baseline_
                    reused` from the SC0-staged baseline text (cell.yaml
                    `ladder.dose_zero_rung`), regraded fresh under this
                    harness's own gen_lib.grade_row. This IS the dose-0
                    rung; it never calls run_rows/steer_lib.

  preflight         GPU. Mandatory before `generate-family` (gates.yaml
                    SC1_dose_and_preflight, PI standing directive
                    2026-07-16). Per family: 4 rows, dosed at EACH of the
                    bottom rung (0.0625x), the 1.0x rung, and the top two
                    rungs (3x, 4x) -- the SAME 4 rows across all four rung-
                    points (a build-time interpretation, not a spec value;
                    documented below), so the per-row well-formedness
                    trajectory across the ladder extremes is directly
                    observable as a preflight collapse-location estimate.
                    Refuses without --i-know-this-runs-on-gpu.

  generate-family   GPU. The full 10-rung staircase for one family's
                    population (confab subsample + full known pool, from
                    the SC0-committed `subsample_ids_<family>.json`).
                    REFUSES to start unless `analysis/preflight/PASS`
                    exists AND this family's own preflight_report.json
                    entry says all_passed (checked in code). Live
                    first-batch assertion on every rung's first batch, plus
                    a per-rung-completion assertion over the whole rung's
                    runlog, both hard-abort via SystemExit on any readback
                    miss (relative 0.005 of the commanded ladder dose).
                    RunLog-checkpointed per rung; resumable.

This harness-BUILD task invokes `reuse-baseline` and `preflight` only (the
mandated GPU preflight); the lead launches `generate-family` separately
after reviewing this build.
"""

from __future__ import annotations

import argparse
import datetime
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
EXPERIMENT_DIR = HERE.parent
REPO_ROOT = HERE.parents[2]
TUNER_DIR = REPO_ROOT / "synaptic-tuner"
for _p in (str(TUNER_DIR), str(HERE)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import config  # noqa: E402
import common  # noqa: E402
import row_pool  # noqa: E402
import gen_lib  # noqa: E402
import sc1_checks  # noqa: E402
import dose_ladder  # noqa: E402

ANALYSIS = EXPERIMENT_DIR / "analysis"
COMMITTED = EXPERIMENT_DIR / "analysis-committed"
PREFLIGHT_DIR = ANALYSIS / "preflight"


def runlog_path(tag: str) -> Path:
    return ANALYSIS / "runlog" / f"{tag}.jsonl"


def _preflight_report_path() -> Path:
    return PREFLIGHT_DIR / "preflight_report.json"


def _preflight_pass_marker_path() -> Path:
    return PREFLIGHT_DIR / "PASS"


def resolve_model_revision(family: str) -> tuple[str, str]:
    return config.SUBSTRATE[family], config.REVISION[family]


def _rows_for_keys(qpool: dict[str, dict], keys: list[str]) -> list[dict]:
    return [{"row_key": rk, **qpool[rk]} for rk in keys]


def population_row_keys(family: str) -> list[str]:
    """confab subsample (400) union full known pool, from the SC0-committed
    subsample_ids_<family>.json. Sorted for determinism."""
    path = COMMITTED / f"subsample_ids_{family}.json"
    if not path.is_file():
        raise SystemExit(f"population_row_keys FAIL ({family}): no {path}; run subsample.py first.")
    payload = common.load_json(path)
    keys = set(payload["confab_subsample"]["row_keys"]) | set(payload["known_full"]["row_keys"])
    return sorted(keys)


def pass_is_durable(tag: str, expected_row_keys: list[str]) -> bool:
    from shared.utilities.run_log import RunLog

    meta_path = runlog_path(tag).with_suffix(".jsonl.meta.json")
    if not meta_path.is_file():
        return False
    try:
        meta = common.load_json(meta_path)
    except Exception:
        return False
    if not meta.get("complete"):
        return False
    done = RunLog.peek_done_keys(runlog_path(tag))
    return done == set(expected_row_keys)


# ---------------------------------------------------------------------------
# CPU-only: dose-0 rung (reuse factorial baseline text, RG0, fresh regrade)
# ---------------------------------------------------------------------------

def cmd_reuse_baseline(args: argparse.Namespace) -> int:
    """CPU-only: no GPU, no model. `{family}__baseline_reused` from the
    SC0-staged baseline text, regraded fresh under this harness's own
    gen_lib.grade_row. This is the dose-0 rung (cell.yaml `ladder.
    dose_zero_rung`)."""
    import staging

    family = args.family
    rg0 = staging.rg0_baseline_check(family)
    print(f"[reuse-baseline] {family}: RG0 check PASSED", flush=True)

    qpool = row_pool.question_pool(family)
    baseline_pool = row_pool.baseline_text_pool(family)
    population = population_row_keys(family)
    missing = [rk for rk in population if rk not in baseline_pool]
    if missing:
        raise SystemExit(f"[reuse-baseline] FAIL ({family}): {len(missing)} population rows missing from staged baseline; sample {missing[:5]}.")

    tag = f"{family}__baseline_reused"
    from shared.utilities.run_log import RunLog

    log = RunLog(runlog_path(tag), run_config={"stage": "dose_zero_rung", "family": family, "tag": tag}, fresh=True)
    done = log.done_keys()
    for rk in population:
        if rk in done:
            continue
        rec = baseline_pool[rk]
        aliases = qpool.get(rk, {}).get("aliases")
        text = rec.get("answer_text", "")
        grade = gen_lib.grade_row(text, bool(rec.get("terminated_naturally", True)), aliases)
        log.record(rk, {
            "row_key": rk, "role": rec.get("role") or qpool.get(rk, {}).get("role"),
            "source": rec.get("source") or qpool.get(rk, {}).get("source"),
            "category_canon": rec.get("category_canon") or qpool.get(rk, {}).get("category_canon"),
            "answer_text": text, "terminated_naturally": bool(rec.get("terminated_naturally", True)),
            "readback_measured": None, "rung_multiplier": 0.0, "setpoint": 0.0, **grade,
        })
    log.finalize({"n_rows": len(population)})
    log.close()

    print(f"[reuse-baseline] {family}: done ({len(population)} rows) -> {runlog_path(tag)}", flush=True)
    summary = {"family": family, "n_population": len(population), "rg0": rg0}
    ANALYSIS.mkdir(parents=True, exist_ok=True)
    common.write_json(ANALYSIS / f"reuse_baseline_summary_{family}.json", summary)
    return 0


# ---------------------------------------------------------------------------
# Live SC1 assertions during generation (PI directive, 2026-07-16)
# ---------------------------------------------------------------------------

def _live_sc1_after_first_batch(family: str, rung_label: str, target: float):
    state = {"checked": False}

    def _cb(batch_records: list[dict[str, Any]]) -> None:
        if state["checked"]:
            return
        state["checked"] = True
        checks = [
            sc1_checks.check_readback(r["row_key"], family, r.get("readback_measured"), target)
            for r in batch_records
        ]
        failed = [c for c in checks if not c["passed"]]
        if failed:
            raise SystemExit(
                f"LIVE SC1 FAIL ({family}/{rung_label}): first-batch readback outside "
                f"tolerance rel<= {sc1_checks.READBACK_TOLERANCE_REL}; {len(failed)}/{len(checks)} rows "
                f"failed; worst={max(failed, key=lambda c: c['rel_delta'])}"
            )
        print(
            f"[live-sc1] {family}/{rung_label}: first-batch readback OK "
            f"({len(checks)} rows, max_rel_delta={max(c['rel_delta'] for c in checks):.6f})",
            flush=True,
        )

    return _cb


def _live_sc1_rung_completion(family: str, rung_label: str, tag: str, target: float) -> None:
    rows = common.load_jsonl(runlog_path(tag))
    checks = [
        sc1_checks.check_readback(r["row_key"], family, r.get("readback_measured"), target)
        for r in rows if r.get("readback_measured") is not None
    ]
    failed = [c for c in checks if not c["passed"]]
    if failed:
        raise SystemExit(
            f"LIVE SC1 FAIL ({family}/{rung_label}): rung-completion readback outside tolerance "
            f"for {len(failed)}/{len(checks)} rows; worst={max(failed, key=lambda c: c['rel_delta'])}"
        )
    print(
        f"[live-sc1] {family}/{rung_label}: rung-completion readback OK "
        f"({len(checks)} rows, max_rel_delta={(max((c['rel_delta'] for c in checks), default=0.0)):.6f})",
        flush=True,
    )


def load_c_hat_vector(family: str):
    import numpy as np

    if family == "qwen35_4b":
        path = config.DOUBT_SNAP_DIR / "analysis-committed" / "directions" / "hs20" / "c_hat.json"
    else:
        path = ANALYSIS / "staged_inputs" / "mistral7b_v03" / "directions" / "hs16_c_hat.json"
    c_hat = common.load_json(path)["vector"]
    return np.asarray(c_hat, dtype=np.float64)


# ---------------------------------------------------------------------------
# GPU preflight (mandatory before generate-family)
# ---------------------------------------------------------------------------

def cmd_preflight(args: argparse.Namespace) -> int:
    """GPU. Per family: `args.rows` rows (default 4) dosed at EACH of the
    four preflight rung-points (config.PREFLIGHT_RUNG_MULTIPLIERS: bottom
    rung 0.0625x, the 1.0x rung, and the top two rungs 3x/4x) -- the SAME
    rows at every rung-point (build-time interpretation: this makes the
    preflight itself a tiny per-row ladder, directly showing the collapse
    trajectory for those rows, consistent with the experiment's own
    per-row-margin construct; not a spec value, does not touch any locked
    threshold). Verifies readback within config.READBACK_TOLERANCE_REL at
    every dosed row; records observed well-formedness at 3x/4x as the
    collapse-location estimate. Refuses without --i-know-this-runs-on-gpu."""
    if not args.i_know_this_runs_on_gpu:
        print(
            "[preflight] this loads the model and generates on GPU (a few "
            "rows at the ladder extremes) to verify dosing before any full "
            "rung; refusing without --i-know-this-runs-on-gpu.",
            file=sys.stderr,
        )
        return 2

    import gc

    import torch
    import steer_lib
    from MechInterp.intervention import get_decoder_layer
    from shared.utilities.run_log import RunLog

    family = args.family
    n_rows = args.rows

    population = population_row_keys(family)
    if len(population) < n_rows:
        raise SystemExit(f"[preflight] FAIL ({family}): population has only {len(population)} rows, need {n_rows}.")
    preflight_row_keys = population[:n_rows]

    qpool = row_pool.question_pool(family)
    rows = _rows_for_keys(qpool, preflight_row_keys)

    c_hat = load_c_hat_vector(family)
    sigma = config.SIGMA_C[family]

    model_name, revision = resolve_model_revision(family)
    model, tokenizer, device = steer_lib.load_model(model_name, revision)
    layer_module = get_decoder_layer(model, config.DECODER_BLOCK_INDEX[family])

    results: dict[str, Any] = {}
    all_passed = True
    try:
        for multiplier in config.PREFLIGHT_RUNG_MULTIPLIERS:
            setpoint = dose_ladder.rung_dose_abs(family, multiplier)
            _, gain = dose_ladder.c_hat_write_params(family, setpoint)
            rung_tag = dose_ladder.rung_tag(multiplier)
            tag = f"{family}__preflight_rung_{rung_tag}"
            log_path = PREFLIGHT_DIR / f"{tag}.jsonl"
            log = RunLog(log_path, run_config={"stage": "preflight", "family": family, "multiplier": multiplier, "setpoint": setpoint, "sigma": sigma, "gain": gain, "n_rows": n_rows}, fresh=True)
            hook, ctrl = steer_lib.build_hook_and_controller(torch.tensor(c_hat, dtype=torch.float32), sigma)
            handle = layer_module.register_forward_hook(ctrl)
            try:
                steer_lib.run_rows(model, tokenizer, device, ctrl, "gen_stream", rows, gain, config.GEN_MAX_NEW_TOKENS, n_rows, log)
                log.finalize({"n_rows": n_rows})
            finally:
                handle.remove()
                ctrl.reset()
                log.close()
            logged = common.load_jsonl(log_path)
            checks = [sc1_checks.check_readback(r["row_key"], family, r.get("readback_measured"), setpoint) for r in logged]
            passed = len(checks) == n_rows and all(c["passed"] for c in checks)
            all_passed = all_passed and passed
            n_well_formed = sum(1 for r in logged if r.get("well_formed"))
            results[str(multiplier)] = {
                "multiplier": multiplier, "setpoint": setpoint, "sigma": sigma, "gain": gain,
                "n_rows": len(checks), "readback_passed": passed,
                "n_well_formed": n_well_formed, "well_formed_frac": (n_well_formed / len(logged) if logged else None),
                "checks": checks,
            }
            print(f"[preflight] {family}/{multiplier}x: setpoint={setpoint} sigma={sigma} gain={gain} well_formed={n_well_formed}/{len(logged)}", flush=True)
            for c in checks:
                print(f"[preflight]   row_key={c['row_key']} readback_measured={c['readback_measured']} rel_delta={c.get('rel_delta')} passed={c['passed']}", flush=True)
    finally:
        del model
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    collapse_estimate = {
        m: results[str(m)]["well_formed_frac"]
        for m in config.PREFLIGHT_RUNG_MULTIPLIERS
        if str(m) in results
    }

    report_path = _preflight_report_path()
    PREFLIGHT_DIR.mkdir(parents=True, exist_ok=True)
    report = common.load_json(report_path) if report_path.is_file() else {}
    report[family] = {
        "all_passed": all_passed,
        "n_rows": n_rows,
        "preflight_row_keys": preflight_row_keys,
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "well_formed_frac_by_multiplier": collapse_estimate,
        "results": results,
    }
    common.write_json(report_path, report)

    if all_passed:
        _preflight_pass_marker_path().parent.mkdir(parents=True, exist_ok=True)
        _preflight_pass_marker_path().write_text(
            f"PASS written {datetime.datetime.now(datetime.timezone.utc).isoformat()} "
            f"(most recent passing family: {family}); see preflight_report.json for per-family detail.\n",
            encoding="utf-8",
        )

    if not all_passed:
        print(f"[preflight] {family}: FAIL -- see per-row checks above; PASS marker NOT written for this result; generate-family will refuse.", file=sys.stderr)
        return 1
    print(f"[preflight] {family}: PASS -- report at {report_path}, marker at {_preflight_pass_marker_path()}", flush=True)
    return 0


# ---------------------------------------------------------------------------
# GPU: full 10-rung staircase for one family
# ---------------------------------------------------------------------------

def cmd_generate_family(args: argparse.Namespace) -> int:
    """GPU. Refuses without --i-know-this-runs-on-gpu AND without a passing
    preflight marker for this family. NOT invoked by the harness-build task
    -- the lead launches this after reviewing the build."""
    if not args.i_know_this_runs_on_gpu:
        print(
            "[generate-family] this loads the model and generates the full "
            "10-rung ladder on GPU; refusing without "
            "--i-know-this-runs-on-gpu. This harness-build task never "
            "passes this flag itself.",
            file=sys.stderr,
        )
        return 2

    marker_path = _preflight_pass_marker_path()
    if not marker_path.is_file():
        print(f"[generate-family] refusing: no preflight PASS marker at {marker_path}; run `preflight --family {args.family} --i-know-this-runs-on-gpu` first.", file=sys.stderr)
        return 2
    report_path = _preflight_report_path()
    if not report_path.is_file():
        print(f"[generate-family] refusing: no preflight_report.json at {report_path}.", file=sys.stderr)
        return 2
    report = common.load_json(report_path)
    fam_report = report.get(args.family)
    if not fam_report or not fam_report.get("all_passed"):
        print(f"[generate-family] refusing: preflight report for {args.family} is missing or FAILED ({fam_report}); rerun preflight.", file=sys.stderr)
        return 2
    print(f"[generate-family] {args.family}: preflight PASS confirmed (report timestamp {fam_report.get('timestamp')})", flush=True)

    import gc

    import torch
    import steer_lib
    from MechInterp.intervention import get_decoder_layer
    from shared.utilities.run_log import RunLog

    family = args.family
    population = population_row_keys(family)
    qpool = row_pool.question_pool(family)
    rows = _rows_for_keys(qpool, population)

    c_hat = load_c_hat_vector(family)
    sigma = config.SIGMA_C[family]

    model_name, revision = resolve_model_revision(family)
    model, tokenizer, device = steer_lib.load_model(model_name, revision)
    layer_module = get_decoder_layer(model, config.DECODER_BLOCK_INDEX[family])

    try:
        for multiplier in config.LADDER_MULTIPLIERS:
            setpoint = dose_ladder.rung_dose_abs(family, multiplier)
            _, gain = dose_ladder.c_hat_write_params(family, setpoint)
            rung_tag = dose_ladder.rung_tag(multiplier)
            tag = f"{family}__rung_{rung_tag}"
            expected_keys = [r["row_key"] for r in rows]
            if not pass_is_durable(tag, expected_keys):
                log = RunLog(runlog_path(tag), run_config={"stage": "ladder_rung", "family": family, "multiplier": multiplier, "setpoint": setpoint, "sigma": sigma, "gain": gain}, fresh=False)
                hook, ctrl = steer_lib.build_hook_and_controller(torch.tensor(c_hat, dtype=torch.float32), sigma)
                handle = layer_module.register_forward_hook(ctrl)
                try:
                    steer_lib.run_rows(
                        model, tokenizer, device, ctrl, "gen_stream", rows, gain,
                        config.GEN_MAX_NEW_TOKENS, args.batch_size, log,
                        after_batch=_live_sc1_after_first_batch(family, f"rung_{multiplier}", setpoint),
                    )
                    log.finalize({"n_rows": len(rows)})
                finally:
                    handle.remove()
                    ctrl.reset()
                    log.close()
            _live_sc1_rung_completion(family, f"rung_{multiplier}", tag, setpoint)
            print(f"[generate-family] {family}: rung {multiplier}x done -> {runlog_path(tag)}", flush=True)
    finally:
        del model
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_reuse = sub.add_parser("reuse-baseline", help="CPU-only: dose-0 rung from staged baseline text, regraded fresh")
    p_reuse.add_argument("--family", required=True, choices=config.FAMILIES)
    p_reuse.set_defaults(func=cmd_reuse_baseline)

    p_preflight = sub.add_parser("preflight", help="GPU: mandatory dosing smoke at the ladder extremes before generate-family")
    p_preflight.add_argument("--family", required=True, choices=config.FAMILIES)
    p_preflight.add_argument("--rows", type=int, default=config.PREFLIGHT_ROWS_DEFAULT)
    p_preflight.add_argument("--i-know-this-runs-on-gpu", action="store_true")
    p_preflight.set_defaults(func=cmd_preflight)

    p_gen = sub.add_parser("generate-family", help="GPU: full 10-rung ladder for one family's population")
    p_gen.add_argument("--family", required=True, choices=config.FAMILIES)
    p_gen.add_argument("--batch-size", type=int, default=config.BATCH_SIZE)
    p_gen.add_argument("--i-know-this-runs-on-gpu", action="store_true")
    p_gen.set_defaults(func=cmd_generate_family)

    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
