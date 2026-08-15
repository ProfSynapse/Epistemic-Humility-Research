---
title: only-sft-installs-abstention-in-weights
aliases:
- SFT internalizes abstention beyond instruction compliance
- only SFT installs abstention in the weights, not the prompt
- DPO/KTO/GRPO from a cold start modulate compliance, they do not internalize
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:only-sft-installs-abstention-in-weights
  type: mechanism
  status: canonical
cause: "Removing the abstention-eliciting instruction (evaluating under the structure-only P-struct contract, zero abstention affordance) from checkpoints of all four cold-start training objectives (SFT, DPO, KTO, GRPO), each trained from the raw untrained Qwen3-4B base with no SFT warm-up: SFT and DPO/KTO measured across three seeds (prompt-vs-training-panel seed 1, pstruct-internalization-seed-robustness seeds 2-3), GRPO measured at one seed (grpo-cold-start-induction, via its P-struct arm in the panel)."
effect: "Only cold-SFT checkpoints retain refusal recall once the instruction is removed: 69.57% / 76.94% / 79.36% across the three seeds, all clearing the panel's registered 30% internalization floor against a base+P-struct ceiling fixed at 0.00% (< 10%; SR-G1 and R3 both pass, neither falsifier fires). Cold DPO and KTO read 0.00% at all three seeds, indistinguishable from the untrained base under P-struct despite reading 93-94% under the P-rc contract that carries their abstention. Cold GRPO reads 0.00% under P-struct too, despite training on real policy gradient (zero-advantage group fraction 0.6478, well under the 0.90 Null-B floor) and reaching 85.66% recall under the instructed P-rc contract. Training therefore installs abstention that survives prompt removal only under the SFT objective; DPO, KTO, and GRPO from a cold start modulate compliance with an instruction the prompt already supplies, without writing new abstention behavior into the weights."
polarity: enables
related:
- '[[prompt-vs-training-panel]]'
- '[[pstruct-internalization-seed-robustness]]'
- '[[grpo-cold-start-induction]]'
- '[[rc-prompt-elicits-near-ceiling-abstention-from-untrained-base]]'
- '[[context-invariance]]'
- '[[icl-only-alignment-matches-sft-rlhf-quality]]'
- '[[idk-sft]]'
- '[[refusal-aware-instruction-tuning]]'
- '[[abstention]]'
relationships:
- type: supported_by
  target: '[[prompt-vs-training-panel]]'
  target_id: experiment:prompt-vs-training-panel
  confidence: high
  evidence:
  - "experiments/prompt-vs-training-panel/AMENDMENT.md#outcome (Bands, R3
    FIRED - cold SFT seed 1 69.57 >= 30 with base 0.00 < 10; cold DPO/KTO
    seed 1 track the base at every prompt, 0≈0 plain/struct)"
- type: supported_by
  target: '[[pstruct-internalization-seed-robustness]]'
  target_id: experiment:pstruct-internalization-seed-robustness
  confidence: high
  evidence:
  - experiments/pstruct-internalization-seed-robustness/AMENDMENT.md#outcome
    (SR-G1 PASS; SFT seeds 2-3 76.94/79.36, DPO/KTO seeds 2-3 all 0.00)
- type: supported_by
  target: '[[grpo-cold-start-induction]]'
  target_id: experiment:grpo-cold-start-induction
  confidence: medium
  evidence:
  - experiments/grpo-cold-start-induction/AMENDMENT.md#outcome (cold GRPO
    trained on real gradient, 0.6478 zero-advantage fraction, yet reads
    0.00% P-struct via the panel's cold_grpo_seed1_pstruct arm)
- type: related_to
  target: '[[rc-prompt-elicits-near-ceiling-abstention-from-untrained-base]]'
  target_id: mechanism:rc-prompt-elicits-near-ceiling-abstention-from-untrained-base
  confidence: medium
  evidence:
  - experiments/prompt-vs-training-panel/AMENDMENT.md#outcome (the P-struct
    base floor, 0.00%, that internalization is scored against, is the same
    base reading that shows P-rc alone carries most of the untrained base's
    abstention)
