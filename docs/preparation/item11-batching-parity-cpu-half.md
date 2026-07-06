# TODO item 11 — Batched steering engine parity (CPU half)

Prep for **Amendment AK Stage 2**. Implements and CPU-tests the two batched-engine
features the next steering amendment needs, and parks (does NOT run) the GPU
equivalence cell.

## Where the steering edit actually lives

`arm_b_batched.py` is **subprocess orchestration only** — it renders prompts and
drives the public synaptic-tuner CLI (`batch-generate` / `batch-capture`); it
never touches hidden states. The hidden-state edit is
`confidence_steer.SteeringHook.__call__`, gated at generate-time by
`steering_common.GenerationHookController`. The two requested features therefore
belong in `SteeringHook` (its module), which is where they were implemented.

## Features implemented (confidence_steer.py `SteeringHook`)

### 1. Final-position steering (`position="final"`)
Steers **each batch row's true last non-pad token**, not a shared column.
- Per-row indices come from `self.final_positions` (length `batch`) if set,
  else derived from `self.attention_mask` `(batch, seq_len)`, else fall back to
  the last position of every row.
- Attention-mask derivation is **left- and right-padding correct**: it flips the
  mask and argmaxes to find the last `1` per row (handles interior gaps too;
  clamps a fully-padded row to the last index defensively).
- Set `final_positions` / `attention_mask` externally between generate calls,
  exactly like the existing `anchor_token_idx` / `anchor_start` pattern.

### 2. Per-element alpha vectors
`alpha` now accepts a length-`batch` vector (list / numpy / torch) **in addition
to** a scalar. Row `b` is shifted by `alpha[b] * d`; a length-1 vector or a
scalar behaves identically. Works in all three position modes. Lets a caller
pass `compute_proportional_alpha`'s per-row effective alphas in one forward.

### Backward compatibility
- Scalar-alpha `anchor` / `all_post` output is **bitwise-identical** to the
  pre-change path (verified against a verbatim copy of the old edit math).
- `position` validation now accepts `"final"` as a third value; the constructor
  signature adds keyword-only-by-convention args with `None`/`1.0` defaults, so
  every existing call site is unaffected.

## Tests (CPU-only, no model download)

New file: `tests/test_arm_b_batched_parity.py`
- scalar backward-compat (bitwise) for anchor + all_post; anchor-None -> last.
- per-element alpha: per-row scaling, scalar/len-1 agreement, numpy+tensor
  accepted, wrong-length raises.
- final-position: explicit positions, per-row alpha, zero-alpha row skipped,
  wrong-length raises, no-padding fallback.
- final from attention mask: right padding, left padding, interior gap,
  explicit-positions-win-over-mask, batch-mismatch raises.
- **batch-vs-loop equivalence**: batched final-position + per-row alpha under
  mixed random left/right padding == one-at-a-time application (atol 1e-6);
  same for anchor + vector alpha.

Result: **91 passed** for the parity + `test_confidence_steer` +
`test_steering_common` set; existing `test_arm_b_batched.py` still
**35 passed, 2 skipped** (the 2 skips are the CUDA-gated e2e, correctly skipped
on CPU).

## GPU equivalence cell (methodology fixed after r1; engine parity intact)

`gpu_equivalence_cell.py` — loud DO-NOT-RUN docstring + a required
`--i-know-this-runs-on-gpu` flag (refuses to run without it). On a handful of
real prompts it verifies the batched final-position + per-row-alpha edit at the
direction's `best_layer`. Launch only under a signed amendment + explicit user
approval, and only when the GPU is free.

### r1 mis-fire and the fix (cell methodology, NOT the engine)

The first GPU launch (r1, Modal A10G, real clean-SFT + grpo-v2 lineage) reported
per-row divergences `[2, 6, 4, 1, 2]` and overall `6.0` vs the `1e-2` floor —
FAIL. Diagnosis (CPU-reproduced on a tiny bf16 Qwen3 model, no GPU, no real
checkpoint): the cell had compared **absolute steered hidden states** between a
padded batched forward and unpadded single forwards. Those two forwards are NOT
bit-identical in bf16 even with correct masking (attention softmax over a longer
padded key set, RoPE offsets, float reduction order), and at layer 34 of a 4B
model the residual magnitude is large, so this legitimate batched-vs-unbatched
numeric noise is integer-scale in bf16. The `SteeringHook` was applying the
correct per-row alpha at the correct token the whole time — the max component of
the unit-norm `direction_caution` is only `0.18`, so no per-row-alpha
misassignment (max swap `4*0.18 = 0.72`) could produce a `6.0` divergence; the
`6.0` was pure model noise, not a steering bug.

The fix compares the **steering delta** (steered − unsteered) at each row's final
real token against the analytic expectation `alpha_i * d`, and cross-checks the
batched delta against the unbatched delta. The delta cancels the model's shared
forward numerics and isolates exactly the hook's edit, so the `1e-2` floor stays
tight and now actually means "the hook applied `alpha_i * d`." The cell also pins
`tokenizer.padding_side = "right"` (the cleaner apples-to-apples capture; the
delta is robust to either side). On a tiny bf16 Qwen3 model the fixed cell
reports ~5e-3 vs-analytic / ~8e-3 batched-vs-unbatched — PASS.

**Scope:** this was a *cell* (measurement) bug, not an *engine* bug. The
`SteeringHook` batched final-position + per-row-alpha path is unchanged and still
proven by the CPU parity tests below; no registered/scientific run consumed the
batched path (it is unrun AK-Stage-2 prep; the AL arms used batch-1 generation).

New regression tests (`TestGpuEquivalenceCellMethodology`, tiny real bf16 Qwen3,
no download / no GPU) would have caught it: they assert the delta comparison is
floor-tight under both padding sides and that the old absolute comparison is
strictly noisier under bf16 left padding. Runnable without pytest via
`python experiment/phase1/probe/steering/tests/test_arm_b_batched_parity.py`.

## Files changed
- `experiment/phase1/probe/steering/confidence_steer.py` (SteeringHook: final
  position + per-element alpha; docstring + validation)
- `experiment/phase1/probe/steering/tests/test_arm_b_batched_parity.py` (new)
- `experiment/phase1/probe/steering/gpu_equivalence_cell.py` (new, DO-NOT-RUN)
- `docs/preparation/item11-batching-parity-cpu-half.md` (this doc)
