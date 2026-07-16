#!/usr/bin/env python3
"""Generation runner for gate-contribution-factorial (cell.yaml `arms` +
`gates_construction`; gates.yaml SC0/SC1/SC3).

Per family, five arms x two populations:

  baseline              reuse text (RG0), full confab + full known, regraded
                         fresh under this experiment's own gen_lib.grade_row.
  true_gate__c_hat       reuse text (RG0): the fired-rows-only gated.jsonl
                         COMBINED with baseline for non-fired rows, over the
                         full confab + full known population, regraded fresh.
  permuted_gate__c_hat   GENERATE: same total fire count as the true gate,
                         rows chosen uniformly at random over the FULL
                         combined deployment pool (gate_construction), real
                         c_hat write at the family setpoint; non-selected
                         rows inherit baseline. Full confab + full known.
  true_gate__random       GENERATE, K=5 seeds: the SAME fired rows as
                         true_gate__c_hat, frozen per-seed random direction
                         at matched magnitude (gain = setpoint/1.0, the
                         random_direction.json sigma=1.0 convention).
                         S_confab=300 subsample + full known.
  permuted_gate__random   GENERATE, K=5 seeds: the permuted gate's fired
                         rows, same per-seed random direction. S_confab=300
                         subsample + full known.

One CPU-only subcommand needs no GPU/model at all (`reuse-family`); the two
GPU subcommands (`decoy-baseline`, `generate-family`) refuse without
`--i-know-this-runs-on-gpu`, mirroring `qwen35-4b-midband-heldout/
pipeline.py`'s own refusal convention. This harness-build task invokes ONLY
`reuse-family`, never `decoy-baseline`/`generate-family` -- the lead
launches generation separately, after reviewing this build.

`decoy-baseline` (GPU, small, unsteered): a fresh baseline generation pass
over `heldback_decoys.decoy_source_rows(family)`, the FIT/atlas-split
known-correct rows that supply the held-back clear-negative decoy pool
(lead decision, NOTEBOOK.md 2026-07-15). This is NOT one of the five
factorial arms above and is never part of any scored rate; it must run
before `heldback_decoys.py build` / `build_pool.py`.

RunLog persistence with per-pass checkpoints (`shared.utilities.run_log.
RunLog`); every pass is keyed so a killed process resumes exactly where it
left off (whole-pass durability convention, `pass_is_durable`, ported
(logic) from `placebo-seed-distribution-census/run_census.py`).
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[1]
TUNER_DIR = REPO_ROOT / "synaptic-tuner"
for _p in (str(TUNER_DIR), str(HERE)):
    if _p not in sys.path:
        sys.path.insert(0, _p)
import config  # noqa: E402
import common  # noqa: E402
import row_pool  # noqa: E402
import gate_construction  # noqa: E402
import sc1_checks  # noqa: E402
import gen_lib  # noqa: E402
import heldback_decoys  # noqa: E402
from direction_draw import fresh_random_direction  # noqa: E402

ANALYSIS = HERE / "analysis"
COMMITTED = HERE / "analysis-committed"

FAMILIES = ("qwen35_4b", "mistral7b_v03")


def _run_log(tag: str, run_config: dict[str, Any], *, fresh: bool = False):
    from shared.utilities.run_log import RunLog

    return RunLog(ANALYSIS / "runlog" / f"{tag}.jsonl", run_config=run_config, fresh=fresh)


def runlog_path(tag: str) -> Path:
    return ANALYSIS / "runlog" / f"{tag}.jsonl"


# ---------------------------------------------------------------------------
# Row-level RG0 baseline check (CPU-only, no GPU)
# ---------------------------------------------------------------------------

def baseline_rg0_check(family: str, expected_row_keys: list[str]) -> dict[str, Any]:
    """SC0 hard-stop: re-verifies, on the EXACT row set this invocation is
    about to reuse, that (a) the staged baseline file has not drifted since
    SC0 staging (live sha256 must match the committed staging_manifest.json
    entry) and (b) every requested row_key's baseline text is present."""
    staged_path = ANALYSIS / "staged_inputs" / family / "baseline.jsonl"
    if not staged_path.is_file():
        raise SystemExit(f"RG0 baseline check FAIL ({family}): staged baseline missing at {staged_path}; run staging.py first.")
    live_sha256 = common.sha256_of_file(staged_path)

    staging_manifest_path = COMMITTED / "staging_manifest.json"
    committed_entry = None
    if staging_manifest_path.is_file():
        manifest = common.load_json(staging_manifest_path)
        for rec in manifest.get("files", []):
            if rec.get("dest_path") == f"analysis/staged_inputs/{family}/baseline.jsonl":
                committed_entry = rec
                break
    if committed_entry is None:
        raise SystemExit(f"RG0 baseline check FAIL ({family}): no staging_manifest.json entry for staged_inputs/{family}/baseline.jsonl; run staging.py first.")
    if live_sha256 != committed_entry["sha256"]:
        raise SystemExit(
            f"RG0 baseline check FAIL ({family}): staged baseline sha256 {live_sha256} != "
            f"SC0-committed {committed_entry['sha256']} (source drift since staging)."
        )

    baseline_pool = row_pool.baseline_text_pool(family)
    missing = [rk for rk in expected_row_keys if rk not in baseline_pool]
    if missing:
        raise SystemExit(f"RG0 baseline check FAIL ({family}): {len(missing)} of {len(expected_row_keys)} rows missing from staged baseline; sample {missing[:5]}.")
    return {"family": family, "staged_baseline_sha256": live_sha256, "n_rows_checked": len(expected_row_keys), "n_missing": 0, "passed": True}


