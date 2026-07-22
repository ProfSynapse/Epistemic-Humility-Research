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
import presign_smoke
import source_and_generate
from instrument_common import containment_lint, gate, load_jsonl, source_fingerprint
from match_and_gate import ROLES, build_triads, grouped_pairwise_classifier, stage_row_exhaust
from presign_smoke import (
    RUN_NAMES, compare_repeat_rows, planted_matcher_reachability, select_smoke_rows,
    smoke_evidence_rows,
    validate_required_failure_outcomes, validate_smoke_context,
)
from grader_port import grade_generation
from source_and_generate import (
    BaselineRunLog, _generation_config, _load_vllm_completions,
    _load_vllm_provenance, build_vllm_command, derive_finish_evidence,
    generation_config_sha256, materialize_source, render_prompt,
    load_prior_failure_manifest, load_prior_smoke_ids,
    resolve_eos_ids, validate_structured_completion,
    validate_predecessor_parity, validate_suppression_mapping,
)


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")


def test_pinned_tuner_source_fingerprint_matches_runtime_without_git() -> None:
    import yaml

    cfg = yaml.safe_load((HERE / "cell.yaml").read_text(encoding="utf-8"))
    spec = cfg["generation"]["vllm"]["synaptic_tuner_source"]
    observed = source_fingerprint(HERE.parents[1] / spec["root"], spec["files"])
    assert observed["sha256"] == spec["sha256"]


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
        "suppressed_token_strings": ["<stop>"],
        "suppressed_token_ids": [9],
        "prompt_token_ids_sha256": hashlib.sha256(b"[4,5]").hexdigest(),
        "completion_token_ids": [7, 8, 1],
        "prompt_token_count": 2, "schema_valid": True,
        "generation_engine": "vllm", "generation_engine_version": "0.23.0",
        "generation_config_sha256": "config", "batch_invariant": True,
        "structured_output_backend": "xgrammar",
        "structured_output_disable_any_whitespace": True,
        "prompt_bytes_sha256": "prompt", "parsed_object": {
            "answer": "7", "response_confidence": 0.9,
        },
        "vllm_version": "0.23.0", "vllm_model_runner": "v1",
        "image_digest": "sha256:" + "a" * 64,
        "runtime_versions": {"vllm": "0.23.0"}, "schema_sha256": "schema",
        "scheduler_pins": {"batch_size": 32},
        "checkpoint_config_sha256": "checkpoint", "resume_history": [],
        "loader_pins": {"trust_remote_code": False},
        "hardware_pins": {
            "minimum_compute_capability": "8.0",
            "registered_compute_capability": "8.6",
            "hardware_class": "NVIDIA_RTX_3090_sm86",
            "registered_host_driver": "591.86",
        },
        "synaptic_tuner_source_fingerprint": "tuner-source",
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
    assert "prompt_token_ids" not in staged[0]
    assert "completion_token_ids" not in staged[0]


