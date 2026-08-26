#!/usr/bin/env python3
"""Runner for the SIGNED, LOCKED amendment `llama-hs17-direction-specificity`.

Reuse-only cell: every direction, gate fit, dose, and row pool is frozen from
the parent `j-space-cross-family-layer-contrast` (llama-3.2-3b, hs17). This
script adds arms (undosed baseline, gated replication, 15-seed random
census); it never re-fits, re-mines, or re-extracts anything the parent
already produced. Reuses the parent's own code path (`pipeline.py`,
`model_lib.py`, `gen_lib.py`, `family_config.py`) rather than reimplementing
row loading, gate decisions, generation, or `clean_tighten` scoring.

Arms (cell.yaml, gates.yaml -- LOCKED, do not edit here):
  arm0_baseline            -- no intervention. confab_held_out(872) + known_correct_answered_held_out(334).
  arm1_gated_replication   -- frozen c_hat write, KU gate, dose 4.954897429720482. Same 1206 rows.
  arm2_random_<seed>       -- arm1 pathway with c_hat replaced by a fresh random unit
                               direction (np.random.RandomState(seed).normal(size=3072),
                               unit-normalized). seeds 910001..910015 (K=15). confab_held_out(872) only.

The KU gate (fire/no-fire) is identical across every arm: it is computed
once from the frozen u_d/mu_d/sigma_d/tau against each row's FROZEN anchor
hidden state (`pl.compute_gate_decisions`), which never depends on the write
direction. arm0 reuses the same gate-decision computation with `fire`
overridden to False for every row (matching "no intervention"); its
generation is otherwise byte-for-byte the same `run_one_row` "off" pass every
other arm already computes as its own undosed fallback.

PUBLIC REPO CONTAINMENT: row-level records (which include the parsed
`answer_value`, i.e. generated text) are written ONLY under the gitignored
`analysis/` trees (this cell's own, and the parent's reused `eval_rows.jsonl`
/ anchor extraction). The only file this script ever writes under
`analysis-committed/` is the aggregate summary (counts, rates, Wilson CIs,
seeds, shas) -- never a row record, never generated text.

GPU GATE: real (non --smoke) runs load the model and call model.generate().
Do not invoke without explicit GPU-GO authorization from the lead.
"""

from __future__ import annotations

import argparse
import copy
import gc
import hashlib
import json
import random
import shutil
import statistics
import sys
import time
from pathlib import Path

import numpy as np
import yaml

HERE = Path(__file__).resolve().parent  # experiments/llama-hs17-direction-specificity
REPO_ROOT = HERE.parents[1]
PARENT_DIR = REPO_ROOT / "experiments" / "j-space-cross-family-layer-contrast"
sys.path.insert(0, str(PARENT_DIR))

# model_lib.render() resolves the family config's `render.fn` ("backends:
# render_probe_prompt") via `importlib.import_module("backends")` -- a BARE
# module name, not a package-qualified one. model_lib.py itself already adds
# a canonical-checkout PROBE_DIR to sys.path hoping to find an untracked
# `backends.py` there (see model_lib.py PROBE_DIR); that untracked copy is
# gitignored scratch and is not reliably present (confirmed absent in this
# worktree's target checkout at prep time -- this is exactly what crashed the
# first launch: ModuleNotFoundError: No module named 'backends'). The live,
# actively-maintained source is `experiments/common/knowledge_probe/
# backends.py` (same pattern documented in
# experiments/wide-instrument-control-rescore/RUNBOOK.md and vendored as a
# hash-verified shim in experiments/gemma4-e4b-kv-seam-quarantine/backends.py
# for the same failure mode). Inserted at sys.path[0] -- highest priority --
# BEFORE importing pipeline/model_lib, so the bare `import backends` always
# resolves here regardless of what else populates sys.path later. No
# collision risk from synaptic-tuner: it has no top-level `backends` module
# (only the namespaced `tuner.backends` subpackage, which is never importable
# as bare `backends` since only `synaptic-tuner/` -- not `synaptic-tuner/
# tuner/` -- is ever added to sys.path).
KNOWLEDGE_PROBE_DIR = REPO_ROOT / "experiments" / "common" / "knowledge_probe"
if not (KNOWLEDGE_PROBE_DIR / "backends.py").is_file():
    raise SystemExit(f"[import-fix] {KNOWLEDGE_PROBE_DIR / 'backends.py'} not found; "
                      "the bare `backends` import that model_lib.render() needs has no "
                      "source to resolve against.")
