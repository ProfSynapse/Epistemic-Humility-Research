---
title: grpo-cold-start-induction
aliases:
- 'Cold-start GRPO: can the appropriateness reward induce abstention from the base model?'
- cold-start GRPO induction cell
tags:
- kg/experiment
- experiment
- abstention
kg:
  id: experiment:grpo-cold-start-induction
  type: experiment
  status: canonical
related:
- '[[cold-grpo-falsifier-fires-but-reclassified-as-prompt-preservation]]'
- '[[only-sft-installs-abstention-in-weights]]'
- '[[prompt-vs-training-panel]]'
- '[[rl-insufficient-exploration-blocks-open-ended-abstention]]'
- '[[preference-opt-reduces-abstention-overtax]]'
relationships:
- type: built_on_by
  target: '[[prompt-vs-training-panel]]'
  target_id: experiment:prompt-vs-training-panel
  confidence: high
  evidence:
  - experiments/grpo-cold-start-induction/AMENDMENT.md#outcome (Mechanism,
    per the contemporaneous panel; the falsifier's causal verb does not
    survive the base counterfactual this cell's design lacked)
- type: supports
  target: '[[cold-grpo-falsifier-fires-but-reclassified-as-prompt-preservation]]'
  target_id: mechanism:cold-grpo-falsifier-fires-but-reclassified-as-prompt-preservation
  confidence: high
  evidence:
  - experiments/grpo-cold-start-induction/AMENDMENT.md#outcome (CG-G1 not
    Null-B; eval refusal recall 85.66%, registered >= 20% falsifier fired;
    reclassified via the panel's R2 band)
- type: supports
  target: '[[only-sft-installs-abstention-in-weights]]'
  target_id: mechanism:only-sft-installs-abstention-in-weights
  confidence: high
  evidence:
  - experiments/grpo-cold-start-induction/AMENDMENT.md#outcome (via
    prompt-vs-training-panel arm cold_grpo_seed1_pstruct; cold GRPO reads
    0.00% P-struct, base-identical, despite training on real gradient)
- type: related_to
  target: '[[rl-insufficient-exploration-blocks-open-ended-abstention]]'
  target_id: mechanism:rl-insufficient-exploration-blocks-open-ended-abstention
  confidence: medium
  evidence:
  - experiments/grpo-cold-start-induction/AMENDMENT.md (Design; Null-B, the
    registrants' modal expectation, is exactly this exploration-failure
    mechanism specialized to the rebalanced appropriateness reward; the cell
    found real gradient instead, 0.6478 zero-advantage fraction < 0.90 floor)
- type: related_to
  target: '[[preference-opt-reduces-abstention-overtax]]'
  target_id: mechanism:preference-opt-reduces-abstention-overtax
  confidence: medium
  evidence:
  - experiments/grpo-cold-start-induction/AMENDMENT.md (mirror contrast;
    Cheng et al.'s preference-optimization arms reduce over-refusal on top
    of an SFT-warmed chat base, while this cell's cold DPO/KTO/GRPO track
    the untrained base with no SFT warm-up to build on)
---

Tier-2 exploratory cell closing the 2x4 objective design: cold-start GRPO
(raw Qwen3-4B base, single seed) under the same rebalanced appropriateness
reward used by the program's SFT-warmed GRPO arms, with the trainer and
rollout engine held identical to the warmed comparison (parity-locked engine
exception). Two pre-stated null mechanisms distinguished the modal
expectation: Null-A (trained but did not learn) versus Null-B (no trainable
signal, the registrants' modal call, 0.03%-style exploration failure).

Resolved 2026-08-14 (training 2026-08-13T18:20Z to 2026-08-14T03:35Z, full
1,861-step budget, exit 0). CG-G0 passed. CG-G1: not Null-B (zero-advantage
group fraction 0.6478, under the 0.90 floor; mean reward moved 0.362 to
0.603, KL 0.005 to 0.155, real gradient). Eval refusal recall reached
85.66% (884/1,032), over-refusal 60.89%, firing the registered >= 20%
falsifier far above the band; the registered prediction (recall < 10%,
Null-B modal) was wrong on both counts.

The mechanism call did not stop there: `prompt-vs-training-panel`, signed
and run contemporaneously, measured the raw untrained base under this
cell's identical eval contract at 90.89% recall, ABOVE this trained
checkpoint, and this exact checkpoint under a structure-only prompt at
0.00% (base-identical). Per the panel's R2 band, the outcome verb is
"preserves and sharpens instruction-elicited abstention," not induction;
training moved the model slightly toward answering (error rates down
4-5pp) while doing nothing to the model's behavior once the instruction is
removed.

**Why it matters here:** a falsifier firing against a registered numeric
threshold is not on its own evidence of the registered mechanism (Null-A/
Null-B were both trained-vs-untrained framings; neither anticipated a
counterfactual showing the untrained base already exceeded the trained
checkpoint under the same prompt). This cell is the concrete case for why
`prompt-vs-training-panel` was needed: a bare eval number cannot be read as
"induction" without the base counterfactual.

**Lineage:** the 2x4 design's fourth objective, extending
`grpo-three-seed-confirmatory`'s SFT-warmed GRPO arm to a cold start.
Reclassified via [[prompt-vs-training-panel]]. Source of truth:
`experiments/grpo-cold-start-induction/AMENDMENT.md`, Outcome section,
resolved 2026-08-14.
