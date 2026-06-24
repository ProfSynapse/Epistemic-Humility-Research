---
aliases:
- chain-of-thought monitorability
- reasoning monitorability
- CoT monitor accuracy
tags:
- kg/term
- concept
- term
kg:
  id: term:cot-monitorability
  type: term
  status: canonical
area: terms
related:
- '[[2512.00218--reasoning-under-pressure-monitorability]]'
- '[[hallucination]]'
- '[[knowledge-boundary]]'
- '[[generation-discrimination-gap]]'
- '[[reasoning-trace-collapse]]'
- '[[kl-divergence-penalty]]'
relationships:
- type: proposed_by
  target: '[[2512.00218--reasoning-under-pressure-monitorability]]'
  target_id: paper:2512.00218
  confidence: high
- type: related_to
  target: '[[hallucination]]'
  target_id: term:hallucination
  confidence: medium
- type: related_to
  target: '[[knowledge-boundary]]'
  target_id: term:knowledge-boundary
  confidence: medium
- type: related_to
  target: '[[generation-discrimination-gap]]'
  target_id: term:generation-discrimination-gap
  confidence: medium
- type: related_to
  target: '[[reasoning-trace-collapse]]'
  target_id: term:reasoning-trace-collapse
  confidence: medium
- type: related_to
  target: '[[kl-divergence-penalty]]'
  target_id: term:kl-divergence-penalty
  confidence: medium
---

The degree to which an external monitor can accurately predict a latent variable of interest from a reasoning model's chain-of-thought reasoning traces. Defined operationally as the accuracy of a monitor LLM prompted zero-shot to predict the latent variable given only the CoT; high monitorability means the CoT legibly encodes information about the latent even when the latent is not directly required for observed-variable prediction.

**Why it matters here:** If common training incentives degrade CoT monitorability, CoT-based safety monitoring of reasoning models becomes unreliable without additional safeguards. The paper establishes that ordinary incentives do not consistently degrade it, but adversarial optimization can.

**Lineage:** Introduced in MacDermott et al. 2025 (arXiv:2512.00218) as an empirical operationalization of CoT faithfulness concepts from prior work on ELK (Christiano et al. 2021) and CoT faithfulness (Turpin et al. 2023, Lanham et al. 2023).
