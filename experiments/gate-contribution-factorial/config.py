"""Locked registered constants for gate-contribution-factorial.

Unlike `placebo-seed-distribution-census/cell.yaml` (which has a PyYAML
ParserError at sign time and is never parsed programmatically), THIS
experiment's `cell.yaml` and `gates.yaml` both parse as valid YAML and both
sha256-match their `experiment.yaml` pins (verified live below, and by
`test_factorial_smoke.py::test_cell_and_gates_yaml_parse_and_match_pins`).
Every numeric constant below is still transcribed LITERALLY (not read via
`yaml.safe_load` at import time) so the harness's behavior is reviewable from
this file alone and cannot silently change if the locked YAML is edited
without a re-sign; `verify_against_live_yaml()` cross-checks a representative
subset of these literals against a live parse of cell.yaml/gates.yaml and is
exercised by the smoke suite, so drift between this file and the signed YAML
is caught rather than assumed away.

Every value is cited to the AMENDMENT.md/cell.yaml/gates.yaml line(s) it was
read from (both read in full before writing this).
"""

from __future__ import annotations

import hashlib
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[1]

CELL_YAML_PATH = HERE / "cell.yaml"
GATES_YAML_PATH = HERE / "gates.yaml"
EXPERIMENT_YAML_PATH = HERE / "experiment.yaml"

CELL_YAML_SHA256_PINNED = "c4939dbdcfe9588750eb5cdc38f4f9d9f0613c8f532dffd9edbc333db6f44047"
GATES_YAML_SHA256_PINNED = "0fb40a9d3b28d562838e6978319082d270f2e3dcf4f9d08d385a801b629cee66"

# ---------------------------------------------------------------------------
# Cross-worktree source roots (THIS machine's local worktree layout; see
# `git worktree list`). Mirrors placebo-seed-distribution-census/config.py's
# own `_WT` convention.
# ---------------------------------------------------------------------------
_WT = Path("/home/profsynapse/code/ehr-worktrees")
QH_WT = _WT / "qwen35-midband-heldout" / "experiments" / "qwen35-4b-midband-heldout"     # qwen baseline/gated/permuted_gate runlogs, fire decisions, private rows (gitignored there)
RR2_WT = _WT / "rr2-mistral-confirm" / "experiments" / "rr2-mistral-adjudicated-refusal-confirm"  # mistral baseline/gated runlogs, reconstructed hs16 directions, private rows (gitignored there)

# Committed-in-THIS-worktree sources (no cross-worktree staging needed).
DOUBT_SNAP_DIR = REPO_ROOT / "experiments" / "qwen35-4b-midband-doubt-snap"
RR_LOCAL_DIR = REPO_ROOT / "experiments" / "rr-cross-family-raw-refusal"
QH_LOCAL_DIR = REPO_ROOT / "experiments" / "qwen35-4b-midband-heldout"  # committed experiment dir (frozen_operating_point_hashes.json), NOT the gitignored analysis/ (that lives only in QH_WT)

# ---------------------------------------------------------------------------
# Families
# ---------------------------------------------------------------------------
FAMILIES = ("qwen35_4b", "mistral7b_v03")

LAYER_HS_INDEX = {"qwen35_4b": 20, "mistral7b_v03": 16}          # cell.yaml lines 40, 69
DECODER_BLOCK_INDEX = {"qwen35_4b": 19, "mistral7b_v03": 15}     # hs_index - 1, per midband-heldout/RR2 convention
HIDDEN_DIM = {"qwen35_4b": 2560, "mistral7b_v03": 4096}          # doubt-snap build_manifest.json / RR hs16_fit_build_manifest.json

SUBSTRATE = {
    "qwen35_4b": "Qwen/Qwen3.5-4B",                              # cell.yaml line 35
    "mistral7b_v03": "mistralai/Mistral-7B-Instruct-v0.3",       # cell.yaml line 64
}
REVISION = {
    "qwen35_4b": "851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a",     # cell.yaml line 36
    "mistral7b_v03": "c170c708c41dac9275d15a8fff4eca08d52bab71", # cell.yaml line 65
}

# qwen doubt-standardization / snap-standardization / gate (cell.yaml lines 43-48;
# doubt-snap build_manifest.json layers.hs20, cross-checked at staging time)
QWEN_MU_D = -0.290345686796538
QWEN_SIGMA_D = 1.669221862861343
QWEN_MU_C = -4.031343053353048
QWEN_SIGMA_C = 1.576023489724997
QWEN_TAU_FROZEN = -0.589747307635842

