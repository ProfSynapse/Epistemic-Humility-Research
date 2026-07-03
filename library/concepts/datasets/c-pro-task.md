---
aliases:
- Concrete Permuted Rule Operations
- C-PRO
- C-PRO paradigm
- C-PRO Task Paradigm
tags:
- kg/dataset
- concept
- dataset
kg:
  id: dataset:c-pro-task
  type: dataset
  status: canonical
area: neuroscience
related:
- '[[2209.07431--compositional-generalization-through-abstract-representations-human-artificial]]'
relationships:
- type: proposed_by
  target: '[[2209.07431--compositional-generalization-through-abstract-representations-human-artificial]]'
  target_id: paper:2209.07431
  confidence: high
---

The Concrete Permuted Rule Operations (C-PRO) paradigm is a 64-context compositional cognitive task that permutes 12 rules across three domains (logical decision, sensory/semantic, and motor response) to create a large space of novel task contexts. Four of the 64 contexts are practiced during training; the remaining 60 are held out as zero-shot compositional test contexts, making the paradigm a stringent test of whether learned rule representations generalize by composition rather than memorization. Data are collected from both human participants via fMRI (openneuro.org/datasets/ds003701) and artificial neural networks trained under matched conditions.

**Why it matters here:** C-PRO operationalizes the divide between systems that memorize context-specific patterns and those that form [[abstract-representations]] amenable to compositional reuse, a distinction that maps directly onto the question of whether epistemic representations in language models are context-rigid or flexibly composable.

**Lineage:** proposed in [[2209.07431--compositional-generalization-through-abstract-representations-human-artificial]]; the benchmark drove the development of [[primitives-pretraining]] as a training intervention and [[parallelism-score]] as the representation-geometry metric.
