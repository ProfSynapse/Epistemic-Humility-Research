---
aliases:
- static conflict in Cor-RAIT
- feature-space label collision in RAIT
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:static-conflict-degrades-rait-calibration
  type: mechanism
  status: canonical
cause: "Correctness-only data construction assigns opposite labels (vanilla vs IdK) to semantically similar samples that are nearby in the model's representation space"
effect: "The trained model receives contradictory supervision on similar inputs, causing misclassification of known questions as unknown and increasing over-refusal rates"
polarity: increases
related:
- '[[2410.06913--craft]]'
- '[[sft-abstention-causes-over-refusal]]'
- '[[craft]]'
- '[[refusal-aware-instruction-tuning]]'
- '[[over-abstention]]'
- '[[consistency-based-confidence]]'
relationships:
- type: supported_by
  target: '[[2410.06913--craft]]'
  target_id: paper:2410.06913
  confidence: high
- type: related_to
  target: '[[sft-abstention-causes-over-refusal]]'
  target_id: mechanism:sft-abstention-causes-over-refusal
  confidence: high
- type: related_to
  target: '[[craft]]'
  target_id: method:craft
  confidence: high
- type: related_to
  target: '[[refusal-aware-instruction-tuning]]'
  target_id: method:refusal-aware-instruction-tuning
  confidence: high
- type: related_to
  target: '[[over-abstention]]'
  target_id: term:over-abstention
  confidence: high
- type: related_to
  target: '[[consistency-based-confidence]]'
  target_id: method:consistency-based-confidence
  confidence: high
---

In Cor-RAIT, the sole criterion for flipping a sample's label to IdK is whether the initial model answered incorrectly. Because correctness has a non-differentiable link to the hidden state (the gradient is discontinuous at token boundaries), semantically similar samples can end up on opposite sides of the correctness threshold. t-SNE and the CRSS metric both confirm significant overlap between vanilla and IdK subsets at cosine-similarity threshold 0.97. This overlap produces conflicting gradients during SFT and is what the paper calls static conflict. Adding response certainty as a joint filter (CRaFT Stage 1) substantially reduces CRSS and improves THS.
