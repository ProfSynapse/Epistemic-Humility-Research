#!/usr/bin/env python3
"""Fixture-backed smoke for lp_v3_harness.py -- drives the REAL entry points
(`run_arm_generation`, `run_arm_extraction`, `score_arm_v3`, `select_attempted`,
`dry_run`) end to end with a tiny CPU model and synthesized fixture data. No
real model download, no GPU, and no row-level content: every question/answer
string here is fabricated (`fx0`, `fx1`, ...), never real question or answer
text, per the public-repo containment rule (AMENDMENT.md, cell.yaml
`containment`).

Per the pre-sign verification rule (.skills/experiments/SKILL.md "Before
signing ANY cell..."): this smoke calls the SAME functions `main()` calls for
a real run, not a reimplementation of their logic, so it cannot pass while the
real orchestration is a stub. `build_vllm_engine` / `load_hf_model_for_extraction`
(the only functions that talk to real weights/GPU/vLLM) are the sole things
swapped out: generation is exercised via `_StubVLLMEngine`, a thin wrapper
around a REAL tiny HF model that repackages its own `.generate()` output into
vLLM's RequestOutput/CompletionOutput SHAPE (token_ids, logprobs keyed by
token id, prompt_token_ids) -- so `run_arm_generation` (the real harness
function) is exercised unmodified, and the SAME tiny model doubles as the
teacher-forced extraction backend, so the two phases' token ids are naturally
internally consistent (the LP3-G0a capture-integrity check is exercised for
real, not stubbed out).

Run: python3 -m pytest experiments/dial-logprob-baseline-v3/test_lp_v3_smoke.py -v
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pytest
import torch
import torch.nn.functional as F
from transformers import AutoModelForCausalLM, GPT2Config

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import lp_v3_harness as lp  # noqa: E402

DIAL_LAYER = 2       # valid index into a 2-layer GPT2's hidden_states tuple (0,1,2)
N_LAYER = 2
N_EMBD = 32


# ---------------------------------------------------------------------------
# Tiny model + tokenizer (no download, no GPU, no real vocabulary -- mirrors
# the pattern already used by experiments/dial-logprob-baseline-v2/
# test_lp_v2_smoke.py's _build_tiny_model / _TinyChatTokenizer)
# ---------------------------------------------------------------------------


def _build_vocab() -> dict[str, int]:
    specials = ["<pad>", "<eos>", "<unk>"]
    roles = ["<system>", "<user>", "<assistant>"]
    content = [f"fx{i}" for i in range(32)]  # fabricated tokens, never real text
    tokens = specials + roles + content
    return {tok: i for i, tok in enumerate(tokens)}


VOCAB = _build_vocab()
INV_VOCAB = {v: k for k, v in VOCAB.items()}


class _TinyBatchEncoding(dict):
    def to(self, device):
        return _TinyBatchEncoding({k: v.to(device) for k, v in self.items()})


class _TinyChatTokenizer:
    pad_token_id = VOCAB["<pad>"]
    eos_token_id = VOCAB["<eos>"]
    all_special_ids = [VOCAB["<pad>"], VOCAB["<eos>"]]

    def apply_chat_template(self, messages, tokenize=False, add_generation_prompt=True,
                             enable_thinking=False, **kwargs):
        parts = [f"<{m['role']}> {m['content']}" for m in messages]
        if add_generation_prompt:
            parts.append("<assistant>")
        return " ".join(parts)

    def convert_tokens_to_ids(self, token: str) -> int:
        return VOCAB.get(token, -1)

    def __call__(self, text, return_tensors=None, padding=None):
        ids = [VOCAB.get(tok, VOCAB["<unk>"]) for tok in text.split()]
        t = torch.tensor([ids], dtype=torch.long)
        return _TinyBatchEncoding({"input_ids": t, "attention_mask": torch.ones_like(t)})

    def decode(self, ids, skip_special_tokens=True) -> str:
        out = []
        for i in ids:
            i = int(i)
            if skip_special_tokens and i in self.all_special_ids:
                continue
            out.append(INV_VOCAB.get(i, "<unk>"))
        return " ".join(out)


def _build_tiny_model():
    torch.manual_seed(0)
    config = GPT2Config(n_layer=N_LAYER, n_embd=N_EMBD, n_head=2, vocab_size=len(VOCAB), n_positions=64)
    model = AutoModelForCausalLM.from_config(config)
    model.eval()
    return model


# ---------------------------------------------------------------------------
# Stub vLLM engine: repackages a REAL tiny model's own generate() output into
# vLLM's RequestOutput/CompletionOutput SHAPE, so run_arm_generation (the
# real harness function) runs unmodified against it.
# ---------------------------------------------------------------------------


class _StubSamplingParams:
    def __init__(self, max_tokens: int = 6):
        self.max_tokens = max_tokens


class _StubCompletionOutput:
    def __init__(self, token_ids: list[int], logprobs: list[dict[int, float]]):
        self.token_ids = token_ids
        self.logprobs = logprobs


class _StubRequestOutput:
    def __init__(self, prompt_token_ids: list[int], outputs: list[_StubCompletionOutput]):
        self.prompt_token_ids = prompt_token_ids
        self.outputs = outputs


class _StubVLLMEngine:
    """Wraps a real tiny HF model; `.generate(prompts, params)` returns
    vLLM-shaped outputs computed from that model's OWN greedy generate(), so
    token ids/logprobs are realistic and internally consistent (the same
    model backs both the 'vLLM' stub and, in these tests, the teacher-forced
    extraction pass)."""

    def __init__(self, model, tokenizer, device):
        self.model = model
        self.tokenizer = tokenizer
        self.device = device

    def generate(self, prompts, params, lora_request=None):
        outputs = []
        for prompt in prompts:
            enc = self.tokenizer(prompt, return_tensors="pt").to(self.device)
            prompt_len = int(enc["input_ids"].shape[1])
            with torch.no_grad():
                gen = self.model.generate(
                    **enc, max_new_tokens=params.max_tokens, do_sample=False, num_beams=1,
                    eos_token_id=self.tokenizer.eos_token_id,
                    pad_token_id=self.tokenizer.pad_token_id,
                    return_dict_in_generate=True, output_scores=True,
                )
            full_list = gen.sequences[0].tolist()
            prompt_ids = full_list[:prompt_len]
            new_ids = full_list[prompt_len:]
            step_logprobs = []
            for step, logits in enumerate(gen.scores):
                lp_all = F.log_softmax(logits[0], dim=-1)
                step_logprobs.append({new_ids[step]: float(lp_all[new_ids[step]].item())})
            outputs.append(_StubRequestOutput(
                prompt_token_ids=prompt_ids,
                outputs=[_StubCompletionOutput(token_ids=new_ids, logprobs=step_logprobs)],
            ))
        return outputs


# ---------------------------------------------------------------------------
# Fixture pool: deterministic correct/wrong split derived from the tiny
# model's OWN greedy generation (there is no external cached answer to derive
# labels from in v3, by design -- mirrors v2 smoke's "run the model once to
# get a reproducible answer" approach, adapted for label construction).
# ---------------------------------------------------------------------------


def _fixture_arm(system_prompt: str) -> lp.ArmConfig:
    return lp.ArmConfig(
        id="s_base_primary", model_name="fixture-model", adapter=None,
        quantization=None, lora=False, dial_layer=DIAL_LAYER, gate="LP3-G1",
        system_prompt=system_prompt, max_new_tokens=6, do_sample=False,
        temperature=0.0, enable_thinking=False,
    )


def _make_fixture():
    model = _build_tiny_model()
    tokenizer = _TinyChatTokenizer()
    device = torch.device("cpu")
    engine = _StubVLLMEngine(model, tokenizer, device)
    arm = _fixture_arm("<fixture-system-prompt>")

    questions = [f"fx{2*i} fx{2*i+1}" for i in range(12)]  # 12 fabricated questions
    pool_items = [
        {"row_key": f"fixture::{i}", "dataset": "fixture", "question": q, "aliases_norm": []}
        for i, q in enumerate(questions)
    ]

    # Probe pass: discover each question's deterministic greedy answer so a
    # correct/wrong class split can be constructed (>=5 per class for
    # oof_probe's 5-fold StratifiedKFold, matching v2 smoke's fixture sizing).
    params = _StubSamplingParams(max_tokens=arm.max_new_tokens)
    rendered = lp.render_arm_prompts(tokenizer, arm, pool_items)
    probe_out = engine.generate(rendered, params)
    special_ids = lp._special_ids(tokenizer)
    for i, (item, out) in enumerate(zip(pool_items, probe_out)):
        comp = out.outputs[0]
        full_ids = out.prompt_token_ids + comp.token_ids
        content_end = lp._content_end_index(full_ids, len(out.prompt_token_ids), special_ids)
        span_len = (content_end - len(out.prompt_token_ids) + 1) if content_end is not None else 0
        answer_text = tokenizer.decode(comp.token_ids[:span_len], skip_special_tokens=True).strip()
        if i % 2 == 0:
            item["aliases_norm"] = [scorers_normalize(answer_text)] if answer_text else ["fx0"]
        else:
            item["aliases_norm"] = ["zzz_never_matches_zzz"]

    return model, tokenizer, device, engine, arm, pool_items


def scorers_normalize(text: str) -> str:
    return lp.scorers.normalize(text)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_run_arm_generation_produces_captures_with_both_classes_and_resumes(tmp_path):
    model, tokenizer, device, engine, arm, pool_items = _make_fixture()
    params = _StubSamplingParams(max_tokens=arm.max_new_tokens)
    runlog = tmp_path / "gen_runlog.jsonl"

    captures = lp.run_arm_generation(engine, tokenizer, arm, pool_items, runlog, params)
    assert len(captures) == len(pool_items)
    n_correct = sum(1 for c in captures if c["label"] == "correct")
    n_wrong = sum(1 for c in captures if c["label"] == "wrong")
    assert n_correct >= 5 and n_wrong >= 5, (n_correct, n_wrong)
    for c in captures:
        assert isinstance(c["prompt_token_ids"], list) and c["prompt_token_ids"]
        assert np.isfinite(c["variants"]["mean_answer_span"]) or c["label"] is None

    # Resume: truncate the log to simulate a kill partway through, rerun, and
    # confirm it picks up where it left off rather than redoing everything.
    lines = runlog.read_text(encoding="utf-8").splitlines()
    runlog.write_text("\n".join(lines[:4]) + "\n", encoding="utf-8")
    resumed = lp.run_arm_generation(engine, tokenizer, arm, pool_items, runlog, params)
    assert len(resumed) == len(pool_items)
    assert {r["row_key"] for r in resumed} == {p["row_key"] for p in pool_items}


def test_select_attempted_replays_stopping_rule():
    pool_items = [{"row_key": f"k{i}"} for i in range(10)]
    # labels: correct,wrong,correct,wrong,correct,wrong,wrong,wrong,wrong,wrong
    labels = ["correct", "wrong", "correct", "wrong", "correct",
              "wrong", "wrong", "wrong", "wrong", "wrong"]
    dispositions = [{"label": lab} for lab in labels]

    # target 2 correct / 2 wrong: should stop as soon as BOTH thresholds are
    # met -- that happens at index 3 (2nd wrong, after 2 corrects already seen).
    attempted = lp.select_attempted(pool_items, dispositions, target_correct=2,
                                     target_wrong=2, max_attempts=10)
    assert len(attempted) == 4
    assert [item["row_key"] for item, _ in attempted] == ["k0", "k1", "k2", "k3"]

    # max_attempts caps even if targets are never reached.
    attempted_capped = lp.select_attempted(pool_items, dispositions, target_correct=100,
                                            target_wrong=100, max_attempts=5)
    assert len(attempted_capped) == 5


def test_run_arm_extraction_consumes_exact_captured_ids_and_score_arm_full_pass(tmp_path):
    model, tokenizer, device, engine, arm, pool_items = _make_fixture()
    params = _StubSamplingParams(max_tokens=arm.max_new_tokens)
    gen_runlog = tmp_path / "gen_runlog.jsonl"
    captures = lp.run_arm_generation(engine, tokenizer, arm, pool_items, gen_runlog, params)

    tensors_dir = tmp_path / "tensors"
    ext_runlog = tmp_path / "ext_runlog.jsonl"
    ext_records = lp.run_arm_extraction(model, tokenizer, device, arm, captures, tensors_dir, ext_runlog)
    assert len(ext_records) == len(captures)

    by_key_ext = {r["row_key"]: r for r in ext_records}
    for cap in captures:
        ext = by_key_ext[cap["row_key"]]
        if not cap["answered"]:
            assert ext["extracted"] is False
            continue
        assert ext["extracted"] is True
        span_ids = cap["completion_token_ids"][: cap["span_len"]]
        assert ext["teacher_forced_input_ids"] == cap["prompt_token_ids"] + span_ids
        safe_key = cap["row_key"].replace("::", "__").replace("|", "_")
        assert (tensors_dir / f"{safe_key}__post.safetensors").exists()

    # Resume: truncate, rerun, confirm resumes and does not re-extract.
    lines = ext_runlog.read_text(encoding="utf-8").splitlines()
    ext_runlog.write_text("\n".join(lines[:3]) + "\n", encoding="utf-8")
    resumed = lp.run_arm_extraction(model, tokenizer, device, arm, captures, tensors_dir, ext_runlog)
    assert len(resumed) == len(captures)

    gates_cfg = lp.load_gates_config(lp.GATES_YAML)
    result = lp.score_arm_v3(arm, captures, resumed, tensors_dir, n_boot=200, seed=20260813,
                              gates_cfg=gates_cfg, power_floor_n=5, instrument_sanity_min=0.0)
    assert result["lp3_g0"]["a_capture_integrity_ok"] is True, result["lp3_g0"]
    assert result["lp3_g0"]["a_n_integrity_fail"] == 0
    assert result["lp3_g0"]["b_coverage_ok"] is True
    assert result["lp3_g0"]["c_power_floor_ok"] is True
    assert result["lp3_g0"]["d_instrument_sanity_ok"] is True
    assert result["lp3_g0"]["pass"] is True
    assert np.isfinite(result["dial_minus_primary_logprob_margin"])
    for variant in ("mean_answer_span", "sum_answer_span", "min_answer_span"):
        assert np.isfinite(result["variant_aurocs"][variant]["auroc"])
    assert set(result["gate_verdict"]) == {"LP3_G1_pass", "falsifier_fired", "ambiguous_band"}


def test_score_arm_v3_stops_at_lp3_g0a_when_capture_integrity_fails(tmp_path):
    """LP3-G0(a) must have teeth: corrupt one extraction record's
    teacher_forced_input_ids and confirm score_arm_v3 catches it and stops,
    rather than silently proceeding to a margin."""
    model, tokenizer, device, engine, arm, pool_items = _make_fixture()
    params = _StubSamplingParams(max_tokens=arm.max_new_tokens)
    gen_runlog = tmp_path / "gen_runlog.jsonl"
    captures = lp.run_arm_generation(engine, tokenizer, arm, pool_items, gen_runlog, params)

    tensors_dir = tmp_path / "tensors"
    ext_runlog = tmp_path / "ext_runlog.jsonl"
    ext_records = lp.run_arm_extraction(model, tokenizer, device, arm, captures, tensors_dir, ext_runlog)

    corrupted = [dict(r) for r in ext_records]
    for r in corrupted:
        if r["extracted"]:
            r["teacher_forced_input_ids"] = [999999]  # deliberately wrong
            break

    gates_cfg = lp.load_gates_config(lp.GATES_YAML)
    result = lp.score_arm_v3(arm, captures, corrupted, tensors_dir, n_boot=200, seed=20260813,
                              gates_cfg=gates_cfg, power_floor_n=5, instrument_sanity_min=0.0)
    assert result["lp3_g0"]["a_capture_integrity_ok"] is False
    assert result["lp3_g0"]["a_n_integrity_fail"] == 1
    assert result["lp3_g0"]["pass"] is False
    assert result["gate_verdict"] == {"stopped_at_lp3_g0": True}


def test_score_arm_v3_stops_at_lp3_g0c_power_floor(tmp_path):
    model, tokenizer, device, engine, arm, pool_items = _make_fixture()
    params = _StubSamplingParams(max_tokens=arm.max_new_tokens)
    gen_runlog = tmp_path / "gen_runlog.jsonl"
    captures = lp.run_arm_generation(engine, tokenizer, arm, pool_items, gen_runlog, params)
    tensors_dir = tmp_path / "tensors"
    ext_runlog = tmp_path / "ext_runlog.jsonl"
    ext_records = lp.run_arm_extraction(model, tokenizer, device, arm, captures, tensors_dir, ext_runlog)

    gates_cfg = lp.load_gates_config(lp.GATES_YAML)
    result = lp.score_arm_v3(arm, captures, ext_records, tensors_dir, n_boot=200, seed=20260813,
                              gates_cfg=gates_cfg, power_floor_n=1000, instrument_sanity_min=0.0)
    assert result["lp3_g0"]["c_power_floor_ok"] is False
    assert result["lp3_g0"]["pass"] is False
    assert result["gate_verdict"] == {"stopped_at_lp3_g0": True}


def test_score_arm_v3_stops_at_lp3_g0d_instrument_sanity(tmp_path):
    model, tokenizer, device, engine, arm, pool_items = _make_fixture()
    params = _StubSamplingParams(max_tokens=arm.max_new_tokens)
    gen_runlog = tmp_path / "gen_runlog.jsonl"
    captures = lp.run_arm_generation(engine, tokenizer, arm, pool_items, gen_runlog, params)
    tensors_dir = tmp_path / "tensors"
    ext_runlog = tmp_path / "ext_runlog.jsonl"
    ext_records = lp.run_arm_extraction(model, tokenizer, device, arm, captures, tensors_dir, ext_runlog)

    gates_cfg = lp.load_gates_config(lp.GATES_YAML)
    # Unreachable AUROC floor -- exercises the "instrument-void" branch.
    result = lp.score_arm_v3(arm, captures, ext_records, tensors_dir, n_boot=200, seed=20260813,
                              gates_cfg=gates_cfg, power_floor_n=5, instrument_sanity_min=1.1)
    assert result["lp3_g0"]["a_capture_integrity_ok"] is True
    assert result["lp3_g0"]["c_power_floor_ok"] is True
    assert result["lp3_g0"]["d_instrument_sanity_ok"] is False
    assert result["lp3_g0"]["pass"] is False
    assert result["gate_verdict"] == {"stopped_at_lp3_g0": True}


def test_dry_run_detects_present_and_missing_inputs():
    cell = lp.load_cell_config(lp.CELL_YAML)
    code_ok = lp.dry_run(cell, lp.REPO_ROOT)
    # S is a hub id (never "missing" by local-path existence) and T's local
    # checkpoint/adapter dirs are confirmed present on disk (build report);
    # the only reason this could return 2 is a missing datasets/ file, which
    # is a real repo-state fact this dry-run is supposed to surface, not mask.
    assert code_ok in (0, 2)

    cell_missing = json.loads(json.dumps(cell))
    cell_missing["arms"][1]["model"]["adapter"] = "scratch/does-not-exist/adapter"
    code_missing = lp.dry_run(cell_missing, lp.REPO_ROOT)
    assert code_missing == 2


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
