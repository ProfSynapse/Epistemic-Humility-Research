---
title: rc-prompt-elicits-near-ceiling-abstention-from-untrained-base
aliases:
- the response-confidence contract alone induces near-ceiling base abstention
- untrained base abstains at 90.89% under an explicit instruction, 0% without one
- prompt carries the base's abstention, not training
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:rc-prompt-elicits-near-ceiling-abstention-from-untrained-base
  type: mechanism
  status: canonical
cause: "Evaluating the raw, untrained Qwen3-4B base (no adapter, no post-training of any kind) on the full SelfAware set under three prompt levels: the response-confidence contract (P-rc, explicit abstention affordance), the plain-answer contract (P-plain, its own weaker 'say so plainly' clause), and a minimal structure-only JSON contract (P-struct, no abstention affordance at all)."
effect: "Under P-rc the untrained base reads unknown-labeled refusal recall 90.89% (over-refusal 65.38%), clearing the panel's registered R2 60% band; under P-plain it reads 0.00% (R1's 20% band does not fire) despite P-plain's own abstention clause, and under P-struct it reads 0.00% scored (audited ~4-6% for natural-language hedges not matched by the pinned markers, still under the R3 10% ceiling). No training occurred anywhere in this measurement: the near-ceiling abstention rate under P-rc is carried entirely by the prompt, and removing or weakening the instruction collapses it to the spontaneous-abstention floor."
polarity: enables
related:
- '[[prompt-vs-training-panel]]'
- '[[grpo-cold-start-induction]]'
- '[[only-sft-installs-abstention-in-weights]]'
- '[[prompt-cannot-override-rlvr-abstention-deficit]]'
- '[[abstention]]'
- '[[prompt-crossing-heldout-confirmatory]]'
relationships:
- type: supported_by
  target: '[[prompt-crossing-heldout-confirmatory]]'
  target_id: experiment:prompt-crossing-heldout-confirmatory
  confidence: high
  evidence:
  - "experiments/prompt-crossing-heldout-confirmatory/experiment.yaml (verdict:
    C1 confirmed and promoted, instruction gap 70.26pp on held-out AmbigQA,
    base P-rc 70.26 vs P-plain 0.00, inside the registered 50-90pp band; F1
    not fired)"
- type: supported_by
  target: '[[prompt-vs-training-panel]]'
  target_id: experiment:prompt-vs-training-panel
  confidence: high
  evidence:
  - "experiments/prompt-vs-training-panel/AMENDMENT.md#outcome (per-arm table,
    raw base row - P-rc 90.89/65.38, P-plain 0.00/0.04, P-struct 0.00/0.09;
    Bands, R1 not fired, R2 fired)"
- type: related_to
  target: '[[grpo-cold-start-induction]]'
  target_id: experiment:grpo-cold-start-induction
  confidence: high
  evidence:
  - experiments/grpo-cold-start-induction/AMENDMENT.md#outcome (this base
    reading, 90.89%, is the counterfactual that reclassifies cold GRPO's
    85.66% eval recall as preservation rather than induction)
- type: related_to
  target: '[[only-sft-installs-abstention-in-weights]]'
  target_id: mechanism:only-sft-installs-abstention-in-weights
  confidence: medium
  evidence:
  - experiments/prompt-vs-training-panel/AMENDMENT.md#outcome (the P-struct
    floor measured here, base 0.00%, is the ceiling against which every
    trained arm's internalization is scored)
- type: related_to
  target: '[[prompt-cannot-override-rlvr-abstention-deficit]]'
  target_id: mechanism:prompt-cannot-override-rlvr-abstention-deficit
  confidence: medium
  evidence:
  - "experiments/prompt-vs-training-panel/AMENDMENT.md#outcome (mirror
    polarity - that mechanism is an RLVR-trained always-answer prior resisting
    an explicit abstention prompt; this one is an untrained base's abstention
    behavior being entirely constituted by the prompt, with no trained prior
    to resist it)"
---

The `prompt-vs-training-panel` gives the program's first raw-base SelfAware
reading under any prompt contract. It shows the untrained Qwen3-4B base is
not behaviorally inert with respect to abstention: an explicit
response-confidence instruction alone, no gradient update anywhere, elicits
90.89% unknown-labeled refusal recall, indistinguishable in scale from the
program's trained checkpoints under the same contract (cold DPO 94.48%,
cold KTO 93.99%, cold GRPO's own eval 85.66%). The same base reads 0.00%
under both a weaker plain-answer instruction and a structure-only prompt
with no abstention affordance at all. The 0-to-91-to-94 spread across
contracts on essentially the same (untrained or lightly trained) weights is
the panel's evidence that a large share of what looks like "trained
abstention" in the program's confirmatory contract is the prompt doing the
work.

**Why it matters here:** this reading is the base counterfactual that was
missing when `grpo-cold-start-induction` was signed, and it is what forces
that cell's induction falsifier to be reclassified rather than taken at
face value (see [[cold-grpo-falsifier-fires-but-reclassified-as-prompt-preservation]]).
It also sets the P-struct floor (0.00%, audited ~4-6%) against which every
trained arm's internalization claim in [[only-sft-installs-abstention-in-weights]]
is scored.

**Lineage:** established in [[prompt-vs-training-panel]], signed and
resolved 2026-08-14, scaffolded from the cold-GRPO red-team audit. Confirmed
and promoted to exploratory-companion tier on held-out AmbigQA by
[[prompt-crossing-heldout-confirmatory]] (base P-rc minus P-plain gap
70.26pp, resolved 2026-08-17/18).
