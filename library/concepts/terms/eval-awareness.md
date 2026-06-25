---
aliases:
- Evaluation awareness
- Eval awareness
tags:
- kg/term
- concept
- term
kg:
  id: term:eval-awareness
  type: term
  status: canonical
area: terms
related:
- '[[2606.26071--model-forensics-investigating-whether-concerning-behavior-reflects]]'
- '[[cot-monitorability]]'
relationships:
- type: proposed_by
  target: '[[2606.26071--model-forensics-investigating-whether-concerning-behavior-reflects]]'
  target_id: paper:2606.26071
  confidence: high
- type: related_to
  target: '[[cot-monitorability]]'
  target_id: term:cot-monitorability
  confidence: medium
---

A model's recognition that it is being tested, which can confound a forensic investigation: an eval-aware model may subvert a misalignment test, or (in "reverse" eval awareness) deliberately take the tested-for action. It is one of several benign explanations that must be ruled out before attributing behavior to misalignment.

**Why it matters here:** it is a key confound for negative results in model forensics, where a model's failure to behave as a hypothesis predicts may reflect eval awareness rather than the absence of the hypothesized motive.

**Lineage:** discussed alongside capability limits and competing motivations as confounds (Section 7); reverse eval awareness has been observed in Gemini models (Lindner et al. 2026).