- type: related_to
  target: '[[context-invariance]]'
  target_id: term:context-invariance
  confidence: medium
  evidence:
  - experiments/pstruct-internalization-seed-robustness/AMENDMENT.md#outcome
    (SFT-internalized abstention stays stable once the instruction is
    removed at inference time; DPO/KTO/GRPO behavior remains coupled to the
    prompt's presence)
- type: related_to
  target: '[[icl-only-alignment-matches-sft-rlhf-quality]]'
  target_id: mechanism:icl-only-alignment-matches-sft-rlhf-quality
  confidence: medium
  evidence:
  - "experiments/prompt-vs-training-panel/AMENDMENT.md#outcome (mirror
    contrast - URIAL shows prompting alone can match trained response
    quality; here cold DPO/KTO/GRPO's trained behavior IS the untrained
    base's prompted behavior, adding nothing beyond what the prompt already
    supplies)"
- type: related_to
  target: '[[idk-sft]]'
  target_id: method:idk-sft
  confidence: medium
  evidence:
  - experiments/pstruct-internalization-seed-robustness/AMENDMENT.md
    (lineage; the program's cold-SFT recipe is trained directly on
    IDK-labeled data, the same supervised-signal shape as Idk-SFT, and is
    the one objective that shows analogous weights-level installation)
- type: related_to
  target: '[[refusal-aware-instruction-tuning]]'
  target_id: method:refusal-aware-instruction-tuning
  confidence: medium
  evidence:
  - experiments/pstruct-internalization-seed-robustness/AMENDMENT.md
    (lineage; R-Tuning is the same SFT-on-refusal-labels lineage the
    program's cold-SFT arm belongs to)
---

Across three cold-start experiments measuring the same structure-only
P-struct readout, one pattern holds without exception: only the SFT
objective leaves a trained-from-cold checkpoint able to abstain once the
eliciting instruction is removed at inference time. `prompt-vs-training-panel`
established this for seed 1 (SFT 69.57% vs base 0.00%, R3 fired) and
measured cold DPO/KTO seed 1 and cold GRPO seed 1 at 0.00% each despite
strong instructed-prompt performance. `pstruct-internalization-seed-robustness`
replicated the SFT finding across seeds 2 and 3 (76.94%, 79.36%) and the
DPO/KTO negative across the same two seeds (four more 0.00% arms), passing
its registered SR-G1 claim gate with no falsifier firing. `grpo-cold-start-induction`
adds the sharpest negative case: cold GRPO trained on genuine policy
gradient (not Null-B, 64.78% zero-advantage groups against a 90% floor,
mean reward roughly doubling over the run) and reached 85.66% recall under
the instructed contract, yet still reads exactly 0.00% once the instruction
is removed, identical to the untrained base.

**Why it matters here:** this is the program's central claim about where
training-regimen abstention lives. SFT changes what the model does even in
the prompt's absence; DPO, KTO, and GRPO from a cold start change how well
the model complies with an instruction the base already responds to, but
leave nothing behind once that instruction is taken away. The claim now
rests on nine measured cold-start arms across three seeds and, for GRPO, an
independently verified real-gradient training run, not a single
observation.

**Lineage:** the panel's R3 band (single seed) confirmed to three seeds by
[[pstruct-internalization-seed-robustness]]; extended to a fourth objective,
GRPO, by [[grpo-cold-start-induction]]. Contrast:
[[icl-only-alignment-matches-sft-rlhf-quality]] (URIAL: prompting alone
matches trained quality); here, for DPO/KTO/GRPO from a cold start, trained
behavior does not exceed prompted behavior. Source of truth: the three
experiments' AMENDMENT.md Outcome sections, all resolved 2026-08-14.