# mistral hs16 fit stats (cell.yaml does not restate these directly; RR's own
# committed hs16_fit_build_manifest.json, cross-checked against RR2's own
# reconstruction by mistral_direction_provenance.py at build)
MISTRAL_MU_D = -0.6997460008464047
MISTRAL_SIGMA_D = 0.501277980342804
MISTRAL_MU_C = -0.2035861113333241
MISTRAL_SIGMA_C = 0.3054430504224313
MISTRAL_TAU_FROZEN = -0.7844209705182725

SETPOINT_DOSE_ABS = {
    "qwen35_4b": 12.608187917799976,      # cell.yaml line 48; dose_mult 8 x sigma_c
    "mistral7b_v03": 3.6653166050691756,  # cell.yaml line 71; dose_mult 12 x sigma_c(hs16)=0.3054430504224313
}
DOSE_MULTIPLIER_SIGMA_C = {"qwen35_4b": 8, "mistral7b_v03": 12}  # cell.yaml lines 49, 72

# c_hat write gain = setpoint_dose_abs / sigma_c (the c_hat direction is
# calibrated so gain=1.0 corresponds to one sigma_c of realized projection;
# midband-heldout pipeline.py: `gain_gated = DOSE_ABS / fop["sigma_c"]`).
# random_direction write gain = setpoint_dose_abs / 1.0 (random_direction.json's
# own convention is sigma=1.0; midband-heldout: `gain_random = DOSE_ABS / 1.0`).
SIGMA_C = {"qwen35_4b": QWEN_SIGMA_C, "mistral7b_v03": MISTRAL_SIGMA_C}

HELDOUT_POOL = {
    "qwen35_4b": {"confab": 1332, "known_correct_answered": 360},   # cell.yaml line 50
    "mistral7b_v03": {"confab": 1312, "known_correct_answered": 382},  # cell.yaml line 73
}

TRUE_GATE_FIRE_COUNTS = {
    "mistral7b_v03": {"confab": 1303, "known": 0},   # cell.yaml line 74; RR2 lines 142, 151
    # qwen fire counts are NOT pre-registered as a flat constant (they are
    # recomputed per row from tau_frozen/mu_d/sigma_d via the staged fire
    # decisions); AMENDMENT states them descriptively as ~96.5%/~4.7%
    # (confab 1286/1332, known 17/360 -- verified against the staged
    # fire_decisions_heldout.jsonl at SC0, see staging.py).
}

WRITE_LAW = "erase_write"          # cell.yaml line 165
WRITE_POSITION = "anchor_onward"   # cell.yaml line 165
READBACK_TOLERANCE_REL = 0.005     # cell.yaml line 166; gates.yaml sc1
RANDOMNESS_BAR_COS = 0.015         # cell.yaml line 167; gates.yaml sc1

GEN_DO_SAMPLE = False               # cell.yaml line 170
GEN_MIN_NEW_TOKENS = 1              # cell.yaml line 171
GEN_MAX_NEW_TOKENS = 200            # cell.yaml line 172
GEN_EOS_ENABLED = True              # cell.yaml line 173
GEN_ENABLE_THINKING = False         # cell.yaml line 174

# Batch size: NOT a locked design knob in cell.yaml/AMENDMENT.md (no
# Decision-record item pins it). Adopted here as a build-time execution
# choice, matching placebo-seed-distribution-census's own LEAD DECISION
# (config.py BATCH_SIZE docstring) and this experiment's team-lead brief
# ("BATCH_SIZE=4 worked there"). `run_factorial.py --batch-size` can override
# at launch; report this as a build-time choice, not a spec value.
BATCH_SIZE = 4

# ---------------------------------------------------------------------------
# K fresh random-direction seeds (cell.yaml `random_seeds`, lines 146-148;
# Decision record item 15)
# ---------------------------------------------------------------------------
K_SEEDS_PER_FAMILY = 5
RANDOM_SEED_BLOCKS = {
    "qwen35_4b": [44000001, 44000002, 44000003, 44000004, 44000005],
    "mistral7b_v03": [45000001, 45000002, 45000003, 45000004, 45000005],
}

# ---------------------------------------------------------------------------
# Permuted-gate construction (cell.yaml `gates_construction`, lines 131-141)
# ---------------------------------------------------------------------------
PERMUTED_GATE_SEED = {
    "qwen35_4b": 20260713,      # SAME seed as qwen35-4b-midband-heldout's own permuted_gate arm; cell.yaml line 139
    "mistral7b_v03": 20260715,  # NEW, pinned at sign; cell.yaml line 140
}

