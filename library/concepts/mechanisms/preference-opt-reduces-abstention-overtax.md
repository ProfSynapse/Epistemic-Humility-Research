---
aliases:
- Preference optimization reduces SFT-induced over-refusal in abstention training
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:preference-opt-reduces-abstention-overtax
  type: mechanism
  status: canonical
cause: Preference optimization ([[direct-preference-optimization]], [[proximal-policy-optimization]], BoN) applied on top of SFT-warmed [[abstention]] model
effect: Reduced Idk-Ik (over-refusal) rate while maintaining high Ik-Idk (correct refusal) rate, increasing aggregate Truthful rate
polarity: decreases
related:
- '[[2401.13275--can-ai-assistants-know-what-they-dont-know]]'
- '[[direct-preference-optimization]]'
- '[[proximal-policy-optimization]]'
- '[[abstention]]'
relationships:
- type: supported_by
  target: '[[2401.13275--can-ai-assistants-know-what-they-dont-know]]'
  target_id: paper:2401.13275
  confidence: high
- type: related_to
  target: '[[direct-preference-optimization]]'
  target_id: method:direct-preference-optimization
- type: related_to
  target: '[[proximal-policy-optimization]]'
  target_id: method:proximal-policy-optimization
- type: related_to
  target: '[[abstention]]'
  target_id: term:abstention
---

Preference optimization provides a contrastive signal that SFT alone lacks: pairing cases where the model should answer with cases where it should abstain teaches the model to discriminate rather than default to refusal. This corrects the over-conservative bias introduced by SFT on abstention data. The can-ai-assistants paper (arXiv:2401.13275) shows DPO, PPO, and Best-of-N all reduce the Idk-Ik rate while preserving the correct Ik-Idk abstention rate, increasing overall truthfulness.