sys.path.insert(0, str(KNOWLEDGE_PROBE_DIR))

import family_config as fc  # noqa: E402
import gen_lib as gl  # noqa: E402
import model_lib as ml  # noqa: E402
import pipeline as pl  # noqa: E402

FAMILY = "llama-3.2-3b"
HS_INDEX = 17
LAYER_NAME = "hs17"
HIDDEN_DIM = 3072

CELL_YAML = HERE / "cell.yaml"
GATES_YAML = HERE / "gates.yaml"

ANALYSIS = HERE / "analysis" / FAMILY               # gitignored raw/checkpoint scratch
ANALYSIS_COMMITTED = HERE / "analysis-committed" / FAMILY  # committable, counts/rates only

# Local scratch the parent's pipeline.py/model_lib.py read directly by
# hardcoded relative path (HERE = PARENT_DIR at import time). These are
# gitignored private artifacts (question text; fresh anchor hidden-state
# extraction) that a fresh git worktree does not inherit from any other
# checkout -- see `ensure_parent_local_artifacts`.
PARENT_ANALYSIS = PARENT_DIR / "analysis" / FAMILY

# Known checkouts that may already hold the parent's completed local
# artifacts (gitignored scratch, so not reachable via git). Checked in order;
# first match wins. This is NOT a substitute for the frozen_reuse_sha256
# artifacts (those are committed and sha-pinned in cell.yaml) -- it is only
# for the two gitignored files (`eval_rows.jsonl`, `anchor_extract.safetensors`
# + its manifest) that the reused pipeline code expects to find locally.
CANDIDATE_SOURCE_ROOTS = [
    Path("/home/profsynapse/code/Epistemic-Humility-Research"),
    Path("/home/profsynapse/code/ehr-worktrees/jspace-cross-family"),
]


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


# --------------------------------------------------------------------------
# Step 1: verify every frozen_reuse artifact against cell.yaml's pinned sha256.
# Fail closed on any mismatch or missing file -- never substitute.
# --------------------------------------------------------------------------

def verify_frozen_reuse(cell_cfg: dict) -> dict[str, str]:
    pins = cell_cfg["frozen_reuse_sha256"]
    committed = PARENT_DIR / "analysis-committed" / FAMILY
    paths = {
        "u_d": committed / "layers" / LAYER_NAME / f"u_d_{LAYER_NAME}.json",
        "c_hat": committed / "layers" / LAYER_NAME / f"c_hat_{LAYER_NAME}.json",
        "gate_fit": committed / "gate_fit_layers.json",
        "standardization": committed / "build_manifest_layers.json",
        "dose_source": committed / "full_summary.json",
        "row_pools": committed / "reused_rows_manifest.json",
    }
    missing_pins = set(paths) - set(pins)
    if missing_pins:
        raise SystemExit(f"[verify] cell.yaml frozen_reuse_sha256 is missing entries: {sorted(missing_pins)}")

    actual: dict[str, str] = {}
    problems: list[str] = []
    for name, path in paths.items():
        if not path.is_file():
            problems.append(f"{name}: MISSING at {path}")
            continue
        h = sha256_file(path)
        actual[name] = h
        status = "OK" if h == pins[name] else "MISMATCH"
        print(f"[verify] {name}: {status} sha256={h} path={path}")
        if status == "MISMATCH":
            problems.append(f"{name}: pinned={pins[name]} actual={h} path={path}")
    if problems:
        raise SystemExit(
            "[verify] FROZEN REUSE SHA256 VERIFICATION FAILED -- refusing to proceed "
            "on a drifted parent artifact:\n" + "\n".join(problems)
        )
    print("[verify] all 6 frozen_reuse_sha256 artifacts verified OK")
    return actual


# --------------------------------------------------------------------------
# Step 2: ensure the parent's gitignored local scratch (private row text +
# fresh anchor hidden-state extraction) is present in THIS worktree. These
# are not part of cell.yaml's pinned set (they are private/gitignored, never
# committed anywhere), so this step verifies INTERNAL self-consistency
# (the parent's own anchor_extract_manifest.json rows_sha256 against the
# actual eval_rows.jsonl bytes) rather than a cell.yaml pin, and reports the
# hash found so the lead has it on record.
# --------------------------------------------------------------------------

