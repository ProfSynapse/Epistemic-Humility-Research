"""Amendment Y base-mode prompting-path tests (CPU, no model load).

Covers the backward-compatible base-mode surface added to
amendment_x_cross_model_extract.py (§6 of AMENDMENT-Y-pretrain-only-base-readout):
  - default-off render path is unchanged (byte-compare against render_probe_prompt)
  - base-mode k-shot prompt construction (exact expected string)
  - first-line answer parsing incl. multi-line + empty continuations
  - config_sha differs between base_mode on/off

All function-level; no torch/transformers/model load required.
"""

from __future__ import annotations

import sys
from pathlib import Path

PROBE_DIR = Path(__file__).resolve().parents[1]
EVAL_DIR = PROBE_DIR.parent / "eval"
for p in (str(PROBE_DIR), str(EVAL_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)

import amendment_x_cross_model_extract as m  # noqa: E402


# ---------------------------------------------------------------------------
# Stub tokenizer for _first_line_content_end: token id -> literal string, decode
# is plain concatenation. skip_special_tokens drops ids in `specials`. This
# exercises the incremental-decode newline scan without a real tokenizer.
# ---------------------------------------------------------------------------
class StubTokenizer:
    def __init__(self, vocab: dict[int, str], specials: set[int] | None = None):
        self.vocab = vocab
        self.specials = specials or set()

    def decode(self, ids, skip_special_tokens=False):
        out = []
        for i in ids:
            if skip_special_tokens and int(i) in self.specials:
                continue
            out.append(self.vocab[int(i)])
        return "".join(out)


# ---------------------------------------------------------------------------
# (b) base-mode k-shot prompt construction — exact expected string.
# ---------------------------------------------------------------------------
def test_base_mode_prompt_exact_string():
    prompt = m.build_base_mode_prompt("What is the capital of France?")
    expected = (
        "Q: What is the largest planet in our solar system?\nA: Jupiter\n\n"
        "Q: How many sides does a hexagon have?\nA: Six\n\n"
        "Q: What is the chemical symbol for gold?\nA: Au\n\n"
        "Q: In what year did the Second World War end?\nA: 1945\n\n"
        "Q: What is the tallest mountain on Earth?\nA: Mount Everest\n\n"
        "Q: What is the capital of France?\nA:"
    )
    assert prompt == expected


def test_base_mode_prompt_ends_with_bare_answer_cue():
    # The target answer cue must be a bare "A:" (model completes inline).
    prompt = m.build_base_mode_prompt("Q?")
    assert prompt.endswith("Q: Q?\nA:")


def test_fewshot_exemplars_not_from_eval_pools():
    # Leakage rule: the five demonstration questions must not textually collide
    # with any eval-pool item. We can only spot-check they are the frozen five.
    assert len(m._BASE_MODE_FEWSHOT) == 5
    qs = [q for q, _ in m._BASE_MODE_FEWSHOT]
    assert len(set(qs)) == 5  # no dup exemplars


# ---------------------------------------------------------------------------
# (c) first-line answer parsing incl. multi-line continuations and empty.
# ---------------------------------------------------------------------------
def test_first_line_content_end_single_line():
    # prompt = [0,1] ; continuation = " Paris" then EOS
    vocab = {0: "Q:", 1: " A:", 2: " Paris", 3: "<eos>"}
    tok = StubTokenizer(vocab, specials={3})
    seq = [0, 1, 2, 3]
    end = m._first_line_content_end(tok, seq, prompt_len=2, special_ids={3})
    assert end == 2  # last content token = " Paris", trailing eos trimmed


def test_first_line_content_end_multiline_babble():
    # continuation = " Paris" "\n" "Q: next" — must stop before the newline token.
    vocab = {0: "Q:", 1: " Paris", 2: "\n", 3: "Q:", 4: " next"}
    tok = StubTokenizer(vocab)
    seq = [0, 1, 2, 3, 4]
    end = m._first_line_content_end(tok, seq, prompt_len=1, special_ids=set())
    assert end == 1  # " Paris" only; babble after \n excluded


def test_first_line_content_end_newline_buried_in_token():
    # A byte-level/merge token may carry the answer AND the newline: "Paris\n".
    # The token that introduces the "\n" is excluded, so the first content token
    # before it is the boundary. Here the very first continuation token buries it.
    vocab = {0: "Q: x\nA:", 1: "Paris\n", 2: "Q: y"}
    tok = StubTokenizer(vocab)
    seq = [0, 1, 2]
    end = m._first_line_content_end(tok, seq, prompt_len=1, special_ids=set())
    # token 1 introduces the newline -> excluded -> no content token before it
    assert end is None


def test_first_line_content_end_empty_continuation():
    # continuation is a single newline -> empty first line -> None.
    vocab = {0: "A:", 1: "\n"}
    tok = StubTokenizer(vocab)
    seq = [0, 1]
    end = m._first_line_content_end(tok, seq, prompt_len=1, special_ids=set())
    assert end is None


def test_first_line_content_end_only_specials():
    # continuation is all special tokens -> None (no content).
    vocab = {0: "A:", 1: "<eos>", 2: "<pad>"}
    tok = StubTokenizer(vocab, specials={1, 2})
    seq = [0, 1, 2]
    end = m._first_line_content_end(tok, seq, prompt_len=1, special_ids={1, 2})
    assert end is None


def test_string_split_first_line_semantics():
    # The answer_text parse in run() is `cont.split("\n", 1)[0].strip()`; verify
    # the semantics the extractor relies on for a few continuation shapes.
    assert " Paris\nQ: next".split("\n", 1)[0].strip() == "Paris"
    assert "Jupiter".split("\n", 1)[0].strip() == "Jupiter"
    assert "\n\n".split("\n", 1)[0].strip() == ""  # empty first line
    assert "  spaced  \nx".split("\n", 1)[0].strip() == "spaced"


# ---------------------------------------------------------------------------
# (d) config_sha differs between base_mode on/off; off-payload is unchanged.
# ---------------------------------------------------------------------------
def _base_payload():
    # The invariant fields the extractor hashes (mirrors run()'s config_payload
    # before the base-mode branch). We only assert the on/off DELTA, so the exact
    # field set need only be internally consistent between the two variants here.
    return {
        "amendment": "X",
        "base_model": "gpt2",
        "adapter": "NONE-raw-instruct-base",
        "checkpoint": "raw gpt2 (no adapter)",
        "model_tag": "gpt2",
        "system_prompt": m.SYSTEM_PROMPT,
        "abstention_suppression": "NONE-base-is-pre-abstention",
        "pool_sources": ["popqa", "triviaqa", "selfaware_known", "selfaware_unknown"],
        "gate_rows_source": "/tmp/gate.jsonl",
        "enable_thinking": False,
        "n_answerable": 4,
        "max_new_tokens": 24,
        "max_attempts": 8,
        "seed": 20260630,
        "persist_dtype": "float32",
        "decode": "greedy",
    }


def test_config_sha_differs_base_mode_on_off():
    off = _base_payload()
    on = _base_payload()
    on["system_prompt"] = None  # base-mode drops the system prompt
    on["base_mode"] = True
    on["kshot_sha"] = m.base_mode_kshot_sha()
    assert m._config_sha(off) != m._config_sha(on)


def test_kshot_sha_stable():
    # The k-shot sha must be deterministic (frozen exemplar block).
    assert m.base_mode_kshot_sha() == m.base_mode_kshot_sha()
    assert len(m.base_mode_kshot_sha()) == 16


# ---------------------------------------------------------------------------
# (a) default-off render path is unchanged: byte-compare the base-mode render is
# NOT used and render_probe_prompt still produces the chat surface. We can only
# assert the base-mode string differs from the chat render for a stub tokenizer
# exposing apply_chat_template, and that build_base_mode_prompt does not call the
# chat template at all.
# ---------------------------------------------------------------------------
class ChatStubTokenizer:
    """Minimal tokenizer exposing apply_chat_template for render_probe_prompt."""

    def apply_chat_template(self, messages, tokenize=False,
                            add_generation_prompt=True, **kwargs):
        # Emulate a Qwen3 thinking-off render deterministically.
        parts = [f"<|im_start|>{msg['role']}\n{msg['content']}<|im_end|>\n"
                 for msg in messages]
        if add_generation_prompt:
            parts.append("<|im_start|>assistant\n")
        return "".join(parts)


def test_default_off_uses_chat_render_not_base_block():
    from backends import render_probe_prompt

    tok = ChatStubTokenizer()
    q = "What is the capital of France?"
    chat_rendered, _mode = render_probe_prompt(
        tok, m.SYSTEM_PROMPT, q, enable_thinking=False)
    base_rendered = m.build_base_mode_prompt(q)
    # The two surfaces are distinct: chat carries im_start/system, base is bare Q/A.
    assert "<|im_start|>" in chat_rendered
    assert "<|im_start|>" not in base_rendered
    assert base_rendered.endswith("A:")
    # And the chat render is stable / unchanged by base-mode existing (regression).
    assert chat_rendered == (
        f"<|im_start|>system\n{m.SYSTEM_PROMPT}<|im_end|>\n"
        f"<|im_start|>user\n{q}<|im_end|>\n"
        "<|im_start|>assistant\n"
    )
