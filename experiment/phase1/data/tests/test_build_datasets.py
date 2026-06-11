#!/usr/bin/env python3
"""Smoke tests for the WS-2 dataset builders (experiment/phase1/data/build_datasets.py).

Scope (CODE-phase smoke, not exhaustive TEST-phase coverage): does it run on a
fixture, do all four arms appear, and do the four load-bearing invariants hold?
  1. leakage guard aborts on overlap and passes when disjoint (tested both ways);
  2. budget = distinct source questions (frozen set sizing);
  3. every abstention phrasing carries a refusal marker (bank validation);
  4. dev split is excluded from train and identical across arms.
Plus: KTO T/F/T/F interleaving, DPO schema shape, and determinism.

Run:
    python -m pytest experiment/phase1/data/tests/test_build_datasets.py -q
    # or, without pytest installed:
    python experiment/phase1/data/tests/test_build_datasets.py
"""

import json
import sys
from pathlib import Path

import yaml

# Make build_datasets importable whether run via pytest or directly.
DATA_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(DATA_DIR))

import build_datasets as bd  # noqa: E402

FIXTURES = Path(__file__).resolve().parent / "fixtures"
PROBE = FIXTURES / "probe_results.jsonl"
CHENG_CLEAN = FIXTURES / "cheng_test_gold_clean.jsonl"
CHENG_LEAK = FIXTURES / "cheng_test_gold_leak.jsonl"
BANK = DATA_DIR / "abstention_bank.json"
CONFIG = DATA_DIR / "config" / "build.yaml"


def _load_config():
    return yaml.safe_load(CONFIG.read_text(encoding="utf-8"))


def _paths(out_dir: Path, cheng=CHENG_CLEAN):
    return {
        "probe_results": PROBE,
        "cheng_test_gold": cheng,
        "abstention_bank": BANK,
        "output_dir": out_dir,
        "config": CONFIG,
    }


def _read_jsonl(path: Path):
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


# ---------------------------------------------------------------------------
# Invariant 1: leakage guard (both ways).
# ---------------------------------------------------------------------------


def test_leakage_guard_passes_when_disjoint(tmp_path):
    manifest = bd.build_all(_load_config(), "test-model", _paths(tmp_path))
    assert manifest["leakage_guard"]["passed"] is True
    assert manifest["leakage_guard"]["intersection_count"] == 0


def test_leakage_guard_aborts_on_overlap(tmp_path):
    raised = False
    try:
        bd.build_all(_load_config(), "test-model", _paths(tmp_path, cheng=CHENG_LEAK))
    except bd.LeakageError as exc:
        raised = True
        assert "LEAKAGE GUARD FAILED" in str(exc)
        assert "who wrote paradise lost" in str(exc)
    assert raised, "leak fixture must trigger LeakageError"


def test_leakage_guard_fails_closed_on_empty_cheng(tmp_path):
    empty = tmp_path / "empty_cheng.jsonl"
    empty.write_text("", encoding="utf-8")
    raised = False
    try:
        bd.build_all(_load_config(), "test-model", _paths(tmp_path, cheng=empty))
    except bd.LeakageError:
        raised = True
    assert raised, "empty Cheng test set must fail closed, not pass vacuously"


# ---------------------------------------------------------------------------
# All four arms + output artifacts present.
# ---------------------------------------------------------------------------


def test_all_arms_and_manifest_written(tmp_path):
    bd.build_all(_load_config(), "test-model", _paths(tmp_path))
    expected = [
        "sft_train.jsonl", "sft_dev.jsonl",
        "dpo_train.jsonl", "dpo_dev.jsonl",
        "kto_congruence_train.jsonl", "kto_congruence_dev.jsonl",
        "kto_correctness_safe_train.jsonl", "kto_correctness_safe_dev.jsonl",
        "questions_frozen.json", "build_manifest.json",
    ]
    for name in expected:
        assert (tmp_path / name).exists(), f"missing output: {name}"


# ---------------------------------------------------------------------------
# Invariant 2: budget = distinct source questions.
# ---------------------------------------------------------------------------


def test_budget_is_distinct_questions(tmp_path):
    manifest = bd.build_all(_load_config(), "test-model", _paths(tmp_path))
    probe = bd.load_probe_records(PROBE)
    n_known = sum(1 for r in probe if r["label"] == "known")
    n_unknown = sum(1 for r in probe if r["label"] == "unknown")
    budget = manifest["budget"]
    assert budget["known_questions"] == n_known
    assert budget["unknown_questions"] == n_unknown
    assert budget["distinct_questions"] == n_known + n_unknown


# ---------------------------------------------------------------------------
# Invariant 3: abstention marker invariant.
# ---------------------------------------------------------------------------


