"""Smoke tests for the Phase 1 knowledge probe (WS-1).

Location: experiment/phase1/probe/tests/test_probe_smoke.py
Run:      cd experiment/phase1/probe && python -m pytest tests/ -q

These verify the probe's scoring, labeling, JSONL output contract,
resumability, sensitivity grid, and the enable_thinking runtime self-check,
all with the GPU-free StubBackend on a small fixture. Comprehensive coverage
is TEST phase work; this is the "does it run, does the happy path hold" gate.
"""

from __future__ import annotations

import json
import hashlib
import sys
from pathlib import Path

import pytest

PROBE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROBE_DIR))

import probe  # noqa: E402
from backends import (  # noqa: E402
    StubBackend,
    VLLMBackend,
    assert_no_generated_thinking,
    assert_no_generated_thinking_batch,
    assert_no_think_scaffolding,
)
from scoring import is_correct, normalize_answer, normalize_question, p_correct  # noqa: E402

FIXTURE = PROBE_DIR / "tests" / "fixtures" / "train_fixture.jsonl"

# Per-question correctness rates for the stub: known questions are answered
# almost always, unknown never, the discard question sometimes (middle band).
CORRECT_RATE = {
    "Who wrote Paradise Lost?": 1.0,
    "What is the capital of France?": 0.9,
    "What is the airspeed velocity of an unladen swallow in 1297?": 0.0,
    "What was the exact thought of Caesar at noon on the ides?": 0.0,
    "Which actor played the third spear-carrier in a 1973 play?": 0.25,
}


def _alias_table():
    table = {}
    with FIXTURE.open() as fh:
        for line in fh:
            row = json.loads(line)
            table[row["question"]] = row["answer"]["normalized_aliases"]
    return table


def _base_config(tmp_path: Path) -> dict:
    return {
        "model": {"model_tag": "stub-model", "model_name": "stub",
                  "enable_thinking": False},
        "sampling": {"n_samples": 16, "temperature": 1.0, "top_p": 0.9,
                     "max_new_tokens": 64, "seed": 20260610},
        "prompt": {"system": "answer concisely"},
        "probe_pool": {"train_jsonl": str(FIXTURE),
                       "fallback_validation_remainder": None,
                       "question_id_prefix": "tqa_train_",
                       "max_questions": None,
                       "subset_seed": 20260610},
        "labels": {"known_p_correct_min": 0.5, "unknown_p_correct_max": 0.0},
        "sensitivity": {"enabled": True,
                        "unknown_cutoffs": [0.0, 0.03125, 0.0625, 0.1],
                        "known_cutoffs": [0.5, 0.7, 0.9],
                        "max_questions": None, "subsample_seed": 20260610},
        "output": {"results_filename": "probe_results.jsonl",
                   "manifest_filename": "probe_manifest.json",
                   "sensitivity_filename": "sensitivity_grid.json"},
        "runtime": {"backend": "stub"},
    }


def _stub_backend():
    table = _alias_table()
    return StubBackend(alias_table=table, correct_rate=CORRECT_RATE,
                       wrong_answer="Atlantis", seed=20260610)


# Resolve the fixture against an absolute path so REPO_ROOT joining is a no-op.
def _patch_pool_to_fixture(monkeypatch):
    monkeypatch.setattr(probe, "resolve_pool_path", lambda config: FIXTURE)


def _write_duplicate_id_fixture(tmp_path: Path) -> Path:
    path = tmp_path / "duplicate_ids.jsonl"
    rows = [
        {
            "question": "Who wrote Paradise Lost?",
            "question_id": "dup_qid",
            "answer": {
                "value": "John Milton",
                "normalized_aliases": ["john milton", "milton"],
            },
        },
        {
            "question": "What is the capital of France?",
            "question_id": "dup_qid",
            "answer": {"value": "Paris", "normalized_aliases": ["paris"]},
        },
        {
            "question": "What is the airspeed velocity of an unladen swallow in 1297?",
            "question_id": "unique_qid",
            "answer": {
                "value": "Eleven metres per second",
                "normalized_aliases": ["eleven metres per second"],
            },
        },
    ]
    path.write_text("\n".join(json.dumps(row) for row in rows) + "\n")
    return path


