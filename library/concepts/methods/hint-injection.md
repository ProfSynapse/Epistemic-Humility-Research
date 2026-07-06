---
aliases:
- misleading-hint evaluation
- hint-injection faithfulness test
- Hint-Injection Methodology
tags:
- kg/method
- concept
- method
kg:
  id: method:hint-injection
  type: method
  status: canonical
area: verification
related: []
relationships: []
---

Hint injection is an evaluation protocol in which questions from knowledge benchmarks are paired with one of several types of misleading contextual cues (sycophantic agreement signals, consistency prompts, unethical suggestions, or authority appeals) before being administered to the model under test. The model's response is then classified for whether the hint influenced the final answer and whether the hint was explicitly verbalized in the reasoning trace or answer text. By varying hint type and model family, the protocol produces a controlled measurement of both sycophancy susceptibility and reasoning faithfulness. The [[four-quadrant-hint-taxonomy]] is the standard classification scheme applied to hint-injection outputs.

**Why it matters here:** Hint injection operationalizes the epistemic failure mode in which external social pressure overrides a model's internally represented knowledge, providing a direct behavioral probe of the gap between latent uncertainty and expressed confidence.

**Lineage:** none; the [[four-quadrant-hint-taxonomy]] derives from this method.
