"""Tests for the opt-in base-mode k-shot prompting surface of the knowledge probe.

Location: experiments/common/knowledge_probe/tests/test_base_kshot_surface.py
Run:      python -m pytest experiments/common/knowledge_probe/tests -q

prompt.surface (backends.PROMPT_SURFACES):
  chat        default (key absent): chat template + system prompt, unchanged
  base_kshot  Amendment Y's pretrain-only base surface, vendored byte-identical
              from experiments/common/readouts/amendment_x_cross_model_extract.py
GPU-free: stub backends, a fake vLLM SamplingParams, and a tokenizer that
refuses to render a chat template.
"""

from __future__ import annotations

import ast
import sys
import types
from pathlib import Path

import pytest

TESTS_DIR = Path(__file__).resolve().parent
PROBE_DIR = TESTS_DIR.parent
REPO = PROBE_DIR.parents[2]
sys.path.insert(0, str(PROBE_DIR))
sys.path.insert(0, str(TESTS_DIR))

import probe  # noqa: E402
from backends import (  # noqa: E402
    BASE_MODE_FEWSHOT,
    StubBackend,
    VLLMBackend,
    base_mode_first_line,
    base_mode_kshot_sha,
    build_base_mode_prompt,
    resolve_prompt_surface,
)
from test_probe_smoke import CORRECT_RATE, _alias_table, _base_config, _patch_pool_to_fixture  # noqa: E402

Y_SOURCE = REPO / "experiments/common/readouts/amendment_x_cross_model_extract.py"


def _y_fewshot_from_source():
    tree = ast.parse(Y_SOURCE.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.AnnAssign) and getattr(node.target, "id", None) == "_BASE_MODE_FEWSHOT":
            return ast.literal_eval(node.value)
        if isinstance(node, ast.Assign) and any(getattr(t, "id", None) == "_BASE_MODE_FEWSHOT" for t in node.targets):
            return ast.literal_eval(node.value)
    raise AssertionError("_BASE_MODE_FEWSHOT not found in Amendment Y source")


def test_exemplars_byte_identical_to_amendment_y_source():
    assert BASE_MODE_FEWSHOT == _y_fewshot_from_source()


def test_base_mode_prompt_exact_string():
    # Same expected string as test_amendment_y_base_mode.py pins for Y's builder.
    expected = (
        "Q: What is the largest planet in our solar system?\nA: Jupiter\n\n"
        "Q: How many sides does a hexagon have?\nA: Six\n\n"
        "Q: What is the chemical symbol for gold?\nA: Au\n\n"
        "Q: In what year did the Second World War end?\nA: 1945\n\n"
        "Q: What is the tallest mountain on Earth?\nA: Mount Everest\n\n"
        "Q: What is the capital of France?\nA:"
    )
    assert build_base_mode_prompt("What is the capital of France?") == expected
    assert len(base_mode_kshot_sha()) == 16


def test_first_line_parse_matches_amendment_y_rule():
    assert base_mode_first_line(" Paris") == "Paris"
    assert base_mode_first_line(" Paris\nQ: What is next?\nA: x") == "Paris"
    assert base_mode_first_line("\n\nParis") == ""  # Y splits BEFORE stripping
    assert base_mode_first_line("") == ""


def test_surface_default_and_validation():
    assert resolve_prompt_surface({"prompt": {"system": "x"}}) == "chat"
    assert resolve_prompt_surface({"prompt": {"surface": "base_kshot"}, "model": {"enable_thinking": False}}) == "base_kshot"
    with pytest.raises(ValueError, match="prompt.surface"):
        resolve_prompt_surface({"prompt": {"surface": "fewshot"}})
    with pytest.raises(ValueError, match="enable_thinking"):
        resolve_prompt_surface({"prompt": {"surface": "base_kshot"}, "model": {"enable_thinking": True}})


class _NoChatTokenizer:
    def apply_chat_template(self, *a, **k):
        raise AssertionError("chat template must not be applied under base_kshot")


def _bare_backend(surface):
    b = object.__new__(VLLMBackend)
    b.model_name, b.enable_thinking, b.system_prompt = "fake", False, "SYSTEM PROMPT"
    b.tokenizer, b._chat_template_mode = _NoChatTokenizer(), None
    b.prompt_surface = surface
    return b


def test_vllm_render_no_chat_template_no_system_prompt():
    b = _bare_backend("base_kshot")
    rendered = b._render_prompt("Who wrote Paradise Lost?")
    assert rendered == build_base_mode_prompt("Who wrote Paradise Lost?")
    assert "SYSTEM PROMPT" not in rendered and "<|im_start|>" not in rendered
    b._self_check_thinking_off()  # skipped, does not touch the tokenizer


def test_vllm_sampling_stops_at_newline_only_under_base_kshot(monkeypatch):
    class FakeSP:
        def __init__(self, **kw):
            self.kw = kw
    monkeypatch.setitem(sys.modules, "vllm", types.SimpleNamespace(SamplingParams=FakeSP))
    assert _bare_backend("base_kshot")._sampling_params(4, 1.0, 0.9, 64, 7).kw["stop"] == ["\n"]
    assert "stop" not in _bare_backend("chat")._sampling_params(4, 1.0, 0.9, 64, 7).kw


class _BabbleStub(StubBackend):
    """Stub whose generations continue past the answer like a base model."""

    def generate_batch(self, question, n_samples, temperature, top_p, max_new_tokens, seed):
        return [f" {t}\nQ: What else?\nA: Atlantis" for t in super().generate_batch(
            question, n_samples, temperature, top_p, max_new_tokens, seed)]

    def generate_greedy(self, question, max_new_tokens):
        return f" {super().generate_greedy(question, max_new_tokens)}\nQ: Next?\nA: Milton"


def test_probe_scores_first_line_only_under_base_kshot(tmp_path, monkeypatch):
    _patch_pool_to_fixture(monkeypatch)
    config = _base_config(tmp_path)
    config["prompt"]["surface"] = "base_kshot"
    stub = _BabbleStub(alias_table=_alias_table(), correct_rate=CORRECT_RATE, wrong_answer="Atlantis", seed=20260610)
    rows = {r["question"]: r for r in probe.read_results(probe.run_probe(config, stub, tmp_path / "out"))}
    unknown = rows["What is the airspeed velocity of an unladen swallow in 1297?"]
    # "Milton" appears only on the babbled second line of the greedy decode; it must not count.
    assert all("\n" not in a for a in unknown["sampled_answers"])
    assert unknown["greedy_answer"] == "Atlantis"
    assert rows["Who wrote Paradise Lost?"]["label"] == "known"
    assert all(r["prompt_surface"] == "base_kshot" for r in rows.values())
    probe.finalize(config, tmp_path / "out" / "probe_results.jsonl", tmp_path / "out")
    import json
    m = json.loads((tmp_path / "out" / "probe_manifest.json").read_text())
    assert m["prompt_surface"]["kshot_sha"] == base_mode_kshot_sha()


def test_default_surface_rows_and_sha_unchanged(tmp_path, monkeypatch):
    _patch_pool_to_fixture(monkeypatch)
    config = _base_config(tmp_path)
    stub = StubBackend(alias_table=_alias_table(), correct_rate=CORRECT_RATE, wrong_answer="Atlantis", seed=20260610)
    for r in probe.read_results(probe.run_probe(config, stub, tmp_path / "out")):
        assert "prompt_surface" not in r
    opted = _base_config(tmp_path)
    opted["prompt"]["surface"] = "base_kshot"
    assert probe.config_sha(config) != probe.config_sha(opted)
