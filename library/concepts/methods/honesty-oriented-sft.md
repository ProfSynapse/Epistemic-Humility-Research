---
aliases:
- honesty-oriented fine-tuning
- Absolute
- Confidence
- Multisample
- alignment for honesty
- Honesty-Oriented Supervised Fine-Tuning
tags:
- kg/method
- concept
- method
kg:
  id: method:honesty-oriented-sft
  type: method
  status: canonical
area: methods
related:
- '[[2312.07000--alignment-for-honesty]]'
- '[[supervised-finetuning]]'
relationships:
- type: proposed_by
  target: '[[2312.07000--alignment-for-honesty]]'
  target_id: paper:2312.07000
  confidence: high
- type: derived_from
  target: '[[supervised-finetuning]]'
  target_id: method:supervised-finetuning
---

Honesty-oriented SFT is a family of supervised fine-tuning methods that teach a
model to proactively abstain on questions it cannot reliably answer. The core
pipeline labels each training question as "known" or "unknown" by measuring the
model's expected accuracy over multiple sampled answers, then replaces the
targets for unknown questions with idk responses; the model is then fine-tuned on
this relabeled corpus. Variants differ in the labeling strategy: Absolute uses a
fixed correctness threshold, Confidence uses the model's own probability
estimates, and Multisample averages accuracy across several independent samples.

**Why it matters here:** Honesty-oriented SFT is the primary baseline method in
the alignment-for-honesty framework and represents one end of the training
spectrum the locked training-regimen study extends with preference-optimization alternatives
([[direct-preference-optimization]] and [[kahneman-tversky-optimization]]). Its
success establishes that the expected-accuracy signal alone can teach
[[abstention]], but also reveals the [[over-abstention]] failure mode the study
investigates.

**Lineage:** derives from [[supervised-finetuning]]; the expected-accuracy
labeling idea is related to [[p-ik]] and the broader [[answer-relabeling]]
technique.
