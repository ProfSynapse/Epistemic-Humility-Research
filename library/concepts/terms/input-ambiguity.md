---
aliases:
- prompt ambiguity
- U_input
- input uncertainty
tags:
- kg/term
- concept
- term
kg:
  id: term:input-ambiguity
  type: term
  status: canonical
area: terms
related:
- '[[2603.24967--uncertainty-source-decomposition]]'
- '[[uncertainty-source-decomposition]]'
- '[[decoding-randomness]]'
- '[[knowledge-gap]]'
- '[[hallucination]]'
- '[[calibration]]'
- '[[verbalized-confidence]]'
relationships:
- type: proposed_by
  target: '[[2603.24967--uncertainty-source-decomposition]]'
  target_id: paper:2603.24967
  confidence: high
- type: related_to
  target: '[[uncertainty-source-decomposition]]'
  target_id: method:uncertainty-source-decomposition
  confidence: medium
- type: related_to
  target: '[[decoding-randomness]]'
  target_id: term:decoding-randomness
  confidence: medium
- type: related_to
  target: '[[knowledge-gap]]'
  target_id: term:knowledge-gap
  confidence: medium
- type: related_to
  target: '[[hallucination]]'
  target_id: term:hallucination
  confidence: medium
- type: related_to
  target: '[[calibration]]'
  target_id: term:calibration
  confidence: medium
- type: related_to
  target: '[[verbalized-confidence]]'
  target_id: method:verbalized-confidence
  confidence: medium
---

A component of LLM uncertainty arising from vagueness or underspecification in the input prompt, measured as semantic disagreement across K semantically equivalent paraphrases of the same question. High input ambiguity indicates that the prompt, rather than the model's knowledge or sampling strategy, is the primary source of output variability.

**Why it matters here:** For larger models on factual QA tasks, input ambiguity is the dominant failure predictor (AUROC 0.761 for Gemma 3 27B on TriviaQA), suggesting that prompt engineering or clarification requests are the highest-leverage intervention at scale.

**Lineage:** Defined as U_input in Taparia et al. 2026 (arXiv:2603.24967). Related to the generation-discrimination-gap literature in that models may correctly read uncertainty from ambiguous prompts without expressing it in outputs.
