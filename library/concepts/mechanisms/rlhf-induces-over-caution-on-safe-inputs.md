---
aliases:
- RLHF safety training causes over-refusal of safe requests
- RLHF induces excessive hedging on innocuous inputs
- safety RLHF over-refusal
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:rlhf-induces-over-caution-on-safe-inputs
  type: mechanism
  status: canonical
cause: "Safety-focused [[reinforcement-learning-from-human-feedback]] training with underspecified labeler instructions"
effect: "Model becomes overly cautious on safe inputs: refusing innocuous requests or excessively hedging on questions that have clear answers"
polarity: enables
related:
- '[[2303.08774--gpt4-technical-report]]'
- '[[reinforcement-learning-from-human-feedback]]'
- '[[rule-based-reward-model]]'
- '[[over-hedging]]'
- '[[over-abstention]]'
- '[[safety-refusal]]'
- '[[rlhf-helpfulness-bias-suppresses-refusal]]'
- '[[sft-abstention-causes-over-refusal]]'
relationships:
- type: supported_by
  target: '[[2303.08774--gpt4-technical-report]]'
  target_id: paper:2303.08774
  confidence: high
- type: related_to
  target: '[[reinforcement-learning-from-human-feedback]]'
  target_id: method:reinforcement-learning-from-human-feedback
  confidence: high
- type: related_to
  target: '[[rule-based-reward-model]]'
  target_id: method:rule-based-reward-model
  confidence: high
- type: related_to
  target: '[[over-hedging]]'
  target_id: term:over-hedging
  confidence: high
- type: related_to
  target: '[[over-abstention]]'
  target_id: term:over-abstention
  confidence: high
- type: related_to
  target: '[[safety-refusal]]'
  target_id: term:safety-refusal
  confidence: high
- type: related_to
  target: '[[rlhf-helpfulness-bias-suppresses-refusal]]'
  target_id: mechanism:rlhf-helpfulness-bias-suppresses-refusal
  confidence: high
- type: related_to
  target: '[[sft-abstention-causes-over-refusal]]'
  target_id: mechanism:sft-abstention-causes-over-refusal
  confidence: high
---

When RLHF labeler instructions for safety are underspecified, the reward model cannot reliably distinguish genuinely harmful requests from sensitive-but-benign ones. The policy learns to hedge or refuse broadly as a safe default. OpenAI documents this in the GPT-4 Technical Report (arXiv:2303.08774, §6) and addresses it using [[rule-based-reward-model]] classifiers that provide an explicit penalty for over-refusal on guaranteed-safe prompts, targeting the symmetrical failure alongside under-refusal on harmful prompts. This mechanism is distinct from [[rlhf-helpfulness-bias-suppresses-refusal]] (which describes the failure to refuse out-of-knowledge-boundary questions) and from [[sft-abstention-causes-over-refusal]] (which describes SFT on abstention data overshooting): here the cause is safety-signal underspecification rather than abstention-training overfitting.
