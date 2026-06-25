---
aliases:
- Repeated resampling
- Repeated rejection resampling
tags:
- kg/method
- concept
- method
kg:
  id: method:repeated-resampling
  type: method
  status: canonical
area: methods
related:
- '[[2606.26071--model-forensics-investigating-whether-concerning-behavior-reflects]]'
- '[[sentence-resampling]]'
relationships:
- type: related_to
  target: '[[2606.26071--model-forensics-investigating-whether-concerning-behavior-reflects]]'
  target_id: paper:2606.26071
  confidence: high
- type: related_to
  target: '[[sentence-resampling]]'
  target_id: method:sentence-resampling
  confidence: high
---

An intervention that repeatedly resamples a model's generation to suppress a targeted class of sentences (for example, sentences in which the model identifies with a previous instance of itself), then measures the resulting change in behavior. Suppressing self-consistency sentences dropped DeepSeek R1 0528's deception rate from 46.9% to 27.5% (p = 0.01).

**Why it matters here:** it converts a correlational sentence-importance signal into causal evidence by removing the candidate driver and observing the effect.

**Lineage:** introduced by Macar et al. 2025; builds on [[sentence-resampling]] (which measures influence) by acting on it.
