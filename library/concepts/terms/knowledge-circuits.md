---
aliases:
- knowledge circuit
- knowledge subgraph
tags:
- kg/term
- concept
- term
kg:
  id: term:knowledge-circuits
  type: term
  status: canonical
area: mechanistic-interpretability
related:
- '[[2405.17969--knowledge-circuits-pretrained-transformers]]'
- '[[automated-circuit-discovery]]'
- '[[knowledge-circuit-isolation-preserves-performance]]'
- '[[sparse-feature-circuits]]'
relationships:
- type: proposed_by
  target: '[[2405.17969--knowledge-circuits-pretrained-transformers]]'
  target_id: paper:2405.17969
  confidence: high
- type: derived_from
  target: '[[automated-circuit-discovery]]'
  target_id: method:automated-circuit-discovery
- type: related_to
  target: '[[knowledge-circuit-isolation-preserves-performance]]'
  target_id: mechanism:knowledge-circuit-isolation-preserves-performance
- type: related_to
  target: '[[sparse-feature-circuits]]'
  target_id: method:sparse-feature-circuits
---

A knowledge circuit is a critical subgraph of a language model's computation graph (the DAG of attention heads, MLPs, and embeddings) that is causally responsible for expressing and recalling a specific piece of knowledge. Knowledge circuits are discovered by systematically ablating edges and measuring prediction degradation, then validated by showing the isolated subgraph reproduces the full model's output distribution for the target fact. They extend general circuit-discovery methodology to the domain of factual knowledge.

**Why it matters here:** Knowledge circuits provide a mechanistic account of where and how facts are stored and retrieved, which grounds interventions for correcting, suppressing, or auditing specific beliefs and thus bears directly on hallucination, knowledge-boundary enforcement, and honest uncertainty expression.

**Lineage:** proposed in [[2405.17969--knowledge-circuits-pretrained-transformers]]; derives from [[automated-circuit-discovery]] as the general circuit-extraction methodology; validated by [[knowledge-circuit-isolation-preserves-performance]]; related to [[sparse-feature-circuits]] which extends circuit analysis to SAE-level features.
