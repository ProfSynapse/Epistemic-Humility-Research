---
title: dial-margin-over-logprob-is-checkpoint-dependent
aliases:
- The dial's advantage over the model's own logprob depends on which
  checkpoint is measured
- Negligible on the raw base, large and gated on the deployed
  abstention-trained checkpoint
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:dial-margin-over-logprob-is-checkpoint-dependent
  type: mechanism
  status: canonical
cause: "Measuring the correctness dial's margin over the model's own length-normalized mean answer-span log-probability on two checkpoints of the same fresh self-consistent single-pass instrument (same lineage, same paired-bootstrap statistic, same falsifier): the raw Qwen3-4B Instruct base (S arm, dial-logprob-baseline-v3) and the deployed abstention-trained checkpoint (T arm, dial-logprob-t-deployed-confirmatory)."
effect: "The margin's size and gate outcome differ by checkpoint. On the raw base, the margin is small and statistically uncertain (+0.0118, paired 95% CI [-0.0122, +0.0359]) and lands in the pre-registered ambiguous band, gate not passed. On the deployed abstention-trained checkpoint, the margin is large and gated (+0.1393, paired 95% CI [0.1031, 0.1755]), clearing the +0.05 LT-G1 floor with the CI excluding zero. The dial's independent value over the model's own confidence signal is checkpoint-dependent, not a fixed property of the dial."
polarity: modulates
related:
- '[[dial-logprob-baseline-v3]]'
- '[[dial-logprob-t-deployed-confirmatory]]'
- '[[qwen3-4b-dial-margin-over-logprob-remains-ambiguous-on-fresh-generation]]'
- '[[qwen3-4b-dial-margin-over-logprob-large-on-deployed-checkpoint]]'
- '[[sequence-probability]]'
relationships:
- type: supported_by
  target: '[[dial-logprob-baseline-v3]]'
  target_id: experiment:dial-logprob-baseline-v3
  confidence: high
  evidence:
  - experiments/dial-logprob-baseline-v3/AMENDMENT.md#outcome (S arm; "dial
    AUROC minus primary-logprob AUROC = +0.0118, paired 95% CI [-0.0122,
    +0.0359]"; ambiguous-band disposition, gate not passed)
- type: supported_by
  target: '[[dial-logprob-t-deployed-confirmatory]]'
  target_id: experiment:dial-logprob-t-deployed-confirmatory
  confidence: high
  evidence:
  - experiments/dial-logprob-t-deployed-confirmatory/AMENDMENT.md#outcome
    (paired with v3's S-arm result, raw base margin +0.0118 ambiguous
    band, the program-level shape is that the dial's margin over the
    model's own answer-span logprob is checkpoint dependent -- negligible
    on the raw base, large and now gated on the deployed abstention-trained
    checkpoint)
- type: related_to
  target: '[[qwen3-4b-dial-margin-over-logprob-remains-ambiguous-on-fresh-generation]]'
  target_id: mechanism:qwen3-4b-dial-margin-over-logprob-remains-ambiguous-on-fresh-generation
  confidence: high
  evidence:
  - experiments/dial-logprob-baseline-v3/AMENDMENT.md#outcome (the base-arm
    half of this checkpoint comparison)
- type: related_to
  target: '[[qwen3-4b-dial-margin-over-logprob-large-on-deployed-checkpoint]]'
  target_id: mechanism:qwen3-4b-dial-margin-over-logprob-large-on-deployed-checkpoint
  confidence: high
  evidence:
  - experiments/dial-logprob-t-deployed-confirmatory/AMENDMENT.md#outcome
    (the deployed-checkpoint half of this checkpoint comparison)
- type: related_to
  target: '[[sequence-probability]]'
  target_id: term:sequence-probability
  confidence: high
  evidence:
  - experiments/dial-logprob-t-deployed-confirmatory/AMENDMENT.md (Design;
    both arms compare against the same length-normalized mean answer-span
    logprob statistic)
---

Two gated cells in the dial-logprob-baseline lineage now bracket the same
comparison, dial AUROC minus the model's own answer-span logprob AUROC, on
two different checkpoints of the same fresh self-consistent instrument.
[[dial-logprob-baseline-v3]]'s S arm measured the raw Qwen3-4B Instruct
base and landed in the pre-registered ambiguous band (+0.0118, CI
straddling 0). [[dial-logprob-t-deployed-confirmatory]]'s T arm measured
the deployed abstention-trained checkpoint and cleared the novelty gate by
a wide margin (+0.1393, CI [0.1031, 0.1755]).

**Why it matters here:** the two results are not in tension, they are the
same instrument run twice under identical statistics and falsifier
structure, differing only in which checkpoint was measured. That rules out
instrument artifact as the explanation for either read and licenses the
program-level claim: the dial's independent value over the model's own
sequence-probability signal is not a fixed property of the dial, it
depends on the checkpoint. On the raw base, sequence probability alone
already captures nearly all of the dial's separation; on the deployed,
abstention-trained checkpoint, the dial retains a large, gated advantage
the model's own logprob does not have.

**Lineage:** synthesizes the S-arm outcome of [[dial-logprob-baseline-v3]]
(resolved 2026-08-13) and the T-arm outcome of
[[dial-logprob-t-deployed-confirmatory]] (resolved 2026-08-13), the two
gated halves of the same base-vs-deployed checkpoint comparison.