def gated_rg0_check(family: str, expected_fired_row_keys: list[str]) -> dict[str, Any]:
    """Same RG0 shape as `baseline_rg0_check`, for the staged gated.jsonl
    (true_gate__c_hat's fired-rows-only text)."""
    staged_path = ANALYSIS / "staged_inputs" / family / "gated.jsonl"
    if not staged_path.is_file():
        raise SystemExit(f"RG0 gated check FAIL ({family}): staged gated.jsonl missing at {staged_path}; run staging.py first.")
    live_sha256 = common.sha256_of_file(staged_path)

    staging_manifest_path = COMMITTED / "staging_manifest.json"
    committed_entry = None
    if staging_manifest_path.is_file():
        manifest = common.load_json(staging_manifest_path)
        for rec in manifest.get("files", []):
            if rec.get("dest_path") == f"analysis/staged_inputs/{family}/gated.jsonl":
                committed_entry = rec
                break
    if committed_entry is None:
        raise SystemExit(f"RG0 gated check FAIL ({family}): no staging_manifest.json entry for staged_inputs/{family}/gated.jsonl; run staging.py first.")
    if live_sha256 != committed_entry["sha256"]:
        raise SystemExit(f"RG0 gated check FAIL ({family}): staged gated.jsonl sha256 {live_sha256} != SC0-committed {committed_entry['sha256']}.")

    gated_pool = row_pool.gated_text_pool(family)
    missing = [rk for rk in expected_fired_row_keys if rk not in gated_pool]
    if missing:
        raise SystemExit(f"RG0 gated check FAIL ({family}): {len(missing)} of {len(expected_fired_row_keys)} fired rows missing from staged gated.jsonl; sample {missing[:5]}.")
    extra = set(gated_pool) - set(expected_fired_row_keys)
    return {
        "family": family, "staged_gated_sha256": live_sha256,
        "n_fired_expected": len(expected_fired_row_keys), "n_missing": 0,
        "n_gated_pool_rows": len(gated_pool), "n_extra_in_gated_pool_not_in_expected_fired": len(extra),
        "passed": True,
    }


# ---------------------------------------------------------------------------
# Fire decisions (CPU-only, no GPU): true gate + permuted gate, per family
# ---------------------------------------------------------------------------

def true_gate_fired_row_keys(family: str) -> list[str]:
    if family == "qwen35_4b":
        fire_decisions = common.load_jsonl(ANALYSIS / "staged_inputs" / "qwen35_4b" / "fire_decisions_heldout.jsonl")
        check = gate_construction.verify_qwen_fire_counts(fire_decisions)
        if not check["pass"]:
            raise SystemExit(f"true_gate_fired_row_keys FAIL (qwen35_4b): fire-count cross-check against AMENDMENT figures failed: {check}")
        return gate_construction.qwen_true_gate_fired_row_keys(fire_decisions)
    if family == "mistral7b_v03":
        gated_pool = row_pool.gated_text_pool(family)
        fired = sorted(gated_pool.keys())
        expected = config.TRUE_GATE_FIRE_COUNTS["mistral7b_v03"]
        n_confab_fired = sum(1 for rk, r in gated_pool.items() if r.get("role") == "confab")
        if len(fired) != expected["confab"] + expected["known"] or n_confab_fired != expected["confab"]:
            raise SystemExit(f"true_gate_fired_row_keys FAIL (mistral7b_v03): computed {len(fired)} fired ({n_confab_fired} confab), cell.yaml registers confab={expected['confab']} known={expected['known']}.")
        return fired
    raise ValueError(family)


