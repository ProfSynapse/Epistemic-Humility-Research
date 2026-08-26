---
aliases:
- Refusal axis reads at the J-lens mid-band site but ablation there does not actuate
- hs17 read/write dissociation on a trained checkpoint
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:refusal-axis-readable-but-not-ablatable-at-midband
  type: mechanism
  status: canonical
cause: "On the trained clean_sft_grpo_v2_seed1 checkpoint (SFT + GRPO-v2 seed 1 lineage), fitting and fully ablating the mass-mean refusal-axis direction (known_refused vs known_correct_answered) at hs17, the shallowest interior J-lens grid point clearing the pre-registered site-selection rule (interior window hs/36 in [0.35, 0.85], threshold >= 0.5x interior max effective_dim_frac_mean), instead of at the governed late write site L35 used by the same-checkpoint caution-ablation-rederivation."
effect: "hs17 reads the refusal axis nearly as well as L35 (construction AUROC 0.8645 vs 0.8688), but full ablation there releases none of the known-item over-refusal collapse: known_refused refusal stays at 1.0000 (past the 0.30 falsifier line, where L35 releases 163 of the same 168 rows) and induces refusal on 47.99% of the 373 previously answered known-item rows (correct rate falls to 0.5013), a catastrophic specificity break. Row-paired against the L35 rederivation on the identical 541 rows, the two sites' released rows have zero overlap. A -2 SD shift at hs17 releases more of the collapse (0.7143) than full ablation (1.0000 refused), suggesting the axis at this depth is entangled with the model's answering computation rather than acting as a clean refusal toggle. The strongest same-checkpoint, same-axis demonstration of read/actuate depth dissociation in the program: J-lens read-side localization does not license a write site here."
polarity: decouples
related:
- '[[jlens-trained-checkpoint-midband-ablation]]'
- '[[j-space-mediated-actuation-fragility]]'
- '[[raw-theta-refusal-axis-ablation-rederives-archived-overrefusal-collapse]]'
- '[[full-refusal-axis-ablation-collapse-is-seed1-specific]]'
- '[[caution-encoding-read-actuate-dissociation-across-families]]'
- '[[training-flattens-and-deepens-jlens-workspace-band]]'
- '[[directional-ablation]]'
- '[[jacobian-lens]]'
- '[[refusal-direction]]'
relationships:
- type: supported_by
  target: '[[jlens-trained-checkpoint-midband-ablation]]'
  target_id: experiment:jlens-trained-checkpoint-midband-ablation
  confidence: high
  evidence:
  - "experiments/jlens-trained-checkpoint-midband-ablation/AMENDMENT.md#outcome (JT-G1 falsifier fired on both clauses: known-item over-refusal release 1.0000 >= 0.30; induced refusal on knowns 0.4799 > 0.05)"
- type: related_to
  target: '[[j-space-mediated-actuation-fragility]]'
  target_id: mechanism:j-space-mediated-actuation-fragility
  confidence: high
  evidence:
  - "extends the write/read-site-mismatch account from raw-base steering writes to a trained checkpoint's full refusal-axis ablation; the mismatch here is directional and total, not merely a smaller effect size"
- type: related_to
  target: '[[raw-theta-refusal-axis-ablation-rederives-archived-overrefusal-collapse]]'
  target_id: mechanism:raw-theta-refusal-axis-ablation-rederives-archived-overrefusal-collapse
  confidence: high
  evidence:
  - "this mechanism's L35 comparison point (163/168 released, 0.0298 known-item over-refusal) is the governed collapse that mechanism established on the same checkpoint"
- type: related_to
  target: '[[full-refusal-axis-ablation-collapse-is-seed1-specific]]'
  target_id: mechanism:full-refusal-axis-ablation-collapse-is-seed1-specific
  confidence: medium
  evidence:
  - "companion falsified generalization test of the same governed L35 collapse: that mechanism shows the magnitude does not transfer across seeds at the fixed late site, this mechanism shows it does not transfer across depth at the fixed seed"
- type: related_to
  target: '[[caution-encoding-read-actuate-dissociation-across-families]]'
  target_id: mechanism:caution-encoding-read-actuate-dissociation-across-families
  confidence: medium
  evidence:
  - "same-checkpoint, same-axis instance of the program's read/actuate depth-dissociation doctrine, complementing that mechanism's cross-family late-site dissociation with a single-checkpoint cross-depth dissociation"
- type: related_to
  target: '[[training-flattens-and-deepens-jlens-workspace-band]]'
  target_id: mechanism:training-flattens-and-deepens-jlens-workspace-band
  confidence: medium
  evidence:
  - "same cell's companion finding: the J-lens interior band this site sits inside is itself reshaped by training"
- type: related_to
  target: '[[directional-ablation]]'
  target_id: method:directional-ablation
  confidence: high
- type: related_to
  target: '[[jacobian-lens]]'
  target_id: method:jacobian-lens
  confidence: high
- type: related_to
  target: '[[refusal-direction]]'
  target_id: term:refusal-direction
  confidence: medium
---

Registered exploratory finding, resolved 2026-08-16: on the trained
`clean_sft_grpo_v2_seed1` checkpoint, the refusal axis is linearly readable at
the J-lens rule-selected mid-band site hs17 nearly as well as at the governed
late write site L35 (construction AUROC 0.8645 vs 0.8688), but the causal
handle does not transfer. Full ablation at hs17 releases zero of the
known-item over-refusal collapse that the same operation releases almost
entirely at L35 (163 of 168 rows), and it additionally breaks specificity,
inducing refusal on 47.99% of previously answered known items. A row-paired
comparison on the identical 541 rows finds zero overlap between what the two
sites release.

**Why it matters here:** this is not a smaller or noisier version of the L35
effect, it is a directionally different one. A -2 SD shift at hs17 releases
more of the collapse (0.7143) than full ablation does (1.0000 refused),
which suggests the axis at this depth is entangled with the model's
answering computation itself rather than isolable as a clean refusal toggle.
J-lens read-side localization of a workspace-like band at this depth does not
license treating it as a write site: readability and actuatability decouple
here even though both were measured on the identical checkpoint and axis.

**Scope:** registered exploratory tier; does not move the governed paper-3
late-site ablation numbers, which this finding validates as the site where
the causal handle actually works rather than a naive legacy choice. Source of
truth: `experiments/jlens-trained-checkpoint-midband-ablation/AMENDMENT.md`,
Outcome section, resolved 2026-08-16.