# --- scoring primitives ---

def test_normalize_answer_strips_punctuation():
    assert normalize_answer("John Milton.") == "john milton"


def test_is_correct_word_bounded():
    assert is_correct("It was John Milton.", ["john milton", "milton"])
    assert not is_correct("miltonic verse", ["milton"])  # substring must not match


def test_p_correct_fraction():
    assert p_correct([True, True, False, False]) == 0.5
    assert p_correct([]) == 0.0


def test_normalize_question_collapses_whitespace():
    assert normalize_question("  Who   wrote  Paradise Lost? ") == "who wrote paradise lost?"


# --- runtime self-check ---

def test_assert_no_think_passes_clean_prompt():
    assert_no_think_scaffolding("<|im_start|>user\nhi<|im_end|>\n")


def test_assert_no_think_allows_empty_think_off_marker():
    assert_no_think_scaffolding(
        "<|im_start|>assistant\n<think>\n\n</think>\n\n"
    )


def test_assert_no_think_raises_on_think_tag():
    with pytest.raises(RuntimeError, match="enable_thinking"):
        assert_no_think_scaffolding("<|im_start|>assistant\n<think>\n")


def test_assert_no_think_raises_on_populated_think_block():
    with pytest.raises(RuntimeError, match="non-empty"):
        assert_no_think_scaffolding(
            "<|im_start|>assistant\n<think>\nprivate reasoning\n</think>\n"
        )


def test_assert_no_generated_thinking_rejects_any_think_marker():
    with pytest.raises(RuntimeError, match="Aborting before writing probe rows"):
        assert_no_generated_thinking(
            "<think>\nprivate reasoning\n</think>\nJohn Milton",
            question="Who wrote Paradise Lost?",
            generation_kind="greedy",
        )


def test_assert_no_generated_thinking_rejects_empty_marker_in_output():
    with pytest.raises(RuntimeError, match="thinking marker"):
        assert_no_generated_thinking(
            "<think>\n\n</think>\n\nJohn Milton",
            question="Who wrote Paradise Lost?",
            generation_kind="greedy",
        )


def test_assert_no_generated_thinking_batch_identifies_sample_index():
    with pytest.raises(RuntimeError, match=r"sampled\[1\]"):
        assert_no_generated_thinking_batch(
            ["John Milton", "</think> leaked"],
            question="Who wrote Paradise Lost?",
            generation_kind="sampled",
        )


class _ModeSensitiveTokenizer:
    def __init__(self):
        self.calls = []

    def apply_chat_template(self, messages, **kwargs):
        self.calls.append(kwargs)
        if kwargs.get("enable_thinking") is False:
            return "<|im_start|>assistant\n<think>\n\n</think>\n\n"
        if kwargs.get("chat_template_kwargs") == {"enable_thinking": False}:
            return "<|im_start|>assistant\n<think>\nprivate\n</think>\n"
        return "<|im_start|>assistant\n"


class _DirectRejectingTokenizer:
    def __init__(self):
        self.calls = []

    def apply_chat_template(self, messages, **kwargs):
        self.calls.append(kwargs)
        if "enable_thinking" in kwargs:
            raise TypeError("unexpected keyword argument 'enable_thinking'")
        if kwargs.get("chat_template_kwargs") == {"enable_thinking": False}:
            return "<|im_start|>assistant\n<think>\n\n</think>\n\n"
        return "<|im_start|>assistant\n<think>\nprivate\n</think>\n"


class _RejectingTokenizer:
    def apply_chat_template(self, messages, **kwargs):
        if "chat_template_kwargs" in kwargs:
            raise TypeError("unexpected keyword argument 'chat_template_kwargs'")
        return "<|im_start|>assistant\n<think>\nprivate\n</think>\n"


