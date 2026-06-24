---
aliases:
- ERFT disperses refusal activations
- rich refusal format diffuses safety direction
- output verbosity distributes refusal representation
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:extended-refusal-fine-tuning-disperses-safety-signal
  type: mechanism
  status: canonical
cause: "Fine-tuning on semantically rich, multi-component refusal responses that span many token positions (extended-refusal format)."
effect: "The refusal signal is distributed across multiple dimensions of the residual-stream activation space rather than concentrated in a single direction, making weight-orthogonalization attacks fail to collapse refusal behavior."
polarity: prevents
related:
- '[[2505.19056--abliteration-defense-dose-response]]'
- '[[refusal-direction-mediates-refusal]]'
- '[[refusal-directions-are-geometrically-distinct]]'
- '[[extended-refusal-fine-tuning]]'
- '[[weight-orthogonalization]]'
- '[[refusal-direction]]'
- '[[safety-refusal]]'
relationships:
- type: supported_by
  target: '[[2505.19056--abliteration-defense-dose-response]]'
  target_id: paper:2505.19056
  confidence: high
- type: related_to
  target: '[[refusal-direction-mediates-refusal]]'
  target_id: mechanism:refusal-direction-mediates-refusal
  confidence: high
- type: related_to
  target: '[[refusal-directions-are-geometrically-distinct]]'
  target_id: mechanism:refusal-directions-are-geometrically-distinct
  confidence: high
- type: related_to
  target: '[[extended-refusal-fine-tuning]]'
  target_id: method:extended-refusal-fine-tuning
  confidence: high
- type: related_to
  target: '[[weight-orthogonalization]]'
  target_id: method:weight-orthogonalization
  confidence: high
- type: related_to
  target: '[[refusal-direction]]'
  target_id: term:refusal-direction
  confidence: high
- type: related_to
  target: '[[safety-refusal]]'
  target_id: term:safety-refusal
  confidence: high
---

Conventional safety-aligned models produce brief, repetitive refusal tokens, which creates a stereotyped activation signature isolable as a single linear direction. Projecting that direction out of weight matrices reduces refusal rates by 70-80 pp. Extended-refusal training forces diverse semantic content before and around the refusal token, spreading the signature across many directions. Empirically, baseline models lose 28-34 points of centroid distance between harmful and benign hidden states after abliteration; extended-refusal models lose only 8-14 points (Table 2). Post-abliteration refusal rates stay above 90% for extended-refusal models vs. 13-21% for baselines (Table 1). The cost is a 5 pp larger MMLU drop after abliteration, indicating the refusal signal has become entangled with general-purpose computation.
