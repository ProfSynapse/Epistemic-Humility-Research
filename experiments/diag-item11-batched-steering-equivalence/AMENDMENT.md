# Diagnostic Item 11 - Batched Steering Equivalence

Status: historical lab-notebook diagnostic. This is not an amendment and not a
confirmatory claim; it is an engineering gate for the steering harness.

Question: does the batched final-position, per-row-alpha steering hook apply the
same residual edit as the one-prompt-at-a-time reference path on the deployed
Qwen3-4B clean-SFT to GRPO-v2 lineage?

Instrument: `experiment/phase1/probe/steering/gpu_equivalence_cell.py`, launched
through the RunPod/Modal wrappers under `experiment/phase1/probe/cloud/`. The
cell compares steering deltas, not absolute hidden states, to avoid bf16
padded-vs-unpadded forward noise.

Input direction: `artifacts/directions/qwen3-4b-grpo-v2/direction_caution.json`
and `.npy`, a unit-normalized caution direction with `best_layer=34`.

Result: the CPU half of the parity work passed on 2026-07-04. The GPU half was
recorded done on 2026-07-05 after the equivalence cell was corrected to compare
steering deltas and the bf16 floor was re-dimensioned in ULP terms. The recorded
outcome was PASS at machine parity on the deployed lineage, clearing the AK
Stage 2 engine gate.

Verdict: historical harness diagnostic banked as provenance. The direction files
remain tracked because fresh cloud clones need them to replay the diagnostic.
