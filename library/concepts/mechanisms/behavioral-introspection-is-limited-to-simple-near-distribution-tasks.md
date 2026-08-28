---
aliases:
- Behavioral introspection is limited to simple near-distribution tasks
- Self-prediction fails on long responses and distant self-knowledge tasks
- Looking Inward does not generalize to broad situational awareness
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:behavioral-introspection-is-limited-to-simple-near-distribution-tasks
  type: mechanism
  status: canonical
cause: "Self-prediction requires a long response, a complex behavioral property, or transfer to a distant self-knowledge task."
effect: "The trained model loses its self-prediction advantage or fails to improve beyond matched baselines."
polarity: limits
related:
- '[[2410.13787--looking-inward-language-models-can-learn-about]]'
- '[[self-prediction-training]]'
- '[[behavioral-introspection]]'
relationships:
- type: supported_by
  target: '[[2410.13787--looking-inward-language-models-can-learn-about]]'
  target_id: paper:2410.13787
  confidence: high
- type: related_to
  target: '[[self-prediction-training]]'
  target_id: method:self-prediction-training
  confidence: high
- type: related_to
  target: '[[behavioral-introspection]]'
  target_id: term:behavioral-introspection
  confidence: high
---

Models failed on properties of long responses such as review sentiment,
character names, and response length. They had no own-model advantage for
sycophancy prediction and showed no broad gains on situational awareness,
sandbagging, coordination, or steganography evaluations.