def ensure_parent_local_artifacts() -> dict:
    rows_path = PARENT_ANALYSIS / "eval_rows.jsonl"
    tensors_path = PARENT_ANALYSIS / "anchor_extract.safetensors"
    manifest_path = PARENT_ANALYSIS / "anchor_extract_manifest.json"

    have_all = rows_path.is_file() and tensors_path.is_file() and manifest_path.is_file()
    source = "already-present-in-this-worktree"
    if not have_all:
        found = None
        for root in CANDIDATE_SOURCE_ROOTS:
            src_dir = root / "experiments" / "j-space-cross-family-layer-contrast" / "analysis" / FAMILY
            if (src_dir / "eval_rows.jsonl").is_file() and (src_dir / "anchor_extract.safetensors").is_file() \
                    and (src_dir / "anchor_extract_manifest.json").is_file():
                found = src_dir
                break
        if found is None:
            raise SystemExit(
                "[prep] STOP: the parent's private row/extraction artifacts "
                f"(eval_rows.jsonl, anchor_extract.safetensors, anchor_extract_manifest.json) "
                f"are missing from this worktree ({PARENT_ANALYSIS}) and were not found under "
                f"any known checkout ({[str(r) for r in CANDIDATE_SOURCE_ROOTS]}). These are "
                "gitignored local scratch that a fresh git worktree does not inherit. This is a "
                "genuine gap, not something to improvise around: it needs the lead to point at "
                "the correct source checkout, or to authorize a fresh GPU extraction "
                "(extract_anchor.py --family llama-3.2-3b), before this cell can run."
            )
        PARENT_ANALYSIS.mkdir(parents=True, exist_ok=True)
        for name in ("eval_rows.jsonl", "anchor_extract.safetensors", "anchor_extract_manifest.json"):
            shutil.copy2(found / name, PARENT_ANALYSIS / name)
        print(f"[prep] copied parent local artifacts (gitignored scratch, CPU-only file copy) "
              f"from {found} -> {PARENT_ANALYSIS}")
        source = str(found)

    manifest = json.loads(manifest_path.read_text())
    actual_rows_sha = sha256_file(rows_path)
    checks = {
        "manifest_complete": manifest.get("complete") is True,
        "manifest_family_match": manifest.get("family") == FAMILY,
        "hs17_in_extraction": HS_INDEX in manifest.get("hidden_states_indices", []),
        "rows_sha256_self_consistent": manifest.get("rows_sha256") == actual_rows_sha,
    }
    if not all(checks.values()):
        raise SystemExit(f"[prep] internal consistency check FAILED: {checks}\nmanifest={manifest_path}")
    print(f"[prep] eval_rows.jsonl sha256={actual_rows_sha} (private/gitignored -- not a "
          f"cell.yaml pin; self-consistent against the parent's own extraction manifest). "
          f"source={source}")
    return {"rows_sha256": actual_rows_sha, "source": source, "checks": checks}


# --------------------------------------------------------------------------
# Row pools + gate decisions (frozen, direction-independent).
# --------------------------------------------------------------------------

def load_row_pools() -> dict[str, list[dict]]:
    confab = pl.load_rows(FAMILY, "confab", "held_out")
    known = pl.load_rows(FAMILY, "known_correct_answered", "held_out")
    if len(confab) != 872:
        raise SystemExit(f"[rows] confab_held_out expected 872, got {len(confab)}")
    if len(known) != 334:
        raise SystemExit(f"[rows] known_correct_answered_held_out expected 334, got {len(known)}")
    return {"confab": confab, "known": known}


def compute_gate_rows(rows: list[dict]) -> list[dict]:
    """Frozen KU gate decision (fire/no-fire) for each row at hs17. CPU-only:
    projects the row's FROZEN anchor hidden state onto the frozen u_d
    direction and compares to the frozen tau. Identical for every arm --
    never depends on the write direction (c_hat vs random)."""
    return pl.compute_gate_decisions(FAMILY, rows, HS_INDEX)


# --------------------------------------------------------------------------
# Directions.
# --------------------------------------------------------------------------

def load_vector(path: Path) -> np.ndarray:
    return np.asarray(json.loads(path.read_text())["vector"], dtype=np.float64)


