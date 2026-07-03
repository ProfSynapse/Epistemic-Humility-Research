---
aliases:
- TCH
- truth co-occurrence
- truth clustering hypothesis
- Truth Co-occurrence Hypothesis (TCH)
tags:
- kg/term
- concept
- term
kg:
  id: term:truth-co-occurrence-hypothesis
  type: term
  status: canonical
area: terms
related:
- '[[2510.15804--emergence-linear-truth-encodings-language-models]]'
- '[[truth-direction]]'
relationships:
- type: proposed_by
  target: '[[2510.15804--emergence-linear-truth-encodings-language-models]]'
  target_id: paper:2510.15804
  confidence: high
- type: related_to
  target: '[[truth-direction]]'
  target_id: term:truth-direction
---

The Truth Co-occurrence Hypothesis (TCH) proposes that in naturally occurring text, true statements are statistically more likely to co-occur with other true statements within the same document, and false with false. This creates a loss-reduction incentive during language model pretraining to track a latent truth bit across sentences: a model that infers the factuality regime of the current context can assign higher probability to subsequent statements of the same polarity. The hypothesis generates a mechanistic prediction that truth encoding should emerge from gradient descent even without explicit truthfulness supervision, because co-occurrence structure is directly exploitable by next-token prediction.

**Why it matters here:** If TCH holds, a model's internal truth representation is a natural byproduct of exposure to well-structured factual corpora, which grounds the expectation that epistemic humility can be elicited from latent state rather than injected by post-training.

**Lineage:** operationalizes and motivates [[truth-direction]]; tested against [[maven-fact]] co-occurrence statistics and verified in [[llama3-8b]] probing experiments described in [[2510.15804--emergence-linear-truth-encodings-language-models]].
