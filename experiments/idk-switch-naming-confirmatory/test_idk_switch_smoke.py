"""Synthetic-fixture smoke tests for the idk-switch-naming-confirmatory
harness. No real generation text or real naming-battery data is read here
except where a test explicitly targets THIS cell's own committed
`cell.yaml` (to prove the real, currently-DRAFT config fails closed).

Per the harness-build assignment, this covers: the seed fail-closed guard
(unset and collision cases), arm config completeness, screen priority,
decoy sourcing from fresh F4 positives only, the empty-text fail-closed
guard, and N1/N2/N3 arithmetic on hand-computed fixtures.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))

import axis_n1n2n3_arithmetic  # noqa: E402
import build_judge_pool  # noqa: E402
import pipeline  # noqa: E402
import screen_lib  # noqa: E402
import stats_lib  # noqa: E402


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row) + "\n")


# ---------------------------------------------------------------------------
# 1. Seed fail-closed guard (unset and collision cases)
# ---------------------------------------------------------------------------

def _base_cell_cfg(**gen_overrides) -> dict:
    gen = {
        "decode_mode": "greedy", "do_sample": False,
        "temperature": "REGISTERED_AT_SIGN", "top_p": "REGISTERED_AT_SIGN",
        "min_new_tokens": 1, "max_new_tokens": 200, "batch_size": 8,
    }
    gen.update(gen_overrides)
    return {"surface": {"generation": gen, "seeds": {"generation_sampling_seed": 99999999}}}


def test_seed_unset_refuses():
    cfg = _base_cell_cfg()
    cfg["surface"]["seeds"]["generation_sampling_seed"] = "REGISTERED_AT_SIGN"
    with pytest.raises(SystemExit, match="REGISTERED_AT_SIGN"):
        pipeline.resolve_generation_config(cfg)


def test_seed_none_refuses():
    cfg = _base_cell_cfg()
    cfg["surface"]["seeds"]["generation_sampling_seed"] = None
    with pytest.raises(SystemExit, match="REGISTERED_AT_SIGN"):
        pipeline.resolve_generation_config(cfg)


@pytest.mark.parametrize("collision_seed", sorted(pipeline.NAMING_BATTERY_EXCLUDED_SEEDS))
def test_seed_collision_with_naming_battery_refuses(collision_seed):
    cfg = _base_cell_cfg()
    cfg["surface"]["seeds"]["generation_sampling_seed"] = collision_seed
    with pytest.raises(SystemExit, match="naming battery"):
        pipeline.resolve_generation_config(cfg)


def test_seed_fresh_and_greedy_resolves():
    cfg = _base_cell_cfg()
    cfg["surface"]["seeds"]["generation_sampling_seed"] = 20260801  # not a naming-battery seed
    resolved = pipeline.resolve_generation_config(cfg)
    assert resolved["generation_sampling_seed"] == 20260801
    assert resolved["decode_mode"] == "greedy"
    assert resolved["do_sample"] is False


def test_decode_mode_inconsistent_with_do_sample_refuses():
    cfg = _base_cell_cfg(decode_mode="greedy", do_sample=True)
    cfg["surface"]["seeds"]["generation_sampling_seed"] = 1
    with pytest.raises(SystemExit, match="inconsistent"):
        pipeline.resolve_generation_config(cfg)


def test_sampled_without_temperature_refuses():
    cfg = _base_cell_cfg(decode_mode="sampled", do_sample=True, temperature="REGISTERED_AT_SIGN")
    cfg["surface"]["seeds"]["generation_sampling_seed"] = 1
    with pytest.raises(SystemExit, match="REGISTERED_AT_SIGN"):
        pipeline.resolve_generation_config(cfg)


def test_sampled_with_temperature_and_top_p_resolves():
    cfg = _base_cell_cfg(decode_mode="sampled", do_sample=True, temperature=0.7, top_p=0.9)
    cfg["surface"]["seeds"]["generation_sampling_seed"] = 1
    resolved = pipeline.resolve_generation_config(cfg)
    assert resolved["decode_mode"] == "sampled"
    assert resolved["temperature"] == 0.7
    assert resolved["top_p"] == 0.9


def test_real_cell_yaml_resolves_to_the_proposed_registration():
    """The lead resolved the generation block on 2026-07-31 (Build-time
    ruling 1: sampled decode per the SR registered standard; ruling 6: seed
    20260802). This test pins the actual cell.yaml to exactly those proposed
    values so any drift between now and sign is caught."""
    cell_cfg = yaml.safe_load((Path(__file__).resolve().parent / "cell.yaml").read_text())
    resolved = pipeline.resolve_generation_config(cell_cfg)
    assert resolved == {
        "decode_mode": "sampled",
        "do_sample": True,
        "temperature": 0.7,
        "top_p": 0.9,
        "generation_sampling_seed": 20260802,
    }


def test_unsigned_cell_refuses_at_provenance_gate(tmp_path, monkeypatch):
    """Pre-sign launch protection: with instrument.runtime_image_digest unset
    (it is only written at sign), read_container_provenance must hard-refuse
    even when a provenance script exists and reports a real sha256 digest, so
    no GPU verb can run on the unsigned cell."""
    script = tmp_path / "synaptic-tuner" / "docker" / "mechinterp-runner" / "print_provenance.py"
    script.parent.mkdir(parents=True)
    script.write_text(
        "import json; print(json.dumps({'event': 'mechinterp_runner_provenance',"
        " 'image_digest': 'sha256:' + 'ab' * 32}))\n"
    )
    monkeypatch.setattr(pipeline, "REPO_ROOT", tmp_path, raising=True)
    with pytest.raises(SystemExit, match="runtime_image_digest"):
        pipeline.read_container_provenance()


# ---------------------------------------------------------------------------
# 2. Arm config completeness
# ---------------------------------------------------------------------------

def test_arms_are_the_registered_reduced_ladder():
    names = {arm["name"] for arm in pipeline.ARMS}
    assert names == {"a_baseline", "a_dose_0p5", "a_dose_1", "a_placebo_1"}
    by_name = {arm["name"]: arm for arm in pipeline.ARMS}
    assert by_name["a_baseline"]["multiplier"] == 0.0
    assert by_name["a_baseline"]["readout"] == "c_hat"
    assert by_name["a_dose_0p5"]["multiplier"] == 0.5
    assert by_name["a_dose_0p5"]["readout"] == "c_hat"
    assert by_name["a_dose_1"]["multiplier"] == 1.0
    assert by_name["a_dose_1"]["readout"] == "c_hat"
    assert by_name["a_placebo_1"]["multiplier"] == 1.0
    assert by_name["a_placebo_1"]["readout"] == "random_direction"
    assert all(arm["population"] == "P_CONFAB" for arm in pipeline.ARMS)


def test_screen_lib_arm_keys_match_pipeline_arms():
    assert set(screen_lib.ALL_ARM_KEYS) == {arm["name"] for arm in pipeline.ARMS}


def test_cell_yaml_arms_match_pipeline_arms():
    cell_cfg = yaml.safe_load((Path(__file__).resolve().parent / "cell.yaml").read_text())
    assert set(cell_cfg["arms"].keys()) == {arm["name"] for arm in pipeline.ARMS}
    for arm in pipeline.ARMS:
        cy = cell_cfg["arms"][arm["name"]]
        assert cy["population"] == arm["population"]
        assert cy["readout"] == arm["readout"]
        assert cy["multiplier"] == arm["multiplier"]


# ---------------------------------------------------------------------------
# 3. Screen priority order
# ---------------------------------------------------------------------------

def test_screen_priority_f5_beats_f4():
    row = {"degenerate": True, "semantic_refuse": True, "refused_v2": True}
    assert screen_lib.classify_screen(row) == screen_lib.F5_DEGENERATE


def test_screen_priority_f4_via_semantic_refuse():
    row = {"degenerate": False, "semantic_refuse": True, "refused_v2": False}
    assert screen_lib.classify_screen(row) == screen_lib.F4_EXPLICIT_IDK


def test_screen_priority_f4_via_refused_v2():
    row = {"degenerate": False, "semantic_refuse": False, "refused_v2": True}
    assert screen_lib.classify_screen(row) == screen_lib.F4_EXPLICIT_IDK


def test_screen_priority_screened_in_remainder():
    row = {"degenerate": False, "semantic_refuse": False, "refused_v2": False}
    assert screen_lib.classify_screen(row) == screen_lib.SCREENED_IN


# ---------------------------------------------------------------------------
# 4. Decoy sourcing from fresh F4 positives only
# ---------------------------------------------------------------------------

def test_decoy_sourcing_populations(tmp_path: Path):
    runlog_dir = tmp_path / "runlog"
    write_jsonl(runlog_dir / "a_baseline.jsonl", [
        {"row_key": "f4-row", "arm": "a_baseline", "answer_text": "I don't know",
         "degenerate": False, "semantic_refuse": True, "refused_v2": False},
        {"row_key": "core-row", "arm": "a_baseline", "answer_text": "a committed answer",
         "degenerate": False, "semantic_refuse": False, "refused_v2": False},
        {"row_key": "degenerate-row", "arm": "a_baseline", "answer_text": "",
         "degenerate": True, "semantic_refuse": False, "refused_v2": False},
    ])
    write_jsonl(runlog_dir / "a_dose_1.jsonl", [
        {"row_key": "core-row-2", "arm": "a_dose_1", "answer_text": "another answer",
         "degenerate": False, "semantic_refuse": False, "refused_v2": False},
    ])

    core_by_arm, clear_pos, report = build_judge_pool.build_candidate_populations(runlog_dir)

    assert {r["row_key"] for r in clear_pos} == {"f4-row"}
    assert "core-row" not in {r["row_key"] for r in clear_pos}
    assert "degenerate-row" not in {r["row_key"] for r in clear_pos}
    assert {r["row_key"] for r in core_by_arm["a_baseline"]} == {"core-row"}
    assert {r["row_key"] for r in core_by_arm["a_dose_1"]} == {"core-row-2"}
    assert report["n_clear_positive_candidates_total"] == 1
    assert report["n_core_candidates_total"] == 2


def test_build_full_pool_decoys_embedded_and_tagged(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(build_judge_pool, "SHARDS_DIR", tmp_path / "shards")
    core_by_arm = {
        "a_baseline": [{"row_key": "c1", "arm": "a_baseline", "text": "committed one"}],
        "a_dose_0p5": [], "a_dose_1": [], "a_placebo_1": [],
    }
    decoys = [{"row_key": "d1", "arm": "a_dose_1", "text": "I don't know the answer"}]
    shards = build_judge_pool.build_full_pool_shards_with_decoys(core_by_arm, decoys, n_shards=1, seed=1, salt="salt")
    assert len(shards) == 1
    id_map = shards[0]["id_map"]
    decoy_entries = [m for m in id_map if m["is_decoy"]]
    core_entries = [m for m in id_map if not m["is_decoy"]]
    assert len(decoy_entries) == 1
    assert decoy_entries[0]["decoy_type"] == "clear_positive"
    assert decoy_entries[0]["row_key"] == "d1"
    assert len(core_entries) == 1
    assert core_entries[0]["row_key"] == "c1"


# ---------------------------------------------------------------------------
# 5. Empty-text fail-closed guard
# ---------------------------------------------------------------------------

def test_write_shards_refuses_empty_text(tmp_path, monkeypatch):
    monkeypatch.setattr(build_judge_pool, "SHARDS_DIR", tmp_path / "shards")
    shards = [{
        "shard_id": "s00",
        "blinded_pool": [
            {"opaque_id": "aa", "text": "a real answer"},
            {"opaque_id": "bb", "text": "   "},
        ],
        "id_map": [], "n_core": 2, "n_decoy_clear_positive": 0,
    }]
    with pytest.raises(SystemExit):
        build_judge_pool.write_shards(shards)
    assert not (tmp_path / "shards").exists()


def test_write_shards_accepts_nonempty_text(tmp_path, monkeypatch):
    monkeypatch.setattr(build_judge_pool, "SHARDS_DIR", tmp_path / "shards")
    shards = [{
        "shard_id": "s00",
        "blinded_pool": [{"opaque_id": "aa", "text": "a real answer"}],
        "id_map": [{"opaque_id": "aa", "row_key": "r0", "arm": "a_baseline", "is_decoy": False, "decoy_type": None}],
        "n_core": 1, "n_decoy_clear_positive": 0,
    }]
    entries = build_judge_pool.write_shards(shards)
    assert len(entries) == 1
    assert (tmp_path / "shards" / "s00.jsonl").is_file()


# ---------------------------------------------------------------------------
# 6. N1/N2/N3 arithmetic on hand-computed fixtures
# ---------------------------------------------------------------------------

def test_wilson_matches_known_values():
    # 50/100: Wilson center should sit near 0.5, CI roughly symmetric.
    w = stats_lib.wilson(50, 100)
    assert w["rate"] == pytest.approx(0.5)
    assert w["wilson_ci_95"][0] < 0.5 < w["wilson_ci_95"][1]


def test_wilson_zero_n():
    w = stats_lib.wilson(0, 0)
    assert w["rate"] == 0.0
    assert w["wilson_ci_95"] == [0.0, 0.0]


def test_bootstrap_paired_diff_ci_point_estimate_hand_computed():
    # 4 rows: baseline all False, dosed all True -> point diff must be 1.0
    # regardless of resample draws, and the CI must be degenerate [1.0, 1.0].
    flags_a = [False, False, False, False]
    flags_b = [True, True, True, True]
    result = stats_lib.bootstrap_paired_diff_ci(flags_a, flags_b, n_resamples=500, seed=42)
    assert result["point_diff"] == pytest.approx(1.0)
    assert result["bootstrap_ci"][0] == pytest.approx(1.0)
    assert result["bootstrap_ci"][1] == pytest.approx(1.0)


def test_bootstrap_paired_diff_ci_zero_diff_hand_computed():
    flags_a = [True, False, True, False]
    flags_b = [True, False, True, False]  # identical -> point diff 0, CI collapses to 0
    result = stats_lib.bootstrap_paired_diff_ci(flags_a, flags_b, n_resamples=500, seed=1)
    assert result["point_diff"] == pytest.approx(0.0)
    assert result["bootstrap_ci"][0] == pytest.approx(0.0)
    assert result["bootstrap_ci"][1] == pytest.approx(0.0)


def test_bootstrap_paired_diff_ci_deterministic_given_seed():
    flags_a = [True, False, True, False, True]
    flags_b = [False, True, True, False, False]
    r1 = stats_lib.bootstrap_paired_diff_ci(flags_a, flags_b, n_resamples=200, seed=7)
    r2 = stats_lib.bootstrap_paired_diff_ci(flags_a, flags_b, n_resamples=200, seed=7)
    assert r1["bootstrap_ci"] == r2["bootstrap_ci"]


def test_n1_or_n3_rate_diff_hand_computed():
    # baseline: 1/4 F4; dosed: 3/4 F4 -> point diff = 0.5
    flags_by_arm = {
        "a_baseline": {
            "r0": {"f5_degenerate": False, "f4_explicit_idk": True, "screened_in": False},
            "r1": {"f5_degenerate": False, "f4_explicit_idk": False, "screened_in": True},
            "r2": {"f5_degenerate": False, "f4_explicit_idk": False, "screened_in": True},
            "r3": {"f5_degenerate": False, "f4_explicit_idk": False, "screened_in": True},
        },
        "a_dose_1": {
            "r0": {"f5_degenerate": False, "f4_explicit_idk": True, "screened_in": False},
            "r1": {"f5_degenerate": False, "f4_explicit_idk": True, "screened_in": False},
            "r2": {"f5_degenerate": False, "f4_explicit_idk": True, "screened_in": False},
            "r3": {"f5_degenerate": False, "f4_explicit_idk": False, "screened_in": True},
        },
    }
    result = axis_n1n2n3_arithmetic.n1_or_n3_rate_diff(flags_by_arm, "a_baseline", "a_dose_1", bootstrap_seed=0)
    assert result["n_common_row_keys"] == 4
    assert result["rate_a"]["rate"] == pytest.approx(0.25)
    assert result["rate_b"]["rate"] == pytest.approx(0.75)
    assert result["point_diff_b_minus_a"] == pytest.approx(0.5)
    assert result["bootstrap_diff_ci"]["point_diff"] == pytest.approx(0.5)


def test_n1_or_n3_rate_diff_reports_missing_row_keys_not_silent():
    flags_by_arm = {
        "a_baseline": {"r0": {"f5_degenerate": False, "f4_explicit_idk": False, "screened_in": True}},
        "a_dose_1": {
            "r0": {"f5_degenerate": False, "f4_explicit_idk": True, "screened_in": False},
            "r1": {"f5_degenerate": False, "f4_explicit_idk": True, "screened_in": False},
        },
    }
    result = axis_n1n2n3_arithmetic.n1_or_n3_rate_diff(flags_by_arm, "a_baseline", "a_dose_1", bootstrap_seed=0)
    assert result["n_common_row_keys"] == 1
    assert result["n_missing_from_a"] == 1  # r1 present in a_dose_1, missing from a_baseline


def test_n2_f2f3_shares_hand_computed():
    # baseline: 10 rows, 8 screened-in (F1=6, F2=2, F3=0), 2 F4, 0 F5.
    #   non_degenerate = 6+2+0+2 = 10; share = (2+0)/10 = 0.2
    # a_dose_0p5: 10 rows, 8 screened-in (F1=2, F2=3, F3=3), 2 F4, 0 F5.
    #   non_degenerate = 2+3+3+2 = 10; share = 6/10 = 0.6; delta over baseline = 0.4 -> rises
    flags_by_arm = {}
    for arm, n_f4 in (("a_baseline", 2), ("a_dose_0p5", 2), ("a_dose_1", 0), ("a_placebo_1", 0)):
        rows = {}
        for i in range(n_f4):
            rows[f"{arm}_f4_{i}"] = {"f5_degenerate": False, "f4_explicit_idk": True, "screened_in": False}
        for i in range(8):
            rows[f"{arm}_si_{i}"] = {"f5_degenerate": False, "f4_explicit_idk": False, "screened_in": True}
        flags_by_arm[arm] = rows

    payload_rows = []
    for i in range(6):
        payload_rows.append({"row_key": f"a_baseline_si_{i}", "arm": "a_baseline", "form_label": "F1"})
    for i in range(6, 8):
        payload_rows.append({"row_key": f"a_baseline_si_{i}", "arm": "a_baseline", "form_label": "F2"})
    for i in range(2):
        payload_rows.append({"row_key": f"a_dose_0p5_si_{i}", "arm": "a_dose_0p5", "form_label": "F1"})
    for i in range(2, 5):
        payload_rows.append({"row_key": f"a_dose_0p5_si_{i}", "arm": "a_dose_0p5", "form_label": "F2"})
    for i in range(5, 8):
        payload_rows.append({"row_key": f"a_dose_0p5_si_{i}", "arm": "a_dose_0p5", "form_label": "F3"})
    for i in range(8):
        payload_rows.append({"row_key": f"a_dose_1_si_{i}", "arm": "a_dose_1", "form_label": "F1"})
    for i in range(8):
        payload_rows.append({"row_key": f"a_placebo_1_si_{i}", "arm": "a_placebo_1", "form_label": "F1"})

    result = axis_n1n2n3_arithmetic.n2_f2f3_shares(flags_by_arm, payload_rows)
    assert result["baseline_share"] == pytest.approx(0.2)
    assert result["per_arm"]["a_baseline"]["screened_vs_graded_mismatch"] is False
    dose_0p5 = result["per_dosed_arm"]["a_dose_0p5"]
    assert dose_0p5["share"] == pytest.approx(0.6)
    assert dose_0p5["delta_over_baseline"] == pytest.approx(0.4)
    assert dose_0p5["rises_0p10_or_more_over_baseline"] is True
    dose_1 = result["per_dosed_arm"]["a_dose_1"]
    assert dose_1["share"] == pytest.approx(0.0)
    assert dose_1["rises_0p10_or_more_over_baseline"] is False


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
