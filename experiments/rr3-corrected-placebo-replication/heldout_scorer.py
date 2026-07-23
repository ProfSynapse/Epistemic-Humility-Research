#!/usr/bin/env python3
"""Held-out generation driver for rr3-corrected-placebo-replication.

Covers every registered generation pass in cell.yaml: the mistral CORE cell
(baseline, gated, K-seed random_direction, dose_knowns_ungated), the two
RIDER dose ladders (mistral hs16, llama hs20; random_direction at each dose
in `{2,4,6,8,12,16,20} x sigma_c`, both populations), and the held-back
clear-negative decoy source pass (AMENDMENT.md "Successor instrument fix
(a)"): an undosed baseline pass over each family's FIT-split known-correct
rows, which are NEVER part of any scored held-out arm, so decoys drawn from
them cannot cannibalize scored cost coverage.

One run_log file per (arm, family, seed-or-dose) combination -- never a
shared file across seeds/doses for the same row_key -- because the same
held-out row legitimately gets MULTIPLE distinct generation texts across the
K random-seed placebo passes and the 7-rung dose ladders; `steer_lib.run_rows`
keys within a single run log by `row_key` alone, so distinct passes need
distinct files, not distinct keys within one file.

Each row's FULL sub-grade dict (v1 AND v2 fields) is persisted per the
data-exhaust build-time rule (`steer_lib.run_rows` / `gen_lib.grade_row`);
this module computes and reports v1/v2 rate summaries only. RG1/RG2/RG3 (the
core promotion gates) and the rider's descriptive dose-response report are
NOT computed here -- they require the blinded adjudication lane
(`build_adjudication_pool.py` then `apply_adjudication.py`), a separate,
out-of-band step (`pipeline.py`'s printed instructions), exactly mirroring
RR2's `heldout_scorer.py` "provisional_detector_v1_v2_only" status.

Two build-time interpretations, recorded here (not resolvable from cell.yaml
alone, which registers the SHAPE of these seeds but not the RNG formula):
  1. Core random_direction K-seed directions: cell.yaml gives the K seed
     INTEGERS directly (`core_cell.arms[random_direction].random_seeds`);
     each seed draws one fresh unit-norm direction via
     `unit(np.random.default_rng(seed).normal(size=hidden_dim))` -- the same
     normal-then-unit construction `direction_fit.fit_directions` uses for
     its own embedded random_direction, without that function's
     `+hidden_dim+layer_idx` offset (which exists there only to keep a
     fit-time random draw distinct from the fit seed itself; these K seeds
     are already distinct top-level registered values, so no offset is
     needed or would be reproducible from cell.yaml alone).
  2. Rider per-dose fresh random directions: cell.yaml specifies "fresh
     frozen random dir per dose, matched magnitude" without a seed formula.
     `rider_direction_seed(family, dose_multiplier)` derives a deterministic
     per-(family, dose) seed from this experiment's own registered base seed
     (cell.yaml `seed: 20260714`), offset by a family constant so mistral and
     llama draws can never collide with each other or with the core K-seed
     placebo directions (which live in a disjoint value range, see
     `_CORE_SEED_FLOOR`).
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path
from typing import Any

import numpy as np
import yaml

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import direction_fit  # noqa: E402
import gates_lib  # noqa: E402
import materialize_rows as mrows  # noqa: E402
import steer_lib  # noqa: E402

ANALYSIS = HERE / "analysis"
COMMITTED = HERE / "analysis-committed"
DIRECTIONS = HERE / "directions"

FAMILY_TO_LAYER = {"mistral": 16, "llama": 20}
DOSE_LADDER = (2, 4, 6, 8, 12, 16, 20)
CORE_DOSE_MULTIPLIER = 12

RR3_SEED = 20260714  # cell.yaml `seed`
_RIDER_FAMILY_OFFSET = {"mistral": 0, "llama": 1_000_000}
_CORE_SEED_FLOOR = 30_000_000  # core K-seed placebo seeds (30260714..) live above every rider seed


def rider_direction_seed(family: str, dose_multiplier: int) -> int:
    return RR3_SEED + _RIDER_FAMILY_OFFSET[family] + dose_multiplier


def fresh_random_direction(seed: int, hidden_dim: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    return direction_fit.unit(rng.normal(size=hidden_dim))


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


def load_cell_yaml() -> dict[str, Any]:
    with (HERE / "cell.yaml").open(encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def load_reconstructed_directions(family: str) -> dict[str, Any]:
    layer = FAMILY_TO_LAYER[family]
    prefix = f"{family}_hs{layer}"
    for name in (f"{prefix}_c_hat.json", f"{prefix}_random_direction.json", f"{prefix}_u_d.json", f"{prefix}_build_manifest.json"):
        if not (DIRECTIONS / name).is_file():
            raise SystemExit(f"missing {DIRECTIONS / name}; run `fit_reuse.py reconstruct --family {family}` first.")
    c_hat = np.asarray(json.loads((DIRECTIONS / f"{prefix}_c_hat.json").read_text())["vector"])
    u_d = np.asarray(json.loads((DIRECTIONS / f"{prefix}_u_d.json").read_text())["vector"])
    build_manifest = json.loads((DIRECTIONS / f"{prefix}_build_manifest.json").read_text())
    return {"c_hat": c_hat, "u_d": u_d, "build_manifest": build_manifest, "layer": layer}


def load_joined_rows(family: str) -> list[dict[str, Any]]:
    path = ANALYSIS / family / "joined_rows_private.jsonl"
    if not path.is_file():
        raise SystemExit(f"missing {path}; run `materialize_rows.py --family {family}` first.")
    return load_jsonl(path)


def load_anchors(family: str, layer: int) -> dict[str, np.ndarray]:
    path = ANALYSIS / family / "anchors_at_candidate_layer.json"
    raw = json.loads(path.read_text())
    return {rk: np.asarray(per[str(layer)], dtype=np.float64) for rk, per in raw.items() if str(layer) in per}


def score_gate_on_heldout(held_rows, H, u_d, mu_d, sigma_d, tau):
    fit_for_gate = {"u_d": u_d, "stats": {"mu_d": mu_d, "sigma_d": sigma_d}}
    return direction_fit.score_and_fire(held_rows, H, fit_for_gate, tau)


def run_baseline_pass(model, tokenizer, device, rows: list[dict[str, Any]], batch_size: int, tag: str) -> dict[str, dict]:
    log = _run_log(tag, {"stage": "baseline", "tag": tag})
    gains = {r["row_key"]: 0.0 for r in rows}
    steer_lib.run_rows(model, tokenizer, device, None, "off", rows, gains, 200, batch_size, log, lambda r: r["row_key"])
    log.finalize({"n_rows": len(rows)})
    log.close()
    return {r["row_key"]: r for r in load_jsonl(runlog_path(tag))}


def run_active_pass(
    model, tokenizer, device, controller, layer_module, tag: str,
    active_rows: list[dict[str, Any]], gain: float, batch_size: int,
) -> dict[str, dict]:
    handle = layer_module.register_forward_hook(controller)
    try:
        log = _run_log(tag, {"stage": "active", "tag": tag, "gain": gain})
        gains = {r["row_key"]: gain for r in active_rows}
        steer_lib.run_rows(model, tokenizer, device, controller, "gen_stream", active_rows, gains, 200, batch_size, log, lambda r: r["row_key"])
        log.finalize({"n_rows": len(active_rows), "gain": gain})
        log.close()
    finally:
        handle.remove()
        controller.reset()
    return {r["row_key"]: r for r in load_jsonl(runlog_path(tag))}


def combine_active_and_baseline(all_rows, active_by_key, baseline_by_key):
    out = []
    for r in all_rows:
        rk = r["row_key"]
        out.append(active_by_key.get(rk) or baseline_by_key[rk])
    return out


# ---------------------------------------------------------------------------
# CORE: mistral baseline / gated / K-seed random_direction / dose_knowns_ungated
# ---------------------------------------------------------------------------

def cmd_core(args: argparse.Namespace) -> int:
    cell = load_cell_yaml()
    fcell = cell["core_cell"]["family"]
    revision = mrows.resolve_revision("mistral")
    dose_mult = cell["core_cell"]["fixed_operating_point"]["dose_multiplier"]
    seeds = next(a["random_seeds"] for a in cell["core_cell"]["arms"] if a["name"] == "random_direction")
    if len(seeds) < 3:
        raise SystemExit(f"cell.yaml random_direction.random_seeds must carry K >= 3 seeds; got {seeds!r}")

    rows = load_joined_rows("mistral")
    held_confab = [r for r in rows if r["role"] == "confab" and r.get("split") == "held_out"]
    held_known = [r for r in rows if r["role"] == "known_correct_answered" and r.get("split") == "held_out"]
    held_all = held_confab + held_known

    reconstructed = load_reconstructed_directions("mistral")
    build_manifest = reconstructed["build_manifest"]
    dose_abs = float(dose_mult * build_manifest["sigma_c"])
    layer = reconstructed["layer"]
    hidden_dim = build_manifest["hidden_dim"]

    H = load_anchors("mistral", layer)
    scored = score_gate_on_heldout(held_all, H, reconstructed["u_d"], build_manifest["mu_d"], build_manifest["sigma_d"], build_manifest["tau_frozen"])
    fired = [r for r in scored if r["fire"]]
    fired_confab = [r for r in fired if r["role"] == "confab"]
    fired_known = [r for r in fired if r["role"] == "known_correct_answered"]

    model, tokenizer, device = steer_lib.load_model(fcell["model"], revision)
    from MechInterp.intervention import get_decoder_layer
    import torch

    layer_module = get_decoder_layer(model, mrows.decoder_block_index(layer))

    baseline_by_key = run_baseline_pass(model, tokenizer, device, held_all, args.batch_size, "core__baseline")

    hook_c, ctrl_c = steer_lib.build_hook_and_controller(torch.tensor(reconstructed["c_hat"], dtype=torch.float32), build_manifest["sigma_c"])
    gated_active_by_key = run_active_pass(
        model, tokenizer, device, ctrl_c, layer_module, "core__gated",
        fired, float(dose_abs / build_manifest["sigma_c"]), args.batch_size,
    ) if fired else {}

    seed_summaries = []
    for seed in seeds:
        direction = fresh_random_direction(seed, hidden_dim)
        hook_r, ctrl_r = steer_lib.build_hook_and_controller(torch.tensor(direction, dtype=torch.float32), 1.0)
        rand_active_by_key = run_active_pass(
            model, tokenizer, device, ctrl_r, layer_module, f"core__random_direction__seed{seed}",
            fired, float(dose_abs), args.batch_size,
        ) if fired else {}
        rand_all = combine_active_and_baseline(held_all, rand_active_by_key, baseline_by_key)
        rand_confab = [r for r in rand_all if r["role"] == "confab"]
        rand_known = [r for r in rand_all if r["role"] == "known_correct_answered"]
        seed_summaries.append({
            "seed": seed,
            "confab": gates_lib.rate_summary_v2(rand_confab),
            "known": gates_lib.rate_summary_v2(rand_known),
        })

    dose_knowns_gain = float(dose_abs / build_manifest["sigma_c"])
    dku_active_by_key = run_active_pass(
        model, tokenizer, device, ctrl_c, layer_module, "core__dose_knowns_ungated",
        held_known, dose_knowns_gain, args.batch_size,
    )
    dku_all = [dku_active_by_key[r["row_key"]] for r in held_known]

    baseline_confab = [baseline_by_key[r["row_key"]] for r in held_confab]
    baseline_known = [baseline_by_key[r["row_key"]] for r in held_known]

    summary = {
        "status": "provisional_detector_v1_v2_only",
        "note": "RG1/RG2/RG3 verdicts require the blinded adjudication lane; see pipeline.py.",
        "dose_abs": dose_abs, "dose_multiplier": dose_mult, "layer": layer,
        "random_seeds": seeds,
        "n_held_out_confab": len(held_confab), "n_held_out_known": len(held_known),
        "n_fired_confab": len(fired_confab), "n_fired_known": len(fired_known),
        "baseline": {"confab": gates_lib.rate_summary_v2(baseline_confab), "known": gates_lib.rate_summary_v2(baseline_known)},
        "gated": {
            "fired_confab": gates_lib.rate_summary_v2([gated_active_by_key[r["row_key"]] for r in fired_confab]) if fired_confab else gates_lib.rate_summary_v2([]),
            "known_full_population": gates_lib.rate_summary_v2([gated_active_by_key.get(r["row_key"]) or baseline_by_key[r["row_key"]] for r in held_known]),
        },
        "random_direction_per_seed": seed_summaries,
        "dose_knowns_ungated": {
            "known_all": gates_lib.rate_summary_v2(dku_all),
            "clean_false_refusal_v2": gates_lib.rate_wilson(dku_all, "refused_v2"),
            "total_damage_rate": gates_lib.rate_wilson(dku_all, "not_well_formed_correct_v2"),
        },
    }
    write_json(COMMITTED / "core_heldout_summary.json", summary)
    print(json.dumps(summary, indent=2, default=str), flush=True)
    return 0


# ---------------------------------------------------------------------------
# RIDER: mistral/llama placebo dose ladders, both populations
# ---------------------------------------------------------------------------

QL_STYLE_SUBSAMPLE_SEED = 20260714
QL_STYLE_SUBSAMPLE_N = 250


def rider_confab_subsample(rows_by_family: dict[str, list[dict[str, Any]]], families: list[str], dose_ladder=DOSE_LADDER,
                            seed: int = QL_STYLE_SUBSAMPLE_SEED, n: int = QL_STYLE_SUBSAMPLE_N) -> dict[tuple[str, int], list[dict[str, Any]]]:
    """Mirrors `abstention-wide-instrument-calibration/sources.py:ql_subsample`
    exactly: ONE `random.Random(seed)` instance advanced sequentially across
    (family, dose) strata in a fixed sorted order, each stratum's rows sorted
    by row_key before shuffling, so the draw depends only on (seed, the
    registered stratum order, the row pool) -- never process/OS iteration
    order."""
    rng = random.Random(seed)
    out: dict[tuple[str, int], list[dict[str, Any]]] = {}
    for family in families:
        for dose in dose_ladder:
            pool = sorted(rows_by_family[family], key=lambda r: r["row_key"])
            pool_copy = pool[:]
            rng.shuffle(pool_copy)
            out[(family, dose)] = pool_copy[:n]
    return out


def run_rider_family(args: argparse.Namespace, family: str) -> dict[str, Any]:
    cell = load_cell_yaml()
    rider = next(r for r in cell["rider_cells"] if isinstance(r, dict) and r.get("id") == f"rider_{family}_placebo_ladder")
    fcell = mrows.family_block(family)
    revision = mrows.resolve_revision(family)

    rows = load_joined_rows(family)
    held_confab = [r for r in rows if r["role"] == "confab" and r.get("split") == "held_out"]
    held_known = [r for r in rows if r["role"] == "known_correct_answered" and r.get("split") == "held_out"]

    reconstructed = load_reconstructed_directions(family)
    build_manifest = reconstructed["build_manifest"]
    layer = reconstructed["layer"]
    hidden_dim = build_manifest["hidden_dim"]

    subsample = rider_confab_subsample({family: held_confab}, [family])

    model, tokenizer, device = steer_lib.load_model(fcell["model"], revision)
    from MechInterp.intervention import get_decoder_layer
    import torch

    layer_module = get_decoder_layer(model, mrows.decoder_block_index(layer))

    if family == "mistral":
        # reuse_core_baseline: the core cell's own baseline pass already
        # covers this family's full held-out population; do not regenerate.
        baseline_path = runlog_path("core__baseline")
        if not baseline_path.is_file():
            raise SystemExit("rider_mistral_placebo_ladder requires the CORE baseline run log; run `heldout_scorer.py core` first (cell.yaml: arms.baseline = reuse_core_baseline).")
        baseline_by_key = {r["row_key"]: r for r in load_jsonl(baseline_path)}
    else:
        held_all = held_confab + held_known
        baseline_by_key = run_baseline_pass(model, tokenizer, device, held_all, args.batch_size, f"rider_{family}__baseline")

    dose_response: list[dict[str, Any]] = []
    for dose in DOSE_LADDER:
        dose_abs = float(dose * build_manifest["sigma_c"])
        seed = rider_direction_seed(family, dose)
        direction = fresh_random_direction(seed, hidden_dim)
        hook, ctrl = steer_lib.build_hook_and_controller(torch.tensor(direction, dtype=torch.float32), 1.0)

        confab_rung = subsample[(family, dose)]
        known_rung = held_known  # full population at every rung, per cell.yaml binding design requirement

        active_confab_by_key = run_active_pass(
            model, tokenizer, device, ctrl, layer_module, f"rider_{family}__random_direction__dose{dose}__confab",
            confab_rung, dose_abs, args.batch_size,
        ) if confab_rung else {}
        active_known_by_key = run_active_pass(
            model, tokenizer, device, ctrl, layer_module, f"rider_{family}__random_direction__dose{dose}__known_correct_answered",
            known_rung, dose_abs, args.batch_size,
        ) if known_rung else {}

        confab_scored = combine_active_and_baseline(confab_rung, active_confab_by_key, baseline_by_key)
        known_scored = combine_active_and_baseline(known_rung, active_known_by_key, baseline_by_key)

        dose_response.append({
            "dose_multiplier": dose, "dose_abs": dose_abs, "direction_seed": seed,
            "confab": {
                "n": len(confab_scored), "v2": gates_lib.rate_summary_v2(confab_scored),
                "by_source": gates_lib.rate_by_source(confab_scored),
            },
            "known_correct_answered": {
                "n": len(known_scored), "v2": gates_lib.rate_summary_v2(known_scored),
                "by_source": gates_lib.rate_by_source(known_scored),
            },
        })

    summary = {
        "status": "provisional_detector_v2_only",
        "note": "descriptive rider dose-response; no promotion gate; final wide rates require the blinded adjudication lane.",
        "family": family, "layer": layer, "dose_ladder": list(DOSE_LADDER),
        "subsample": {"rows_per_dose_cell": QL_STYLE_SUBSAMPLE_N, "seed": QL_STYLE_SUBSAMPLE_SEED, "n_confab_available": len(held_confab), "n_known_correct_answered": len(held_known)},
        "dose_response": dose_response,
    }
    write_json(COMMITTED / f"rider_{family}_heldout_summary.json", summary)
    return summary


def cmd_rider(args: argparse.Namespace) -> int:
    summary = run_rider_family(args, args.family)
    print(json.dumps(summary, indent=2, default=str), flush=True)
    return 0


# ---------------------------------------------------------------------------
# HELD-BACK clear-negative decoy source: undosed baseline over FIT-split
# known-correct rows (never part of any scored held-out arm).
# ---------------------------------------------------------------------------

def cmd_heldback(args: argparse.Namespace) -> int:
    family = args.family
    fcell = mrows.family_block(family)
    revision = mrows.resolve_revision(family)
    rows = load_joined_rows(family)
    fit_known = [r for r in rows if r["role"] == "known_correct_answered" and r.get("split") == "fit"]
    if not fit_known:
        raise SystemExit(f"no FIT-split known_correct_answered rows found for family={family!r}; cannot build the held-back decoy pool.")

    model, tokenizer, device = steer_lib.load_model(fcell["model"], revision)
    by_key = run_baseline_pass(model, tokenizer, device, fit_known, args.batch_size, f"heldback__{family}__known_fit_baseline")

    scored = [by_key[r["row_key"]] for r in fit_known]
    summary = {
        "family": family, "n_fit_known": len(fit_known),
        "v2": gates_lib.rate_summary_v2(scored),
        "n_well_formed_correct_and_non_refused_v2_candidates": sum(
            1 for r in scored if r.get("well_formed_correct") and not r.get("refused_v2")
        ),
    }
    write_json(COMMITTED / f"heldback_{family}_summary.json", summary)
    print(json.dumps(summary, indent=2, default=str), flush=True)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_core = sub.add_parser("core", help="mistral core cell: baseline/gated/K-seed random_direction/dose_knowns_ungated")
    p_core.add_argument("--batch-size", type=int, default=8)
    p_core.set_defaults(func=cmd_core)

    p_rider = sub.add_parser("rider", help="one family's placebo dose ladder (both populations)")
    p_rider.add_argument("--family", required=True, choices=sorted(FAMILY_TO_LAYER))
    p_rider.add_argument("--batch-size", type=int, default=8)
    p_rider.set_defaults(func=cmd_rider)

    p_hb = sub.add_parser("heldback", help="held-back clear-negative decoy source pass (undosed baseline over FIT known-correct rows)")
    p_hb.add_argument("--family", required=True, choices=sorted(FAMILY_TO_LAYER))
    p_hb.add_argument("--batch-size", type=int, default=8)
    p_hb.set_defaults(func=cmd_heldback)

    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
