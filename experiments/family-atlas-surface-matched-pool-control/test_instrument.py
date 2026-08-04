from __future__ import annotations

import hashlib
import json
import random
import sys
from pathlib import Path

import numpy as np
import pytest
from scipy import sparse

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from analyze_profiles import _peak, bootstrap_auroc_ci, planted_location_control, random_unit_direction
from capture_full_depth import capture_content_digest, repair_invalid_rows, tensor_sha256, validate_activation_bundle
import instrument_common
from instrument_common import containment_lint, gate, load_jsonl
from match_and_gate import ROLES, build_triads, grouped_pairwise_classifier, stage_row_exhaust
from grader_port import grade_generation
from source_and_generate import (
    BaselineRunLog, derive_finish_evidence, materialize_source, render_prompt,
    resolve_eos_ids,
)


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")


def test_umwp_bookkeeping_answers_are_never_materialized_as_aliases(tmp_path: Path) -> None:
    rows = [
        {"id": 1, "answerable": True, "source": "GSM8K", "question": "q", "answer": [7], "category": None},
        {"id": 2613, "answerable": False, "source": "GSM8K", "question": "u1", "answer": [999], "category": 1, "relevant_ids": [1]},
        {"id": 4258, "answerable": False, "source": "GSM8K", "question": "u2", "answer": [888], "category": 2, "relevant_ids": [1]},
    ]
    source = tmp_path / "source.jsonl"
    _write_jsonl(source, rows)
    cfg = {"source": {"raw_sha256": hashlib.sha256(source.read_bytes()).hexdigest(), "expected_rows": 3, "expected_answerable": 1, "expected_unanswerable": 2, "native_source_counts": {"GSM8K": {"answerable": 1, "unanswerable": 2}}}}
    out = tmp_path / "private" / "rows.jsonl"
    materialize_source(source, out, cfg)
    materialized = load_jsonl(out)
    assert [r["aliases"] for r in materialized if not r["answerable"]] == [[], []]


@pytest.mark.parametrize(
    ("answer", "alias", "correct"),
    [("1", "1", True), ("10", "1", False), ("-2", "-2", True), ("1.25", "1.25", True)],
)
def test_numeric_grader_respects_token_boundaries(answer: str, alias: str, correct: bool) -> None:
    text = json.dumps({"answer": answer, "response_confidence": 0.9})
    result = grade_generation(text, [alias], True)
    assert result["full_grader_dict"]["correct"] is correct


def test_grader_covers_refusal_malformed_degenerate_and_wrong() -> None:
    refusal = grade_generation(json.dumps({"answer": "I don't know", "response_confidence": 0.2}), None, True)
    malformed = grade_generation("not json", ["1"], True)
    degenerate = grade_generation(json.dumps({"answer": "x " * 50, "response_confidence": 0.2}), ["1"], True)
    wrong = grade_generation(json.dumps({"answer": "2", "response_confidence": 0.9}), ["1"], True)
    assert refusal["full_grader_dict"]["clean_tighten"]
    assert not malformed["full_grader_dict"]["well_formed"]
    assert degenerate["full_grader_dict"]["degenerate"]
    assert not wrong["full_grader_dict"]["correct"]


def test_standard_raw_refusal_and_clean_tighten_remain_distinct() -> None:
    result = grade_generation(json.dumps({"answer": "I do not know", "response_confidence": 0.2}), None, True)
    assert result["full_grader_dict"]["refused"] is True
    assert result["full_grader_dict"]["clean_tighten"] is False


def test_grader_rejects_bad_confidence_and_never_scores_confidence_number() -> None:
    bad = grade_generation(json.dumps({"answer": "1", "response_confidence": 2.0}), ["1"], True)
    leakage = grade_generation(json.dumps({"answer": "1", "response_confidence": 0.10}), ["10"], True)
    assert not bad["full_grader_dict"]["well_formed"]
    assert not leakage["full_grader_dict"]["correct"]


