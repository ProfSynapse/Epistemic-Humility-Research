---
aliases:
- TBG
- token before generating
- pre-generation token position
tags:
- kg/term
- concept
- term
kg:
  id: term:token-before-generating
  type: term
  status: canonical
area: terms
related:
- '[[2406.15927--semantic-entropy-probes]]'
- '[[semantic-entropy-probes]]'
- '[[residual-stream-activation]]'
- '[[self-knowledge]]'
- '[[knowledge-boundary]]'
relationships:
- type: proposed_by
  target: '[[2406.15927--semantic-entropy-probes]]'
  target_id: paper:2406.15927
  confidence: high
- type: related_to
  target: '[[semantic-entropy-probes]]'
  target_id: method:semantic-entropy-probes
  confidence: medium
- type: related_to
  target: '[[residual-stream-activation]]'
  target_id: term:residual-stream-activation
  confidence: medium
- type: related_to
  target: '[[self-knowledge]]'
  target_id: term:self-knowledge
  confidence: medium
- type: related_to
  target: '[[knowledge-boundary]]'
  target_id: term:knowledge-boundary
  confidence: medium
---

A probing position in SEP experiments: the hidden state at the last input token immediately before any generation begins. Reading SE from this position enables uncertainty estimation in a single forward pass with no generated tokens, earlier than the second-last-token (SLT) position.

**Why it matters here:** TBG probes show that SE is encoded before the model generates anything, suggesting epistemic uncertainty is a property of the prompt-encoding stage rather than only of the generation residual stream. This has implications for cost-free abstention gating.

**Lineage:** Defined and studied in 2406.15927 Section 4 and Figure 3.
