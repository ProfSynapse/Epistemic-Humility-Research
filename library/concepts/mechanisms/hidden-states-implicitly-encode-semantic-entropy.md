---
aliases:
- hidden state SE encoding
- implicit SE encoding in activations
- LLM hidden states capture semantic uncertainty
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:hidden-states-implicitly-encode-semantic-entropy
  type: mechanism
  status: canonical
cause: "Model hidden states at mid-to-late layers of a single forward pass"
effect: "A linear probe trained on those representations predicts binarized semantic entropy at AUROC 0.70-0.95, including from the last input token before any generation"
polarity: enables
related:
- '[[2406.15927--semantic-entropy-probes]]'
- '[[semantic-entropy-probes]]'
- '[[semantic-entropy]]'
- '[[generation-discrimination-gap]]'
- '[[truth-direction]]'
- '[[residual-stream-activation]]'
relationships:
- type: supported_by
  target: '[[2406.15927--semantic-entropy-probes]]'
  target_id: paper:2406.15927
  confidence: high
- type: related_to
  target: '[[semantic-entropy-probes]]'
  target_id: method:semantic-entropy-probes
  confidence: high
- type: related_to
  target: '[[semantic-entropy]]'
  target_id: method:semantic-entropy
  confidence: high
- type: related_to
  target: '[[generation-discrimination-gap]]'
  target_id: term:generation-discrimination-gap
  confidence: high
- type: related_to
  target: '[[truth-direction]]'
  target_id: term:truth-direction
  confidence: high
- type: related_to
  target: '[[residual-stream-activation]]'
  target_id: term:residual-stream-activation
  confidence: high
---

Kossen et al. show across five models and four QA tasks that semantic entropy, a measure of uncertainty in meaning-space computed from 10 sampled generations, is accessible from a single forward pass via a linear probe on hidden states. AUROC rises with layer depth for short-form settings, peaks at intermediate layers for long-form settings. Critically, the signal is present even at the token-before-generating position, before the model produces any output, suggesting SE is encoded at the prompt-representation stage. A counterfactual context experiment confirms the probe tracks intrinsic SE rather than spurious task features: SEP predictions shift appropriately when context reduces SE from 1.84 to 0.50 even though the probe was never trained on context-augmented inputs.
