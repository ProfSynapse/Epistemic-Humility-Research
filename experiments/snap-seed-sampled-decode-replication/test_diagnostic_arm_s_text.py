#!/usr/bin/env python3
"""CPU-only pytest smoke for diagnostic_arm_s_text.py -- NO GPU, NO model
download. model.generate() is mocked; every check here exercises real
control flow (gen_lib._first_eos_position, gen_lib.grade_clean_tighten,
grader.grade_one, RunLog) on synthetic tensors/text.

Run: python3 -m pytest test_diagnostic_arm_s_text.py -v
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import torch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent.parent / "synaptic-tuner"))

import gen_lib as gl  # noqa: E402
import grader  # noqa: E402
from shared.utilities.run_log import RunLog  # noqa: E402

import diagnostic_arm_s_text as diag  # noqa: E402


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
    """model.generate() returns a fixed tensor; if a readback dict is
    configured, setting it on the live controller.hook simulates the real
    per-decode-step forward hook firing during a real generate() call."""

    def __init__(self, output_tensor: torch.Tensor, readback_on_generate: dict | None = None):
        self.output_tensor = output_tensor
        self.readback_on_generate = readback_on_generate
        self.controller_ref: MockController | None = None

    def generate(self, **kwargs):
        if self.controller_ref is not None and self.readback_on_generate is not None:
            self.controller_ref.hook.last_readback = self.readback_on_generate
        return self.output_tensor


class MockTokenizer:
    eos_token_id = 999
    pad_token_id = 0

    def convert_tokens_to_ids(self, token: str):
        return None  # no <|im_end|> in this mock vocabulary; eos_ids == {999}

    def decode(self, tokens, skip_special_tokens: bool = True) -> str:
        return " ".join(str(int(t)) for t in tokens.tolist())


PROMPT_LEN = 3


def _build_batch(rows: list[list[int]]) -> torch.Tensor:
    """rows: per-sample GENERATED token ids only (post-prompt); prompt
    columns (arbitrary values 1..PROMPT_LEN) are prepended identically to
    every row, matching the real N-identical-copies batch shape."""
    prompt = list(range(1, PROMPT_LEN + 1))
    return torch.tensor([prompt + r for r in rows], dtype=torch.long)


def test_batched_diagnostic_termination_cases():
    """Three canonical cases (early eos, boundary eos, never) reproduce
    gen_lib._first_eos_position's own reported position AND the same
    terminated_naturally boolean gen_lib.run_batched_sampled_pass derives
    from it (eos_pos is not None and eos_pos < n - 1)."""
    out = _build_batch([
        [10, 11, 999, 0, 0],   # eos at index 2 of 5 -> terminated True
        [10, 11, 12, 13, 999],  # eos only at last index -> terminated False (conservative)
        [10, 11, 12, 13, 14],   # no eos -> terminated False
    ])
    hook = MockHook()
    controller = MockController(hook)
    model = MockModel(out, readback_on_generate={"measured": [200.0, 200.0, 200.0]})
    model.controller_ref = controller
    tokenizer = MockTokenizer()
    enc = {"input_ids": out[:, :PROMPT_LEN], "attention_mask": torch.ones_like(out[:, :PROMPT_LEN])}

    samples, readback = diag.run_batched_sampled_pass_diagnostic(
        model, controller, tokenizer, enc, mode="gen_stream", strength=1.0,
        generation_kwargs={"do_sample": True, "temperature": 0.7, "top_p": 0.9}, max_new=5,
    )

    assert len(samples) == 3
    assert samples[0]["eos_pos"] == 2 and samples[0]["terminated_naturally"] is True
    assert samples[0]["n_new_tokens_raw"] == 5
    assert samples[0]["text"] == "10 11 999"  # truncated at eos, matches gen_lib's own content slice
    assert samples[0]["raw_text_untruncated"] == "10 11 999 0 0"

    assert samples[1]["eos_pos"] == 4 and samples[1]["terminated_naturally"] is False
    assert samples[1]["text"] == samples[1]["raw_text_untruncated"] == "10 11 12 13 999"

    assert samples[2]["eos_pos"] is None and samples[2]["terminated_naturally"] is False
    assert samples[2]["text"] == "10 11 12 13 14"

    assert readback == {"measured": [200.0, 200.0, 200.0]}
    assert controller.calls[0] == ("begin_pass", "gen_stream", 1.0)
    assert controller.calls[-1] == ("reset",)


def test_diagnostic_matches_pinned_run_batched_sampled_pass():
    """Parity check: the diagnostic wrapper's (text, terminated_naturally)
    per sample must be byte-identical to what the PINNED
    gen_lib.run_batched_sampled_pass itself returns for the same mocked
    generate() output -- proving the diagnostic mirror does not silently
    diverge from the production Arm S generation path it is meant to
    re-run. gen_lib.py is called, never copied or edited."""
    out = _build_batch([
        [10, 11, 999, 0, 0],
        [10, 11, 12, 13, 999],
        [10, 11, 12, 13, 14],
    ])
    tokenizer = MockTokenizer()
    enc = {"input_ids": out[:, :PROMPT_LEN], "attention_mask": torch.ones_like(out[:, :PROMPT_LEN])}
    gen_kwargs = {"do_sample": True, "temperature": 0.7, "top_p": 0.9}

    hook_a = MockHook()
    controller_a = MockController(hook_a)
    model_a = MockModel(out)
    pinned_texts, pinned_terminated, _pinned_readback = gl.run_batched_sampled_pass(
        model_a, controller_a, enc, "gen_stream", 1.0, tokenizer,
        generation_kwargs=gen_kwargs, max_new=5,
    )

    hook_b = MockHook()
    controller_b = MockController(hook_b)
    model_b = MockModel(out)
    samples, _readback = diag.run_batched_sampled_pass_diagnostic(
        model_b, controller_b, tokenizer, enc, "gen_stream", 1.0,
        generation_kwargs=gen_kwargs, max_new=5,
    )

    assert pinned_texts == [s["text"] for s in samples]
    assert pinned_terminated == [s["terminated_naturally"] for s in samples]


def test_off_mode_readback_is_none_even_if_hook_set():
    """mode == "off" must report readback=None regardless of what the hook
    happens to hold, matching gen_lib.run_batched_sampled_pass's own rule."""
    out = _build_batch([[10, 11, 12, 13, 14]])
    hook = MockHook()
    controller = MockController(hook)
    model = MockModel(out, readback_on_generate={"measured": [0.0]})
    model.controller_ref = controller
    tokenizer = MockTokenizer()
    enc = {"input_ids": out[:, :PROMPT_LEN], "attention_mask": torch.ones_like(out[:, :PROMPT_LEN])}

    samples, readback = diag.run_batched_sampled_pass_diagnostic(
        model, controller, tokenizer, enc, mode="off", strength=0.0,
        generation_kwargs={"do_sample": True, "temperature": 0.7, "top_p": 0.9}, max_new=5,
    )
    assert readback is None
    assert len(samples) == 1


