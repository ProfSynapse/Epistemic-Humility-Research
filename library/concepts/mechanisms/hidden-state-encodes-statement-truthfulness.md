---
aliases:
- internal truthfulness encoding
- LLM internal truth representation
- hidden-layer truth signal
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:hidden-state-encodes-statement-truthfulness
  type: mechanism
  status: canonical
cause: "Middle-to-penultimate hidden layers of a pretrained LLM process statement content"
effect: "A lightweight out-of-distribution classifier trained on those activations can detect statement truthfulness well above chance across unseen topics"
polarity: enables
related:
- '[[2304.13734--internal-state-knows-lying]]'
- '[[saplma]]'
- '[[truth-direction]]'
- '[[linear-probe]]'
- '[[truth-direction-causally-mediates-model-truth-output]]'
relationships:
- type: supported_by
  target: '[[2304.13734--internal-state-knows-lying]]'
  target_id: paper:2304.13734
  confidence: high
- type: related_to
  target: '[[saplma]]'
  target_id: method:saplma
  confidence: high
- type: related_to
  target: '[[truth-direction]]'
  target_id: term:truth-direction
  confidence: high
- type: related_to
  target: '[[linear-probe]]'
  target_id: method:linear-probe
  confidence: high
- type: related_to
  target: '[[truth-direction-causally-mediates-model-truth-output]]'
  target_id: mechanism:truth-direction-causally-mediates-model-truth-output
  confidence: high
---

Azaria and Mitchell (2304.13734) train a feedforward probe on hidden-layer activations from one set of factual topics and test it on held-out topics. For OPT-6.7b the 20th-of-32 layer yields 71.0% average cross-topic accuracy; for LLaMA2-7b the 16th layer yields 83.0%. Both compare to 53.7% for few-shot prompting. Training accuracy with genuine labels (86.4%) versus permuted labels (62.5%) confirms the model exploits real structure. The paper argues that coherent next-token generation requires the LLM to maintain an internal representation of statement truthfulness, which probe classifiers can recover. Topic-level variation (60.6-81.3% for OPT-6.7b) suggests the signal is partially confounded with training-data familiarity.
