#!/usr/bin/env python3
"""CPU-only pytest regression tests for gen_lib.py's batched termination
rule -- NO GPU, NO model download. model.generate() is mocked.

Registered in NOTEBOOK.md's 2026-07-13 "DIAGNOSTIC RESULT" entry: the
batched termination rule misgraded eos-at-final-position samples as
not-terminated, contradicting the registered metric text ("terminated
naturally (stopped before max_new)"). These tests lock the corrected
semantics (gen_lib.is_terminated_naturally):
  - terminated_naturally = True iff an eos token is found ANYWHERE in the
    sample's generated block (including the final position), OR the
    generated block length < max_new.
  - terminated_naturally = False only when NO eos was emitted AND the
    block ran to max_new.

Run: python3 -m pytest test_gen_lib_termination.py -v
(NEVER bare `python3 test_gen_lib_termination.py` -- pytest test_
functions are not called by a bare interpreter and the script would exit
0 without asserting anything.)
"""

from __future__ import annotations

import sys
from pathlib import Path

import torch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent.parent / "synaptic-tuner"))

import gen_lib as gl  # noqa: E402


class MockHook:
    def __init__(self) -> None:
        self.last_readback = None


class MockController:
    """Mimics GenerationInterventionController's begin_pass/reset contract
    without touching any real model forward pass."""

    def __init__(self, hook: MockHook) -> None:
        self.hook = hook
        self.calls: list[tuple] = []

    def begin_pass(self, mode, strength, attention_mask=None, force_active=False):
        self.calls.append(("begin_pass", mode, strength))

    def reset(self):
        self.calls.append(("reset",))


class MockModel:
    """model.generate() returns a fixed tensor; no real forward pass."""

    def __init__(self, output_tensor: torch.Tensor) -> None:
        self.output_tensor = output_tensor

    def generate(self, **kwargs):
        return self.output_tensor


class MockTokenizer:
    eos_token_id = 999
    pad_token_id = 0

    def convert_tokens_to_ids(self, token: str):
        return None  # no <|im_end|> in this mock vocabulary; eos_ids == {999}

    def decode(self, tokens, skip_special_tokens: bool = True) -> str:
        return " ".join(str(int(t)) for t in tokens.tolist())


PROMPT_LEN = 3
EOS_IDS = {999}


def _build_batch(rows: list[list[int]]) -> torch.Tensor:
    """rows: per-sample GENERATED token ids only (post-prompt); prompt
    columns are prepended identically to every row (N-identical-copies
    batch shape, matching Arm S's real batching contract)."""
    prompt = list(range(1, PROMPT_LEN + 1))
    return torch.tensor([prompt + r for r in rows], dtype=torch.long)


def _run(rows: list[list[int]], max_new: int) -> tuple[list[str], list[bool]]:
    out = _build_batch(rows)
    hook = MockHook()
    controller = MockController(hook)
    model = MockModel(out)
    tokenizer = MockTokenizer()
    enc = {"input_ids": out[:, :PROMPT_LEN], "attention_mask": torch.ones_like(out[:, :PROMPT_LEN])}
    texts, terminated, _readback = gl.run_batched_sampled_pass(
        model, controller, enc, "gen_stream", 1.0, tokenizer,
        generation_kwargs={"do_sample": True, "temperature": 0.7, "top_p": 0.9},
        max_new=max_new,
    )
    return texts, terminated


# ---------------------------------------------------------------------------
# (a) eos at the LAST generated position -> terminated (the fixed corner).
# ---------------------------------------------------------------------------

def test_eos_at_last_position_is_terminated():
    row = torch.tensor([10, 11, 12, 13, 999])
    eos_pos = gl._first_eos_position(row, EOS_IDS)
    assert eos_pos == 4
    assert gl.is_terminated_naturally(eos_pos, n_new_tokens=5, max_new=5) is True


def test_eos_at_last_position_terminated_via_full_pass():
    texts, terminated = _run([[10, 11, 12, 13, 999]], max_new=5)
    assert terminated == [True]
    assert texts == ["10 11 12 13 999"]