def test_grade_samples_preserves_full_subgrade_dicts():
    """grade_samples() must attach the FULL gen_lib.grade_clean_tighten dict
    (well_formed, n_answer_keys, single_answer_key, trailing_clean,
    answer_value, semantic_refuse, terminated_naturally, degenerate,
    clean_tighten) and the full grader.grade_one dict (degenerate, refused,
    answered, correct, well_formed_correct) -- not just the two booleans
    the resolved H3 run kept."""
    clean_refusal = '{"answer": "I don\'t know the answer", "response_confidence": 0.95}'
    messy_but_refusing = '{"answer": "I don\'t know the answer"} extra trailing junk'
    correct_answer = '{"answer": "Paris", "response_confidence": 0.9}'

    samples = [
        {"sample_idx": 0, "text": clean_refusal, "raw_text_untruncated": clean_refusal,
         "n_new_tokens_raw": 20, "eos_pos": 18, "terminated_naturally": True},
        {"sample_idx": 1, "text": messy_but_refusing, "raw_text_untruncated": messy_but_refusing,
         "n_new_tokens_raw": 25, "eos_pos": None, "terminated_naturally": False},
        {"sample_idx": 2, "text": correct_answer, "raw_text_untruncated": correct_answer,
         "n_new_tokens_raw": 15, "eos_pos": 14, "terminated_naturally": True},
    ]
    graded = diag.grade_samples(samples, aliases=["Paris", "City of Paris"])

    ct0 = graded[0]["grade_clean_tighten"]
    assert set(ct0) == {
        "well_formed", "n_answer_keys", "single_answer_key", "trailing_clean",
        "answer_value", "semantic_refuse", "terminated_naturally", "degenerate",
        "clean_tighten",
    }
    assert ct0["clean_tighten"] is True
    assert ct0["semantic_refuse"] is True
    assert ct0["terminated_naturally"] is True

    # messy_but_refusing: well-formed refusal semantically, but trailing junk
    # after the JSON object AND not terminated naturally -> decomposes the
    # exact NEITHER-bucket distinction the resolved run's booleans-only logs
    # could not make (refused-but-messy, not answered-wrong, not degenerate).
    ct1 = graded[1]["grade_clean_tighten"]
    assert ct1["semantic_refuse"] is True
    assert ct1["trailing_clean"] is False
    assert ct1["clean_tighten"] is False
    wfc1 = graded[1]["grade_one"]
    assert wfc1["refused"] is True
    assert wfc1["answered"] is False

    wfc2 = graded[2]["grade_one"]
    assert set(wfc2) == {"degenerate", "refused", "answered", "correct", "well_formed_correct"}
    assert wfc2["well_formed_correct"] is True

    # Real grader.grade_one, called directly, must agree (grade_samples does
    # not reimplement grading, only attaches gen_lib/grader's own output).
    assert graded[2]["grade_one"] == grader.grade_one(correct_answer, ["Paris", "City of Paris"])


