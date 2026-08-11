#!/usr/bin/env python3
"""Fixture-backed smoke for lp_v2_harness.py -- drives the REAL entry points
(`run_arm`, `score_arm`, `regenerate_and_capture_row`, `dry_run`) end to end
with a tiny CPU model and synthesized fixture data. No real model download, no
GPU, and no row-level content: every question/answer string here is
fabricated (`fx0`, `fx1`, ...), never real question or answer text, per the
public-repo containment rule (AMENDMENT.md "Containment").

Per the pre-sign verification rule (.skills/experiments/SKILL.md "Before
signing ANY cell..."): this smoke calls the SAME functions `main()` calls for
a real run (`run_arm`, `score_arm`), not a reimplementation of their logic, so
it cannot pass while the real orchestration is a stub. `load_model_and_tokenizer`
(the only function that talks to real weights/GPU) is the sole thing swapped
out, by injecting a tiny model/tokenizer directly into `run_arm` -- the
established pattern in this repo's other GPU-cell smokes (see
experiments/rr-cross-family-raw-refusal/test_rr_smoke.py `_build_tiny_model`).

Run: python3 -m pytest experiments/dial-logprob-baseline-v2/test_lp_v2_smoke.py -v
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pytest
import torch
from safetensors.numpy import save_file
from transformers import AutoModelForCausalLM, GPT2Config

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import lp_v2_harness as lp  # noqa: E402

DIAL_LAYER = 7
HIDDEN_DIM = 8


# ---------------------------------------------------------------------------
# Tiny model + tokenizer (no download, no GPU, no real vocabulary -- mirrors
# the _build_tiny_model / _TinyTokenizer pattern already used elsewhere in
# this repo's GPU-cell smokes)
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
    """Minimal tokenizer stand-in: closed fake vocabulary, deterministic
    word-level tokenization, and a fake but valid apply_chat_template (no
    <think> markers, so backends.assert_no_think_scaffolding passes trivially
    -- exercising the REAL render_probe_prompt discovery/self-check path, not
    bypassing it)."""

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
    config = GPT2Config(n_layer=2, n_embd=32, n_head=2, vocab_size=len(VOCAB), n_positions=64)
    model = AutoModelForCausalLM.from_config(config)
    model.eval()
    return model


# ---------------------------------------------------------------------------
# Fixture rows + fixture hidden-state tensors
# ---------------------------------------------------------------------------


def _make_fixture(tmp_path: Path):
    """Builds: (arm_config, rows, tensors_dir). All question/answer text is
    fabricated (fx-tokens). Runs the tiny model's OWN greedy generate() once
    per question to obtain a reproducible 'cached' answer_text, so a correctly
    functioning round-trip check passes on unmodified rows by construction."""
    model = _build_tiny_model()
    tokenizer = _TinyChatTokenizer()
    device = torch.device("cpu")

    system_prompt = "<fixture-system-prompt>"
    # oof_probe hardcodes 5-fold StratifiedKFold, so each class needs >=5
    # members; 12 rows (6 correct / 6 wrong) is the smallest fixture that clears it.
    questions = [f"fx{2*i} fx{2*i+1}" for i in range(12)]  # 12 fabricated questions
    labels = ["correct", "wrong"] * 6  # 6 correct / 6 wrong

    # rows.jsonl lives alongside the safetensors shards, matching the real
    # S/T stage2/ layout (load_position_layers reads `ext_dir / "rows.jsonl"`).
    tensors_dir = tmp_path / "tensors"
    tensors_dir.mkdir()
    rows = []
    rng = np.random.default_rng(20260811)

    eos_for_gen, special_ids = lp._eos_and_special_ids(tokenizer)

    for i, (q, label) in enumerate(zip(questions, labels)):
        rendered, _mode = lp.render_probe_prompt(
            tokenizer, system_prompt, q, enable_thinking=False
        )
        enc = tokenizer(rendered, return_tensors="pt").to(device)
        prompt_len = int(enc["input_ids"].shape[1])
        with torch.no_grad():
            gen = model.generate(
                **enc, max_new_tokens=6, do_sample=False, num_beams=1,
                eos_token_id=eos_for_gen, pad_token_id=tokenizer.pad_token_id,
                return_dict_in_generate=True, output_scores=True,
            )
        full_list = gen.sequences[0].tolist()
        new_ids = full_list[prompt_len:]
        answer_text = tokenizer.decode(new_ids, skip_special_tokens=True).strip()
        content_end = lp._content_end_index(full_list, prompt_len, special_ids)
        answer_tok_len = (content_end - prompt_len + 1) if content_end is not None else 0

        row_key = f"fixture::{i}"
        rows.append({
            "row_key": row_key,
            "dataset": "fixture",
            "question": q,
            "answer_text": answer_text,
            "aliases_norm": ["fx-alias"],
            "answered": True,
            "refused": False,
            "correct": (label == "correct"),
            "label": label,
            "prompt_len": prompt_len,
            "answer_tok_len": answer_tok_len,
        })

        # Fabricated hidden-state vector: correct/wrong classes separated by a
        # mean offset so oof_probe has real (not degenerate) signal to fit.
        offset = 1.0 if label == "correct" else -1.0
        vec = rng.normal(loc=offset, scale=0.4, size=HIDDEN_DIM).astype(np.float32)
        safe_key = row_key.replace("::", "__").replace("|", "_")
        save_file({f"L{DIAL_LAYER}": vec}, str(tensors_dir / f"{safe_key}__post.safetensors"))

    rows_path = tensors_dir / "rows.jsonl"
    with rows_path.open("w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r) + "\n")

    # Signed AUROC target: computed once from this exact fixture (same seed,
    # same data) so LP-G0's dial-reproduction sub-criterion is exercised for
    # real (score_arm recomputes it independently and must match).
    X, y, keys = lp.load_position_layers(tensors_dir, "post")
    p = lp.oof_probe(X[DIAL_LAYER], y, seed=20260719)
    from sklearn.metrics import roc_auc_score
    signed_auroc = float(roc_auc_score(y, p))

    arm = lp.ArmConfig(
        id="s_base_primary", model_name="fixture-model", adapter=None,
        rows_path=rows_path, tensors_dir=tensors_dir,
        dial_layer=DIAL_LAYER, dial_signed_auroc=signed_auroc,
        n_rows_expected=len(rows), gate="LP-G1", system_prompt=system_prompt,
        max_new_tokens=6, do_sample=False, num_beams=1, batch_size=1,
    )
    return model, tokenizer, device, arm, rows


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_regenerate_and_capture_row_roundtrip_passes_on_unmodified_row(tmp_path):
    model, tokenizer, device, arm, rows = _make_fixture(tmp_path)
    eos_for_gen, special_ids = lp._eos_and_special_ids(tokenizer)
    result = lp.regenerate_and_capture_row(
        model, tokenizer, device, rows[0], arm, eos_for_gen, special_ids
    )
    assert result["roundtrip_ok"] is True, result
    assert result["row_key"] == rows[0]["row_key"]
    assert np.isfinite(result["variants"]["mean_answer_span"])
    assert np.isfinite(result["variants"]["sum_answer_span"])
    assert np.isfinite(result["variants"]["min_answer_span"])


def test_regenerate_and_capture_row_roundtrip_fails_on_corrupted_cache(tmp_path):
    """LP-G0's round-trip check must have teeth: deliberately corrupt the
    cached answer_text and confirm the check actually catches it, not just
    happy-path."""
    model, tokenizer, device, arm, rows = _make_fixture(tmp_path)
    eos_for_gen, special_ids = lp._eos_and_special_ids(tokenizer)
    corrupted = dict(rows[0])
    corrupted["answer_text"] = corrupted["answer_text"] + " fx99"
    result = lp.regenerate_and_capture_row(
        model, tokenizer, device, corrupted, arm, eos_for_gen, special_ids
    )
    assert result["roundtrip_ok"] is False, result


def test_run_arm_persists_incrementally_and_resumes(tmp_path):
    model, tokenizer, device, arm, rows = _make_fixture(tmp_path)
    runlog = tmp_path / "runlog" / "s_base_primary.jsonl"

    results = lp.run_arm(model, tokenizer, device, arm, rows, runlog)
    assert len(results) == len(rows)
    assert runlog.exists()
    with runlog.open() as fh:
        n_lines = sum(1 for _ in fh)
    assert n_lines == len(rows)
    assert all(r["roundtrip_ok"] for r in results)

    # Resume: truncate the log to simulate a kill after 3 rows, rerun, and
    # confirm it picks up where it left off rather than redoing everything.
    lines = runlog.read_text(encoding="utf-8").splitlines()
    runlog.write_text("\n".join(lines[:3]) + "\n", encoding="utf-8")
    resumed = lp.run_arm(model, tokenizer, device, arm, rows, runlog)
    assert len(resumed) == len(rows)
    assert {r["row_key"] for r in resumed} == {r["row_key"] for r in rows}


def test_score_arm_computes_finite_metrics_and_reproduces_signed_dial_auroc(tmp_path):
    model, tokenizer, device, arm, rows = _make_fixture(tmp_path)
    runlog = tmp_path / "runlog" / "s_base_primary.jsonl"
    per_row = lp.run_arm(model, tokenizer, device, arm, rows, runlog)

    gates_cfg = lp.load_gates_config(lp.GATES_YAML)
    result = lp.score_arm(arm, per_row, n_boot=200, seed=20260719, gates_cfg=gates_cfg)

    assert result["lp_g0"]["dial_repro_ok"] is True, result["lp_g0"]
    assert result["lp_g0"]["row_count_ok"] is True, result["lp_g0"]
    assert result["lp_g0"]["n_roundtrip_fail"] == 0, result["lp_g0"]
    assert result["lp_g0"]["pass"] is True, result["lp_g0"]
    assert np.isfinite(result["dial_minus_primary_logprob_margin"])
    for variant in ("mean_answer_span", "sum_answer_span", "min_answer_span"):
        assert np.isfinite(result["variant_aurocs"][variant]["auroc"])
        assert result["variant_aurocs"][variant]["n"] == len(rows)
    # LP-G0 passed, so a real (non-stopped) gate verdict must be present.
    assert "stopped_at_lp_g0" not in result["gate_verdict"]
    assert set(result["gate_verdict"]) == {"LP_G1_pass", "falsifier_fired", "ambiguous_band"}


def test_score_arm_stops_at_lp_g0_when_roundtrip_fails(tmp_path):
    """LP-G0 must gate the LP-G1 verdict: if even one row fails the
    round-trip, the harness must report a stop, not a pass/fail gate call --
    mirroring v1's own "any mismatch is a data-stage stop, not a result"."""
    model, tokenizer, device, arm, rows = _make_fixture(tmp_path)
    eos_for_gen, special_ids = lp._eos_and_special_ids(tokenizer)
    per_row = [
        lp.regenerate_and_capture_row(model, tokenizer, device, r, arm, eos_for_gen, special_ids)
        for r in rows
    ]
    per_row[0]["roundtrip_ok"] = False  # simulate one failed row

    gates_cfg = lp.load_gates_config(lp.GATES_YAML)
    result = lp.score_arm(arm, per_row, n_boot=200, seed=20260719, gates_cfg=gates_cfg)
    assert result["lp_g0"]["pass"] is False
    assert result["gate_verdict"] == {"stopped_at_lp_g0": True}


