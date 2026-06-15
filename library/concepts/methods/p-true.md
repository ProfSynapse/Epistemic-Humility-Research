---
aliases:
- P(True)
- self-evaluation via True/False
- probability-true
tags:
- kg/method
- concept
- method
kg:
  id: method:p-true
  type: method
  status: canonical
area: methods
related:
- '[[2207.05221--lms-mostly-know-what-they-know]]'
- '[[calibration]]'
- '[[p-ik]]'
relationships:
- type: proposed_by
  target: '[[2207.05221--lms-mostly-know-what-they-know]]'
  target_id: paper:2207.05221
  confidence: high
- type: related_to
  target: '[[calibration]]'
  target_id: term:calibration
- type: related_to
  target: '[[p-ik]]'
  target_id: method:p-ik
---

P(True) is a prompting-based self-evaluation technique in which a language model,
given a question and one of its own proposed answers, assigns probability to the
token "True" versus "False" as a proxy for confidence in the answer's correctness.
No parameter updates are required; accuracy improves when the model is shown
multiple of its own sampled answers before scoring one (the "brainstorming" variant),
and few-shot examples further sharpen calibration.

**Why it matters here:** P(True) establishes the baseline of prompt-only
self-assessment that the SFT-vs-DPO-vs-KTO abstention study builds on, showing
how much explicit training is needed beyond what a model can recover from its own
token probabilities.

**Lineage:** related to [[calibration]] and to [[p-ik]], which replaces the
prompting step with a trained binary value head evaluated before any answer is
sampled.