class _FakeTokenizer:
    chat_template = "template"
    eos_token_id = 1
    unk_token_id = 0

    def __init__(self):
        self.calls = []

    def apply_chat_template(self, messages, **kwargs):
        self.calls.append((messages, kwargs))
        return f"PROMPT:{messages[-1]['content']}"

    def __call__(self, prompt, **kwargs):
        return {"input_ids": [ord(c) for c in prompt]}

    def convert_tokens_to_ids(self, token):
        return {"<|im_end|>": 2, "<end_of_turn>": 3}.get(token, self.unk_token_id)


def test_resolve_eos_ids_includes_model_chat_terminators() -> None:
    assert resolve_eos_ids(_FakeTokenizer()) == [1, 2, 3]


@pytest.mark.parametrize("model_id", ["gemma4_e4b_it", "qwen3_4b_raw_base"])
def test_model_specific_render_dispatch_has_generation_capture_token_parity(model_id: str) -> None:
    tokenizer = _FakeTokenizer()
    row = {"row_key": "umwp:1", "question": "How many?"}
    generation_prompt = render_prompt(model_id, tokenizer, row)
    capture_prompt = render_prompt(model_id, tokenizer, row)
    assert generation_prompt == capture_prompt
    assert tokenizer(generation_prompt, add_special_tokens=True)["input_ids"] == tokenizer(capture_prompt, add_special_tokens=True)["input_ids"]
    assert tokenizer.calls[0][1]["enable_thinking"] is False


def _candidate(role: str, idx: int) -> dict:
    return {
        "row_key": f"umwp:{role}:{idx}", "role": role, "native_source": "GSM8K",
        "category_canon": "1" if role != "known_correct_answered" else None,
        "original_pair_id": f"{role}:{idx}", "matching_vector": [0.0, 0.0],
    }


def test_matching_is_deterministic_under_equal_costs_and_input_shuffle() -> None:
    rows = [_candidate(role, idx) for role in ROLES for idx in range(4)]
    first = build_triads(rows, 20260721)
    random.Random(99).shuffle(rows)
    second = build_triads(rows, 20260721)
    simplify = lambda triads: [(t["triad_id"], t["split"], {k: v["row_key"] for k, v in t["rows"].items()}) for t in triads]
    assert simplify(first) == simplify(second)
    assert all(len({r["original_pair_id"] for r in t["rows"].values()}) == 3 for t in first)


def test_grouped_pairwise_positive_control_is_reachable() -> None:
    rows = []
    for triad in range(10):
        for role in ROLES:
            rows.append({"role": role, "triad_id": f"t{triad}"})
    features = sparse.csr_matrix((len(rows), 2), dtype=np.float64)
    result = grouped_pairwise_classifier(features, rows, plant_role_tag=True, folds=5)
    assert set(result) == {"known_correct_answered_vs_confab", "known_correct_answered_vs_unknown_refused", "confab_vs_unknown_refused"}
    assert min(result.values()) >= 0.90


def _log_record(row_key: str) -> dict:
    full = {
        "well_formed": True, "n_answer_keys": 1, "single_answer_key": True,
        "trailing_clean": True, "answered": True, "correct": True,
        "well_formed_correct": True, "refused": False,
        "semantic_refuse": False, "degenerate": False, "clean_tighten": False,
        "confidence_valid": True, "terminated_naturally": True,
    }
    return {
        "row_key": row_key, "source": "umwp", "native_source": "GSM8K", "original_pair_id": row_key,
        "category_canon": None, "umwp_id": row_key, "answerable": True,
        "model": "m", "model_revision": "r", "renderer_id": "render",
        "seed": 1, "generation_text": "raw output", "answer_value": "7", "terminated_naturally": True,
        "n_new_tokens": 3, "full_grader_dict": full, "role": "known_correct_answered", "split": None,
        "triad_id": None, "cell_id": "m", "layer": None, "arm": "baseline",
        "dose_or_strength": 0.0, **full,
        "finish_reason": "eos_token", "last_completion_token_id": 1,
        "eos_token_ids": [1, 2],
    }


