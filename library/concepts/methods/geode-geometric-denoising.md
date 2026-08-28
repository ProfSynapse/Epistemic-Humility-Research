---
aliases:
- GeoDe
- Geometric Denoising
- latent-geometric denoising
- geometric-denoising abstention fine-tuning
tags:
- kg/method
- concept
- method
kg:
  id: method:geode-geometric-denoising
  type: method
  status: canonical
area: methods
related:
- '[[2604.14324--purging-gray-zone-latent-geometric-denoising-precise]]'
- '[[linear-probe]]'
- '[[supervised-finetuning]]'
- '[[knowledge-boundary]]'
relationships:
- type: proposed_by
  target: '[[2604.14324--purging-gray-zone-latent-geometric-denoising-precise]]'
  target_id: paper:2604.14324
  confidence: high
- type: derived_from
  target: '[[linear-probe]]'
  target_id: method:linear-probe
  confidence: high
- type: variation_of
  target: '[[supervised-finetuning]]'
  target_id: method:supervised-finetuning
  confidence: high
- type: related_to
  target: '[[knowledge-boundary]]'
  target_id: term:knowledge-boundary
  confidence: high
---

GeoDe is an abstention fine-tuning framework that trains a linear truthfulness probe, ranks training samples by distance from its decision hyperplane, and retains the most distant known and unknown examples. It replaces accuracy-only data partitioning with latent-geometric filtering before supervised fine-tuning.

**Why it matters here:** The method uses an internal known-versus-unknown readout to choose training data that shapes later abstention behavior.

**Lineage:** It combines [[linear-probe]] geometry with [[supervised-finetuning]] for sharper [[knowledge-boundary]] behavior.
