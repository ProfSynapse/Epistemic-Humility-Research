"""CPU smoke suite for gate-contribution-factorial. No model, no GPU. Run via
`/home/profsynapse/miniconda3/bin/python3 -m pytest test_factorial_smoke.py -v`
(explicit file path -- bare `python3 test_*.py` and bare directory globs are
both known rtk/pytest false-negative traps in this repo).

Covers: config/YAML pin verification, detector_v2/grader self-checks and
byte-identity-to-pin, gate_construction pure math INCLUDING a real
cross-check of `qwen_permuted_gate_row_keys` against the on-disk
qwen35-4b-midband-heldout `permuted_gate.jsonl` row_key set (a genuine
cross-experiment integrity test, not a synthetic fixture), sc1_checks
void/redraw ledger logic, subsample determinism, gen_lib's well_formed
JSON-parse field, build_pool's pool-assembly arithmetic, apply_adjudication's
hash-commit-before-unblind refusal behavior, criterion's P1/P2/P3/S1
branches, and containment (no text fields in any committed JSON now on
disk from the real staging/subsample/mistral_direction_provenance runs)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pytest

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import common  # noqa: E402
import config  # noqa: E402
import detector_v2  # noqa: E402
import gate_construction  # noqa: E402
import gen_lib  # noqa: E402
import sc1_checks  # noqa: E402
from direction_draw import fresh_random_direction  # noqa: E402
import subsample  # noqa: E402
import build_pool  # noqa: E402
import apply_adjudication  # noqa: E402
import criterion  # noqa: E402
import heldback_decoys  # noqa: E402
import row_pool  # noqa: E402
import run_factorial  # noqa: E402  (module-level imports are all CPU-only; torch/steer_lib are imported lazily inside its GPU command functions)
import compute_seed_ledger  # noqa: E402


# ---------------------------------------------------------------------------
# config / pins
# ---------------------------------------------------------------------------

def test_config_pinned_hashes_pass():
    result = config.verify_pinned_hashes()
    assert result == {"cell_yaml": True, "gates_yaml": True}, result


def test_config_live_yaml_crosscheck_passes():
    result = config.verify_against_live_yaml()
    assert result["pass"] is True, result["mismatches"]


def test_config_sigma_c_dict_present_and_matches_family_scalars():
    assert config.SIGMA_C["qwen35_4b"] == config.QWEN_SIGMA_C
    assert config.SIGMA_C["mistral7b_v03"] == config.MISTRAL_SIGMA_C


# ---------------------------------------------------------------------------
# run_factorial erase-write sigma/gain wiring (regression guard: a defect
# fixed 2026-07-16 had BOTH `generate-family` call sites pass the GAIN as the
# sigma argument to steer_lib.build_hook_and_controller AND as the
# generation strength, realizing gain**2 (setpoint = gain*sigma =
# gain*gain) instead of the setpoint at every fresh dosed write --
# confirmed against the pre-fix on-disk readbacks in
# analysis-committed/sc1_verification_summary.json: qwen c_hat realized
# 64.03 (=8.0**2) against a setpoint of 12.608 (=8.0*1.576); mistral c_hat
# realized 144.01 (=12.0**2) against 3.665 (=12.0*0.305); qwen random
# realized 159.0 (=12.608**2) against 12.608; mistral random realized 13.44
# (=3.665**2) against 3.665. These tests pin `sigma != gain` (except by
# construction-coincidence, which none of these values hit) so the same
# conflation is caught here on CPU, without a GPU, the next time this wiring
# is touched.
# ---------------------------------------------------------------------------

def test_c_hat_write_params_gain_times_sigma_equals_setpoint():
    for family in config.FAMILIES:
        setpoint = config.SETPOINT_DOSE_ABS[family]
        sigma, gain = run_factorial.c_hat_write_params(family, setpoint)
        assert sigma == config.SIGMA_C[family]
        assert sigma != gain, "sigma and gain must not be conflated (the gain-squared defect)"
        assert abs(sigma * gain - setpoint) < 1e-9
        # setpoint was constructed as dose_mult * sigma_c (cell.yaml), so the
        # correct gain is EXACTLY the registered dose multiplier.
        assert gain == pytest.approx(config.DOSE_MULTIPLIER_SIGMA_C[family])


def test_random_write_params_sigma_is_one_gain_equals_setpoint():
    for family in config.FAMILIES:
        setpoint = config.SETPOINT_DOSE_ABS[family]
        sigma, gain = run_factorial.random_write_params(setpoint)
        assert sigma == 1.0
        assert gain == setpoint
        assert sigma != gain, "sigma and gain must not be conflated (the gain-squared defect)"


def test_c_hat_and_random_write_params_do_not_reproduce_pre_fix_squared_readbacks():
    """Direct regression against the exact pre-fix squared values recorded
    in analysis-committed/sc1_verification_summary.json (worst_case
    readback_measured under the gain-squared defect); the corrected
    setpoint = gain * sigma must land on the true setpoint, not on gain**2."""
    pre_fix_squared_readback = {
        "qwen35_4b": {"c_hat": 64.0282989848638, "random": 158.99454557616264},  # (approx) worst-case observed
        "mistral7b_v03": {"c_hat": 144.01364213170746, "random": 13.44018772407253},
    }
    for family in config.FAMILIES:
        setpoint = config.SETPOINT_DOSE_ABS[family]
        sigma_c, gain_c = run_factorial.c_hat_write_params(family, setpoint)
        sigma_r, gain_r = run_factorial.random_write_params(setpoint)
        assert abs(sigma_c * gain_c - setpoint) < 1e-9
        assert abs(sigma_r * gain_r - setpoint) < 1e-9
        # the OLD (defective) call passed gain as sigma: realized = gain*gain.
        old_c_hat_realized = gain_c * gain_c
        old_random_realized = gain_r * gain_r
        assert old_c_hat_realized == pytest.approx(pre_fix_squared_readback[family]["c_hat"], rel=1e-3)
        assert old_random_realized == pytest.approx(pre_fix_squared_readback[family]["random"], rel=1e-3)
        # and the corrected construction must NOT reproduce those squared values.
        assert sigma_c * gain_c != pytest.approx(old_c_hat_realized, rel=1e-3)
        assert sigma_r * gain_r != pytest.approx(old_random_realized, rel=1e-3)


def test_live_sc1_after_first_batch_passes_on_target_and_aborts_off_target():
    family = "qwen35_4b"
    target = config.SETPOINT_DOSE_ABS[family]
    cb = run_factorial._live_sc1_after_first_batch(family, "unit_test_arm", target)
    good_batch = [{"row_key": "r1", "readback_measured": target}, {"row_key": "r2", "readback_measured": target * 1.001}]
    cb(good_batch)  # must not raise

    cb2 = run_factorial._live_sc1_after_first_batch(family, "unit_test_arm", target)
    bad_batch = [{"row_key": "r1", "readback_measured": target * target}]  # the gain-squared shape of failure
    with pytest.raises(SystemExit, match="LIVE SC1 FAIL"):
        cb2(bad_batch)


def test_live_sc1_after_first_batch_only_checks_first_call():
    family = "qwen35_4b"
    target = config.SETPOINT_DOSE_ABS[family]
    cb = run_factorial._live_sc1_after_first_batch(family, "unit_test_arm", target)
    cb([{"row_key": "r1", "readback_measured": target}])  # first call: checked, passes
    cb([{"row_key": "r2", "readback_measured": target * target}])  # second call: NOT re-checked, must not raise


def test_live_sc1_arm_completion_passes_and_aborts(tmp_path, monkeypatch):
    family = "qwen35_4b"
    target = config.SETPOINT_DOSE_ABS[family]
    monkeypatch.setattr(run_factorial, "ANALYSIS", tmp_path)
    runlog_dir = tmp_path / "runlog"
    runlog_dir.mkdir()
    good_path = runlog_dir / "unit_test_arm_good.jsonl"
    good_path.write_text(json.dumps({"row_key": "r1", "readback_measured": target}) + "\n", encoding="utf-8")
    run_factorial._live_sc1_arm_completion(family, "unit_test_arm_good", "unit_test_arm_good", target)  # must not raise

    bad_path = runlog_dir / "unit_test_arm_bad.jsonl"
    bad_path.write_text(json.dumps({"row_key": "r1", "readback_measured": target * target}) + "\n", encoding="utf-8")
    with pytest.raises(SystemExit, match="LIVE SC1 FAIL"):
        run_factorial._live_sc1_arm_completion(family, "unit_test_arm_bad", "unit_test_arm_bad", target)


# ---------------------------------------------------------------------------
# compute_seed_ledger / random-seed void-and-redraw walk (registered
# mechanism: gates.yaml sc1_magnitude_matching.on_fail)
# ---------------------------------------------------------------------------

def test_compute_seed_ledger_matches_committed_accepted_seeds():
    """Cross-checks the committed random_seed_ledger.json (produced by a
    real run of compute_seed_ledger.py against this experiment's actual
    frozen c_hat/u_d directions) against a fresh recomputation, so drift
    between the committed ledger and a live re-derivation is caught."""
    committed_path = HERE / "analysis-committed" / "random_seed_ledger.json"
    if not committed_path.is_file():
        pytest.skip("random_seed_ledger.json not yet committed")
    committed = json.loads(committed_path.read_text(encoding="utf-8"))
    fresh = compute_seed_ledger.compute_ledger()
    for family in config.FAMILIES:
        assert fresh[family]["accepted_seeds"] == committed[family]["accepted_seeds"]
        assert fresh[family]["n_voids"] == committed[family]["n_voids"]
        assert len(fresh[family]["accepted_seeds"]) == config.K_SEEDS_PER_FAMILY


def test_preflight_seed_disjoint_from_all_registered_seeds():
    registered = set()
    for family in config.FAMILIES:
        registered.update(config.RANDOM_SEED_BLOCKS[family])
    registered.update(config.PERMUTED_GATE_SEED.values())
    registered.add(config.SUBSAMPLE_PERMUTATION_SEED)
    for family, seed in run_factorial.PREFLIGHT_SEED.items():
        assert seed not in registered


# ---------------------------------------------------------------------------
# detector_v2 / grader (byte-identical pin, SC0)
# ---------------------------------------------------------------------------

def test_detector_v2_self_check():
    detector_v2._self_check()  # raises on failure


def test_detector_v2_byte_identical_to_census_pin():
    # CLAUDE.md: the canonical checkout is a fixed sibling of the
    # ehr-worktrees/ directory this worktree lives under, not a path
    # computed relative to this worktree's own nesting depth.
    census_dir = Path("/home/profsynapse/code/Epistemic-Humility-Research/experiments/placebo-seed-distribution-census")
    if not census_dir.is_dir():
        pytest.skip(f"canonical census checkout not found at {census_dir}")
    for name in ("detector_v2.py", "detector_v2_patterns.yaml", "grader.py"):
        mine = common.sha256_of_file(HERE / name)
        theirs = common.sha256_of_file(census_dir / name)
        assert mine == theirs, f"{name} sha256 mismatch: mine={mine} census={theirs}"


def test_gen_lib_well_formed_field_present():
    grade = gen_lib.grade_row('{"answer": "Paris"}', True, ["Paris"])
    assert grade["well_formed"] is True
    assert grade["well_formed_correct_v2"] is True

    grade_confab = gen_lib.grade_row('{"answer": "who knows"}', True, [])
    assert grade_confab["well_formed"] is True
    assert grade_confab["well_formed_correct_v2"] is False  # no aliases -> correct_v2 never True

    grade_garbage = gen_lib.grade_row("not json at all, no answer key here", True, [])
    assert grade_garbage["well_formed"] is False


def test_gen_lib_refusal_detected():
    grade = gen_lib.grade_row("I don't know the answer to that.", True, [])
    assert grade["refused_v2"] is True


# ---------------------------------------------------------------------------
# gate_construction
# ---------------------------------------------------------------------------

def test_gate_decision_fire_boundary():
    fired = gate_construction.gate_decision(proj_d=-5.0, mu_d=0.0, sigma_d=1.0, tau=1.5)
    assert fired["fire"] is True
    assert fired["z_d"] == -2.0  # clipped

    not_fired = gate_construction.gate_decision(proj_d=5.0, mu_d=0.0, sigma_d=1.0, tau=1.5)
    assert not_fired["fire"] is False


def test_verify_qwen_fire_counts_pass_and_fail():
    good = [{"role": "confab", "fire": True}] * 1286 + [{"role": "confab", "fire": False}] * (1332 - 1286) \
        + [{"role": "known_correct_answered", "fire": True}] * 17 + [{"role": "known_correct_answered", "fire": False}] * (360 - 17)
    result = gate_construction.verify_qwen_fire_counts(good)
    assert result["pass"] is True

    bad = good[:-1]  # drop one known non-fired row -> counts off
    result_bad = gate_construction.verify_qwen_fire_counts(bad)
    assert result_bad["pass"] is False


def test_draw_permuted_gate_indices_deterministic():
    a = gate_construction.draw_permuted_gate_indices(1692, 1303, seed=20260713)
    b = gate_construction.draw_permuted_gate_indices(1692, 1303, seed=20260713)
    assert a == b
    assert len(a) == 1303
    assert len(set(a)) == 1303  # no replacement
    assert a == sorted(a)


def test_qwen_permuted_gate_row_keys_matches_real_midband_heldout_artifact():
    """Genuine cross-experiment integrity check (not a synthetic fixture):
    this harness's `qwen_permuted_gate_row_keys`, run over the SAME file
    order and SAME seed midband-heldout used for its own permuted_gate arm,
    must reproduce midband-heldout's already-on-disk fired row_key set
    exactly."""
    steer_path = HERE / "analysis" / "staged_inputs" / "qwen35_4b" / "heldout_rows_for_steer.jsonl"
    reference_path = Path("/home/profsynapse/code/ehr-worktrees/qwen35-midband-heldout/experiments/qwen35-4b-midband-heldout/analysis/runlog/permuted_gate.jsonl")
    if not steer_path.is_file():
        pytest.skip(f"staged steer-row file not found at {steer_path}; run staging.py first")
    if not reference_path.is_file():
        pytest.skip(f"reference midband-heldout permuted_gate.jsonl not found at {reference_path}")

    file_order = [json.loads(line)["row_key"] for line in steer_path.open(encoding="utf-8") if line.strip()]
    reference_fired = sorted({json.loads(line)["row_key"] for line in reference_path.open(encoding="utf-8") if line.strip()})

    computed = gate_construction.qwen_permuted_gate_row_keys(file_order, n_fired=len(reference_fired), seed=config.PERMUTED_GATE_SEED["qwen35_4b"])
    assert computed == reference_fired, (
        f"computed permuted-gate row_key set diverges from midband-heldout's own on-disk artifact "
        f"(n_computed={len(computed)}, n_reference={len(reference_fired)}, "
        f"n_symdiff={len(set(computed) ^ set(reference_fired))})"
    )


def test_mistral_permuted_gate_row_keys_shape():
    confab = [f"c{i}" for i in range(1312)]
    known = [f"k{i}" for i in range(382)]
    result = gate_construction.mistral_permuted_gate_row_keys(confab, known, n_fired=1303, seed=20260715)
    assert len(result) == 1303
    assert result == sorted(result)
    assert set(result) <= set(confab) | set(known)


# ---------------------------------------------------------------------------
# sc1_checks
# ---------------------------------------------------------------------------

def test_readback_within_tolerance_passes():
    result = sc1_checks.check_readback(seed=44000001, family="qwen35_4b",
                                       readback_measured=12.608187917799976 * 1.001, target=12.608187917799976)
    assert result["passed"] is True


def test_readback_outside_tolerance_fails():
    result = sc1_checks.check_readback(seed=44000001, family="qwen35_4b",
                                       readback_measured=12.608187917799976 * 1.05, target=12.608187917799976)
    assert result["passed"] is False


def test_readback_missing_fails_with_reason():
    result = sc1_checks.check_readback(seed=44000001, family="qwen35_4b", readback_measured=None, target=12.608187917799976)
    assert result["passed"] is False
    assert result["reason"] == "no_readback_recorded"


def test_randomness_bar_passes_for_orthogonal_vector():
    # In hidden_dim=2560, two independent random unit vectors are near-orthogonal
    # (cos ~ O(1/sqrt(dim))) with overwhelming probability, well under the 0.015 bar.
    rng = np.random.default_rng(0)
    c_hat = common.unit(rng.normal(size=2560))
    u_d = common.unit(rng.normal(size=2560))
    result = sc1_checks.check_randomness_bar(seed=44000001, hidden_dim=2560, c_hat=c_hat, u_d=u_d)
    assert result["passed"] is True


def test_randomness_bar_fails_when_direction_equals_c_hat():
    # Forcing the drawn direction to literally BE c_hat guarantees cos=1.0,
    # deterministically exceeding any bar -- a clean way to force the fail
    # branch without needing to reverse-engineer fresh_random_direction's RNG.
    seed = 44000001
    c_hat = fresh_random_direction(seed, 2560)
    u_d = common.unit(np.random.default_rng(1).normal(size=2560))
    result = sc1_checks.check_randomness_bar(seed=seed, hidden_dim=2560, c_hat=c_hat, u_d=u_d)
    assert result["passed"] is False
    assert result["abs_cos_to_c_hat"] == pytest.approx(1.0, abs=1e-9)


# ---------------------------------------------------------------------------
# subsample determinism
# ---------------------------------------------------------------------------

def test_subsample_draw_deterministic():
    if not (HERE / "analysis" / "staged_inputs").is_dir():
        pytest.skip("staged_inputs not present; run staging.py first")
    a = subsample.draw_subsample()
    b = subsample.draw_subsample()
    assert a == b
    for family in subsample.FAMILY_ORDER:
        assert len(a[family]) == config.SUBSAMPLE_CONFAB_ROWS_PER_FAMILY
        assert a[family] == sorted(a[family])


def test_subsample_matches_committed_manifest():
    manifest_path = HERE / "analysis-committed" / "subsample_manifest.json"
    if not manifest_path.is_file():
        pytest.skip("subsample_manifest.json not present; run subsample.py first")
    manifest = common.load_json(manifest_path)
    fresh = subsample.draw_subsample()
    for family, keys in fresh.items():
        assert manifest["families"][family]["row_keys"] == keys


# ---------------------------------------------------------------------------
# build_pool pure arithmetic
# ---------------------------------------------------------------------------

def test_salted_opaque_id_deterministic_and_salt_sensitive():
    a = build_pool.salted_opaque_id("salt1", "qwen35_4b", "baseline", "rk1", None)
    b = build_pool.salted_opaque_id("salt1", "qwen35_4b", "baseline", "rk1", None)
    c = build_pool.salted_opaque_id("salt2", "qwen35_4b", "baseline", "rk1", None)
    assert a == b
    assert a != c


def test_pick_n_shards_scales_with_size():
    assert build_pool.pick_n_shards(0) == 1
    assert build_pool.pick_n_shards(700) == 1
    assert build_pool.pick_n_shards(2100) == 3


def test_cap_total_shards_by_cell_respects_decoy_floors():
    n_shards = {"qwen35_4b": 5, "mistral7b_v03": 5}
    capped = build_pool.cap_total_shards_by_cell(n_shards, n_decoys_neg=3, n_decoys_pos=100)
    assert sum(capped.values()) <= 3


def test_carve_decoys_respects_available_pools():
    core = [{"row_key": f"r{i}"} for i in range(100)]
    heldback = [{"row_key": f"h{i}", "refused_v2": False} for i in range(5)]
    positive = [{"row_key": f"p{i}", "refused_v2": True, "arm": "true_gate_c_hat"} for i in range(50)]
    import random
    rng = random.Random(1)
    neg, pos = build_pool.carve_decoys(core, heldback, positive, rng)
    assert len(neg) <= len(heldback)
    assert len(pos) <= len(positive)
    assert all(d["decoy_type"] == "clear_negative" for d in neg)
    assert all(d["decoy_type"] == "clear_positive" for d in pos)


def test_load_heldback_candidates_raises_loudly_when_missing(tmp_path, monkeypatch):
    """See build_pool.py / heldback_decoys.py module docstrings: this
    experiment's own held-out known population is a structurally invalid
    decoy source (full-known-pool design); the REAL clear-negative source
    is `heldback_decoys.py`'s FIT-split decoy-baseline pass, and this
    loader must still raise loudly when THAT pool hasn't been built yet at
    the path it reads from. Isolated from real on-disk build state via a
    monkeypatched empty `ANALYSIS` dir, so this test holds regardless of
    whether this worktree's own heldback__<family>.jsonl runlogs have
    already been built (as they now are, once `heldback_decoys.py build`
    has run against a completed decoy-baseline generation)."""
    monkeypatch.setattr(build_pool, "ANALYSIS", tmp_path)
    with pytest.raises(SystemExit):
        build_pool.load_heldback_candidates()


# ---------------------------------------------------------------------------
# apply_adjudication: hash-commit-before-unblind
# ---------------------------------------------------------------------------

def test_unblinding_refused_without_committed_hash(tmp_path):
    committed_dir = tmp_path / "analysis-committed"
    committed_dir.mkdir()
    graded_file = tmp_path / "graded.jsonl"
    graded_file.write_text('{"opaque_id": "abc"}\n', encoding="utf-8")
    with pytest.raises(SystemExit, match="UNBLINDING REFUSED"):
        apply_adjudication._require_committed_hash("shard_00", graded_file, committed_dir)


def test_unblinding_allowed_after_commit_hash(tmp_path):
    committed_dir = tmp_path / "analysis-committed"
    committed_dir.mkdir()
    graded_path = tmp_path / "graded.jsonl"
    graded_path.write_text('{"opaque_id": "abc"}\n', encoding="utf-8")

    # NOTE: a class body attribute assignment shadows ANY enclosing-scope name
    # it reads on its own RHS (`graded_file = str(graded_file)` raises
    # NameError, not "reads the outer variable then shadows it") -- Python
    # treats an assigned-to name as local throughout the whole class body, so
    # the RHS reference resolves to the not-yet-bound local. Every RHS below
    # therefore reads from a DIFFERENTLY-named local (`_graded_path`/
    # `_committed_dir`), only aliased to the attribute names
    # apply_adjudication.cmd_commit_hash actually expects.
    _graded_path, _committed_dir = graded_path, committed_dir

    class Args:
        shard_id = "shard_00"
        graded_file = str(_graded_path)
        committed_dir = str(_committed_dir)

    apply_adjudication.cmd_commit_hash(Args())
    sha = apply_adjudication._require_committed_hash("shard_00", graded_path, committed_dir)
    assert len(sha) == 64


def test_evaluate_shard_refuses_on_positional_mismatch(tmp_path):
    analysis_dir = tmp_path / "analysis"
    committed_dir = tmp_path / "analysis-committed"
    (analysis_dir / "shards").mkdir(parents=True)
    committed_dir.mkdir()

    id_map = [{"opaque_id": "id1", "cell": "qwen35_4b", "arm": "baseline", "row_key": "rk1", "is_decoy": False, "decoy_type": None}]
    graded = [{"opaque_id": "MISMATCHED", "is_abstention": False}]
    (analysis_dir / "shards" / "qwen35_4b_shard_00_id_map.jsonl").write_text(json.dumps(id_map[0]) + "\n", encoding="utf-8")
    graded_path = tmp_path / "graded.jsonl"
    graded_path.write_text(json.dumps(graded[0]) + "\n", encoding="utf-8")

    common.write_json(committed_dir / "pool_manifest.json", {"shards": [{"shard_id": "qwen35_4b_shard_00", "cell": "qwen35_4b", "pool_sha256": "x"}]})
    apply_adjudication.cmd_commit_hash(type("A", (), {
        "shard_id": "qwen35_4b_shard_00", "graded_file": str(graded_path), "committed_dir": str(committed_dir)})())

    with pytest.raises(SystemExit, match="opaque_id mismatch"):
        apply_adjudication.evaluate_shard("qwen35_4b_shard_00", {"graded_file": str(graded_path), "attempt": 1},
                                          common.load_json(committed_dir / "pool_manifest.json"), analysis_dir, committed_dir)


# ---------------------------------------------------------------------------
# criterion: P1/P2/P3/S1 branches on hand-computable fixtures
# ---------------------------------------------------------------------------

def _rate(successes, n):
    return common.wilson(successes, n)


def test_p1_passes_on_shape_matching_precedent():
    confab_abstention = _rate(695, 1000)  # 0.695, well above 0.60 floor and LCB > 0.50
    confab_well_formed = _rate(990, 1000)  # 0.99 >= 0.80
    known_false_refusal = _rate(14, 360)  # ~0.039 <= 0.05, UCB well under 0.10
    result = criterion.p1_evaluate(confab_abstention, confab_well_formed, known_false_refusal)
    assert result["passed"] is True


def test_p1_fails_on_cost_ceiling_breach():
    confab_abstention = _rate(695, 1000)
    confab_well_formed = _rate(990, 1000)
    known_false_refusal = _rate(60, 360)  # ~0.167, breaches both ceiling and UCB
    result = criterion.p1_evaluate(confab_abstention, confab_well_formed, known_false_refusal)
    assert result["passed"] is False
    assert result["cost"]["passed"] is False


def test_p1_fails_on_well_formed_floor_breach():
    confab_abstention = _rate(695, 1000)
    confab_well_formed = _rate(700, 1000)  # 0.70 < 0.80 floor
    known_false_refusal = _rate(14, 360)
    result = criterion.p1_evaluate(confab_abstention, confab_well_formed, known_false_refusal)
    assert result["passed"] is False
    assert result["benefit"]["well_formed_pass"] is False


def test_p2_c_hat_evaluate_pass_and_fail():
    passing_ci = {"point": 0.45, "bootstrap_ci_95": [0.30, 0.60], "excludes_zero": True}
    result = criterion.p2_c_hat_evaluate(passing_ci)
    assert result["passed"] is True
    assert result["is_primary_falsifier_trigger"] is False

    failing_ci = {"point": 0.10, "bootstrap_ci_95": [-0.05, 0.25], "excludes_zero": False}
    result_fail = criterion.p2_c_hat_evaluate(failing_ci)
    assert result_fail["passed"] is False
    assert result_fail["is_primary_falsifier_trigger"] is True


def test_p2_random_evaluate_directional_pass_and_confident_negative_fail():
    ok_ci = {"median": 0.02, "bootstrap_ci_95": [-0.01, 0.05]}  # positive median, CI includes 0 -> not confidently negative
    result_ok = criterion.p2_random_evaluate(ok_ci)
    assert result_ok["passed"] is True

    confidently_negative_ci = {"median": -0.08, "bootstrap_ci_95": [-0.15, -0.02]}
    result_bad = criterion.p2_random_evaluate(confidently_negative_ci)
    assert result_bad["passed"] is False
    assert result_bad["is_primary_falsifier_trigger"] is True

    negative_but_inconclusive_ci = {"median": -0.03, "bootstrap_ci_95": [-0.10, 0.04]}
    result_inconclusive = criterion.p2_random_evaluate(negative_but_inconclusive_ci)
    assert result_inconclusive["passed"] is True  # not a confident negative -> does not trigger the falsifier
    assert result_inconclusive["is_primary_falsifier_trigger"] is False


def test_p3_c_hat_evaluate_pass_and_fail():
    passing_ci = {"point": 0.15, "bootstrap_ci_95": [0.08, 0.22], "excludes_zero": True}
    result = criterion.p3_c_hat_evaluate(passing_ci)
    assert result["passed"] is True

    failing_ci = {"point": 0.02, "bootstrap_ci_95": [-0.02, 0.06], "excludes_zero": False}
    result_fail = criterion.p3_c_hat_evaluate(failing_ci)
    assert result_fail["passed"] is False
    assert result_fail["is_primary_falsifier_trigger"] is True


def test_s1_sign_opposition_pass_qwen():
    # qwen census null is negative-median (suppresses); a positive gated lift is sign-opposed.
    result = criterion.s1_evaluate("qwen35_4b", gated_confab_lift_pts=0.40)
    assert result["sign_opposition"] is True
    assert result["passed"] is True


def test_s1_effect_ratio_pass_mistral():
    # mistral census null is positive-median; a same-signed lift needs effect_ratio >= 3.0.
    denom = config.CENSUS_NULL["mistral7b_v03"]["max_abs_delta_frac"]
    big_lift = denom * 3.5  # same sign as positive median, ratio clears 3.0
    result = criterion.s1_evaluate("mistral7b_v03", gated_confab_lift_pts=big_lift)
    assert result["sign_opposition"] is False
    assert result["effect_ratio_pass"] is True
    assert result["passed"] is True


def test_s1_fails_when_neither_condition_holds():
    denom = config.CENSUS_NULL["mistral7b_v03"]["max_abs_delta_frac"]
    small_same_signed_lift = denom * 2.0  # same sign, ratio 2.0 < 3.0 floor (matches RR2/RR3 mistral precedent)
    result = criterion.s1_evaluate("mistral7b_v03", gated_confab_lift_pts=small_same_signed_lift)
    assert result["passed"] is False


def test_falsifier_verdict_rollup():
    p1_pass = {"passed": True}
    p2_pass = {"passed": True, "is_primary_falsifier": False}
    p3_pass = {"passed": True, "is_primary_falsifier": False}
    ok = criterion.falsifier_verdict(p1_pass, p2_pass, p3_pass)
    assert ok["gate_axis_falsified"] is False

    p2_fail = {"passed": False, "is_primary_falsifier": True}
    falsified = criterion.falsifier_verdict(p1_pass, p2_fail, p3_pass)
    assert falsified["gate_axis_falsified"] is True
    assert falsified["gate_contributes_nothing"] is True


# ---------------------------------------------------------------------------
# heldback_decoys: FIT-split decoy source (lead decision, NOTEBOOK.md
# 2026-07-15) -- disjointness, filter logic, and loud-failure-when-absent.
# ---------------------------------------------------------------------------

def test_heldback_decoys_source_rows_disjoint_from_every_scored_row_key():
    """decoy_source_rows(family) must never overlap this experiment's own
    held-out scored population (confab OR known_correct_answered) -- the
    function itself asserts this against the known population, this test
    re-derives it independently against BOTH roles as an outside check."""
    if not (HERE / "analysis" / "staged_inputs").is_dir():
        pytest.skip("staged_inputs not present; run staging.py first")
    for family in config.FAMILIES:
        path = heldback_decoys.DECOY_SOURCE_PATH[family]
        if not path.is_file():
            pytest.skip(f"decoy source file not found at {path} (cross-worktree; build-machine-dependent)")
        rows = heldback_decoys.decoy_source_rows(family)
        assert len(rows) > 0, f"{family}: 0 decoy source rows"
        source_keys = {r["row_key"] for r in rows}
        by_role = row_pool.heldout_row_keys_by_role(family)
        scored_keys = set(by_role["confab"]) | set(by_role["known_correct_answered"])
        overlap = source_keys & scored_keys
        assert not overlap, f"{family}: {len(overlap)} decoy source row_keys overlap a scored row_key: {sorted(overlap)[:5]}"
        assert all(r.get("role") == "known_correct_answered" for r in rows)


def test_heldback_decoys_source_rows_counts_match_provenance():
    """Cross-experiment integrity check (not a synthetic fixture): the
    known_correct_answered FIT-split row counts materialized by the source
    experiments' own docs (qwen35-4b-midband-doubt-snap
    materialize_reused_rows.py: 240; rr3-corrected-placebo-replication
    materialize_rows.py check_heldout_power: 255 known_fit)."""
    expected = {"qwen35_4b": 240, "mistral7b_v03": 255}
    if not (HERE / "analysis" / "staged_inputs").is_dir():
        pytest.skip("staged_inputs not present; run staging.py first")
    for family, n_expected in expected.items():
        path = heldback_decoys.DECOY_SOURCE_PATH[family]
        if not path.is_file():
            pytest.skip(f"decoy source file not found at {path} (cross-worktree; build-machine-dependent)")
        rows = heldback_decoys.decoy_source_rows(family)
        assert len(rows) == n_expected, f"{family}: expected {n_expected} FIT known-correct rows, got {len(rows)}"


def test_heldback_decoys_build_candidates_filter_logic(tmp_path, monkeypatch):
    """Synthetic-fixture test of the committed-answer / non-refused filter,
    isolated from GPU/model/cross-worktree dependencies via monkeypatched
    `ANALYSIS` and `decoy_source_rows`. Reuses the exact grade_row behaviors
    already verified by `test_gen_lib_well_formed_field_present` and
    `test_gen_lib_refusal_detected` above, so this test only has to check
    the NEW filtering/exclusion wiring, not gen_lib's grading semantics."""
    monkeypatch.setattr(heldback_decoys, "ANALYSIS", tmp_path)
    monkeypatch.setattr(heldback_decoys, "decoy_source_rows", lambda family: [
        {"row_key": "d1", "aliases": ["Paris"], "category_canon": "geo", "source": "test", "role": "known_correct_answered"},
        {"row_key": "d2", "aliases": [], "category_canon": "geo", "source": "test", "role": "known_correct_answered"},
        {"row_key": "d3", "aliases": ["Paris"], "category_canon": "geo", "source": "test", "role": "known_correct_answered"},
    ])
    monkeypatch.setattr(row_pool, "heldout_row_keys_by_role", lambda family: {"confab": [], "known_correct_answered": []})

    runlog_dir = tmp_path / "runlog"
    runlog_dir.mkdir(parents=True)
    rows = [
        {"row_key": "d1", "answer_text": '{"answer": "Paris"}', "terminated_naturally": True},  # committed + correct -> QUALIFIES
        {"row_key": "d2", "answer_text": "I don't know the answer to that.", "terminated_naturally": True},  # refused -> EXCLUDED
        {"row_key": "d3", "answer_text": '{"answer": "London"}', "terminated_naturally": True},  # committed but not alias-matched -> EXCLUDED
    ]
    (runlog_dir / "qwen35_4b__decoy_baseline.jsonl").write_text(
        "\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8",
    )

    candidates, counters = heldback_decoys.build_heldback_candidates("qwen35_4b")
    assert [c["row_key"] for c in candidates] == ["d1"]
    assert counters["n_qualifying_heldback_candidates"] == 1
    assert counters["n_excluded_regrade_refused_v2"] == 1
    assert counters["n_excluded_regrade_not_well_formed_correct_v2"] == 1
    assert candidates[0]["provenance"]["origin"] == "decoy_baseline_generation_over_fit_split_known_correct_rows"


