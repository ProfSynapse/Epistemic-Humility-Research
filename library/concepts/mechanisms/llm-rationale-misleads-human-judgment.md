---
aliases:
- LLM-Generated Rationales Can Mislead Human Judgment on Uncertain Questions
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:llm-rationale-misleads-human-judgment
  type: mechanism
  status: canonical
cause: Exposure to LLM-generated rationales about whether a question is known or unknown
effect: Human accuracy on known-vs-unknown perception drops when the rationale is uninformative or incorrect, even though users are influenced by it regardless of correctness
polarity: decreases
related:
- '[[2305.13712--kuq-knowledge-of-knowledge]]'
- '[[2305.04388--language-models-don-t-always-say-what]]'
relationships:
- type: supported_by
  target: '[[2305.13712--kuq-knowledge-of-knowledge]]'
  target_id: paper:2305.13712
  confidence: high
- type: supported_by
  target: '[[2305.04388--language-models-don-t-always-say-what]]'
  target_id: paper:2305.04388
  confidence: high
---

Humans tend to anchor on LLM-generated rationales even when those rationales are unreliable, treating fluent explanations as evidence of correctness. The KUQ paper (arXiv:2305.13712) shows that human accuracy on known-vs-unknown classification drops from 0.74 to 0.705 when uninformative or incorrect LLM rationales are presented, because humans defer to the model's apparent confidence. This highlights a risk in human-AI teaming where LLM overconfidence propagates into human judgments.
