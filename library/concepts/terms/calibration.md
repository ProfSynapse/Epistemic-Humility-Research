---
aliases:
- calibrated predictions
- probabilistic calibration
- confidence calibration
- model calibration
tags:
- kg/term
- concept
- term
kg:
  id: term:calibration
  type: term
  status: canonical
area: terms
---

Calibration is the property that a model's stated probability for an event matches the empirical frequency with which that event occurs. A perfectly calibrated model that assigns 70% confidence to a set of predictions is correct on approximately 70% of those predictions. In the LLM context, calibration is typically measured via Expected Calibration Error (ECE), Brier score, or reliability diagrams across bucketed confidence levels.

**Why it matters here:** The SFT-vs-DPO-vs-KTO abstention study relies on calibration as a foundational concept: a model that abstains on unknowns but is miscalibrated in its confidence estimates may over-hedge on known answers or under-hedge on hallucinated ones, so calibration quality shapes how meaningful the [[abstention-rate]] signal is.

**Lineage:** instantiated in practice via [[expected-calibration-error]] and [[brier-score]]; [[verbalized-confidence]] is a complementary measure when logit-based probabilities are unavailable.
