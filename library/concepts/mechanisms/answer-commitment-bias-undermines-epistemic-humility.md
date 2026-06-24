---
aliases:
- Answer-Commitment Bias Undermines False-Option Rejection
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:answer-commitment-bias-undermines-epistemic-humility
  type: mechanism
  status: canonical
cause: A learned bias toward always selecting one of the presented answer options, reinforced by recognition-focused training and evaluation that reward picking a listed choice
effect: Failure of false-option rejection; high recognition accuracy coexists with low NOTA hit rate, and NOTA-only accuracy drops to near random (26.61% avg) while humans score 92%
polarity: decreases
related:
- '[[2509.09658--humblebench-epistemic-humility-multimodal]]'
- '[[false-option-rejection]]'
- '[[epistemic-humility]]'
- '[[multimodal-large-language-model]]'
- '[[hallucination]]'
relationships:
- type: supported_by
  target: '[[2509.09658--humblebench-epistemic-humility-multimodal]]'
  target_id: paper:2509.09658
  confidence: high
- type: related_to
  target: '[[false-option-rejection]]'
  target_id: term:false-option-rejection
- type: related_to
  target: '[[epistemic-humility]]'
  target_id: term:epistemic-humility
- type: related_to
  target: '[[multimodal-large-language-model]]'
  target_id: term:multimodal-large-language-model
- type: related_to
  target: '[[hallucination]]'
  target_id: term:hallucination
---

MLLMs trained and evaluated on standard multiple-choice recognition learn that a
listed option is essentially always correct, so they develop a strong prior to
commit to one of the presented answers. HumbleBench (arXiv:2509.09658) exposes this
by inserting a "None of the above" option and building a NOTA-only stress setting
where every listed answer is removed: average NOTA-only accuracy falls to 26.61%,
close to random, even though a human annotator on the same subset scores 92.00%.
The gap between non-NOTA accuracy and NOTA hit rate confirms the bias is not a
recognition deficit but a refusal-to-abstain one, e.g. Qwen2.5-VL reaches 78.98%
non-NOTA accuracy yet only a 32.33% NOTA hit rate. Cautious prompting shifts the
operating point toward NOTA but trades away recognition accuracy rather than
fixing the underlying commitment bias.
