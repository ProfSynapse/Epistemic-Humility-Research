---
aliases:
- sycophancy intervention
- Wei et al. sycophancy intervention
- counterfactual robustness finetuning
tags:
- kg/method
- concept
- method
kg:
  id: method:synthetic-data-sycophancy-intervention
  type: method
  status: canonical
area: methods
related:
- '[[2308.03958--synthetic-data-reduces-sycophancy]]'
- '[[sycophancy]]'
- '[[supervised-finetuning]]'
- '[[instruction-tuning]]'
- '[[imitative-falsehood]]'
- '[[idk-sft]]'
relationships:
- type: proposed_by
  target: '[[2308.03958--synthetic-data-reduces-sycophancy]]'
  target_id: paper:2308.03958
  confidence: high
- type: related_to
  target: '[[sycophancy]]'
  target_id: term:sycophancy
  confidence: medium
- type: related_to
  target: '[[supervised-finetuning]]'
  target_id: method:supervised-finetuning
  confidence: medium
- type: related_to
  target: '[[instruction-tuning]]'
  target_id: method:instruction-tuning
  confidence: medium
- type: related_to
  target: '[[imitative-falsehood]]'
  target_id: term:imitative-falsehood
  confidence: medium
- type: related_to
  target: '[[idk-sft]]'
  target_id: method:idk-sft
  confidence: medium
---

A lightweight continued-finetuning procedure that generates counterfactual-robustness training examples from public NLP task input-label pairs by injecting synthetic user opinions that contradict the correct label, filters out examples the model already fails without a user opinion, mixes the 100k synthetic examples with instruction-tuning data at a 5:1 ratio, and runs continued finetuning for approximately 1k steps. The design ensures the model only trains on cases where it has sufficient prior knowledge to resist the incorrect user signal.

**Why it matters here:** Demonstrates that a behavioral anti-sycophancy fix can be applied at low cost without new preference pairs or a reward model and without inducing an alignment tax on general benchmarks. The filtration step is the critical ingredient: it is functionally a known-unknown split applied to training data selection, connecting this method to the broader knowledge-boundary literature.

**Lineage:** Proposed in Wei et al. 2023 (arXiv 2308.03958). The filtration criterion adapts the known-unknown distinction from the knowledge-boundary literature to data selection. Related to idk-sft in using model self-knowledge as a gate, but applied to sycophancy rather than abstention.
