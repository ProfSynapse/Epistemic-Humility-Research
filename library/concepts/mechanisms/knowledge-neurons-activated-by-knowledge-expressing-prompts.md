---
aliases:
- Knowledge Neurons Are Selectively Activated by Fact-Expressing Prompts
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:knowledge-neurons-activated-by-knowledge-expressing-prompts
  type: mechanism
  status: canonical
cause: Presenting a prompt that expresses a specific relational fact (head and tail entities in correct relational context)
effect: Identified knowledge neurons show significantly higher average activation (0.485) than for head-only prompts (0.019) or random prompts (-0.018) on BingRel
polarity: increases
related:
- '[[2104.08696--knowledge-neurons-pretrained-transformers]]'
- '[[knowledge-neurons]]'
- '[[bingrel]]'
relationships:
- type: supported_by
  target: '[[2104.08696--knowledge-neurons-pretrained-transformers]]'
  target_id: paper:2104.08696
  confidence: high
- type: related_to
  target: '[[knowledge-neurons]]'
  target_id: term:knowledge-neurons
- type: related_to
  target: '[[bingrel]]'
  target_id: dataset:bingrel
---

[[knowledge-neurons]] for a given factual relation show highly selective activation patterns: prompts expressing the full fact (head + relation + tail) elicit an average activation of 0.485, while prompts containing only the head entity yield 0.019, and random prompts yield -0.018 on [[bingrel]] (arXiv:2104.08696). This three-way contrast demonstrates that knowledge neurons respond to the relational context surrounding a fact, not merely to entity co-occurrence, providing strong evidence that these neurons encode relational knowledge rather than entity-specific surface patterns.