def _vllm_test_cfg() -> dict:
    schema = {
        "type": "object",
        "properties": {
            "answer": {"type": "string"},
            "response_confidence": {
                "type": "number", "minimum": 0, "maximum": 1,
            },
        },
        "required": ["answer", "response_confidence"],
        "additionalProperties": False,
    }
    return {
        "seed": 20260721,
        "models": {
            "gemma4_e4b_it": {
                "repo": "model", "revision": "revision",
                "tokenizer_revision": "revision",
            },
            "qwen3_4b_raw_base": {
                "repo": "qwen", "revision": "qwen-revision",
                "tokenizer_revision": "qwen-revision",
            },
        },
        "generation": {
            "batch_size": 16, "compute_dtype": "bfloat16",
            "min_new_tokens": 1, "max_new_tokens": 512,
            "canonical_eos_enabled": True,
            "vllm": {
                "expected_version": "0.23.0", "model_runner": "v1",
                "compute_dtype": "bfloat16",
                "trust_remote_code": False,
                "tensor_parallel_size": 1, "max_model_len": 2048,
                "gpu_memory_utilization": 0.90,
                "max_num_seqs": 32,
                "max_num_batched_tokens": 8192, "batch_invariant": True,
                "per_model": {
                    "gemma4_e4b_it": {
                        "limit_mm_per_prompt": {"image": 0, "audio": 0, "video": 0},
                        "suppress_tokens": [
                            {"token": "<turn|>", "expected_id": 106},
                            {"token": "<|tool_response>", "expected_id": 50},
                        ],
                    },
                    "qwen3_4b_raw_base": {
                        "limit_mm_per_prompt": {},
                        "suppress_tokens": [
                            {"token": "<|endoftext|>", "expected_id": 151643},
                        ],
                    },
                },
                "structured_output_backend": "xgrammar", "output_schema": schema,
                "structured_output_disable_any_whitespace": True,
                "synaptic_tuner_source": {
                    "sha256": "tuner-source", "root": "synaptic-tuner",
                    "algorithm": "sha256_canonical_path_digest_size_v1", "files": [],
                },
            },
        },
        "containers": {"generation": {
            "minimum_compute_capability": 8.0,
            "registered_compute_capability": 8.6,
            "hardware_class": "NVIDIA_RTX_3090_sm86",
            "registered_host_driver": 591.86,
        }},
    }


def test_structured_completion_accepts_only_exact_schema() -> None:
    assert validate_structured_completion(
        '{"answer":"7","response_confidence":0.8}'
    )["answer"] == "7"
    bad_values = (
        '{"answer":"7","response_confidence":0.8} trailing',
        '{"answer":"7","response_confidence":0.8,"extra":1}',
        '{"answer":7,"response_confidence":0.8}',
        '{"answer":"7","response_confidence":true}',
    )
    for bad in bad_values:
        with pytest.raises(ValueError):
            validate_structured_completion(bad)


def test_vllm_command_pins_schema_scheduler_and_invariance(tmp_path: Path) -> None:
    command = build_vllm_command(
        _vllm_test_cfg(), "gemma4_e4b_it", tmp_path / "prompts.jsonl",
        tmp_path / "out", tmp_path / "schema.json", resume=True,
    )
    assert command[2:5] == ["batch-generate", "--engine", "vllm"]
    assert "--json-schema" in command
    assert "--expected-vllm-version" in command
    assert command[command.index("--vllm-model-runner") + 1] == "v1"
    assert "--max-num-seqs" in command
    assert "--max-num-batched-tokens" in command
    assert command[command.index("--structured-output-backend") + 1] == "xgrammar"
    assert "--structured-output-disable-any-whitespace" in command
    assert command[command.index("--max-model-len") + 1] == "2048"
    assert command[command.index("--batch-size") + 1] == "16"
    assert command[command.index("--max-new-tokens") + 1] == "512"
    assert command[command.index("--gpu-memory-utilization") + 1] == "0.9"
    assert command[command.index("--min-compute-capability") + 1] == "8.0"
    assert "--trust-remote-code" not in command
    assert json.loads(command[command.index("--limit-mm-per-prompt") + 1]) == {
        "image": 0, "audio": 0, "video": 0,
    }
    assert command[command.index("--json-schema") + 1].endswith("schema.json")
    suppression_values = [
        command[index + 1]
        for index, value in enumerate(command)
        if value == "--suppress-token"
    ]
    assert suppression_values == ["<turn|>", "<|tool_response>"]
    assert "--ignore-eos" not in command
    assert command[-1] == "--resume"


def test_vllm_command_preserves_empty_qwen_multimodal_limit(tmp_path: Path) -> None:
    command = build_vllm_command(
        _vllm_test_cfg(), "qwen3_4b_raw_base", tmp_path / "prompts.jsonl",
        tmp_path / "out", tmp_path / "schema.json", resume=False,
    )
    assert json.loads(command[command.index("--limit-mm-per-prompt") + 1]) == {}
    assert command[command.index("--suppress-token") + 1] == "<|endoftext|>"
    assert "--resume" not in command


