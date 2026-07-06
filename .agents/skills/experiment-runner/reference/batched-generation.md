# Batched Generation And Extraction

Standing discipline (user-adopted 2026-07-05) for when GPU cells may batch
and how to do it without corrupting a surface. Batch-1 is the default only
for parity-locked cells; everything else registers an efficient config and
proves it safe with a numerics smoke.

## When batching is allowed

| Cell type | Batch policy |
|-----------|--------------|
| Parity-locked surface (regenerating or extending a cell whose baseline was batch-1, or any cross-arm comparison where arms must share config) | Batch-1, no exceptions. Comparability is the experiment; a 2x speedup is never worth poisoning it. |
| New surface (the cell defines its own generation config; fit and eval both live on it) | Register a batched config from the start. Batch size becomes part of the frozen, pre-registered config. |
| Pure extraction (forward passes over existing text, no generation) | Always batchable, no smoke needed. Size to VRAM. |

Never compare rows generated under different batch regimes. If two cells
must be compared, they must share the full generation config including
batch size.

## Lane guidance

- Generation-only stages (no hidden states needed during decode): use the
  vLLM lane (`VLLMGenerator`). Roughly 10x to 20x over batch-1 HF generate.
- Generation + hidden-state extraction: HF `generate` with LEFT padding,
  batch 8 to 16 for a 4B model on 24 GB at ~96 new tokens. Roughly 4x to
  8x. Extract states in the same batched forward or a separate batched
  pass.
- Steered/hooked generation (per-row interventions at a layer): batch only
  rows sharing the same intervention arm and parameters, or stay batch-1;
  never mix pushed and unpushed rows in one batch unless the hook applies
  per-row masks that have themselves passed the numerics smoke.

## The numerics smoke (mandatory precondition for a batched new surface)

On a fixed ~20-row subset, generate greedy at batch-1 and at the registered
batch N in the same environment. Require token-level agreement (identical
generated token ids) on all rows. If any row diverges, bisect downward
(N -> 8 -> 4 -> 2 -> 1) and freeze the largest agreeing batch; record the
final value in the cell's registered config before the full run. Greedy
decode with left padding should be batch-invariant; the smoke converts that
assumption into a checked precondition for a few seconds of GPU time.

Record in the run record / amendment doc: registered batch size, smoke
outcome (agreed at N, or fell back to M), and the padding side.

First registered use: Amendment AM (residual-catch veto coverage), batch 12
with the bisect-down smoke as a precondition.
