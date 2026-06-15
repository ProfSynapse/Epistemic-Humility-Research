---
aliases:
- P(IK)
- probability-I-know
- ProbIK
- I Know probability
tags:
- kg/method
- concept
- method
kg:
  id: method:p-ik
  type: method
  status: canonical
area: methods
related:
- '[[2207.05221--lms-mostly-know-what-they-know]]'
- '[[p-true]]'
- '[[calibration]]'
relationships:
- type: proposed_by
  target: '[[2207.05221--lms-mostly-know-what-they-know]]'
  target_id: paper:2207.05221
  confidence: high
- type: related_to
  target: '[[p-true]]'
  target_id: method:p-true
- type: related_to
  target: '[[calibration]]'
  target_id: term:calibration
---

P(IK) (Probability "I Know") adds a binary value head to a language model and
trains it via cross-entropy to predict, before any answer is sampled, whether the
model will answer a question correctly at unit temperature. Labels are derived
empirically by sampling 30 answers per question and recording the pass rate.
Unlike [[p-true]], P(IK) operates as a pre-generation confidence estimate rather
than a post-hoc self-evaluation, and requires supervised training to learn.

**Why it matters here:** P(IK) demonstrates that a model can be trained to know
what it knows, providing a reference point for how much signal is available from
fine-tuning when the SFT-vs-DPO-vs-KTO study asks whether preference optimization
further improves calibrated abstention.

**Lineage:** related to [[p-true]], which achieves similar discrimination via
prompting alone rather than a trained head; both were introduced in the same paper.