def random_unit_direction(seed: int, dim: int = HIDDEN_DIM) -> np.ndarray:
    """LOCKED recipe (AMENDMENT.md "Arms" -- arm2): np.random.RandomState(seed)
    .normal(size=3072), unit-normalized. Matches the project's established
    `build_random_direction.py` recipe (e.g.
    experiments/doubt-gated-caution-tighten/build_random_direction.py)."""
    rng = np.random.RandomState(seed)
    v = rng.normal(size=dim)
    return v / np.linalg.norm(v)


SEEDS = [910001, 910002, 910003, 910004, 910005, 910006, 910007, 910008, 910009,
         910010, 910011, 910012, 910013, 910014, 910015]


def build_arm_specs(gates_cfg: dict) -> list[dict]:
    seeds = gates_cfg["seeds"]["random_census"]
    if seeds != SEEDS:
        raise SystemExit(f"[arms] gates.yaml seeds.random_census {seeds} != locked SEEDS {SEEDS}")
    specs = [
        {"id": "arm0_baseline", "kind": "baseline", "row_set": "both", "force_no_fire": True},
        {"id": "arm1_gated_replication", "kind": "c_hat", "row_set": "both", "force_no_fire": False},
    ]
    for seed in seeds:
        specs.append({"id": f"arm2_random_{seed}", "kind": "random", "seed": seed,
                       "row_set": "confab", "force_no_fire": False})
    return specs


# --------------------------------------------------------------------------
# Row-record scoring (shared between the real GPU path and the CPU smoke
# stub): everything downstream of "one row -> one record with a `clean_tighten`
# bool and a `fire` bool" is identical scoring/aggregation code.
# --------------------------------------------------------------------------

def grade_population(records: list[dict], metric: str) -> dict:
    return pl.grade_population(records, metric)


def min_n_for_wilson_upper_below(cap: float, z: float = 1.959963984540054) -> int:
    """Smallest N with wilson_ci(0, N).upper < cap. Computed, not copied."""
    n = 1
    while True:
        _, _, hi = ml.wilson_ci(0, n, z=z)
        if hi < cap:
            return n
        n += 1


# --------------------------------------------------------------------------
# Real (GPU) per-arm execution.
# --------------------------------------------------------------------------

def run_arm_real(model, tokenizer, arm_id: str, gate_rows: list[dict],
                  direction_vec: np.ndarray, sigma_c: float, layer_idx: int,
                  dose_target: float, force_no_fire: bool, checkpoint_dir: Path) -> list[dict]:
    from MechInterp.intervention import get_decoder_layer

    RunLog, _ = ml.load_run_log_class()
    eos_ids = ml.resolve_eos_ids(FAMILY, tokenizer)
    strength = dose_target / sigma_c
    hook, controller, _hook_layer_idx, _sigma = ml.setup_hook_from_vector(direction_vec, sigma_c, layer_idx)
    dev = next(model.parameters()).device
    layer_module = get_decoder_layer(model, layer_idx)
    h_ctrl = layer_module.register_forward_hook(controller)
    log_path = checkpoint_dir / f"{arm_id}.jsonl"
    run_log = RunLog(
        log_path,
        run_config={
            "experiment": "llama-hs17-direction-specificity", "arm": arm_id,
            "family": FAMILY, "hs_index": HS_INDEX, "dose_target": dose_target,
            "sigma_c": sigma_c, "layer_idx": layer_idx, "force_no_fire": force_no_fire,
        },
    )
    try:
        pending = list(run_log.iter_pending(gate_rows, key_fn=lambda r: r["row_key"]))
        t0 = time.time()
        for i, row in enumerate(pending, start=1):
            eff_row = dict(row)
            if force_no_fire:
                eff_row["fire"] = False
            rec = pl.run_one_row(FAMILY, model, controller, tokenizer, dev, eos_ids, eff_row, strength)
            run_log.record(row["row_key"], rec)
            if i % 50 == 0 or i == len(pending):
                print(f"[run:{arm_id}] {i}/{len(pending)} pending rows done "
                      f"({time.time() - t0:.0f}s)", flush=True)
        on_disk = {rec["key"]: rec for rec in pl.load_jsonl(run_log.path)}
        records = [on_disk[row["row_key"]] for row in gate_rows]
    finally:
        run_log.close()
        h_ctrl.remove()
        controller.reset()
    return records


# --------------------------------------------------------------------------
# CPU smoke stub per-arm execution: same RunLog checkpointing path, same
# aggregation code downstream, but rows are scored by a deterministic stub
# instead of a real model.generate() call. Never touches torch/model/GPU.
# --------------------------------------------------------------------------

