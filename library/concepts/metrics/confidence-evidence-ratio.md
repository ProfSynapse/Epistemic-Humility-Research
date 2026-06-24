---
aliases:
- Phi metric
- CER
- confidence-evidence ratio
tags:
- kg/metric
- concept
- metric
kg:
  id: metric:confidence-evidence-ratio
  type: metric
  status: canonical
area: metrics
related:
- '[[2511.07477--epistemic-pathology-polite-liar]]'
- '[[calibration-humility-gap]]'
- '[[expected-calibration-error]]'
- '[[verbalized-confidence]]'
- '[[overconfidence]]'
- '[[hallucination]]'
relationships:
- type: proposed_by
  target: '[[2511.07477--epistemic-pathology-polite-liar]]'
  target_id: paper:2511.07477
  confidence: high
- type: related_to
  target: '[[calibration-humility-gap]]'
  target_id: term:calibration-humility-gap
  confidence: medium
- type: related_to
  target: '[[expected-calibration-error]]'
  target_id: metric:expected-calibration-error
  confidence: medium
- type: related_to
  target: '[[verbalized-confidence]]'
  target_id: method:verbalized-confidence
  confidence: medium
- type: related_to
  target: '[[overconfidence]]'
  target_id: term:overconfidence
  confidence: medium
- type: related_to
  target: '[[hallucination]]'
  target_id: term:hallucination
  confidence: medium
---

Phi = E[confidence] / E[evidence_support], where confidence is assertoric force in the model's output and evidence_support is proxied by retrieval overlap with authoritative sources or likelihood on grounded corpora. Phi approximately 1 is proportional confidence; Phi much greater than 1 is polite overreach; Phi much less than 1 is excessive diffidence.

**Why it matters here:** Provides a formal, computable operationalization of communicative epistemic humility that can be measured per output rather than only in aggregate, distinguishing overreach from diffidence with a single scalar.

**Lineage:** Proposed by DeVilling (2511.07477) §6.1 as a diagnostic for the polite-liar pathology. Not yet empirically validated in the paper; the paper treats it as a proposed metric.
