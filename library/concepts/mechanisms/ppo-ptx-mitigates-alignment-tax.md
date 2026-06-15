---
aliases:
- Pretraining mix mitigates alignment tax
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:ppo-ptx-mitigates-alignment-tax
  type: mechanism
  status: canonical
cause: Mixing pretraining distribution gradients into PPO updates (PPO-ptx)
effect: Performance regressions on public NLP benchmarks captured by the [[alignment-tax]] are largely eliminated without compromising labeler preference scores
polarity: prevents
related:
- '[[2203.02155--instructgpt-rlhf]]'
- '[[alignment-tax]]'
relationships:
- type: supported_by
  target: '[[2203.02155--instructgpt-rlhf]]'
  target_id: paper:2203.02155
  confidence: high
- type: related_to
  target: '[[alignment-tax]]'
  target_id: term:alignment-tax
---

RLHF fine-tuning shifts the model distribution toward labeler-preferred outputs, which can degrade performance on tasks not represented in the preference data. PPO-ptx counteracts this by periodically injecting pretraining log-likelihood gradients, anchoring the model to its original distribution. The InstructGPT paper (arXiv:2203.02155) shows this largely closes the gap on public NLP benchmarks while retaining the preference gains from RLHF.