def test_run_log_persists_full_subgrades_and_resumes_after_kill(tmp_path: Path) -> None:
    path = tmp_path / "rows.jsonl"
    BaselineRunLog(path).append(_log_record("umwp:1"))
    resumed = BaselineRunLog(path)
    resumed.append(_log_record("umwp:1"))
    resumed.append(_log_record("umwp:2"))
    rows = load_jsonl(path)
    assert [r["row_key"] for r in rows] == ["umwp:1", "umwp:2"]
    assert rows[0]["generation_text"] == "raw output"
    assert rows[0]["full_grader_dict"]["well_formed_correct"] is True
    assert rows[0]["dose_or_strength"] == 0.0


def test_run_log_rejects_boolean_only_record(tmp_path: Path) -> None:
    record = _log_record("umwp:1")
    record["full_grader_dict"] = {}
    with pytest.raises(ValueError, match="complete grader"):
        BaselineRunLog(tmp_path / "rows.jsonl").append(record)


def test_run_log_rejects_flattened_grader_mismatch(tmp_path: Path) -> None:
    record = _log_record("umwp:1")
    record["correct"] = False
    with pytest.raises(ValueError, match="differ"):
        BaselineRunLog(tmp_path / "rows.jsonl").append(record)


def test_low_yield_path_stages_standard_row_exhaust(tmp_path: Path) -> None:
    private = _log_record("umwp:1")
    out = tmp_path / "rows.jsonl"
    stage_row_exhaust("m", [private], [], out)
    staged = load_jsonl(out)
    assert len(staged) == 1
    assert staged[0]["split"] is None and staged[0]["triad_id"] is None
    assert "last_completion_token_id" not in staged[0]
    assert "eos_token_ids" not in staged[0]


def test_finish_evidence_is_reconstructed_from_private_tokens() -> None:
    assert derive_finish_evidence(3, 200, 2, [1, 2]) == ("eos_token", True)
    assert derive_finish_evidence(3, 200, 9, [1, 2]) == ("stopping_criteria", True)
    assert derive_finish_evidence(200, 200, 2, [1, 2]) == ("eos_token", True)
    assert derive_finish_evidence(200, 200, 9, [1, 2]) == ("length", False)


def test_activation_index_detects_tensor_mutation(tmp_path: Path) -> None:
    from safetensors.numpy import save_file
    root = tmp_path / "activations"
    (root / "shards").mkdir(parents=True)
    tensor = np.asarray([1.0, 2.0], dtype=np.float32)
    shard = root / "shards" / "row.safetensors"
    save_file({"hs_000": tensor}, str(shard))
    digest = tensor_sha256(tensor)
    content = capture_content_digest("umwp:1", "tokens", 4, "model", "revision", [digest])
    record = {"row_key": "umwp:1", "hs_index": 0, "shard_key": "shards/row.safetensors", "dtype": "float32", "shape": [2], "anchor_index": 4, "token_ids_sha256": "tokens", "model": "model", "model_revision": "revision", "tensor_sha256": digest, "instrument_fingerprint": "f", "capture_content_digest": content}
    _write_jsonl(root / "activation_index.jsonl", [record])
    assert validate_activation_bundle(root, 1, "model", "revision", "f")["status"] == "pass"
    save_file({"hs_000": np.asarray([1.0, 3.0], dtype=np.float32)}, str(shard))
    assert validate_activation_bundle(root, 1, "model", "revision", "f")["status"] == "fail"


