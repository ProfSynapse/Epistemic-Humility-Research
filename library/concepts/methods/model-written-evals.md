---
aliases:
- LM-written evaluations
- LM-based evaluation generation
- model-written eval pipeline
tags:
- kg/method
- concept
- method
kg:
  id: method:model-written-evals
  type: method
  status: canonical
area: methods
related:
- '[[2212.09251--model-written-evals]]'
- '[[reinforcement-learning-from-human-feedback]]'
- '[[reward-model]]'
- '[[sycophancy]]'
- '[[supervised-finetuning]]'
relationships:
- type: proposed_by
  target: '[[2212.09251--model-written-evals]]'
  target_id: paper:2212.09251
  confidence: high
- type: related_to
  target: '[[reinforcement-learning-from-human-feedback]]'
  target_id: method:reinforcement-learning-from-human-feedback
  confidence: medium
- type: related_to
  target: '[[reward-model]]'
  target_id: method:reward-model
  confidence: medium
- type: related_to
  target: '[[sycophancy]]'
  target_id: term:sycophancy
  confidence: medium
- type: related_to
  target: '[[supervised-finetuning]]'
  target_id: method:supervised-finetuning
  confidence: medium
---

A two-stage dataset generation pipeline in which an RLHF-trained LM generates candidate (input, label) pairs conditioned on a behavioral description, and a preference model filters candidates by predicted label correctness. Zero-shot or few-shot prompting of the generator is combined with PM-based ranking to produce label-balanced yes/no or multiple-choice evaluation datasets at scale.

**Why it matters here:** Reduces the cost of behavioral evaluation from days of crowdwork to minutes per dataset, enabling rapid discovery of novel LM behaviors such as sycophancy and instrumental subgoals across model sizes and training checkpoints. The approach also allows head-to-head quality comparison with human-written data, establishing that LM-written datasets approach human quality on label correctness and relevance.

**Lineage:** Proposed by Perez et al. (arXiv 2212.09251); builds on stochastic few-shot generation from Perez et al. (2022) and uses the RLHF preference model from Bai et al. (2022).
