---
aliases:
- Self-prediction outperforms matched cross-prediction
- Models predict themselves better than another trained model can
- Own-behavior prediction has a privileged-access advantage
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:self-prediction-outperforms-matched-cross-prediction
  type: mechanism
  status: canonical
cause: "A model is fine-tuned on properties of its own simple hypothetical behavior, while a different model receives matched examples about that same target model."
effect: "On held-out tasks, the target model predicts itself more accurately than the comparison model predicts it."
polarity: enables
related:
- '[[2410.13787--looking-inward-language-models-can-learn-about]]'
- '[[self-prediction-training]]'
- '[[cross-prediction-introspection-test]]'
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
  target: '[[cross-prediction-introspection-test]]'
  target_id: method:cross-prediction-introspection-test
  confidence: high
- type: related_to
  target: '[[behavioral-introspection]]'
  target_id: term:behavioral-introspection
  confidence: high
---

Llama-3.1-70B predicted itself at 48.5 percent accuracy while GPT-4o predicted
that Llama model at 31.8 percent. GPT-4o predicted itself at 49.4 percent while
Llama reached 36.6 percent on GPT-4o. Bidirectional comparisons and a
cross-prediction data-scaling plateau support the paper's privileged-access
interpretation for simple behavior properties.
