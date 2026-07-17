"""CPU smoke suite for margin-mapping (M1). No model, no GPU. Run via
`/home/profsynapse/miniconda3/bin/python3 -m pytest test_margin_smoke.py -v`
(explicit file path -- bare `python3 test_*.py` and bare directory globs are
both known rtk/pytest false-negative traps in this repo, per this repo's own
standing gotcha).

Covers: config/YAML pin verification (including the documented cell.yaml
line-89 parse-bug workaround), dose-ladder computation against cell.yaml's
own reference values, sigma_c/write-param sigma-gain non-conflation
(regression guard, same class of defect the factorial fixed 2026-07-16),
subsample draw determinism, SC0 staging-manifest hash-assertion logic, and
RunLog resume-from-checkpoint behavior.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import config  # noqa: E402
import common  # noqa: E402
import dose_ladder  # noqa: E402
import sc1_checks  # noqa: E402
import detector_v2  # noqa: E402
import grader  # noqa: E402


# ---------------------------------------------------------------------------
# config / pins
# ---------------------------------------------------------------------------

def test_config_pinned_hashes_pass():
    result = config.verify_pinned_hashes()
    assert result == {"cell_yaml": True, "gates_yaml": True}, result


def test_config_live_yaml_crosscheck_passes():
    """Exercises the documented in-memory workaround for cell.yaml's line-89
    YAML parse bug (an unquoted colon inside the `disagreement_gate` prose
    value). If this test starts failing with a parse error instead of a
    mismatch, the anomaly note in config.py's docstring needs revisiting."""
    result = config.verify_against_live_yaml()
    assert result["pass"] is True, result["mismatches"]


def test_cell_yaml_has_the_documented_line_89_parse_bug():
    """Documents (does not fix -- cell.yaml is locked) that a raw
    yaml.safe_load of cell.yaml fails exactly as config.py's docstring
    describes. If this test starts passing, the signed file changed
    (which must never happen without a re-sign) or PyYAML's grammar
    changed; either way, re-verify the anomaly note before trusting it."""
    import yaml

    with pytest.raises(yaml.YAMLError):
        yaml.safe_load(config.CELL_YAML_PATH.read_text(encoding="utf-8"))


def test_gates_yaml_parses_cleanly():
    import yaml

    yaml.safe_load(config.GATES_YAML_PATH.read_text(encoding="utf-8"))  # must not raise


def test_permissive_loader_recovers_the_disagreement_gate_prose_value():
    cell = config._load_cell_yaml_permissive()
    val = cell["readout"]["calibration_slice"]["disagreement_gate"]
    assert str(config.DISAGREEMENT_GATE_MAX) in val
    assert "remedy" in val  # the exact prose fragment that breaks the raw parse


# ---------------------------------------------------------------------------
# dose ladder (cell.yaml `ladder.multipliers`; Decision record item 1)
# ---------------------------------------------------------------------------

def test_ladder_multipliers_match_cell_yaml():
    assert config.LADDER_MULTIPLIERS == (0.0625, 0.125, 0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0, 4.0)


def test_rung_dose_abs_at_1x_equals_reference_dose():
    """The pinned reference values from the task brief: qwen
    12.608187917799976, mistral 3.6653166050691756 -- these ARE the 1.0x
    rung by construction (cell.yaml `ladder.write.setpoint: multiplier x
    reference_dose_abs`)."""
    assert dose_ladder.rung_dose_abs("qwen35_4b", 1.0) == pytest.approx(12.608187917799976, rel=0, abs=1e-12)
    assert dose_ladder.rung_dose_abs("mistral7b_v03", 1.0) == pytest.approx(3.6653166050691756, rel=0, abs=1e-12)


def test_rung_dose_abs_scales_linearly_with_multiplier():
    for family in config.FAMILIES:
        ref = config.REFERENCE_DOSE_ABS[family]
        for m in config.LADDER_MULTIPLIERS:
            assert dose_ladder.rung_dose_abs(family, m) == pytest.approx(m * ref)


