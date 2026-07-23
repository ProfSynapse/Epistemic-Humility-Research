"""Locked registered constants for evidence-response-direction-search (M4c).

Every numeric/string constant below is transcribed LITERALLY from the signed
`cell.yaml` / `gates.yaml` / `AMENDMENT.md` (all three read in full before
writing this), following the M4-WK / M1 / susceptibility-as-probe
`harness/config.py` convention: values are hardcoded here (not read from a
live YAML parse at import time) so the harness's behavior is reviewable from
this file alone and cannot silently drift if the locked YAML is edited
without a re-sign. `assert_pinned_hashes()` re-checks cell.yaml/gates.yaml
sha256 against experiment.yaml's pins; every entry script calls it before
doing anything else.

CPU rungs only (a, c, KUQ transfer). Rung (b) is GPU, conditional, and out of
scope for this harness -- no code here launches a model or touches a GPU.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXPERIMENT_DIR = HERE.parent
EXPERIMENTS_DIR = EXPERIMENT_DIR.parent
REPO_ROOT = EXPERIMENTS_DIR.parent

CELL_YAML_PATH = EXPERIMENT_DIR / "cell.yaml"
GATES_YAML_PATH = EXPERIMENT_DIR / "gates.yaml"
EXPERIMENT_YAML_PATH = EXPERIMENT_DIR / "experiment.yaml"

# experiment.yaml instrument.pins (signed 2026-07-18, HEAD 7b38e72c)
CELL_YAML_SHA256_PINNED = "c060fd9b2a29e826246bc1fce5de8dbd3c6c20ca7a934468e9c286d171a35049"
GATES_YAML_SHA256_PINNED = "9038b6a85533d1c2c749f6f30e3a661f4201afe4aee2c54d9a3a1c4b7ac3bd7b"

# ---------------------------------------------------------------------------
# Substrate (cell.yaml `substrate`) -- record-only; this harness never loads
# the model or runs a forward pass. All hidden states are reused verbatim.
# ---------------------------------------------------------------------------
MODEL_REPO = "Qwen/Qwen3.5-4B"
MODEL_REVISION = "851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a"
HIDDEN_DIM = 2560
HS_INDEX = 20           # hs20 anchor
LAYER_INDEX = 19        # decoder-block index (hs_index - 1); mirrors
                         # c_hat_worldknown.json's "layer" field convention

# ---------------------------------------------------------------------------
# Reused M4-WK channel-1 captures (cell.yaml `population`). Physical location
# is the retained M4-WK worktree (gitignored path there; never committed).
# ---------------------------------------------------------------------------
CAPTURE_SOURCE_DIR = Path(
    "/home/profsynapse/code/ehr-worktrees/m4-worldknown/experiments/"
    "margin-evidence-responsiveness-worldknown/analysis/channel1_capture"
)
ARMS = ("no_answer_baseline", "true_answer", "false_answer_placebo")
ANCHOR_TENSOR_KEY = "anchor__L20"

ROLE_CONFAB = "confab"
ROLE_CORRECT = "correct_on_answerable"
ROLE_REFUSED = "refused_on_answerable"
ROLE_COMPOSITION_EXPECTED = {ROLE_CONFAB: 400, ROLE_CORRECT: 360, ROLE_REFUSED: 241}
N_ROWS_PER_ARM = 1001

# test_population.json (M4-WK, seed 48260727), committed in THIS repo tree
# (main merged M4-WK PR #306; present in this worktree at HEAD).
TEST_POPULATION_PATH = (
    EXPERIMENTS_DIR / "margin-evidence-responsiveness-worldknown"
    / "analysis-committed" / "selection" / "test_population.json"
)
TEST_POPULATION_SHA256_PINNED = "69c68d91f5024958ca77ac6f5dc1c92c8deb1e544b38c7ada59c72c3f629feba"

# ---------------------------------------------------------------------------
# Comparator directions (cell.yaml `readouts.rung_c_primary_companion`)
# ---------------------------------------------------------------------------
C_HAT_WORLDKNOWN_PATH = (
    EXPERIMENTS_DIR / "margin-evidence-responsiveness-worldknown"
    / "analysis-committed" / "directions" / "hs20" / "c_hat_worldknown.json"
)
C_HAT_WORLDKNOWN_SHA256_PINNED = "432c9f1f2753ed9d68f9da99705ae2955396e6eb0ec38e9ca2fbc5a40963176c"
C_HAT_WORLDKNOWN_BASELINE_AUROC_REFERENCE = 0.86275  # full-test-population anchor only (m-4); NOT recomputed here

KUQ_CHAT_PATH = (
    EXPERIMENTS_DIR / "qwen35-4b-midband-doubt-snap"
    / "analysis-committed" / "directions" / "hs20" / "c_hat.json"
)
KUQ_CHAT_SHA256_PINNED = "937d1bffe1924e73bca40a88c8096d7e01bb67c5b64286362196aa968e2c2e1f"
KUQ_CHAT_BASELINE_AUROC_REFERENCE = 0.3018  # AMENDMENT-cited reference on this population; reported, not recomputed for the lower comparator

# ---------------------------------------------------------------------------
# KUQ transfer readout (cell.yaml `readouts.kuq_transfer_ungated`). Physical
# location is the doubt-snap experiment's gitignored analysis/ dir; only
# present in the canonical checkout (never committed by that experiment).
# ---------------------------------------------------------------------------
KUQ_ANCHOR_EXTRACT_PATH = Path(
    "/home/profsynapse/code/Epistemic-Humility-Research/experiments/"
    "qwen35-4b-midband-doubt-snap/analysis/anchor_extract.safetensors"
)
KUQ_ANCHOR_MANIFEST_PATH = Path(
    "/home/profsynapse/code/Epistemic-Humility-Research/experiments/"
    "qwen35-4b-midband-doubt-snap/analysis/anchor_extract_manifest.json"
)
KUQ_FIT_ROWS_PATH = Path(
    "/home/profsynapse/code/Epistemic-Humility-Research/experiments/"
    "qwen35-4b-midband-doubt-snap/analysis/fit_rows_for_anchor.jsonl"
)
KUQ_ANCHOR_HS_KEY_PREFIX = "hs20__"
KUQ_ROLE_CONFAB = "confab"
KUQ_ROLE_CORRECT = "known_correct_answered"

# ---------------------------------------------------------------------------
# Fit / held-out split (cell.yaml `fit.split`, byte-pinned routine)
# ---------------------------------------------------------------------------
SPLIT_SEED = 48260728
N_FIT = 200
N_HELD_OUT = 200

# ---------------------------------------------------------------------------
# Seeds (cell.yaml `seeds`; extends the 4826072x series)
# ---------------------------------------------------------------------------
BOOTSTRAP_SEED = 48260724
RANDOM_NULL_SEED = 48260729
N_BOOT = 10000
K_NULL = 1000

# ---------------------------------------------------------------------------
# Criterion floors / bars (gates.yaml `criterion`)
# ---------------------------------------------------------------------------
RUNG_A_AUROC_FLOOR = 0.70                    # D_a, fixed carried numeric; POINT ESTIMATE gates
NATIVE_COMPARATOR_STRONG_BAR_LOWER_CI = -0.05  # D_c STRONG bar: paired AUROC-diff (d_ev - native) lower 95% CI >= this
NULL_PERCENTILE_ALPHA = 0.05                 # D_c: d_ev must exceed the 95th percentile (p < 0.05)

# ---------------------------------------------------------------------------
# Rung (b) reference-dose convention (recorded in d_ev.json for provenance
# completeness / future rung-b funding decision; this harness NEVER runs
# rung (b), never loads the model, never computes a survival contrast).
# ---------------------------------------------------------------------------
REFERENCE_DOSE_MULTIPLIER = 8.0  # 8 x sigma_c, rulings record item 3

# ---------------------------------------------------------------------------
# Containment (AMENDMENT `Containment`, gates.yaml SC0)
# ---------------------------------------------------------------------------
# Committed artifacts carry ONLY aggregates, the direction vector, opaque
# id-lists, and sha256 hashes. NEVER generation/question/answer text or token
# ids in any analysis-committed/ path.


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