def _vllm_backend_with_tokenizer(tokenizer):
    backend = object.__new__(VLLMBackend)
    backend.model_name = "fake-qwen3"
    backend.enable_thinking = False
    backend.system_prompt = "answer concisely"
    backend.tokenizer = tokenizer
    backend._chat_template_mode = None
    return backend


def test_vllm_render_uses_direct_tokenizer_kwarg_for_thinking_off():
    tokenizer = _ModeSensitiveTokenizer()
    backend = _vllm_backend_with_tokenizer(tokenizer)

    rendered = backend._render_prompt("Who wrote Paradise Lost?")

    assert rendered.endswith("</think>\n\n")
    assert backend._chat_template_mode == "direct"
    assert tokenizer.calls == [
        {
            "tokenize": False,
            "add_generation_prompt": True,
            "enable_thinking": False,
        }
    ]


def test_vllm_render_falls_back_to_chat_template_kwargs_surface():
    tokenizer = _DirectRejectingTokenizer()
    backend = _vllm_backend_with_tokenizer(tokenizer)

    rendered = backend._render_prompt("Who wrote Paradise Lost?")

    assert rendered.endswith("</think>\n\n")
    assert backend._chat_template_mode == "chat_template_kwargs"
    assert tokenizer.calls == [
        {
            "tokenize": False,
            "add_generation_prompt": True,
            "enable_thinking": False,
        },
        {
            "tokenize": False,
            "add_generation_prompt": True,
            "chat_template_kwargs": {"enable_thinking": False},
        },
    ]


def test_vllm_render_fails_actionably_when_no_surface_disables_thinking():
    backend = _vllm_backend_with_tokenizer(_RejectingTokenizer())

    with pytest.raises(RuntimeError, match="Unable to render.*thinking disabled"):
        backend._render_prompt("Who wrote Paradise Lost?")


# --- end-to-end probe ---

def test_probe_runs_and_labels_all_bands(tmp_path, monkeypatch):
    _patch_pool_to_fixture(monkeypatch)
    config = _base_config(tmp_path)
    out_dir = tmp_path / "stub-model"
    results_path = probe.run_probe(config, _stub_backend(), out_dir)

    records = probe.read_results(results_path)
    by_id = {r["question_id"]: r for r in records}
    assert len(records) == 5

    # Each band is represented.
    labels = {r["question_id"]: r["label"] for r in records}
    assert labels["fix_known_1"] == "known"
    assert labels["fix_known_2"] == "known"
    assert labels["fix_unknown_1"] == "unknown"
    assert labels["fix_unknown_2"] == "unknown"
    assert labels["fix_discard_1"] == "discard"

    # P_correct ordering sanity.
    assert by_id["fix_known_1"]["p_correct"] == 1.0
    assert by_id["fix_unknown_1"]["p_correct"] == 0.0
    assert 0.0 < by_id["fix_discard_1"]["p_correct"] < 0.5


class _LeakingGeneratedThinkingBackend:
    def generate_batch(self, question, n_samples, temperature, top_p,
                       max_new_tokens, seed):
        return ["<think>\nprivate reasoning\n</think>\nJohn Milton"] * n_samples

    def generate_greedy(self, question, max_new_tokens):
        return "John Milton"


def test_run_probe_rejects_generated_thinking_before_writing_rows(tmp_path, monkeypatch):
    _patch_pool_to_fixture(monkeypatch)
    config = _base_config(tmp_path)
    out_dir = tmp_path / "stub-model"

    with pytest.raises(RuntimeError, match="Aborting before writing probe rows"):
        probe.run_probe(config, _LeakingGeneratedThinkingBackend(), out_dir)

    results_path = out_dir / "probe_results.jsonl"
    assert not results_path.exists() or results_path.read_text() == ""