def test_mistral_sigma_c_reconstructs_reference_dose():
    """M1's own cell.yaml does not restate mistral's sigma_c (only qwen's,
    via snap_standardization); MISTRAL_SIGMA_C is reused byte-identically
    from the factorial's config.py. This is the live cross-check: 12x
    sigma_c (the factorial's own DOSE_MULTIPLIER_SIGMA_C for mistral) must
    reconstruct the registered reference_dose_abs exactly."""
    assert 12 * config.MISTRAL_SIGMA_C == pytest.approx(config.REFERENCE_DOSE_ABS["mistral7b_v03"], rel=0, abs=1e-9)


def test_c_hat_write_params_gain_times_sigma_equals_setpoint_every_rung():
    """Regression guard against the SAME class of defect the factorial fixed
    2026-07-16 (sigma/gain conflation realizing gain**2 instead of
    gain*sigma). Checked at every ladder rung, not just the 1.0x setpoint."""
    for family in config.FAMILIES:
        for m in config.LADDER_MULTIPLIERS:
            setpoint = dose_ladder.rung_dose_abs(family, m)
            sigma, gain = dose_ladder.c_hat_write_params(family, setpoint)
            assert sigma == config.SIGMA_C[family]
            assert sigma != gain, "sigma and gain must not be conflated (the gain-squared defect)"
            assert abs(sigma * gain - setpoint) < 1e-9


def test_rung_tag_is_filesystem_safe_and_unique():
    tags = [dose_ladder.rung_tag(m) for m in config.LADDER_MULTIPLIERS]
    assert len(set(tags)) == len(tags), tags
    for t in tags:
        assert "." not in t
        assert "/" not in t


# ---------------------------------------------------------------------------
# SC1 readback checks
# ---------------------------------------------------------------------------

def test_check_readback_passes_within_tolerance():
    target = 12.608187917799976
    c = sc1_checks.check_readback("r1", "qwen35_4b", target * 1.001, target)
    assert c["passed"] is True


def test_check_readback_fails_outside_tolerance():
    target = 12.608187917799976
    c = sc1_checks.check_readback("r1", "qwen35_4b", target * 1.05, target)
    assert c["passed"] is False


def test_check_readback_fails_on_missing_readback():
    c = sc1_checks.check_readback("r1", "qwen35_4b", None, 12.6)
    assert c["passed"] is False
    assert c["reason"] == "no_readback_recorded"


def test_check_readback_catches_gain_squared_shape_of_failure():
    """Same regression class as the factorial's own live-SC1 test: a
    gain**2 readback must NOT pass the relative-0.005 tolerance at any
    non-trivial rung."""
    for family in config.FAMILIES:
        for m in config.LADDER_MULTIPLIERS:
            setpoint = dose_ladder.rung_dose_abs(family, m)
            _, gain = dose_ladder.c_hat_write_params(family, setpoint)
            squared = gain * gain
            if squared == pytest.approx(setpoint, rel=1e-3):
                continue  # construction-coincidence, skip
            c = sc1_checks.check_readback("r1", family, squared, setpoint)
            assert c["passed"] is False


# ---------------------------------------------------------------------------
# Subsample determinism (cell.yaml `population.confab_subsample`)
# ---------------------------------------------------------------------------

def test_subsample_draw_is_deterministic_under_fixed_seed(monkeypatch):
    import subsample

    fake_pool = {
        "qwen35_4b": {"confab": [f"c{i}" for i in range(20)], "known_correct_answered": []},
        "mistral7b_v03": {"confab": [f"m{i}" for i in range(20)], "known_correct_answered": []},
    }

    class _FakeRowPool:
        @staticmethod
        def heldout_row_keys_by_role(family):
            return fake_pool[family]

    monkeypatch.setattr(subsample, "row_pool", _FakeRowPool)

    out1 = subsample.draw_confab_subsample(seed=48260714, n=5)
    out2 = subsample.draw_confab_subsample(seed=48260714, n=5)
    assert out1 == out2
    assert len(out1["qwen35_4b"]) == 5
    assert len(out1["mistral7b_v03"]) == 5
    assert out1["qwen35_4b"] == sorted(out1["qwen35_4b"])  # committed lists are sorted


