---
aliases:
- FA/AH/UH taxonomy
- three-way hallucination taxonomy
- knowledge-recall hallucination taxonomy
tags:
- kg/term
- concept
- term
kg:
  id: term:ah-uh-hallucination-taxonomy
  type: term
  status: canonical
area: terms
related:
- '[[2510.09033--probes-read-recall-not-truth]]'
- '[[associated-hallucination]]'
- '[[unassociated-hallucination]]'
- '[[hallucination]]'
- '[[causal-intervention]]'
- '[[knowledge-boundary]]'
- '[[estimator-divergence-invalidates-single-probe-faithfulness]]'
relationships:
- type: proposed_by
  target: '[[2510.09033--probes-read-recall-not-truth]]'
  target_id: paper:2510.09033
  confidence: high
- type: related_to
  target: '[[associated-hallucination]]'
  target_id: term:associated-hallucination
  confidence: medium
- type: related_to
  target: '[[unassociated-hallucination]]'
  target_id: term:unassociated-hallucination
  confidence: medium
- type: related_to
  target: '[[hallucination]]'
  target_id: term:hallucination
  confidence: medium
- type: related_to
  target: '[[causal-intervention]]'
  target_id: method:causal-intervention
  confidence: medium
- type: related_to
  target: '[[knowledge-boundary]]'
  target_id: term:knowledge-boundary
  confidence: medium
- type: related_to
  target: '[[estimator-divergence-invalidates-single-probe-faithfulness]]'
  target_id: mechanism:estimator-divergence-invalidates-single-probe-faithfulness
  confidence: medium
---

A three-category classification of LLM outputs on factual queries based on correctness and reliance on subject representation: Factual Associations (correct, subject-grounded), Associated Hallucinations (incorrect, but subject-grounded via spurious parametric associations), and Unassociated Hallucinations (incorrect, not grounded in subject parametric knowledge). Operationalized using causal mediation analysis to determine whether subject-representation interventions causally shift the output distribution.

**Why it matters here:** The taxonomy reveals that aggregating all hallucinations into a single category is the primary reason probe-based detectors appear to work in some settings but fail in others: detectability is not a property of hallucination in general but of hallucination type. It also implies that refusal tuning, detection probe training, and evaluation benchmarks must stratify by AH/UH membership to be interpretable.

**Lineage:** Proposed in Cheang et al. (2510.09033); builds on causal mediation analysis of knowledge recall (Geva et al. 2023, Meng et al. 2022) and on earlier recognition that confidence-based detectors conflate recall confidence with factual accuracy.
