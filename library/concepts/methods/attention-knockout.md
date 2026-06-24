---
aliases:
- SSM knockout
- attention knock-out
- information flow blocking
- Attention Knockout (SSM Blocking)
- attention edge intervention
- attention blocking
tags:
- kg/method
- concept
- method
kg:
  id: method:attention-knockout
  type: method
  status: canonical
area: mechanistic-interpretability
related:
- '[[2304.14767--dissecting-recall-factual-associations]]'
- '[[activation-patching]]'
- '[[logit-lens]]'
- '[[causal-intervention]]'
relationships:
- type: proposed_by
  target: '[[2304.14767--dissecting-recall-factual-associations]]'
  target_id: paper:2304.14767
  confidence: high
- type: variation_of
  target: '[[activation-patching]]'
  target_id: method:activation-patching
- type: related_to
  target: '[[logit-lens]]'
  target_id: method:logit-lens
- type: related_to
  target: '[[causal-intervention]]'
  target_id: method:causal-intervention
---

Attention knockout is a causal intervention technique that zeroes out all attention edges between two token positions at a specific layer by setting the attention logits to negative infinity for every head, thereby blocking information flow along that edge entirely. The technique measures the drop in prediction probability when a given (source, destination) position pair is silenced, identifying which attention edges are critical for a prediction. It can be extended to SSM architectures by analogously blocking selective-state-space information pathways between positions.

**Why it matters here:** Attention knockout enables fine-grained causal decomposition of factual recall into specific information-flow pathways, establishing mechanistic evidence for which parts of a model "know" a fact and thus grounding claims about knowledge localization and the conditions for hallucination.

**Lineage:** introduced in [[2304.14767--dissecting-recall-factual-associations]]; variation of [[activation-patching]] (which patches activations rather than blocks edges); related to [[logit-lens]] and [[causal-intervention]] as complementary tools for tracing information flow.
