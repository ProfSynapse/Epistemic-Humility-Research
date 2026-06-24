---
aliases:
- penalise monitorability
- monitor accuracy penalization
- adversarial monitorability training
tags:
- kg/method
- concept
- method
kg:
  id: method:adversarial-monitor-penalization
  type: method
  status: canonical
area: methods
related:
- '[[2512.00218--reasoning-under-pressure-monitorability]]'
- '[[cot-monitorability]]'
- '[[latent-variable-monitor-accuracy]]'
- '[[group-relative-policy-optimization]]'
- '[[kl-divergence-penalty]]'
relationships:
- type: proposed_by
  target: '[[2512.00218--reasoning-under-pressure-monitorability]]'
  target_id: paper:2512.00218
  confidence: high
- type: related_to
  target: '[[cot-monitorability]]'
  target_id: term:cot-monitorability
  confidence: medium
- type: related_to
  target: '[[latent-variable-monitor-accuracy]]'
  target_id: metric:latent-variable-monitor-accuracy
  confidence: medium
- type: related_to
  target: '[[group-relative-policy-optimization]]'
  target_id: method:group-relative-policy-optimization
  confidence: medium
- type: related_to
  target: '[[kl-divergence-penalty]]'
  target_id: term:kl-divergence-penalty
  confidence: medium
---

A training incentive that adds a negative reward when a monitor correctly predicts a latent variable from the reasoner's CoT, and a positive reward when the monitor fails. Implemented as rmonitorability = +1 if monitor incorrect, -1 if monitor correct, with reweighting for latent variable imbalance. Used to create model organisms of deliberately unmonitorable reasoning and to establish an upper bound on how hard monitoring can be made.

**Why it matters here:** Demonstrates that CoT monitorability can be deliberately degraded with only minor accuracy loss, enabling adversarial stress-testing of monitor pipelines and model organism construction for monitoring research.

**Lineage:** Introduced in MacDermott et al. 2025 (arXiv:2512.00218), Section 4.1 and Section 5.3.2.
