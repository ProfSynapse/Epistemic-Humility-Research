---
aliases:
- recalled facts improve answer recall
- generative self-retrieval improves recall
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:factual-priming-improves-recall
  type: mechanism
  status: canonical
cause: "Generating (or being conditioned on) topically related facts surfaced during reasoning before producing the final answer, isolated via the ON Facts and OFF Facts variants against dummy-length-matched controls."
effect: "pass@k rises well above the dummy controls; conditioning on the extracted fact list recovers most of the reasoning-ON gain even with reasoning disabled (OFF Facts), and on EntityQuestions ON Facts matches full reasoning ON at far lower compute."
polarity: increases
related:
- '[[2603.09906--thinking-recall-how-reasoning-unlocks-parametric-knowledge]]'
- '[[factual-priming]]'
- '[[generation-discrimination-gap]]'
relationships:
- type: supported_by
  target: '[[2603.09906--thinking-recall-how-reasoning-unlocks-parametric-knowledge]]'
  target_id: paper:2603.09906
  confidence: high
- type: related_to
  target: '[[factual-priming]]'
  target_id: term:factual-priming
  confidence: high
- type: related_to
  target: '[[generation-discrimination-gap]]'
  target_id: term:generation-discrimination-gap
  confidence: medium
---

The semantic content of reasoning traces, specifically recalled related facts, drives the majority of reasoning's recall gains: providing just the extracted facts as context recovers most of the pass@k improvement even without reasoning, while dummy-length-matched controls do not (Figure 6, Section 5.2). This is direct evidence that a model can be primed to express latent knowledge it would otherwise fail to retrieve.
