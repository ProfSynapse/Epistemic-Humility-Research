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

## GPU equivalence cell (PREPARED, NOT RUN)

`gpu_equivalence_cell.py` — loud DO-NOT-RUN docstring + a required
`--i-know-this-runs-on-gpu` flag (refuses to run without it). On a handful of
real prompts it compares the batched final-position + per-row-alpha edit at the
direction's `best_layer` against a one-prompt-at-a-time reference, and reports
per-row and overall max abs divergence at each row's last real token. Expected
result is the model's own batched-vs-unbatched numeric floor, orders of
magnitude below the steering magnitude. Launch only under a signed amendment +
explicit user approval, and only when the GPU is free.

## Files changed
- `experiment/phase1/probe/steering/confidence_steer.py` (SteeringHook: final
  position + per-element alpha; docstring + validation)
- `experiment/phase1/probe/steering/tests/test_arm_b_batched_parity.py` (new)
- `experiment/phase1/probe/steering/gpu_equivalence_cell.py` (new, DO-NOT-RUN)
- `docs/preparation/item11-batching-parity-cpu-half.md` (this doc)