def test_surface_preparation_binds_rows_prompts_tokens_and_artifacts(
    tmp_path: Path, monkeypatch,
) -> None:
    monkeypatch.setattr(source_and_generate, "ANALYSIS", tmp_path)
    model_id = "gemma4_e4b_it"
    surface = tmp_path / model_id / "surface"
    surface.mkdir(parents=True)
    (surface / "basis.joblib").write_bytes(b"basis")
    _write_jsonl(surface / "coordinates.jsonl", [
        {"row_key": "umwp:1", "scalars": {}, "matching_vector": [0.0]},
    ])
    rows = [{"row_key": "umwp:1"}]
    prompts = ["prompt"]
    token_ids = [[4, 5]]
    digest = "sha256:" + "a" * 64
    record = {
        "schema_version": 1,
        "model_id": model_id,
        "capture_image_digest": digest,
        "surface_input_fingerprint": source_and_generate._surface_input_fingerprint(
            rows, prompts, token_ids
        ),
        "basis_sha256": source_and_generate.sha256_file(surface / "basis.joblib"),
        "coordinates_sha256": source_and_generate.sha256_file(
            surface / "coordinates.jsonl"
        ),
        "runtime_versions": {
            "scikit_learn": "1.0", "scipy": "1.0", "joblib": "1.0",
        },
    }
    (surface / "preparation.json").write_text(
        json.dumps(record), encoding="utf-8"
    )
    cfg = {"containers": {"capture": {"image_digest": digest}}}
    assert source_and_generate._validate_surface_preparation(
        cfg, model_id, rows, prompts, token_ids
    ) == record

    with pytest.raises(ValueError, match="signed generation inputs"):
        source_and_generate._validate_surface_preparation(
            cfg, model_id, rows, ["changed"], token_ids
        )


def test_vllm_provenance_binds_backend_context_and_multimodal_pins(tmp_path: Path) -> None:
    gen = _generation_config(_vllm_test_cfg(), "gemma4_e4b_it")
    schema_hash = generation_config_sha256(gen["output_schema"])
    config = {
        "model": gen["model"], "model_revision": gen["model_revision"],
        "tokenizer_revision": gen["tokenizer_revision"], "engine": "vllm",
        "prompts_sha256": "prompts",
        "batch_size": gen["batch_size"], "max_new_tokens": gen["max_new_tokens"],
        "min_new_tokens": gen["min_new_tokens"], "seed": gen["seed"],
        "dtype": gen["compute_dtype"], "json_schema_sha256": schema_hash,
        "trust_remote_code": False,
        "structured_output_backend": "xgrammar",
        "structured_output_disable_any_whitespace": True,
        "expected_vllm_version": gen["engine_version"],
        "vllm_model_runner": "v1",
        "min_compute_capability": "8.0",
        "vllm_batch_invariant": True,
        "tensor_parallel_size": gen["tensor_parallel_size"],
        "max_num_seqs": gen["max_num_seqs"],
        "max_num_batched_tokens": gen["max_num_batched_tokens"],
        "max_model_len": 2048,
        "limit_mm_per_prompt": {"image": 0, "audio": 0, "video": 0},
        "gpu_memory_utilization": 0.9,
        "suppress_tokens": ["<turn|>", "<|tool_response>"],
    }
    provenance = {
        "config_hash": "checkpoint", "config": config,
        "runtime": {
            "vllm_version": "0.23.0", "vllm_batch_invariant": True,
            "vllm_model_runner": "v1",
            "structured_outputs": True, "structured_output_backend": "xgrammar",
            "structured_output_disable_any_whitespace": True,
            "suppress_tokens": ["<turn|>", "<|tool_response>"],
            "suppressed_token_ids": [106, 50],
            "suppressed_bad_word_token_ids": [[106], [50]],
            "documented_compute_capability_floor": "8.0",
            "effective_compute_capability_floor": "8.0",
            "hardware": {
                "devices": [{
                    "index": 0, "name": "NVIDIA GeForce RTX 3090",
                    "compute_capability": "8.6",
                }],
                "nvidia_driver_versions": ["591.86"],
                "cuda_runtime": "13.0", "torch_version": "2.9.1+cu130",
            },
        },
    }
    path = tmp_path / "provenance.json"
    path.write_text(json.dumps(provenance), encoding="utf-8")
    assert _load_vllm_provenance(
        path, gen, schema_hash, "prompts"
    )["config_hash"] == "checkpoint"
    provenance["config"]["max_model_len"] = 4096
    path.write_text(json.dumps(provenance), encoding="utf-8")
    with pytest.raises(ValueError, match="registered generation config"):
        _load_vllm_provenance(path, gen, schema_hash, "prompts")
    provenance["config"]["max_model_len"] = 2048
    provenance["runtime"]["suppressed_token_ids"] = [106]
    path.write_text(json.dumps(provenance), encoding="utf-8")
    with pytest.raises(ValueError, match="incomplete or inconsistent"):
        _load_vllm_provenance(path, gen, schema_hash, "prompts")