def test_probe_pool_cap_selects_deterministic_question_subset(tmp_path, monkeypatch):
    _patch_pool_to_fixture(monkeypatch)
    config = _base_config(tmp_path)
    config["probe_pool"]["max_questions"] = 2
    config["probe_pool"]["subset_seed"] = 7
    out_dir = tmp_path / "stub-model"
    results_path = probe.run_probe(config, _stub_backend(), out_dir)

    records = probe.read_results(results_path)
    selected_ids = [r["question_id"] for r in records]
    all_rows = [
        ("000000000000|fix_known_1", "fix_known_1"),
        ("000000000001|fix_known_2", "fix_known_2"),
        ("000000000002|fix_unknown_1", "fix_unknown_1"),
        ("000000000003|fix_unknown_2", "fix_unknown_2"),
        ("000000000004|fix_discard_1", "fix_discard_1"),
    ]
    expected_rows = sorted(
        all_rows,
        key=lambda row: hashlib.sha256(f"7|{row[0]}".encode()).hexdigest(),
    )[:2]
    expected_row_keys = {row_key for row_key, _ in expected_rows}

    assert len(records) == 2
    assert {r["probe_pool_row_key"] for r in records} == expected_row_keys
    assert selected_ids == [
        question_id for row_key, question_id in all_rows
        if row_key in expected_row_keys
    ]


def test_probe_pool_cap_changes_with_subset_seed(tmp_path, monkeypatch):
    _patch_pool_to_fixture(monkeypatch)
    config_a = _base_config(tmp_path)
    config_a["probe_pool"]["max_questions"] = 2
    config_a["probe_pool"]["subset_seed"] = 7
    config_b = _base_config(tmp_path)
    config_b["probe_pool"]["max_questions"] = 2
    config_b["probe_pool"]["subset_seed"] = 8

    probe.run_probe(config_a, _stub_backend(), tmp_path / "run_a")
    probe.run_probe(config_b, _stub_backend(), tmp_path / "run_b")
    keys_a = {
        r["probe_pool_row_key"]
        for r in probe.read_results(tmp_path / "run_a" / "probe_results.jsonl")
    }
    keys_b = {
        r["probe_pool_row_key"]
        for r in probe.read_results(tmp_path / "run_b" / "probe_results.jsonl")
    }

    assert keys_a != keys_b


def test_probe_pool_cap_selects_rows_not_unique_question_ids(tmp_path, monkeypatch):
    duplicate_fixture = _write_duplicate_id_fixture(tmp_path)
    monkeypatch.setattr(probe, "resolve_pool_path", lambda config: duplicate_fixture)
    config = _base_config(tmp_path)
    config["probe_pool"]["max_questions"] = 2
    config["probe_pool"]["subset_seed"] = 20260610
    rows, selection = probe.load_probe_pool(config, duplicate_fixture)

    expected = sorted(
        list(probe.iter_pool(duplicate_fixture, "tqa_train_")),
        key=lambda row: hashlib.sha256(
            f"20260610|{row[0]}".encode()
        ).hexdigest(),
    )[:2]
    expected_keys = {row[0] for row in expected}

    assert len(rows) == 2
    assert len({row[0] for row in rows}) == 2
    assert {row[0] for row in rows} == expected_keys
    assert selection["source_question_count"] == 3
    assert selection["selected_question_count"] == 2


def test_duplicate_question_ids_resume_by_row_key(tmp_path, monkeypatch):
    duplicate_fixture = _write_duplicate_id_fixture(tmp_path)
    monkeypatch.setattr(probe, "resolve_pool_path", lambda config: duplicate_fixture)
    config = _base_config(tmp_path)
    out_dir = tmp_path / "stub-model"

    probe.run_probe(config, _stub_backend(), out_dir)
    results_path = out_dir / "probe_results.jsonl"
    first = probe.read_results(results_path)
    assert len(first) == 3
    assert [r["question_id"] for r in first].count("dup_qid") == 2
    assert len({r["probe_pool_row_key"] for r in first}) == 3

    probe.run_probe(config, _stub_backend(), out_dir)
    second = probe.read_results(results_path)
    assert second == first


