---
aliases:
- arbitrary facts
- systematic facts
- arbitrary factoids
- 5W factoids
- rule-governed facts
tags:
- kg/term
- concept
- term
kg:
  id: term:arbitrary-vs-systematic-facts
  type: term
  status: canonical
area: terms
related:
- '[[2311.14648--calibrated-lms-must-hallucinate]]'
- '[[hallucination]]'
- '[[knowledge-boundary]]'
- '[[monofact-estimator]]'
relationships:
- type: proposed_by
  target: '[[2311.14648--calibrated-lms-must-hallucinate]]'
  target_id: paper:2311.14648
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
  target: '[[monofact-estimator]]'
  target_id: term:monofact-estimator
  confidence: medium
---

A distinction between two classes of facts in the Kalai-Vempala (2023) hallucination framework. Arbitrary facts (e.g., 5W factoids: who ate what when where why) are facts whose truth cannot be determined from training data alone by learning underlying rules; their missing mass is governed by the monofact rate and calibrated LMs must hallucinate on them. Systematic facts (e.g., arithmetic inequalities) can be determined by learnable rules; there is no statistical necessity for calibrated LMs to hallucinate on them.

**Why it matters here:** The distinction determines which facts are subject to the monofact lower bound and which are not, motivating stratified evaluation of training arms by fact type and explaining why reference hallucinations may require capacity-based rather than calibration-based interventions.

**Lineage:** Introduced by Kalai and Vempala (arXiv:2311.14648), Sections 1 and 4, building on the notion of missing mass from Good (1953).
