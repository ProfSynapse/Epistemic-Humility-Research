---
aliases:
- Diamond Vault dataset
- vault dataset
tags:
- kg/dataset
- concept
- dataset
kg:
  id: dataset:diamond-vault
  type: dataset
  status: canonical
area: datasets
related:
- '[[2512.00218--reasoning-under-pressure-monitorability]]'
- '[[cot-monitorability]]'
- '[[latent-variable-monitor-accuracy]]'
- '[[function-correctness]]'
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
  target: '[[function-correctness]]'
  target_id: dataset:function-correctness
  confidence: medium
- type: related_to
  target: '[[group-relative-policy-optimization]]'
  target_id: method:group-relative-policy-optimization
  confidence: medium
---

A code-reading dataset from Roger et al. (2023) in which each example is a Python snippet involving a Vault, a Diamond, a protector, and a robber. The observed variables are sensor measurements (max_shine, max_hardness, diamond string presence); the latent variable is whether the diamond is actually in the vault. Sensor measurements and diamond presence can be decoupled because the robber may replace the diamond with a fake or tamper with sensors.

**Why it matters here:** Provides a controlled ELK-style setting where reasoning about a latent variable is useful but not strictly necessary to predict the observed variables, enabling measurement of CoT monitorability with known ground truth labels for the latent.

**Lineage:** Originated in Roger et al. (2023) empirical ELK work; used in MacDermott et al. 2025 (arXiv:2512.00218) for monitorability experiments.