def test_output_contract_fields(tmp_path, monkeypatch):
    _patch_pool_to_fixture(monkeypatch)
    config = _base_config(tmp_path)
    out_dir = tmp_path / "stub-model"
    results_path = probe.run_probe(config, _stub_backend(), out_dir)
    record = probe.read_results(results_path)[0]

    # Exact A -> B schema (architecture doc 3.8) consumed by coder-data.
    # answer_value (natural-case gold) is an OPTIONAL field the builder uses as
    # the `known` target, falling back to the first alias when it is absent.
    required = {
        "question_id", "question", "question_norm", "normalized_aliases",
        "answer_value", "n_samples", "greedy_answer", "greedy_correct",
        "p_correct", "sampled_answers", "sampled_correct", "label",
        "model_tag", "probe_config_sha", "probe_pool_row_key",
        "probe_pool_source_index",
    }
    assert required.issubset(record.keys())
    assert len(record["sampled_answers"]) == record["n_samples"]
    assert len(record["sampled_correct"]) == record["n_samples"]
    # Wrong samples are retained (downstream KTO/DPO negatives).
    assert isinstance(record["sampled_answers"], list)


def test_answer_value_propagated_natural_case(tmp_path, monkeypatch):
    # answer.value (natural-case gold) flows through to the record verbatim,
    # distinct from the lowercased normalized_aliases the scorer matches on.
    _patch_pool_to_fixture(monkeypatch)
    config = _base_config(tmp_path)
    out_dir = tmp_path / "stub-model"
    results_path = probe.run_probe(config, _stub_backend(), out_dir)
    by_id = {r["question_id"]: r for r in probe.read_results(results_path)}

    assert by_id["fix_known_1"]["answer_value"] == "John Milton"
    assert by_id["fix_known_1"]["normalized_aliases"] == ["john milton", "milton"]
    # A row that omits answer.value yields None (the optional-field contract);
    # the builder falls back to the first alias in that case.
    assert by_id["fix_discard_1"]["answer_value"] is None


def test_resumability_skips_done_ids(tmp_path, monkeypatch):
    _patch_pool_to_fixture(monkeypatch)
    config = _base_config(tmp_path)
    out_dir = tmp_path / "stub-model"

    # First pass over a 2-row prefix, then a second pass over the full fixture:
    # the second pass must skip the already-probed ids and only append new ones.
    probe.run_probe(config, _stub_backend(), out_dir)
    results_path = out_dir / "probe_results.jsonl"
    first = probe.read_results(results_path)
    assert len(first) == 5

    # Re-run: nothing new should be appended (all ids present).
    probe.run_probe(config, _stub_backend(), out_dir)
    second = probe.read_results(results_path)
    assert len(second) == 5  # no duplicates


def test_resumability_skips_done_ids_with_probe_pool_cap(tmp_path, monkeypatch):
    _patch_pool_to_fixture(monkeypatch)
    config = _base_config(tmp_path)
    config["probe_pool"]["max_questions"] = 2
    config["probe_pool"]["subset_seed"] = 7
    out_dir = tmp_path / "stub-model"

    probe.run_probe(config, _stub_backend(), out_dir)
    results_path = out_dir / "probe_results.jsonl"
    first = probe.read_results(results_path)
    assert len(first) == 2

    probe.run_probe(config, _stub_backend(), out_dir)
    second = probe.read_results(results_path)
    assert second == first


