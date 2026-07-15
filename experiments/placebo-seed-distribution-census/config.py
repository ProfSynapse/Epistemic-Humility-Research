"""Locked registered constants for placebo-seed-distribution-census.

BUILD-TIME FINDING (report this to the lead, do not self-repair): as of HEAD
f1c1983a (the SIGNED commit; sha256 of cell.yaml in this worktree matches
experiment.yaml's pinned 593e08d3...), `cell.yaml` does NOT parse as valid
YAML. `yaml.safe_load` raises `ParserError: mapping values are not allowed
here` at line 113 column 118, inside the plain (unquoted) scalar value of
`adjudication.pool_contents`:

    pool_contents: shared_baseline_S_rows + K x S dosed rows (all families in
    one lane or per-family; labels stripped: arm, dose, seed, role, source)

The colon after "labels stripped" inside that unquoted scalar is parsed by
PyYAML as a nested mapping key, which is invalid inside a plain scalar. This
predates this harness build (present at the signed HEAD; not introduced by
any edit made during this build) and mirrors the EXACT same class of defect
`rr3-corrected-placebo-replication/cell.yaml` shipped with at ITS harness
build (that experiment's `test_rr3_smoke.py` module docstring documents a
different but analogous PyYAML ParserError at its own line 134, also
"reported as the primary STOP item for the lead; the harness is not being
self-repaired against a locked spec file"). Following that established
precedent exactly: this harness does NOT edit cell.yaml (it is hash-pinned in
experiment.yaml and locked), does NOT programmatically `yaml.safe_load` it at
runtime anywhere, and instead hardcodes every registered value below as a
Python constant with an inline citation to the cell.yaml/AMENDMENT.md line(s)
it was read from -- the SAME pattern already used throughout this repo's prior
harnesses (e.g. `rr3-corrected-placebo-replication/materialize_rows.py`'s
`resolve_revision` reads the fleet's own `model_matrix.yaml` rather than
cell.yaml for revision pins; `placebo-signflip-question-type-analysis/
staging.py` hardcodes every source path as a Python dict rather than parsing
its own cell.yaml). gates.yaml (a SEPARATE file, sha256 2d0c069e... matching
its own experiment.yaml pin) DOES parse as valid YAML and IS loaded
programmatically by `gates_lib.py`/`sc1_checks.py` where useful.

Every numeric value below is transcribed verbatim from the signed
`AMENDMENT.md` / `cell.yaml` text (both read in full by this harness's
author) and cross-checked against on-disk artifacts where noted.
"""

from __future__ import annotations

from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[1]

# ---------------------------------------------------------------------------
# Cross-worktree source roots (this MACHINE's local worktree layout; see
# `git worktree list`). Mirrors placebo-signflip-question-type-analysis/
# staging.py's own _WT convention.
# ---------------------------------------------------------------------------
_WT = Path("/home/profsynapse/code/ehr-worktrees")
QH_WT = _WT / "qwen35-midband-heldout" / "experiments" / "qwen35-4b-midband-heldout"
RR2_WT = _WT / "rr2-mistral-confirm" / "experiments" / "rr2-mistral-adjudicated-refusal-confirm"
RR_WT = _WT / "rr-raw-refusal" / "experiments" / "rr-cross-family-raw-refusal"
RR3_WT = _WT / "rr3-corrected-placebo" / "experiments" / "rr3-corrected-placebo-replication"

# Committed-in-THIS-worktree sources (no staging/symlink needed).
DOUBT_SNAP_DIR = HERE.parent / "qwen35-4b-midband-doubt-snap"
RR_LOCAL_DIR = HERE.parent / "rr-cross-family-raw-refusal"

# ---------------------------------------------------------------------------
# Families and fixed matched-magnitude operating points
# (cell.yaml `families` block, lines 30-67; AMENDMENT.md "Design" table)
# ---------------------------------------------------------------------------

FAMILIES = ("qwen35_4b", "mistral7b_v03", "llama32_3b")

LAYER_HS_INDEX = {
    "qwen35_4b": 20,        # cell.yaml line 34
    "mistral7b_v03": 16,    # cell.yaml line 45 (decoder block 15)
    "llama32_3b": 20,       # cell.yaml line 60 (most potent llama atlas layer)
}

# qwen: confirmed at sign -- absolute setpoint, no sigma_c multiplier asserted
# (cell.yaml line 35-36; AMENDMENT.md lines 89-95).
QWEN_SETPOINT_DOSE_ABS = 12.608187917799976