def permuted_gate_fired_row_keys(family: str, n_fired: int) -> list[str]:
    seed = config.PERMUTED_GATE_SEED[family]
    if family == "qwen35_4b":
        pool_order = row_pool.heldout_rows_for_steer_file_order(family)
        return gate_construction.qwen_permuted_gate_row_keys(pool_order, n_fired, seed)
    if family == "mistral7b_v03":
        by_role = row_pool.heldout_row_keys_by_role(family)
        return gate_construction.mistral_permuted_gate_row_keys(by_role["confab"], by_role["known_correct_answered"], n_fired, seed)
    raise ValueError(family)


# ---------------------------------------------------------------------------
# CPU-only reuse: baseline + true_gate__c_hat (RG0 text reuse, fresh regrade)
# ---------------------------------------------------------------------------

def combine_active_and_baseline(population_row_keys: list[str], active_by_key: dict[str, dict], baseline_by_key: dict[str, dict]) -> list[dict]:
    """Ported (logic) from qwen35-4b-midband-heldout/pipeline.py's own
    function of the same name: every row in the population takes its active
    (dosed) record if present, else its baseline record."""
    out = []
    for rk in population_row_keys:
        rec = active_by_key.get(rk) or baseline_by_key.get(rk)
        if rec is None:
            raise KeyError(f"row_key {rk!r} missing from both active and baseline pools")
        out.append(rec)
    return out


def _regrade_and_log(tag: str, records: list[dict[str, Any]], qpool: dict[str, dict]) -> dict[str, dict]:
    log = _run_log(tag, {"stage": "text_reuse_regrade", "tag": tag})
    done = log.done_keys()
    for rec in records:
        rk = rec["row_key"]
        if rk in done:
            continue
        aliases = qpool.get(rk, {}).get("aliases")
        text = rec.get("answer_text", "")
        grade = gen_lib.grade_row(text, bool(rec.get("terminated_naturally", True)), aliases)
        log.record(rk, {
            "row_key": rk, "role": rec.get("role") or qpool.get(rk, {}).get("role"),
            "source": rec.get("source") or qpool.get(rk, {}).get("source"),
            "category_canon": rec.get("category_canon") or qpool.get(rk, {}).get("category_canon"),
            "answer_text": text, "terminated_naturally": bool(rec.get("terminated_naturally", True)),
            "readback_measured": rec.get("readback_measured"), **grade,
        })
    log.finalize({"n_rows": len(records)})
    log.close()
    return {r["row_key"]: r for r in common.load_jsonl(runlog_path(tag))}


def cmd_reuse_family(args: argparse.Namespace) -> int:
    """CPU-only: no GPU, no model. Builds `{family}__baseline_reused` and
    `{family}__true_gate_c_hat_reused` runlogs from staged text, regraded
    fresh under this experiment's own gen_lib.grade_row."""
    family = args.family
    by_role = row_pool.heldout_row_keys_by_role(family)
    full_population = sorted(by_role["confab"] + by_role["known_correct_answered"])
    if args.rows is not None:
        full_population = full_population[: args.rows]

    rg0_baseline = baseline_rg0_check(family, full_population)
    print(f"[reuse-family] {family}: RG0 baseline check PASSED ({rg0_baseline['n_rows_checked']} rows)", flush=True)

    qpool = row_pool.question_pool(family)
    baseline_pool = row_pool.baseline_text_pool(family)
    baseline_records = [baseline_pool[rk] for rk in full_population]
    baseline_by_key = _regrade_and_log(f"{family}__baseline_reused", baseline_records, qpool)
    print(f"[reuse-family] {family}: baseline_reused done ({len(baseline_by_key)} rows)", flush=True)

    fired = true_gate_fired_row_keys(family)
    fired_in_pop = [rk for rk in fired if rk in set(full_population)]
    rg0_gated = gated_rg0_check(family, fired_in_pop)
    print(f"[reuse-family] {family}: RG0 gated check PASSED ({rg0_gated['n_fired_expected']} fired rows)", flush=True)

    gated_pool = row_pool.gated_text_pool(family)
    active_by_key = {rk: gated_pool[rk] for rk in fired_in_pop}
    combined = combine_active_and_baseline(full_population, active_by_key, baseline_pool)
    true_gate_c_hat_by_key = _regrade_and_log(f"{family}__true_gate_c_hat_reused", combined, qpool)
    print(f"[reuse-family] {family}: true_gate_c_hat_reused done ({len(true_gate_c_hat_by_key)} rows, {len(fired_in_pop)} fired/active)", flush=True)

    summary = {
        "family": family, "n_population": len(full_population), "n_fired_true_gate": len(fired_in_pop),
        "rg0_baseline": rg0_baseline, "rg0_gated": rg0_gated,
    }
    ANALYSIS.mkdir(parents=True, exist_ok=True)
    common.write_json(ANALYSIS / f"reuse_family_summary_{family}.json", summary)
    return 0