def test_dry_run_detects_present_and_missing_inputs(tmp_path):
    model, tokenizer, device, arm, rows = _make_fixture(tmp_path)
    tensors_dir_t = tmp_path / "tensors_t"
    tensors_dir_t.mkdir()

    cell_ok = {
        "arms": [
            {"id": "s_base_primary",
             "model": {"name": "fixture-hub-id", "adapter": None},
             "rows": str(arm.rows_path.relative_to(lp.REPO_ROOT)) if _is_under(arm.rows_path, lp.REPO_ROOT) else str(arm.rows_path),
             "tensors_dir": str(arm.tensors_dir.relative_to(lp.REPO_ROOT)) if _is_under(arm.tensors_dir, lp.REPO_ROOT) else str(arm.tensors_dir)},
        ]
    }
    # Use absolute paths directly (outside repo_root) by passing repo_root=tmp_path
    # so _resolve_ref / dry_run treat tmp_path as the base for relative lookups.
    cell_ok["arms"][0]["rows"] = str(arm.rows_path)
    cell_ok["arms"][0]["tensors_dir"] = str(arm.tensors_dir)
    code_ok = lp.dry_run(cell_ok, repo_root=Path("/"))
    assert code_ok == 0

    cell_missing = json.loads(json.dumps(cell_ok))
    cell_missing["arms"][0]["rows"] = str(tmp_path / "does-not-exist.jsonl")
    code_missing = lp.dry_run(cell_missing, repo_root=Path("/"))
    assert code_missing == 2


def _is_under(path: Path, base: Path) -> bool:
    try:
        path.relative_to(base)
        return True
    except ValueError:
        return False


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
