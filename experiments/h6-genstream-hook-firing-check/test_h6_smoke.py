"""CPU smoke for the H6 harness (h6_hook_check.py) itself.

This is a harness-code-correctness check, NOT the H6 instrument check: it
proves the measurement pipeline (firing counters, post-steer hidden-state
readback, no-op delta, gate arithmetic) is wired correctly, using a tiny,
randomly initialized, from-scratch plain-HF causal LM (no download, no GPU,
no multi-GB model). It cannot exercise the actual AK-diagnosed confound
(Unsloth's FastLanguageModel.for_inference optimized decode path bypassing
the hooked module's forward()) because that confound only exists inside
Unsloth's real fused kernels on a real GPU load -- see AMENDMENT.md
"Preconditions" and the module docstring in h6_hook_check.py.

PATH-TUNER on the tiny model is expected to CERTIFY (G1+G2+G3 pass): a plain
HF model's decoder-layer forward() is a normal Python call, so
register_forward_hook fires on every decode step. This mirrors
synaptic-tuner/tests/mech_interp/test_gen_stream_firing.py's own finding on
an equivalent tiny model.

PATH-BESPOKE's SteeringHook + GenerationHookController are ALSO run here, but
against the SAME tiny plain-HF model (no Unsloth): this validates that this
harness's PATH-BESPOKE instrumentation code (adapter, gate arithmetic) is
correct when the underlying hook mechanism does fire normally. It is
explicitly NOT a check of the real AK confound, which requires the actual
Unsloth GPU load this build step must not perform.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
import torch
from transformers import AutoModelForCausalLM, GPT2Config

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import h6_hook_check as h6  # noqa: E402

# Smallest architecture PATH-TUNER's get_decoder_layer already handles
# ("transformer.h"), mirroring synaptic-tuner's own
# tests/mech_interp/test_gen_stream_firing.py fixture.
_VOCAB_SIZE = 64
_HIDDEN_DIM = 32
_PROMPT_LEN = 5
_LAYER_IDX = 0
_DECODE_LEN = 16
_COMMANDED_DOSE = 6.0


def _build_tiny_model():
    torch.manual_seed(0)
    config = GPT2Config(
        n_layer=2, n_embd=_HIDDEN_DIM, n_head=2, vocab_size=_VOCAB_SIZE, n_positions=64,
    )
    model = AutoModelForCausalLM.from_config(config)
    model.eval()
    return model


def _unit_direction() -> torch.Tensor:
    d = torch.zeros(_HIDDEN_DIM, dtype=torch.float32)
    d[0] = 1.0
    return d


def _tiny_enc():
    torch.manual_seed(1)
    input_ids = torch.randint(0, _VOCAB_SIZE, (1, _PROMPT_LEN))
    attention_mask = torch.ones_like(input_ids)
    return {"input_ids": input_ids, "attention_mask": attention_mask}


@pytest.fixture(params=["tuner", "bespoke"])
def path(request):
    return request.param


def _layer_module(path_name: str, model):
    resolver = h6.PATH_LAYER_RESOLVERS[path_name]
    return resolver(model, _LAYER_IDX)


def test_construction_check_recording_hook_sees_poststeer_output(path):
    model = _build_tiny_model()
    layer_module = _layer_module(path, model)
    direction = _unit_direction()
    enc = _tiny_enc()
    result = h6.assert_recording_hook_observes_poststeer_output(
        model, layer_module, h6.PATH_BUILDERS[path], direction, _COMMANDED_DOSE, enc,
    )
    assert result["checked"] is True
    assert result["identical"] is False
    assert result["decode_call_observed"] is True


def test_diagnose_construction_check_genuine_nonfiring_does_not_raise():
    """The Unsloth-for_inference confound this experiment exists to catch: the
    decoder layer's forward() never gets called during decode at all (only
    the prefill fires), so pre/post recording hooks never even see a
    seq_len==1 call. This must be reported, not raised -- H6-G1's own
    call-count gate is what adjudicates it. Real GPU repro: PATH-BESPOKE on
    the actual Unsloth load, see NOTEBOOK.md."""
    pre = {19: torch.zeros(1, 19, _HIDDEN_DIM)}  # only the prefill call fired
    post = {19: torch.zeros(1, 19, _HIDDEN_DIM)}
    result = h6._diagnose_construction_check(pre, post)
    assert result["checked"] is True
    assert result["identical"] is None
    assert result["decode_call_observed"] is False


def test_diagnose_construction_check_raises_when_decode_fires_but_hooks_tie():
    """A real harness bug: the decode call DOES fire (seq_len==1 observed),
    but the post-hook captured the same tensor as the pre-hook -- the
    steering write is not reaching the recording hook. Must raise."""
    pre = {19: torch.zeros(1, 19, _HIDDEN_DIM), 1: torch.ones(1, 1, _HIDDEN_DIM)}
    post = {19: torch.zeros(1, 19, _HIDDEN_DIM), 1: torch.ones(1, 1, _HIDDEN_DIM)}
    with pytest.raises(AssertionError, match="harness construction failure"):
        h6._diagnose_construction_check(pre, post)


def test_diagnose_construction_check_passes_when_decode_fires_and_differs():
    pre = {19: torch.zeros(1, 19, _HIDDEN_DIM), 1: torch.ones(1, 1, _HIDDEN_DIM)}
    post = {19: torch.zeros(1, 19, _HIDDEN_DIM), 1: torch.full((1, 1, _HIDDEN_DIM), 2.0)}
    result = h6._diagnose_construction_check(pre, post)
    assert result["checked"] is True
    assert result["identical"] is False
    assert result["decode_call_observed"] is True


def test_gate_pipeline_passes_on_tiny_plain_hf_model(path):
    model = _build_tiny_model()
    layer_module = _layer_module(path, model)
    direction = _unit_direction()
    enc = _tiny_enc()

    result = h6.run_prompt(path, model, layer_module, direction, _COMMANDED_DOSE, enc, _DECODE_LEN)

    assert result["g1"]["passed"], result["g1"]
    assert result["g2"]["passed"], result["g2"]
    assert result["g3"]["passed"], result["g3"]
    # G4 is diagnostic only; just confirm it produced a well-formed result.
    assert "diverged" in result["g4"]


def test_g1_fails_closed_on_the_ak_failure_signature():
    """Negative control, path-agnostic: evaluate_g1 is the gate function that
    must catch the AK section 8 signature (register_forward_hook never fires
    during decode -- only the single prefill call reaches any hook on the
    module). Unit-tests the gate arithmetic directly with a synthetic
    PassRecord carrying that exact signature, rather than trying to reproduce
    "hook built but not registered" through run_one_condition (which always
    registers whatever controller it is given -- there is no code path in
    this harness that builds a controller and then skips registering it, so
    that scenario cannot be reproduced through the public run path; this is
    the direct, honest way to test the gate's failure-closed behavior)."""
    ak_signature = h6.PassRecord(
        condition="ON", n_generated=16, decode_hidden=[], decode_logits=[],
        in_hook_total_calls=1, independent_total_calls=1, independent_decode_calls=0,
    )
    g1 = h6.evaluate_g1(ak_signature, decode_len=16)
    assert g1["passed"] is False
    assert g1["independent_decode_calls"] == 0

    never_called_signature = h6.PassRecord(
        condition="ON", n_generated=16, decode_hidden=[], decode_logits=[],
        in_hook_total_calls=0, independent_total_calls=16, independent_decode_calls=15,
    )
    g1_mismatch = h6.evaluate_g1(never_called_signature, decode_len=16)
    assert g1_mismatch["passed"] is False  # in-hook counter disagrees with the independent one


def test_evaluate_g3_treats_shared_neg_inf_as_zero_delta_not_nan():
    """Real vocab logits (Qwen3, confirmed on the actual GPU run) carry -inf
    entries for suppressed tokens. Naive (a - b) at a position where BOTH
    are -inf is the indeterminate -inf - (-inf) = NaN, which then fails
    every downstream tolerance check via NaN propagation even though the
    two conditions genuinely agree there. A position where only ONE side is
    -inf is a real divergence and must still fail (delta stays inf)."""
    on = h6.PassRecord(
        condition="NOOP", n_generated=2, decode_hidden=[torch.zeros(4)],
        decode_logits=[torch.tensor([1.0, -float("inf"), 2.0, -float("inf")])],
        in_hook_total_calls=1, independent_total_calls=1, independent_decode_calls=1,
    )
    absent = h6.PassRecord(
        condition="ABSENT", n_generated=2, decode_hidden=[torch.zeros(4)],
        decode_logits=[torch.tensor([1.0, -float("inf"), 2.0, -float("inf")])],
        in_hook_total_calls=None, independent_total_calls=1, independent_decode_calls=1,
    )
    g3 = h6.evaluate_g3(on, absent)
    assert g3["logit_checks"][0]["max_abs_delta"] == 0.0
    assert g3["passed"] is True

    absent_diverged = h6.PassRecord(
        condition="ABSENT", n_generated=2, decode_hidden=[torch.zeros(4)],
        decode_logits=[torch.tensor([1.0, 3.0, 2.0, -float("inf")])],  # index 1 no longer -inf
        in_hook_total_calls=None, independent_total_calls=1, independent_decode_calls=1,
    )
    g3_diverged = h6.evaluate_g3(on, absent_diverged)
    assert g3_diverged["logit_checks"][0]["max_abs_delta"] == float("inf")
    assert g3_diverged["passed"] is False


def test_aggregate_certifies_iff_all_prompts_pass(path):
    model = _build_tiny_model()
    layer_module = _layer_module(path, model)
    direction = _unit_direction()

    per_prompt = []
    for seed in (1, 2, 3):
        torch.manual_seed(seed)
        input_ids = torch.randint(0, _VOCAB_SIZE, (1, _PROMPT_LEN))
        enc = {"input_ids": input_ids, "attention_mask": torch.ones_like(input_ids)}
        per_prompt.append(
            h6.run_prompt(path, model, layer_module, direction, _COMMANDED_DOSE, enc, _DECODE_LEN)
        )

    report = h6.aggregate(path, per_prompt)
    assert report["n_prompts"] == 3
    assert report["h6_g1_passed"] is True
    assert report["h6_g2_passed"] is True
    assert report["h6_g3_passed"] is True
    assert report["certified"] is True