def test_vllm_completion_contract_rejects_token_or_row_mismatch(tmp_path: Path) -> None:
    expected = [{
        "row_key": "umwp:1", "prompt": "prompt",
        "prompt_token_ids_expected": [4, 5],
    }]
    prompt_ids_hash = hashlib.sha256(b"[4,5]").hexdigest()
    valid = {
        "id": "umwp:1",
        "completion_text": '{"answer":"7","response_confidence":0.8}',
        "prompt_token_ids_sha256": prompt_ids_hash,
        "prompt_sha256": hashlib.sha256(b"prompt").hexdigest(),
        "completion_token_ids": [6, 7], "prompt_token_len": 2,
        "finish_reason": "stop",
    }
    path = tmp_path / "completions.jsonl"
    _write_jsonl(path, [valid])
    gen = _generation_config(_vllm_test_cfg(), "gemma4_e4b_it")
    observed = _load_vllm_completions(path, expected, gen)
    assert set(observed) == {"umwp:1"}
    _write_jsonl(path, [{**valid, "prompt_token_ids_sha256": "wrong"}])
    with pytest.raises(ValueError, match="prompt tokens differ"):
        _load_vllm_completions(path, expected, gen)


def test_vllm_completion_contract_rejects_suppressed_token_evidence(
    tmp_path: Path,
) -> None:
    expected = [{
        "row_key": "umwp:1", "prompt": "prompt",
        "prompt_token_ids_expected": [4, 5],
    }]
    row = {
        "id": "umwp:1",
        "completion_text": '{"answer":"7","response_confidence":0.8}',
        "prompt_token_ids_sha256": hashlib.sha256(b"[4,5]").hexdigest(),
        "prompt_sha256": hashlib.sha256(b"prompt").hexdigest(),
        "completion_token_ids": [6, 106, 7], "prompt_token_len": 2,
        "finish_reason": "stop",
    }
    path = tmp_path / "completions.jsonl"
    _write_jsonl(path, [row])
    with pytest.raises(ValueError, match="suppressed token ID"):
        _load_vllm_completions(
            path, expected, _generation_config(_vllm_test_cfg(), "gemma4_e4b_it")
        )


def test_suppression_mapping_requires_exact_single_token_ids() -> None:
    gen = _generation_config(_vllm_test_cfg(), "gemma4_e4b_it")

    class Tokenizer:
        mappings = {"<turn|>": [106], "<|tool_response>": [50]}
        eos_token_id = 1

        def encode(self, token, add_special_tokens):
            assert add_special_tokens is False
            return self.mappings[token]

    assert validate_suppression_mapping(Tokenizer(), gen) == {
        "token_strings": ["<turn|>", "<|tool_response>"],
        "token_ids": [106, 50],
    }
    Tokenizer.mappings["<turn|>"] = [1, 106]
    with pytest.raises(ValueError, match="expected exactly"):
        validate_suppression_mapping(Tokenizer(), gen)


def test_suppression_mapping_rejects_canonical_eos_intersection() -> None:
    gen = _generation_config(_vllm_test_cfg(), "gemma4_e4b_it")

    class Tokenizer:
        eos_token_id = [1, 106]

        def encode(self, token, add_special_tokens):
            return {"<turn|>": [106], "<|tool_response>": [50]}[token]

    with pytest.raises(ValueError, match="intersect canonical"):
        validate_suppression_mapping(Tokenizer(), gen)


