---
aliases:
- binary-scoring incentivizes guessing
- IDK-penalizing evaluation reinforces overconfidence
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:binary-grading-reinforces-hallucination
  type: mechanism
  status: canonical
cause: "Benchmark evaluations that use binary grading (0/1 for correct/wrong, 0 for IDK)"
effect: "Models learn that IDK responses are strictly suboptimal, reinforcing overconfident hallucination over calibrated abstention"
polarity: enables
related:
- '[[2509.04664--why-language-models-hallucinate]]'
- '[[hallucination]]'
- '[[overconfidence]]'
- '[[abstention]]'
- '[[over-abstention]]'
- '[[iiv-reduction]]'
- '[[confidence-target-scoring]]'
relationships:
- type: supported_by
  target: '[[2509.04664--why-language-models-hallucinate]]'
  target_id: paper:2509.04664
  confidence: high
- type: related_to
  target: '[[hallucination]]'
  target_id: term:hallucination
  confidence: high
- type: related_to
  target: '[[overconfidence]]'
  target_id: term:overconfidence
  confidence: high
- type: related_to
  target: '[[abstention]]'
  target_id: term:abstention
  confidence: high
- type: related_to
  target: '[[over-abstention]]'
  target_id: term:over-abstention
  confidence: high
- type: related_to
  target: '[[iiv-reduction]]'
  target_id: method:iiv-reduction
  confidence: high
- type: related_to
  target: '[[confidence-target-scoring]]'
  target_id: method:confidence-target-scoring
  confidence: high
---

Observation 1 (Section 4.1) proves that under any binary grading rubric and any belief distribution over correct answers, the optimal response is never an abstention. Table 2 shows 9 of 10 surveyed benchmarks use binary grading; the one exception (WildBench) gives partial credit but its rubric may still score IDK (3-4/10) below a hallucinated response (5-6/10). Because post-training optimizes for leaderboard performance, this creates a systemic incentive for guessing over uncertainty expression.
