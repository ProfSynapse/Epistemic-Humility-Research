---
aliases:
- confidence comparison task
- relative confidence ranking
- pairwise metacognitive task
tags:
- kg/method
- concept
- method
kg:
  id: method:pairwise-confidence-comparison
  type: method
  status: canonical
area: methods
related:
- '[[2510.05126--metacognition-uncertainty-communication]]'
- '[[verbalized-confidence]]'
- '[[consistency-based-confidence]]'
- '[[confidence-elicitation]]'
- '[[auroc]]'
- '[[selective-classification-auc]]'
- '[[generation-discrimination-gap]]'
relationships:
- type: proposed_by
  target: '[[2510.05126--metacognition-uncertainty-communication]]'
  target_id: paper:2510.05126
  confidence: high
- type: related_to
  target: '[[verbalized-confidence]]'
  target_id: method:verbalized-confidence
  confidence: medium
- type: related_to
  target: '[[consistency-based-confidence]]'
  target_id: method:consistency-based-confidence
  confidence: medium
- type: related_to
  target: '[[confidence-elicitation]]'
  target_id: method:confidence-elicitation
  confidence: medium
- type: related_to
  target: '[[auroc]]'
  target_id: metric:auroc
  confidence: medium
- type: related_to
  target: '[[selective-classification-auc]]'
  target_id: metric:selective-classification-auc
  confidence: medium
- type: related_to
  target: '[[generation-discrimination-gap]]'
  target_id: term:generation-discrimination-gap
  confidence: medium
---

A metacognitive task format in which an LLM is presented with two questions simultaneously and asked to select which one it is more likely to answer correctly, before or alongside providing answers to both. Discrimination is evaluated via AUCc (agreement with consistency-based reference ranking) and AUCa (agreement with actual answer correctness on mixed-outcome pairs).

**Why it matters here:** Provides a format-agnostic test of metacognitive discrimination that does not require numeric confidence output, paralleling forced-choice paradigms in human metacognition research; reveals whether calibration improvements learned in numeric estimation transfer to relative judgment, and vice versa.

**Lineage:** Analogous to the forced-choice confidence paradigm in human metacognitive research; formalized as a supervised fine-tuning target in Steyvers et al. (2025) alongside single-question confidence estimation.
