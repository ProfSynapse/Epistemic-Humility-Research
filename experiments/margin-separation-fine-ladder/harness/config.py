"""Locked registered constants for margin-separation-fine-ladder (M1b).

Every numeric constant below is transcribed LITERALLY from the signed
`cell.yaml`/`gates.yaml` (not read via `yaml.safe_load` at import time), the
same convention `margin-mapping/config.py` (M1) and
`gate-contribution-factorial/config.py` use, so the harness's behavior is
reviewable from this file alone and cannot silently change if the locked
YAML is edited without a re-sign. `verify_pinned_hashes()` checks this
file's own two YAML pins against the live files on disk.

qwen35_4b ONLY (AMENDMENT.md posture: "mistral is void by instrument loss
per M1"). Several dict-by-family shapes are kept from M1's own config.py
(FAMILIES, SUBSTRATE, REVISION, ...) even though there is only one family
here, so the ported M1 modules (row_pool.py, dose_ladder.py, sc1_checks.py,
steer_lib.py) can be reused with the SAME call signatures unchanged.

Every value is cited to the line(s) it was read from in `cell.yaml`/
`gates.yaml`/`AMENDMENT.md` (all read in full before writing this).
"""

from __future__ import annotations

import hashlib
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXPERIMENT_DIR = HERE.parent
REPO_ROOT = HERE.parents[2]

CELL_YAML_PATH = EXPERIMENT_DIR / "cell.yaml"
GATES_YAML_PATH = EXPERIMENT_DIR / "gates.yaml"
EXPERIMENT_YAML_PATH = EXPERIMENT_DIR / "experiment.yaml"

# Pins recomputed from the signed files on 2026-07-17 during harness build;
# these match experiment.yaml's own `instrument.pins` block exactly.
CELL_YAML_SHA256_PINNED = "cc40b4327489d118ab3e105ba721538ac1e72e9632d4ae4e61f1350350dee849"
GATES_YAML_SHA256_PINNED = "45ea8f4f525257b81dfc44179aa440ce6c5f33b5cbcc6eb5eae35236fd7f6ab4"

# ---------------------------------------------------------------------------
# Family and frozen operating point (cell.yaml `families`, lines 31-45)
# ---------------------------------------------------------------------------
FAMILIES = ("qwen35_4b",)
FAMILY = "qwen35_4b"

LAYER_HS_INDEX = {"qwen35_4b": 20}                # cell.yaml line 38
DECODER_BLOCK_INDEX = {"qwen35_4b": 19}           # hs_index - 1, M1/factorial convention

SUBSTRATE = {"qwen35_4b": "Qwen/Qwen3.5-4B"}                              # cell.yaml line 34
REVISION = {"qwen35_4b": "851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a"}      # cell.yaml line 35

REFERENCE_DOSE_ABS = {"qwen35_4b": 12.608187917799976}   # cell.yaml line 44 (unchanged from M1 cell.yaml line 32)
QWEN_SIGMA_C = 1.576023489724997                          # cell.yaml line 45 (snap_standardization.sigma_c)
SIGMA_C = {"qwen35_4b": QWEN_SIGMA_C}

# ---------------------------------------------------------------------------
# Ladder (cell.yaml `ladder`, lines 50-56; Decision record item 1)
# ---------------------------------------------------------------------------
LADDER_MULTIPLIERS = (0.5, 0.55, 0.6, 0.65, 0.7, 0.75, 1.5, 2.0)   # cell.yaml line 51
NEW_RUNGS = (0.55, 0.6, 0.65, 0.7)                                  # cell.yaml line 52
REUSED_RUNGS = (0.5, 0.75, 1.5, 2.0)                                # cell.yaml line 53
FLOOR_EXACT_RUNG_MULT = 0.6                                         # cell.yaml line 54

WRITE_LAW = "erase_write"          # cell.yaml line 55
WRITE_POSITION = "anchor_onward"   # cell.yaml line 55