# ---------------------------------------------------------------------------
# Subsample (cell.yaml `subsample`, lines 153-159; Decision record item 9)
# ---------------------------------------------------------------------------
SUBSAMPLE_CONFAB_ROWS_PER_FAMILY = 300
SUBSAMPLE_PERMUTATION_SEED = 46260714

# ---------------------------------------------------------------------------
# Census wide-instrument random null (direction-specificity reference; S1)
# cell.yaml `families.<family>.census_wide_null`, lines 53-60 / 77-84.
# ---------------------------------------------------------------------------
CENSUS_NULL = {
    "qwen35_4b": {
        "k": 15, "median_delta_pts": -6.0,
        "iqr_pts": [-6.833333333333334, -3.6666666666666674],
        "span_pts": [-8.333333333333334, 0.6666666666666667],
        "f_neg": 0.9333333333333333,
        "max_abs_delta_frac": 0.08333333333333334,
        "committed_sign": "negative",
    },
    "mistral7b_v03": {
        "k": 15, "median_delta_pts": 7.0,
        "iqr_pts": [1.1666666666666687, 13.666666666666666],
        "span_pts": [-7.999999999999999, 20.333333333333336],
        "f_pos": 0.8,
        "max_abs_delta_frac": 0.20333333333333334,
        "committed_sign": "positive",
    },
}

# ---------------------------------------------------------------------------
# Criterion floors (gates.yaml P1/P2/P3/S1; Decision record items 3, 5, 6)
# ---------------------------------------------------------------------------
P1_CONFAB_ABSTENTION_FLOOR = 0.60
P1_CONFAB_WILSON_LCB_FLOOR = 0.50
P1_WELL_FORMED_FLOOR = 0.80
P1_KNOWN_FALSE_REFUSAL_CEIL = 0.05
P1_KNOWN_WILSON_UCB_CEIL = 0.10

P2_GAP_SEL_C_HAT_FLOOR = 0.20
P3_COST_PROTECTION_C_HAT_FLOOR = 0.10
S1_EFFECT_RATIO_FLOOR = 3.0

# ---------------------------------------------------------------------------
# CG1 (grader calibration) constants -- identical to census/RR3
# ---------------------------------------------------------------------------
CG1_CLEAR_NEGATIVE_MIN_PER_SHARD = 0.95
CG1_CLEAR_POSITIVE_MIN_PER_SHARD = 0.60
CG1_CLEAR_POSITIVE_MIN_POOLED = 0.60
CG1_CLEAR_POSITIVE_DECOYS_PER_SHARD_FLOOR = 25

# ---------------------------------------------------------------------------
# Fleet model resolution (mirrors census/RR3's own resolve_revision
# discipline; used only as a live cross-check, SUBSTRATE/REVISION above are
# the constants the harness actually runs with).
# ---------------------------------------------------------------------------
FLEET_DIR = REPO_ROOT / "experiments" / "doubt-snap-cross-family-confirmatory"
FAMILY_TO_CELL_ID = {"qwen35_4b": "qwen35_4b", "mistral7b_v03": "mistral7b_instruct_v03"}


