---
aliases:
- declarative-knowledge advantage
- procedural-computation deficit
- declarative vs procedural gap in LLMs
tags:
- kg/term
- concept
- term
kg:
  id: term:declarative-procedural-accuracy-gap
  type: term
  status: canonical
area: terms
related:
- '[[2009.03300--mmlu-benchmark]]'
- '[[mmlu]]'
- '[[generation-discrimination-gap]]'
- '[[evidence-access-bottlenecks-expert-calibration]]'
- '[[calibration-humility-gap]]'
relationships:
- type: proposed_by
  target: '[[2009.03300--mmlu-benchmark]]'
  target_id: paper:2009.03300
  confidence: high
- type: related_to
  target: '[[mmlu]]'
  target_id: dataset:mmlu
  confidence: medium
- type: related_to
  target: '[[generation-discrimination-gap]]'
  target_id: term:generation-discrimination-gap
  confidence: medium
- type: related_to
  target: '[[evidence-access-bottlenecks-expert-calibration]]'
  target_id: mechanism:evidence-access-bottlenecks-expert-calibration
  confidence: medium
- type: related_to
  target: '[[calibration-humility-gap]]'
  target_id: term:calibration-humility-gap
  confidence: medium
---

The empirical pattern in which large autoregressive language models score substantially higher on questions requiring retrieval of factual or conceptual knowledge (declarative knowledge) than on questions requiring multi-step calculation or algorithm execution (procedural knowledge), even when the declarative questions are nominally harder by educational level.

**Why it matters here:** The gap implies that MMLU overall accuracy can obscure opposite failure modes: a model may be well-calibrated on recall-type questions and severely miscalibrated on calculation-heavy ones. Evaluations of calibration and abstention training should disaggregate by question type rather than relying on pooled benchmark scores.

**Lineage:** Documented empirically in Hendrycks et al. 2020 (arXiv:2009.03300) via GPT-3 subject-level analysis; conceptually related to the generation-discrimination gap and to evidence-access-bottlenecks-expert-calibration.
