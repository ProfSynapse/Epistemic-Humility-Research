"""CPU smoke tests for apply_adjudication.py, against synthetic fixtures
only -- never the real graded files (per the harness-build assignment: build,
smoke, report, stop; do not run against real graded output even if present).

Every test builds its own isolated `analysis_dir` / `committed_dir` under
pytest's tmp_path, with a tiny 3-line synthetic shard (1 core row + 1
clear_negative decoy + 1 clear_positive decoy), so nothing here reads or
writes the real experiment's `analysis/` or `analysis-committed/` trees.
"""
from __future__ import annotations

import json
from pathlib import Path

import apply_adjudication as aa
import gates_lib


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r) + "\n")


def _make_shard(analysis_dir: Path, committed_dir: Path, shard_id: str = "shard_00") -> None:
    """A 3-line synthetic shard: 1 core row (a confab gated dose6 row), 1
    clear_negative decoy, 1 clear_positive decoy."""
    id_map = [
        {"opaque_id": "op0", "row_key": "q1", "arm": "gated", "hs_index": 20, "dose_multiplier": 6,
         "role": "confab", "is_decoy": False, "decoy_type": None},
        {"opaque_id": "op1", "row_key": "q2", "arm": "baseline", "hs_index": None, "dose_multiplier": None,
         "role": "known_correct_answered", "is_decoy": True, "decoy_type": "clear_negative"},
        {"opaque_id": "op2", "row_key": "q3", "arm": "random_direction", "hs_index": 20, "dose_multiplier": 12,
         "role": "confab", "is_decoy": True, "decoy_type": "clear_positive"},
    ]
    pool = [{"opaque_id": r["opaque_id"], "text": f"text for {r['opaque_id']}"} for r in id_map]
    _write_jsonl(analysis_dir / "shards" / f"{shard_id}_id_map.jsonl", id_map)
    _write_jsonl(analysis_dir / "shards" / f"{shard_id}.jsonl", pool)
    pool_sha = aa.sha256_of_file(analysis_dir / "shards" / f"{shard_id}.jsonl")
    aa.write_json(committed_dir / "adjudication_pool_manifest.json", {
        "cell": aa.CELL_ID, "n_shards": 1,
        "shards": [{"shard_id": shard_id, "pool_sha256": pool_sha, "row_count": 3}],
    })


def _write_graded(path: Path, records: list[dict]) -> Path:
    _write_jsonl(path, records)
    return path


# ---------------------------------------------------------------------------
# (1) hash-refusal path: apply must refuse to unblind a shard whose graded
#     file's hash was never committed via commit-hash.
# ---------------------------------------------------------------------------

def test_apply_refuses_unblinding_without_committed_hash(tmp_path):
    analysis_dir = tmp_path / "analysis"
    committed_dir = tmp_path / "analysis-committed"
    _make_shard(analysis_dir, committed_dir)
    graded_path = _write_graded(tmp_path / "graded_shard_00.jsonl", [
        {"opaque_id": "op0", "is_abstention": False},
        {"opaque_id": "op1", "is_abstention": False},
        {"opaque_id": "op2", "is_abstention": True},
    ])
    grading_manifest_path = tmp_path / "grading_manifest.json"
    grading_manifest_path.write_text(json.dumps({"shard_00": {"graded_file": str(graded_path), "attempt": 1}}))

    # NO commit-hash call happened -- apply must raise, not silently join.
    pool_manifest = aa.load_pool_manifest(committed_dir)
    grading_manifest = json.loads(grading_manifest_path.read_text())
    try:
        aa.evaluate_shard("shard_00", grading_manifest["shard_00"], pool_manifest, analysis_dir, committed_dir)
        assert False, "expected SystemExit: hash was never committed"
    except SystemExit as e:
        assert "UNBLINDING REFUSED" in str(e)
        assert "commit-hash" in str(e)


def test_apply_succeeds_after_hash_is_committed(tmp_path):
    analysis_dir = tmp_path / "analysis"
    committed_dir = tmp_path / "analysis-committed"
    _make_shard(analysis_dir, committed_dir)
    graded_path = _write_graded(tmp_path / "graded_shard_00.jsonl", [
        {"opaque_id": "op0", "is_abstention": False},
        {"opaque_id": "op1", "is_abstention": False},  # clear_negative correctly NOT credited
        {"opaque_id": "op2", "is_abstention": True},   # clear_positive correctly credited
    ])
    aa.cmd_commit_hash(argparse_ns(shard_id="shard_00", graded_file=str(graded_path), committed_dir=str(committed_dir)))

    pool_manifest = aa.load_pool_manifest(committed_dir)
    result = aa.evaluate_shard("shard_00", {"graded_file": str(graded_path), "attempt": 1}, pool_manifest, analysis_dir, committed_dir)
    assert result["cg1"]["passed"] is True
    assert result["cg1"]["status"] == "PASS"
    assert result["core_rows"] == [
        {"row_key": "q1", "arm": "gated", "hs_index": 20, "dose_multiplier": 6, "role": "confab", "refused_final": False},
    ]


