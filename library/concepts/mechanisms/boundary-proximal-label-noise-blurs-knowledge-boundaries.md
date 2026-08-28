---
aliases:
- Gray-zone examples introduce contradictory abstention gradients
- Near-hyperplane samples blur known versus unknown training signals
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:boundary-proximal-label-noise-blurs-knowledge-boundaries
  type: mechanism
  status: canonical
cause: "Accuracy-based abstention labels include examples whose hidden states lie near the known-versus-unknown probe boundary."
effect: "Ambiguous supervision introduces conflicting gradients and weakens the learned knowledge boundary."
polarity: complicates
related:
- '[[2604.14324--purging-gray-zone-latent-geometric-denoising-precise]]'
- '[[knowledge-boundary]]'
- '[[linear-probe]]'
relationships:
- type: supported_by
  target: '[[2604.14324--purging-gray-zone-latent-geometric-denoising-precise]]'
  target_id: paper:2604.14324
  confidence: high
- type: related_to
  target: '[[knowledge-boundary]]'
  target_id: term:knowledge-boundary
  confidence: high
- type: related_to
  target: '[[linear-probe]]'
  target_id: method:linear-probe
  confidence: high
---

The paper identifies a latent gray zone in which known and unknown representations overlap near the probe hyperplane. Models trained on these boundary examples perform worse than models trained on the farthest examples, and retaining too large a fraction of samples reintroduces noise.
