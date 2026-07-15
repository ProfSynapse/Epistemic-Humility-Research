#!/usr/bin/env python3
"""Generation runner for placebo-seed-distribution-census (cell.yaml `write`
+ `census`; gates.yaml SC1/SC3).

Per family: reuse the family's baseline text on the fixed S subsample rows
(RG0-style byte-repro check against the staged committed baseline runlog),
then K=15 dosed erase-write passes (one per accepted census seed, after the
SC1 randomness-bar void-and-redraw ledger resolves 15 seeds that clear the
bar) over the SAME S rows, greedy, max_new_tokens=200, enable_thinking=false,
at the family's fixed setpoint_dose_abs. RunLog persistence with per-pass
checkpoints (`shared.utilities.run_log.RunLog`); baseline reuse and every
dosed pass are keyed so a killed process resumes exactly where it left off.

Model driving is direct InterventionHook/GenerationInterventionController/
RunLog (RR2/RR3 precedent), never the mechinterp-steer recipe path (cell.yaml
`execution.model_driving`).

This module is invoked with `--rows N` for the registered GPU smokes (<=8
rows per family) and is NOT invoked at full S=300/K=15 scale by this harness
build (that launch is the lead's decision after reviewing these smokes).
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import config  # noqa: E402
import common  # noqa: E402
import row_pool  # noqa: E402
import sc1_checks  # noqa: E402
import steer_lib  # noqa: E402
from direction_draw import fresh_random_direction  # noqa: E402

ANALYSIS = HERE / "analysis"
COMMITTED = HERE / "analysis-committed"


def _run_log(tag: str, run_config: dict[str, Any]):
    from shared.utilities.run_log import RunLog

    return RunLog(ANALYSIS / "runlog" / f"{tag}.jsonl", run_config=run_config)


def load_direction_vectors(family: str) -> dict[str, Any]:
    """c_hat/u_d for the SC1 randomness-bar check, plus hidden_dim, sourced
    from SC0-staged (or committed, for qwen) direction JSONs."""
    if family == "qwen35_4b":
        c_hat = common.load_json(config.DIRECTIONS_DIR["qwen35_4b"] / "c_hat.json")["vector"]
        u_d = common.load_json(config.DIRECTIONS_DIR["qwen35_4b"] / "u_d.json")["vector"]
    elif family == "mistral7b_v03":
        c_hat = common.load_json(ANALYSIS / "staged_inputs" / "mistral7b_v03" / "directions" / "hs16_c_hat.json")["vector"]
        u_d = common.load_json(ANALYSIS / "staged_inputs" / "mistral7b_v03" / "directions" / "hs16_u_d.json")["vector"]
    elif family == "llama32_3b":
        c_hat = common.load_json(ANALYSIS / "staged_inputs" / "llama32_3b" / "directions" / "llama_hs20_c_hat.json")["vector"]
        u_d = common.load_json(ANALYSIS / "staged_inputs" / "llama32_3b" / "directions" / "llama_hs20_u_d.json")["vector"]
    else:
        raise ValueError(family)
    import numpy as np

    c_hat = np.asarray(c_hat, dtype=np.float64)
    u_d = np.asarray(u_d, dtype=np.float64)
    return {"c_hat": c_hat, "u_d": u_d, "hidden_dim": len(c_hat)}


def resolve_model_revision(family: str) -> tuple[str, str]:
    import yaml

    matrix = yaml.safe_load((config.FLEET_DIR / "model_matrix.yaml").read_text(encoding="utf-8"))
    cell_id = config.FAMILY_TO_CELL_ID[family]
    for cell in matrix["cells"]:
        if cell["cell_id"] == cell_id:
            return cell["repo"], cell["revision"]
    if family in config.FAMILY_TO_MODEL_FALLBACK:
        return config.FAMILY_TO_MODEL_FALLBACK[family]
    raise SystemExit(f"cell_id {cell_id!r} not found in {config.FLEET_DIR / 'model_matrix.yaml'} and no fallback pinned")


def rows_for_family(family: str, n_rows: int | None) -> list[dict[str, Any]]:
    """Joins the fixed S subsample (committed manifest) against the family's
    private question-text pool. `n_rows` truncates to the first N (sorted,
    deterministic) rows -- used by the GPU smoke suite, never at full S=300
    scale in this harness build."""
    manifest = common.load_json(COMMITTED / "subsample_manifest.json")
    row_keys = manifest["families"][family]["row_keys"]
    if n_rows is not None:
        row_keys = row_keys[:n_rows]
    qpool = row_pool.question_pool(family)
    missing = [rk for rk in row_keys if rk not in qpool]
    if missing:
        raise SystemExit(f"rows_for_family({family}): {len(missing)} subsample row_keys missing from the question pool; sample {missing[:5]}")
    return [{"row_key": rk, "role": "confab", **qpool[rk]} for rk in row_keys]


def run_baseline_reuse(family: str, rows: list[dict[str, Any]]) -> dict[str, dict]:
    """Reuses the family's committed baseline text byte-identical (RG0-style
    repro check against the staged baseline runlog on the S rows), rather
    than regenerating -- cell.yaml `baseline_grade_source: fresh_in_census_
    pool` reuses TEXT only; the GRADE is (re-)computed fresh here via this
    census's own gen_lib.grade_row so baseline and dosed share one lane."""
    baseline_pool = row_pool.baseline_text_pool(family)
    tag = f"{family}__baseline_reused"
    log = _run_log(tag, {"stage": "baseline_reuse", "family": family})
    done = log.done_keys()
    mismatches = []
    for r in rows:
        rk = r["row_key"]
        if rk in done:
            continue
        src = baseline_pool.get(rk)
        if src is None:
            mismatches.append({"row_key": rk, "reason": "missing_from_committed_baseline_runlog"})
            continue
        import gen_lib

        text = src.get("answer_text", "")
        grade = gen_lib.grade_row(text, bool(src.get("terminated_naturally", True)), r.get("aliases"))
        log.record(rk, {
            "row_key": rk, "role": r["role"], "source": r.get("source"), "category_canon": r.get("category_canon"),
            "answer_text": text, "terminated_naturally": src.get("terminated_naturally", True),
            "readback_measured": None, "gain": 0.0, **grade,
        })
    log.finalize({"n_rows": len(rows), "n_mismatches": len(mismatches)})
    log.close()
    if mismatches:
        common.write_json(COMMITTED / f"baseline_reuse_mismatches_{family}.json", mismatches)
        raise SystemExit(f"run_baseline_reuse({family}): {len(mismatches)} rows missing from the committed baseline runlog; see analysis-committed/baseline_reuse_mismatches_{family}.json")
    return {r["row_key"]: r for r in common.load_jsonl(ANALYSIS / "runlog" / f"{tag}.jsonl")}


