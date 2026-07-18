"""Locked registered constants for margin-evidence-responsiveness-worldknown
(M4-WK).

Every numeric/string constant below is transcribed LITERALLY from the signed
`cell.yaml` / `gates.yaml` / `AMENDMENT.md` (all three read in full before
writing this), following the `margin-mapping/harness/config.py` /
`susceptibility-as-probe/harness/config.py` convention: values are hardcoded
here (not read from a live YAML parse at import time) so the harness's
behavior is reviewable from this file alone and cannot silently drift if the
locked YAML is edited without a re-sign. `verify_pinned_hashes()` re-checks
cell.yaml/gates.yaml sha256 against the experiment.yaml pins; every entry
script calls it before doing anything else.
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

# experiment.yaml instrument.pins
CELL_YAML_SHA256_PINNED = "d43fdc2a5ff369173e9bf7825ec3b70d3d39caebe79ec5b91815ce67a7931486"  # repinned to extend ladder multipliers (bracketing re-derivation, PI approval 2026-07-18), see instrument.repins
GATES_YAML_SHA256_PINNED = "cd78e84a95eb777f0bcee73c2cfee57c071628dc7a49112be88e3385c8985909"  # repinned to freeze native d2_absolute_floor at n=51 (transfer void, not frozen), see instrument.repins

# ---------------------------------------------------------------------------
# Family and frozen operating point (cell.yaml `families`, qwen only)
# ---------------------------------------------------------------------------
FAMILY = "qwen35_4b"
MODEL_REPO = "Qwen/Qwen3.5-4B"
MODEL_REVISION = "851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a"
HIDDEN_DIM = 2560
LAYER_HS_INDEX = 20          # cell.yaml families.qwen35_4b.layer_hs_index
DECODER_BLOCK_INDEX = 19     # hs_index - 1 (project convention)

# ---------------------------------------------------------------------------
# Directions (cell.yaml `directions`)
# ---------------------------------------------------------------------------
TRANSFER_C_HAT_PATH = REPO_ROOT / "experiments/qwen35-4b-midband-doubt-snap/analysis-committed/directions/hs20/c_hat.json"
TRANSFER_C_HAT_SHA256_PINNED = "937d1bffe1924e73bca40a88c8096d7e01bb67c5b64286362196aa968e2c2e1f"
TRANSFER_LAYER_INDEX = 19
TRANSFER_HS_INDEX = 20
TRANSFER_REFERENCE_DOSE_ABS = 12.608187917799976       # cell.yaml directions.transfer.reference_dose_abs
TRANSFER_MU_C = -4.031343053353048
TRANSFER_SIGMA_C = 1.576023489724997

NATIVE_C_HAT_PATH = EXPERIMENT_DIR / "analysis-committed" / "directions" / "hs20" / "c_hat_worldknown.json"
NATIVE_LAYER_INDEX = 19
NATIVE_HS_INDEX = 20
NATIVE_REFERENCE_DOSE_MULTIPLIER = 8.0   # fork 1: SAME 8x multiplier that set the KUQ (transfer) reference dose

DIRECTIONS = ("transfer", "native")

# ---------------------------------------------------------------------------
# Readout (cell.yaml `readout`) -- sign pinned in code, per direction.
# Registered score = NEGATIVE z-projection (confab-positive orientation).
# TRANSFER sign is empirically known from M2 (raw proj is confab-negative).
# NATIVE sign requires the build-time assertion (MINOR m2) before use.
# ---------------------------------------------------------------------------
READOUT_SIGN = {"transfer": -1.0, "native": -1.0}
READOUT_ADD_SPECIAL_TOKENS = True
READOUT_PERSIST_DTYPE = "float32"
READOUT_ENGINE = "hf-batched"
READOUT_CAPTURE_BATCH_SIZE = 8

# ---------------------------------------------------------------------------
# Population (cell.yaml `population`)
# ---------------------------------------------------------------------------
POPQA_PATH = REPO_ROOT / "datasets" / "popqa" / "test.jsonl"
POPQA_N_ROWS = 14267
POPQA_GOLD_FIELD = "obj"
POPQA_ALIASES_FIELD = "possible_answers"
POPQA_CATEGORY_FIELD = "prop"

NATIVE_FIT_SPLIT_TARGETS = {"confab": 400, "correct": 240, "refused": 180}
TEST_CONFAB_N = 400
TEST_CORRECT_N = 360

SELECTION_PERMUTATION_SEED = 48260727     # native-fit / test split permutation
DISTRACTOR_PERMUTATION_SEED = 48260725    # category-matched false-answer distractor
CALIBRATION_SLICE_SEED = 48260726         # blinded correctness + abstention calibration
BOOTSTRAP_SEED = 48260724                 # bootstrap (channel-1 shifts, channel-2 survival, all CIs)

# ---------------------------------------------------------------------------
# Arms (cell.yaml `arms`)
# ---------------------------------------------------------------------------
ARMS = ("no_answer_baseline", "true_answer", "false_answer_placebo")

# ---------------------------------------------------------------------------
# Generation (byte-identical carried pins from M1/M4 lineage)
# ---------------------------------------------------------------------------
GEN_DO_SAMPLE = False
GEN_MAX_NEW_TOKENS = 200
GEN_ENABLE_THINKING = False
CENSUS_BATCH_SIZE = 8
LADDER_BATCH_SIZE = 4
SURVIVAL_BATCH_SIZE = 4

# ---------------------------------------------------------------------------
# Channel 1: projection collapse
# ---------------------------------------------------------------------------
TRANSFER_FIRING_AUROC_FLOOR = 0.70   # BLOCKER B1 / S1; LOCKED at sign
NATIVE_AUROC_REPRODUCTION_TOLERANCE = 0.05

COLLAPSE_FLOOR_FRACTION = 0.5   # carried (M4 decision record item 1); numeric frozen at repin

# ---------------------------------------------------------------------------
# Channel 2: margin lengthening
# ---------------------------------------------------------------------------
LADDER_MULTIPLIERS = (0.0625, 0.125, 0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0, 4.0, 6.0, 8.0, 12.0, 16.0)  # extended (repin, PI approval 2026-07-18): see cell.yaml channel2_margin.ladder_rebuild.multipliers
WRITE_LAW = "erase_write"
WRITE_POSITION = "anchor_onward"

BASELINE_STALENESS_CEILING = 0.05   # channel-2 S1: no_answer_baseline survival must be <= this

# D2 absolute floor formula: 1.96 * sqrt(0.25 / n_margin_eligible); numeric frozen at repin
D2_WALD_Z = 1.959963984540054

# ---------------------------------------------------------------------------
# SC1 dose readback (M1's amended rule, carried verbatim)
# ---------------------------------------------------------------------------
READBACK_TOLERANCE_REL = 0.005
READBACK_TOLERANCE_ABS_FRAC_OF_REF = 0.005

# ---------------------------------------------------------------------------
# Preflight
# ---------------------------------------------------------------------------
PREFLIGHT_CAPTURE_SMOKE_ROWS = 8
PREFLIGHT_GENERATION_SMOKE_ROWS = 8
PREFLIGHT_PASS_MARKER = "analysis/preflight/PASS.json"  # relative to EXPERIMENT_DIR

# ---------------------------------------------------------------------------
# SC2 blinded calibration
# ---------------------------------------------------------------------------
CORRECTNESS_CALIBRATION_MIN_N = 150
CORRECTNESS_CALIBRATION_FALSE_WRONG_NULL_INTERPRETABLE_MAX = 0.10
CG1_CLEAR_NEGATIVE_AGREEMENT_MIN = 0.95
CG1_CLEAR_POSITIVE_AGREEMENT_MIN = 0.60
CG1_CLEAR_POSITIVE_DECOYS_MIN = 25
DETECTOR_ADJUDICATION_DISAGREEMENT_MAX = 0.05

# ---------------------------------------------------------------------------
# Statistics (gates.yaml `statistics`)
# ---------------------------------------------------------------------------
BOOTSTRAP_N_RESAMPLES = 10000
BOOTSTRAP_CI = 0.95


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


def assert_pinned_hashes() -> None:
    hashes = verify_pinned_hashes()
    if not all(hashes.values()):
        raise SystemExit(f"config FAIL: cell.yaml/gates.yaml sha256 mismatch vs experiment.yaml pins: {hashes}")
