---
aliases:
- Elicitation Discourse Type Surfaces Distinct Persona Facets
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:elicitation-discourse-type-surfaces-distinct-facets
  type: mechanism
  status: canonical
cause: "Choice of discourse type (description, dialogue, or narration) used to elicit persona expressions from a base model for [[difference-in-means]] vector extraction"
effect: "All three strategies yield statistically significant cross-evaluation steering, but each emphasises qualitatively distinct facets of the same underlying persona"
polarity: enables
related:
- '[[2605.13329--tracing-persona-vectors-through-llm-pretraining]]'
- '[[persona-vectors]]'
- '[[difference-in-means]]'
- '[[representation-reading]]'
relationships:
- type: supported_by
  target: '[[2605.13329--tracing-persona-vectors-through-llm-pretraining]]'
  target_id: paper:2605.13329
  confidence: high
- type: related_to
  target: '[[persona-vectors]]'
  target_id: method:persona-vectors
- type: related_to
  target: '[[difference-in-means]]'
  target_id: method:difference-in-means
- type: related_to
  target: '[[representation-reading]]'
  target_id: method:representation-reading
---

Persona vector extraction via difference-in-means depends on which type of text is used to elicit the target trait: descriptive prompts, dialogues, and narrative passages each probe different surface realisations of the same underlying character dimension. The pretraining-tracing paper (arXiv:2605.13329) shows that all three discourse types yield vectors that transfer significantly in cross-evaluation steering, confirming they capture the same latent direction, but qualitative inspection reveals that each emphasises different behavioural facets (e.g., direct assertion vs. conversational implicature). Practitioners therefore should select discourse type based on which facet of the trait is most relevant for the intended downstream application.