GEN_DO_SAMPLE = False               # cell.yaml line 56 (decode: greedy)
GEN_MAX_NEW_TOKENS = 200            # not restated in M1b's cell.yaml; reused byte-identically
                                     # from M1's own config.py GEN_MAX_NEW_TOKENS (M1 cites the
                                     # factorial's GEN_MAX_NEW_TOKENS=200; unchanged generation
                                     # stack per AMENDMENT.md "Design")
BATCH_SIZE = 4                      # cell.yaml line 56

# gates.yaml SC1_dose_and_preflight (M1's amended OR-rule, carried verbatim)
READBACK_TOLERANCE_REL = 0.005
READBACK_TOLERANCE_ABS_FRAC_OF_REF = 0.005

PREFLIGHT_ROWS_DEFAULT = 4                    # gates.yaml SC1 / cell.yaml preflight, line 177
PREFLIGHT_RUNG_MULTIPLIERS = (0.55, 0.7)      # cell.yaml preflight.gpu_preflight, line 177

RG0_DRIFT_CHECK_N_ROWS = 8            # cell.yaml preflight.rg0_drift_check, line 182
RG0_DRIFT_CHECK_RUNG_MULT = 0.75      # cell.yaml preflight.rg0_drift_check, line 183

# ---------------------------------------------------------------------------
# Population (cell.yaml `population`, lines 60-114; Decision record item 2)
# ---------------------------------------------------------------------------
REFINED_SUBSET_N = 53                   # cell.yaml line 71
REFINED_SUBSET_TIPPING_IDX = 5          # cell.yaml line 70 ("M1 tipping_idx == 5")
NEW_GENERATIONS_TOTAL = 212             # cell.yaml line 72 (53 rows x 4 new rungs)

KNOWN_ROWS_N = 360                      # cell.yaml line 99

# The highest pre-collapse rung on M1's OWN 10-rung index (0=baseline,
# 1=0.0625x, ..., 7=1.5x, 8=2.0x, 9=3.0x, 10=4.0x) -- this is the SAME index
# M1's own compute_scoreboard.py uses for `hp_idx` (leg_b), reused verbatim
# because the merge rule reuses M1's known-row tipping_idx/collapse_idx
# fields from the pinned margin_dataset unchanged (Decision record item 3,
# Option 1: zero new known-row generations).
HIGHEST_PRECOLLAPSE_RUNG_IDX_M1 = 7
HIGHEST_PRECOLLAPSE_RUNG_DOSE_ABS = 18.912281876699964   # the 1.5x rung; cell.yaml line 155

# The M1 10-rung series-index convention for margin_dataset rows (derive_margins.py):
# 0=baseline, then LADDER_MULTIPLIERS index+1 for M1's OWN 10-rung ladder
# (0.0625, 0.125, 0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0, 4.0). idx<=4 means
# tipped at or before 0.5x; idx==5 means tipped exactly at 0.75x; idx>=6
# means tipped at 1.0x or later.
M1_TIPPING_IDX_LE = 4     # idx<=4 bracket (margin <= 0.5x); cell.yaml merge_rule.idx_le_4
M1_TIPPING_IDX_GE = 6     # idx>=6 bracket (margin > 0.75x); cell.yaml merge_rule.idx_ge_6_or_censored

EXPECTED_PARTITION = {"idx_le_4": 181, "idx_5_refined": 53, "idx_ge_6_or_censored": 166}  # Decision record item 2
EXPECTED_CONFAB_TOTAL = 400

# ---------------------------------------------------------------------------
# Criterion surface (cell.yaml `criteria`, lines 150-159; gates.yaml
# `criteria`; Decision record items 4-5)
# ---------------------------------------------------------------------------
OBSERVABLE_BOUND_FLOOR = 2.5                          # cell.yaml line 156; gates.yaml line 35 (UNCHANGED from M1)
NUMERATOR_DOSE_ABS = 18.912281876699964               # cell.yaml line 155 (the 1.5x rung)
FLOOR_EXACT_RUNG_DOSE_ABS = 7.564912750679985         # cell.yaml line 158 (the 0.6x rung; equivalent pass surface)
ON_RUNG_BOUNDS = (2.0, 2.1429, 2.3077, 2.5, 2.7273, 3.0)   # cell.yaml line 157; NOT an exhaustive outcome enumeration

