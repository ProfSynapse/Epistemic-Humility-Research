"""Locked registered constants for margin-mapping (M1).

Every numeric constant below is transcribed LITERALLY from the signed
`cell.yaml`/`gates.yaml` (not read via `yaml.safe_load` at import time), the
same convention `gate-contribution-factorial/config.py` uses, so the
harness's behavior is reviewable from this file alone and cannot silently
change if the locked YAML is edited without a re-sign. `verify_against_live_
yaml()` cross-checks a representative subset of these literals against a
live parse of cell.yaml/gates.yaml and is exercised by the smoke suite.

KNOWN ANOMALY (documented, not fixed -- cell.yaml is locked and hash-pinned,
never edited by this harness): `cell.yaml` line 89 (the `disagreement_gate`
value under `readout.calibration_slice`) is a prose string containing an
unquoted "remedy: ..." colon, which breaks `yaml.safe_load` with
`ParserError: mapping values are not allowed here` at line 89 col 113. This
is a genuine authoring bug in the signed file, confirmed present in the
byte-identical, hash-pinned copy (sha256 matches `experiment.yaml`'s pin
exactly -- this is not a staleness or corruption issue, the bug was signed
in). `_load_cell_yaml_permissive()` below works around it by quoting that
one line's value IN MEMORY ONLY before parsing (the on-disk file is never
touched), so this module can still cross-check its literals against a live
parse. `gates.yaml` parses cleanly with no such issue.

Every value is cited to the line(s) it was read from in `cell.yaml`/
`gates.yaml`/`AMENDMENT.md` (all three read in full before writing this).
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXPERIMENT_DIR = HERE.parent
REPO_ROOT = HERE.parents[2]

CELL_YAML_PATH = EXPERIMENT_DIR / "cell.yaml"
GATES_YAML_PATH = EXPERIMENT_DIR / "gates.yaml"
EXPERIMENT_YAML_PATH = EXPERIMENT_DIR / "experiment.yaml"

CELL_YAML_SHA256_PINNED = "476463c6c7153af4fb996f4434df3b6dfd1f8b4a6e36b29b69fe31d580090da4"
GATES_YAML_SHA256_PINNED = "934cacae33965682976db6d64ce88c4ef29158ff26a6677994a3c6fd90cd60d2"  # repinned 2026-07-17 (PI-approved SC1 OR-abs amendment)

# ---------------------------------------------------------------------------
# Cross-worktree source roots (THIS machine's local worktree layout; see
# `git worktree list`). Byte-identical to gate-contribution-factorial's own
# `config.py` roots -- M1 reuses the SAME upstream sources, not copies.
# ---------------------------------------------------------------------------
_WT = Path("/home/profsynapse/code/ehr-worktrees")
QH_WT = _WT / "qwen35-midband-heldout" / "experiments" / "qwen35-4b-midband-heldout"
RR2_WT = _WT / "rr2-mistral-confirm" / "experiments" / "rr2-mistral-adjudicated-refusal-confirm"
DOUBT_SNAP_DIR = REPO_ROOT / "experiments" / "qwen35-4b-midband-doubt-snap"  # committed in THIS worktree's git history

# The factorial's committed staging manifest -- M1's SC0 staging asserts
# every reused artifact's sha256 against THIS file (cell.yaml "byte-identical
# (sha256 verified vs the factorial staging manifest)"). The manifest is
# git-tracked, so it is read from THIS worktree's own checkout; the
# factorial's separate worktree no longer exists (removed 2026-07-17 after
# merge; see NOTEBOOK recovery entry of that date).
FACTORIAL_EXPERIMENT_DIR = REPO_ROOT / "experiments" / "gate-contribution-factorial"
FACTORIAL_STAGING_MANIFEST = FACTORIAL_EXPERIMENT_DIR / "analysis-committed" / "staging_manifest.json"

# ---------------------------------------------------------------------------
# Families and frozen operating points (cell.yaml `families`, lines 23-52)
# ---------------------------------------------------------------------------
FAMILIES = ("qwen35_4b", "mistral7b_v03")

LAYER_HS_INDEX = {"qwen35_4b": 20, "mistral7b_v03": 16}          # cell.yaml lines 30, 45
DECODER_BLOCK_INDEX = {"qwen35_4b": 19, "mistral7b_v03": 15}     # hs_index - 1, factorial convention (config.py DECODER_BLOCK_INDEX)

SUBSTRATE = {
    "qwen35_4b": "Qwen/Qwen3.5-4B",                              # cell.yaml line 26
    "mistral7b_v03": "mistralai/Mistral-7B-Instruct-v0.3",       # cell.yaml line 41
}
REVISION = {
    "qwen35_4b": "851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a",     # cell.yaml line 27
    "mistral7b_v03": "c170c708c41dac9275d15a8fff4eca08d52bab71", # cell.yaml line 42
}

REFERENCE_DOSE_ABS = {
    "qwen35_4b": 12.608187917799976,      # cell.yaml line 32 ("1x" ladder unit)
    "mistral7b_v03": 3.6653166050691756,  # cell.yaml line 47
}

# c_hat write sigma (the direction is calibrated so gain=1.0 corresponds to
# one sigma_c of realized projection). qwen's sigma_c IS restated directly in
# M1's own cell.yaml (`snap_standardization.sigma_c`, line 33). Mistral's is
# NOT restated in M1's cell.yaml (only reference_dose_abs is given, line 47);
# reused byte-identically from gate-contribution-factorial/config.py
# MISTRAL_SIGMA_C, cross-checked here: 12 (factorial's DOSE_MULTIPLIER_SIGMA_C
# for mistral) * 0.3054430504224313 == 3.6653166050691756 == REFERENCE_DOSE_ABS
# (verified in the smoke suite, test_mistral_sigma_c_reconstructs_reference_dose).
QWEN_SIGMA_C = 1.576023489724997          # cell.yaml line 33
MISTRAL_SIGMA_C = 0.3054430504224313      # reused from factorial config.py MISTRAL_SIGMA_C (not restated in M1 cell.yaml)
SIGMA_C = {"qwen35_4b": QWEN_SIGMA_C, "mistral7b_v03": MISTRAL_SIGMA_C}

POOLS = {
    "qwen35_4b": {"confab_full": 1332, "known_full": 360},   # cell.yaml lines 35-36
    "mistral7b_v03": {"confab_full": 1312, "known_full": 382},  # cell.yaml lines 49-50
}

# ---------------------------------------------------------------------------
# Ladder and populations (cell.yaml `ladder`/`population`, lines 57-68;
# Decision record items 1-2)
# ---------------------------------------------------------------------------
LADDER_MULTIPLIERS = (0.0625, 0.125, 0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0, 4.0)  # cell.yaml line 58

WRITE_LAW = "erase_write"          # cell.yaml line 60
WRITE_POSITION = "anchor_onward"   # cell.yaml line 60

# gates.yaml SC1_dose_and_preflight; cell.yaml `write.readback_tolerance_rel`
# reused byte-identically from the factorial pin (cell.yaml does not restate
# a numeric readback tolerance itself -- gates.yaml line 16 states it as
# prose "within RELATIVE 0.005 of the commanded ladder dose").
READBACK_TOLERANCE_REL = 0.005
# PI-approved amendment 2026-07-17 (pre-generation, repinned gates.yaml
# 934cacae): a check also passes if abs_delta <= 0.005 x the family
# reference_dose_abs (deterministic bf16 readback floor dominates the
# relative bar only at the 0.0625x rung; see NOTEBOOK 2026-07-17 entries
# and analysis/preflight_diag/).
READBACK_TOLERANCE_ABS_FRAC_OF_REF = 0.005

# ladder.generation (cell.yaml line 61): decode=greedy, batch_size=4,
# runlog_checkpointing=true. max_new_tokens is NOT restated in M1's cell.yaml
# (the render/generation stack is reused byte-identically from the
# factorial's own generation pins, AMENDMENT.md "Arms" -- factorial
# config.py GEN_MAX_NEW_TOKENS=200).
GEN_DO_SAMPLE = False
GEN_MAX_NEW_TOKENS = 200
GEN_ENABLE_THINKING = False
BATCH_SIZE = 4                     # cell.yaml line 61

SUBSAMPLE_CONFAB_N_PER_FAMILY = 400   # cell.yaml line 65; Decision record item 2
SUBSAMPLE_PERMUTATION_SEED = 48260714  # cell.yaml line 66

# ---------------------------------------------------------------------------
# Readout (cell.yaml `readout`, lines 81-89; Decision record item 3)
# ---------------------------------------------------------------------------
CALIBRATION_SLICE_ROWS_PER_FAMILY = 700   # cell.yaml line 85
CALIBRATION_SLICE_SEED = 48260715         # cell.yaml line 86
DISAGREEMENT_GATE_MAX = 0.05              # cell.yaml line 89 (prose value, see anomaly note above); gates.yaml line 23

# ---------------------------------------------------------------------------
# Criterion floors (cell.yaml `criteria`, lines 94-107; gates.yaml `criteria`)
# ---------------------------------------------------------------------------
OBSERVABLE_BOUND_FLOOR = 2.5              # cell.yaml line 98; gates.yaml line 33
RETRODICTION_TOLERANCE_ABS = 0.10         # cell.yaml line 102; gates.yaml line 40
NON_MONOTONE_CEILING = {"confab": 0.05, "known": 0.10}  # cell.yaml line 107; gates.yaml line 44

RETRODICTION_ANCHORS = {
    "qwen35_4b": {"permuted_confab": 0.693, "permuted_known": 0.065, "baseline_confab": 0.0833, "baseline_known": 0.0},
    "mistral7b_v03": {"permuted_confab": 0.692, "permuted_known": 0.051, "baseline_confab": 0.2820, "baseline_known": 0.0052},
}  # cell.yaml lines 104-105

# ---------------------------------------------------------------------------
# Statistics (gates.yaml `statistics`)
# ---------------------------------------------------------------------------
BOOTSTRAP_N_RESAMPLES = 10000
BOOTSTRAP_SEED = 48260716   # gates.yaml line 7

# ---------------------------------------------------------------------------
# GPU preflight (gates.yaml SC1_dose_and_preflight, PI standing directive
# 2026-07-16): per family, 4 rows at the bottom rung, the 1.0x rung, and the
# top two rungs (3x, 4x).
# ---------------------------------------------------------------------------
PREFLIGHT_ROWS_DEFAULT = 4
PREFLIGHT_RUNG_MULTIPLIERS = (0.0625, 1.0, 3.0, 4.0)


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


_DISAGREEMENT_GATE_LINE_RE = re.compile(r"^(\s*disagreement_gate:\s)(.*)$", re.MULTILINE)


def _load_cell_yaml_permissive() -> dict:
    """Loads cell.yaml despite the line-89 YAML bug documented in this
    module's docstring, by quoting the ONE offending value IN MEMORY before
    parsing. Never writes to the on-disk file. Re-checks after the fix that
    no OTHER parse error remains (yaml.safe_load only ever reports the
    first error it hits, so a second latent error would otherwise be
    silently masked by this workaround)."""
    import yaml

    text = CELL_YAML_PATH.read_text(encoding="utf-8")

    def _quote(m: "re.Match[str]") -> str:
        val = m.group(2)
        return m.group(1) + '"' + val.replace('"', '\\"') + '"'

    patched, n_subs = _DISAGREEMENT_GATE_LINE_RE.subn(_quote, text, count=1)
    if n_subs != 1:
        raise RuntimeError(
            "config._load_cell_yaml_permissive: expected exactly one "
            "'disagreement_gate:' line to patch in cell.yaml; found "
            f"{n_subs}. The known line-89 anomaly may have moved or been "
            "fixed upstream -- re-verify before trusting this loader."
        )
    return yaml.safe_load(patched)


def verify_against_live_yaml() -> dict[str, object]:
    """Cross-checks a representative subset of the literal constants above
    against a fresh parse of the locked, hash-verified cell.yaml/gates.yaml
    (cell.yaml via the documented permissive workaround), so drift between
    this file and the signed spec is caught rather than silently trusted."""
    import yaml

    cell = _load_cell_yaml_permissive()
    gates = yaml.safe_load(GATES_YAML_PATH.read_text(encoding="utf-8"))

    mismatches: dict[str, tuple] = {}

    def check(name: str, expected, actual):
        if expected != actual:
            mismatches[name] = (expected, actual)

    qf = cell["families"]["qwen35_4b"]
    check("qwen.substrate", SUBSTRATE["qwen35_4b"], qf["substrate"])
    check("qwen.revision", REVISION["qwen35_4b"], qf["revision"])
    check("qwen.layer_hs_index", LAYER_HS_INDEX["qwen35_4b"], qf["layer_hs_index"])
    check("qwen.reference_dose_abs", REFERENCE_DOSE_ABS["qwen35_4b"], qf["reference_dose_abs"])
    check("qwen.sigma_c", QWEN_SIGMA_C, qf["snap_standardization"]["sigma_c"])
    check("qwen.pools.confab_full", POOLS["qwen35_4b"]["confab_full"], qf["pools"]["confab_full"])
    check("qwen.pools.known_full", POOLS["qwen35_4b"]["known_full"], qf["pools"]["known_full"])

    mf = cell["families"]["mistral7b_v03"]
    check("mistral.substrate", SUBSTRATE["mistral7b_v03"], mf["substrate"])
    check("mistral.revision", REVISION["mistral7b_v03"], mf["revision"])
    check("mistral.layer_hs_index", LAYER_HS_INDEX["mistral7b_v03"], mf["layer_hs_index"])
    check("mistral.reference_dose_abs", REFERENCE_DOSE_ABS["mistral7b_v03"], mf["reference_dose_abs"])
    check("mistral.pools.confab_full", POOLS["mistral7b_v03"]["confab_full"], mf["pools"]["confab_full"])
    check("mistral.pools.known_full", POOLS["mistral7b_v03"]["known_full"], mf["pools"]["known_full"])

    check("ladder.multipliers", list(LADDER_MULTIPLIERS), cell["ladder"]["multipliers"])
    check("ladder.write.law", WRITE_LAW, cell["ladder"]["write"]["law"])
    check("ladder.write.position", WRITE_POSITION, cell["ladder"]["write"]["position"])
    check("ladder.generation.batch_size", BATCH_SIZE, cell["ladder"]["generation"]["batch_size"])
    check("ladder.generation.decode", "greedy", cell["ladder"]["generation"]["decode"])

    check("subsample.n_per_family", SUBSAMPLE_CONFAB_N_PER_FAMILY, cell["population"]["confab_subsample"]["n_per_family"])
    check("subsample.seed", SUBSAMPLE_PERMUTATION_SEED, cell["population"]["confab_subsample"]["seed"])

    check("calibration_slice.per_family_rows", CALIBRATION_SLICE_ROWS_PER_FAMILY, cell["readout"]["calibration_slice"]["per_family_rows"])
    # calibration_slice.sampling is a prose string ("registered seed 48260715,
    # stratified..."), not a numeric key; checked as substring containment.
    if str(CALIBRATION_SLICE_SEED) not in cell["readout"]["calibration_slice"]["sampling"]:
        mismatches["calibration_slice.sampling_seed_in_prose"] = (CALIBRATION_SLICE_SEED, cell["readout"]["calibration_slice"]["sampling"])

    check("criteria.observable_bound_floor", OBSERVABLE_BOUND_FLOOR, cell["criteria"]["separation_censoring_aware"]["observable_bound_floor"])
    check("criteria.retrodiction.tolerance_abs", RETRODICTION_TOLERANCE_ABS, cell["criteria"]["retrodiction"]["tolerance_abs"])
    check("criteria.non_monotone_ceiling", NON_MONOTONE_CEILING, cell["criteria"]["non_monotone_ceiling"])
    check("criteria.retrodiction.anchors", RETRODICTION_ANCHORS, cell["criteria"]["retrodiction"]["anchors"])

    # gates.yaml records the bootstrap seed as a prose string
    # ("bootstrap 95% CI, 10000 resamples, seed 48260716"), not a numeric
    # key; checked as substring containment rather than equality.
    if str(BOOTSTRAP_SEED) not in gates["statistics"]["medians_and_ratios"]:
        mismatches["gates.statistics.bootstrap_seed_in_prose"] = (BOOTSTRAP_SEED, gates["statistics"]["medians_and_ratios"])
    check("gates.criteria.P1.observable_bound_floor", OBSERVABLE_BOUND_FLOOR, gates["criteria"]["P1_separation_censoring_aware"]["observable_bound_floor"])
    check("gates.criteria.P3.tolerance_abs", RETRODICTION_TOLERANCE_ABS, gates["criteria"]["P3_retrodiction"]["tolerance_abs"])
    check("gates.criteria.C1.non_monotone_ceiling", NON_MONOTONE_CEILING, gates["criteria"]["C1_construct_integrity"]["non_monotone_ceiling"])
    check("gates.criteria.C1.calibration_agreement_max_disagreement", DISAGREEMENT_GATE_MAX, gates["criteria"]["C1_construct_integrity"]["calibration_agreement_max_disagreement"])

    return {"pass": not mismatches, "mismatches": mismatches}
