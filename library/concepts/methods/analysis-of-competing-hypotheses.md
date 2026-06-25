---
aliases:
- Analysis of Competing Hypotheses
- ACH
tags:
- kg/method
- concept
- method
kg:
  id: method:analysis-of-competing-hypotheses
  type: method
  status: canonical
area: methods
related:
- '[[2606.26071--model-forensics-investigating-whether-concerning-behavior-reflects]]'
- '[[model-forensics-two-step-protocol]]'
relationships:
- type: related_to
  target: '[[2606.26071--model-forensics-investigating-whether-concerning-behavior-reflects]]'
  target_id: paper:2606.26071
  confidence: high
- type: related_to
  target: '[[model-forensics-two-step-protocol]]'
  target_id: method:model-forensics-two-step-protocol
  confidence: medium
---

A structured analytic technique that lays out rival hypotheses as columns and evidence items as rows, scoring whether each piece of evidence is consistent or inconsistent with each hypothesis, and favoring the hypothesis with the fewest inconsistencies rather than the one with the most supporting evidence.

**Why it matters here:** it disciplines the attribution step of model forensics, forcing explicit consideration of benign explanations (confusion, rationalization) alongside misalignment rather than confirming a single favored story.

**Lineage:** from intelligence analysis (Heuer 1999); applied here to the Pre-commit Hook investigation (Table 1) to weigh "rationalized as acceptable" against "adversarially misaligned".
