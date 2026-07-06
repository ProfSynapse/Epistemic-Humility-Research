"""Batched-steering parity tests (TODO item 11 — Amendment AK Stage 2 prep).

CPU-only, tiny synthetic tensors — no model downloads, no GPU. The steering
edit itself lives in confidence_steer.SteeringHook (arm_b_batched.py is
subprocess orchestration that never touches hidden states); these tests cover
the two new batched-engine features and their backward compatibility:

  - FINAL-POSITION steering (position="final"): steers each batch row's TRUE
    last non-pad token, derived from an attention mask under BOTH left and
    right padding, or from explicit per-row final_positions.
  - PER-ELEMENT alpha vectors: alpha as a length-`batch` vector broadcasts so
    row b is shifted by alpha[b] * d; a scalar behaves exactly as before.
  - BACKWARD COMPATIBILITY: scalar-alpha anchor / all_post output is
    bitwise-identical to the pre-change code path on a synthetic case.
  - BATCH-vs-LOOP EQUIVALENCE: the batched final-position + per-row-alpha edit
    equals one-at-a-time application to each row within float tolerance.

Run with an explicit file path (rtk pytest directory-glob false negative):
  pytest experiment/phase1/probe/steering/tests/test_arm_b_batched_parity.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

STEERING_DIR = Path(__file__).resolve().parents[1]
if str(STEERING_DIR) not in sys.path:
    sys.path.insert(0, str(STEERING_DIR))

torch = pytest.importorskip("torch", reason="torch required for steering hook tests")

from confidence_steer import SteeringHook  # noqa: E402


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _unit_direction(hidden_dim: int, seed: int = 0) -> "torch.Tensor":
    d = np.random.default_rng(seed).standard_normal(hidden_dim).astype(np.float32)
    d /= np.linalg.norm(d)
    return torch.from_numpy(d)


def _apply(hook: SteeringHook, hidden: "torch.Tensor") -> "torch.Tensor":
    """Run the hook on a (batch, seq, dim) tuple output, return edited hidden."""
    return hook(None, None, (hidden.clone(),))[0].detach()


def _reference_scalar_edit(hidden, d, alpha, mask):
    """The PRE-CHANGE scalar-alpha edit (verbatim math) for a shared mask."""
    h = hidden.clone()
    h[:, mask, :] = h[:, mask, :] + alpha * d.unsqueeze(0)
    return h


# ---------------------------------------------------------------------------
# Backward compatibility: scalar-alpha shared-position path is UNCHANGED
# ---------------------------------------------------------------------------

class TestScalarBackwardCompat:
    def test_anchor_scalar_bitwise_identical_to_old_path(self):
        batch, seq_len, hd = 3, 7, 16
        d = _unit_direction(hd, seed=1)
        alpha = 2.5
        anchor_idx = 4
        hidden = torch.randn(batch, seq_len, hd)

        hook = SteeringHook(d=d, alpha=alpha, position="anchor",
                            anchor_token_idx=anchor_idx)
        got = _apply(hook, hidden)

        mask = torch.zeros(seq_len, dtype=torch.bool)
        mask[anchor_idx] = True
        want = _reference_scalar_edit(hidden, d, alpha, mask)
        assert torch.equal(got, want)

    def test_all_post_scalar_bitwise_identical_to_old_path(self):
        batch, seq_len, hd = 2, 6, 8
        d = _unit_direction(hd, seed=2)
        alpha = -1.3
        start = 2
        hidden = torch.randn(batch, seq_len, hd)

        hook = SteeringHook(d=d, alpha=alpha, position="all_post",
                            anchor_start=start)
        got = _apply(hook, hidden)

        mask = torch.zeros(seq_len, dtype=torch.bool)
        mask[start:] = True
        want = _reference_scalar_edit(hidden, d, alpha, mask)
        assert torch.equal(got, want)

    def test_anchor_none_idx_steers_last_position(self):
        batch, seq_len, hd = 2, 5, 8
        d = _unit_direction(hd, seed=3)
        hidden = torch.zeros(batch, seq_len, hd)
        hook = SteeringHook(d=d, alpha=1.0, position="anchor",
                            anchor_token_idx=None)
        got = _apply(hook, hidden)
        # last position shifted by d on every row, others untouched
        assert torch.allclose(got[:, -1, :], d.unsqueeze(0).expand(batch, hd),
                              atol=1e-6)
        assert got[:, :-1, :].abs().max().item() == 0.0


# ---------------------------------------------------------------------------
# Per-element alpha vectors (shared-position modes)
# ---------------------------------------------------------------------------

class TestPerElementAlpha:
    def test_vector_alpha_scales_each_row(self):
        batch, seq_len, hd = 3, 4, 8
        d = torch.zeros(hd)
        d[0] = 1.0  # unit along dim 0 -> shift reads off channel 0
        alphas = [0.5, -2.0, 3.0]
        hidden = torch.zeros(batch, seq_len, hd)

        hook = SteeringHook(d=d, alpha=alphas, position="anchor",
                            anchor_token_idx=seq_len - 1)
        got = _apply(hook, hidden)
        for b, a in enumerate(alphas):
            assert got[b, -1, 0].item() == pytest.approx(a)
            assert got[b, :-1, :].abs().max().item() == 0.0

    def test_scalar_and_length1_vector_agree(self):
        batch, seq_len, hd = 2, 5, 8
        d = _unit_direction(hd, seed=4)
        hidden = torch.randn(batch, seq_len, hd)

        h_scalar = SteeringHook(d=d, alpha=1.7, position="all_post",
                                anchor_start=0)
        h_vec1 = SteeringHook(d=d, alpha=[1.7], position="all_post",
                              anchor_start=0)
        assert torch.allclose(_apply(h_scalar, hidden), _apply(h_vec1, hidden),
                              atol=1e-6)

    def test_wrong_length_alpha_raises(self):
        batch, seq_len, hd = 3, 4, 8
        d = _unit_direction(hd, seed=5)
        hidden = torch.zeros(batch, seq_len, hd)
        hook = SteeringHook(d=d, alpha=[1.0, 2.0], position="anchor")  # len 2 != 3
        with pytest.raises(ValueError, match="alpha vector"):
            _apply(hook, hidden)

    def test_numpy_and_tensor_alpha_accepted(self):
        batch, seq_len, hd = 2, 3, 8
        d = torch.zeros(hd)
        d[0] = 1.0
        hidden = torch.zeros(batch, seq_len, hd)
        for alpha in (np.array([1.0, 2.0], dtype=np.float32),
                      torch.tensor([1.0, 2.0])):
            hook = SteeringHook(d=d, alpha=alpha, position="anchor",
                                anchor_token_idx=seq_len - 1)
            got = _apply(hook, hidden)
            assert got[0, -1, 0].item() == pytest.approx(1.0)
            assert got[1, -1, 0].item() == pytest.approx(2.0)


# ---------------------------------------------------------------------------
# Final-position steering: per-row last non-pad token
# ---------------------------------------------------------------------------

class TestFinalPositionExplicit:
    def test_explicit_final_positions_per_row(self):
        batch, seq_len, hd = 3, 6, 8
        d = torch.zeros(hd)
        d[0] = 1.0
        final_pos = [2, 5, 0]
        hidden = torch.zeros(batch, seq_len, hd)

        hook = SteeringHook(d=d, alpha=1.0, position="final",
                            final_positions=final_pos)
        got = _apply(hook, hidden)
        for b, p in enumerate(final_pos):
            assert got[b, p, 0].item() == pytest.approx(1.0)
            others = [c for c in range(seq_len) if c != p]
            assert got[b, others, :].abs().max().item() == 0.0

    def test_final_with_per_row_alpha(self):
        batch, seq_len, hd = 2, 4, 8
        d = torch.zeros(hd)
        d[0] = 1.0
        hook = SteeringHook(d=d, alpha=[2.0, -3.0], position="final",
                            final_positions=[1, 3])
        got = _apply(hook, torch.zeros(batch, seq_len, hd))
        assert got[0, 1, 0].item() == pytest.approx(2.0)
        assert got[1, 3, 0].item() == pytest.approx(-3.0)

    def test_zero_alpha_row_not_steered(self):
        batch, seq_len, hd = 2, 4, 8
        d = torch.zeros(hd)
        d[0] = 1.0
        hook = SteeringHook(d=d, alpha=[0.0, 5.0], position="final",
                            final_positions=[1, 2])
        got = _apply(hook, torch.zeros(batch, seq_len, hd))
        assert got[0].abs().max().item() == 0.0  # alpha 0 -> untouched
        assert got[1, 2, 0].item() == pytest.approx(5.0)

    def test_wrong_length_final_positions_raises(self):
        d = torch.zeros(8)
        d[0] = 1.0
        hook = SteeringHook(d=d, alpha=1.0, position="final",
                            final_positions=[0, 1, 2])  # len 3
        with pytest.raises(ValueError, match="final_positions has length"):
            _apply(hook, torch.zeros(2, 4, 8))

    def test_no_padding_info_falls_back_to_last(self):
        batch, seq_len, hd = 2, 5, 8
        d = torch.zeros(hd)
        d[0] = 1.0
        hook = SteeringHook(d=d, alpha=1.0, position="final")  # no mask, no pos
        got = _apply(hook, torch.zeros(batch, seq_len, hd))
        assert torch.allclose(got[:, -1, 0],
                              torch.ones(batch), atol=1e-6)
        assert got[:, :-1, :].abs().max().item() == 0.0


class TestFinalPositionFromAttentionMask:
    def test_right_padding_last_real_token(self):
        # right padding: real tokens first, pads (mask 0) trailing
        # row 0: 4 real tokens (indices 0..3), row 1: 2 real tokens (0..1)
        batch, seq_len, hd = 2, 6, 8
        d = torch.zeros(hd)
        d[0] = 1.0
        attn = torch.tensor([[1, 1, 1, 1, 0, 0],
                             [1, 1, 0, 0, 0, 0]])
        hook = SteeringHook(d=d, alpha=1.0, position="final",
                            attention_mask=attn)
        got = _apply(hook, torch.zeros(batch, seq_len, hd))
        # last real token: row 0 -> index 3, row 1 -> index 1
        assert got[0, 3, 0].item() == pytest.approx(1.0)
        assert got[1, 1, 0].item() == pytest.approx(1.0)
        # nothing else steered (pads included)
        assert got[0, [0, 1, 2, 4, 5], :].abs().max().item() == 0.0
        assert got[1, [0, 2, 3, 4, 5], :].abs().max().item() == 0.0

    def test_left_padding_last_real_token(self):
        # left padding: pads (mask 0) leading, real tokens trailing -> last real
        # token is always the final index seq_len-1 for every row
        batch, seq_len, hd = 2, 6, 8
        d = torch.zeros(hd)
        d[0] = 1.0
        attn = torch.tensor([[0, 0, 1, 1, 1, 1],
                             [0, 0, 0, 0, 1, 1]])
        hook = SteeringHook(d=d, alpha=1.0, position="final",
                            attention_mask=attn)
        got = _apply(hook, torch.zeros(batch, seq_len, hd))
        assert got[0, seq_len - 1, 0].item() == pytest.approx(1.0)
        assert got[1, seq_len - 1, 0].item() == pytest.approx(1.0)
        assert got[:, :-1, :].abs().max().item() == 0.0

    def test_mixed_interior_pad_takes_last_ones(self):
        # defensive: mask with an interior gap; "final" is the last 1, not the
        # last contiguous run
        batch, seq_len, hd = 1, 6, 8
        d = torch.zeros(hd)
        d[0] = 1.0
        attn = torch.tensor([[1, 1, 0, 1, 0, 0]])  # last real token at index 3
        hook = SteeringHook(d=d, alpha=1.0, position="final",
                            attention_mask=attn)
        got = _apply(hook, torch.zeros(batch, seq_len, hd))
        assert got[0, 3, 0].item() == pytest.approx(1.0)
        assert got[0, [0, 1, 2, 4, 5], :].abs().max().item() == 0.0

    def test_explicit_positions_win_over_attention_mask(self):
        batch, seq_len, hd = 1, 5, 8
        d = torch.zeros(hd)
        d[0] = 1.0
        attn = torch.tensor([[1, 1, 1, 0, 0]])  # mask says index 2
        hook = SteeringHook(d=d, alpha=1.0, position="final",
                            final_positions=[0], attention_mask=attn)
        got = _apply(hook, torch.zeros(batch, seq_len, hd))
        assert got[0, 0, 0].item() == pytest.approx(1.0)  # explicit wins
        assert got[0, 2, 0].item() == 0.0

    def test_mask_batch_mismatch_raises(self):
        d = torch.zeros(8)
        d[0] = 1.0
        attn = torch.tensor([[1, 1, 0]])  # batch 1
        hook = SteeringHook(d=d, alpha=1.0, position="final",
                            attention_mask=attn)
        with pytest.raises(ValueError, match="attention_mask batch"):
            _apply(hook, torch.zeros(2, 3, 8))  # hidden batch 2


# ---------------------------------------------------------------------------
# Batch-vs-loop equivalence: the batched engine edit == one-at-a-time
# ---------------------------------------------------------------------------

class TestBatchVsLoopEquivalence:
    def test_final_position_per_row_alpha_matches_loop(self):
        batch, seq_len, hd = 5, 9, 32
        d = _unit_direction(hd, seed=7)
        rng = np.random.default_rng(11)
        # random right/left padding lengths per row
        attn = torch.ones(batch, seq_len, dtype=torch.long)
        for b in range(batch):
            n_pad = int(rng.integers(0, 4))
            if n_pad:
                if b % 2 == 0:  # right pad
                    attn[b, seq_len - n_pad:] = 0
                else:           # left pad
                    attn[b, :n_pad] = 0
        alphas = torch.tensor(rng.standard_normal(batch), dtype=torch.float32)
        hidden = torch.randn(batch, seq_len, hd)

        # Batched edit
        batched_hook = SteeringHook(d=d, alpha=alphas, position="final",
                                    attention_mask=attn)
        batched = _apply(batched_hook, hidden)

        # One-at-a-time reference: each row alone, its own mask + scalar alpha
        loop = hidden.clone()
        for b in range(batch):
            row_hook = SteeringHook(
                d=d, alpha=float(alphas[b]), position="final",
                attention_mask=attn[b:b + 1])
            edited = _apply(row_hook, hidden[b:b + 1])
            loop[b] = edited[0]

        assert torch.allclose(batched, loop, atol=1e-6), \
            (batched - loop).abs().max().item()

    def test_anchor_vector_alpha_matches_loop(self):
        batch, seq_len, hd = 4, 6, 16
        d = _unit_direction(hd, seed=8)
        rng = np.random.default_rng(3)
        alphas = torch.tensor(rng.standard_normal(batch), dtype=torch.float32)
        anchor_idx = 2
        hidden = torch.randn(batch, seq_len, hd)

        batched = _apply(SteeringHook(d=d, alpha=alphas, position="anchor",
                                      anchor_token_idx=anchor_idx), hidden)
        loop = hidden.clone()
        for b in range(batch):
            edited = _apply(SteeringHook(d=d, alpha=float(alphas[b]),
                                         position="anchor",
                                         anchor_token_idx=anchor_idx),
                            hidden[b:b + 1])
            loop[b] = edited[0]
        assert torch.allclose(batched, loop, atol=1e-6)


# ---------------------------------------------------------------------------
# Regression: the GPU equivalence CELL's comparison methodology
#
# TODO item 11 r1 mis-fired: the cell compared ABSOLUTE steered hidden states
# between a padded batched forward and unpadded single forwards. In bf16 at a
# deep layer of a real model those two forwards legitimately differ by
# integer-scale amounts (batched-vs-unbatched numeric noise, worse under left
# padding), which the r1 cell reported as 1-6 units of "divergence" (FAIL)
# although the SteeringHook was correct. The fix compares the STEERING DELTA
# (steered - unsteered), which cancels that shared model noise.
#
# These tests run a TINY real Qwen3 model in bf16 (no download of the real
# checkpoint, no GPU) so they exercise the same failure condition the r1 GPU run
# hit, and prove: (1) the old absolute comparison IS noisy under bf16 left
# padding, and (2) the new delta comparison is tight and padding-independent.
# ---------------------------------------------------------------------------

def _tiny_qwen3_bf16():
    """A small real Qwen3ForCausalLM in bf16 + the Qwen3 tokenizer.

    Weights are randomly initialized (no download of any large checkpoint); the
    tokenizer is the tiny Qwen3-0.6B tokenizer. Deep enough (12 layers) and wide
    enough that bf16 residual magnitudes reproduce the batched-vs-unbatched noise
    the real 4B run hit.
    """
    from transformers import (Qwen3Config, Qwen3ForCausalLM,  # noqa: PLC0415
                              AutoTokenizer)
    torch.manual_seed(0)
    cfg = Qwen3Config(
        vocab_size=151936, hidden_size=512, intermediate_size=1024,
        num_hidden_layers=12, num_attention_heads=8, num_key_value_heads=2,
        head_dim=64, max_position_embeddings=4096, attn_implementation="sdpa")
    model = Qwen3ForCausalLM(cfg).eval().to(torch.bfloat16)
    tok = AutoTokenizer.from_pretrained("Qwen/Qwen3-0.6B")
    if tok.pad_token_id is None:
        tok.pad_token = tok.eos_token
    return model, tok


def _cell_equiv(model, tok, layer_idx, d, prompts, alphas, padding_side, delta):
    """Reproduce the cell's capture logic; return (max_vs_analytic, max_bvu).

    delta=True  -> compare steering delta (steered - unsteered), the FIX.
    delta=False -> compare absolute steered states, the r1 bug (batched steered
                   vs unbatched steered at the final token).
    """
    from confidence_steer import get_decoder_layer  # noqa: PLC0415
    tok.padding_side = padding_side
    layer = get_decoder_layer(model, layer_idx)

    def last_idx(am):
        am = am.to(torch.bool)
        seq = am.shape[1]
        return (seq - 1) - torch.argmax(torch.flip(am.to(torch.int64),
                                                    dims=[1]), dim=1)

    class _Cap:
        def __init__(self):
            self.h = None

        def __call__(self, m, i, o):
            self.h = (o[0] if isinstance(o, tuple) else o).detach().float()
            return o

    def cap_final(enc, steer_hook):
        fi = last_idx(enc["attention_mask"])
        c = _Cap()
        handles = []
        if steer_hook is not None:
            handles.append(layer.register_forward_hook(steer_hook))
        handles.append(layer.register_forward_hook(c))
        with torch.no_grad():
            model(**enc)
        for h in handles:
            h.remove()
        return torch.stack([c.h[b, fi[b].item(), :]
                            for b in range(enc["attention_mask"].shape[0])])

    encB = tok(prompts, return_tensors="pt", padding=True)
    steer = SteeringHook(d=d, alpha=alphas, position="final",
                         attention_mask=encB["attention_mask"])
    bat_steered = cap_final(encB, steer)

    unb_steered = []
    unb_base = []
    bat_base = cap_final(encB, None) if delta else None
    for i, p in enumerate(prompts):
        e1 = tok(p, return_tensors="pt")
        s1 = SteeringHook(d=d, alpha=float(alphas[i]), position="final",
                          attention_mask=e1["attention_mask"])
        unb_steered.append(cap_final(e1, s1)[0])
        if delta:
            unb_base.append(cap_final(e1, None)[0])
    unb_steered = torch.stack(unb_steered)

    d_cpu = d.detach().float().cpu()
    expected = torch.stack([float(alphas[i]) * d_cpu
                            for i in range(len(prompts))])
    if delta:
        bat = bat_steered - bat_base
        unb = unb_steered - torch.stack(unb_base)
    else:
        bat = bat_steered
        unb = unb_steered
        expected = None  # absolute states have no clean analytic target
    max_bvu = float((bat - unb).abs().max())
    max_vs_analytic = (float((bat - expected).abs().max())
                       if expected is not None else float("nan"))
    return max_vs_analytic, max_bvu


class TestGpuEquivalenceCellMethodology:
    """Tiny real Qwen3 bf16 forward; no download, no GPU, no real checkpoint."""

    PROMPTS = [
        "The capital of France is",
        "Pride and Prejudice was written by a famous English author named",
        "A random stock price next Tuesday will probably be about",
        "Gold",
        "Mars has this many moons and a little extra text:",
    ]
    ALPHAS = [4.0 * (1.0 + 0.25 * i) for i in range(5)]
    FLOOR = 1e-2

    def _setup(self):
        pytest.importorskip("transformers",
                            reason="transformers required for tiny-model test")
        model, tok = _tiny_qwen3_bf16()
        d = _unit_direction(model.config.hidden_size, seed=13)
        return model, tok, d

    def test_delta_comparison_tight_both_padding_sides(self):
        """The FIX: delta comparison is under floor for right AND left padding."""
        model, tok, d = self._setup()
        for side in ("right", "left"):
            va, bvu = _cell_equiv(model, tok, 10, d, self.PROMPTS, self.ALPHAS,
                                  side, delta=True)
            assert va < self.FLOOR, (side, "vs-analytic", va)
            assert bvu < self.FLOOR, (side, "batched-vs-unbatched", bvu)

    def test_absolute_comparison_is_noisy_under_bf16_left_padding(self):
        """The r1 BUG: absolute steered-state comparison is NOT floor-tight.

        This documents WHY the delta fix is needed: the same tiny model, same
        hook, but comparing absolute states inflates the reported divergence
        well past the delta result under bf16 left padding.
        """
        model, tok, d = self._setup()
        _, abs_bvu = _cell_equiv(model, tok, 10, d, self.PROMPTS, self.ALPHAS,
                                 "left", delta=False)
        _, delta_bvu = _cell_equiv(model, tok, 10, d, self.PROMPTS, self.ALPHAS,
                                   "left", delta=True)
        # Absolute comparison carries the model's bf16 batched-vs-unbatched noise
        # that the delta comparison cancels; it is strictly larger.
        assert abs_bvu > delta_bvu, (abs_bvu, delta_bvu)


def _run_without_pytest() -> int:
    """Plain runner (pytest is not installed in local envs): python -m ...

    Runs the two methodology regression tests and the batch-vs-loop check and
    prints PASS/FAIL. Returns a nonzero exit code on any failure.
    """
    import traceback
    failures = 0
    t = TestGpuEquivalenceCellMethodology()
    checks = [
        ("delta_comparison_tight_both_padding_sides",
         t.test_delta_comparison_tight_both_padding_sides),
        ("absolute_comparison_is_noisy_under_bf16_left_padding",
         t.test_absolute_comparison_is_noisy_under_bf16_left_padding),
        ("final_position_per_row_alpha_matches_loop",
         TestBatchVsLoopEquivalence().test_final_position_per_row_alpha_matches_loop),
    ]
    for name, fn in checks:
        try:
            fn()
            print(f"PASS {name}")
        except Exception:  # noqa: BLE001
            failures += 1
            print(f"FAIL {name}")
            traceback.print_exc()
    print(f"\n{len(checks) - failures}/{len(checks)} passed")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(_run_without_pytest())
