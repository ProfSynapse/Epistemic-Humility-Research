---
aliases:
- prompts fail to induce abstention
- gradient-baked always-answer prior
- structural abstention failure
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:prompt-cannot-override-rlvr-abstention-deficit
  type: mechanism
  status: canonical
cause: "RLVR training with binary rewards (+1 correct, 0 wrong) that treat abstention as failure, repeated across thousands of training steps"
effect: "The resulting always-answer prior is impervious to inference-time prompts that explicitly instruct abstention and warn of severe penalties, leaving frontier models abstaining less than 1% of the time even at lambda=100"
polarity: prevents
related:
- '[[2511.11500--reinforced-hesitation]]'
- '[[rlvr-post-training-degrades-abstention]]'
- '[[reasoning-finetuning-degrades-abstention]]'
- '[[binary-grading-reinforces-hallucination]]'
- '[[abstention]]'
- '[[reinforced-hesitation]]'
relationships:
- type: supported_by
  target: '[[2511.11500--reinforced-hesitation]]'
  target_id: paper:2511.11500
  confidence: high
- type: related_to
  target: '[[rlvr-post-training-degrades-abstention]]'
  target_id: mechanism:rlvr-post-training-degrades-abstention
  confidence: high
- type: related_to
  target: '[[reasoning-finetuning-degrades-abstention]]'
  target_id: mechanism:reasoning-finetuning-degrades-abstention
  confidence: high
- type: related_to
  target: '[[binary-grading-reinforces-hallucination]]'
  target_id: mechanism:binary-grading-reinforces-hallucination
  confidence: high
- type: related_to
  target: '[[abstention]]'
  target_id: term:abstention
  confidence: high
- type: related_to
  target: '[[reinforced-hesitation]]'
  target_id: method:reinforced-hesitation
  confidence: high
---

Evaluated on GSM8K, MedQA, and GPQA with 11 frontier models and 5 penalty conditions (lambda in {1, 5, 25, 100} plus baseline), Section 2 of the RH paper finds abstention rates near zero across all models and penalty magnitudes. MedQA yields exactly zero abstentions across all 11 models and all conditions on 1,273 questions. Reasoning-tuned models (Gemini 2.5 Pro, Kimi-K2, DeepSeek-Reasoner) show no advantage and some accuracy degradation under higher penalties, suggesting that accuracy-maximization at training time overrides epistemic signals at inference time. The mechanism is consistent with gradient dominance: thousands of training steps that reward guessing create a prior that a single-prompt instruction cannot overcome.
