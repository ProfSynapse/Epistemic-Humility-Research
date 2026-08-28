---
aliases:
- Gemma-2-2B
- Gemma 2 2B
- google/gemma-2-2b
tags:
- kg/model
- concept
- model
kg:
  id: model:gemma-2-2b
  type: model
  status: canonical
area: models
related:
- '[[2607.19317--circuitkit-circuit-discovery-evaluation-application-toolkit-mechanistic]]'
- '[[gemma-3-12b]]'
relationships:
- type: studied_by
  target: '[[2607.19317--circuitkit-circuit-discovery-evaluation-application-toolkit-mechanistic]]'
  target_id: paper:2607.19317
  confidence: high
- type: related_to
  target: '[[gemma-3-12b]]'
  target_id: model:gemma-3-12b
  confidence: medium
---

Gemma-2-2B is a two-billion-parameter Google language model with rotary embeddings, a gated MLP, and logit soft-capping. CircuitKIT includes it in the six-family EAP-IG discovery study on IOI and Greater-Than.

**Why it matters here:** Its low hard-ablation sufficiency on IOI despite perfect soft-patching recovery illustrates why circuit validity should be assessed with more than one intervention model.

**Lineage:** A Gemma 2 family model, related to the later [[gemma-3-12b]] atom already used in the library.