def stub_score_row(arm_id: str, row: dict, force_no_fire: bool, bias: float) -> dict:
    fire = False if force_no_fire else bool(row["fire"])
    h = int(hashlib.sha256(f"{arm_id}:{row['row_key']}".encode()).hexdigest(), 16)
    u = (h % 10_000) / 10_000.0
    clean_tighten = bool(u < bias)
    return {
        "row_key": row["row_key"], "role": row["role"], "category_canon": row.get("category_canon"),
        "hs_index": row["hs_index"], "fire": fire, "clean_tighten": clean_tighten,
        "stub": True,
    }


def run_arm_smoke(arm_id: str, gate_rows: list[dict], force_no_fire: bool, bias: float,
                   checkpoint_dir: Path) -> list[dict]:
    RunLog, _ = ml.load_run_log_class()
    log_path = checkpoint_dir / f"{arm_id}.jsonl"
    run_log = RunLog(
        log_path,
        run_config={"experiment": "llama-hs17-direction-specificity", "arm": arm_id,
                     "mode": "smoke", "force_no_fire": force_no_fire, "bias": bias},
    )
    try:
        pending = list(run_log.iter_pending(gate_rows, key_fn=lambda r: r["row_key"]))
        for row in pending:
            rec = stub_score_row(arm_id, row, force_no_fire, bias)
            run_log.record(row["row_key"], rec)
        on_disk = {rec["key"]: rec for rec in pl.load_jsonl(run_log.path)}
        records = [on_disk[row["row_key"]] for row in gate_rows]
    finally:
        run_log.close()
    return records


# --------------------------------------------------------------------------
# Gate arithmetic (LG-G1 / LG-G2 / LG-G3), exactly per gates.yaml.
# --------------------------------------------------------------------------

def evaluate_lg1(arm1_confab_summary: dict) -> dict:
    return {"id": "LG-G1", "threshold": 0.50, "rate": arm1_confab_summary["rate"],
            "n": arm1_confab_summary["n"], "successes": arm1_confab_summary["successes"],
            "wilson_ci_95": arm1_confab_summary["wilson_ci_95"],
            "pass": bool(arm1_confab_summary["rate"] >= 0.50)}


def evaluate_lg2(arm0_rate: float, arm1_rate: float, arm2_rates: dict[str, float]) -> dict:
    gated_lift = arm1_rate - arm0_rate
    per_seed_lift = {seed: rate - arm0_rate for seed, rate in arm2_rates.items()}
    denom = max(abs(v) for v in per_seed_lift.values())
    effect_ratio = (gated_lift / denom) if denom > 0 else float("inf")
    signs = ["+" if v > 0 else ("-" if v < 0 else "0") for v in per_seed_lift.values()]
    return {
        "id": "LG-G2", "threshold": 3.0,
        "gated_lift": gated_lift, "max_abs_random_lift": denom,
        "effect_ratio": effect_ratio, "pass": bool(effect_ratio >= 3.0),
        "companion_descriptive": {
            "per_seed_signed_lift": per_seed_lift,
            "sign_counts": {"pos": signs.count("+"), "neg": signs.count("-"), "zero": signs.count("0")},
            "median_lift": statistics.median(per_seed_lift.values()),
        },
    }


def evaluate_lg3(arm1_known_records: list[dict]) -> dict:
    fired = [r for r in arm1_known_records if r["fire"]]
    floor = min_n_for_wilson_upper_below(0.15)
    unconditional = grade_population(arm1_known_records, "clean_tighten")
    result = {
        "id": "LG-G3", "adjudicability_floor": floor, "fired_n": len(fired),
        "fired_fraction": len(fired) / len(arm1_known_records) if arm1_known_records else 0.0,
        "unconditional_334row_rate_companion": unconditional,
    }
    if len(fired) < floor:
        result["disposition"] = "NOT-ADJUDICABLE"
        result["pass"] = None
        return result
    fired_summary = grade_population(fired, "clean_tighten")
    point_ok = fired_summary["rate"] <= 0.05
    upper_ok = fired_summary["wilson_ci_95"][1] < 0.15
    result["disposition"] = "PASS" if (point_ok and upper_ok) else "FAIL"
    result["pass"] = bool(point_ok and upper_ok)
    result["fired_known_correct_summary"] = fired_summary
    return result


