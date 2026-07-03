---
aliases:
- Conversational Role Cue Flips Factuality Representation
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:conversational-role-cue-flips-factuality-representation
  type: mechanism
  status: canonical
cause: "A model engaging in a multi-turn conversation that cues a role incompatible with standard factuality (e.g., asserting opposite-day answers, roleplaying as a deity describing metaphysical claims), including off-policy replays written by another model"
effect: "Linear factuality representation directions invert for context-relevant questions; factual answers project onto the non-factual pole and the [[factuality-margin-score]] goes negative, while generic question representations remain stable"
polarity: enables
related:
- '[[2601.20834--linear-representations-language-models-can-change-dramatically]]'
- '[[factuality-margin-score]]'
- '[[conversational-representation-dynamics]]'
- '[[truth-direction]]'
relationships:
- type: supported_by
  target: '[[2601.20834--linear-representations-language-models-can-change-dramatically]]'
  target_id: paper:2601.20834
  confidence: high
- type: related_to
  target: '[[factuality-margin-score]]'
  target_id: metric:factuality-margin-score
- type: related_to
  target: '[[conversational-representation-dynamics]]'
  target_id: term:conversational-representation-dynamics
- type: related_to
  target: '[[truth-direction]]'
  target_id: term:truth-direction
---

The linear factuality direction in a model's residual stream is not a static property of the model weights but is dynamically overwritten by conversational context. When the conversation establishes a role in which false assertions are rewarded or expected, the model's internal factuality encoding for context-relevant queries inverts: representations that normally project onto the factual pole instead project onto the non-factual pole, as measured by the factuality margin score (arXiv:2601.20834). This context-driven inversion is role-specific rather than global, since generic questions asked in the same conversation maintain their normal factuality representations, implying that the model tracks which claims are subject to the role-induced inversion.
