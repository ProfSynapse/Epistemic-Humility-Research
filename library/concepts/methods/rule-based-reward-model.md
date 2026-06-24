---
aliases:
- RBRM
- rule-based reward models
- zero-shot RLHF classifier
tags:
- kg/method
- concept
- method
kg:
  id: method:rule-based-reward-model
  type: method
  status: canonical
area: methods
related:
- '[[2303.08774--gpt4-technical-report]]'
- '[[reinforcement-learning-from-human-feedback]]'
- '[[reward-model]]'
- '[[safety-refusal]]'
- '[[over-hedging]]'
- '[[over-abstention]]'
relationships:
- type: proposed_by
  target: '[[2303.08774--gpt4-technical-report]]'
  target_id: paper:2303.08774
  confidence: high
- type: related_to
  target: '[[reinforcement-learning-from-human-feedback]]'
  target_id: method:reinforcement-learning-from-human-feedback
  confidence: medium
- type: related_to
  target: '[[reward-model]]'
  target_id: method:reward-model
  confidence: medium
- type: related_to
  target: '[[safety-refusal]]'
  target_id: term:safety-refusal
  confidence: medium
- type: related_to
  target: '[[over-hedging]]'
  target_id: term:over-hedging
  confidence: medium
- type: related_to
  target: '[[over-abstention]]'
  target_id: term:over-abstention
  confidence: medium
---

A set of zero-shot GPT-4 classifiers used as an additional reward signal during RLHF fine-tuning. Each RBRM takes a prompt, model output, and human-written rubric, and classifies the output into categories (e.g., desired refusal, undesired refusal, disallowed content, safe non-refusal). The reward signal simultaneously penalizes under-refusal on harmful prompts and over-refusal on safe prompts.

**Why it matters here:** RBRMs operationalize the dual-failure-mode correction: they try to push the model away from both harmful compliance and excessive over-caution on innocuous inputs. This is the closest existing industrial technique to a precision abstention-calibration signal, making it a design reference for Phase 1's abstention training arms.

**Lineage:** Introduced in GPT-4 Technical Report (arXiv:2303.08774, §6). Related to reward-model approaches in [[reinforcement-learning-from-human-feedback]]; concurrent with constitutional AI methods.