def test_persistence_schema_round_trip():
    """The row-level record run_row_diagnostic would produce (row_key,
    role, fire, seed, derived_seed, readback, samples[]) survives a RunLog
    JSONL write + reopen with the full sub-grade dicts intact -- this is the
    schema the H3 resolved run's booleans-only logs violated the program's
    data-exhaust principle by not persisting."""
    clean_refusal = '{"answer": "I don\'t know the answer", "response_confidence": 0.95}'
    raw_samples = [{
        "sample_idx": i, "text": clean_refusal, "raw_text_untruncated": clean_refusal,
        "n_new_tokens_raw": 20, "eos_pos": 18, "terminated_naturally": True,
    } for i in range(8)]
    graded_samples = diag.grade_samples(raw_samples, aliases=[])

    row_record = {
        "row_key": "ahx::kuq_ku_unknown_x::002650", "role": "confab", "fire": True,
        "seed": diag.DIAGNOSTIC_SEED, "derived_seed": 123456789,
        "readback": {"measured": [200.02] * 8},
        "samples": graded_samples,
    }

    with tempfile.TemporaryDirectory() as td:
        log_path = Path(td) / "diagnostic_arm_s_text_seed20260710.jsonl"
        run_config = {"seed": diag.DIAGNOSTIC_SEED, "dose_target": 200.0, "n_samples": 8}

        log1 = RunLog(log_path, run_config, key_field="row_key")
        log1.record(row_record["row_key"], row_record)
        log1.finalize({"n_rows": 1})
        log1.close()

        log2 = RunLog(log_path, run_config, key_field="row_key")
        stored = log2.done_keys()
        assert row_record["row_key"] in stored
        log2.close()

        text = log_path.read_text(encoding="utf-8").strip()
        reloaded = __import__("json").loads(text)

    for field in ("row_key", "role", "fire", "seed", "derived_seed", "readback", "samples"):
        assert field in reloaded, f"missing field {field!r} in persisted record"

    assert len(reloaded["samples"]) == 8
    reloaded_ct = reloaded["samples"][0]["grade_clean_tighten"]
    assert set(reloaded_ct) == {
        "well_formed", "n_answer_keys", "single_answer_key", "trailing_clean",
        "answer_value", "semantic_refuse", "terminated_naturally", "degenerate",
        "clean_tighten",
    }
    assert reloaded_ct["clean_tighten"] is True
    reloaded_wfc = reloaded["samples"][0]["grade_one"]
    assert set(reloaded_wfc) == {"degenerate", "refused", "answered", "correct", "well_formed_correct"}
    # generation text itself must also survive the round trip (this is the
    # whole point of the diagnostic: the resolved run discarded it).
    assert reloaded["samples"][0]["text"] == clean_refusal


def test_out_path_naming():
    assert diag._out_path(20260710).name == "diagnostic_arm_s_text_seed20260710.jsonl"


if __name__ == "__main__":
    raise SystemExit(__import__("pytest").main([__file__, "-v"]))
