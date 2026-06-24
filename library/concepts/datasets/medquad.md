---
aliases:
- MedQuad
- MEDQuad
- Comprehensive Medical Q&A Dataset
tags:
- kg/dataset
- concept
- dataset
kg:
  id: dataset:medquad
  type: dataset
  status: canonical
area: datasets
related:
- '[[2502.08177--syceval]]'
- '[[amps-math]]'
- '[[sycophancy]]'
- '[[progressive-regressive-sycophancy-taxonomy]]'
relationships:
- type: proposed_by
  target: '[[2502.08177--syceval]]'
  target_id: paper:2502.08177
  confidence: high
- type: related_to
  target: '[[amps-math]]'
  target_id: dataset:amps-math
  confidence: medium
- type: related_to
  target: '[[sycophancy]]'
  target_id: term:sycophancy
  confidence: medium
- type: related_to
  target: '[[progressive-regressive-sycophancy-taxonomy]]'
  target_id: term:progressive-regressive-sycophancy-taxonomy
  confidence: medium
---

A dataset of over 43,000 patient medical inquiries from real-life situations, categorized into 31 question types including susceptibility, symptoms, prevention, and frequency. Ben Abacha and Demner-Fushman (2019) assembled it from structured medical sources. SycEval samples 500 pairs for sycophancy evaluation.

**Why it matters here:** Represents a high-stakes open-ended domain where regressive sycophancy carries direct patient-harm risk. Its open-ended answer structure produces more uniform sycophancy across rebuttal contexts compared to the structured AMPS domain, revealing that domain type moderates susceptibility to anticipatory framing.

**Lineage:** Ben Abacha and Demner-Fushman (2019), BMC Bioinformatics; used in SycEval (2502.08177) as the medical-advice evaluation split.
