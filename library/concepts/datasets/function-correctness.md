---
aliases:
- Function Correctness dataset
- code correctness dataset
tags:
- kg/dataset
- concept
- dataset
kg:
  id: dataset:function-correctness
  type: dataset
  status: canonical
area: datasets
related:
- '[[2512.00218--reasoning-under-pressure-monitorability]]'
- '[[cot-monitorability]]'
- '[[latent-variable-monitor-accuracy]]'
- '[[diamond-vault]]'
- '[[group-relative-policy-optimization]]'
relationships:
- type: proposed_by
  target: '[[2512.00218--reasoning-under-pressure-monitorability]]'
  target_id: paper:2512.00218
  confidence: high
- type: related_to
  target: '[[cot-monitorability]]'
  target_id: term:cot-monitorability
  confidence: medium
- type: related_to
  target: '[[latent-variable-monitor-accuracy]]'
  target_id: metric:latent-variable-monitor-accuracy
  confidence: medium
- type: related_to
  target: '[[diamond-vault]]'
  target_id: dataset:diamond-vault
  confidence: medium
- type: related_to
  target: '[[group-relative-policy-optimization]]'
  target_id: method:group-relative-policy-optimization
  confidence: medium
---

A code-evaluation dataset from Roger et al. (2023) in which each example contains a problem description, a Python function, and test cases. The observed variables are whether the test cases pass; the latent variable is whether the function is genuinely correct according to the problem description. Test cases are limited in scope so an incorrect function may pass them all, making the latent variable potentially independent of the observed ones.

**Why it matters here:** Tests CoT monitorability in a setting where the reasoner has no structural need to track the latent variable (function correctness) to predict the observed variable (test outcomes), providing a harder and more naturalistic probe of whether the CoT volunteers latent information.

**Lineage:** Originated in Roger et al. (2023) empirical ELK work; used in MacDermott et al. 2025 (arXiv:2512.00218) for monitorability experiments.
