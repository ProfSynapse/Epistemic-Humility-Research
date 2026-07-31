"""Synthetic-fixture smoke tests for the form-judge-axis-g-rescore harness.

No real naming-battery data is read here -- every fixture is fabricated
inline. Per the harness-build assignment, this covers: screen priority
order, spent-slice exclusion, decoy sourcing from the right populations,
positional-join mismatch raising, unblind-before-hash refusal, and the
direction-breakdown arithmetic. A couple of extra axis-arithmetic checks are
included since that module is cheap to exercise with synthetic counts.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

import apply_judge_grades  # noqa: E402
import axis_g_arithmetic  # noqa: E402
import build_judge_pool  # noqa: E402
import screen_lib  # noqa: E402


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row) + "\n")


# ---------------------------------------------------------------------------
# 1. Screen priority order
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
# 2. Spent-slice exclusion
# ---------------------------------------------------------------------------

def test_spent_slice_exclusion(tmp_path: Path):
    runlog_dir = tmp_path / "runlog"
    spent_dir = tmp_path / "spent_shards"
    c_baseline = tmp_path / "c_baseline.jsonl"
    write_jsonl(c_baseline, [])

    write_jsonl(runlog_dir / "a_baseline.jsonl", [
        {"row_key": "spent-1", "arm": "a_baseline", "answer_text": "spent row",
         "degenerate": False, "semantic_refuse": False, "refused_v2": False},
        {"row_key": "fresh-1", "arm": "a_baseline", "answer_text": "fresh row",
         "degenerate": False, "semantic_refuse": False, "refused_v2": False},
    ])
    # naming battery's spent id_map, unblinded, on disk already (gitignored).
    write_jsonl(spent_dir / "shard_00_id_map.jsonl", [
        {"opaque_id": "abc123", "row_key": "spent-1", "arm": "a_baseline",
         "is_decoy": False, "decoy_type": None},
    ])

    core_by_arm, _, _, report = build_judge_pool.build_candidate_populations(runlog_dir, c_baseline, spent_dir)

    core_row_keys = {r["row_key"] for r in core_by_arm["a_baseline"]}
    assert "spent-1" not in core_row_keys
    assert "fresh-1" in core_row_keys
    assert report["n_core_excluded_as_spent"] == 1
    assert report["n_spent_pairs_total"] == 1


def test_spent_slice_exclusion_is_arm_scoped(tmp_path: Path):
    """A row_key spent in one arm must NOT be excluded from a different arm
    -- the naming battery's own id_map shows the same row_key recurring
    across dosed sub-arms as the SAME underlying prompt at different doses,
    each a distinct generation the lead did not necessarily see."""
    runlog_dir = tmp_path / "runlog"
    spent_dir = tmp_path / "spent_shards"
    c_baseline = tmp_path / "c_baseline.jsonl"
    write_jsonl(c_baseline, [])

    write_jsonl(runlog_dir / "a_baseline.jsonl", [
        {"row_key": "shared-key", "arm": "a_baseline", "answer_text": "baseline text",
         "degenerate": False, "semantic_refuse": False, "refused_v2": False},
    ])
    write_jsonl(runlog_dir / "a_dose_1.jsonl", [
        {"row_key": "shared-key", "arm": "a_dose_1", "answer_text": "dosed text",
         "degenerate": False, "semantic_refuse": False, "refused_v2": False},
    ])
    write_jsonl(spent_dir / "shard_00_id_map.jsonl", [
        {"opaque_id": "abc123", "row_key": "shared-key", "arm": "a_baseline",
         "is_decoy": False, "decoy_type": None},
    ])

    core_by_arm, _, _, _ = build_judge_pool.build_candidate_populations(runlog_dir, c_baseline, spent_dir)

    assert not any(r["row_key"] == "shared-key" for r in core_by_arm["a_baseline"])
    assert any(r["row_key"] == "shared-key" for r in core_by_arm["a_dose_1"])


# ---------------------------------------------------------------------------
# 3. Decoy sourcing from the right populations
# ---------------------------------------------------------------------------

def test_decoy_sourcing_populations(tmp_path: Path):
    runlog_dir = tmp_path / "runlog"
    spent_dir = tmp_path / "spent_shards"  # left empty: no exclusions
    c_baseline = tmp_path / "c_baseline.jsonl"

    write_jsonl(runlog_dir / "a_baseline.jsonl", [
        {"row_key": "f4-row", "arm": "a_baseline", "answer_text": "I don't know",
         "degenerate": False, "semantic_refuse": True, "refused_v2": False},
        {"row_key": "core-row", "arm": "a_baseline", "answer_text": "a committed answer",
         "degenerate": False, "semantic_refuse": False, "refused_v2": False},
        {"row_key": "degenerate-row", "arm": "a_baseline", "answer_text": "",
         "degenerate": True, "semantic_refuse": False, "refused_v2": False},
    ])
    write_jsonl(c_baseline, [
        {"row_key": "c-correct", "arm": "c_baseline", "answer_text": "Paris", "correct_v2": True},
        {"row_key": "c-wrong", "arm": "c_baseline", "answer_text": "London", "correct_v2": False},
        {"row_key": "c-null", "arm": "c_baseline", "answer_text": "unsure", "correct_v2": None},
    ])

    core_by_arm, clear_pos, clear_neg, report = build_judge_pool.build_candidate_populations(runlog_dir, c_baseline, spent_dir)

    # clear-positive decoys: F4 screen positives only, never core or degenerate rows.
    assert {r["row_key"] for r in clear_pos} == {"f4-row"}
    assert "core-row" not in {r["row_key"] for r in clear_pos}
    assert "degenerate-row" not in {r["row_key"] for r in clear_pos}

    # clear-negative lane REMOVED (governed deviation, PI-approved
    # 2026-07-30): the registered Arm C source retains no generation text
    # (metrics-only runlog; the original synthetic fixture here gave it an
    # answer_text field the real data never had, which is how the empty-text
    # bug slipped past this suite). The builder must return NO clear-negative
    # candidates even when the runlog rows carry text.
    assert clear_neg == []

    # core candidates: the screened-in remainder, neither F4 nor F5.
    assert {r["row_key"] for r in core_by_arm["a_baseline"]} == {"core-row"}

    # Counters are inert now the lane is removed; kept in the report shape
    # for manifest continuity, always zero.
    assert report["n_c_baseline_rows_total"] == 0
    assert report["n_c_baseline_correct_v2_true"] == 0


# ---------------------------------------------------------------------------
# 4. Positional-join mismatch raises
# ---------------------------------------------------------------------------

def _commit(analysis_dir: Path, shard_id: str, role: str, graded_path: Path) -> None:
    manifest = apply_judge_grades.load_graded_manifest(analysis_dir)
    manifest.append({
        "shard_id": shard_id, "role": role,
        "sha256": apply_judge_grades.sha256_of_file(graded_path),
        "file_name": graded_path.name, "committed_at": "test",
    })
    apply_judge_grades.write_json(apply_judge_grades.graded_manifest_path(analysis_dir), manifest)


def test_positional_join_mismatch_raises(tmp_path: Path):
    analysis_dir = tmp_path / "analysis"
    id_map = [
        {"opaque_id": "id-0", "row_key": "r0", "arm": "a_baseline", "is_decoy": False, "decoy_type": None},
        {"opaque_id": "id-1", "row_key": "r1", "arm": "a_baseline", "is_decoy": False, "decoy_type": None},
    ]
    graded_path = tmp_path / "graded.jsonl"
    # Mismatched: only one line for a two-row id_map.
    write_jsonl(graded_path, [{"opaque_id": "id-0", "form_label": "F1"}])
    _commit(analysis_dir, "shard_00", "judge", graded_path)

    with pytest.raises(SystemExit, match="positional"):
        apply_judge_grades._load_and_validate_graded("shard_00", "judge", graded_path, id_map, analysis_dir)


def test_positional_join_reordered_opaque_id_raises(tmp_path: Path):
    analysis_dir = tmp_path / "analysis"
    id_map = [
        {"opaque_id": "id-0", "row_key": "r0", "arm": "a_baseline", "is_decoy": False, "decoy_type": None},
        {"opaque_id": "id-1", "row_key": "r1", "arm": "a_baseline", "is_decoy": False, "decoy_type": None},
    ]
    graded_path = tmp_path / "graded.jsonl"
    # Same count, but line 0/1 swapped relative to id_map order.
    write_jsonl(graded_path, [
        {"opaque_id": "id-1", "form_label": "F1"},
        {"opaque_id": "id-0", "form_label": "F2"},
    ])
    _commit(analysis_dir, "shard_00", "judge", graded_path)

    with pytest.raises(SystemExit, match="opaque_id mismatch"):
        apply_judge_grades._load_and_validate_graded("shard_00", "judge", graded_path, id_map, analysis_dir)


# ---------------------------------------------------------------------------
# 5. Unblind-before-hash refusal
# ---------------------------------------------------------------------------

def test_unblind_before_hash_refusal(tmp_path: Path):
    analysis_dir = tmp_path / "analysis"
    id_map = [{"opaque_id": "id-0", "row_key": "r0", "arm": "a_baseline", "is_decoy": False, "decoy_type": None}]
    graded_path = tmp_path / "graded.jsonl"
    write_jsonl(graded_path, [{"opaque_id": "id-0", "form_label": "F1"}])
    # NOTE: no _commit() call -- hash was never committed.

    with pytest.raises(SystemExit, match="UNBLINDING REFUSED"):
        apply_judge_grades._load_and_validate_graded("shard_00", "judge", graded_path, id_map, analysis_dir)


def test_unblind_refusal_is_role_scoped(tmp_path: Path):
    """Committing the judge's hash must not authorize unblinding the
    adjudicator's grading for the same shard -- each role's hash is tracked
    and required independently."""
    analysis_dir = tmp_path / "analysis"
    id_map = [{"opaque_id": "id-0", "row_key": "r0", "arm": "a_baseline", "is_decoy": False, "decoy_type": None}]
    judge_graded = tmp_path / "judge.jsonl"
    adjudicator_graded = tmp_path / "adjudicator.jsonl"
    write_jsonl(judge_graded, [{"opaque_id": "id-0", "form_label": "F1"}])
    write_jsonl(adjudicator_graded, [{"opaque_id": "id-0", "form_label": "F2"}])
    _commit(analysis_dir, "shard_00", "judge", judge_graded)

    # judge role: fine.
    apply_judge_grades._load_and_validate_graded("shard_00", "judge", judge_graded, id_map, analysis_dir)
    # adjudicator role: not yet committed, must refuse.
    with pytest.raises(SystemExit, match="UNBLINDING REFUSED"):
        apply_judge_grades._load_and_validate_graded("shard_00", "adjudicator", adjudicator_graded, id_map, analysis_dir)


# ---------------------------------------------------------------------------
# 6. Direction-breakdown arithmetic
# ---------------------------------------------------------------------------

def test_direction_breakdown_arithmetic(tmp_path: Path):
    analysis_dir = tmp_path / "analysis"
    shard_id = "shard_00"
    id_map = [
        {"opaque_id": "id-0", "row_key": "r0", "arm": "a_dose_0p5", "is_decoy": False, "decoy_type": None},
        {"opaque_id": "id-1", "row_key": "r1", "arm": "a_dose_0p5", "is_decoy": False, "decoy_type": None},
        {"opaque_id": "id-2", "row_key": "r2", "arm": "a_dose_0p5", "is_decoy": False, "decoy_type": None},
        {"opaque_id": "id-3", "row_key": "decoy-pos", "arm": "a_placebo_1", "is_decoy": True, "decoy_type": "clear_positive"},
        {"opaque_id": "id-4", "row_key": "decoy-neg", "arm": "c_baseline", "is_decoy": True, "decoy_type": "clear_negative"},
    ]
    write_jsonl(analysis_dir / "shards" / f"{shard_id}_id_map.jsonl", id_map)

    judge_graded = tmp_path / "judge.jsonl"
    adjudicator_graded = tmp_path / "adjudicator.jsonl"
    # row0: judge F1, adjudicator F2 -> disagree, direction F1->F2
    # row1: judge F2, adjudicator F2 -> agree, direction F2->F2
    # row2: judge F3, adjudicator F3 -> agree, direction F3->F3
    # decoy-pos: judge correctly says not-F1 (F2) -> agrees decoy
    # decoy-neg: judge correctly says F1 -> agrees decoy
    write_jsonl(judge_graded, [
        {"opaque_id": "id-0", "form_label": "F1"},
        {"opaque_id": "id-1", "form_label": "F2"},
        {"opaque_id": "id-2", "form_label": "F3"},
        {"opaque_id": "id-3", "form_label": "F2"},
        {"opaque_id": "id-4", "form_label": "F1"},
    ])
    write_jsonl(adjudicator_graded, [
        {"opaque_id": "id-0", "form_label": "F2"},
        {"opaque_id": "id-1", "form_label": "F2"},
        {"opaque_id": "id-2", "form_label": "F3"},
        {"opaque_id": "id-3", "form_label": "F3"},
        {"opaque_id": "id-4", "form_label": "F1"},
    ])
    _commit(analysis_dir, shard_id, "judge", judge_graded)
    _commit(analysis_dir, shard_id, "adjudicator", adjudicator_graded)

    pool_manifest = {"shards": [{"shard_id": shard_id, "pool_sha256": "unused-pool-not-written"}]}
    result = apply_judge_grades.evaluate_calibration_shard(
        shard_id,
        {"graded_file": str(judge_graded)}, {"graded_file": str(adjudicator_graded)},
        pool_manifest, analysis_dir,
    )

    assert result["n_core"] == 3
    assert result["n_disagree"] == 1
    assert result["direction_counts"] == {"F1->F2": 1, "F2->F2": 1, "F3->F3": 1}
    assert result["n_decoy_clear_positive"] == 1
    assert result["n_decoy_clear_positive_agree"] == 1
    assert result["n_decoy_clear_negative"] == 1
    assert result["n_decoy_clear_negative_agree"] == 1


def test_direction_breakdown_pooled_across_shards():
    shard_a = {
        "n_core": 2, "n_disagree": 1,
        "n_decoy_clear_positive": 0, "n_decoy_clear_positive_agree": 0,
        "n_decoy_clear_negative": 0, "n_decoy_clear_negative_agree": 0,
        "direction_counts": {"F1->F2": 1, "F1->F1": 1},
    }
    shard_b = {
        "n_core": 1, "n_disagree": 0,
        "n_decoy_clear_positive": 0, "n_decoy_clear_positive_agree": 0,
        "n_decoy_clear_negative": 0, "n_decoy_clear_negative_agree": 0,
        "direction_counts": {"F1->F1": 1},
    }
    pooled = apply_judge_grades.pooled_calibration_verdict([shard_a, shard_b])
    assert pooled["direction_counts_pooled"] == {"F1->F2": 1, "F1->F1": 2}
    assert pooled["n_core_total"] == 3
    assert pooled["disagreement_rate"] == pytest.approx(1 / 3)


# ---------------------------------------------------------------------------
# Extra: axis-G share arithmetic (cheap, synthetic counts only)
# ---------------------------------------------------------------------------

def test_axis_g_share_and_verdict():
    screen_counts = {"per_arm": {
        "a_baseline": {"n_total": 100, "n_f5_degenerate": 0, "n_f4_explicit_idk": 10, "n_screened_in": 90},
        "a_dose_0p5": {"n_total": 100, "n_f5_degenerate": 0, "n_f4_explicit_idk": 10, "n_screened_in": 90},
    }}
    # baseline: 90 screened-in, non-degenerate = 100; F2+F3 share small.
    # a_dose_0p5: F2+F3 share large, clearing both the floor and the over-baseline leg.
    graded_rows = (
        [{"row_key": f"b{i}", "arm": "a_baseline", "form_label": "F1"} for i in range(85)]
        + [{"row_key": f"b{i}", "arm": "a_baseline", "form_label": "F2"} for i in range(5)]
        + [{"row_key": f"d{i}", "arm": "a_dose_0p5", "form_label": "F1"} for i in range(50)]
        + [{"row_key": f"d{i}", "arm": "a_dose_0p5", "form_label": "F2"} for i in range(30)]
        + [{"row_key": f"d{i}", "arm": "a_dose_0p5", "form_label": "F3"} for i in range(10)]
    )
    per_arm = axis_g_arithmetic.compute_per_arm_shares(screen_counts, graded_rows)
    assert per_arm["a_baseline"]["f2_f3_share"] == pytest.approx(5 / 100)
    assert per_arm["a_dose_0p5"]["f2_f3_share"] == pytest.approx(40 / 100)
    assert per_arm["a_baseline"]["screened_vs_graded_mismatch"] is False
    assert per_arm["a_dose_0p5"]["screened_vs_graded_mismatch"] is False

    verdict = axis_g_arithmetic.adjudicate_axis_g(per_arm)
    assert verdict["verdict"] == "GRADED"
    assert verdict["per_dose"]["a_dose_0p5"]["both_legs"] is True


def test_axis_g_screen_dominated_not_adjudicable():
    screen_counts = {"per_arm": {
        "a_baseline": {"n_total": 100, "n_f5_degenerate": 0, "n_f4_explicit_idk": 90, "n_screened_in": 10},
        "a_dose_0p25": {"n_total": 100, "n_f5_degenerate": 0, "n_f4_explicit_idk": 95, "n_screened_in": 5},
        "a_dose_0p5": {"n_total": 100, "n_f5_degenerate": 0, "n_f4_explicit_idk": 97, "n_screened_in": 3},
        "a_dose_0p75": {"n_total": 100, "n_f5_degenerate": 0, "n_f4_explicit_idk": 99, "n_screened_in": 1},
    }}
    per_arm = axis_g_arithmetic.compute_per_arm_shares(screen_counts, [])
    verdict = axis_g_arithmetic.adjudicate_axis_g(per_arm)
    assert verdict["verdict"] == "NOT-ADJUDICABLE"
    assert verdict["reason"] == "screen-dominated"


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))


# ---------------------------------------------------------------------------
# Post-void additions: empty-text fail-closed guard; voided-attempt exclusion
# ---------------------------------------------------------------------------

def test_write_shards_refuses_empty_text(tmp_path, monkeypatch):
    """The guard added after calibration attempt 1: any blinded-pool row with
    empty/whitespace text aborts the whole write, no shard files created."""
    import pytest
    monkeypatch.setattr(build_judge_pool, "SHARDS_DIR", tmp_path / "shards")
    shards = [{
        "shard_id": "s00",
        "blinded_pool": [
            {"opaque_id": "aa", "text": "a real answer"},
            {"opaque_id": "bb", "text": "   "},
        ],
        "id_map": [], "n_core": 2,
        "n_decoy_clear_positive": 0, "n_decoy_clear_negative": 0,
    }]
    with pytest.raises(SystemExit):
        build_judge_pool.write_shards(shards)
    assert not (tmp_path / "shards").exists()


def test_extra_spent_dirs_exclude_voided_attempt(tmp_path):
    """(row_key, arm) pairs from --extra-spent-dirs id maps join the spent set."""
    runlog_dir = tmp_path / "runlog_form_merged"
    runlog_dir.mkdir()
    spent_dir = tmp_path / "spent_empty"
    spent_dir.mkdir()
    voided_dir = tmp_path / "voided_shards"
    voided_dir.mkdir()
    c_baseline = tmp_path / "c_baseline.jsonl"
    write_jsonl(c_baseline, [])
    write_jsonl(runlog_dir / "a_baseline.jsonl", [
        {"row_key": "seen-in-attempt1", "arm": "a_baseline", "answer_text": "x",
         "degenerate": False, "semantic_refuse": False, "refused_v2": False},
        {"row_key": "never-seen", "arm": "a_baseline", "answer_text": "y",
         "degenerate": False, "semantic_refuse": False, "refused_v2": False},
    ])
    write_jsonl(voided_dir / "form_judge_calib_shard_00_id_map.jsonl", [
        {"opaque_id": "zz", "row_key": "seen-in-attempt1", "arm": "a_baseline",
         "is_decoy": False, "decoy_type": None},
    ])
    core_by_arm, _, _, report = build_judge_pool.build_candidate_populations(
        runlog_dir, c_baseline, spent_dir, extra_spent_dirs=[voided_dir])
    assert {r["row_key"] for r in core_by_arm["a_baseline"]} == {"never-seen"}