def test_activation_validation_recomputes_private_token_digest_and_rejects_extras(tmp_path: Path) -> None:
    from safetensors.numpy import save_file
    root = tmp_path / "activations"
    (root / "shards").mkdir(parents=True)
    token_ids = [4, 5]
    token_digest = hashlib.sha256(json.dumps(token_ids, separators=(",", ":")).encode()).hexdigest()
    tensor = np.asarray([1.0], dtype=np.float32)
    tensor_digest = tensor_sha256(tensor)
    save_file({"hs_000": tensor}, str(root / "shards" / "row.safetensors"))
    record = {"row_key": "umwp:1", "hs_index": 0, "shard_key": "shards/row.safetensors", "dtype": "float32", "shape": [1], "anchor_index": 1, "token_ids_sha256": token_digest, "model": "model", "model_revision": "revision", "tensor_sha256": tensor_digest, "instrument_fingerprint": "f", "capture_content_digest": capture_content_digest("umwp:1", token_digest, 1, "model", "revision", [tensor_digest])}
    _write_jsonl(root / "activation_index.jsonl", [record])
    inputs = tmp_path / "inputs.jsonl"
    input_record = {
        "row_key": "umwp:1", "token_ids": token_ids,
        "token_ids_sha256": token_digest, "anchor_index": 1,
        "model": "model", "model_revision": "revision",
        "instrument_fingerprint": "f",
    }
    _write_jsonl(inputs, [input_record])
    assert validate_activation_bundle(root, 1, "model", "revision", "f", inputs, {"umwp:1"})["status"] == "pass"
    _write_jsonl(inputs, [{**input_record, "token_ids": [4, 6]}])
    assert validate_activation_bundle(root, 1, "model", "revision", "f", inputs, {"umwp:1"})["status"] == "fail"
    _write_jsonl(inputs, [{**input_record, "instrument_fingerprint": "stale"}])
    assert validate_activation_bundle(root, 1, "model", "revision", "f", inputs, {"umwp:1"})["status"] == "fail"
    assert validate_activation_bundle(root, 1, "model", "revision", "f", inputs, {"umwp:1", "umwp:2"})["status"] == "fail"


def test_malformed_activation_index_fails_closed_without_raising(tmp_path: Path) -> None:
    root = tmp_path / "activations"
    root.mkdir()
    _write_jsonl(root / "activation_index.jsonl", [{"row_key": "umwp:1"}])
    result = validate_activation_bundle(root, 1, "model", "revision", "f")
    assert result["status"] == "fail"
    assert "missing" in result["errors"][0]


def test_corrupt_resume_removes_invalid_row_then_accepts_recapture(tmp_path: Path) -> None:
    from safetensors.numpy import save_file
    root = tmp_path / "activations"
    (root / "shards").mkdir(parents=True)
    tensor = np.asarray([1.0, 2.0], dtype=np.float32)
    digest = tensor_sha256(tensor)
    shard = root / "shards" / "row.safetensors"
    save_file({"hs_000": np.asarray([9.0, 9.0], dtype=np.float32)}, str(shard))
    record = {"row_key": "umwp:1", "hs_index": 0, "shard_key": "shards/row.safetensors", "dtype": "float32", "shape": [2], "anchor_index": 4, "token_ids_sha256": "tokens", "model": "model", "model_revision": "revision", "tensor_sha256": digest, "instrument_fingerprint": "f", "capture_content_digest": capture_content_digest("umwp:1", "tokens", 4, "model", "revision", [digest])}
    _write_jsonl(root / "activation_index.jsonl", [record])
    kept, completed = repair_invalid_rows(root, 1, "model", "revision", "f")
    assert kept == [] and completed == set() and not shard.exists()
    save_file({"hs_000": tensor}, str(shard))
    _write_jsonl(root / "activation_index.jsonl", [record])
    assert validate_activation_bundle(root, 1, "model", "revision", "f")["status"] == "pass"


@pytest.mark.parametrize(("input_anchor", "index_anchor"), [(2, 1), (1, 2)])
def test_corrupt_anchor_is_removed_for_recapture(
    tmp_path: Path, input_anchor: int, index_anchor: int,
) -> None:
    from safetensors.numpy import save_file
    root = tmp_path / "activations"
    (root / "shards").mkdir(parents=True)
    token_ids = [4, 5]
    token_digest = hashlib.sha256(json.dumps(token_ids, separators=(",", ":")).encode()).hexdigest()
    tensor = np.asarray([1.0], dtype=np.float32)
    tensor_digest = tensor_sha256(tensor)
    shard = root / "shards" / "row.safetensors"
    save_file({"hs_000": tensor}, str(shard))
    record = {
        "row_key": "umwp:1", "hs_index": 0, "shard_key": "shards/row.safetensors",
        "dtype": "float32", "shape": [1], "anchor_index": index_anchor,
        "token_ids_sha256": token_digest, "model": "model", "model_revision": "revision",
        "tensor_sha256": tensor_digest, "instrument_fingerprint": "f",
        "capture_content_digest": capture_content_digest(
            "umwp:1", token_digest, index_anchor, "model", "revision", [tensor_digest]
        ),
    }
    _write_jsonl(root / "activation_index.jsonl", [record])
    inputs = {"umwp:1": {
        "row_key": "umwp:1", "token_ids": token_ids, "token_ids_sha256": token_digest,
        "anchor_index": input_anchor, "model": "model", "model_revision": "revision",
        "instrument_fingerprint": "f",
    }}
    kept, completed = repair_invalid_rows(
        root, 1, "model", "revision", "f", inputs, {"umwp:1"}
    )
    assert kept == [] and completed == set() and not shard.exists()


