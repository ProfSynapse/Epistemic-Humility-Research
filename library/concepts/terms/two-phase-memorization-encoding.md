---
aliases:
- two-phase learning
- memorization then truth encoding
- two-phase training dynamic
- Two-Phase Memorization-Encoding Dynamic
tags:
- kg/term
- concept
- term
kg:
  id: term:two-phase-memorization-encoding
  type: term
  status: canonical
area: terms
related:
- '[[2510.15804--emergence-linear-truth-encodings-language-models]]'
- '[[truth-co-occurrence-hypothesis]]'
- '[[truth-direction]]'
relationships:
- type: proposed_by
  target: '[[2510.15804--emergence-linear-truth-encodings-language-models]]'
  target_id: paper:2510.15804
  confidence: high
- type: related_to
  target: '[[truth-co-occurrence-hypothesis]]'
  target_id: term:truth-co-occurrence-hypothesis
- type: related_to
  target: '[[truth-direction]]'
  target_id: term:truth-direction
---

Two-phase memorization-encoding describes an observed training dynamic in which a language model first rapidly memorises subject-attribute associations within roughly 1000 training batches (achieving over 99% accuracy on true sequences) and then, over a much longer horizon of roughly 7500 additional batches, develops a linearly separable truth representation that further reduces loss on false sequences. The first phase exploits recency and frequency signals in the data; the second phase exploits the co-occurrence structure predicted by the [[truth-co-occurrence-hypothesis]], gradually building a geometry in activation space that distinguishes true from false propositions even for novel contexts.

**Why it matters here:** The finding that truth encoding is a late, slow-forming consequence of pretraining gradient dynamics means it is present in base models before any alignment fine-tuning, directly supporting the project's thesis that epistemic humility is readable from latent state without requiring post-training intervention.

**Lineage:** introduced alongside [[truth-co-occurrence-hypothesis]] in [[2510.15804--emergence-linear-truth-encodings-language-models]]; the second phase explains why [[truth-direction]] probes are detectable in pretrained but not randomly-initialized models.
