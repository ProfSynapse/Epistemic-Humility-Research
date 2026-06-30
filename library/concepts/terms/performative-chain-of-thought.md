---
aliases:
- performative CoT
- performative reasoning
- reasoning theater
- Performative Chain-of-Thought
tags:
- kg/term
- concept
- term
kg:
  id: term:performative-chain-of-thought
  type: term
  status: canonical
area: verification
related:
- '[[chain-of-thought-faithfulness]]'
relationships:
- type: derived_from
  target: '[[chain-of-thought-faithfulness]]'
  target_id: term:chain-of-thought-faithfulness
---

A performative chain-of-thought is a mismatch between a model's internal belief
state and its emitted reasoning tokens: the model is already strongly confident
in a final answer but continues generating chain-of-thought without disclosing
that confidence, producing reasoning that is unfaithful to its actual
deliberation. The pattern is detected empirically by tracking when an internal
probe (e.g., an attention probe on hidden states) commits to a final answer much
earlier in the sequence than the model's emitted tokens reveal that commitment.

**Why it matters here:** Performative CoT is a direct calibration failure: a
model that has internally resolved a question yet still performs visible
uncertainty is misrepresenting its epistemic state, which undermines the
reliability of stated uncertainty as a signal for downstream use.

**Lineage:** derived from [[chain-of-thought-faithfulness]], which is the broader
construct of whether emitted reasoning tracks internal computation.