# ---------------------------------------------------------------------------
# (2) positional-mismatch raise: extra/missing/reordered lines must raise,
#     never silently misalign.
# ---------------------------------------------------------------------------

def test_apply_raises_on_opaque_id_positional_mismatch(tmp_path):
    analysis_dir = tmp_path / "analysis"
    committed_dir = tmp_path / "analysis-committed"
    _make_shard(analysis_dir, committed_dir)
    # op1 and op2 swapped relative to the id map's line order.
    graded_path = _write_graded(tmp_path / "graded_shard_00.jsonl", [
        {"opaque_id": "op0", "is_abstention": False},
        {"opaque_id": "op2", "is_abstention": True},
        {"opaque_id": "op1", "is_abstention": False},
    ])
    aa.cmd_commit_hash(argparse_ns(shard_id="shard_00", graded_file=str(graded_path), committed_dir=str(committed_dir)))
    pool_manifest = aa.load_pool_manifest(committed_dir)
    try:
        aa.evaluate_shard("shard_00", {"graded_file": str(graded_path), "attempt": 1}, pool_manifest, analysis_dir, committed_dir)
        assert False, "expected SystemExit: positional opaque_id mismatch"
    except SystemExit as e:
        assert "opaque_id mismatch" in str(e)


def test_apply_raises_on_line_count_mismatch(tmp_path):
    analysis_dir = tmp_path / "analysis"
    committed_dir = tmp_path / "analysis-committed"
    _make_shard(analysis_dir, committed_dir)
    graded_path = _write_graded(tmp_path / "graded_shard_00.jsonl", [
        {"opaque_id": "op0", "is_abstention": False},
        {"opaque_id": "op1", "is_abstention": False},
        # missing the third line entirely
    ])
    aa.cmd_commit_hash(argparse_ns(shard_id="shard_00", graded_file=str(graded_path), committed_dir=str(committed_dir)))
    pool_manifest = aa.load_pool_manifest(committed_dir)
    try:
        aa.evaluate_shard("shard_00", {"graded_file": str(graded_path), "attempt": 1}, pool_manifest, analysis_dir, committed_dir)
        assert False, "expected SystemExit: line count mismatch"
    except SystemExit as e:
        assert "positional and requires exact line alignment" in str(e)


def test_apply_raises_on_non_boolean_is_abstention(tmp_path):
    analysis_dir = tmp_path / "analysis"
    committed_dir = tmp_path / "analysis-committed"
    _make_shard(analysis_dir, committed_dir)
    graded_path = _write_graded(tmp_path / "graded_shard_00.jsonl", [
        {"opaque_id": "op0", "is_abstention": "no"},  # string, not bool
        {"opaque_id": "op1", "is_abstention": False},
        {"opaque_id": "op2", "is_abstention": True},
    ])
    aa.cmd_commit_hash(argparse_ns(shard_id="shard_00", graded_file=str(graded_path), committed_dir=str(committed_dir)))
    pool_manifest = aa.load_pool_manifest(committed_dir)
    try:
        aa.evaluate_shard("shard_00", {"graded_file": str(graded_path), "attempt": 1}, pool_manifest, analysis_dir, committed_dir)
        assert False, "expected SystemExit: non-boolean is_abstention"
    except SystemExit as e:
        assert "boolean" in str(e)


# ---------------------------------------------------------------------------
# (3) CG1 void ladder: attempt-1 failure -> VOID_REGRADE_ONCE (lane not
#     voided yet); attempt-2 failure on the same content -> VOID_CELL_TERMINAL
#     (whole lane voided, zero rows applied even from otherwise-passing shards).
# ---------------------------------------------------------------------------

def test_cg1_attempt1_failure_is_void_regrade_once_not_terminal(tmp_path):
    analysis_dir = tmp_path / "analysis"
    committed_dir = tmp_path / "analysis-committed"
    _make_shard(analysis_dir, committed_dir)
    # clear_positive decoy (op2) graded False -- grader missed an unambiguous
    # abstention, clear_positive_agreement = 0/1 = 0.0 < 0.60 floor.
    graded_path = _write_graded(tmp_path / "graded_shard_00.jsonl", [
        {"opaque_id": "op0", "is_abstention": False},
        {"opaque_id": "op1", "is_abstention": False},
        {"opaque_id": "op2", "is_abstention": False},
    ])
    aa.cmd_commit_hash(argparse_ns(shard_id="shard_00", graded_file=str(graded_path), committed_dir=str(committed_dir)))
    pool_manifest = aa.load_pool_manifest(committed_dir)
    result = aa.evaluate_shard("shard_00", {"graded_file": str(graded_path), "attempt": 1}, pool_manifest, analysis_dir, committed_dir)
    assert result["cg1"]["passed"] is False
    assert result["cg1"]["status"] == "VOID_REGRADE_ONCE"
    assert result["core_rows"] is None