# ---------------------------------------------------------------------------
# (b) no eos, block ran to max_new -> not terminated.
# ---------------------------------------------------------------------------

def test_no_eos_and_full_max_new_is_not_terminated():
    row = torch.tensor([10, 11, 12, 13, 14])
    eos_pos = gl._first_eos_position(row, EOS_IDS)
    assert eos_pos is None
    assert gl.is_terminated_naturally(eos_pos, n_new_tokens=5, max_new=5) is False


def test_no_eos_and_full_max_new_via_full_pass():
    texts, terminated = _run([[10, 11, 12, 13, 14]], max_new=5)
    assert terminated == [False]
    assert texts == ["10 11 12 13 14"]


# ---------------------------------------------------------------------------
# (c) eos mid-block -> terminated, text truncated at first eos.
# ---------------------------------------------------------------------------

def test_eos_mid_block_terminated_and_text_truncated():
    row = torch.tensor([10, 11, 999, 13, 14])
    eos_pos = gl._first_eos_position(row, EOS_IDS)
    assert eos_pos == 2
    assert gl.is_terminated_naturally(eos_pos, n_new_tokens=5, max_new=5) is True

    texts, terminated = _run([[10, 11, 999, 13, 14]], max_new=5)
    assert terminated == [True]
    assert texts == ["10 11 999"]  # truncated at (and including) the eos token


# ---------------------------------------------------------------------------
# (d) no eos, block SHORTER than max_new -> terminated (all rows finished
# early, so HF's generate() returned a narrower tensor than max_new).
# ---------------------------------------------------------------------------

def test_no_eos_but_block_shorter_than_max_new_is_terminated():
    assert gl.is_terminated_naturally(eos_pos=None, n_new_tokens=3, max_new=5) is True


def test_no_eos_but_block_shorter_than_max_new_via_full_pass():
    # Every row in the batch already finished before max_new, so the
    # tensor HF returns is narrower than max_new (3 generated columns, cap
    # of 5) with no eos id inside the returned slice itself.
    texts, terminated = _run([[10, 11, 12]], max_new=5)
    assert terminated == [True]
    assert texts == ["10 11 12"]


# ---------------------------------------------------------------------------
# (e) batch-of-8 diagnostic geometry: every member emits eos and ties for
# longest-in-batch (eos at the block's final column for all) -> ALL graded
# terminated. This reproduces the exact mechanism the diagnostic identified
# (764/769 refused-but-messy Arm S samples failing ONLY this conjunct).
# ---------------------------------------------------------------------------

def test_batch_of_8_all_tie_for_longest_with_eos_at_final_position_all_terminated():
    rows = [[1, 2, 3, 4, 5, 999] for _ in range(8)]  # 8 identical-length copies, eos at col 5
    texts, terminated = _run(rows, max_new=6)
    assert len(terminated) == 8
    assert terminated == [True] * 8
    assert texts == ["1 2 3 4 5 999"] * 8


def test_batch_of_8_mixed_early_and_boundary_eos_all_terminated_none_never():
    """A more realistic batch: some rows stop early, some tie for longest
    with eos exactly at the final column, none exhaust the budget without
    eos -- every row terminated."""
    rows = [
        [1, 999, 0, 0, 0, 0],       # early eos (padded with 0s after)
        [1, 2, 3, 999, 0, 0],       # mid eos
        [1, 2, 3, 4, 5, 999],       # boundary eos (longest-in-batch)
        [1, 2, 3, 4, 5, 999],
        [1, 999, 0, 0, 0, 0],
        [1, 2, 3, 999, 0, 0],
        [1, 2, 3, 4, 5, 999],
        [1, 2, 3, 4, 5, 999],
    ]
    _texts, terminated = _run(rows, max_new=6)
    assert terminated == [True] * 8


if __name__ == "__main__":
    raise SystemExit(__import__("pytest").main([__file__, "-v"]))
