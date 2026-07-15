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

Two CPU-only subcommands need no GPU/model at all (`reuse-family`); the GPU
subcommand (`generate-family`) refuses without `--i-know-this-runs-on-gpu`,
mirroring `qwen35-4b-midband-heldout/pipeline.py`'s own refusal convention.
This harness-build task invokes ONLY `reuse-family`, never `generate-family`
-- the lead launches generation separately, after reviewing this build.

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
        return [{"row_key": rk, **qpool[rk]} for rk in keys]

    try:
        # --- permuted_gate__c_hat: full confab + full known population ---
        full_population = sorted(full_confab + full_known)
        active_keys = sorted(permuted_fired)
        tag = f"{family}__permuted_gate_c_hat"
        if not pass_is_durable(tag, active_keys):
            log = RunLog(runlog_path(tag), run_config={"stage": "permuted_gate_c_hat", "family": family, "setpoint": setpoint}, fresh=True)
            gain_gated = float(setpoint / config.SIGMA_C[family])  # midband-heldout convention: gain = dose_abs / sigma_c
            hook, ctrl = steer_lib.build_hook_and_controller(torch.tensor(vecs["c_hat"], dtype=torch.float32), gain_gated)
            handle = layer_module.register_forward_hook(ctrl)
            try:
                steer_lib.run_rows(model, tokenizer, device, ctrl, "gen_stream", rows_for_keys(active_keys), gain_gated, config.GEN_MAX_NEW_TOKENS, args.batch_size, log)
                log.finalize({"n_rows": len(active_keys)})
            finally:
                handle.remove()
                ctrl.reset()
                log.close()
        active_by_key = {r["row_key"]: r for r in common.load_jsonl(runlog_path(tag))}
        combined = combine_active_and_baseline(full_population, active_by_key, baseline_pool)
        _regrade_and_log(f"{family}__permuted_gate_c_hat_final", combined, qpool)

        # --- true_gate__random / permuted_gate__random: K=5 seeds each ---
        random_population = sorted(set(s_confab) | set(full_known))
        for label, fired_set in (("true_gate_random", fired), ("permuted_gate_random", permuted_fired)):
            active_keys = sorted(k for k in random_population if k in fired_set)
            for seed in config.RANDOM_SEED_BLOCKS[family]:
                direction = fresh_random_direction(seed, hidden_dim)
                tag = f"{family}__{label}__seed{seed}"
                if not pass_is_durable(tag, active_keys):
                    log = RunLog(runlog_path(tag), run_config={"stage": label, "family": family, "seed": seed, "setpoint": setpoint}, fresh=True)
                    gain_random = float(setpoint / 1.0)
                    hook, ctrl = steer_lib.build_hook_and_controller(torch.tensor(direction, dtype=torch.float32), gain_random)
                    handle = layer_module.register_forward_hook(ctrl)
                    try:
                        steer_lib.run_rows(model, tokenizer, device, ctrl, "gen_stream", rows_for_keys(active_keys), gain_random, config.GEN_MAX_NEW_TOKENS, args.batch_size, log)
                        log.finalize({"n_rows": len(active_keys)})
                    finally:
                        handle.remove()
                        ctrl.reset()
                        log.close()
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

    p_gen = sub.add_parser("generate-family", help="GPU: permuted_gate__c_hat + K=5 true_gate__random + K=5 permuted_gate__random")
    p_gen.add_argument("--family", required=True, choices=FAMILIES)
    p_gen.add_argument("--batch-size", type=int, default=config.BATCH_SIZE)
    p_gen.add_argument("--i-know-this-runs-on-gpu", action="store_true")
    p_gen.set_defaults(func=cmd_generate_family)

    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