NON_MONOTONE_CEILING_REFINED = 0.05           # gates.yaml C1_construct_integrity, line 39 (fraction gate, flagged/53)
CALIBRATION_DISAGREEMENT_MAX = 0.05           # gates.yaml C1/SC2, line 24/40
CALIBRATION_CG1_CLEAR_NEGATIVE_MIN = 0.95     # gates.yaml SC2_grading_integrity, line 23
CALIBRATION_CG1_CLEAR_POSITIVE_MIN = 0.60     # gates.yaml SC2_grading_integrity, line 23
CALIBRATION_CG1_MIN_CLEAR_POSITIVE_DECOYS = 25  # gates.yaml SC2_grading_integrity, line 23

# ---------------------------------------------------------------------------
# Statistics (gates.yaml `statistics`; cell.yaml `analysis.bootstrap`)
# ---------------------------------------------------------------------------
BOOTSTRAP_N_RESAMPLES = 10000            # cell.yaml line 163; gates.yaml line 8
BOOTSTRAP_SEED = 48260719                # cell.yaml line 165; Decision record item 8
CALIBRATION_SLICE_SEED = 48260720        # cell.yaml/gates.yaml calibration_slice; Decision record item 8
CALIBRATION_SLICE_ROWS_TOTAL = 100       # cell.yaml line 131
CALIBRATION_SLICE_PER_RUNG = 25          # cell.yaml line 131 ("stratified 25 per new rung")

DESIGN_INFO_P_BOUND_GE_FLOOR_EMPIRICAL = 0.6727   # cell.yaml line 168; Decision record item 9
DESIGN_INFO_P_BOUND_GE_FLOOR_PROBIT = 0.5311      # cell.yaml line 169; Decision record item 9

# ---------------------------------------------------------------------------
# Cross-worktree / cross-experiment source roots (committed in THIS repo's
# git history; not ephemeral ehr-worktrees paths).
# ---------------------------------------------------------------------------
M1_DIR = REPO_ROOT / "experiments" / "margin-mapping"
DOUBT_SNAP_DIR = REPO_ROOT / "experiments" / "qwen35-4b-midband-doubt-snap"