# mistral: 12 x sigma_c(hs16 mistral) = 3.6653166050691756 (cell.yaml line 46-47;
# cross-checked against RR's own committed hs16_fit_build_manifest.json,
# sigma_c=0.3054430504224313, 12*0.3054430504224313=3.665316605069176, matches
# to float precision -- see llama_setpoint_provenance.py for the analogous
# llama derivation and its committed crosscheck note).
MISTRAL_SETPOINT_DOSE_ABS = 3.6653166050691756
MISTRAL_DOSE_MULTIPLIER_SIGMA_C = 12

# llama: TO-DERIVE at cell.yaml sign time (line 61); derived by this harness's
# llama_setpoint_provenance.py from RR's own committed
# rr-cross-family-raw-refusal/analysis-committed/llama/hs20_fit_build_manifest.json
# (sigma_c=1.1261957002181966, COMMITTED IN THIS WORKTREE, no staging needed)
# cross-checked against rr3-corrected-placebo-replication's own independent
# RG0 reconstruction of the SAME fit (gitignored in the rr3-corrected-placebo
# worktree; fit_reuse_report.json field-for-field match, pass=true,
# mismatches={}). See llama_setpoint_provenance.py for the executable
# crosscheck and the committed provenance note it writes.
LLAMA_DOSE_MULTIPLIER_SIGMA_C = 12
LLAMA_SIGMA_C_HS20 = 1.1261957002181966
LLAMA_SETPOINT_DOSE_ABS = LLAMA_DOSE_MULTIPLIER_SIGMA_C * LLAMA_SIGMA_C_HS20  # 13.514348402618359

SETPOINT_DOSE_ABS = {
    "qwen35_4b": QWEN_SETPOINT_DOSE_ABS,
    "mistral7b_v03": MISTRAL_SETPOINT_DOSE_ABS,
    "llama32_3b": LLAMA_SETPOINT_DOSE_ABS,
}

PAIRED_CONFAB_POOL_N = {
    "qwen35_4b": 1286,       # cell.yaml line 37 (calibration QH paired n)
    "mistral7b_v03": 1312,   # cell.yaml line 48 (RR2/MC paired n)
    "llama32_3b": 872,       # cell.yaml line 63 (RR3 cell.yaml line 164, held-out confab)
}

HISTORICAL_SINGLE_SEED_DELTA_PTS = {
    "qwen35_4b": -5.13,      # cell.yaml line 40; suppression
    "mistral7b_v03": 7.39,   # cell.yaml line 51; recruitment
    "llama32_3b": 0.1,       # cell.yaml line 66; null
}

COMMITTED_SIGN = {
    "qwen35_4b": "negative",
    "mistral7b_v03": "positive",
    "llama32_3b": "none",    # null / negative-control family; no sign to defend
}

FAMILIES_WITH_COMMITTED_SIGN = ("qwen35_4b", "mistral7b_v03")  # gates.yaml sc_criterion.applies_to_families_with_committed_sign

# baseline_runlog per family (cell.yaml lines 38, 49, 64), resolved to
# absolute cross-worktree paths on THIS machine.
BASELINE_RUNLOG = {
    "qwen35_4b": QH_WT / "analysis" / "runlog" / "baseline.jsonl",
    "mistral7b_v03": RR2_WT / "analysis" / "runlog" / "heldout__baseline.jsonl",
    # DEVIATION (report straight, not silently resolved): cell.yaml line 64
    # names "rr-cross-family-raw-refusal (llama32_3b_instruct cell) baseline"
    # as the llama baseline source. NO such wide-instrument baseline runlog
    # exists anywhere under rr-cross-family-raw-refusal on this machine (RR's
    # own llama cell never ran a baseline pass under this generation contract;
    # llama had no gated arm, RR3 cell.yaml itself notes "llama has NO viable
    # gated operating point"). The only baseline text actually generated for
    # llama at this exact contract (greedy, min_new_tokens=1, max_new_tokens=
    # 200, eos enabled, enable_thinking=false) is
    # rr3-corrected-placebo-replication's OWN rider_llama__baseline.jsonl
    # (1206 rows, both populations, gitignored in the rr3-corrected-placebo
    # worktree). This harness reuses THAT file as "the family's committed
    # baseline runlog" for SC0's byte-repro check and the census's baseline
    # reuse, flagged here and in the final report for the lead's review.
    "llama32_3b": RR3_WT / "analysis" / "runlog" / "rider_llama__baseline.jsonl",
}

