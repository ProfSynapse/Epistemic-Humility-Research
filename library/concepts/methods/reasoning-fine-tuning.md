---
aliases:
- reasoning post-training
- RLVR
- reinforcement learning with verifiable rewards
- test-time compute scaling
- Reasoning Fine-Tuning
tags:
- kg/method
- concept
- method
kg:
  id: method:reasoning-fine-tuning
  type: method
  status: canonical
area: methods
related:
- '[[direct-preference-optimization]]'
relationships:
- type: derived_from
  target: '[[direct-preference-optimization]]'
  target_id: method:direct-preference-optimization
---

Reasoning Fine-Tuning is a post-training paradigm that optimizes a language model
for deliberate chain-of-thought reasoning using a verifiable correctness signal,
typically a rule-based or process reward. The model is encouraged to allocate
additional token budget to intermediate reasoning steps before committing to a
final answer, producing models such as DeepSeek R1 and s1 that markedly
outperform their base checkpoints on formal reasoning benchmarks. Unlike DPO or
KTO, the training signal comes from outcome verification rather than from
human-preference pairs.

**Why it matters here:** The AbstentionBench survey (2506.09038) finds that
reasoning fine-tuning degrades abstention behaviour, providing a negative control:
extended deliberation does not substitute for calibrated
[[abstention]] and may in fact suppress it, which is a key comparison point
for the SFT-vs-DPO-vs-KTO abstention study.

**Lineage:** extends [[direct-preference-optimization]] in the sense that RLVR
replaces the paired-preference loss with a verifiable-reward signal while
retaining the online policy-update loop.