# ---------------------------------------------------------------------------
# GPU generation: permuted_gate__c_hat, true_gate__random x K, permuted_gate__random x K
# refuses without --i-know-this-runs-on-gpu; NOT invoked by this build task.
# ---------------------------------------------------------------------------

def resolve_model_revision(family: str) -> tuple[str, str]:
    return config.SUBSTRATE[family], config.REVISION[family]


# ---------------------------------------------------------------------------
# Erase-write sigma/gain construction (midband-heldout convention: setpoint =
# gain * sigma; InterventionHook's own contract, hooks.py "h' = h - (h.c)c +
# (gain*sigma)c"). Pulled into named, independently-testable functions after
# a defect (PI-approved fix, 2026-07-16) had BOTH call sites pass the gain as
# the sigma argument to steer_lib.build_hook_and_controller AND as the
# generation strength, realizing gain**2 instead of gain*sigma at every fresh
# dosed write. `test_factorial_smoke.py` pins `sigma != gain` for both
# functions as a regression guard against the same conflation recurring.
# ---------------------------------------------------------------------------

def c_hat_write_params(family: str, setpoint: float) -> tuple[float, float]:
    """c_hat erase-write: sigma = SIGMA_C[family] (the c_hat direction is
    calibrated so gain=1.0 corresponds to one sigma_c of realized
    projection), gain = setpoint / sigma_c (qwen35-4b-midband-heldout
    pipeline.py: `gain_gated = DOSE_ABS / fop["sigma_c"]`)."""
    sigma = config.SIGMA_C[family]
    gain = float(setpoint / sigma)
    return sigma, gain


def random_write_params(setpoint: float) -> tuple[float, float]:
    """random-direction erase-write: sigma = 1.0 (random_direction.json's
    own convention), gain = setpoint / 1.0 (qwen35-4b-midband-heldout
    pipeline.py: `gain_random = DOSE_ABS / 1.0`)."""
    sigma = 1.0
    gain = float(setpoint / sigma)
    return sigma, gain


def _rows_for_keys(qpool: dict[str, dict], keys: list[str]) -> list[dict]:
    return [{"row_key": rk, **qpool[rk]} for rk in keys]


# ---------------------------------------------------------------------------
# Live SC1 assertions during generation (PI directive, 2026-07-16): hard-abort
# the whole run the moment a dosed write's readback misses the family
# setpoint, rather than discovering it only in a post-hoc verification pass.
# Uses sc1_checks.check_readback verbatim (sc1_checks.py itself untouched).
# ---------------------------------------------------------------------------

def _live_sc1_after_first_batch(family: str, arm_label: str, target: float):
    """Returns a steer_lib.run_rows `after_batch` callback that checks ONLY
    the first batch it sees (subsequent batches are no-ops) and raises
    SystemExit if any row's readback misses config.READBACK_TOLERANCE_REL of
    the family setpoint -- so a mis-dosed arm aborts before the rest of its
    rows are spent, not after the full (possibly resumed) arm completes."""
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
                f"LIVE SC1 FAIL ({family}/{arm_label}): first-batch readback outside "
                f"tolerance rel<= {sc1_checks.READBACK_TOLERANCE_REL}; {len(failed)}/{len(checks)} rows "
                f"failed; worst={max(failed, key=lambda c: c['rel_delta'])}"
            )
        print(
            f"[live-sc1] {family}/{arm_label}: first-batch readback OK "
            f"({len(checks)} rows, max_rel_delta={max(c['rel_delta'] for c in checks):.6f})",
            flush=True,
        )

    return _cb