def test_predecessor_parity_repairs_only_registered_failures(
    tmp_path: Path, monkeypatch,
) -> None:
    predecessor = tmp_path / "predecessor.jsonl"
    valid_text = '{"answer":"7","response_confidence":0.8}'
    _write_jsonl(predecessor, [
        {
            "id": "umwp:1", "completion_text": valid_text,
            "completion_token_ids": [7, 8], "finish_reason": "stop",
        },
        {
            "id": "umwp:2", "completion_text": '{"answer":',
            "completion_token_ids": [9], "finish_reason": "stop",
        },
    ])
    cfg = {
        "generation": {"max_new_tokens": 512},
        "presign_reachability": {
            "prior_failure_manifest": {"sha256": "failure-manifest"},
        },
        "private_predecessor_comparator": {
            "model_id": "gemma4_e4b_it",
            "completions": {
                "local_artifact": str(predecessor),
                "sha256": hashlib.sha256(predecessor.read_bytes()).hexdigest(),
                "expected_rows": 2,
                "expected_strict_valid": 1,
                "expected_invalid": 1,
            },
        },
    }
    monkeypatch.setattr(
        source_and_generate, "load_prior_failure_manifest",
        lambda _cfg: {"failure_ids": ["umwp:2"]},
    )
    successor = {
        "umwp:1": {
            "id": "umwp:1", "completion_text": valid_text,
            "completion_token_ids": [7, 8], "finish_reason": "stop",
        },
        "umwp:2": {
            "id": "umwp:2",
            "completion_text": '{"answer":"9","response_confidence":0.7}',
            "completion_token_ids": [10, 11], "finish_reason": "stop",
        },
    }
    private = tmp_path / "private.jsonl"
    committed = tmp_path / "summary.json"
    summary = validate_predecessor_parity(
        cfg, "gemma4_e4b_it", successor,
        private_path=private, committed_path=committed,
    )
    assert summary["status"] == "pass"
    assert summary["n_prior_failures_repaired"] == 1
    assert all(
        "completion_text" not in row and "parsed_object" not in row
        for row in load_jsonl(private)
    )

    successor["umwp:1"]["completion_token_ids"] = [99]
    with pytest.raises(ValueError, match="predecessor parity G0 failed"):
        validate_predecessor_parity(
            cfg, "gemma4_e4b_it", successor,
            private_path=tmp_path / "failed-private.jsonl",
            committed_path=tmp_path / "failed-summary.json",
        )
    failed_summary = json.loads(
        (tmp_path / "failed-summary.json").read_text(encoding="utf-8")
    )
    assert failed_summary["status"] == "fail"
    assert failed_summary["n_parity_failures"] == 1


def test_generation_config_digest_is_key_order_invariant() -> None:
    assert generation_config_sha256({"a": 1, "b": 2}) == generation_config_sha256(
        {"b": 2, "a": 1}
    )


def test_tuner_source_fingerprint_binds_paths_bytes_and_sizes(tmp_path: Path) -> None:
    (tmp_path / "a.py").write_text("a = 1\n", encoding="utf-8")
    (tmp_path / "b.py").write_text("b = 2\n", encoding="utf-8")
    first = source_fingerprint(tmp_path, ["b.py", "a.py"])
    assert first == source_fingerprint(tmp_path, ["a.py", "b.py"])
    (tmp_path / "a.py").write_text("a = 3\n", encoding="utf-8")
    assert source_fingerprint(tmp_path, ["a.py", "b.py"])["sha256"] != first["sha256"]