def test_subsample_draw_differs_under_different_seed(monkeypatch):
    import subsample

    fake_pool = {
        "qwen35_4b": {"confab": [f"c{i}" for i in range(50)], "known_correct_answered": []},
        "mistral7b_v03": {"confab": [f"m{i}" for i in range(50)], "known_correct_answered": []},
    }

    class _FakeRowPool:
        @staticmethod
        def heldout_row_keys_by_role(family):
            return fake_pool[family]

    monkeypatch.setattr(subsample, "row_pool", _FakeRowPool)

    out1 = subsample.draw_confab_subsample(seed=48260714, n=10)
    out2 = subsample.draw_confab_subsample(seed=99999999, n=10)
    assert out1 != out2


def test_registered_subsample_seed_and_n_match_cell_yaml():
    assert config.SUBSAMPLE_PERMUTATION_SEED == 48260714
    assert config.SUBSAMPLE_CONFAB_N_PER_FAMILY == 400


# ---------------------------------------------------------------------------
# SC0 staging manifest hash-assertion logic
# ---------------------------------------------------------------------------

def test_staging_hard_fails_on_factorial_manifest_mismatch(tmp_path, monkeypatch):
    import staging

    src = tmp_path / "source.jsonl"
    src.write_text('{"row_key": "a"}\n', encoding="utf-8")

    entry = {"name": "fake_entry", "factorial_name": "fake_entry", "kind": "jsonl", "source": src, "dest": "fake/fake.jsonl"}
    monkeypatch.setattr(staging, "STAGED", tmp_path / "staged")

    wrong_hash_manifest = {"fake_entry": {"name": "fake_entry", "sha256": "0" * 64}}
    with pytest.raises(SystemExit, match="does NOT match"):
        staging.stage_gitignored(entry, wrong_hash_manifest)


def test_staging_passes_on_factorial_manifest_match(tmp_path, monkeypatch):
    import staging

    src = tmp_path / "source.jsonl"
    src.write_text('{"row_key": "a"}\n', encoding="utf-8")
    real_hash = common.sha256_of_file(src)

    monkeypatch.setattr(staging, "STAGED", tmp_path / "staged")
    monkeypatch.setattr(staging, "EXPERIMENT_DIR", tmp_path)
    entry = {"name": "fake_entry", "factorial_name": "fake_entry", "kind": "jsonl", "source": src, "dest": "fake/fake.jsonl"}
    factorial_manifest = {"fake_entry": {"name": "fake_entry", "sha256": real_hash}}

    record = staging.stage_gitignored(entry, factorial_manifest)
    assert record["sha256"] == real_hash
    assert record["matches_factorial_manifest_entry"] == "fake_entry"


def test_staging_hard_fails_when_factorial_manifest_entry_missing(tmp_path, monkeypatch):
    import staging

    src = tmp_path / "source.jsonl"
    src.write_text('{"row_key": "a"}\n', encoding="utf-8")
    monkeypatch.setattr(staging, "STAGED", tmp_path / "staged")
    entry = {"name": "fake_entry", "factorial_name": "does_not_exist", "kind": "jsonl", "source": src, "dest": "fake/fake.jsonl"}

    with pytest.raises(SystemExit, match="no factorial staging_manifest.json entry"):
        staging.stage_gitignored(entry, {})


def test_real_sc0_staging_manifest_on_disk_matches_factorial_and_detector_stack_is_identical():
    """Live check against the actual SC0 output on disk from this build (not
    a synthetic fixture): every staged entry's sha256 traces to the
    factorial's own committed staging_manifest.json, and the detector stack
    copied into this harness/ is byte-identical to the factorial's."""
    import staging

    manifest_path = staging.COMMITTED / "staging_manifest.json"
    if not manifest_path.is_file():
        pytest.skip("staging.py has not been run yet in this worktree")
    manifest = common.load_json(manifest_path)
    factorial_by_name = staging._load_factorial_manifest()
    for rec in manifest["files"]:
        fact = factorial_by_name[rec["matches_factorial_manifest_entry"]]
        assert rec["sha256"] == fact["sha256"], rec["name"]

    detector_check = staging.verify_detector_stack_byte_identical()
    assert detector_check["pass"] is True