def _live_sc1_arm_completion(family: str, arm_label: str, tag: str, target: float) -> None:
    """Re-checks EVERY row in the (now-complete, possibly resumed-from-a-
    prior-durable-pass) runlog against the family setpoint; hard-aborts on
    any miss. Runs unconditionally, including when the arm was already
    durable from a prior invocation, so a resumed run is re-verified too."""
    rows = common.load_jsonl(runlog_path(tag))
    checks = [
        sc1_checks.check_readback(r["row_key"], family, r.get("readback_measured"), target)
        for r in rows if r.get("readback_measured") is not None
    ]
    failed = [c for c in checks if not c["passed"]]
    if failed:
        raise SystemExit(
            f"LIVE SC1 FAIL ({family}/{arm_label}): arm-completion readback outside tolerance "
            f"for {len(failed)}/{len(checks)} rows; worst={max(failed, key=lambda c: c['rel_delta'])}"
        )
    print(
        f"[live-sc1] {family}/{arm_label}: arm-completion readback OK "
        f"({len(checks)} rows, max_rel_delta={(max((c['rel_delta'] for c in checks), default=0.0)):.6f})",
        flush=True,
    )


def load_direction_vectors(family: str):
    import numpy as np

    if family == "qwen35_4b":
        c_hat = common.load_json(ANALYSIS / "staged_inputs" / "qwen35_4b" / "c_hat.json" if False else config.DOUBT_SNAP_DIR / "analysis-committed" / "directions" / "hs20" / "c_hat.json")["vector"]
        u_d = common.load_json(config.DOUBT_SNAP_DIR / "analysis-committed" / "directions" / "hs20" / "u_d.json")["vector"]
    else:
        c_hat = common.load_json(ANALYSIS / "staged_inputs" / "mistral7b_v03" / "directions" / "hs16_c_hat.json")["vector"]
        u_d = common.load_json(ANALYSIS / "staged_inputs" / "mistral7b_v03" / "directions" / "hs16_u_d.json")["vector"]
    c_hat = np.asarray(c_hat, dtype=np.float64)
    u_d = np.asarray(u_d, dtype=np.float64)
    return {"c_hat": c_hat, "u_d": u_d, "hidden_dim": len(c_hat)}


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


def cmd_decoy_baseline(args: argparse.Namespace) -> int:
    """GPU subcommand, small and unsteered: a fresh baseline (no hook)
    generation pass over `heldback_decoys.decoy_source_rows(family)` (the
    FIT/atlas-split known-correct rows, lead decision NOTEBOOK.md
    2026-07-15 harness-accepted entry item 2), writing
    `analysis/runlog/{family}__decoy_baseline.jsonl`. This is the sole GPU
    input `heldback_decoys.build_heldback_candidates` needs; it must run
    BEFORE `build_pool.py` (which calls `heldback_decoys.py` to build the
    heldback__<family> runlog). Refuses without --i-know-this-runs-on-gpu,
    same convention as `generate-family`. RunLog-checkpointed, resumable."""
    if not args.i_know_this_runs_on_gpu:
        print(
            "[decoy-baseline] this loads the model and generates on GPU (a small "
            "unsteered baseline pass over the FIT-split known-correct decoy source "
            "rows); refusing without --i-know-this-runs-on-gpu.",
            file=sys.stderr,
        )
        return 2

    import torch
    import steer_lib
    from shared.utilities.run_log import RunLog

    family = args.family
    rows = heldback_decoys.decoy_source_rows(family)
    expected_keys = sorted(r["row_key"] for r in rows)
    tag = f"{family}__decoy_baseline"

    if pass_is_durable(tag, expected_keys):
        print(f"[decoy-baseline] {family}: already durable ({len(expected_keys)} rows); nothing to do.", flush=True)
        return 0

    model_name, revision = resolve_model_revision(family)
    model, tokenizer, device = steer_lib.load_model(model_name, revision)
    try:
        log = RunLog(runlog_path(tag), run_config={"stage": "decoy_baseline", "family": family, "unsteered": True, "n_rows": len(rows)}, fresh=True)
        try:
            steer_lib.run_rows(model, tokenizer, device, None, "off", rows, None, config.GEN_MAX_NEW_TOKENS, args.batch_size, log)
            log.finalize({"n_rows": len(rows)})
        finally:
            log.close()
    finally:
        del model
        import gc

        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    print(f"[decoy-baseline] {family}: done ({len(expected_keys)} rows) -> {runlog_path(tag)}", flush=True)
    return 0


# ---------------------------------------------------------------------------
# GPU preflight smoke (PI directive, 2026-07-16): mandatory before any full
# `generate-family` arm. Generates a FEW rows per write-type (c_hat, random)
# for one family, verifies readback against the family setpoint, and on an
# all-pass result updates the shared `analysis/preflight_passed.json` marker
# that `generate-family` refuses to run without (simple, loud, file-based
# gate -- deliberately not "same invocation only": preflight and
# generate-family are separate process invocations per the lead's brief).
# ---------------------------------------------------------------------------

