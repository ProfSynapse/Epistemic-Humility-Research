"""Locked registered constants for susceptibility-as-probe (M2).

Every numeric/string constant below is transcribed LITERALLY from the signed
`cell.yaml` / `gates.yaml` / `AMENDMENT.md` (all three read in full before
writing this), following the `margin-mapping/harness/config.py` convention:
values are hardcoded here (not read from a live YAML parse at import time) so
the harness's behavior is reviewable from this file alone and cannot silently
drift if the locked YAML is edited without a re-sign. `verify_pinned_hashes()`
below re-checks cell.yaml/gates.yaml sha256 against the experiment.yaml pins
every time this module is imported by a run script.
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

# experiment.yaml instrument.pins (verified against a fresh sha256 of both
# files before any staging/capture/analysis step runs).
CELL_YAML_SHA256_PINNED = "d361224f2f800e28e7b10a10ee6bbc57c28c8a1241a90f9fd1ffd42be8c5a7cd"
GATES_YAML_SHA256_PINNED = "a19da59d4a9d232389724f5e99332ce874d45cd71ad6a4f1455f3486badaab54"

# ---------------------------------------------------------------------------
# Model (cell.yaml `model`)
# ---------------------------------------------------------------------------
FAMILY = "qwen35_4b"
MODEL_REPO = "Qwen/Qwen3.5-4B"
MODEL_REVISION = "851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a"

# ---------------------------------------------------------------------------
# Population (cell.yaml `population`)
# ---------------------------------------------------------------------------
N_CONFAB = 400
N_KNOWN = 360
N_POPULATION = N_CONFAB + N_KNOWN  # 760

SUBSAMPLE_IDS_PATH = REPO_ROOT / "experiments/margin-mapping/analysis-committed/subsample_ids_qwen35_4b.json"
SUBSAMPLE_IDS_SHA256_PINNED = "60d5a3e13de5f85d35776dcee3c15dddea2e301951ded42849516865fe32723d"

MARGIN_DATASET_PATH = REPO_ROOT / "experiments/margin-mapping/analysis/margin_dataset/qwen35_4b_margin_rows.jsonl"
MARGIN_DATASET_SHA256_PINNED = "84f4d3b8674a18eb944a4b921383e1cfb1147db892dee2c19348f671b7f41565"

SPLIT_MANIFEST_PATH = REPO_ROOT / "experiments/doubt-snap-cross-family-confirmatory/analysis-committed/qwen35_4b/split_manifest.json"
SPLIT_MANIFEST_SHA256_PINNED = "2f622f5abe110349216207424bdbd919775e93f6d92f334b99f6424505f21e5c"

C_HAT_PATH = REPO_ROOT / "experiments/qwen35-4b-midband-doubt-snap/analysis-committed/directions/hs20/c_hat.json"
C_HAT_SHA256_PINNED = "937d1bffe1924e73bca40a88c8096d7e01bb67c5b64286362196aa968e2c2e1f"

# FIT split values: every row that participated in fitting u_d / u_p /
# caution / c_hat (fit_directions() in
# doubt-snap-cross-family-confirmatory/prep_tuner_cell.py uses confab_fit +
# known_fit for h_fit/proj_c, and unknown + confab_fit for the caution/u_p
# fit) -- i.e. every row NOT split=="held_out". Verified on disk: ('confab',
# 'fit')=887, ('known_correct_answered','fit')=240, ('unknown_refused',
# 'fit_only')=181; 887+240=1127 matches build_manifest.json's
# n_confab_fit/n_known_fit exactly.
FIT_SPLIT_VALUES = ("fit", "fit_only")

# Auxiliary (unpinned) question-text source: not one of the four SC0-pinned
# inputs, but a hard prerequisite to render any row at all. Reused read-only
# from margin-mapping's own gitignored analysis/ (M1 already staged this
# byte-identically from the qwen35-midband-heldout worktree at build time).
HELDOUT_ROWS_FOR_STEER_PATH = REPO_ROOT / "experiments/margin-mapping/analysis/staged_inputs/qwen35_4b/heldout_rows_for_steer.jsonl"

# ---------------------------------------------------------------------------
# Readout channel (cell.yaml `channels.readout`)
# ---------------------------------------------------------------------------
READOUT_LAYER_INDEX = 19   # decoder block index (hs_index - 1)
READOUT_HS_INDEX = 20      # hidden_states[] index; capture key "anchor__L20"
READOUT_HIDDEN_DIM = 2560
READOUT_BATCH_SIZE = 8
READOUT_PERSIST_DTYPE = "float32"
READOUT_ENGINE = "hf-batched"
READOUT_ADD_SPECIAL_TOKENS = True

# ---------------------------------------------------------------------------
# Verbalized-confidence channel (cell.yaml `channels.verbalized_confidence`)
# ---------------------------------------------------------------------------
CONFIDENCE_TEMPLATE_USER_SUFFIX = (
    'Before answering, output your confidence that you can answer this '
    'question correctly as the first line, in exactly this format '
    '"CONFIDENCE <integer 0-100>". Then answer the question.'
)
CONFIDENCE_PARSE_LINES = 2  # "first two output lines"
CONFIDENCE_MAX_VALID = 100

# ---------------------------------------------------------------------------
# Preflight (cell.yaml `preflight`; Decision record item 7)
# ---------------------------------------------------------------------------
PREFLIGHT_CAPTURE_SMOKE_ROWS = 8
PREFLIGHT_ELICITATION_SMOKE_ROWS = 8
PREFLIGHT_PASS_MARKER = "analysis/preflight/PASS.json"  # relative to EXPERIMENT_DIR

# ---------------------------------------------------------------------------
# Analysis (cell.yaml `analysis`; gates.yaml `statistics`)
# ---------------------------------------------------------------------------
BOOTSTRAP_N_RESAMPLES = 10000
BOOTSTRAP_CI = 0.95
BOOTSTRAP_SEED = 48260717
CROSS_FIT_N_FOLDS = 5
CROSS_FIT_FOLD_SEED = 48260718

# ---------------------------------------------------------------------------
# Gates / criteria (gates.yaml `criteria`; Decision record items 3, 5, 6)
# ---------------------------------------------------------------------------
P1_INCREMENTAL_AUROC_FLOOR = 0.02
S1_READOUT_SANITY_FLOOR = 0.80
SC2_CONFIDENCE_PARSE_RATE_FLOOR = 0.95


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
