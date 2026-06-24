---
aliases:
- mass-covering f-divergence preserves diversity
- forward-KL rehearsal mechanism
- JS-divergence policy anchoring
- f-divergence prevents catastrophic forgetting in RLVR
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:mass-covering-divergence-preserves-policy-diversity
  type: mechanism
  status: canonical
cause: "Using a mass-covering f-divergence (forward-KL or Jensen-Shannon) as the regularization term in RLVR training, applied to a static pre-sampled near-perfect dataset from the reference policy"
effect: "The updated policy retains probability coverage over all solution modes present in the reference distribution, preserving OOD generalization and Pass@k while still improving Pass@1 on the training domain"
polarity: prevents
related:
- '[[2509.07430--choice-of-divergence-rlvr-diversity]]'
- '[[dph-rl]]'
- '[[self-distillation-suppresses-representational-drift]]'
- '[[reverse-kl-narrows-policy-to-single-mode]]'
- '[[rlvr-post-training-degrades-abstention]]'
- '[[kl-divergence-penalty]]'
- '[[pass-at-k]]'
relationships:
- type: supported_by
  target: '[[2509.07430--choice-of-divergence-rlvr-diversity]]'
  target_id: paper:2509.07430
  confidence: high
- type: related_to
  target: '[[dph-rl]]'
  target_id: method:dph-rl
  confidence: high
- type: related_to
  target: '[[self-distillation-suppresses-representational-drift]]'
  target_id: mechanism:self-distillation-suppresses-representational-drift
  confidence: high
- type: related_to
  target: '[[reverse-kl-narrows-policy-to-single-mode]]'
  target_id: mechanism:reverse-kl-narrows-policy-to-single-mode
  confidence: high
- type: related_to
  target: '[[rlvr-post-training-degrades-abstention]]'
  target_id: mechanism:rlvr-post-training-degrades-abstention
  confidence: high
- type: related_to
  target: '[[kl-divergence-penalty]]'
  target_id: term:kl-divergence-penalty
  confidence: high
- type: related_to
  target: '[[pass-at-k]]'
  target_id: metric:pass-at-k
  confidence: high
---

When the divergence penalty forces the policy to maintain mass on every mode the reference policy assigns non-negligible probability, the model cannot forget solution strategies it previously knew. Sampling the reference policy into a static dataset before training creates an anchor: if the policy's probability for any previously-covered response falls toward zero, the f-divergence loss rises sharply. This rehearsal effect prevents catastrophic forgetting without requiring extra external data or a live reference model during training. In contrast, reverse-KL samples from the current policy so once a solution path is forgotten it can never re-enter the gradient signal, and no-KL training provides no anchor at all. The DPH-RL experiments confirm that DPH-F recovers the base-model OOD math average (60.98 vs base 60.35) while GRPO and DAPO drop ~8 points after SQL-only training.
