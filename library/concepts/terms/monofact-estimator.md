---
aliases:
- monofacts estimate
- MonoFacts
- fraction of singletons
- Good-Turing hallucination rate estimate
tags:
- kg/term
- concept
- term
kg:
  id: term:monofact-estimator
  type: term
  status: canonical
area: terms
related:
- '[[2311.14648--calibrated-lms-must-hallucinate]]'
- '[[hallucination]]'
- '[[calibration]]'
- '[[knowledge-boundary]]'
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
  target: '[[calibration]]'
  target_id: term:calibration
  confidence: medium
- type: related_to
  target: '[[knowledge-boundary]]'
  target_id: term:knowledge-boundary
  confidence: medium
---

The fraction of facts that appear exactly once in the training data, used as an estimator of the missing fact rate and hence as a lower bound on the LM hallucination rate for calibrated models under the factoid model of Kalai and Vempala (2023). It is the Good-Turing estimator applied to the factoid distribution: hat_p_U = |{y : y appears exactly once in training}| / n.

**Why it matters here:** Provides a computable, distribution-free lower bound on how often a calibrated pretrained LM must hallucinate on arbitrary facts, connecting the Good-Turing literature to empirical hallucination rates and giving a baseline to compare SFT, DPO, and KTO post-training effects against.

**Lineage:** Introduced by Kalai and Vempala (arXiv:2311.14648) as a renaming of the Good-Turing estimator (Good 1953) in the LM factoid context; Good-Turing concentration bounds proved by McAllester and Ortiz (2003) and refined in Appendix A of the same paper.
