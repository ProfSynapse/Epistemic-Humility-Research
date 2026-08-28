---
aliases:
- Distant latent samples provide cleaner abstention supervision
- Geometric denoising improves knowledge-boundary fine-tuning
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:hyperplane-distance-filtering-improves-abstention-training
  type: mechanism
  status: canonical
cause: "Training retains examples whose hidden states lie far from a truthfulness-probe decision hyperplane."
effect: "The resulting abstention model learns a cleaner known-versus-unknown boundary and improves reliability across in-domain and out-of-domain tasks."
polarity: increases
related:
- '[[2604.14324--purging-gray-zone-latent-geometric-denoising-precise]]'
- '[[geode-geometric-denoising]]'
- '[[knowledge-boundary]]'
relationships:
- type: supported_by
  target: '[[2604.14324--purging-gray-zone-latent-geometric-denoising-precise]]'
  target_id: paper:2604.14324
  confidence: high
- type: related_to
  target: '[[geode-geometric-denoising]]'
  target_id: method:geode-geometric-denoising
  confidence: high
- type: related_to
  target: '[[knowledge-boundary]]'
  target_id: term:knowledge-boundary
  confidence: high
---

On Qwen3-8B and TriviaQA, the farthest latent-distance tier reached reliability F1 of 77.6, compared with 74.6 for the middle tier and 73.2 for the nearest tier. Probe accuracy also increased monotonically with hyperplane distance, while the nearest bin had AUROC below 0.6.