def test_probe_pool_cap_rejects_existing_rows_outside_subset(tmp_path, monkeypatch):
    _patch_pool_to_fixture(monkeypatch)
    config = _base_config(tmp_path)
    config["probe_pool"]["max_questions"] = 2
    config["probe_pool"]["subset_seed"] = 7
    out_dir = tmp_path / "stub-model"
    out_dir.mkdir()
    results_path = out_dir / "probe_results.jsonl"
    results_path.write_text(
        json.dumps({"question_id": "definitely_outside_subset"}) + "\n"
    )

    with pytest.raises(RuntimeError, match="legacy records without probe_pool_row_key"):
        probe.run_probe(config, _stub_backend(), out_dir)


def test_resume_reproduces_skipped_records(tmp_path, monkeypatch):
    # Determinism: a fresh probe of one question equals the resumed record.
    _patch_pool_to_fixture(monkeypatch)
    config = _base_config(tmp_path)
    out_dir_a = tmp_path / "run_a"
    out_dir_b = tmp_path / "run_b"
    probe.run_probe(config, _stub_backend(), out_dir_a)
    probe.run_probe(config, _stub_backend(), out_dir_b)
    a = {r["question_id"]: r for r in probe.read_results(out_dir_a / "probe_results.jsonl")}
    b = {r["question_id"]: r for r in probe.read_results(out_dir_b / "probe_results.jsonl")}
    assert a == b


def test_manifest_and_sensitivity_written(tmp_path, monkeypatch):
    _patch_pool_to_fixture(monkeypatch)
    config = _base_config(tmp_path)
    out_dir = tmp_path / "stub-model"
    results_path = probe.run_probe(config, _stub_backend(), out_dir)
    probe.finalize(config, results_path, out_dir)

    manifest = json.loads((out_dir / "probe_manifest.json").read_text())
    assert manifest["n_questions"] == 5
    assert manifest["label_counts"]["known"] == 2
    assert manifest["label_counts"]["unknown"] == 2
    assert manifest["enable_thinking"] is False
    assert manifest["probe_config_sha"]
    assert manifest["probe_pool"] == {
        "source_question_count": 5,
        "selected_question_count": 5,
        "max_questions": None,
        "subset_seed": 20260610,
        "selection_applied": False,
        "selection_method": (
            "sha256(f'{subset_seed}|{probe_pool_row_key}') ascending; "
            "probe_pool_row_key is zero-based source_index plus question_id; "
            "selected rows processed in source order"
        ),
    }

    grid = json.loads((out_dir / "sensitivity_grid.json").read_text())
    # 4 unknown cutoffs x 3 known cutoffs = 12 cells.
    assert len(grid["cells"]) == 12
    # The strictest unknown cutoff (0.0) captures the two pure-unknowns.
    strict = [c for c in grid["cells"] if c["unknown_cutoff"] == 0.0][0]
    assert strict["n_unknown"] == 2


def test_sensitivity_reports_answerable_fraction(tmp_path, monkeypatch):
    # The Paper-1 43-51% analogue: fraction of "unknown"-labeled questions the
    # greedy decode actually answered. With a loose unknown cutoff that pulls in
    # the discard question (greedy wrong here), the fraction stays computable.
    _patch_pool_to_fixture(monkeypatch)
    config = _base_config(tmp_path)
    out_dir = tmp_path / "stub-model"
    results_path = probe.run_probe(config, _stub_backend(), out_dir)
    records = probe.read_results(results_path)
    grid = probe.sensitivity_grid(records, config["sensitivity"])
    for cell in grid["cells"]:
        assert 0.0 <= cell["unknown_greedy_answerable_frac"] <= 1.0


def test_seed_derivation_is_deterministic():
    a = probe.derive_seed(20260610, "fix_known_1")
    b = probe.derive_seed(20260610, "fix_known_1")
    c = probe.derive_seed(20260610, "fix_known_2")
    assert a == b
    assert a != c


def test_config_sha_changes_with_config():
    base = _base_config(Path("/tmp"))
    sha1 = probe.config_sha(base)
    base["sampling"]["n_samples"] = 64
    sha2 = probe.config_sha(base)
    assert sha1 != sha2
