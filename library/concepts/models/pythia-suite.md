---
aliases:
- Pythia
- EleutherAI Pythia
- Pythia Model Suite
tags:
- kg/model
- concept
- model
kg:
  id: model:pythia-suite
  type: model
  status: canonical
area: mechanistic-interpretability
related:
- '[[pythia-70m]]'
- '[[sparse-probing]]'
relationships:
- type: related_to
  target: '[[pythia-70m]]'
  target_id: model:pythia-70m
- type: related_to
  target: '[[sparse-probing]]'
  target_id: method:sparse-probing
---

The Pythia suite is EleutherAI's family of autoregressive transformer language models trained on The Pile, spanning seven sizes from 70M to 6.9B parameters. All models use parallel attention layers and rotary positional encodings, and intermediate training checkpoints are publicly released, enabling mechanistic studies of capability emergence over training. The uniform architecture across scales makes Pythia a controlled test bed for comparing representational properties at different model sizes.

**Why it matters here:** The Pythia suite enables controlled comparisons of self-knowledge and calibration behavior as a function of model scale, directly bearing on the hypothesis that larger models have better-calibrated uncertainty representations.

**Lineage:** [[pythia-70m]] is the smallest member used in sparse-probing experiments; the suite enables scale ablations across [[sparse-probing]] and related mechanistic interpretability methods.
