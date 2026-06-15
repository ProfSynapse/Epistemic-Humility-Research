---
aliases:
- Compete
- competitive multi-LLM abstention
- adversarial multi-LLM abstention
- Compete (multi-LLM abstention)
tags:
- kg/method
- concept
- method
kg:
  id: method:multi-llm-compete
  type: method
  status: canonical
area: methods
related:
- '[[2402.00367--dont-hallucinate-abstain]]'
- '[[self-consistency]]'
relationships:
- type: proposed_by
  target: '[[2402.00367--dont-hallucinate-abstain]]'
  target_id: paper:2402.00367
  confidence: high
- type: related_to
  target: '[[self-consistency]]'
  target_id: method:self-consistency
---

Compete is a multi-LLM abstention method that pits the target model against peer
LLMs generating conflicting alternative answers. If the target model is swayed
away from its parametric answer in a majority of trials, the model is judged
low-confidence and should abstain rather than respond.

**Why it matters here:** The method operationalizes epistemic humility through
social pressure from adversarial peers, providing a reference point for comparing
abstention strategies without requiring labelled uncertainty data; it is studied
alongside cooperative approaches in the AbstainQA framework.

**Lineage:** related to [[self-consistency]], which aggregates multiple
model-generated chains rather than introducing external adversarial pressure.