PREFLIGHT_ROWS_DEFAULT = 4
# Preflight-only direction seeds. NOT part of any pre-registered seed
# (config.RANDOM_SEED_BLOCKS, PERMUTED_GATE_SEED, SUBSAMPLE_PERMUTATION_SEED);
# chosen well outside every registered family's 1,000,000-wide seed block so
# they can never collide. Preflight rows are discarded, never scored, so the
# SC1 randomness bar does not apply to this direction -- only the readback
# check does.
PREFLIGHT_SEED = {"qwen35_4b": 99000001, "mistral7b_v03": 99000002}


def _preflight_marker_path() -> Path:
    return ANALYSIS / "preflight_passed.json"


def cmd_preflight(args: argparse.Namespace) -> int:
    """GPU: generates `args.rows` rows (default 4) for EACH write-type
    (c_hat, random) for one family, using the SAME c_hat_write_params/
    random_write_params sigma/gain construction generate-family uses, and
    asserts every row's readback against the family setpoint within
    config.READBACK_TOLERANCE_REL. Writes preflight rows under
    `analysis/preflight/` (never `analysis/runlog/`; never combined with any
    scored arm). On an all-pass result, updates
    `analysis/preflight_passed.json` for this family; generate-family
    refuses to start without a passing marker. Refuses without
    --i-know-this-runs-on-gpu."""
    if not args.i_know_this_runs_on_gpu:
        print(
            "[preflight] this loads the model and generates a few rows on GPU "
            "to verify dosing before any full arm; refusing without "
            "--i-know-this-runs-on-gpu.",
            file=sys.stderr,
        )
        return 2

    import datetime
    import gc

    import torch
    import steer_lib
    from MechInterp.intervention import get_decoder_layer
    from shared.utilities.run_log import RunLog

    family = args.family
    n_rows = args.rows
    setpoint = config.SETPOINT_DOSE_ABS[family]
    vecs = load_direction_vectors(family)
    hidden_dim = vecs["hidden_dim"]

    qpool = row_pool.question_pool(family)
    by_role = row_pool.heldout_row_keys_by_role(family)
    population = sorted(by_role["confab"] + by_role["known_correct_answered"])[:n_rows]
    if len(population) < n_rows:
        raise SystemExit(f"[preflight] FAIL ({family}): population has only {len(population)} rows, need {n_rows}.")
    rows = _rows_for_keys(qpool, population)

    model_name, revision = resolve_model_revision(family)
    model, tokenizer, device = steer_lib.load_model(model_name, revision)
    layer_module = get_decoder_layer(model, config.DECODER_BLOCK_INDEX[family])

    results: dict[str, Any] = {}
    all_passed = True
    try:
        combos = (
            ("c_hat", torch.tensor(vecs["c_hat"], dtype=torch.float32), *c_hat_write_params(family, setpoint)),
            (
                "random",
                torch.tensor(fresh_random_direction(PREFLIGHT_SEED[family], hidden_dim), dtype=torch.float32),
                *random_write_params(setpoint),
            ),
        )
        for write_type, direction_vec, sigma, gain in combos:
            tag = f"{family}__preflight_{write_type}"
            log_path = ANALYSIS / "preflight" / f"{tag}.jsonl"
            log = RunLog(log_path, run_config={"stage": "preflight", "family": family, "write_type": write_type, "setpoint": setpoint, "sigma": sigma, "gain": gain, "n_rows": n_rows}, fresh=True)
            hook, ctrl = steer_lib.build_hook_and_controller(direction_vec, sigma)
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
            results[write_type] = {"sigma": sigma, "gain": gain, "setpoint": setpoint, "n_rows": len(checks), "passed": passed, "checks": checks}
            print(f"[preflight] {family}/{write_type}: sigma={sigma} gain={gain} setpoint={setpoint}", flush=True)
            for c in checks:
                print(f"[preflight]   row_key={c['seed']} readback_measured={c['readback_measured']} rel_delta={c.get('rel_delta')} passed={c['passed']}", flush=True)
    finally:
        del model
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    marker_path = _preflight_marker_path()
    marker = common.load_json(marker_path) if marker_path.is_file() else {}
    marker[family] = {
        "all_passed": all_passed,
        "n_rows": n_rows,
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "results": results,
    }
    common.write_json(marker_path, marker)

    if not all_passed:
        print(f"[preflight] {family}: FAIL -- see per-row checks above; NOT a passing marker; generate-family will refuse.", file=sys.stderr)
        return 1
    print(f"[preflight] {family}: PASS -- marker written to {marker_path}", flush=True)
    return 0