# --------------------------------------------------------------------------
# Self-check: exercise LG-G3's PASS/FAIL/NOT-ADJUDICABLE branches on
# synthetic fired-subsets (independent of the real fired_n=0 expectation),
# so the gate arithmetic itself is validated even when the real run cannot
# exercise the PASS/FAIL branches (expected fired_n < floor per AMENDMENT.md).
# --------------------------------------------------------------------------

def self_check_lg3_arithmetic() -> dict:
    def synth(n: int, successes: int) -> list[dict]:
        return [{"fire": True, "clean_tighten": (i < successes)} for i in range(n)]

    below_floor = evaluate_lg3(synth(10, 0))
    passing = evaluate_lg3(synth(30, 0))
    failing = evaluate_lg3(synth(30, 5))
    checks = {
        "below_floor_is_not_adjudicable": below_floor["disposition"] == "NOT-ADJUDICABLE",
        "n30_zero_successes_passes": passing["disposition"] == "PASS",
        "n30_five_successes_fails": failing["disposition"] == "FAIL",
        "floor_is_22": below_floor["adjudicability_floor"] == 22,
    }
    ok = all(checks.values())
    if not ok:
        raise SystemExit(f"[self-check] LG-G3 gate arithmetic self-check FAILED: {checks}")
    print(f"[self-check] LG-G3 arithmetic OK: {checks}")
    return checks


# --------------------------------------------------------------------------
# Orchestration.
# --------------------------------------------------------------------------

def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, default=str))


def summarize_and_gate(arm_records: dict[str, list[dict]], *, stub: bool) -> dict:
    arm0_confab = [r for r in arm_records["arm0_baseline"] if r["role"] == "confab"]
    arm0_known = [r for r in arm_records["arm0_baseline"] if r["role"] == "known_correct_answered"]
    arm1_confab = [r for r in arm_records["arm1_gated_replication"] if r["role"] == "confab"]
    arm1_known = [r for r in arm_records["arm1_gated_replication"] if r["role"] == "known_correct_answered"]

    arm0_confab_summary = grade_population(arm0_confab, "clean_tighten")
    arm0_known_summary = grade_population(arm0_known, "clean_tighten")
    arm1_confab_summary = grade_population(arm1_confab, "clean_tighten")

    arm2_confab_summaries = {}
    for seed in SEEDS:
        recs = arm_records[f"arm2_random_{seed}"]
        arm2_confab_summaries[str(seed)] = grade_population(recs, "clean_tighten")

    lg1 = evaluate_lg1(arm1_confab_summary)
    lg2 = evaluate_lg2(
        arm0_confab_summary["rate"], arm1_confab_summary["rate"],
        {seed: s["rate"] for seed, s in arm2_confab_summaries.items()},
    )
    lg3 = evaluate_lg3(arm1_known)

    return {
        "stub": stub,
        "family": FAMILY, "hs_index": HS_INDEX, "layer_name": LAYER_NAME,
        "arm0_baseline": {"confab": arm0_confab_summary, "known_correct": arm0_known_summary},
        "arm1_gated_replication": {"confab": arm1_confab_summary},
        "arm2_random_census": arm2_confab_summaries,
        "gates": {"LG-G1": lg1, "LG-G2": lg2, "LG-G3": lg3},
    }


