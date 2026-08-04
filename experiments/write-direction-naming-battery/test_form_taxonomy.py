"""CPU smoke tests for form_taxonomy.py and the blinded-adjudication
tooling (build_form_adjudication_pool.py / apply_form_adjudication.py).

Synthetic fixtures only -- no question, alias, or real generation text
(containment rule shared with every other pattern-instrument test in this
repo, e.g. detector_v2's own self-checks and the CG1 reference test file
`llama-atlas-gated-wide-instrument-retest/test_apply_adjudication_smoke.py`,
read before writing this).
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

import apply_form_adjudication as afa
import build_form_adjudication_pool as bfap
import form_taxonomy as ft


# ---------------------------------------------------------------------------
# (1) Priority-order exclusivity: every synthetic string lands in exactly
#     one of the five classes, and the check that produced it is the
#     HIGHEST-priority one whose surface condition is true.
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def cfg():
    return ft.load_patterns()


def _row(text, *, degenerate=False, semantic_refuse=False, refused_v2=False, answer_value=None):
    row = {"answer_text": text, "degenerate": degenerate, "semantic_refuse": semantic_refuse, "refused_v2": refused_v2}
    if answer_value is not None:
        row["answer_value"] = answer_value
    return row


EXCLUSIVITY_CASES = [
    ("F5_degenerate", _row("", degenerate=True)),
    ("F5_degenerate", _row("True True True True True", degenerate=True)),
    ("F4_explicit_idk", _row('{"answer": "I don\'t know"}', semantic_refuse=True)),
    ("F4_explicit_idk", _row('{"answer": "It is impossible to predict."}', refused_v2=True)),
    ("F3_non_answerability", _row(
        '{"answer": "This cannot be answered with a single fact because it depends on specific data."}',
        answer_value="This cannot be answered with a single fact because it depends on specific data.",
    )),
    ("F3_non_answerability", _row('{"answer": "..."}', answer_value="There is no single correct answer to this question.")),
    ("F2_hedged_assertion", _row('{"answer": "..."}', answer_value="It is probably Kazan.")),
    ("F2_hedged_assertion", _row('{"answer": "..."}', answer_value="My best guess is York.")),
    ("F1_committed_assertion", _row('{"answer": "Kazan"}', answer_value="Kazan")),
    ("F1_committed_assertion", _row('{"answer": "1900"}', answer_value="1900")),
    ("F1_committed_assertion", _row('{"answer": "York"}', answer_value="York")),
]


@pytest.mark.parametrize("expected_class,row", EXCLUSIVITY_CASES)
def test_priority_order_exclusivity(cfg, expected_class, row):
    result = ft.classify(row, cfg)
    assert result["form_class"] == expected_class
    assert result["form_class"] in ft.FORM_CLASSES


def test_every_case_maps_to_a_distinct_expected_class_across_all_five():
    """The parametrized battery above must actually exercise all five
    classes, not just some subset -- a regression here means the fixture
    list stopped covering the taxonomy, not that the code is wrong."""
    covered = {expected for expected, _ in EXCLUSIVITY_CASES}
    assert covered == set(ft.FORM_CLASSES)


# ---------------------------------------------------------------------------
# (2) Structural precedence: a row satisfying MULTIPLE classes' surface
#     conditions must resolve to the highest-priority one, because the
#     lower-priority checks never even run -- not because of ad hoc
#     tie-breaking logic.
# ---------------------------------------------------------------------------

def test_degenerate_wins_even_if_text_also_matches_f4_f3_f2_patterns(cfg):
    row = _row(
        '{"answer": "I don\'t know, but possibly Kazan, since it cannot be answered with a single fact"}',
        degenerate=True, semantic_refuse=True,
        answer_value="I don't know, but possibly Kazan, since it cannot be answered with a single fact",
    )
    assert ft.classify(row, cfg)["form_class"] == "F5_degenerate"


def test_idk_wins_over_f3_and_f2_when_not_degenerate(cfg):
    row = _row(
        '{"answer": "..."}', semantic_refuse=True,
        answer_value="It is probably Kazan, but this cannot be answered with a single fact.",
    )
    assert ft.classify(row, cfg)["form_class"] == "F4_explicit_idk"


def test_f3_wins_over_f2_when_both_patterns_present(cfg):
    row = _row(
        '{"answer": "..."}',
        answer_value="It is probably Kazan, but there is no single correct answer to this question.",
    )
    result = ft.classify(row, cfg)
    assert result["form_class"] == "F3_non_answerability"


def test_f5_f4_are_field_checks_with_no_matched_pattern_ids(cfg):
    assert ft.classify(_row("", degenerate=True), cfg)["form_matched_pattern_ids"] == []
    assert ft.classify(_row('{"answer": "I don\'t know"}', semantic_refuse=True), cfg)["form_matched_pattern_ids"] == []


def test_f1_is_the_remainder_with_no_matched_pattern_ids(cfg):
    result = ft.classify(_row('{"answer": "Kazan"}', answer_value="Kazan"), cfg)
    assert result["form_class"] == "F1_committed_assertion"
    assert result["form_matched_pattern_ids"] == []


# ---------------------------------------------------------------------------
# (3) Frozen referents from AMENDMENT.md "Feasibility probe" classify
#     correctly -- these are the exact class-boundary examples the draft
#     itself cites, transcribed verbatim, not paraphrased.
# ---------------------------------------------------------------------------

def test_frozen_referent_f3_cannot_be_answered_with_a_single_fact(cfg):
    text = "This cannot be answered with a single fact because it depends on specific data."
    row = _row('{"answer": "..."}', answer_value=text)
    result = ft.classify(row, cfg)
    assert result["form_class"] == "F3_non_answerability"
    assert "f3_frozen_referent_cannot_single_fact" in result["form_matched_pattern_ids"]


@pytest.mark.parametrize("bare_answer", ["Kazan", "1900", "York"])
def test_frozen_referents_f1_bare_unmarked_substitutions(cfg, bare_answer):
    row = _row(f'{{"answer": "{bare_answer}"}}', answer_value=bare_answer)
    result = ft.classify(row, cfg)
    assert result["form_class"] == "F1_committed_assertion"


def test_frozen_referent_f1_confident_false_biography(cfg):
    text = "Marie Curie was born in Paris in 1850 and won three Nobel Prizes in chemistry."
    row = _row('{"answer": "..."}', answer_value=text)
    assert ft.classify(row, cfg)["form_class"] == "F1_committed_assertion"


# ---------------------------------------------------------------------------
# (4) F5>F4>F3>F2>F1 precedence enforced structurally: patch the config to
#     an F3 pattern that would ALSO match under F2 vocabulary, and confirm
#     the priority order is a property of the CODE PATH (classify() returns
#     before ever inspecting f2_hedged_assertion), not just the pattern data.
# ---------------------------------------------------------------------------

def test_precedence_is_structural_not_just_pattern_luck():
    """A minimal config where the F3 group is empty and the F2 group
    contains a pattern that matches -- confirms F2 only fires when F3
    genuinely did not, by construction (empty F3 group can never
    short-circuit), and a row already flagged `refused_v2` never reaches
    the pattern-matching code path at all (a spy config makes any pattern
    check here fail the test if it runs)."""
    poison_cfg = {
        "f3_non_answerability": [{"id": "f3_never", "pattern": r"MUST_NOT_BE_REACHED_F3"}],
        "f2_hedged_assertion": [{"id": "f2_never", "pattern": r"MUST_NOT_BE_REACHED_F2"}],
    }
    row = _row('{"answer": "..."}', refused_v2=True, answer_value="MUST_NOT_BE_REACHED_F3 MUST_NOT_BE_REACHED_F2")
    result = ft.classify(row, poison_cfg)
    assert result["form_class"] == "F4_explicit_idk"
    assert result["form_matched_pattern_ids"] == []


def test_f2_only_checked_when_f3_group_is_empty_or_non_matching():
    cfg = {
        "f3_non_answerability": [],
        "f2_hedged_assertion": [{"id": "f2_probe", "pattern": r"probe_marker"}],
    }
    row = _row('{"answer": "..."}', answer_value="a probe_marker answer")
    result = ft.classify(row, cfg)
    assert result["form_class"] == "F2_hedged_assertion"
    assert result["form_matched_pattern_ids"] == ["f2_probe"]


# ---------------------------------------------------------------------------
# (5) Decoy machinery round-trip: build_form_adjudication_pool.py writes a
#     pool from synthetic RunLog fixtures; apply_form_adjudication.py joins
#     a synthetic graded file back against it. Mirrors the CG1 reference
#     test file's shape (hash-refusal, positional mismatch, invalid label).
# ---------------------------------------------------------------------------

def _write_runlog(runlog_dir: Path, arm: str, rows: list[dict]) -> None:
    runlog_dir.mkdir(parents=True, exist_ok=True)
    with (runlog_dir / f"{arm}.jsonl").open("w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r) + "\n")


def _make_synthetic_runlogs(runlog_dir: Path) -> None:
    _write_runlog(runlog_dir, "a_baseline", [
        {"row_key": "kuq_unknowns_all:1", "answer_text": '{"answer": "Kazan"}', "form_class": "F1_committed_assertion"},
        {"row_key": "kuq_unknowns_all:2", "answer_text": '{"answer": "..."}', "form_class": "F2_hedged_assertion"},
    ])
    _write_runlog(runlog_dir, "a_dose_0p5", [
        {"row_key": "kuq_unknowns_all:3", "answer_text": '{"answer": "..."}', "form_class": "F3_non_answerability"},
        {"row_key": "kuq_unknowns_all:4", "answer_text": '{"answer": "..."}', "form_class": "F4_explicit_idk"},
        {"row_key": "kuq_unknowns_all:5", "answer_text": '{"answer": "..."}', "form_class": "F5_degenerate"},
    ])
    _write_runlog(runlog_dir, "a_placebo_0p5", [
        {"row_key": "kuq_unknowns_all:6", "answer_text": '{"answer": "..."}', "form_class": "F2_hedged_assertion"},
        {"row_key": "kuq_unknowns_all:7", "answer_text": '{"answer": "Kazan"}', "form_class": "F1_committed_assertion"},
    ])


def test_build_pool_discovers_runlogs_and_excludes_f4_f5_from_core(tmp_path):
    runlog_dir = tmp_path / "runlog"
    _make_synthetic_runlogs(runlog_dir)

    core, decoys, coverage = bfap.load_core_and_decoy_candidates(runlog_dir)

    core_keys = {r["row_key"] for r in core}
    assert core_keys == {"kuq_unknowns_all:1", "kuq_unknowns_all:2", "kuq_unknowns_all:3"}
    assert all(r["form_class"] in bfap.CORE_FORM_CLASSES for r in core)

    decoy_keys = {r["row_key"] for r in decoys}
    assert decoy_keys == {"kuq_unknowns_all:6"}  # only the placebo F2/F3 row, not the placebo F1 row
    assert coverage["n_core_candidates"] == 3
    assert coverage["n_clear_positive_candidates"] == 1


def test_build_pool_end_to_end_writes_committed_manifest(tmp_path, monkeypatch):
    runlog_dir = tmp_path / "runlog"
    _make_synthetic_runlogs(runlog_dir)
    analysis_dir = tmp_path / "analysis"
    committed_dir = tmp_path / "analysis-committed"
    monkeypatch.setattr(bfap, "SHARDS_DIR", analysis_dir / "shards")
    monkeypatch.setattr(bfap, "COMMITTED", committed_dir)

    args = argparse_ns(
        runlog_dir=str(runlog_dir), seed=1, salt="test-salt", slice_n=3, min_decoys=1, target_shard_size=10,
    )
    bfap.cmd_build(args)

    manifest_path = committed_dir / "form_adjudication_pool_manifest.json"
    assert manifest_path.is_file()
    manifest = json.loads(manifest_path.read_text())
    assert manifest["n_core_total"] == 3
    assert manifest["n_decoy_clear_positive_total"] == 1
    assert "text" not in json.dumps(manifest)  # containment: no generation text in the committed manifest

    shard = manifest["shards"][0]
    shard_pool_path = (analysis_dir / "shards" / f"{shard['shard_id']}.jsonl")
    assert shard_pool_path.is_file()
    pool_rows = [json.loads(l) for l in shard_pool_path.read_text().splitlines()]
    assert len(pool_rows) == shard["row_count"]
    assert all(set(r.keys()) == {"opaque_id", "text"} for r in pool_rows)  # blinded: no row_key/arm/form_class


def argparse_ns(**kwargs):
    import argparse
    return argparse.Namespace(**kwargs)


# ---------------------------------------------------------------------------
# (6) apply_form_adjudication.py: hash-refusal, positional mismatch, invalid
#     label, and the pooled disagreement/decoy-agreement verdict arithmetic.
# ---------------------------------------------------------------------------

def _make_shard(analysis_dir: Path, committed_dir: Path, shard_id: str = "shard_00") -> None:
    """A 4-line synthetic shard: 3 core rows (F1, F2, F3) + 1 clear_positive
    decoy (an F2-classified placebo row)."""
    id_map = [
        {"opaque_id": "op0", "row_key": "q1", "arm": "a_baseline", "form_class": "F1_committed_assertion", "is_decoy": False, "decoy_type": None},
        {"opaque_id": "op1", "row_key": "q2", "arm": "a_dose_0p5", "form_class": "F2_hedged_assertion", "is_decoy": False, "decoy_type": None},
        {"opaque_id": "op2", "row_key": "q3", "arm": "a_dose_0p5", "form_class": "F3_non_answerability", "is_decoy": False, "decoy_type": None},
        {"opaque_id": "op3", "row_key": "q4", "arm": "a_placebo_0p5", "form_class": "F2_hedged_assertion", "is_decoy": True, "decoy_type": "clear_positive"},
    ]
    pool = [{"opaque_id": r["opaque_id"], "text": f"text for {r['opaque_id']}"} for r in id_map]
    (analysis_dir / "shards").mkdir(parents=True, exist_ok=True)
    with (analysis_dir / "shards" / f"{shard_id}_id_map.jsonl").open("w", encoding="utf-8") as fh:
        for r in id_map:
            fh.write(json.dumps(r) + "\n")
    with (analysis_dir / "shards" / f"{shard_id}.jsonl").open("w", encoding="utf-8") as fh:
        for r in pool:
            fh.write(json.dumps(r) + "\n")
    pool_sha = afa.sha256_of_file(analysis_dir / "shards" / f"{shard_id}.jsonl")
    afa.write_json(committed_dir / "form_adjudication_pool_manifest.json", {
        "cell": "write_direction_naming_battery_form_taxonomy", "n_shards": 1,
        "shards": [{"shard_id": shard_id, "pool_sha256": pool_sha, "row_count": 4}],
    })


def _write_graded(path: Path, records: list[dict]) -> Path:
    with path.open("w", encoding="utf-8") as fh:
        for r in records:
            fh.write(json.dumps(r) + "\n")
    return path


def test_apply_refuses_unblinding_without_committed_hash(tmp_path):
    analysis_dir = tmp_path / "analysis"
    committed_dir = tmp_path / "analysis-committed"
    _make_shard(analysis_dir, committed_dir)
    graded_path = _write_graded(tmp_path / "graded_shard_00.jsonl", [
        {"opaque_id": "op0", "form_label": "F1"},
        {"opaque_id": "op1", "form_label": "F2"},
        {"opaque_id": "op2", "form_label": "F3"},
        {"opaque_id": "op3", "form_label": "F2"},
    ])
    pool_manifest = afa.load_pool_manifest(committed_dir)
    try:
        afa.evaluate_shard("shard_00", {"graded_file": str(graded_path)}, pool_manifest, analysis_dir, committed_dir)
        assert False, "expected SystemExit: hash was never committed"
    except SystemExit as e:
        assert "UNBLINDING REFUSED" in str(e)
        assert "commit-hash" in str(e)


def test_apply_succeeds_after_hash_is_committed_and_computes_perfect_agreement(tmp_path):
    analysis_dir = tmp_path / "analysis"
    committed_dir = tmp_path / "analysis-committed"
    _make_shard(analysis_dir, committed_dir)
    graded_path = _write_graded(tmp_path / "graded_shard_00.jsonl", [
        {"opaque_id": "op0", "form_label": "F1"},
        {"opaque_id": "op1", "form_label": "F2"},
        {"opaque_id": "op2", "form_label": "F3"},
        {"opaque_id": "op3", "form_label": "F2"},  # decoy correctly NOT labeled F1
    ])
    afa.cmd_commit_hash(argparse_ns(shard_id="shard_00", graded_file=str(graded_path), committed_dir=str(committed_dir)))

    pool_manifest = afa.load_pool_manifest(committed_dir)
    result = afa.evaluate_shard("shard_00", {"graded_file": str(graded_path)}, pool_manifest, analysis_dir, committed_dir)
    assert result["n_core"] == 3
    assert result["n_disagree"] == 0
    assert result["disagreement_rate"] == 0.0
    assert result["n_decoy_clear_positive"] == 1
    assert result["decoy_agreement_rate"] == 1.0


def test_apply_raises_on_opaque_id_positional_mismatch(tmp_path):
    analysis_dir = tmp_path / "analysis"
    committed_dir = tmp_path / "analysis-committed"
    _make_shard(analysis_dir, committed_dir)
    graded_path = _write_graded(tmp_path / "graded_shard_00.jsonl", [
        {"opaque_id": "op0", "form_label": "F1"},
        {"opaque_id": "op2", "form_label": "F3"},  # swapped with op1
        {"opaque_id": "op1", "form_label": "F2"},
        {"opaque_id": "op3", "form_label": "F2"},
    ])
    afa.cmd_commit_hash(argparse_ns(shard_id="shard_00", graded_file=str(graded_path), committed_dir=str(committed_dir)))
    pool_manifest = afa.load_pool_manifest(committed_dir)
    try:
        afa.evaluate_shard("shard_00", {"graded_file": str(graded_path)}, pool_manifest, analysis_dir, committed_dir)
        assert False, "expected SystemExit: positional opaque_id mismatch"
    except SystemExit as e:
        assert "opaque_id mismatch" in str(e)


def test_apply_raises_on_line_count_mismatch(tmp_path):
    analysis_dir = tmp_path / "analysis"
    committed_dir = tmp_path / "analysis-committed"
    _make_shard(analysis_dir, committed_dir)
    graded_path = _write_graded(tmp_path / "graded_shard_00.jsonl", [
        {"opaque_id": "op0", "form_label": "F1"},
        {"opaque_id": "op1", "form_label": "F2"},
    ])
    afa.cmd_commit_hash(argparse_ns(shard_id="shard_00", graded_file=str(graded_path), committed_dir=str(committed_dir)))
    pool_manifest = afa.load_pool_manifest(committed_dir)
    try:
        afa.evaluate_shard("shard_00", {"graded_file": str(graded_path)}, pool_manifest, analysis_dir, committed_dir)
        assert False, "expected SystemExit: line count mismatch"
    except SystemExit as e:
        assert "positional and requires exact line alignment" in str(e)


def test_apply_raises_on_invalid_form_label(tmp_path):
    analysis_dir = tmp_path / "analysis"
    committed_dir = tmp_path / "analysis-committed"
    _make_shard(analysis_dir, committed_dir)
    graded_path = _write_graded(tmp_path / "graded_shard_00.jsonl", [
        {"opaque_id": "op0", "form_label": "F1"},
        {"opaque_id": "op1", "form_label": "not_a_class"},
        {"opaque_id": "op2", "form_label": "F3"},
        {"opaque_id": "op3", "form_label": "F2"},
    ])
    afa.cmd_commit_hash(argparse_ns(shard_id="shard_00", graded_file=str(graded_path), committed_dir=str(committed_dir)))
    pool_manifest = afa.load_pool_manifest(committed_dir)
    try:
        afa.evaluate_shard("shard_00", {"graded_file": str(graded_path)}, pool_manifest, analysis_dir, committed_dir)
        assert False, "expected SystemExit: invalid form_label"
    except SystemExit as e:
        assert "invalid 'form_label'" in str(e)


def test_pooled_verdict_fails_below_decoy_count_floor():
    shard_results = [{
        "n_core": 100, "n_disagree": 0, "n_decoy_clear_positive": 10, "n_decoy_agree": 10,
    }]
    verdict = afa.pooled_verdict(shard_results)
    assert verdict["decoy_count_pass"] is False
    assert verdict["passed"] is False
    assert verdict["status"] == "AXIS_G_VOID"


def test_pooled_verdict_fails_above_disagreement_ceiling():
    shard_results = [{
        "n_core": 100, "n_disagree": 6, "n_decoy_clear_positive": 30, "n_decoy_agree": 30,
    }]
    verdict = afa.pooled_verdict(shard_results)
    assert verdict["disagreement_rate"] == pytest.approx(0.06)
    assert verdict["disagreement_pass"] is False
    assert verdict["passed"] is False
    assert verdict["status"] == "AXIS_G_VOID"


def test_pooled_verdict_fails_below_decoy_agreement_floor():
    shard_results = [{
        "n_core": 100, "n_disagree": 0, "n_decoy_clear_positive": 30, "n_decoy_agree": 15,
    }]
    verdict = afa.pooled_verdict(shard_results)
    assert verdict["decoy_agreement_rate"] == pytest.approx(0.5)
    assert verdict["decoy_agreement_pass"] is False
    assert verdict["passed"] is False


def test_pooled_verdict_passes_when_all_three_floors_clear():
    shard_results = [
        {"n_core": 100, "n_disagree": 4, "n_decoy_clear_positive": 15, "n_decoy_agree": 10},
        {"n_core": 100, "n_disagree": 1, "n_decoy_clear_positive": 15, "n_decoy_agree": 12},
    ]
    verdict = afa.pooled_verdict(shard_results)
    assert verdict["n_core_total"] == 200
    assert verdict["disagreement_rate"] == pytest.approx(5 / 200)
    assert verdict["n_decoy_clear_positive_total"] == 30
    assert verdict["decoy_agreement_rate"] == pytest.approx(22 / 30)
    assert verdict["passed"] is True
    assert verdict["status"] == "PASS"


def test_apply_end_to_end_writes_committed_applied_manifest_and_applies_rows(tmp_path):
    analysis_dir = tmp_path / "analysis"
    committed_dir = tmp_path / "analysis-committed"
    _make_shard(analysis_dir, committed_dir)
    graded_path = _write_graded(tmp_path / "graded_shard_00.jsonl", [
        {"opaque_id": "op0", "form_label": "F1"},
        {"opaque_id": "op1", "form_label": "F2"},
        {"opaque_id": "op2", "form_label": "F3"},
        {"opaque_id": "op3", "form_label": "F2"},
    ])
    afa.cmd_commit_hash(argparse_ns(shard_id="shard_00", graded_file=str(graded_path), committed_dir=str(committed_dir)))
    grading_manifest_path = tmp_path / "grading_manifest.json"
    grading_manifest_path.write_text(json.dumps({"shard_00": {"graded_file": str(graded_path)}}))

    args = argparse_ns(
        grading_manifest=str(grading_manifest_path), analysis_dir=str(analysis_dir), committed_dir=str(committed_dir),
    )
    afa.cmd_apply(args)

    applied_report = json.loads((committed_dir / "form_adjudication_applied_manifest.json").read_text())
    # 4 core rows total pooled across the run (but this fixture has n_core=3
    # and 1 decoy per the shard's own 4-row layout) -- below both the
    # slice_n=200 and min_decoys=25 registered targets, so the pooled
    # verdict is expected to read AXIS_G_VOID on this tiny smoke fixture;
    # the point of this test is the WIRING (manifest written, rows applied
    # iff passed), not a real calibration result.
    assert applied_report["pooled_verdict"]["n_core_total"] == 3
    assert applied_report["pooled_verdict"]["n_decoy_clear_positive_total"] == 1
    assert "text" not in json.dumps(applied_report)  # containment

    applied_path = analysis_dir / "form_adjudication_applied.jsonl"
    assert applied_path.is_file()
