"""Tests for the opt-in generated-thinking policy of the knowledge probe.

Location: experiments/common/knowledge_probe/tests/test_generated_thinking_policy.py
Run:      python -m pytest experiments/common/knowledge_probe/tests -q

scoring.generated_thinking_policy (backends.GENERATED_THINKING_POLICIES):
  abort        default (key absent): a generated thinking marker raises, as before
  count_wrong  the marker-bearing generation is scored incorrect, the run
               continues, and counts land in the row and the manifest
Added 2026-10-04 for experiments/decision-model-calibrated-choice.
GPU-free: a StubBackend subclass injects '</think>' into chosen generations.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

TESTS_DIR = Path(__file__).resolve().parent
PROBE_DIR = TESTS_DIR.parent
sys.path.insert(0, str(PROBE_DIR))
sys.path.insert(0, str(TESTS_DIR))

import probe  # noqa: E402
from backends import (  # noqa: E402
    StubBackend,
    VLLMBackend,
    build_backend,
    has_generated_thinking,
    resolve_generated_thinking_policy,
)
from test_probe_smoke import (  # noqa: E402
    CORRECT_RATE,
    _alias_table,
    _base_config,
    _patch_pool_to_fixture,
)

MARKED_Q = "Who wrote Paradise Lost?"  # correct_rate 1.0 -> every sample is gold


class MarkerStub(StubBackend):
    """Stub that appends '</think>' to every 4th sample (indices 0, 4, 8, ...)
    of MARKED_Q, keeping the gold alias in the text so that only the policy can
    make those samples wrong; optionally marks the greedy decode too."""

    def __init__(self, *args, mark_greedy: bool = False, **kwargs):
        super().__init__(*args, **kwargs)
        self.mark_greedy = mark_greedy

    def generate_batch(self, question, n_samples, temperature, top_p, max_new_tokens, seed):
        out = super().generate_batch(question, n_samples, temperature, top_p, max_new_tokens, seed)
        if question == MARKED_Q:
            out = [f"{t} </think>" if i % 4 == 0 else t for i, t in enumerate(out)]
        return out

    def generate_greedy(self, question, max_new_tokens):
        text = super().generate_greedy(question, max_new_tokens)
        if question == MARKED_Q and self.mark_greedy:
            text = f"{text}\n</think>"
        return text


def _marker_stub(mark_greedy: bool = False) -> MarkerStub:
    return MarkerStub(alias_table=_alias_table(), correct_rate=CORRECT_RATE,
                      wrong_answer="Atlantis", seed=20260610, mark_greedy=mark_greedy)


def _by_question(results_path: Path) -> dict[str, dict]:
    return {r["question"]: r for r in probe.read_results(results_path)}


def test_policy_defaults_to_abort_and_validates():
    assert resolve_generated_thinking_policy({}) == "abort"
    assert resolve_generated_thinking_policy({"scoring": {}}) == "abort"
    assert resolve_generated_thinking_policy({"scoring": {"generated_thinking_policy": "count_wrong"}}) == "count_wrong"
    with pytest.raises(ValueError, match="generated_thinking_policy"):
        resolve_generated_thinking_policy({"scoring": {"generated_thinking_policy": "ignore"}})


def test_detection_matches_abort_markers():
    assert has_generated_thinking("milton </think>")
    assert has_generated_thinking("<think> hmm")
    assert not has_generated_thinking("John Milton")


def test_default_policy_aborts_on_generated_marker(tmp_path, monkeypatch):
    _patch_pool_to_fixture(monkeypatch)
    config = _base_config(tmp_path)  # no scoring block -> abort
    with pytest.raises(RuntimeError, match="thinking marker"):
        probe.run_probe(config, _marker_stub(), tmp_path / "out")


def test_default_policy_row_schema_unchanged(tmp_path, monkeypatch):
    _patch_pool_to_fixture(monkeypatch)
    config = _base_config(tmp_path)
    results = probe.run_probe(config, StubBackend(alias_table=_alias_table(), correct_rate=CORRECT_RATE,
                                                  wrong_answer="Atlantis", seed=20260610), tmp_path / "out")
    for row in probe.read_results(results):
        assert "n_sampled_thinking_marker" not in row
        assert "greedy_thinking_marker" not in row
        assert "generated_thinking_policy" not in row
    probe.finalize(config, results, tmp_path / "out")
    manifest = json.loads((tmp_path / "out" / "probe_manifest.json").read_text())
    assert "generated_thinking" not in manifest


def test_count_wrong_scores_marked_samples_wrong_and_continues(tmp_path, monkeypatch):
    _patch_pool_to_fixture(monkeypatch)
    config = _base_config(tmp_path)
    config["scoring"] = {"generated_thinking_policy": "count_wrong"}
    out = tmp_path / "out"
    results = probe.run_probe(config, _marker_stub(), out)
    rows = _by_question(results)
    assert len(rows) == 5  # run continued past the marked question
    marked = rows[MARKED_Q]
    n = config["sampling"]["n_samples"]
    expected_marked = len(range(0, n, 4))
    assert marked["n_sampled_thinking_marker"] == expected_marked
    # every sample contains the gold alias, so only the policy can make it wrong
    assert marked["sampled_correct"] == [i % 4 != 0 for i in range(n)]
    assert marked["p_correct"] == (n - expected_marked) / n
    assert marked["greedy_thinking_marker"] is False
    assert marked["greedy_correct"] is True
    assert marked["generated_thinking_policy"] == "count_wrong"
    for q, row in rows.items():
        if q != MARKED_Q:
            assert row["n_sampled_thinking_marker"] == 0
            assert row["greedy_thinking_marker"] is False


def test_count_wrong_greedy_marker_blocks_known(tmp_path, monkeypatch):
    _patch_pool_to_fixture(monkeypatch)
    config = _base_config(tmp_path)
    config["scoring"] = {"generated_thinking_policy": "count_wrong"}
    results = probe.run_probe(config, _marker_stub(mark_greedy=True), tmp_path / "out")
    marked = _by_question(results)[MARKED_Q]
    assert marked["greedy_thinking_marker"] is True
    assert marked["greedy_correct"] is False
    assert marked["label"] != "known"  # known requires a correct greedy decode


def test_count_wrong_manifest_records_run_level_counts(tmp_path, monkeypatch):
    _patch_pool_to_fixture(monkeypatch)
    config = _base_config(tmp_path)
    config["scoring"] = {"generated_thinking_policy": "count_wrong"}
    out = tmp_path / "out"
    results = probe.run_probe(config, _marker_stub(mark_greedy=True), out)
    probe.finalize(config, results, out)
    g = json.loads((out / "probe_manifest.json").read_text())["generated_thinking"]
    n = config["sampling"]["n_samples"]
    n_rows = 5
    assert g["policy"] == "count_wrong"
    assert g["n_questions"] == n_rows
    assert g["n_questions_affected"] == 1
    assert g["n_sampled_marked"] == len(range(0, n, 4))
    assert g["n_greedy_marked"] == 1
    assert g["n_generations"] == n_rows * (n + 1)
    assert g["marked_rate"] == pytest.approx((len(range(0, n, 4)) + 1) / (n_rows * (n + 1)))
    assert g["sampled_marked_rate"] == pytest.approx(len(range(0, n, 4)) / (n_rows * n))


def test_count_wrong_changes_probe_config_sha_only_when_set(tmp_path):
    base = _base_config(tmp_path)
    opted = _base_config(tmp_path)
    opted["scoring"] = {"generated_thinking_policy": "count_wrong"}
    assert probe.config_sha(base) == probe.config_sha(_base_config(tmp_path))
    assert probe.config_sha(base) != probe.config_sha(opted)


class _FakeOut:
    def __init__(self, text):
        self.text = text


class _FakeReq:
    def __init__(self, texts):
        self.outputs = [_FakeOut(t) for t in texts]


class _FakeLLM:
    def __init__(self, texts):
        self.texts = texts

    def generate(self, prompts, params):
        return [_FakeReq(self.texts)]


def _bare_vllm_backend(texts, policy: str | None):
    backend = object.__new__(VLLMBackend)
    backend.model_name = "fake"
    backend.enable_thinking = False
    backend.system_prompt = "answer concisely"
    backend._chat_template_mode = "direct"
    backend._render_prompt = lambda q: "<|im_start|>assistant\n<think>\n\n</think>\n\n"
    backend._sampling_params = lambda *a, **k: None
    backend.llm = _FakeLLM(texts)
    if policy is not None:
        backend._abort_on_generated_thinking = policy == "abort"
    return backend


@pytest.mark.parametrize("policy", [None, "abort"])
def test_vllm_backend_aborts_by_default(policy):
    backend = _bare_vllm_backend(["milton", "milton </think>"], policy)
    with pytest.raises(RuntimeError, match="thinking marker"):
        backend.generate_batch("q", 2, 1.0, 0.9, 8, 0)


def test_vllm_backend_count_wrong_passes_marked_text_through():
    backend = _bare_vllm_backend(["milton", "milton </think>"], "count_wrong")
    assert backend.generate_batch("q", 2, 1.0, 0.9, 8, 0) == ["milton", "milton </think>"]
    assert backend.generate_greedy("q", 8) == "milton"


def test_build_backend_rejects_unknown_policy(monkeypatch):
    config = {"runtime": {"backend": "vllm", "vllm": {}},
              "model": {"model_name": "x", "enable_thinking": False},
              "scoring": {"generated_thinking_policy": "bogus"}}
    with pytest.raises(ValueError, match="generated_thinking_policy"):
        build_backend(config, "sys")
