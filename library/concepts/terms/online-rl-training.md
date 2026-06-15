---
aliases:
- online training
- online sampling
- online reinforcement learning
tags:
- kg/term
- concept
- term
kg:
  id: term:online-rl-training
  type: term
  status: canonical
area: methods
related:
- '[[group-relative-policy-optimization]]'
- '[[proximal-policy-optimization]]'
- '[[direct-preference-optimization]]'
relationships:
- type: related_to
  target: '[[group-relative-policy-optimization]]'
  target_id: method:group-relative-policy-optimization
- type: related_to
  target: '[[proximal-policy-optimization]]'
  target_id: method:proximal-policy-optimization
- type: related_to
  target: '[[direct-preference-optimization]]'
  target_id: method:direct-preference-optimization
---

Online RL training is a regime in which the policy being updated also generates the training rollouts at each step, so the data distribution continuously tracks the evolving policy. This contrasts with offline training (as in DPO or static RFT), where data is sampled once from a fixed reference model and the policy may drift far from that distribution during optimization. Online sampling typically requires a reward signal available at inference time rather than a pre-collected preference dataset.

**Why it matters here:** The distinction between online and offline training regimes is relevant to understanding the generalization properties of abstention training: the mechanism [[online-rl-outperforms-offline-rl]] reflects evidence that online sampling better tracks the policy's current knowledge boundary than fixed offline data.

**Lineage:** related to [[group-relative-policy-optimization]] and [[proximal-policy-optimization]] (online methods); [[direct-preference-optimization]] is the canonical offline alternative.
