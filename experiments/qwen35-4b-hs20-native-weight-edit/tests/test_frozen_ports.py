"""Frozen render/grader/detector-v2 ports: origin pins, byte/behavior equivalence, question-only render."""

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import pytest

from hs20_nwe import detector_v2 as det_port
from hs20_nwe import gen_lib as gen_port
from hs20_nwe import grader as grader_port
from hs20_nwe import render as render_port

PKG = Path(grader_port.__file__).parent
REPO = Path(__file__).resolve().parents[3]
ORIGIN = REPO / "experiments/gate-contribution-factorial"
ORIGINS = json.loads((PKG / "ORIGINS.json").read_text())


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


@pytest.mark.parametrize("name", sorted(ORIGINS["files"]))
def test_origin_and_port_hashes_are_pinned(name):
    entry = ORIGINS["files"][name]
    assert sha(ORIGIN / name) == entry["origin_sha256"], "origin file drifted from the recorded pin"
    assert sha(PKG / name) == entry["port_sha256"], "port changed after being pinned"


def test_unchanged_files_are_byte_identical():
    for name, entry in ORIGINS["files"].items():
        if entry["change"] == "byte-identical":
            assert entry["origin_sha256"] == entry["port_sha256"]


def _load_origin_modules():
    """Origin modules import their siblings by bare name; alias them for this test only."""
    names = ("grader", "detector_v2", "gen_lib", "render")
    saved = {n: sys.modules.get(n) for n in names}
    try:
        mods = {}
        for n in ("grader", "detector_v2", "gen_lib"):
            spec = importlib.util.spec_from_file_location(n, ORIGIN / f"{n}.py")
            mod = importlib.util.module_from_spec(spec)
            sys.modules[n] = mod
            spec.loader.exec_module(mod)
            mods[n] = mod
        spec = importlib.util.spec_from_file_location("origin_render", ORIGIN / "render.py")
        mods["render"] = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mods["render"])
        return mods
    finally:
        for n, v in saved.items():
            if v is None:
                sys.modules.pop(n, None)
            else:
                sys.modules[n] = v


CORPUS = [
    '{"answer": "I don\'t know the answer", "response_confidence": 0.9}',
    '{"answer": "It is impossible to predict the outcome.", "response_confidence": 0.8}',
    '{"answer": "Paris is the capital of France.", "response_confidence": 0.99}',
    '{"answer": "Probably Berlin, but I cannot determine this.", "response_confidence": 0.4}',
    '{"answer": "' + "True " * 90,
    "", "   ", "!!!", "I do not know", "abstain from answering",
    '{"answer": "dhoti is worn in India", "response_confidence": 0.95}',
    "The answer is unclear and varies by source.",
]


@pytest.mark.parametrize("aliases", [None, [], ["dhoti"], ["Paris", "france"]])
def test_grader_detector_genlib_behavior_equals_origin(aliases):
    o = _load_origin_modules()
    for text in CORPUS:
        for terminated in (True, False):
            assert gen_port.grade_row(text, terminated, aliases) == o["gen_lib"].grade_row(text, terminated, aliases)
            assert grader_port.grade_one(text, aliases) == o["grader"].grade_one(text, aliases)
            assert det_port.grade_one_v2(text, aliases) == o["detector_v2"].grade_one_v2(text, aliases)


class FakeTokenizer:
    chat_template = "x"

    def apply_chat_template(self, messages, tokenize=False, add_generation_prompt=True, **kw):
        return "<s>" + "|".join(f"{m['role']}:{m['content']}" for m in messages) + "<think>\n\n</think>"


def test_render_equals_origin_with_a_fake_tokenizer_and_reads_question_only(monkeypatch):
    o = _load_origin_modules()
    monkeypatch.setattr(render_port, "_tokenizer", lambda: FakeTokenizer())
    monkeypatch.setattr(o["render"], "_tokenizer", lambda: FakeTokenizer())
    monkeypatch.setenv("HS20NWE_RENDER_MODEL", "m")
    monkeypatch.setenv("GATEFACT_RENDER_MODEL", "m")
    row = {"row_key": "a", "question": "Who wrote X?"}
    decorated = {**row, "aliases": ["secret"], "role": "confab", "answer_text": "OLD", "fire": True, "source": "kuq"}
    assert render_port.render(row) == o["render"].render(row)
    assert render_port.render(decorated) == render_port.render(row)
    assert "secret" not in render_port.render(decorated)
    with pytest.raises(KeyError):
        render_port.render({"row_key": "b"})


def test_render_env_namespace_is_distinct():
    src = (PKG / "render.py").read_text()
    assert "HS20NWE_RENDER_MODEL" in src and "GATEFACT" not in src.replace("(HS20NWE", "")