# ---------------------------------------------------------------------------
# Pinned inputs. The first six match experiment.yaml's `inputs:` list plus
# the c_hat direction (cell.yaml `directions_source`) -- these seven sha256
# values are all restated explicitly in cell.yaml's own text EXCEPT the
# c_hat direction's hex digest, which cell.yaml's prose does not restate
# (only the path/provenance: "M1 staged c_hat ... reused byte-identically
# ... sha256 verified at staging (SC0)"). That digest is transcribed here
# from M1's OWN committed staging_manifest.json entry `qwen_hs20_c_hat`
# (experiments/margin-mapping/analysis-committed/staging_manifest.json) --
# FLAGGED as a build-time interpretation in the harness-build report, not a
# cell.yaml-literal value.
#
# `question_pool` is an EIGHTH staged item, needed to render any prompt at
# all, and is NOT named among cell.yaml's/experiment.yaml's pins at all.
# This mirrors M1's OWN precedent exactly: M1's staging.py docstring
# describes the identical gap ("qwen_heldout_rows_for_steer ... not itself
# named in `directions_source`/`baseline_runlog` fields ... a staging-scope
# call, not a spec value") and stages it anyway, verified against the
# factorial's manifest. M1b carries that SAME convention forward one level:
# this entry is verified against M1's OWN committed staging_manifest.json
# `qwen_heldout_rows_for_steer` entry. FLAGGED in the harness-build report.
# ---------------------------------------------------------------------------
PINNED_INPUTS: dict[str, dict[str, object]] = {
    "subsample_ids": {
        "path": M1_DIR / "analysis-committed" / "subsample_ids_qwen35_4b.json",
        "sha256": "60d5a3e13de5f85d35776dcee3c15dddea2e301951ded42849516865fe32723d",
        "dest": "qwen35_4b/subsample_ids_qwen35_4b.json",
        "cell_yaml_pin": True,
    },
    "margin_dataset": {
        "path": M1_DIR / "analysis" / "margin_dataset" / "qwen35_4b_margin_rows.jsonl",
        "sha256": "84f4d3b8674a18eb944a4b921383e1cfb1147db892dee2c19348f671b7f41565",
        "dest": "qwen35_4b/qwen35_4b_margin_rows.jsonl",
        "cell_yaml_pin": True,
    },
    "rung_0p5": {
        "path": M1_DIR / "analysis" / "runlog" / "qwen35_4b__rung_0p5.jsonl",
        "sha256": "7bccb26ad3c02f586ca03fb426a7cf4489c892d4116d4f49db550f4ff96a42fd",
        "dest": "qwen35_4b/runlog/qwen35_4b__rung_0p5.jsonl",
        "cell_yaml_pin": True,
    },
    "rung_0p75": {
        "path": M1_DIR / "analysis" / "runlog" / "qwen35_4b__rung_0p75.jsonl",
        "sha256": "512a33d0bd984cd5659f0554673357aef4397f42a785c8ca8c0ad730463154f6",
        "dest": "qwen35_4b/runlog/qwen35_4b__rung_0p75.jsonl",
        "cell_yaml_pin": True,
    },
    "rung_1p5": {
        "path": M1_DIR / "analysis" / "runlog" / "qwen35_4b__rung_1p5.jsonl",
        "sha256": "c9382f8822533f13c41778c82c270c0bf5d5b5c0ceaf02a0980814fd627b3450",
        "dest": "qwen35_4b/runlog/qwen35_4b__rung_1p5.jsonl",
        "cell_yaml_pin": True,
    },
    "rung_2p0": {
        "path": M1_DIR / "analysis" / "runlog" / "qwen35_4b__rung_2.jsonl",
        "sha256": "b91ebb43900ed1c8db26e19ee584995a3a3210670619df0ff67217ec66842fa1",
        "dest": "qwen35_4b/runlog/qwen35_4b__rung_2.jsonl",
        "cell_yaml_pin": True,
    },
    "c_hat_direction": {
        "path": DOUBT_SNAP_DIR / "analysis-committed" / "directions" / "hs20" / "c_hat.json",
        "sha256": "937d1bffe1924e73bca40a88c8096d7e01bb67c5b64286362196aa968e2c2e1f",
        "dest": "qwen35_4b/directions/hs20_c_hat.json",
        "cell_yaml_pin": False,  # path/provenance named in cell.yaml prose; hex digest transcribed from M1's own manifest
    },
    "question_pool": {
        "path": M1_DIR / "analysis" / "staged_inputs" / "qwen35_4b" / "heldout_rows_for_steer.jsonl",
        "sha256": "76097bf7046cefa673280110a5d3b83aeaf0affbc98dc73078ecdec9785d178b",
        "dest": "qwen35_4b/heldout_rows_for_steer.jsonl",
        "cell_yaml_pin": False,  # not named anywhere in cell.yaml/experiment.yaml; M1-precedent convention (see module docstring)
    },
}


def _sha256_of_file(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def verify_pinned_hashes() -> dict[str, bool]:
    """cell.yaml/gates.yaml sha256 must match experiment.yaml's pins."""
    return {
        "cell_yaml": _sha256_of_file(CELL_YAML_PATH) == CELL_YAML_SHA256_PINNED,
        "gates_yaml": _sha256_of_file(GATES_YAML_PATH) == GATES_YAML_SHA256_PINNED,
    }