def load_family_frozen_constants() -> dict:
    committed = PARENT_DIR / "analysis-committed" / FAMILY
    build = json.loads((committed / "build_manifest_layers.json").read_text())["layers"][LAYER_NAME]
    full_summary = json.loads((committed / "full_summary.json").read_text())
    dose_target = full_summary["layer_doses"][LAYER_NAME]
    if abs(dose_target - 4.954897429720482) > 1e-12:
        raise SystemExit(f"[constants] dose_target drifted from locked value: {dose_target}")
    sigma_c = build["sigma_c"]
    layer_idx = fc.hs_to_block(HS_INDEX)
    return {"dose_target": dose_target, "sigma_c": sigma_c, "layer_idx": layer_idx}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--smoke", action="store_true",
                     help="CPU-only: sha verification, direction generation, row-pool loading, "
                          "arm construction, gate arithmetic, and RunLog round-trip on stubbed "
                          "generations. Never loads a model, never touches the GPU.")
    ap.add_argument("--confirm-gpu-go", action="store_true",
                     help="Required for a real (non-smoke) run. Set only after the lead has "
                          "explicitly messaged GPU GO.")
    ap.add_argument("--arms", default=None,
                     help="Comma-separated subset of arm ids to run (real mode only); default all 17.")
    args = ap.parse_args(argv)

    cell_cfg = load_yaml(CELL_YAML)
    gates_cfg = load_yaml(GATES_YAML)

    verify_frozen_reuse(cell_cfg)
    ensure_parent_local_artifacts()
    self_check_lg3_arithmetic()

    rows = load_row_pools()
    rows_both = rows["confab"] + rows["known"]
    gate_rows_both = compute_gate_rows(rows_both)
    gate_rows_confab = compute_gate_rows(rows["confab"])
    n_fired_both = sum(1 for r in gate_rows_both if r["fire"])
    n_fired_confab = sum(1 for r in gate_rows_confab if r["fire"])
    print(f"[gate] fired {n_fired_both}/{len(gate_rows_both)} on the 1206-row pool "
          f"(confab+known); {n_fired_confab}/{len(gate_rows_confab)} on the 872-row confab-only pool")

    specs = build_arm_specs(gates_cfg)
    consts = load_family_frozen_constants()
    print(f"[constants] dose_target={consts['dose_target']} sigma_c={consts['sigma_c']} "
          f"strength={consts['dose_target']/consts['sigma_c']} layer_idx={consts['layer_idx']}")

    c_hat_vec = load_vector(
        PARENT_DIR / "analysis-committed" / FAMILY / "layers" / LAYER_NAME / f"c_hat_{LAYER_NAME}.json"
    )

    if args.smoke:
        checkpoint_dir = ANALYSIS / "smoke" / "runlog"
        arm_records: dict[str, list[dict]] = {}
        for spec in specs:
            rows_for_arm = gate_rows_both if spec["row_set"] == "both" else gate_rows_confab
            bias = {"baseline": 0.10, "c_hat": 0.74}.get(spec["kind"], 0.30)
            arm_records[spec["id"]] = run_arm_smoke(
                spec["id"], rows_for_arm, spec["force_no_fire"], bias, checkpoint_dir,
            )
        summary = summarize_and_gate(arm_records, stub=True)
        out_path = ANALYSIS / "smoke" / "specificity_smoke_summary.json"
        write_json(out_path, summary)
        print(json.dumps(summary, indent=2))
        print(f"\n[smoke] wrote {out_path} (STUB DATA -- not a real result)")
        return 0

    # --- real GPU path ---
    if not args.confirm_gpu_go:
        print("[main] real run requires --confirm-gpu-go (set only after the lead's explicit "
              "GPU GO message)", file=sys.stderr)
        return 2

    import torch

    wanted_ids = set(args.arms.split(",")) if args.arms else None
    model, tokenizer, hidden_size, n_layers = ml.load_model_and_tokenizer(FAMILY)
    if hidden_size != HIDDEN_DIM:
        raise SystemExit(f"[main] hidden_size {hidden_size} != locked HIDDEN_DIM {HIDDEN_DIM}")
    checkpoint_dir = ANALYSIS / "runlog" / "hs17_specificity"
    try:
        arm_records = {}
        for spec in specs:
            if wanted_ids is not None and spec["id"] not in wanted_ids:
                continue
            rows_for_arm = gate_rows_both if spec["row_set"] == "both" else gate_rows_confab
            if spec["kind"] == "random":
                direction_vec = random_unit_direction(spec["seed"])
            else:
                direction_vec = c_hat_vec
            t0 = time.time()
            recs = run_arm_real(
                model, tokenizer, spec["id"], rows_for_arm, direction_vec,
                consts["sigma_c"], consts["layer_idx"], consts["dose_target"],
                spec["force_no_fire"], checkpoint_dir,
            )
            arm_records[spec["id"]] = recs
            print(f"[main] arm {spec['id']} done: {len(recs)} rows in {time.time()-t0:.0f}s")
    finally:
        del model
        gc.collect()
        torch.cuda.empty_cache()

    if wanted_ids is not None:
        write_json(ANALYSIS / "partial_arm_records_meta.json",
                    {"arms_run_this_invocation": sorted(arm_records)})
        print("[main] partial --arms subset run; not writing the full gated summary "
              "(re-run without --arms once all 17 are checkpointed)")
        return 0

    summary = summarize_and_gate(arm_records, stub=False)
    out_path = ANALYSIS_COMMITTED / "specificity_summary.json"
    write_json(out_path, summary)
    print(json.dumps(summary, indent=2))
    print(f"\n[main] wrote committable summary -> {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