def test_bank_validation_rejects_unmarked_phrasing(tmp_path):
    bad_bank = tmp_path / "bad_bank.json"
    bad_bank.write_text(json.dumps({"phrasings": ["Sure, the answer is 42."]}))
    raised = False
    try:
        bd.load_abstention_bank(bad_bank)
    except bd.AbstentionBankError:
        raised = True
    assert raised, "a phrasing with no refusal marker must be rejected"


def test_every_sft_abstention_carries_marker(tmp_path):
    bd.build_all(_load_config(), "test-model", _paths(tmp_path))
    rows = _read_jsonl(tmp_path / "sft_train.jsonl") + _read_jsonl(tmp_path / "sft_dev.jsonl")
    probe_by_id = {r["question_id"]: r for r in bd.load_probe_records(PROBE)}
    # Every assistant turn that corresponds to an unknown question must be a refusal.
    unknown_questions = {
        r["question"] for r in probe_by_id.values() if r["label"] == "unknown"
    }
    for row in rows:
        user = next(m["content"] for m in row["conversations"] if m["role"] == "user")
        assistant = next(m["content"] for m in row["conversations"] if m["role"] == "assistant")
        if user in unknown_questions:
            assert bd.is_refusal(assistant), f"unknown answer not a refusal: {assistant!r}"


# ---------------------------------------------------------------------------
# Invariant 4: dev split excluded from train, shared across arms.
# ---------------------------------------------------------------------------


def test_dev_questions_excluded_from_train_and_shared(tmp_path):
    bd.build_all(_load_config(), "test-model", _paths(tmp_path))
    frozen = json.loads((tmp_path / "questions_frozen.json").read_text())
    dev_ids = set(frozen["dev_question_ids"])
    train_ids = set(frozen["train_question_ids"])
    assert dev_ids and train_ids, "expected non-empty dev and train"
    assert dev_ids.isdisjoint(train_ids), "dev and train question sets must be disjoint"

    # The dev questions are the same set the SFT dev file is built from; spot-check
    # that the SFT dev questions are a subset of the frozen dev_question_ids.
    probe_by_q = {r["question"]: r["question_id"] for r in bd.load_probe_records(PROBE)}
    sft_dev = _read_jsonl(tmp_path / "sft_dev.jsonl")
    for row in sft_dev:
        user = next(m["content"] for m in row["conversations"] if m["role"] == "user")
        assert probe_by_q[user] in dev_ids


# ---------------------------------------------------------------------------
# KTO interleaving + DPO schema.
# ---------------------------------------------------------------------------


def test_kto_congruence_is_interleaved(tmp_path):
    bd.build_all(_load_config(), "test-model", _paths(tmp_path))
    rows = _read_jsonl(tmp_path / "kto_congruence_train.jsonl")
    assert rows, "expected KTO congruence rows"
    labels = [r["label"] for r in rows]
    # Pre-interleaved T/F/T/F: even indices True, odd indices False.
    for i, label in enumerate(labels):
        assert label is (i % 2 == 0), f"interleaving broken at index {i}: {labels}"
    assert sum(labels) == len(labels) - sum(labels), "interleaved set must be balanced"


def test_kto_rows_have_boolean_label_and_conversations(tmp_path):
    bd.build_all(_load_config(), "test-model", _paths(tmp_path))
    for name in ("kto_congruence_train.jsonl", "kto_correctness_safe_train.jsonl"):
        for row in _read_jsonl(tmp_path / name):
            assert isinstance(row["label"], bool)
            assert row["conversations"][-1]["role"] == "assistant"


def test_dpo_schema_shape(tmp_path):
    bd.build_all(_load_config(), "test-model", _paths(tmp_path))
    rows = _read_jsonl(tmp_path / "dpo_train.jsonl")
    assert rows, "expected DPO rows"
    for row in rows:
        assert set(row.keys()) == {"prompt", "chosen", "rejected"}
        assert row["prompt"][-1]["role"] == "user"
        assert row["chosen"][0]["role"] == "assistant"
        assert row["rejected"][0]["role"] == "assistant"
        assert isinstance(row["chosen"][0]["content"], str)
        assert isinstance(row["rejected"][0]["content"], str)


def test_dpo_drops_unknown_without_negative(tmp_path):
    # Fixture question tqa_train_000006 is unknown with EMPTY sampled_answers;
    # with strategy "drop" it must not appear in the DPO file.
    manifest = bd.build_all(_load_config(), "test-model", _paths(tmp_path))
    dropped = manifest["unknown_negative_source"]["dropped_no_negative"]
    assert "tqa_train_000006" in dropped


# ---------------------------------------------------------------------------
# B1 regression: correctness_safe must carry BOTH labels (weights-only ablation).
# ---------------------------------------------------------------------------


