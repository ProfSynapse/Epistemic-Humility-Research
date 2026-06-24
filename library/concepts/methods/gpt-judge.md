---
aliases:
- GPT-judge
- GPT judge
- fine-tuned truthfulness classifier
tags:
- kg/method
- concept
- method
kg:
  id: method:gpt-judge
  type: method
  status: canonical
area: methods
related:
- '[[2109.07958--truthfulqa]]'
- '[[llm-as-judge]]'
- '[[truthfulqa]]'
- '[[supervised-finetuning]]'
- '[[truthful-helpfulness-score]]'
relationships:
- type: proposed_by
  target: '[[2109.07958--truthfulqa]]'
  target_id: paper:2109.07958
  confidence: high
- type: related_to
  target: '[[llm-as-judge]]'
  target_id: method:llm-as-judge
  confidence: medium
- type: related_to
  target: '[[truthfulqa]]'
  target_id: dataset:truthfulqa
  confidence: medium
- type: related_to
  target: '[[supervised-finetuning]]'
  target_id: method:supervised-finetuning
  confidence: medium
- type: related_to
  target: '[[truthful-helpfulness-score]]'
  target_id: metric:truthful-helpfulness-score
  confidence: medium
---

A GPT-3-6.7B model fine-tuned on human-labeled (question, answer, true/false) triples to automatically classify whether a model-generated answer to a TruthfulQA question is truthful. Trained on 6.9k reference-answer examples and approximately 15.5k model-generated examples with human labels, it achieves 90-96% cross-validation accuracy on held-out model families and generalizes to architecturally different models (UnifiedQA) and to human-generated baselines not seen during training. A parallel model trained on informativeness labels (GPT-info) achieves 86.3% on UnifiedQA.

**Why it matters here:** GPT-judge establishes the template for LLM-as-judge evaluation of truthfulness: a fine-tuned LLM as cheap proxy for human annotation that generalizes across model families and architectures. It is the direct ancestor of the LLM-as-judge convention now widely used in alignment evaluation.

**Lineage:** Proposed in TruthfulQA (Lin et al., 2021, arXiv 2109.07958); prefigures the general llm-as-judge method.