def test_presign_selection_is_deterministic_and_spans_registered_strata() -> None:
    candidates = []
    for source in ("ASDiv", "GSM8K", "MultiArith", "SVAMP"):
        for answerable in (False, True):
            for index in range(5):
                candidates.append({
                    "row_key": f"{source}:{int(answerable)}:{index}",
                    "native_source": source, "answerable": answerable,
                    "prompt_token_ids_expected": list(range(index + 1)),
                })
    prior_failures = [f"umwp:{index}" for index in range(100, 111)]
    candidates.extend({
        "row_key": row_id, "native_source": "GSM8K", "answerable": False,
        "prompt_token_ids_expected": [1, 2, 3],
    } for row_id in prior_failures)
    base = select_smoke_rows(
        [row for row in candidates if row["row_key"] not in prior_failures],
        n_rows=20, seed=20260721,
    )
    first = select_smoke_rows(
        candidates, n_rows=31, seed=20260721, required_row_ids=prior_failures,
    )
    second = select_smoke_rows(
        list(reversed(candidates)), n_rows=31, seed=20260721,
        required_row_ids=prior_failures,
    )
    pinned = select_smoke_rows(
        list(reversed(candidates)), n_rows=31, seed=999,
        required_row_ids=prior_failures,
        base_row_ids=[row["row_key"] for row in base],
    )
    assert [row["row_key"] for row in first] == [row["row_key"] for row in second]
    assert [row["row_key"] for row in first] == [row["row_key"] for row in pinned]
    assert len(first) == 31
    assert {row["row_key"] for row in first} == (
        {row["row_key"] for row in base} | set(prior_failures)
    )
    assert not {row["row_key"] for row in base}.intersection(prior_failures)
    assert {(row["native_source"], row["answerable"]) for row in first} == {
        (source, answerable)
        for source in ("ASDiv", "GSM8K", "MultiArith", "SVAMP")
        for answerable in (False, True)
    }


def test_registered_successor_smoke_is_exact_20_plus_11_without_overlap() -> None:
    import yaml

    cfg = yaml.safe_load((HERE / "cell.yaml").read_text(encoding="utf-8"))
    smoke = cfg["presign_reachability"]
    expected_failures = {
        "umwp:43", "umwp:747", "umwp:959", "umwp:1373", "umwp:1436",
        "umwp:1570", "umwp:2437", "umwp:4223", "umwp:4682",
        "umwp:5051", "umwp:5103",
    }
    assert smoke["base_stratified_rows_per_model"] == 20
    assert smoke["private_rows_per_model"] == 31
    manifest = load_prior_failure_manifest(cfg)
    assert set(manifest["failure_ids"]) == expected_failures
    assert len(manifest["failure_ids"]) == 11
    assert manifest["failure_count"] == 11
    assert manifest["expected_completion_rows"] == 5200
    assert manifest["expected_strict_valid_rows"] == 5189
    gemma_base = set(load_prior_smoke_ids(cfg, "gemma4_e4b_it"))
    qwen_base = set(load_prior_smoke_ids(cfg, "qwen3_4b_raw_base"))
    assert len(gemma_base) == len(qwen_base) == 20
    assert gemma_base - qwen_base == {"umwp:609"}
    assert qwen_base - gemma_base == {"umwp:717"}
    assert len(gemma_base & qwen_base) == 19
    assert not (gemma_base | qwen_base).intersection(expected_failures)
    assert len((gemma_base | expected_failures) & (qwen_base | expected_failures)) == 30
    assert smoke["require_base_failure_id_overlap"] == 0
    assert cfg["generation"]["max_new_tokens"] == 512
    assert cfg["generation"]["canonical_eos_enabled"] is True


def test_presign_context_and_prior_failure_cap_assertions() -> None:
    gen = _generation_config(_vllm_test_cfg(), "gemma4_e4b_it")
    validate_smoke_context(
        [{"prompt_token_ids_expected": [1] * (2048 - 512)}], gen
    )
    with pytest.raises(RuntimeError, match="exceeds max_model_len"):
        validate_smoke_context(
            [{"prompt_token_ids_expected": [1] * (2048 - 511)}], gen
        )

    failure_ids = ["umwp:43"]
    rows = [{
        "id": "umwp:43", "completion_token_ids": [1] * 511,
        "finish_reason": "stop",
    }]
    validate_required_failure_outcomes({name: rows for name in RUN_NAMES}, failure_ids, 512)
    invalid = {name: rows for name in RUN_NAMES}
    invalid["resume"] = [{
        "id": "umwp:43", "completion_token_ids": [1] * 512,
        "finish_reason": "length",
    }]
    with pytest.raises(ValueError, match="did not finish naturally"):
        validate_required_failure_outcomes(invalid, failure_ids, 512)