def test_heldback_decoys_build_candidates_raises_when_decoy_baseline_runlog_absent(tmp_path, monkeypatch):
    """Loud-failure requirement (module docstring, build_pool.py docstring):
    build_heldback_candidates must SystemExit, never silently return an
    empty pool, when the decoy-baseline GPU pass has not produced a
    runlog yet."""
    if not (HERE / "analysis" / "staged_inputs").is_dir():
        pytest.skip("staged_inputs not present; run staging.py first")
    family = "qwen35_4b"
    path = heldback_decoys.DECOY_SOURCE_PATH[family]
    if not path.is_file():
        pytest.skip(f"decoy source file not found at {path} (cross-worktree; build-machine-dependent)")
    monkeypatch.setattr(heldback_decoys, "ANALYSIS", tmp_path)  # empty tmp dir: no runlog/<family>__decoy_baseline.jsonl
    with pytest.raises(SystemExit):
        heldback_decoys.build_heldback_candidates(family)


def test_heldback_decoys_source_rows_raises_when_source_file_missing(tmp_path, monkeypatch):
    monkeypatch.setitem(heldback_decoys.DECOY_SOURCE_PATH, "qwen35_4b", tmp_path / "does_not_exist.jsonl")
    with pytest.raises(SystemExit):
        heldback_decoys.decoy_source_rows("qwen35_4b")


# ---------------------------------------------------------------------------
# containment: no free text in any committed JSON currently on disk
# ---------------------------------------------------------------------------

_FORBIDDEN_KEYS = {"answer_text", "question", "aliases", "answer_value", "text"}


def test_no_forbidden_text_keys_in_committed_json():
    committed_dir = HERE / "analysis-committed"
    if not committed_dir.is_dir():
        pytest.skip("analysis-committed not present yet")

    def _walk(obj, path):
        if isinstance(obj, dict):
            for k, v in obj.items():
                assert k not in _FORBIDDEN_KEYS, f"forbidden key {k!r} found at {path}.{k} in a committed file"
                _walk(v, f"{path}.{k}")
        elif isinstance(obj, list):
            for i, v in enumerate(obj):
                _walk(v, f"{path}[{i}]")

    for path in committed_dir.glob("*.json"):
        payload = json.loads(path.read_text(encoding="utf-8"))
        _walk(payload, path.name)


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
