#!/usr/bin/env python3
"""CPU-only pytest smoke for the data-exhaust persistence schema ported into
pipeline.run_batch_sampled_for_row (2026-07-13) -- NO GPU, NO model download.
model.generate() and model_lib.render() are mocked; the rest of the call
path (gen_lib.run_batched_sampled_pass_with_text, gen_lib.grade_clean_tighten,
grader.grade_one) is the REAL pinned code.

Asserts the schema the resolved H3 run's booleans-only logs violated the
program's data-exhaust principle by not persisting: per-sample generation
text, the raw termination inputs (eos_pos, n_new_tokens_raw), and the FULL
grade_clean_tighten sub-grade dict, alongside the existing
clean_tighten/well_formed_correct/not_well_formed_correct booleans that
compute_h3_g1/g2/score_row_samples already depend on.

Run: python3 -m pytest test_pipeline_persistence_schema.py -v
"""

from __future__ import annotations

import sys
from pathlib import Path

import torch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent.parent / "synaptic-tuner"))

import pipeline as pl  # noqa: E402


class MockHook:
    def __init__(self) -> None:
        self.last_readback = None


class MockController:
    def __init__(self, hook: MockHook) -> None:
        self.hook = hook
        self.calls: list[tuple] = []

    def begin_pass(self, mode, strength, attention_mask=None, force_active=False):
        self.calls.append(("begin_pass", mode, strength))

    def reset(self):
        self.calls.append(("reset",))


class MockModel:
    """model.generate() returns a fixed tensor: N_SAMPLES identical-length
    rows, each a clean JSON refusal that ends in eos at the LAST generated
    column -- the exact geometry the diagnostic identified as the failure
    mechanism (batch ties for longest, eos at the block's final position)."""

    def __init__(self, output_tensor: torch.Tensor) -> None:
        self.output_tensor = output_tensor

    def generate(self, **kwargs):
        return self.output_tensor


class MockTokenizer:
    eos_token_id = 999
    pad_token_id = 0

    def __call__(self, prompt: str, return_tensors: str = "pt"):
        ids = torch.tensor([[1, 2, 3]])
        return {"input_ids": ids, "attention_mask": torch.ones_like(ids)}

    def convert_tokens_to_ids(self, token: str):
        return None  # no <|im_end|> in this mock vocabulary; eos_ids == {999}

    def decode(self, tokens, skip_special_tokens: bool = True) -> str:
        ids = [int(t) for t in tokens.tolist()]
        if ids == REFUSAL_IDS:
            return REFUSAL_TEXT
        return " ".join(str(t) for t in ids)


REFUSAL_TEXT = '{"answer": "I don\'t know the answer"}'
REFUSAL_IDS = [10, 11, 999]  # tokenizer.decode(these) -> REFUSAL_TEXT; eos (999) at last column
N_SAMPLES = 2


def test_run_batch_sampled_for_row_persists_full_schema(monkeypatch):
    monkeypatch.setattr(pl.ml, "render", lambda row: "mock prompt")

    prompt_len = 3  # matches MockTokenizer's fixed 3-token prompt encoding
    row_tail = REFUSAL_IDS  # eos at final column, per-row
    batch = torch.tensor([[1, 2, 3] + row_tail for _ in range(N_SAMPLES)], dtype=torch.long)

    hook = MockHook()
    controller = MockController(hook)
    model = MockModel(batch)
    tokenizer = MockTokenizer()
    row = {"row_key": "confab::row1", "role": "confab", "fire": True, "aliases": []}

    rec = pl.run_batch_sampled_for_row(
        model, controller, tokenizer, "cpu", row, seed=20260710,
        strength_c_hat=200.0, n_samples=N_SAMPLES,
    )

    assert rec["row_key"] == "confab::row1"
    assert rec["role"] == "confab"
    assert rec["fire"] is True
    assert len(rec["samples"]) == N_SAMPLES

    for sample in rec["samples"]:
        # Pre-existing fields the gates already depend on (score_row_samples
        # reads these three keys) must survive unchanged.
        assert set(["clean_tighten", "well_formed_correct", "not_well_formed_correct"]) <= set(sample)
        assert isinstance(sample["clean_tighten"], bool)

        # Data-exhaust additions: text, raw termination inputs, and the full
        # sub-grade dict must all be present and intact.
        assert sample["text"] == REFUSAL_TEXT
        assert sample["n_new_tokens_raw"] == len(row_tail)
        assert sample["eos_pos"] == len(row_tail) - 1  # eos at the LAST column
        ct = sample["grade_clean_tighten"]
        assert set(ct) == {
            "well_formed", "n_answer_keys", "single_answer_key", "trailing_clean",
            "answer_value", "semantic_refuse", "terminated_naturally", "degenerate",
            "clean_tighten",
        }
        # Corrected termination rule: eos at the final column IS terminated.
        assert ct["terminated_naturally"] is True
        assert ct["clean_tighten"] is True
        assert sample["clean_tighten"] == ct["clean_tighten"]


if __name__ == "__main__":
    raise SystemExit(__import__("pytest").main([__file__, "-v"]))
