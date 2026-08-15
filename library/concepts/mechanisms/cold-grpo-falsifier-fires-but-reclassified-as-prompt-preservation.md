---
title: cold-grpo-falsifier-fires-but-reclassified-as-prompt-preservation
aliases:
- cold-start GRPO's induction falsifier fires but the base counterfactual reclassifies it
- 85.66% recall is preservation of instruction-elicited abstention, not induction
- the induction framing is retired for cold-start GRPO
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:cold-grpo-falsifier-fires-but-reclassified-as-prompt-preservation
  type: mechanism
  status: canonical
cause: "Cold-start GRPO trains the raw Qwen3-4B base under the rebalanced appropriateness reward for the full registered 1,861-step budget, producing real policy gradient (zero-advantage group fraction 0.6478, under the 0.90 Null-B floor; mean reward 0.362 -> 0.603, KL 0.005 -> 0.155), and is then evaluated on the standard instructed (P-rc) SelfAware contract, reaching unknown-labeled refusal recall 85.66% (over-refusal 60.89%), which clears the cell's own registered >= 20% induction falsifier by a wide margin; the contemporaneously run prompt-vs-training-panel measures the same eval contract on the untrained base (no adapter) at 90.89% recall, above this trained checkpoint, and on this exact checkpoint under a structure-only prompt with no abstention affordance at 0.00%, identical to the untrained base."
effect: "The registered falsifier's causal reading does not survive the base counterfactual the cell's own design lacked at signing: the trained checkpoint's instructed-prompt recall (85.66%) sits below the untrained base's own instructed-prompt recall (90.89%), so training moved the model slightly TOWARD answering rather than toward abstention (both error rates down roughly 4-5 percentage points), and the checkpoint's abstention vanishes entirely once the instruction is removed. Per the panel's frozen R2 band, the outcome verb becomes \"preserves and sharpens instruction-elicited abstention\" rather than \"induces\"; the registered prediction (recall < 10%, Null-B modal) is falsified on both the mechanism call and the numeric band, but the plain \"induction\" reading the falsifier was built to detect is retired with it."
polarity: complicates
related:
- '[[grpo-cold-start-induction]]'
- '[[prompt-vs-training-panel]]'
- '[[rc-prompt-elicits-near-ceiling-abstention-from-untrained-base]]'
- '[[only-sft-installs-abstention-in-weights]]'
- '[[rl-insufficient-exploration-blocks-open-ended-abstention]]'
- '[[abstention]]'
relationships:
- type: supported_by
  target: '[[grpo-cold-start-induction]]'
  target_id: experiment:grpo-cold-start-induction
  confidence: high
  evidence:
  - experiments/grpo-cold-start-induction/AMENDMENT.md#outcome (CG-G0 PASS;
    CG-G1 not Null-B, 0.6478 < 0.90 floor; eval refusal recall 85.66%,
    registered >= 20% falsifier FIRED; Mechanism, per the contemporaneous
    panel)
- type: supported_by
  target: '[[prompt-vs-training-panel]]'
  target_id: experiment:prompt-vs-training-panel
  confidence: high
  evidence:
  - experiments/prompt-vs-training-panel/AMENDMENT.md#outcome (raw base
    P-rc 90.89/65.38; Bands, R2 FIRED at base+P-rc 90.89 >= 60, the
    cold-GRPO outcome verb becomes "preserves and sharpens
    instruction-elicited abstention")
- type: related_to
  target: '[[rc-prompt-elicits-near-ceiling-abstention-from-untrained-base]]'
  target_id: mechanism:rc-prompt-elicits-near-ceiling-abstention-from-untrained-base
  confidence: high
  evidence:
  - experiments/prompt-vs-training-panel/AMENDMENT.md#outcome (the base's
    90.89% P-rc reading is the counterfactual this reclassification turns
    on)
- type: related_to
  target: '[[only-sft-installs-abstention-in-weights]]'
  target_id: mechanism:only-sft-installs-abstention-in-weights
  confidence: high
  evidence:
  - experiments/grpo-cold-start-induction/AMENDMENT.md#outcome (this
    checkpoint's 0.00% P-struct reading, base-identical, is cold GRPO's
    negative arm in the internalization mechanism)
- type: related_to
  target: '[[rl-insufficient-exploration-blocks-open-ended-abstention]]'
  target_id: mechanism:rl-insufficient-exploration-blocks-open-ended-abstention
  confidence: low
  evidence:
  - experiments/grpo-cold-start-induction/AMENDMENT.md (Design; Null-B was
    registered as the modal expectation, an exploration-failure mechanism
    of this shape, but the run found real gradient instead, 0.6478
    zero-advantage fraction, ruling that specific mechanism out here)
---

`grpo-cold-start-induction` registered a strict falsifier (eval refusal
recall >= 20%) meant to distinguish "this reward can induce abstention from
a cold start" from two pre-stated nulls. The run cleared the falsifier by a
wide margin, 85.66% against the 20% threshold, and the CG-G1 mechanism gate
independently ruled out Null-B (no trainable signal): the training produced
real gradient, with mean reward roughly doubling and KL rising from 0.005
to 0.155 over the full 1,861-step budget. Read alone, this looks like a
clean falsification in the "induces abstention" direction.

The cell's own design lacked a base counterfactual, and
`prompt-vs-training-panel`, signed and run in the same window, supplies
one: the untrained base reads 90.89% recall under the identical instructed
contract, above this trained checkpoint, and this exact checkpoint reads
0.00% under a structure-only prompt with the instruction removed, identical
to the untrained base under the same prompt. Training therefore moved the
checkpoint slightly toward answering, not toward abstention, and left
nothing behind once the instruction was taken away. The registered
falsifier's raw numeric threshold still fired, but the causal verb it was
built to support, "induces," does not survive the counterfactual and is
retired for this cell; the panel's frozen R2 band supplies the replacement
verb, "preserves and sharpens instruction-elicited abstention."

**Why it matters here:** a falsifier firing against a registered threshold
is necessary but not sufficient for the mechanism claim the threshold was
meant to license; a bare eval number needed the base counterfactual to be
read correctly. This is the concrete instance, inside the program, of why
`prompt-vs-training-panel` exists.

**Lineage:** the registered falsifier and its numeric result belong to
[[grpo-cold-start-induction]] (SIGNED 2026-08-13, resolved 2026-08-14); the
reclassification is licensed by [[prompt-vs-training-panel]]'s frozen R2
band (also resolved 2026-08-14). Source of truth: both AMENDMENT.md Outcome
sections.
