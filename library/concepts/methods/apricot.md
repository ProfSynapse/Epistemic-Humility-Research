---
aliases:
- APRICOT
- Auxiliary Prediction of Confidence Targets
tags:
- kg/method
- concept
- method
kg:
  id: method:apricot
  type: method
  status: canonical
area: methods
related:
- '[[2403.05973--calibrating-large-language-models-using-their-generations]]'
- '[[clustering-derived-calibration-target]]'
- '[[surrogate-confidence-estimation]]'
- '[[verbalized-confidence]]'
- '[[expected-calibration-error]]'
- '[[confidnet]]'
relationships:
- type: proposed_by
  target: '[[2403.05973--calibrating-large-language-models-using-their-generations]]'
  target_id: paper:2403.05973
  confidence: high
- type: related_to
  target: '[[clustering-derived-calibration-target]]'
  target_id: method:clustering-derived-calibration-target
  confidence: high
- type: related_to
  target: '[[surrogate-confidence-estimation]]'
  target_id: method:surrogate-confidence-estimation
  confidence: high
- type: related_to
  target: '[[verbalized-confidence]]'
  target_id: method:verbalized-confidence
  confidence: medium
---

APRICOT (Auxiliary Prediction of Confidence Targets) is a black-box
LLM-calibration method: (1) prompt the target LLM to generate answers for a
question set; (2) set per-cluster calibration targets by clustering an embedding
model's question representations (HDBSCAN over normalized SentenceBERT
embeddings) and taking each cluster's observed accuracy; (3) finetune a separate
small auxiliary model (DeBERTaV3) on the (question, generated-answer) text alone
to regress those targets via MSE. The predicted confidence needs no logits,
sequence likelihoods, or internal states, and can be verbalized or used to adjust
the answer.

**Why it matters here:** It is the canonical LLM-specific auxiliary calibrator —
the deliberately external/black-box contrast to the experiment's internal-state
readout head. It shows a trained auxiliary head can recover competitive
calibration and the best misprediction AUROC from text alone, framing the
question of how much an internal-state head adds over a generations-only one.

**Lineage:** Ulmer et al. 2024; extends Mielke et al. 2022 (white-box
hidden-state calibrator) by removing model access and using
[[clustering-derived-calibration-target]]; an LLM-era sibling of [[confidnet]].
