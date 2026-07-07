---
aliases:
- IFEval
- instruction following eval
- instruction-following evaluation
tags:
- kg/dataset
- concept
- dataset
kg:
  id: dataset:ifeval
  type: dataset
  status: canonical
area: evaluation
related:
- '[[2607.05355--faithfulness-refusal-causal-audit-neuron-selectors]]'
relationships:
- type: used_by
  target: '[[2607.05355--faithfulness-refusal-causal-audit-neuron-selectors]]'
  target_id: paper:2607.05355
  confidence: high
---

IFEval is an instruction-following benchmark that checks whether a model satisfies explicit formatting and content constraints in a prompt. In Faithfulness to Refusal, it is used as a downstream utility measure after refusal masks are applied.

**Why it matters here:** A refusal intervention that preserves harmful-request refusal but damages ordinary instruction following is not a clean safety or epistemic-humility improvement. IFEval catches that kind of utility collapse.

**Lineage:** standard instruction-following benchmark; used as a utility check in [[2607.05355--faithfulness-refusal-causal-audit-neuron-selectors]].
