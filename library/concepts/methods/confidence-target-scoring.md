---
aliases:
- explicit confidence target
- penalty-weighted grading
- t/(1-t) penalty scoring
tags:
- kg/method
- concept
- method
kg:
  id: method:confidence-target-scoring
  type: method
  status: canonical
area: methods
related:
- '[[2509.04664--why-language-models-hallucinate]]'
- '[[abstention]]'
- '[[overconfidence]]'
- '[[calibration]]'
- '[[hallucination]]'
- '[[over-abstention]]'
relationships:
- type: proposed_by
  target: '[[2509.04664--why-language-models-hallucinate]]'
  target_id: paper:2509.04664
  confidence: high
- type: related_to
  target: '[[abstention]]'
  target_id: term:abstention
  confidence: medium
- type: related_to
  target: '[[overconfidence]]'
  target_id: term:overconfidence
  confidence: medium
- type: related_to
  target: '[[calibration]]'
  target_id: term:calibration
  confidence: medium
- type: related_to
  target: '[[hallucination]]'
  target_id: term:hallucination
  confidence: medium
- type: related_to
  target: '[[over-abstention]]'
  target_id: term:over-abstention
  confidence: medium
---

An evaluation protocol that appends an explicit confidence threshold t to each benchmark question prompt and penalizes wrong answers by t/(1-t) points while awarding 1 point for correct answers and 0 for IDK; answering is then optimal only when the model's correctness probability exceeds t. Running benchmarks at multiple t values (e.g., 0.5, 0.75, 0.9) converts binary leaderboard evaluations into hallucination-sensitive evaluations without replacing them.

**Why it matters here:** Addresses the benchmark-alignment problem identified in Section 4.1 by making abstention strictly optimal below a stated confidence threshold, removing the structural incentive for overconfident guessing that binary grading creates.

**Lineage:** Proposed in Section 4.2 of this paper; cites earlier work on standardized exams with penalties (Indian JEE, AMC, SAT/GRE) and Wu et al. (2025) risk-informing prompts as partial precedents.
