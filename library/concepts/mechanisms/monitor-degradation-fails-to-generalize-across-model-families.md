---
aliases:
- monitor family generalization failure
- cross-family monitor transfer failure
- adversarial monitorability non-generalization
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:monitor-degradation-fails-to-generalize-across-model-families
  type: mechanism
  status: canonical
cause: "Adversarial training to reduce monitor accuracy for one monitor family (GPT-4o mini / GPT-4o)"
effect: "Reduced monitorability does not transfer to monitors from a different model family (Claude Sonnet 4.5), even when baseline accuracy is similar"
polarity: prevents
related:
- '[[2512.00218--reasoning-under-pressure-monitorability]]'
- '[[cot-monitorability]]'
- '[[adversarial-monitor-penalization]]'
- '[[adversarial-monitor-penalization-degrades-cot-monitorability]]'
- '[[estimator-divergence-invalidates-single-probe-faithfulness]]'
- '[[p-ik-ood-generalization-gap]]'
relationships:
- type: supported_by
  target: '[[2512.00218--reasoning-under-pressure-monitorability]]'
  target_id: paper:2512.00218
  confidence: high
- type: related_to
  target: '[[cot-monitorability]]'
  target_id: term:cot-monitorability
  confidence: high
- type: related_to
  target: '[[adversarial-monitor-penalization]]'
  target_id: method:adversarial-monitor-penalization
  confidence: high
- type: related_to
  target: '[[adversarial-monitor-penalization-degrades-cot-monitorability]]'
  target_id: mechanism:adversarial-monitor-penalization-degrades-cot-monitorability
  confidence: high
- type: related_to
  target: '[[estimator-divergence-invalidates-single-probe-faithfulness]]'
  target_id: mechanism:estimator-divergence-invalidates-single-probe-faithfulness
  confidence: high
- type: related_to
  target: '[[p-ik-ood-generalization-gap]]'
  target_id: mechanism:p-ik-ood-generalization-gap
  confidence: high
---

After adversarial monitor penalization targeting GPT-4o mini, monitorability decreases are Bonferroni-significant under GPT-4o mini and GPT-4o (same OpenAI family) on both datasets. However, Claude Sonnet 4.5 shows no significant degradation, including on Diamond Vault where its baseline monitor accuracy is comparable to GPT-4o. This family-specific confinement of degradation suggests the model exploits monitor-family-specific vulnerabilities in interpreting reasoning traces rather than learning to suppress the latent variable from its CoT entirely.
