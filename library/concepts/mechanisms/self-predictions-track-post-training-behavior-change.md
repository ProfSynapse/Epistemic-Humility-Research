---
aliases:
- Self-predictions track post-training behavior change
- A model updates self-reports after its behavior changes
- Behavioral self-knowledge follows a modified policy
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:self-predictions-track-post-training-behavior-change
  type: mechanism
  status: canonical
cause: "Further object-level fine-tuning changes a self-prediction-trained model's behavior without providing hypothetical labels about the new behavior."
effect: "The model's later hypothetical self-predictions move toward its changed behavior rather than remaining tied to its old behavior."
polarity: explains
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

After 1,000 object-level examples changed GPT-4o's behavior, it predicted its
new behavior at 35.4 percent accuracy and its old behavior at 21.7 percent. GPT-4
showed a similar pattern, while GPT-3.5 was weaker. The finetuning data contained
no hypothetical labels about the new behavior.
