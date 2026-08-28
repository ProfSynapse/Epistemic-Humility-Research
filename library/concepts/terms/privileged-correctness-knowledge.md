---
aliases:
- privileged knowledge of correctness
- model-private correctness information
- private correctness signal
tags:
- kg/term
- concept
- term
kg:
  id: term:privileged-correctness-knowledge
  type: term
  status: canonical
area: verification
related:
- '[[2604.12373--masked-consensus-disentangling-privileged-knowledge-llm-correctness]]'
- '[[self-vs-peer-correctness-probing]]'
- '[[premium-gap]]'
relationships:
- type: proposed_by
  target: '[[2604.12373--masked-consensus-disentangling-privileged-knowledge-llm-correctness]]'
  target_id: paper:2604.12373
  confidence: high
- type: measured_by
  target: '[[self-vs-peer-correctness-probing]]'
  target_id: method:self-vs-peer-correctness-probing
  confidence: high
- type: measured_by
  target: '[[premium-gap]]'
  target_id: metric:premium-gap
  confidence: high
---

Privileged correctness knowledge is target-model-specific internal information that predicts whether that model will answer correctly and cannot be recovered as well from a peer model's representation of the same question. It excludes question features and shared difficulty patterns that are externally available.

**Why it matters here:** The construct distinguishes a model-private correctness readout from a generic difficulty classifier that works equally well from another model's hidden states.

**Lineage:** The paper operationalizes the construct through [[self-vs-peer-correctness-probing]] and quantifies it with the [[premium-gap]] on disagreement subsets.