def test_correctness_safe_contains_both_labels(tmp_path):
    # B1: correctness_safe used to emit only desirable(True) rows, which the tuner
    # truncates to an empty set / crashes on a zero undesirable count. The
    # weights-only ruling means it emits the SAME four rows as congruence, so the
    # file MUST contain both True and False labels.
    bd.build_all(_load_config(), "test-model", _paths(tmp_path))
    for name in ("kto_correctness_safe_train.jsonl", "kto_correctness_safe_dev.jsonl"):
        rows = _read_jsonl(tmp_path / name)
        labels = {r["label"] for r in rows}
        assert True in labels, f"{name}: missing desirable(True) rows"
        assert False in labels, f"{name}: missing undesirable(False) rows -> would crash trainer"


def test_correctness_safe_and_congruence_have_same_label_multiset(tmp_path):
    # Weights-only ablation: the two mappings differ ONLY in training-time weights,
    # so their emitted row sets (hence label multisets) are identical.
    bd.build_all(_load_config(), "test-model", _paths(tmp_path))
    cong = sorted(r["label"] for r in _read_jsonl(tmp_path / "kto_congruence_train.jsonl"))
    safe = sorted(r["label"] for r in _read_jsonl(tmp_path / "kto_correctness_safe_train.jsonl"))
    assert cong == safe, "correctness_safe and congruence must emit the same label multiset"


def test_correctness_safe_is_interleaved(tmp_path):
    # The B1 fix also added correctness_safe to the pre-interleave path.
    bd.build_all(_load_config(), "test-model", _paths(tmp_path))
    labels = [r["label"] for r in _read_jsonl(tmp_path / "kto_correctness_safe_train.jsonl")]
    for i, label in enumerate(labels):
        assert label is (i % 2 == 0), f"correctness_safe interleaving broken at {i}: {labels}"


# ---------------------------------------------------------------------------
# MA1: gold_answer prefers natural-case answer_value, falls back to alias.
# ---------------------------------------------------------------------------


def test_gold_answer_prefers_natural_case_value():
    rec = {"question_id": "q", "answer_value": "John Milton", "normalized_aliases": ["john milton"]}
    assert bd.gold_answer(rec) == "John Milton"


def test_gold_answer_falls_back_to_alias_when_value_absent():
    rec = {"question_id": "q", "normalized_aliases": ["paris"]}
    assert bd.gold_answer(rec) == "paris"


def test_gold_answer_falls_back_when_value_blank():
    rec = {"question_id": "q", "answer_value": "   ", "normalized_aliases": ["paris"]}
    assert bd.gold_answer(rec) == "paris"


def test_known_sft_target_uses_natural_case_from_fixture(tmp_path):
    # Fixture tqa_train_000001 carries answer_value "John Milton" (natural case)
    # while its normalized_aliases are lowercased; the SFT target must be the
    # natural-case form.
    bd.build_all(_load_config(), "test-model", _paths(tmp_path))
    rows = _read_jsonl(tmp_path / "sft_train.jsonl") + _read_jsonl(tmp_path / "sft_dev.jsonl")
    milton = [
        r for r in rows
        if any(m["content"] == "Who wrote Paradise Lost?" for m in r["conversations"])
    ]
    assert milton, "Paradise Lost question should appear in SFT output"
    target = next(m["content"] for m in milton[0]["conversations"] if m["role"] == "assistant")
    assert target == "John Milton", f"expected natural-case gold, got {target!r}"


# ---------------------------------------------------------------------------
# MT3: distractor negative-sourcing strategy.
# ---------------------------------------------------------------------------


def test_distractor_strategy_substitutes_and_records(tmp_path):
    # With strategy "distractor", an unknown question lacking a hallucinated
    # sample (tqa_train_000006) gets the distractor text as its DPO rejected /
    # KTO False completion, and its question_id lands in distractor_substituted.
    config = _load_config()
    config["unknown_negative_source"]["strategy"] = "distractor"
    distractor = config["unknown_negative_source"]["distractor_text"]
    manifest = bd.build_all(config, "test-model", _paths(tmp_path))

    substituted = manifest["unknown_negative_source"]["distractor_substituted"]
    assert "tqa_train_000006" in substituted
    assert not manifest["unknown_negative_source"]["dropped_no_negative"], (
        "distractor strategy should drop nothing"
    )
    # The distractor appears as a DPO rejected completion.
    dpo = _read_jsonl(tmp_path / "dpo_train.jsonl") + _read_jsonl(tmp_path / "dpo_dev.jsonl")
    rejected_contents = {r["rejected"][0]["content"] for r in dpo}
    assert distractor in rejected_contents
    # And as a KTO False completion.
    kto = _read_jsonl(tmp_path / "kto_congruence_train.jsonl")
    false_contents = {
        r["conversations"][-1]["content"] for r in kto if r["label"] is False
    }
    assert distractor in false_contents