def _sha256_of_file(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def verify_pinned_hashes() -> dict[str, bool]:
    """cell.yaml/gates.yaml sha256 must match experiment.yaml's pins. Both
    files parse as valid YAML in this experiment (unlike census's cell.yaml),
    so this is a live, exact check, not a documented deviation."""
    return {
        "cell_yaml": _sha256_of_file(CELL_YAML_PATH) == CELL_YAML_SHA256_PINNED,
        "gates_yaml": _sha256_of_file(GATES_YAML_PATH) == GATES_YAML_SHA256_PINNED,
    }


def verify_against_live_yaml() -> dict[str, object]:
    """Cross-checks a representative subset of the literal constants above
    against a fresh `yaml.safe_load` of the locked, hash-verified cell.yaml/
    gates.yaml, so drift between this file and the signed spec is caught by
    the smoke suite rather than silently trusted."""
    import yaml

    cell = yaml.safe_load(CELL_YAML_PATH.read_text(encoding="utf-8"))
    gates = yaml.safe_load(GATES_YAML_PATH.read_text(encoding="utf-8"))

    mismatches: dict[str, tuple] = {}

    def check(name: str, expected, actual):
        if expected != actual:
            mismatches[name] = (expected, actual)

    qf = cell["families"]["qwen35_4b"]
    check("qwen.setpoint_dose_abs", SETPOINT_DOSE_ABS["qwen35_4b"], qf["setpoint_dose_abs"])
    check("qwen.tau_frozen", QWEN_TAU_FROZEN, qf["gate"]["tau_frozen"])
    check("qwen.heldout_confab", HELDOUT_POOL["qwen35_4b"]["confab"], qf["heldout_pool"]["confab"])
    check("qwen.heldout_known", HELDOUT_POOL["qwen35_4b"]["known_correct_answered"], qf["heldout_pool"]["known_correct_answered"])
    check("qwen.census_max_abs_delta_frac", CENSUS_NULL["qwen35_4b"]["max_abs_delta_frac"], qf["census_wide_null"]["max_abs_delta_frac"])

    mf = cell["families"]["mistral7b_v03"]
    check("mistral.setpoint_dose_abs", SETPOINT_DOSE_ABS["mistral7b_v03"], mf["setpoint_dose_abs"])
    check("mistral.heldout_confab", HELDOUT_POOL["mistral7b_v03"]["confab"], mf["heldout_pool"]["confab"])
    check("mistral.heldout_known", HELDOUT_POOL["mistral7b_v03"]["known_correct_answered"], mf["heldout_pool"]["known_correct_answered"])
    check("mistral.true_gate_fire_confab", TRUE_GATE_FIRE_COUNTS["mistral7b_v03"]["confab"], mf["true_gate_fire_counts"]["confab"])
    check("mistral.true_gate_fire_known", TRUE_GATE_FIRE_COUNTS["mistral7b_v03"]["known"], mf["true_gate_fire_counts"]["known"])
    check("mistral.census_max_abs_delta_frac", CENSUS_NULL["mistral7b_v03"]["max_abs_delta_frac"], mf["census_wide_null"]["max_abs_delta_frac"])

    check("permuted_seed.qwen", PERMUTED_GATE_SEED["qwen35_4b"], cell["gates_construction"]["permuted_gate"]["seed"]["qwen35_4b"])
    check("permuted_seed.mistral", PERMUTED_GATE_SEED["mistral7b_v03"], cell["gates_construction"]["permuted_gate"]["seed"]["mistral7b_v03"])

    check("random_seeds.qwen", RANDOM_SEED_BLOCKS["qwen35_4b"], cell["random_seeds"]["qwen35_4b"])
    check("random_seeds.mistral", RANDOM_SEED_BLOCKS["mistral7b_v03"], cell["random_seeds"]["mistral7b_v03"])

    check("subsample.rows_per_family", SUBSAMPLE_CONFAB_ROWS_PER_FAMILY, cell["subsample"]["confab"]["random_condition_arms"]["rows_per_family"])
    check("subsample.permutation_seed", SUBSAMPLE_PERMUTATION_SEED, cell["subsample"]["confab"]["random_condition_arms"]["permutation_seed"])

    check("write.readback_tolerance_rel", READBACK_TOLERANCE_REL, cell["write"]["readback_tolerance_rel"])
    check("write.randomness_bar_cos", RANDOMNESS_BAR_COS, cell["write"]["randomness_bar_cos"])
    check("gen.max_new_tokens", GEN_MAX_NEW_TOKENS, cell["write"]["generation"]["max_new_tokens"])
    check("gen.enable_thinking", GEN_ENABLE_THINKING, cell["write"]["generation"]["enable_thinking"])

    check("p2.c_hat_floor", P2_GAP_SEL_C_HAT_FLOOR, gates["p2_gate_selectivity_gap"]["c_hat_condition"]["floor"])
    check("p3.c_hat_floor", P3_COST_PROTECTION_C_HAT_FLOOR, gates["p3_cost_protection"]["c_hat_condition"]["floor"])
    # p1/s1 thresholds are embedded in gates.yaml prose fields (e.g.
    # "confab_abstention >= 0.60 AND ..."), not clean numeric keys; checked as
    # a substring containment on the literal's repr rather than a numeric
    # equality, since gates.yaml records them as a rule string, not a scalar.
    if str(P1_CONFAB_ABSTENTION_FLOOR) not in gates["p1_gate_benefit_cost"]["benefit"]:
        mismatches["p1.confab_floor_in_prose"] = (P1_CONFAB_ABSTENTION_FLOOR, gates["p1_gate_benefit_cost"]["benefit"])
    if str(S1_EFFECT_RATIO_FLOOR) not in gates["s1_direction_specificity"]["pass_conditions"]["effect_ratio"]:
        mismatches["s1.effect_ratio_floor_in_prose"] = (S1_EFFECT_RATIO_FLOOR, gates["s1_direction_specificity"]["pass_conditions"]["effect_ratio"])

    return {"pass": not mismatches, "mismatches": mismatches}