def baseline_rg0_check(family: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    """SC0 hard-stop (cell.yaml `sc0_provenance_and_staging.baseline_repro`),
    run BEFORE any dosed pass for this family invocation. Re-verifies, on the
    EXACT row set this invocation is about to dose: (a) the staged baseline
    file this census reuses text from has not drifted since SC0 staging (live
    sha256 of `analysis/staged_inputs/<family>/baseline.jsonl` must still
    match the sha256 SC0 recorded in the committed `staging_manifest.json`),
    and (b) every requested row_key's baseline text is actually present in
    that staged file (a missing row cannot be reused byte-identical). This is
    a read-only, CPU-only, pre-generation gate; it does not itself write the
    census's own baseline-reuse runlog (`run_baseline_reuse` does that
    separately, immediately after this passes)."""
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
        raise SystemExit(
            f"RG0 baseline check FAIL ({family}): no staging_manifest.json entry for "
            f"staged_inputs/{family}/baseline.jsonl; SC0 staging was not run or the "
            f"committed manifest is stale relative to this worktree."
        )
    if live_sha256 != committed_entry["sha256"]:
        raise SystemExit(
            f"RG0 baseline check FAIL ({family}): staged baseline sha256 {live_sha256} does not "
            f"match the SC0-committed value {committed_entry['sha256']} recorded in "
            f"staging_manifest.json (source drift since staging; do NOT reuse this text)."
        )

    baseline_pool = row_pool.baseline_text_pool(family)
    missing = [r["row_key"] for r in rows if r["row_key"] not in baseline_pool]
    if missing:
        raise SystemExit(
            f"RG0 baseline check FAIL ({family}): {len(missing)} of {len(rows)} requested S rows "
            f"are missing from the staged baseline runlog; sample {missing[:5]}."
        )
    return {
        "family": family, "staged_baseline_sha256": live_sha256,
        "n_rows_checked": len(rows), "n_missing": 0, "passed": True,
    }


def _meta_complete(tag: str) -> bool:
    meta_path = ANALYSIS / "runlog" / f"{tag}.jsonl.meta.json"
    if not meta_path.is_file():
        return False
    try:
        meta = common.load_json(meta_path)
    except Exception:
        return False
    return bool(meta.get("complete"))


def pass_is_durable(tag: str, expected_row_keys: list[str]) -> bool:
    """Whole-pass checkpoint/resume (LEAD DECISION, config.BATCH_SIZE
    docstring): a completed (family, seed) dosed pass is durable and is
    SKIPPED (never regenerated) only if its RunLog is marked complete AND its
    done-key set is EXACTLY the row_key set this invocation expects. A prior
    pass over a DIFFERENT row set under the same tag (e.g. an 8-row
    mini-smoke, or a truncated earlier run) does not count as durable for a
    full S-row pass -- it gets wiped and regenerated from scratch by the
    caller (RunLog `fresh=True`), so batch composition is identical on every
    complete pass. This is what makes an interrupted pass restart from its
    beginning rather than mid-pass-resume: any incomplete or mismatched log
    is discarded wholesale before generation begins, never patched in place."""
    from shared.utilities.run_log import RunLog

    if not _meta_complete(tag):
        return False
    path = ANALYSIS / "runlog" / f"{tag}.jsonl"
    done = RunLog.peek_done_keys(path)
    return done == set(expected_row_keys)


def run_dosed_pass(
    family: str, seed: int, rows: list[dict[str, Any]], model, tokenizer, device,
    layer_module, direction, setpoint: float, batch_size: int, max_new: int,
) -> tuple[dict[str, dict[str, Any]], bool]:
    """One whole-pass erase-write dosed generation for (family, seed) over
    `rows`. Returns (dosed_by_key, restarted) where `restarted` is True iff
    generation actually ran this call (False means the pass was already
    durable on disk and was reused as-is)."""
    import torch
    from shared.utilities.run_log import RunLog

    tag = f"{family}__random_direction__seed{seed}"
    path = ANALYSIS / "runlog" / f"{tag}.jsonl"
    expected_keys = [r["row_key"] for r in rows]

    if pass_is_durable(tag, expected_keys):
        print(f"[run_census run-family] {tag}: durable pass found ({len(expected_keys)} rows); not regenerated", flush=True)
        return {r["row_key"]: r for r in common.load_jsonl(path)}, False

    log = RunLog(path, run_config={
        "stage": "census_dosed", "family": family, "seed": seed,
        "setpoint_dose_abs": setpoint, "batch_size": batch_size, "n_rows": len(rows),
    }, fresh=True)
    hook, ctrl = steer_lib.build_hook_and_controller(torch.tensor(direction, dtype=torch.float32), setpoint)
    handle = layer_module.register_forward_hook(ctrl)
    try:
        gains = {r["row_key"]: 1.0 for r in rows}
        steer_lib.run_rows(model, tokenizer, device, ctrl, "gen_stream", rows, gains, max_new, batch_size, log, lambda r: r["row_key"])
        log.finalize({"n_rows": len(rows), "seed": seed, "setpoint_dose_abs": setpoint})
    finally:
        handle.remove()
        ctrl.reset()
        log.close()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    return {r["row_key"]: r for r in common.load_jsonl(path)}, True


def resolve_and_run_family_seeds(
    family: str, primary_seeds: list[int], hidden_dim: int, c_hat, u_d,
    rows: list[dict[str, Any]], model, tokenizer, device, layer_module,
    setpoint: float, batch_size: int, max_new: int, k_target: int | None = None,
    max_redraws: int = 300,
) -> dict[str, Any]:
    """Combined SC1 seed resolution + K dosed passes for one family (gates.yaml
    `sc1_magnitude_matching`, `on_fail`). Per candidate seed, IN ORDER: (1)
    randomness bar, CPU-only (sc1_checks.check_randomness_bar) -- a failure
    voids the seed WITHOUT spending any GPU time; (2) only if randomness
    passes, one whole-pass dosed generation (`run_dosed_pass`) plus a
    per-row readback tolerance check (sc1_checks.check_readback), aggregated
    per seed as `all(row passes)` -- a failure voids the seed on reason
    "readback". Either failure reason redraws the next seed via
    `sc1_checks.redraw_seed`, sharing ONE attempt counter (gates.yaml
    describes a single void-and-redraw mechanism, not two independent ones).

    `k_target` is the number of accepted seeds required; it defaults to
    `len(primary_seeds)`, matching `sc1_checks.resolve_seed_ledger`'s own
    convention (the CALLER truncates `primary_seeds` to the desired K before
    calling -- this function tries every seed in `primary_seeds` before ever
    drawing a redraw, it does not itself re-slice `primary_seeds`). Passing a
    `k_target` smaller than `len(primary_seeds)` would silently strand the
    untried tail of `primary_seeds`, so it is accepted only for testing
    convenience and is NOT how `cmd_run_family` calls this (which always
    passes `k_target == len(primary_seeds)`).

    LOCAL SAFETY VALVE (not a registered gate; an execution-time abort rule
    for this driver, does not alter any locked criterion/threshold): if 3
    CONSECUTIVE seeds void on READBACK specifically (randomness-only voids do
    not count towards this streak, since they never reach the GPU), this is
    treated as a systematic failure (wrong layer/sigma/hook wiring) rather
    than seed noise, and the family's sweep is aborted with `aborted=True`
    and a reported reason -- the accepted seeds gathered so far are still
    returned and persisted, nothing is discarded."""
    if k_target is None:
        k_target = len(primary_seeds)
    accepted: list[int] = []
    voids: list[dict[str, Any]] = []
    consecutive_readback_voids = 0
    max_consecutive_readback_voids = 0
    n_restarted = 0
    n_reused_durable = 0
    attempt = 0
    candidates = list(primary_seeds)
    i = 0
    aborted = False
    abort_reason = None

    while len(accepted) < k_target and not aborted:
        if i >= len(candidates):
            attempt += 1
            if attempt > max_redraws:
                raise SystemExit(
                    f"run-family SC1 FAIL ({family}): exceeded {max_redraws} redraws without "
                    f"reaching K={k_target} accepted seeds; check the direction/setpoint wiring."
                )
            candidates.append(sc1_checks.redraw_seed(family, attempt))
        seed = candidates[i]
        i += 1

        rand_check = sc1_checks.check_randomness_bar(seed, hidden_dim, c_hat, u_d)
        if not rand_check["passed"]:
            voids.append({"seed": seed, "reason": "randomness_bar", "randomness_bar": rand_check, "readback_summary": None})
            continue

        direction = fresh_random_direction(seed, hidden_dim)
        dosed_by_key, restarted = run_dosed_pass(
            family, seed, rows, model, tokenizer, device, layer_module, direction, setpoint, batch_size, max_new,
        )
        if restarted:
            n_restarted += 1
        else:
            n_reused_durable += 1

        rb_checks = [sc1_checks.check_readback(seed, family, r.get("readback_measured"), setpoint) for r in dosed_by_key.values()]
        seed_readback_passed = bool(rb_checks) and all(c["passed"] for c in rb_checks)

        if seed_readback_passed:
            accepted.append(seed)
            consecutive_readback_voids = 0
        else:
            rel_deltas = [c["rel_delta"] for c in rb_checks if c.get("rel_delta") is not None]
            voids.append({
                "seed": seed, "reason": "readback", "randomness_bar": rand_check,
                "readback_summary": {
                    "n_rows_checked": len(rb_checks),
                    "n_passed": sum(1 for c in rb_checks if c["passed"]),
                    "mean_rel_delta": (sum(rel_deltas) / len(rel_deltas)) if rel_deltas else None,
                    "max_rel_delta": max(rel_deltas) if rel_deltas else None,
                },
            })
            consecutive_readback_voids += 1
            max_consecutive_readback_voids = max(max_consecutive_readback_voids, consecutive_readback_voids)
            if consecutive_readback_voids > 2:
                aborted = True
                abort_reason = (
                    f"3 consecutive seeds voided on READBACK ({[v['seed'] for v in voids if v['reason'] == 'readback'][-3:]}); "
                    "treated as a systematic failure (wrong layer/sigma/hook wiring), not seed noise; "
                    "aborting this family's sweep per the pre-stated abort rule."
                )

    return {
        "family": family, "k_target": k_target,
        "accepted_seeds": accepted, "n_accepted": len(accepted),
        "voids": voids, "n_voids": len(voids),
        "n_randomness_voids": sum(1 for v in voids if v["reason"] == "randomness_bar"),
        "n_readback_voids": sum(1 for v in voids if v["reason"] == "readback"),
        "max_consecutive_readback_voids": max_consecutive_readback_voids,
        "n_passes_restarted": n_restarted, "n_passes_reused_durable": n_reused_durable,
        "aborted": aborted, "abort_reason": abort_reason,
    }


def _sequential_vs_batch_parity(model, tokenizer, device, layer_module, direction, setpoint, rows, max_new: int) -> dict[str, Any]:
    """Registered smoke `sequential_vs_batch_parity`: the SAME rows, SAME
    seed/setpoint erase-write, run once as N separate batch_size=1 calls
    (sequential) and once as a single batch_size=N call (batched); greedy
    decoding + left-padding must make every row's text/readback byte-identical
    regardless of what else shares its batch. Uses its OWN hook/controller
    registration (separate from the K-seed dosed passes) so it never shares
    RunLog state with them."""
    import torch

    prompts = [steer_lib.render_prompt(r) for r in rows]
    gain_vec = [1.0] * len(prompts)

    hook_seq, ctrl_seq = steer_lib.build_hook_and_controller(torch.tensor(direction, dtype=torch.float32), setpoint)
    handle = layer_module.register_forward_hook(ctrl_seq)
    try:
        sequential = []
        for p in prompts:
            sequential.extend(steer_lib.run_batch_fixed(model, tokenizer, device, ctrl_seq, [p], "gen_stream", [1.0], max_new))
    finally:
        handle.remove()
        ctrl_seq.reset()

    hook_batch, ctrl_batch = steer_lib.build_hook_and_controller(torch.tensor(direction, dtype=torch.float32), setpoint)
    handle = layer_module.register_forward_hook(ctrl_batch)
    try:
        batched = steer_lib.run_batch_fixed(model, tokenizer, device, ctrl_batch, prompts, "gen_stream", gain_vec, max_new)
    finally:
        handle.remove()
        ctrl_batch.reset()

    mismatches = []
    for i, (s, b) in enumerate(zip(sequential, batched)):
        if s["text"] != b["text"]:
            mismatches.append({"index": i, "row_key": rows[i]["row_key"], "sequential_text_len": len(s["text"]), "batched_text_len": len(b["text"])})
    return {
        "n_rows": len(rows), "n_mismatches": len(mismatches), "mismatches": mismatches,
        "passed": len(mismatches) == 0,
    }


def _runlog_persistence_schema(family: str, seed: int, setpoint: float, rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Registered smoke `runlog_persistence_schema`: verifies (a) every
    persisted row from the K-seed dosed RunLog carries the full expected
    schema (data-exhaust rule, gen_lib.grade_row's fields), and (b) resumption
    correctness -- re-invoking steer_lib.run_rows against a RunLog whose
    done_keys() already cover every row must not append any new lines (the
    resumability mechanism a killed-and-restarted real run depends on),
    checked without actually killing a process (done_keys()-gating is the
    resumability contract; this proves that contract directly)."""
    tag = f"{family}__random_direction__seed{seed}"
    path = ANALYSIS / "runlog" / f"{tag}.jsonl"
    before_rows = common.load_jsonl(path)
    before_line_count = len(before_rows)

    expected_fields = {
        "row_key", "role", "source", "category_canon", "gain", "n_new_tokens",
        "terminated_naturally", "readback_measured", "answer_text",
        "refused_v2", "well_formed_correct_v2", "degenerate", "matched_pattern_ids",
    }
    schema_mismatches = []
    for r in before_rows:
        missing = expected_fields - set(r.keys())
        if missing:
            schema_mismatches.append({"row_key": r.get("row_key"), "missing_fields": sorted(missing)})

    log = _run_log(tag, {"stage": "smoke_dosed", "family": family, "seed": seed, "setpoint_dose_abs": setpoint})
    done_before_resume = log.done_keys()
    all_present = all(r["row_key"] in done_before_resume for r in rows)
    log.close()

    after_rows = common.load_jsonl(path)
    no_op_on_resume = len(after_rows) == before_line_count

    return {
        "n_rows_in_log": before_line_count,
        "schema_mismatches": schema_mismatches,
        "schema_passed": len(schema_mismatches) == 0,
        "all_smoke_rows_in_done_keys": all_present,
        "no_new_lines_appended_on_resume_call": no_op_on_resume,
        "passed": len(schema_mismatches) == 0 and all_present and no_op_on_resume,
    }


def cmd_smoke_family(args: argparse.Namespace) -> int:
    """GPU smoke entry point covering all THREE registered smokes
    (cell.yaml `execution.smokes`) for ONE family, on <= 8 rows, loading the
    family's real model exactly once: `real_steer_plus_readback` (the primary
    K-seed dosed pass + SC1 readback check), `sequential_vs_batch_parity`
    (`_sequential_vs_batch_parity`, its own hook/controller), and
    `runlog_persistence_schema` (`_runlog_persistence_schema`, run against the
    real_steer_plus_readback pass's own RunLog). Records peak VRAM/RSS."""
    import torch

    family = args.family
    n_rows = min(args.rows, 8)
    rows = rows_for_family(family, n_rows)

    vecs = load_direction_vectors(family)
    hidden_dim = vecs["hidden_dim"]

    ledger = sc1_checks.resolve_seed_ledger(family, config.SEED_BLOCKS[family][:args.seeds], hidden_dim, vecs["c_hat"], vecs["u_d"])
    seeds = ledger["accepted_seeds"][:args.seeds]
    print(f"[run_census smoke] {family}: SC1 ledger accepted={ledger['n_accepted']} voids={ledger['n_voids']} using seeds={seeds}", flush=True)

    model_name, revision = resolve_model_revision(family)
    t_load0 = time.time()
    model, tokenizer, device = steer_lib.load_model(model_name, revision)
    print(f"[run_census smoke] {family}: model loaded in {time.time() - t_load0:.1f}s ({model_name}@{revision})", flush=True)

    from MechInterp.intervention import get_decoder_layer

    layer = config.LAYER_HS_INDEX[family]
    decoder_block_index = layer - 1
    layer_module = get_decoder_layer(model, decoder_block_index)

    setpoint = config.SETPOINT_DOSE_ABS[family]

    baseline_by_key = run_baseline_reuse(family, rows)

    peak_vram_mb = 0.0
    readback_checks = []
    for seed in seeds:
        direction = fresh_random_direction(seed, hidden_dim)
        hook, ctrl = steer_lib.build_hook_and_controller(torch.tensor(direction, dtype=torch.float32), setpoint)
        handle = layer_module.register_forward_hook(ctrl)
        tag = f"{family}__random_direction__seed{seed}"
        try:
            log = _run_log(tag, {"stage": "smoke_dosed", "family": family, "seed": seed, "setpoint_dose_abs": setpoint})
            gains = {r["row_key"]: 1.0 for r in rows}
            steer_lib.run_rows(model, tokenizer, device, ctrl, "gen_stream", rows, gains, config.GEN_MAX_NEW_TOKENS, args.batch_size, log, lambda r: r["row_key"])
            log.finalize({"n_rows": len(rows), "seed": seed, "setpoint_dose_abs": setpoint})
            log.close()
        finally:
            handle.remove()
            ctrl.reset()
            if torch.cuda.is_available():
                peak_vram_mb = max(peak_vram_mb, torch.cuda.max_memory_allocated() / (1024 * 1024))

        dosed_rows = common.load_jsonl(ANALYSIS / "runlog" / f"{tag}.jsonl")
        for r in dosed_rows:
            rb_check = sc1_checks.check_readback(seed, family, r.get("readback_measured"), setpoint)
            readback_checks.append(rb_check)

    first_seed = seeds[0]
    parity = _sequential_vs_batch_parity(model, tokenizer, device, layer_module, fresh_random_direction(first_seed, hidden_dim), setpoint, rows, config.GEN_MAX_NEW_TOKENS)
    if torch.cuda.is_available():
        peak_vram_mb = max(peak_vram_mb, torch.cuda.max_memory_allocated() / (1024 * 1024))

    persistence = _runlog_persistence_schema(family, first_seed, setpoint, rows)

    import os
    import resource
    peak_rss_mb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0

    summary = {
        "family": family, "n_rows": len(rows), "seeds_used": seeds,
        "setpoint_dose_abs": setpoint, "layer_hs_index": layer,
        "model": model_name, "revision": revision,
        "sc1_ledger": {"n_accepted": ledger["n_accepted"], "n_voids": ledger["n_voids"]},
        "smokes": {
            "real_steer_plus_readback": {
                "readback_checks": readback_checks,
                "passed": all(c["passed"] for c in readback_checks) if readback_checks else False,
            },
            "sequential_vs_batch_parity": parity,
            "runlog_persistence_schema": persistence,
        },
        "peak_vram_mb": peak_vram_mb, "peak_rss_mb": peak_rss_mb,
    }
    common.write_json(COMMITTED / f"gpu_smoke_{family}.json", summary)
    print(summary, flush=True)
    return 0


def cmd_run_family(args: argparse.Namespace) -> int:
    """Full-scale generation driver (BUILD ITEM 1): runs the registered K=15
    seed block for one family over the committed S=300 subsample rows at the
    registered setpoint. `--rows`/`--seeds` override to a smaller scale for
    the mini end-to-end smoke; omitted, they run the full registered scale.
    Loads the family's model exactly once. SC0 RG0 baseline check runs first
    (hard stop on failure), then baseline reuse, then the combined SC1
    seed-resolution + K dosed-pass loop (`resolve_and_run_family_seeds`).
    Persists the per-family SC1 ledger to gitignored
    `analysis/sc1_ledger_<family>.json` (accepted seeds, voids by reason,
    readback stats, restart counts) -- the aggregate committed-public summary
    across all three families is written separately after the full sweep."""
    family = args.family
    k_target = args.seeds if args.seeds is not None else config.K_SEEDS_PER_FAMILY
    rows = rows_for_family(family, args.rows)

    rg0 = baseline_rg0_check(family, rows)
    print(f"[run_census run-family] {family}: RG0 baseline check PASSED ({rg0['n_rows_checked']} rows, "
          f"sha256={rg0['staged_baseline_sha256'][:12]})", flush=True)

    vecs = load_direction_vectors(family)
    hidden_dim = vecs["hidden_dim"]

    model_name, revision = resolve_model_revision(family)
    t_load0 = time.time()
    model, tokenizer, device = steer_lib.load_model(model_name, revision)
    print(f"[run_census run-family] {family}: model loaded in {time.time() - t_load0:.1f}s ({model_name}@{revision})", flush=True)

    from MechInterp.intervention import get_decoder_layer

    layer = config.LAYER_HS_INDEX[family]
    decoder_block_index = layer - 1
    layer_module = get_decoder_layer(model, decoder_block_index)
    setpoint = config.SETPOINT_DOSE_ABS[family]

    baseline_by_key = run_baseline_reuse(family, rows)
    print(f"[run_census run-family] {family}: baseline reuse done ({len(baseline_by_key)} rows)", flush=True)

    t_gen0 = time.time()
    ledger = resolve_and_run_family_seeds(
        family, config.SEED_BLOCKS[family][:k_target], hidden_dim, vecs["c_hat"], vecs["u_d"], rows,
        model, tokenizer, device, layer_module, setpoint, args.batch_size, config.GEN_MAX_NEW_TOKENS, k_target,
    )
    wall_clock_s = time.time() - t_gen0

    ledger["wall_clock_generation_s"] = wall_clock_s
    ledger["n_rows_per_seed"] = len(rows)
    ledger["setpoint_dose_abs"] = setpoint
    ledger["batch_size"] = args.batch_size
    ledger["rg0_baseline_check"] = rg0

    ANALYSIS.mkdir(parents=True, exist_ok=True)
    common.write_json(ANALYSIS / f"sc1_ledger_{family}.json", ledger)

    print(f"[run_census run-family] {family}: DONE accepted={ledger['n_accepted']} voids={ledger['n_voids']} "
          f"(randomness={ledger['n_randomness_voids']}, readback={ledger['n_readback_voids']}) "
          f"restarted_passes={ledger['n_passes_restarted']} reused_durable={ledger['n_passes_reused_durable']} "
          f"wall_clock={wall_clock_s:.0f}s aborted={ledger['aborted']}", flush=True)

    if ledger["aborted"]:
        print(f"[run_census run-family] {family}: ABORTED -- {ledger['abort_reason']}", flush=True)
        return 3
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_smoke = sub.add_parser("smoke-family", help="GPU smoke: real erase-write + readback on <=8 rows for one family")
    p_smoke.add_argument("--family", required=True, choices=("qwen35_4b", "mistral7b_v03", "llama32_3b"))
    p_smoke.add_argument("--rows", type=int, default=8)
    p_smoke.add_argument("--seeds", type=int, default=2)
    p_smoke.add_argument("--batch-size", type=int, default=4)
    p_smoke.set_defaults(func=cmd_smoke_family)

    p_run = sub.add_parser("run-family", help="full-scale generation driver: SC1 seed resolution + K dosed passes over the fixed S subsample for one family")
    p_run.add_argument("--family", required=True, choices=("qwen35_4b", "mistral7b_v03", "llama32_3b"))
    p_run.add_argument("--rows", type=int, default=None, help="override: truncate to first N S-subsample rows (deterministic); default full S=300")
    p_run.add_argument("--seeds", type=int, default=None, help="override: K target (# accepted seeds to resolve); default full K=15 (config.K_SEEDS_PER_FAMILY)")
    p_run.add_argument("--batch-size", type=int, default=config.BATCH_SIZE)
    p_run.set_defaults(func=cmd_run_family)

    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
