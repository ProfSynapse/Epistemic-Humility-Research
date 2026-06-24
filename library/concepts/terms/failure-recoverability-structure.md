---
aliases:
- recoverability structure
- recoverability regime
- failure topography
tags:
- kg/term
- concept
- term
kg:
  id: term:failure-recoverability-structure
  type: term
  status: canonical
area: terms
related:
- '[[2606.05145--distributional-failure-signatures]]'
- '[[policy-entropy-collapse]]'
- '[[output-diversity-collapse]]'
- '[[best-of-n-sampling]]'
- '[[group-relative-policy-optimization]]'
- '[[supervised-finetuning]]'
relationships:
- type: proposed_by
  target: '[[2606.05145--distributional-failure-signatures]]'
  target_id: paper:2606.05145
  confidence: high
- type: related_to
  target: '[[policy-entropy-collapse]]'
  target_id: term:policy-entropy-collapse
  confidence: medium
- type: related_to
  target: '[[output-diversity-collapse]]'
  target_id: term:output-diversity-collapse
  confidence: medium
- type: related_to
  target: '[[best-of-n-sampling]]'
  target_id: method:best-of-n-sampling
  confidence: medium
- type: related_to
  target: '[[group-relative-policy-optimization]]'
  target_id: method:group-relative-policy-optimization
  confidence: medium
- type: related_to
  target: '[[supervised-finetuning]]'
  target_id: method:supervised-finetuning
  confidence: medium
---

The latent organization of a model's failed reasoning traces into stable clusters that predict which class of test-time intervention can rescue the failure, recoverable from the distributional signature of rollouts rather than from reading trace text.

**Why it matters here:** If failure recoverability is structured, allocating test-time compute and intervention type by regime is more efficient than uniform retry; and the structure itself carries an interpretable audit signal about post-training method.

**Lineage:** Introduced in 2606.05145 as the central object the paper proposes; no prior atom covers this construct.