# directions_dir per family (cell.yaml lines 39, 50, 65).
DIRECTIONS_DIR = {
    "qwen35_4b": DOUBT_SNAP_DIR / "analysis-committed" / "directions" / "hs20",  # COMMITTED in this worktree
    # RR2's OWN original hs16 reconstruction (gitignored, present in the
    # rr2-mistral-confirm worktree that generated it; cell.yaml line 50 names
    # this exact directory).
    "mistral7b_v03": RR2_WT / "directions",
    # llama: cell.yaml line 65 says "TO-PIN"; this harness pins it to
    # rr3-corrected-placebo-replication's OWN gitignored directions/ dir,
    # which holds byte-identical-to-RR's-committed-manifest reconstructed
    # llama_hs20_{c_hat,u_d,random_direction,build_manifest}.json (see
    # llama_setpoint_provenance.py). Reused rather than re-run because the
    # reconstruction is a deterministic pure function of (RR's committed FIT
    # rows/anchors, RR's own fit seed 20260713) and RR3's own fit_reuse.py
    # already ran it twice and asserted byte-identical, then cross-checked
    # field-for-field against RR's committed manifest (pass=true).
    "llama32_3b": RR3_WT / "directions",
}

# ---------------------------------------------------------------------------
# Census sampling knobs (cell.yaml `census` block, lines 72-83)
# ---------------------------------------------------------------------------

K_SEEDS_PER_FAMILY = 15  # cell.yaml line 73

SEED_BLOCKS = {
    "qwen35_4b": list(range(41000001, 41000016)),      # cell.yaml line 75
    "mistral7b_v03": list(range(42000001, 42000016)),  # cell.yaml line 76
    "llama32_3b": list(range(43000001, 43000016)),      # cell.yaml line 77
}

SUBSAMPLE_ROWS_PER_FAMILY = 300       # cell.yaml line 79
SUBSAMPLE_PERMUTATION_SEED = 40260714  # cell.yaml line 80
SUBSAMPLE_POPULATION = "confab"        # cell.yaml line 81

GENERATION_SCOPE = "subsample_only"    # cell.yaml line 83

# ---------------------------------------------------------------------------
# Matched-magnitude write + generation contract (cell.yaml `write` block,
# lines 88-100)
# ---------------------------------------------------------------------------

WRITE_LAW = "erase_write"
WRITE_POSITION = "anchor_onward"
READBACK_TOLERANCE_REL = 0.005    # SC1; |readback - target| / target <= 0.005 (corrected pre-run 2026-07-14, user-approved; gates.yaml sc1 note)
RANDOMNESS_BAR_COS = 0.015        # SC1; cell.yaml line 94

GEN_DO_SAMPLE = False
GEN_MIN_NEW_TOKENS = 1
GEN_MAX_NEW_TOKENS = 200
GEN_EOS_ENABLED = True
GEN_ENABLE_THINKING = False

# ---------------------------------------------------------------------------
# Model identities (fleet model_matrix.yaml is the live source of truth per
# this repo's resolve_revision discipline; these are the cell_ids used to
# look them up, matching rr3-corrected-placebo-replication/materialize_rows.py
# FAMILY_TO_CELL_ID and rider_llama_placebo_ladder's model/revision pins).
# ---------------------------------------------------------------------------

FLEET_DIR = REPO_ROOT / "experiments" / "doubt-snap-cross-family-confirmatory"

FAMILY_TO_CELL_ID = {
    "qwen35_4b": "qwen35_4b",          # model_matrix.yaml cell_id (verified: grep 'cell_id' doubt-snap-cross-family-confirmatory/model_matrix.yaml)
    "mistral7b_v03": "mistral7b_instruct_v03",
    "llama32_3b": "llama32_3b_instruct",
}

# Fallback pins (used only if a cell_id is not found in the fleet's live
# model_matrix.yaml; resolve_revision always prefers the live fleet file and
# raises loudly on a mismatch, mirroring RR3's own discipline).
FAMILY_TO_MODEL_FALLBACK = {
    "mistral7b_v03": ("mistralai/Mistral-7B-Instruct-v0.3", "c170c708c41dac9275d15a8fff4eca08d52bab71"),
    "llama32_3b": ("unsloth/Llama-3.2-3B-Instruct", "006f5dcd1393c3add266de40994ba96225e9689d"),
}

# ---------------------------------------------------------------------------
# Criterion constants (gates.yaml sc_criterion, lines 74-92)
# ---------------------------------------------------------------------------

CRITERION_MAGNITUDE_FLOOR_PTS = 3.0
CRITERION_F_S_SURVIVE_FLOOR = 0.80
CRITERION_F_S_SURVIVE_BOOTSTRAP_LCB_FLOOR = 0.50
CRITERION_F_S_RETIRE_CEIL = 0.60