def test_presign_repeat_comparison_is_row_keyed_and_strict() -> None:
    rows = [{
        "id": "umwp:1", "completion_text": '{"answer":"7","response_confidence":0.8}',
        "completion_token_ids": [1, 2], "finish_reason": "stop",
    }]
    repeated = {run_name: [dict(rows[0])] for run_name in RUN_NAMES}
    assert compare_repeat_rows(repeated) == {"n_rows": 1, "run_count": 5}
    repeated["permuted_b"][0]["completion_token_ids"] = [1, 3]
    with pytest.raises(ValueError, match="differ"):
        compare_repeat_rows(repeated)


def test_kill_resume_uses_atomic_checkpoint_and_hard_kills_process_group(
    tmp_path: Path, monkeypatch,
) -> None:
    out_dir = tmp_path / "run"
    out_dir.mkdir()
    _write_jsonl(
        out_dir / "completions.jsonl",
        [{"id": f"row-{index}"} for index in range(16)],
    )
    (out_dir / "checkpoint.json").write_text(
        json.dumps({"count": 16}), encoding="utf-8",
    )
    observed = {}

    class FakeProcess:
        pid = 4242

        def poll(self):
            return None

        def wait(self, timeout):
            observed["wait_timeout"] = timeout
            return -9

    def fake_popen(command, **kwargs):
        observed["popen"] = (command, kwargs)
        return FakeProcess()

    monkeypatch.setattr(presign_smoke.subprocess, "Popen", fake_popen)
    monkeypatch.setattr(
        presign_smoke.os, "killpg",
        lambda pid, sig: observed.update(killpg=(pid, sig)),
    )
    monkeypatch.setattr(
        presign_smoke, "_run_command",
        lambda command, env: observed.update(resume=(command, env)),
    )

    presign_smoke._run_kill_resume(
        ["initial"], ["resume"], out_dir, {"A": "1"}, 16, 20,
    )

    assert observed["popen"][1]["start_new_session"] is True
    assert observed["killpg"] == (4242, presign_smoke.signal.SIGKILL)
    assert observed["wait_timeout"] == 60
    assert observed["resume"][0] == ["resume"]


def test_planted_matcher_reaches_exact_g1_floor(tmp_path: Path) -> None:
    summary = planted_matcher_reachability(
        tmp_path / "private" / "rows.jsonl", tmp_path / "committed" / "summary.json",
    )
    assert summary["status"] == "pass"
    assert summary["planted_triads"] == 128
    assert summary["fit_triads"] == 64
    assert summary["held_out_triads"] == 64


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


def test_committed_jsonl_is_strictly_id_only_and_smoke_evidence_stays_private(
    tmp_path: Path,
) -> None:
    private, committed_rows = smoke_evidence_rows([{
        "row_key": "umwp:1", "prompt_sha256": "prompt-hash",
        "prompt_token_ids_sha256": "token-hash",
        "prompt_token_ids_expected": [1, 2],
    }])
    assert committed_rows == [{"row_id": "umwp:1"}]
    assert set(private[0]) == {
        "row_id", "prompt_sha256", "prompt_token_sequence_sha256",
        "prompt_token_count",
    }
    committed_root = tmp_path / "analysis-committed"
    committed_root.mkdir()
    _write_jsonl(committed_root / "manifest.jsonl", committed_rows)
    assert containment_lint(committed_root)["status"] == "pass"
    _write_jsonl(
        committed_root / "manifest.jsonl",
        [{"row_id": "umwp:1", "prompt_sha256": "prompt-hash"}],
    )
    result = containment_lint(committed_root)
    assert result["status"] == "fail"
    assert result["errors"] == [
        "manifest.jsonl: committed JSONL rows must contain only row_id"
    ]


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