def cmd_generate_family(args: argparse.Namespace) -> int:
    """GPU subcommand. Refuses without --i-know-this-runs-on-gpu. NOT
    invoked by this harness-build task -- the lead launches this after
    reviewing the build."""
    if not args.i_know_this_runs_on_gpu:
        print(
            "[generate-family] this loads the model and generates on GPU "
            "(permuted_gate__c_hat + K=5 true_gate__random + K=5 "
            "permuted_gate__random); refusing without "
            "--i-know-this-runs-on-gpu. This harness-build task never passes "
            "this flag itself.",
            file=sys.stderr,
        )
        return 2

    marker_path = _preflight_marker_path()
    if not marker_path.is_file():
        print(
            f"[generate-family] refusing: no preflight marker at {marker_path}; run "
            f"`preflight --family {args.family} --i-know-this-runs-on-gpu` first.",
            file=sys.stderr,
        )
        return 2
    marker = common.load_json(marker_path)
    fam_marker = marker.get(args.family)
    if not fam_marker or not fam_marker.get("all_passed"):
        print(
            f"[generate-family] refusing: preflight marker for {args.family} is missing or FAILED "
            f"({fam_marker}); rerun `preflight` before `generate-family`.",
            file=sys.stderr,
        )
        return 2
    print(f"[generate-family] {args.family}: preflight marker OK (passed at {fam_marker.get('timestamp')})", flush=True)

    ledger_path = COMMITTED / "random_seed_ledger.json"
    if not ledger_path.is_file():
        print(f"[generate-family] refusing: no random-seed ledger at {ledger_path}; run compute_seed_ledger.py first.", file=sys.stderr)
        return 2
    ledger = common.load_json(ledger_path)
    fam_ledger = ledger.get(args.family)
    if not fam_ledger or fam_ledger.get("n_accepted") != config.K_SEEDS_PER_FAMILY:
        raise SystemExit(
            f"[generate-family] FAIL ({args.family}): random_seed_ledger.json does not have "
            f"{config.K_SEEDS_PER_FAMILY} accepted seeds for this family: {fam_ledger}"
        )
    accepted_seeds = fam_ledger["accepted_seeds"]
    print(f"[generate-family] {args.family}: accepted random seeds from ledger: {accepted_seeds} (n_voids={fam_ledger.get('n_voids')})", flush=True)

    import torch
    import steer_lib
    from MechInterp.intervention import get_decoder_layer
    from shared.utilities.run_log import RunLog

    family = args.family
    by_role = row_pool.heldout_row_keys_by_role(family)
    full_confab, full_known = by_role["confab"], by_role["known_correct_answered"]

    subsample_manifest = common.load_json(COMMITTED / "subsample_manifest.json")
    s_confab = subsample_manifest["families"][family]["row_keys"]

    fired = set(true_gate_fired_row_keys(family))
    n_fired = len(fired)
    permuted_fired = set(permuted_gate_fired_row_keys(family, n_fired))

    setpoint = config.SETPOINT_DOSE_ABS[family]
    vecs = load_direction_vectors(family)
    hidden_dim = vecs["hidden_dim"]

    model_name, revision = resolve_model_revision(family)
    model, tokenizer, device = steer_lib.load_model(model_name, revision)
    layer_module = get_decoder_layer(model, config.DECODER_BLOCK_INDEX[family])

    qpool = row_pool.question_pool(family)
    baseline_pool = row_pool.baseline_text_pool(family)

    def rows_for_keys(keys: list[str]) -> list[dict]:
        return _rows_for_keys(qpool, keys)

    try:
        # --- permuted_gate__c_hat: full confab + full known population ---
        full_population = sorted(full_confab + full_known)
        active_keys = sorted(permuted_fired)
        tag = f"{family}__permuted_gate_c_hat"
        sigma, gain = c_hat_write_params(family, setpoint)
        if not pass_is_durable(tag, active_keys):
            log = RunLog(runlog_path(tag), run_config={"stage": "permuted_gate_c_hat", "family": family, "setpoint": setpoint, "sigma": sigma, "gain": gain}, fresh=True)
            hook, ctrl = steer_lib.build_hook_and_controller(torch.tensor(vecs["c_hat"], dtype=torch.float32), sigma)
            handle = layer_module.register_forward_hook(ctrl)
            try:
                steer_lib.run_rows(
                    model, tokenizer, device, ctrl, "gen_stream", rows_for_keys(active_keys), gain,
                    config.GEN_MAX_NEW_TOKENS, args.batch_size, log,
                    after_batch=_live_sc1_after_first_batch(family, "permuted_gate_c_hat", setpoint),
                )
                log.finalize({"n_rows": len(active_keys)})
            finally:
                handle.remove()
                ctrl.reset()
                log.close()
        _live_sc1_arm_completion(family, "permuted_gate_c_hat", tag, setpoint)
        active_by_key = {r["row_key"]: r for r in common.load_jsonl(runlog_path(tag))}
        combined = combine_active_and_baseline(full_population, active_by_key, baseline_pool)
        _regrade_and_log(f"{family}__permuted_gate_c_hat_final", combined, qpool)

        # --- true_gate__random / permuted_gate__random: K=5 ACCEPTED seeds each (ledger, not raw config block) ---
        random_population = sorted(set(s_confab) | set(full_known))
        sigma_r, gain_r = random_write_params(setpoint)
        for label, fired_set in (("true_gate_random", fired), ("permuted_gate_random", permuted_fired)):
            active_keys = sorted(k for k in random_population if k in fired_set)
            for seed in accepted_seeds:
                direction = fresh_random_direction(seed, hidden_dim)
                tag = f"{family}__{label}__seed{seed}"
                if not pass_is_durable(tag, active_keys):
                    log = RunLog(runlog_path(tag), run_config={"stage": label, "family": family, "seed": seed, "setpoint": setpoint, "sigma": sigma_r, "gain": gain_r}, fresh=True)
                    hook, ctrl = steer_lib.build_hook_and_controller(torch.tensor(direction, dtype=torch.float32), sigma_r)
                    handle = layer_module.register_forward_hook(ctrl)
                    try:
                        steer_lib.run_rows(
                            model, tokenizer, device, ctrl, "gen_stream", rows_for_keys(active_keys), gain_r,
                            config.GEN_MAX_NEW_TOKENS, args.batch_size, log,
                            after_batch=_live_sc1_after_first_batch(family, f"{label}__seed{seed}", setpoint),
                        )
                        log.finalize({"n_rows": len(active_keys)})
                    finally:
                        handle.remove()
                        ctrl.reset()
                        log.close()
                _live_sc1_arm_completion(family, f"{label}__seed{seed}", tag, setpoint)
                active_by_key = {r["row_key"]: r for r in common.load_jsonl(runlog_path(tag))}
                combined = combine_active_and_baseline(random_population, active_by_key, baseline_pool)
                _regrade_and_log(f"{tag}_final", combined, qpool)
    finally:
        del model
        import gc

        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_reuse = sub.add_parser("reuse-family", help="CPU-only: baseline + true_gate__c_hat text reuse (RG0), regraded fresh")
    p_reuse.add_argument("--family", required=True, choices=FAMILIES)
    p_reuse.add_argument("--rows", type=int, default=None, help="override: truncate to first N population rows (deterministic); default full population")
    p_reuse.set_defaults(func=cmd_reuse_family)

    p_decoy = sub.add_parser("decoy-baseline", help="GPU: small unsteered baseline pass over the FIT-split known-correct decoy source rows")
    p_decoy.add_argument("--family", required=True, choices=FAMILIES)
    p_decoy.add_argument("--batch-size", type=int, default=config.BATCH_SIZE)
    p_decoy.add_argument("--i-know-this-runs-on-gpu", action="store_true")
    p_decoy.set_defaults(func=cmd_decoy_baseline)

    p_preflight = sub.add_parser("preflight", help="GPU: mandatory dosing smoke (c_hat + random write-types, a few rows each) before generate-family")
    p_preflight.add_argument("--family", required=True, choices=FAMILIES)
    p_preflight.add_argument("--rows", type=int, default=PREFLIGHT_ROWS_DEFAULT)
    p_preflight.add_argument("--i-know-this-runs-on-gpu", action="store_true")
    p_preflight.set_defaults(func=cmd_preflight)

    p_gen = sub.add_parser("generate-family", help="GPU: permuted_gate__c_hat + K=5 true_gate__random + K=5 permuted_gate__random")
    p_gen.add_argument("--family", required=True, choices=FAMILIES)
    p_gen.add_argument("--batch-size", type=int, default=config.BATCH_SIZE)
    p_gen.add_argument("--i-know-this-runs-on-gpu", action="store_true")
    p_gen.set_defaults(func=cmd_generate_family)

    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