# ---------------------------------------------------------------------------
# FT5: split_dev boundary guards.
# ---------------------------------------------------------------------------


def _q(qid):
    return {"question_id": qid}


def test_split_dev_raises_on_empty_dev():
    # 3 questions x fraction 0.1 -> round(0.3) = 0 dev examples -> raise.
    raised = False
    try:
        bd.split_dev([_q("a"), _q("b"), _q("c")], fraction=0.1, seed=42)
    except bd.DevSplitError:
        raised = True
    assert raised, "dev=0 must raise DevSplitError"


def test_split_dev_raises_on_empty_train():
    raised = False
    try:
        bd.split_dev([_q("a"), _q("b"), _q("c")], fraction=1.0, seed=42)
    except bd.DevSplitError:
        raised = True
    assert raised, "train=0 (fraction=1.0) must raise DevSplitError"


def test_split_dev_normal_case_both_nonempty():
    train, dev = bd.split_dev([_q(str(i)) for i in range(10)], fraction=0.3, seed=42)
    assert len(dev) == 3 and len(train) == 7
    dev_ids = {r["question_id"] for r in dev}
    train_ids = {r["question_id"] for r in train}
    assert dev_ids.isdisjoint(train_ids)


# ---------------------------------------------------------------------------
# FT6: interleave_kto truncation on imbalanced input.
# ---------------------------------------------------------------------------


def test_interleave_kto_truncates_majority_class():
    # 7 True / 3 False -> balanced to 3 each (6 rows), 4 trues dropped, T/F/T/F.
    rows = [{"label": True, "i": i} for i in range(7)] + [{"label": False, "i": i} for i in range(3)]
    out = bd.interleave_kto(rows, seed=42)
    labels = [r["label"] for r in out]
    assert len(out) == 6, f"expected 6 balanced rows, got {len(out)}"
    assert labels == [True, False, True, False, True, False], f"not interleaved: {labels}"
    assert sum(1 for r in out if r["label"] is True) == 3
    assert sum(1 for r in out if r["label"] is False) == 3


def test_interleave_kto_empty_on_single_class():
    # All-True input -> min(n_true, 0) = 0 -> empty (this is exactly the failure
    # mode the B1 fix prevents upstream by always emitting both labels).
    rows = [{"label": True, "i": i} for i in range(5)]
    assert bd.interleave_kto(rows, seed=42) == []


# ---------------------------------------------------------------------------
# FB1: leakage guard re-derives the probe-side key, never trusts stored norm.
# ---------------------------------------------------------------------------


def test_leakage_guard_ignores_stale_stored_question_norm():
    # A probe record whose stored question_norm is STALE/benign but whose real
    # question normalizes INTO the Cheng set must still be caught: the guard
    # re-derives via norm_question and ignores the stored field.
    probe = [{
        "question_id": "q1",
        "question": "Who wrote Paradise Lost?",
        "question_norm": "totally benign unrelated string",
    }]
    cheng = {bd.norm_question("Who wrote Paradise Lost?")}
    raised = False
    try:
        bd.assert_no_leakage(probe, cheng)
    except bd.LeakageError:
        raised = True
    assert raised, "stale stored question_norm must not let a real leak slip through"


# ---------------------------------------------------------------------------
# Determinism.
# ---------------------------------------------------------------------------


def test_build_is_deterministic(tmp_path):
    out_a = tmp_path / "a"
    out_b = tmp_path / "b"
    bd.build_all(_load_config(), "test-model", _paths(out_a))
    bd.build_all(_load_config(), "test-model", _paths(out_b))
    for name in ("sft_train.jsonl", "dpo_train.jsonl", "kto_congruence_train.jsonl"):
        assert (out_a / name).read_bytes() == (out_b / name).read_bytes(), (
            f"non-deterministic output: {name}"
        )


# ---------------------------------------------------------------------------
# Direct-run harness (no pytest dependency).
# ---------------------------------------------------------------------------


def _run_all():
    import inspect
    import tempfile
    import traceback

    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    passed = failed = 0
    for test in tests:
        # Mirror pytest's tmp_path injection: only pass a temp dir to tests that
        # declare a parameter; zero-arg unit tests are called bare.
        takes_arg = len(inspect.signature(test).parameters) > 0
        with tempfile.TemporaryDirectory() as td:
            try:
                test(Path(td)) if takes_arg else test()
                passed += 1
                print(f"PASS {test.__name__}")
            except Exception:  # noqa: BLE001 - smoke harness surfaces all failures
                failed += 1
                print(f"FAIL {test.__name__}")
                traceback.print_exc()
    print(f"\n{passed} passed, {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(_run_all())