def test_containment_lint_rejects_prohibited_fields_and_private_text(tmp_path: Path) -> None:
    committed = tmp_path / "analysis-committed"
    committed.mkdir()
    (committed / "bad.json").write_text(json.dumps({"generation_text": "secret completion"}))
    result = containment_lint(committed, private_texts=["secret completion"])
    assert result["status"] == "fail"
    assert len(result["errors"]) == 2


def test_gate_schema_is_strictly_tristate() -> None:
    assert gate("not_run", {})["status"] == "not_run"
    with pytest.raises(ValueError):
        gate("skipped", {})


def test_high_rank_location_plant_is_reachable() -> None:
    class Reader:
        def matrix(self, row_keys, hs):
            x = np.linspace(-1, 1, len(row_keys))[:, None]
            return np.repeat(x, 24, axis=1)
    base_profile = [{"hs_index": i, "eff_dim_frac": 1 / 24} for i in range(5)]
    result = planted_location_control(Reader(), [f"r{i}" for i in range(24)], base_profile, 2, [0.25, 0.5, 1, 2, 4, 8, 16], 20260722)
    assert result["status"] == "pass"
    assert result["planted_hs_index"] == 2


def test_bootstrap_and_random_direction_match_standard_seed_contract() -> None:
    scores = np.asarray([0.9, 0.8, 0.2, 0.1])
    labels = np.asarray([1, 1, 0, 0])
    first = bootstrap_auroc_ci(scores, labels, n_resamples=2000, seed=20260707)
    second = bootstrap_auroc_ci(scores, labels, n_resamples=2000, seed=20260707)
    assert first == second
    assert first["point"] == 1.0 and first["n_resamples"] == 2000
    expected = np.random.default_rng([20260707, 3]).normal(size=5)
    expected /= np.linalg.norm(expected)
    assert np.allclose(random_unit_direction(5, 3, 20260707), expected)


def test_capture_content_digest_binds_identity_and_anchor() -> None:
    base = capture_content_digest("umwp:1", "tokens", 4, "model", "revision", ["tensor"])
    assert base != capture_content_digest("umwp:2", "tokens", 4, "model", "revision", ["tensor"])
    assert base != capture_content_digest("umwp:1", "tokens", 5, "model", "revision", ["tensor"])


def test_real_peak_tie_is_explicit() -> None:
    peak = _peak([{"eff_dim_frac": 0.2}, {"eff_dim_frac": 0.2}, {"eff_dim_frac": 0.1}], 3)
    assert peak["tie_count"] == 2


def test_instrument_fingerprint_verifies_live_pins(monkeypatch, tmp_path: Path) -> None:
    (tmp_path / "cell.yaml").write_text("seed: 1\n")
    digest = hashlib.sha256((tmp_path / "cell.yaml").read_bytes()).hexdigest()
    (tmp_path / "experiment.yaml").write_text(
        "instrument:\n  configs: [cell.yaml]\n  modules: []\n  pins:\n"
        f"    cell.yaml: {digest}\n"
    )
    monkeypatch.setattr(instrument_common, "ROOT", tmp_path)
    assert instrument_common.instrument_fingerprint()
    (tmp_path / "cell.yaml").write_text("seed: 2\n")
    with pytest.raises(RuntimeError, match="differ"):
        instrument_common.instrument_fingerprint()
