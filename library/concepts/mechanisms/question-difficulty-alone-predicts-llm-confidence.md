---
aliases:
- Question difficulty alone already predicts LLM confidence
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:question-difficulty-alone-predicts-llm-confidence
  type: mechanism
  status: canonical
cause: "Training the auxiliary calibrator on the question text only, with the LLM's generated answer omitted."
effect: "The calibrator already attains respectable calibration and AUROC by inferring difficulty from question type; adding the answer and chain-of-thought improves it further, and verbalized uncertainty can additionally lower calibration error."
polarity: enables
related:
- '[[2403.05973--calibrating-large-language-models-using-their-generations]]'
- '[[apricot]]'
- '[[verbalized-confidence]]'
relationships:
- type: supported_by
  target: '[[2403.05973--calibrating-large-language-models-using-their-generations]]'
  target_id: paper:2403.05973
  confidence: high
- type: related_to
  target: '[[apricot]]'
  target_id: method:apricot
  confidence: high
- type: related_to
  target: '[[verbalized-confidence]]'
  target_id: method:verbalized-confidence
  confidence: medium
---

Ulmer et al. 2024's input-ablation study finds the calibrator already performs
respectably from the question alone (inferring per-question-type difficulty), with
further gains from adding the generated answer and chain-of-thought, and
occasional ECE improvement when also given the LLM's verbalized uncertainty
(Section 4.3, Table 8).
