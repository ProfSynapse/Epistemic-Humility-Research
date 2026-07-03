---
aliases:
- score-based concept algebra
- concept subspace editing
tags:
- kg/method
- concept
- method
kg:
  id: method:concept-algebra
  type: method
  status: canonical
area: steering
related:
- '[[2302.03693--concept-algebra-score-based-text-controlled-generative]]'
- '[[concepts-as-subspaces]]'
- '[[classifier-free-guidance]]'
- '[[score-representation]]'
relationships:
- type: proposed_by
  target: '[[2302.03693--concept-algebra-score-based-text-controlled-generative]]'
  target_id: paper:2302.03693
  confidence: high
- type: derived_from
  target: '[[concepts-as-subspaces]]'
  target_id: term:concepts-as-subspaces
- type: derived_from
  target: '[[classifier-free-guidance]]'
  target_id: method:classifier-free-guidance
---

Concept algebra identifies and manipulates high-level semantic concepts in score-based text-to-image models by locating the subspace of the [[score-representation]] that corresponds to a concept (via PCA-like projection over contrastive prompts) and replacing that subspace component with a target concept's projection, leaving orthogonal components unchanged. The method is compositional: multiple concept edits can be added or subtracted simultaneously. Clean decomposition requires [[causal-separability]] between the edited concepts; when concepts are correlated in training data the algebra introduces bleed-through.

**Why it matters here:** Concept algebra is a direct antecedent to analogous editing operations in language model representations (e.g., [[activation-steering]], [[difference-in-means]]). The framework demonstrates that linear subspace geometry supports faithful concept editing, which motivates reading and writing epistemic-state axes (confidence, uncertainty) in the same way.

**Lineage:** derives from [[concepts-as-subspaces]] (hypothesis that concepts are linear subspaces) and [[classifier-free-guidance]] (supplies the centered [[score-representation]] on which the algebra operates); closely related to [[score-rep-subspace-encodes-concept]].
