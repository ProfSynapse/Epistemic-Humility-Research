---
aliases:
- Instruction Tuning Improves Self-Knowledge
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:instruction-tuning-improves-self-knowledge
  type: mechanism
  status: canonical
cause: '[[instruction-tuning]] applied to a base LLM (e.g., LLaMA to Alpaca/Vicuna, [[gpt-3]] to [[instructgpt]])'
effect: Increased [[self-knowledge-f1]] on unanswerable question detection, with instruction-tuned smaller models outperforming larger base models
polarity: increases
related:
- '[[2305.18153--selfaware-know-what-they-dont-know]]'
- '[[instruction-tuning]]'
- '[[gpt-3]]'
- '[[instructgpt]]'
- '[[self-knowledge-f1]]'
relationships:
- type: supported_by
  target: '[[2305.18153--selfaware-know-what-they-dont-know]]'
  target_id: paper:2305.18153
  confidence: high
- type: related_to
  target: '[[instruction-tuning]]'
  target_id: method:instruction-tuning
- type: related_to
  target: '[[gpt-3]]'
  target_id: model:gpt-3
- type: related_to
  target: '[[instructgpt]]'
  target_id: model:instructgpt
- type: related_to
  target: '[[self-knowledge-f1]]'
  target_id: metric:self-knowledge-f1
---

Instruction tuning trains models to follow diverse directives, which appears to improve their ability to assess whether they can answer a given question, not just how to answer it. The SelfAware paper (arXiv:2305.18153) shows that Vicuna-13B outperforms LLaMA-65B on [[self-knowledge]] tasks, demonstrating that alignment training can substitute for raw scale in developing self-knowledge. The mechanism likely involves instruction tuning exposing models to more meta-cognitive task formats, including tasks where "I don't know" is the correct response.
