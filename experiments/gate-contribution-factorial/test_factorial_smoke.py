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


def test_load_heldback_candidates_raises_loudly_when_missing():
    """See build_pool.py / heldback_decoys.py module docstrings: this
    experiment's full-known-pool design structurally leaves zero held-back
    candidates, so the loader must raise loudly rather than silently
    degrade -- verified here against whatever (missing or empty) runlog
    state currently exists in this worktree."""
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
