#!/usr/bin/env python3
"""Channel 2 ladder rebuild for margin-evidence-responsiveness-worldknown
(M4-WK) (cell.yaml `channel2_margin.ladder_rebuild`).

Re-runs M1's margin-mapping ladder, PER DIRECTION, on
test_population confab (400) + correct_control (360) = 760 rows (NO
refused_available rows -- cell.yaml explicitly scopes the ladder to these
two roles). 10 rungs ONLY (multipliers [0.0625, 0.125, 0.25, 0.5, 0.75, 1.0,
1.5, 2.0, 3.0, 4.0] x reference_dose_abs[direction]) -- there is NO dose-0
rung in this cell (unlike M1's `baseline_reused` rung: M1 reused a prior
factorial's dose-0 generation; M4-WK has no such artifact to reuse, and
cell.yaml's own `ladder_rebuild.multipliers` list starts at 0.0625, so this
script does not invent one). GPU generation ported (mechanics) from
`margin-mapping/harness/run_margin.py::cmd_generate_family` (read in full
before writing this); CPU derivation ported from `margin-mapping/harness/
derive_margins.py::derive_row` (read in full before writing this), with the
dose-0 point removed from the ladder-points series.

Erase-write, position anchor_onward, greedy decode, batch_size=4 (config.
LADDER_BATCH_SIZE), RunLog checkpointing/resume. ONE canonical row order is
computed ONCE and reused at every rung (pinned_batch_composition: true,
cell.yaml); the composition is recorded and re-verified identical at every
rung (MAJOR M2 red-team lesson: single batching regime).

Two subcommands:
  generate   GPU. Runs all 10 rungs for one direction. Refuses without
             --i-know-this-runs-on-gpu and without a passing preflight PASS
             marker.
  derive     CPU. Aggregates the 10 rung runlogs into per-row tipping_dose /
             collapse_dose (RAW deliverables only; no criterion/floor
             comparison -- that is analysis.py's job, lead-adjudicated).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Optional

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[2]
for _p in (str(REPO_ROOT / "synaptic-tuner"), str(HERE)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import config  # noqa: E402
import common  # noqa: E402
import batching  # noqa: E402
import popqa_pool  # noqa: E402
import dose_ladder  # noqa: E402
import sc1_checks  # noqa: E402

ANALYSIS = config.EXPERIMENT_DIR / "analysis"
COMMITTED = config.EXPERIMENT_DIR / "analysis-committed"
SELECTION_DIR = COMMITTED / "selection"
RUNLOG_DIR = ANALYSIS / "runlog"
OUT_DIR = ANALYSIS / "channel2_ladder"


def rung_runlog_path(direction: str, multiplier: float) -> Path:
    tag = dose_ladder.rung_tag(multiplier)
    return RUNLOG_DIR / f"channel2_{direction}__rung_{tag}.jsonl"


def load_ladder_rows(direction: str) -> list[dict[str, Any]]:
    """test_population confab + correct_control ONLY (no refused). Same
    population and canonical order regardless of direction (the ladder's
    row set is direction-independent; only the doses differ)."""
    path = SELECTION_DIR / "test_population.json"
    if not path.is_file():
        raise SystemExit(f"ladder_channel2 FAIL: no {path}; run selection.py first.")
    payload = common.load_json(path)
    pool = popqa_pool.load_pool()
    row_keys = sorted(set(payload["row_keys"]["confab"]) | set(payload["row_keys"]["correct"]))
    role_of = {rk: "confab" for rk in payload["row_keys"]["confab"]}
    role_of.update({rk: "correct_on_answerable" for rk in payload["row_keys"]["correct"]})
    ordered = batching.canonical_order(row_keys)
    rows = []
    for rk in ordered:
        r = pool[rk]
        rows.append({
            "row_key": rk, "question": r["question"], "aliases": r["aliases"],
            "role": role_of[rk], "category_canon": r["category"], "source": "popqa",
            "split": "test_population",
        })
    return rows


def _live_sc1_after_first_batch(direction: str, rung_label: str, target: float):
    state = {"checked": False}
    reference_dose_abs = dose_ladder.reference_dose_abs(direction)

    def _cb(batch_records: list[dict[str, Any]]) -> None:
        if state["checked"]:
            return
        state["checked"] = True
        checks = [
            sc1_checks.check_readback(r["row_key"], direction, r.get("readback_measured"), target, reference_dose_abs)
            for r in batch_records
        ]
        failed = [c for c in checks if not c["passed"]]
        if failed:
            raise SystemExit(
                f"LIVE SC1 FAIL ({direction}/{rung_label}): first-batch readback outside "
                f"tolerance; {len(failed)}/{len(checks)} rows failed; worst={max(failed, key=lambda c: c.get('rel_delta', float('inf')))}"
            )
        print(f"[live-sc1] {direction}/{rung_label}: first-batch readback OK ({len(checks)} rows)", flush=True)

    return _cb


def _live_sc1_rung_completion(direction: str, rung_label: str, log_path: Path, target: float) -> None:
    reference_dose_abs = dose_ladder.reference_dose_abs(direction)
    rows = common.load_jsonl(log_path)
    checks = [
        sc1_checks.check_readback(r["row_key"], direction, r.get("readback_measured"), target, reference_dose_abs)
        for r in rows if r.get("readback_measured") is not None
    ]
    failed = [c for c in checks if not c["passed"]]
    if failed:
        raise SystemExit(
            f"LIVE SC1 FAIL ({direction}/{rung_label}): rung-completion readback outside tolerance "
            f"for {len(failed)}/{len(checks)} rows; worst={max(failed, key=lambda c: c['rel_delta'])}"
        )
    print(f"[live-sc1] {direction}/{rung_label}: rung-completion readback OK ({len(checks)} rows)", flush=True)


def _pass_is_durable(log_path: Path, expected_row_keys: list[str]) -> bool:
    from shared.utilities.run_log import RunLog

    meta_path = log_path.with_suffix(".jsonl.meta.json")
    if not meta_path.is_file():
        return False
    try:
        meta = common.load_json(meta_path)
    except Exception:
        return False
    if not meta.get("complete"):
        return False
    done = RunLog.peek_done_keys(log_path)
    return done == set(expected_row_keys)


def cmd_generate(args: argparse.Namespace) -> int:
    if not args.i_know_this_runs_on_gpu:
        print("[ladder_channel2 generate] this loads the model and generates the full 10-rung ladder on GPU; refusing without --i-know-this-runs-on-gpu.", file=sys.stderr)
        return 2

    marker_path = config.EXPERIMENT_DIR / config.PREFLIGHT_PASS_MARKER
    if not marker_path.is_file():
        print(f"[ladder_channel2 generate] refusing: no preflight PASS marker at {marker_path}; run preflight.py first.", file=sys.stderr)
        return 2
    marker = common.load_json(marker_path)
    if not marker.get("pass"):
        print("[ladder_channel2 generate] refusing: preflight PASS marker records pass=False.", file=sys.stderr)
        return 2

    config.assert_pinned_hashes()
    direction = args.direction

    import gc

    import torch
    import steer_lib
    from MechInterp.intervention import get_decoder_layer
    from shared.utilities.run_log import RunLog

    rows = load_ladder_rows(direction)
    expected_keys = [r["row_key"] for r in rows]
    composition = batching.batch_composition_record(rows, config.LADDER_BATCH_SIZE)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    common.write_json(OUT_DIR / f"{direction}_batch_composition.json", composition)
    print(f"[ladder_channel2 generate] {direction}: {len(rows)} rows, composition row_order_sha256={composition['row_order_sha256'][:16]}", flush=True)

    direction_record = common.load_json(
        config.EXPERIMENT_DIR / "analysis" / "staged_inputs" / "directions" / "hs20" / "c_hat_transfer.json"
        if direction == "transfer" else config.NATIVE_C_HAT_PATH
    )
    vector = torch.tensor(direction_record["vector"], dtype=torch.float32)

    model, tokenizer, device = steer_lib.load_model(config.MODEL_REPO, config.MODEL_REVISION)
    layer_module = get_decoder_layer(model, config.DECODER_BLOCK_INDEX)

    try:
        for multiplier in config.LADDER_MULTIPLIERS:
            setpoint = dose_ladder.rung_dose_abs(direction, multiplier)
            sigma, gain = dose_ladder.c_hat_write_params(direction, setpoint)
            log_path = rung_runlog_path(direction, multiplier)
            if not _pass_is_durable(log_path, expected_keys):
                print(f"[ladder_channel2 generate] === RUNG_STARTING {direction} rung_{multiplier} ===", flush=True)
                log = RunLog(log_path, run_config={"stage": "channel2_ladder_rung", "direction": direction, "multiplier": multiplier, "setpoint": setpoint, "sigma": sigma, "gain": gain, "row_order_sha256": composition["row_order_sha256"]}, fresh=False)
                hook, ctrl = steer_lib.build_hook_and_controller(vector, sigma)
                handle = layer_module.register_forward_hook(ctrl)
                try:
                    steer_lib.run_rows(
                        model, tokenizer, device, ctrl, "gen_stream", rows, gain,
                        config.GEN_MAX_NEW_TOKENS, config.LADDER_BATCH_SIZE, log,
                        after_batch=_live_sc1_after_first_batch(direction, f"rung_{multiplier}", setpoint),
                    )
                    log.finalize({"n_rows": len(rows)})
                finally:
                    handle.remove()
                    ctrl.reset()
                    log.close()
            _live_sc1_rung_completion(direction, f"rung_{multiplier}", log_path, setpoint)
            print(f"[ladder_channel2 generate] {direction}: rung {multiplier}x done -> {log_path}", flush=True)
            print(f"[ladder_channel2 generate] === RUNG_DONE {direction} rung_{multiplier} ===", flush=True)
    finally:
        del model
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    print(f"[ladder_channel2 generate] === ALL_RUNGS_DONE {direction} ({len(config.LADDER_MULTIPLIERS)} rungs) ===", flush=True)
    return 0


# ---------------------------------------------------------------------------
# derive (CPU): tipping_dose / collapse_dose, no dose-0 point.
# ---------------------------------------------------------------------------

def _ladder_points(direction: str) -> list[tuple[float, float, Path]]:
    """[(multiplier, dose_abs, runlog_path), ...] in ascending dose order.
    NO dose-0 point (see module docstring)."""
    out = []
    for m in config.LADDER_MULTIPLIERS:
        dose_abs = dose_ladder.rung_dose_abs(direction, m)
        out.append((m, dose_abs, rung_runlog_path(direction, m)))
    return out


def load_rung_records(path: Path) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for r in common.load_jsonl(path):
        rk = r["row_key"]
        if rk in out:
            raise SystemExit(f"ladder_channel2 derive FAIL: duplicate row_key {rk!r} in {path}")
        out[rk] = r
    return out


def derive_row(row_key: str, role: str, series: list[tuple[float, Optional[dict[str, Any]]]]) -> dict[str, Any]:
    """Ported (logic) from margin-mapping/harness/derive_margins.py::derive_row,
    with the dose-0 point removed: `series` is the 10-rung-ordered
    [(dose_abs, record_or_None), ...] (record_or_None: None means the row was
    missing at that rung -- zero-drop violation, recorded, never silently
    skipped)."""
    n = len(series)
    well_formed = [bool(rec["well_formed"]) if rec is not None else None for _, rec in series]
    refused_v2 = [bool(rec["refused_v2"]) if rec is not None else None for _, rec in series]
    missing_idx = [i for i, (_, rec) in enumerate(series) if rec is None]

    top_dose = series[-1][0]
    bottom_dose = series[0][0]

    collapse_idx: Optional[int] = None
    for i in range(n):
        if well_formed[i] is False:
            collapse_idx = i
            break
    collapse_censored = collapse_idx is None
    collapse_dose = series[collapse_idx][0] if collapse_idx is not None else top_dose

    tipping_idx: Optional[int] = None
    for i in range(n):
        if well_formed[i] is True and refused_v2[i] is True:
            tipping_idx = i
            break
    tipping_censored = tipping_idx is None
    tipping_dose = series[tipping_idx][0] if tipping_idx is not None else top_dose
    tipped_at_bottom_rung = (tipping_idx == 0)

    pre_collapse_end = collapse_idx if collapse_idx is not None else n
    pre_collapse_refused = [refused_v2[i] for i in range(pre_collapse_end) if refused_v2[i] is not None]
    non_monotone = False
    seen_true = False
    for v in pre_collapse_refused:
        if v is True:
            seen_true = True
        elif v is False and seen_true:
            non_monotone = True
            break

    return {
        "row_key": row_key, "role": role,
        "well_formed": well_formed, "refused_v2": refused_v2,
        "missing_rung_indices": missing_idx,
        "tipping_dose_abs": tipping_dose, "tipping_idx": tipping_idx, "tipping_censored": tipping_censored,
        "tipped_at_bottom_rung": tipped_at_bottom_rung,
        "collapse_dose_abs": collapse_dose, "collapse_idx": collapse_idx, "collapse_censored": collapse_censored,
        "non_monotone_pre_collapse": non_monotone,
        "bottom_dose_abs": bottom_dose, "top_dose_abs": top_dose,
    }


def cmd_derive(args: argparse.Namespace) -> int:
    config.assert_pinned_hashes()
    direction = args.direction

    path = SELECTION_DIR / "test_population.json"
    payload = common.load_json(path)
    role_of = {rk: "confab" for rk in payload["row_keys"]["confab"]}
    role_of.update({rk: "correct_on_answerable" for rk in payload["row_keys"]["correct"]})

    points = _ladder_points(direction)
    rung_tables = []
    file_hashes = {}
    for m, dose_abs, rung_path in points:
        if not rung_path.is_file():
            raise SystemExit(f"ladder_channel2 derive FAIL: missing rung file {rung_path}; run `generate --direction {direction}` first.")
        table = load_rung_records(rung_path)
        rung_tables.append(table)
        file_hashes[str(rung_path.name)] = common.sha256_of_file(rung_path)
        if len(table) != len(role_of):
            print(f"WARNING rung {m}x: {len(table)} rows in file vs {len(role_of)} in registered population", file=sys.stderr)

    zero_drop_report: dict[str, list[str]] = {}
    rows_out: list[dict[str, Any]] = []
    for row_key, role in sorted(role_of.items()):
        series: list[tuple[float, Optional[dict[str, Any]]]] = []
        for (m, dose_abs, rung_path), table in zip(points, rung_tables):
            series.append((dose_abs, table.get(row_key)))
        missing_files = [points[i][2].name for i, (_, rec) in enumerate(series) if rec is None]
        if missing_files:
            zero_drop_report[row_key] = missing_files
        rows_out.append(derive_row(row_key, role, series))

    unexpected_by_rung: dict[str, list[str]] = {}
    for (m, dose_abs, rung_path), table in zip(points, rung_tables):
        extra = sorted(set(table.keys()) - set(role_of.keys()))
        if extra:
            unexpected_by_rung[rung_path.name] = extra

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rows_path = OUT_DIR / f"{direction}_margin_rows.jsonl"
    with rows_path.open("w", encoding="utf-8") as fh:
        for r in rows_out:
            fh.write(json.dumps(r, sort_keys=True) + "\n")

    def _counts_by_role(pred) -> dict[str, int]:
        out = {"confab": 0, "correct_on_answerable": 0}
        for r in rows_out:
            if pred(r):
                out[r["role"]] += 1
        return out

    confab_rows = [r for r in rows_out if r["role"] == "confab"]
    n_confab = len(confab_rows)
    n_tipped_at_bottom = sum(1 for r in confab_rows if r["tipped_at_bottom_rung"])
    n_tipping_censored = sum(1 for r in confab_rows if r["tipping_censored"])

    bracketing_report = {
        "n_confab": n_confab,
        "n_confab_tipped_at_bottom_rung": n_tipped_at_bottom,
        "frac_confab_tipped_at_bottom_rung": (n_tipped_at_bottom / n_confab) if n_confab else None,
        "n_confab_tipping_censored_at_top_rung": n_tipping_censored,
        "frac_confab_tipping_censored": (n_tipping_censored / n_confab) if n_confab else None,
        "bottom_dose_abs": points[0][1], "top_dose_abs": points[-1][1],
        "note": (
            "cell.yaml `channel2_margin.ladder_rebuild.bracketing_requirement`: "
            "the ladder rungs MUST bracket the observed tipping doses. A high "
            "frac_tipped_at_bottom_rung means the smallest rung is already too "
            "strong (bracketing concern from below); a high "
            "frac_tipping_censored means the largest rung is not strong enough "
            "(from above). REPORTED HERE, not gated -- re-deriving the ladder "
            "is a protocol decision reserved for lead adjudication, never "
            "silently done by this script."
        ),
    }

    summary = {
        "direction": direction, "n_rows": len(rows_out),
        "role_totals": {"confab": n_confab, "correct_on_answerable": len(rows_out) - n_confab},
        "ladder_multipliers": list(config.LADDER_MULTIPLIERS),
        "ladder_doses_abs": [p[1] for p in points],
        "sc3_zero_drop": {"n_rows_with_any_missing_rung": len(zero_drop_report), "missing_by_row": zero_drop_report, "unexpected_row_keys_by_rung_file": unexpected_by_rung},
        "sc3b_censored_counts_raw": {
            "tipping_censored": _counts_by_role(lambda r: r["tipping_censored"]),
            "collapse_censored": _counts_by_role(lambda r: r["collapse_censored"]),
        },
        "sc3c_non_monotone_raw": {"counts": _counts_by_role(lambda r: r["non_monotone_pre_collapse"])},
        "bracketing_report": bracketing_report,
    }
    summary_path = OUT_DIR / f"{direction}_margin_summary.json"
    common.write_json(summary_path, summary)

    manifest = {
        "direction": direction, "source_runlog_sha256": file_hashes,
        "margin_rows_sha256": common.sha256_of_file(rows_path), "margin_rows_path": str(rows_path),
        "margin_summary_sha256": common.sha256_of_file(summary_path),
    }
    common.write_json(OUT_DIR / f"{direction}_provenance_manifest.json", manifest)

    print(json.dumps(summary, indent=2, sort_keys=True), flush=True)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_gen = sub.add_parser("generate", help="GPU: full 10-rung ladder for one direction")
    p_gen.add_argument("--direction", required=True, choices=config.DIRECTIONS)
    p_gen.add_argument("--i-know-this-runs-on-gpu", action="store_true")
    p_gen.set_defaults(func=cmd_generate)

    p_der = sub.add_parser("derive", help="CPU: aggregate rung runlogs into per-row tipping_dose/collapse_dose")
    p_der.add_argument("--direction", required=True, choices=config.DIRECTIONS)
    p_der.set_defaults(func=cmd_derive)

    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
