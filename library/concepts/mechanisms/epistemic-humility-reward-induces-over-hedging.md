---
aliases:
- Rewarding epistemic humility induces over-hedging
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:epistemic-humility-reward-induces-over-hedging
  type: mechanism
  status: canonical
cause: Instructing labelers to reward epistemic humility in [[reinforcement-learning-from-human-feedback]] training
effect: Model [[over-hedging]] on simple questions with clear answers, producing unwarranted caveats
polarity: increases
related:
- '[[2203.02155--instructgpt-rlhf]]'
- '[[reinforcement-learning-from-human-feedback]]'
- '[[over-hedging]]'
relationships:
- type: supported_by
  target: '[[2203.02155--instructgpt-rlhf]]'
  target_id: paper:2203.02155
  confidence: high
- type: related_to
  target: '[[reinforcement-learning-from-human-feedback]]'
  target_id: method:reinforcement-learning-from-human-feedback
- type: related_to
  target: '[[over-hedging]]'
  target_id: term:over-hedging
---

When labelers reward expressions of uncertainty as a proxy for honesty, the model learns to hedge indiscriminately because hedging is nearly always preferred over confident wrong answers. The InstructGPT paper (arXiv:2203.02155) documents this as a failure mode: the trained policy adds unnecessary caveats even to questions it answers correctly, degrading helpfulness. This mechanism is a central motivation for the Phase 1 study of calibrated abstention.