def test_cg1_attempt2_failure_is_terminal_and_voids_whole_lane(tmp_path):
    analysis_dir = tmp_path / "analysis"
    committed_dir = tmp_path / "analysis-committed"
    _make_shard(analysis_dir, committed_dir, shard_id="shard_00")
    # A second, PASSING shard to prove a terminal void on shard_00 excludes
    # shard_01's otherwise-good rows too (single-cell lane-wide void).
    id_map_01 = [
        {"opaque_id": "op10", "row_key": "q10", "arm": "gated", "hs_index": 22, "dose_multiplier": 8,
         "role": "known_correct_answered", "is_decoy": False, "decoy_type": None},
        {"opaque_id": "op11", "row_key": "q11", "arm": "baseline", "hs_index": None, "dose_multiplier": None,
         "role": "known_correct_answered", "is_decoy": True, "decoy_type": "clear_negative"},
        {"opaque_id": "op12", "row_key": "q12", "arm": "random_direction", "hs_index": 20, "dose_multiplier": 16,
         "role": "confab", "is_decoy": True, "decoy_type": "clear_positive"},
    ]
    pool_01 = [{"opaque_id": r["opaque_id"], "text": f"text {r['opaque_id']}"} for r in id_map_01]
    _write_jsonl(analysis_dir / "shards" / "shard_01_id_map.jsonl", id_map_01)
    _write_jsonl(analysis_dir / "shards" / "shard_01.jsonl", pool_01)
    pool_01_sha = aa.sha256_of_file(analysis_dir / "shards" / "shard_01.jsonl")
    manifest = aa.load_pool_manifest(committed_dir)
    manifest["shards"].append({"shard_id": "shard_01", "pool_sha256": pool_01_sha, "row_count": 3})
    aa.write_json(committed_dir / "adjudication_pool_manifest.json", manifest)

    graded_01 = _write_graded(tmp_path / "graded_shard_01.jsonl", [
        {"opaque_id": "op10", "is_abstention": False},
        {"opaque_id": "op11", "is_abstention": False},
        {"opaque_id": "op12", "is_abstention": True},
    ])
    aa.cmd_commit_hash(argparse_ns(shard_id="shard_01", graded_file=str(graded_01), committed_dir=str(committed_dir)))

    # shard_00 fails CG1 twice (attempt 1 then attempt 2, same failing content).
    graded_00_attempt2 = _write_graded(tmp_path / "graded_shard_00_regrade.jsonl", [
        {"opaque_id": "op0", "is_abstention": False},
        {"opaque_id": "op1", "is_abstention": False},
        {"opaque_id": "op2", "is_abstention": False},  # still misses the clear_positive
    ])
    aa.cmd_commit_hash(argparse_ns(shard_id="shard_00", graded_file=str(graded_00_attempt2), committed_dir=str(committed_dir)))

    grading_manifest_path = tmp_path / "grading_manifest.json"
    grading_manifest_path.write_text(json.dumps({
        "shard_00": {"graded_file": str(graded_00_attempt2), "attempt": 2},
        "shard_01": {"graded_file": str(graded_01), "attempt": 1},
    }))

    import argparse as _argparse
    args = _argparse.Namespace(
        grading_manifest=str(grading_manifest_path), family="llama",
        analysis_dir=str(analysis_dir), committed_dir=str(committed_dir),
    )
    # build_post_adjudication_table reads real runlog dirs; point it at an
    # empty synthetic one so this stays a pure CG1-void smoke test.
    (analysis_dir / "llama" / "runlog").mkdir(parents=True, exist_ok=True)
    _write_jsonl(analysis_dir / "llama" / "joined_rows_private.jsonl", [])
    aa.cmd_apply(args)

    applied_report = json.loads((committed_dir / "adjudication_applied_manifest.json").read_text())
    assert applied_report["experiment_voided"] is True
    assert applied_report["shards"]["shard_00"]["status"] == "VOID_CELL_TERMINAL"
    assert applied_report["shards"]["shard_01"]["status"] == "PASS"
    assert applied_report["n_applied_rows"] == 0, "a terminal void must exclude even a passing shard's rows"

    applied_lines = (analysis_dir / "adjudication_applied.jsonl").read_text().splitlines()
    assert [l for l in applied_lines if l.strip()] == []


def argparse_ns(**kwargs):
    import argparse
    return argparse.Namespace(**kwargs)
