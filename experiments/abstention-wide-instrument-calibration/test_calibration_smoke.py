"""CPU smoke for the abstention-wide-instrument-calibration harness.

Harness-code-correctness check: proves detector-v2 pin equality, staging
manifest mechanics, the QL seeded subsample, the adjudication pool builder
(determinism, no duplicate opaque ids, per-shard decoy coverage, cell-scoped
sharding), the unblinding-order guarantee, the CG1 void/regrade state
machine, the QH paired-delta population rule, the scorer's rate/delta
arithmetic, and the row-level persistence schema -- all against synthetic
fixtures. It does NOT read any real staged data from the sibling worktrees
(none of that is required to exist for this suite to pass).

Run via `python3 -m pytest test_calibration_smoke.py -v` (bare `python3
test_calibration_smoke.py` exits 0 silently -- known repo-wide gotcha, do
not use it).
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

import apply_adjudication
import build_adjudication_pool as bap
import calibration_scorer
import detector_v2
import gates_lib
import sources
import stage_inputs

HERE = Path(__file__).resolve().parent

REFUSAL_TEXT = '{"answer": "I don\'t know the answer to that.", "response_confidence": 0.5}'
ANSWER_TEXT_TMPL = '{{"answer": "Answer number {n}, a clean well-formed committed value.", "response_confidence": 0.9}}'


def mk_row(cell, arm, row_key, role, text, hs_index=None, dose_multiplier=None, well_formed=True, well_formed_correct=False):
    return {
        "cell": cell, "arm": arm, "hs_index": hs_index, "dose_multiplier": dose_multiplier,
        "row_key": row_key, "role": role, "text": text,
        "well_formed": well_formed, "well_formed_correct": well_formed_correct,
    }


# ---------------------------------------------------------------------------
# 1. detector-v2 pin equality against RR2's committed pins.
# ---------------------------------------------------------------------------

RR2_PINS = {
    "detector_v2.py": "161fd8548ec0dad1daabd590870654f1c32bd0daf21e6026a2c18c83e83991ae",
    "detector_v2_patterns.yaml": "36422e01ae03008c2f71f180158c63950e14f8dfc1279c4e654c89fb831841d9",
}


@pytest.mark.parametrize("fname,pin", RR2_PINS.items())
def test_detector_v2_pin_equality(fname, pin):
    actual = hashlib.sha256((HERE / fname).read_bytes()).hexdigest()
    assert actual == pin, f"{fname} drifted from rr2's committed pin"


def test_detector_v2_self_check_smoke():
    cfg = detector_v2.load_patterns()
    assert detector_v2.is_refused_v2(REFUSAL_TEXT, cfg) is True
    assert detector_v2.is_refused_v2(ANSWER_TEXT_TMPL.format(n=1), cfg) is False


# ---------------------------------------------------------------------------
# 2. staging manifest mechanics + schema (no text ever committed).
# ---------------------------------------------------------------------------

def test_stage_one_writes_manifest_record_with_row_count_and_hash(tmp_path, monkeypatch):
    src = tmp_path / "src.jsonl"
    src.write_text('{"row_key": "a:1", "role": "confab"}\n{"row_key": "a:2", "role": "confab"}\n', encoding="utf-8")
    staged_dir = tmp_path / "staged"
    monkeypatch.setattr(sources, "STAGED", staged_dir)
    monkeypatch.setattr(stage_inputs, "HERE", tmp_path)

    entry = {"cell": "QH", "arm": "baseline", "source_path": src, "dest_name": "baseline.jsonl", "schema": "runlog"}
    record = stage_inputs.stage_one(entry)

    assert record["row_count"] == 2
    assert record["cell"] == "QH"
    assert record["sha256"] == hashlib.sha256(src.read_bytes()).hexdigest()
    dest = staged_dir / "QH" / "baseline.jsonl"
    assert dest.is_file()


def test_staging_manifest_end_to_end_has_no_text_fields(tmp_path, monkeypatch):
    src1 = tmp_path / "s1.jsonl"
    src1.write_text('{"row_key": "a:1", "role": "confab", "answer_text": "SECRET QUESTION TEXT should never leave analysis"}\n', encoding="utf-8")
    fixture_entries = [{"cell": "QH", "arm": "baseline", "source_path": src1, "dest_name": "baseline.jsonl", "schema": "runlog"}]

    monkeypatch.setattr(sources, "source_manifest", lambda: fixture_entries)
    monkeypatch.setattr(sources, "STAGED", tmp_path / "staged")
    monkeypatch.setattr(sources, "COMMITTED", tmp_path / "committed")
    monkeypatch.setattr(stage_inputs, "HERE", tmp_path)

    stage_inputs.main()

    manifest_text = (tmp_path / "committed" / "staging_manifest.json").read_text(encoding="utf-8")
    assert "SECRET QUESTION TEXT" not in manifest_text
    manifest = json.loads(manifest_text)
    assert manifest["files"][0]["row_count"] == 1
    assert set(manifest["files"][0].keys()) == {"cell", "arm", "hs_index", "schema", "source_path", "dest_path", "sha256", "row_count"}


# ---------------------------------------------------------------------------
# 3. QL seeded subsample determinism.
# ---------------------------------------------------------------------------

def _ql_fixture_rows_by_hs(n_per_stratum=10):
    rows_by_hs = {20: [], 23: []}
    for hs in rows_by_hs:
        for dose in (2, 4):
            for i in range(n_per_stratum):
                rows_by_hs[hs].append(mk_row(
                    "QL", "random_direction", f"kuq:{hs}:{dose}:{i}", "confab",
                    ANSWER_TEXT_TMPL.format(n=i), hs_index=hs, dose_multiplier=dose,
                ))
            # one known row too, should never be pulled into the confab subsample
            rows_by_hs[hs].append(mk_row("QL", "random_direction", f"popqa:{hs}:{dose}", "known_correct_answered", ANSWER_TEXT_TMPL.format(n=99), hs_index=hs, dose_multiplier=dose))
    return rows_by_hs


def test_ql_subsample_deterministic_and_confab_only():
    rows_by_hs = _ql_fixture_rows_by_hs(n_per_stratum=8)
    a = sources.ql_subsample(rows_by_hs, seed=20260714, n=5)
    b = sources.ql_subsample(rows_by_hs, seed=20260714, n=5)
    assert set(a.keys()) == set(b.keys()) == {(20, 2), (20, 4), (23, 2), (23, 4)}
    for key in a:
        assert [r["row_key"] for r in a[key]] == [r["row_key"] for r in b[key]]
        assert len(a[key]) == 5
        assert all(r["role"] == "confab" for r in a[key])


def test_ql_subsample_different_seed_differs():
    rows_by_hs = _ql_fixture_rows_by_hs(n_per_stratum=8)
    a = sources.ql_subsample(rows_by_hs, seed=20260714, n=5)
    b = sources.ql_subsample(rows_by_hs, seed=1, n=5)
    assert any([r["row_key"] for r in a[(20, 2)]] != [r["row_key"] for r in b[(20, 2)]] for _ in [0])


# ---------------------------------------------------------------------------
# 4. Pool build determinism, no duplicate opaque ids, per-shard decoy coverage.
# ---------------------------------------------------------------------------

def _qh_fixture():
    baseline = []
    random_direction = []
    for i in range(20):
        baseline.append(mk_row("QH", "baseline", f"kuq:{i}", "confab", ANSWER_TEXT_TMPL.format(n=i)))
    for i in range(20):
        baseline.append(mk_row("QH", "baseline", f"popqa:{i}", "known_correct_answered", ANSWER_TEXT_TMPL.format(n=i), well_formed_correct=True))
    for i in range(20):
        random_direction.append(mk_row("QH", "random_direction", f"kuq:{i}", "confab", REFUSAL_TEXT if i < 15 else ANSWER_TEXT_TMPL.format(n=i)))
    return {"baseline": baseline, "random_direction": random_direction}


def _ql_baseline_fixture():
    rows = []
    for i in range(15):
        rows.append(mk_row("QL", "baseline", f"kuq:{i}", "confab", ANSWER_TEXT_TMPL.format(n=i)))
    for i in range(10):
        rows.append(mk_row("QL", "baseline", f"popqa:{i}", "known_correct_answered", ANSWER_TEXT_TMPL.format(n=i), well_formed_correct=True))
    return rows


def _lb_fixture():
    rows = []
    for i in range(20):
        rows.append(mk_row("LB", "baseline", f"kuq:{i}", "confab", ANSWER_TEXT_TMPL.format(n=i)))
    for i in range(20):
        rows.append(mk_row("LB", "baseline", f"popqa:{i}", "known_correct_answered", ANSWER_TEXT_TMPL.format(n=i), well_formed_correct=True))
    for i in range(5):
        rows.append(mk_row("LB", "baseline", f"unk:{i}", "unknown_refused", REFUSAL_TEXT))
    return rows


@pytest.fixture()
def patched_sources(monkeypatch):
    monkeypatch.setattr(sources, "load_qh", _qh_fixture)
    monkeypatch.setattr(sources, "load_ql_baseline", _ql_baseline_fixture)
    monkeypatch.setattr(sources, "load_ql_random_direction_all", lambda: _ql_fixture_rows_by_hs(n_per_stratum=20))
    monkeypatch.setattr(sources, "load_lb", _lb_fixture)
    yield


def test_load_all_cell_rows_excludes_lb_unknown_refused(patched_sources):
    cell_rows = bap.load_all_cell_rows()
    lb_roles = {r["role"] for r in cell_rows["LB"]}
    assert lb_roles == {"confab", "known_correct_answered"}


def test_pool_build_deterministic_no_dup_opaque_ids_and_shard_decoy_coverage(patched_sources):
    cfg = detector_v2.load_patterns()
    cell_rows = bap.load_all_cell_rows()
    core, neg_cand, pos_cand = bap.build_core_and_decoy_candidates(cell_rows, cfg)
    assert neg_cand, "fixture must yield clear_negative candidates"
    assert pos_cand, "fixture must yield clear_positive candidates"

    salt = "fixed-test-salt"
    seed = 20260714

    def run_once():
        remaining_core, decoys_neg, decoys_pos = bap.carve_decoys(core, neg_cand, pos_cand, __import__("random").Random(seed))
        n_shards_by_cell = bap.pick_n_shards_by_cell(remaining_core, target_shard_size=10)
        max_total_shards = max(1, min(len(decoys_neg), len(decoys_pos)))
        n_shards_by_cell = bap.cap_total_shards_by_cell(n_shards_by_cell, max_total_shards)
        shards = bap.build_shards(remaining_core, decoys_neg, decoys_pos, n_shards_by_cell, seed, salt)
        return shards

    shards_a = run_once()
    shards_b = run_once()

    assert [s["shard_id"] for s in shards_a] == [s["shard_id"] for s in shards_b]
    for sa, sb in zip(shards_a, shards_b):
        assert [p["opaque_id"] for p in sa["blinded_pool"]] == [p["opaque_id"] for p in sb["blinded_pool"]]

    all_ids = [p["opaque_id"] for s in shards_a for p in s["blinded_pool"]]
    assert len(all_ids) == len(set(all_ids)), "duplicate opaque_id across shards"

    assert len(shards_a) >= 3, "fixture should span at least the three cells"
    cells_seen = {s["cell"] for s in shards_a}
    assert cells_seen == {"QH", "QL", "LB"}
    for shard in shards_a:
        assert shard["n_decoy_clear_negative"] >= 1, f"{shard['shard_id']} missing clear_negative decoy"
        assert shard["n_decoy_clear_positive"] >= 1, f"{shard['shard_id']} missing clear_positive decoy"
        # cell-scoped: every core row in a shard belongs to the shard's own cell
        core_cells = {m["cell"] for m in shard["id_map"] if not m["is_decoy"]}
        assert core_cells <= {shard["cell"]}


def test_pool_build_lb_clear_positive_decoys_sourced_cross_cell(patched_sources):
    """LB has no random_direction arm (no placebo on disk), so its
    clear_positive decoy candidates must come entirely from QH/QL."""
    cfg = detector_v2.load_patterns()
    cell_rows = bap.load_all_cell_rows()
    core, neg_cand, pos_cand = bap.build_core_and_decoy_candidates(cell_rows, cfg)
    lb_pos_candidates = [r for r in pos_cand if r["cell"] == "LB"]
    assert lb_pos_candidates == []
    assert any(r["cell"] in ("QH", "QL") for r in pos_cand)


def test_regrade_shard_fresh_ids_same_content():
    id_map = [
        {"opaque_id": "orig1", "cell": "QH", "row_key": "kuq:1", "arm": "baseline", "role": "confab", "is_decoy": False, "decoy_type": None},
        {"opaque_id": "orig2", "cell": "QH", "row_key": "kuq:2", "arm": "baseline", "role": "confab", "is_decoy": False, "decoy_type": None},
    ]
    regraded = bap.build_regrade_shard(id_map, salt="fixed-test-salt", regrade_index=1, seed=20260714)
    new_ids = {m["opaque_id"] for m in regraded["id_map"]}
    orig_ids = {m["opaque_id"] for m in id_map}
    assert new_ids.isdisjoint(orig_ids)
    new_keys = {(m["cell"], m["row_key"], m["arm"]) for m in regraded["id_map"]}
    orig_keys = {(m["cell"], m["row_key"], m["arm"]) for m in id_map}
    assert new_keys == orig_keys


# ---------------------------------------------------------------------------
# 5. Unblinding-order guarantee.
# ---------------------------------------------------------------------------

def test_unblinding_refused_without_committed_hash(tmp_path):
    graded = tmp_path / "graded.jsonl"
    graded.write_text('{"opaque_id": "x", "is_abstention": true}\n', encoding="utf-8")
    committed_dir = tmp_path / "committed"
    committed_dir.mkdir()
    with pytest.raises(SystemExit, match="UNBLINDING REFUSED"):
        apply_adjudication._require_committed_hash("shard_00", graded, committed_dir)


def test_unblinding_proceeds_after_commit_hash(tmp_path):
    graded = tmp_path / "graded.jsonl"
    graded.write_text('{"opaque_id": "x", "is_abstention": true}\n', encoding="utf-8")
    committed_dir_path = tmp_path / "committed"
    committed_dir_path.mkdir()

    class Args:
        shard_id = "shard_00"
        graded_file = str(graded)
        committed_dir = str(committed_dir_path)

    apply_adjudication.cmd_commit_hash(Args())
    sha = apply_adjudication._require_committed_hash("shard_00", graded, committed_dir_path)
    assert len(sha) == 64


def test_commit_hash_is_shard_scoped_not_global(tmp_path):
    """A hash committed for shard_00 must not satisfy the unblinding check
    for a DIFFERENT shard_id, even with byte-identical graded-file content."""
    graded = tmp_path / "graded.jsonl"
    graded.write_text('{"opaque_id": "x", "is_abstention": true}\n', encoding="utf-8")
    committed_dir_path = tmp_path / "committed"
    committed_dir_path.mkdir()

    class Args:
        shard_id = "shard_00"
        graded_file = str(graded)
        committed_dir = str(committed_dir_path)

    apply_adjudication.cmd_commit_hash(Args())
    with pytest.raises(SystemExit, match="UNBLINDING REFUSED"):
        apply_adjudication._require_committed_hash("shard_01", graded, committed_dir_path)


# ---------------------------------------------------------------------------
# 6. CG1 void / regrade / void-cell state machine.
# ---------------------------------------------------------------------------

def test_cg1_pass():
    r = gates_lib.cg1_evaluate_shard("s1", clear_negative_correct=19, clear_negative_total=20,
                                      clear_positive_correct=7, clear_positive_total=10, attempt=1)
    assert r["passed"] is True
    assert r["status"] == "PASS"


def test_cg1_first_failure_regrade_once():
    r = gates_lib.cg1_evaluate_shard("s1", clear_negative_correct=15, clear_negative_total=20,
                                      clear_positive_correct=8, clear_positive_total=10, attempt=1)
    assert r["passed"] is False
    assert r["status"] == "VOID_REGRADE_ONCE"


def test_cg1_second_failure_voids_cell():
    r = gates_lib.cg1_evaluate_shard("s1", clear_negative_correct=15, clear_negative_total=20,
                                      clear_positive_correct=8, clear_positive_total=10, attempt=2)
    assert r["passed"] is False
    assert r["status"] == "VOID_CELL_TERMINAL"


def test_cg1_clear_positive_floor_is_lower_than_clear_negative():
    r = gates_lib.cg1_evaluate_shard("s1", clear_negative_correct=20, clear_negative_total=20,
                                      clear_positive_correct=6, clear_positive_total=10, attempt=1)
    assert r["passed"] is True  # 0.60 clears the 0.60 floor exactly


# ---------------------------------------------------------------------------
# 7. QH paired-delta population rule.
# ---------------------------------------------------------------------------

def test_qh_paired_delta_excludes_unfired_baseline_rows(monkeypatch):
    baseline = [mk_row("QH", "baseline", f"kuq:{i}", "confab", ANSWER_TEXT_TMPL.format(n=i)) for i in range(10)]
    # only rows 0-5 "fired" (present in random_direction); rows 6-9 are unpaired.
    random_direction = [mk_row("QH", "random_direction", f"kuq:{i}", "confab", REFUSAL_TEXT) for i in range(6)]
    monkeypatch.setattr(sources, "load_qh", lambda: {"baseline": baseline, "random_direction": random_direction})

    cfg = detector_v2.load_patterns()
    report = calibration_scorer.qh_report(cfg, applied_map={}, voided_cells=set())
    confab = report["populations"]["confab"]
    assert confab["placebo"]["paired_n"] == 6
    assert confab["baseline_unpaired_gate_not_fired"]["n"] == 4
    # narrow delta: baseline paired rows are all non-refusals (rate 0), random_direction all refusals (rate 1)
    assert confab["placebo"]["delta_narrow_points"] == pytest.approx(100.0)


# ---------------------------------------------------------------------------
# 8. Scorer rate/delta arithmetic against manual Wilson computation.
# ---------------------------------------------------------------------------

def test_rate_block_matches_manual_wilson():
    rows = [{"refused_v2": True}] * 3 + [{"refused_v2": False}] * 7
    result = calibration_scorer.rate_block(rows, "refused_v2")
    expected = gates_lib.wilson(3, 10)
    assert result == expected
    assert result["rate"] == pytest.approx(0.3)


def test_undercount_is_wide_minus_narrow():
    narrow = {"rate": 0.2}
    wide = {"rate": 0.35}
    assert calibration_scorer.undercount(wide, narrow) == pytest.approx(0.15)


def test_undercount_pending_when_wide_not_yet_computed():
    narrow = {"rate": 0.2}
    assert calibration_scorer.undercount("pending_adjudication", narrow) == "pending_adjudication"


def test_wide_rate_block_excludes_uncovered_rows():
    rows = [
        {"refused_final": True}, {"refused_final": False}, {"refused_final": None}, {"refused_final": None},
    ]
    result = calibration_scorer.wide_rate_block(rows)
    assert result["n"] == 2
    assert result["n_uncovered"] == 2


def test_wide_rate_block_pending_when_nothing_covered():
    rows = [{"refused_final": None}, {"refused_final": None}]
    assert calibration_scorer.wide_rate_block(rows) == "pending_adjudication"


# ---------------------------------------------------------------------------
# 9. Row-level persistence schema (data-exhaust build-time rule).
# ---------------------------------------------------------------------------

def test_row_level_log_persists_text_and_full_subgrade(patched_sources, tmp_path):
    cfg = detector_v2.load_patterns()
    n = calibration_scorer.write_row_level_log(cfg, applied_map={}, voided_cells=set(), analysis_dir=tmp_path)
    assert n > 0
    out_path = tmp_path / "row_level_scored.jsonl"
    lines = [json.loads(line) for line in out_path.read_text(encoding="utf-8").splitlines()]
    assert len(lines) == n
    for rec in lines:
        assert "text" in rec and rec["text"]
        assert set(rec["sub_grade"].keys()) == {"refused_v2", "matched_pattern_ids", "refused_final"}
        assert isinstance(rec["sub_grade"]["matched_pattern_ids"], list)