# ---------------------------------------------------------------------------
# RunLog resume-from-checkpoint (shared.utilities.run_log.RunLog)
# ---------------------------------------------------------------------------

def test_runlog_resume_skips_already_recorded_keys(tmp_path):
    sys.path.insert(0, str(config.REPO_ROOT / "synaptic-tuner"))
    from shared.utilities.run_log import RunLog

    path = tmp_path / "resume_test.jsonl"
    run_config = {"stage": "unit_test"}

    log1 = RunLog(path, run_config=run_config, fresh=True)
    log1.record("r1", {"value": 1})
    log1.record("r2", {"value": 2})
    log1.close()

    # Simulate a resumed process: reopen the SAME path/run_config, must see
    # r1/r2 as already done and accept a new record without re-writing them.
    log2 = RunLog(path, run_config=run_config, fresh=False)
    assert log2.done_keys() == {"r1", "r2"}
    log2.record("r3", {"value": 3})
    log2.close()

    rows = common.load_jsonl(path)
    assert {r["key"] for r in rows} == {"r1", "r2", "r3"}


def test_runlog_resume_rejects_mismatched_run_config(tmp_path):
    from shared.utilities.run_log import RunLog, RunLogError

    path = tmp_path / "resume_mismatch.jsonl"
    log1 = RunLog(path, run_config={"multiplier": 1.0}, fresh=True)
    log1.record("r1", {"value": 1})
    log1.close()

    with pytest.raises(RunLogError):
        RunLog(path, run_config={"multiplier": 2.0}, fresh=False)


def test_pass_is_durable_true_only_when_complete_and_full_coverage(tmp_path, monkeypatch):
    import run_margin
    from shared.utilities.run_log import RunLog

    monkeypatch.setattr(run_margin, "ANALYSIS", tmp_path)
    tag = "unit_test_rung"
    expected = ["r1", "r2", "r3"]

    assert run_margin.pass_is_durable(tag, expected) is False  # no file yet

    log = RunLog(run_margin.runlog_path(tag), run_config={"stage": "unit"}, fresh=True)
    log.record("r1", {"value": 1})
    log.record("r2", {"value": 2})
    log.close()
    assert run_margin.pass_is_durable(tag, expected) is False  # not finalized

    log2 = RunLog(run_margin.runlog_path(tag), run_config={"stage": "unit"}, fresh=False)
    log2.record("r3", {"value": 3})
    log2.finalize({"n_rows": 3})
    log2.close()
    assert run_margin.pass_is_durable(tag, expected) is True


# ---------------------------------------------------------------------------
# detector stack self-checks (byte-identical copies)
# ---------------------------------------------------------------------------

def test_detector_v2_self_check():
    detector_v2._self_check()


def test_grader_self_check():
    grader._self_check()


# ---------------------------------------------------------------------------
# preflight rung-point registration (gates.yaml SC1_dose_and_preflight)
# ---------------------------------------------------------------------------

def test_preflight_rung_multipliers_match_gates_yaml_spec():
    """bottom rung, 1.0x, and the top two rungs (3x, 4x)."""
    assert config.PREFLIGHT_RUNG_MULTIPLIERS == (0.0625, 1.0, 3.0, 4.0)
    assert config.PREFLIGHT_RUNG_MULTIPLIERS[0] == min(config.LADDER_MULTIPLIERS)
    assert config.PREFLIGHT_RUNG_MULTIPLIERS[-2:] == tuple(sorted(config.LADDER_MULTIPLIERS)[-2:])


def test_preflight_rows_default_is_4():
    assert config.PREFLIGHT_ROWS_DEFAULT == 4
