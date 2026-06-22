---
aliases:
- attribute extraction mechanism
- three-step internal mechanism
- Three-Step Factual Recall Mechanism
tags:
- kg/term
- concept
- term
kg:
  id: term:factual-association-recall-mechanism
  type: term
  status: canonical
area: mechanistic-interpretability
related:
- '[[2304.14767--dissecting-recall-factual-associations]]'
- '[[subject-enrichment]]'
- '[[mover-head]]'
- '[[factual-recall-localization]]'
- '[[residual-stream]]'
relationships:
- type: proposed_by
  target: '[[2304.14767--dissecting-recall-factual-associations]]'
  target_id: paper:2304.14767
  confidence: high
- type: related_to
  target: '[[subject-enrichment]]'
  target_id: term:subject-enrichment
- type: related_to
  target: '[[mover-head]]'
  target_id: term:mover-head
- type: related_to
  target: '[[factual-recall-localization]]'
  target_id: term:factual-recall-localization
- type: related_to
  target: '[[residual-stream]]'
  target_id: term:residual-stream
---

The factual-association recall mechanism is a three-step internal process for fact completion in autoregressive language models, identified by Hernandez et al. (2023). Step 1: early MLP sublayers enrich the last-subject-token position with subject-related attributes ([[subject-enrichment]]). Step 2: the relation token propagates to the prediction position via the residual stream. Step 3: upper multi-head self-attention heads use the relation to query the enriched subject representation and extract the target factual attribute, with subject-attribute mappings encoded in their parameters.

**Why it matters here:** This mechanism frames where factual knowledge resides and how it is retrieved, informing intervention points for editing, suppressing, or auditing model knowledge, which is directly relevant to calibration, knowledge-boundary awareness, and hallucination prevention.

**Lineage:** introduced in [[2304.14767--dissecting-recall-factual-associations]]; component terms include [[subject-enrichment]] and [[mover-head]]; related to [[factual-recall-localization]] established by ROME (2202.05262) and [[knowledge-circuits]] (2405.17969).
