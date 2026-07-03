---
aliases:
- in-context representation shift
- representation dynamics over conversation
tags:
- kg/term
- concept
- term
kg:
  id: term:conversational-representation-dynamics
  type: term
  status: canonical
area: mechanistic-interpretability
related:
- '[[2601.20834--linear-representations-language-models-can-change-dramatically]]'
- '[[linear-representation-hypothesis]]'
relationships:
- type: proposed_by
  target: '[[2601.20834--linear-representations-language-models-can-change-dramatically]]'
  target_id: paper:2601.20834
  confidence: high
- type: related_to
  target: '[[linear-representation-hypothesis]]'
  target_id: term:linear-representation-hypothesis
---

Conversational representation dynamics refers to the systematic change of linear
concept-directions in a language model's activation space as a conversation
unfolds across turns. Factuality, ethics, and identity dimensions identified in
empty-context prompts can invert within a multi-turn conversation: context-relevant
questions that were represented as factual flip to non-factual and vice versa, while
generic context-irrelevant directions remain largely stable. The effect is robust
across model layers and persists even when conversations are replayed off-policy from
a different model.

**Why it matters here:** If the answerability and calibration axes identified in
epistemic-humility probing are direction-unstable over multi-turn context, then
single-turn probe readouts may not generalize to deployed dialogue settings, making
conversation-aware probing a necessary extension.

**Lineage:** related to [[linear-representation-hypothesis]], the claim that
concepts are encoded as linear directions in activation space.
