---
aliases:
- QM9
tags:
- kg/dataset
- concept
- dataset
kg:
  id: dataset:qm9
  type: dataset
  status: canonical
area: datasets
related:
- '[[2402.07148--x-lora-mixture-low-rank-adapter-experts]]'
relationships:
- type: proposed_by
  target: '[[2402.07148--x-lora-mixture-low-rank-adapter-experts]]'
  target_id: paper:2402.07148
  confidence: medium
---

QM9 is a molecular dataset with quantum-mechanical properties such as dipole moment, polarizability, orbital energies, thermodynamic quantities, and spatial extent. X-LoRA-Gemma uses it for property prediction and inverse molecular design.

**Why it matters here:** It supplies a quantitative domain task for testing hidden-state-driven adapter routing.

**Lineage:** The dataset predates X-LoRA and is reused as one of its scientific expert domains.
