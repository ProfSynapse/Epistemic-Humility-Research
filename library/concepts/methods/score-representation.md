---
aliases:
- centered score representation
- score rep
tags:
- kg/method
- concept
- method
kg:
  id: method:score-representation
  type: method
  status: canonical
area: steering
related:
- '[[2302.03693--concept-algebra-score-based-text-controlled-generative]]'
- '[[classifier-free-guidance]]'
- '[[concept-algebra]]'
relationships:
- type: proposed_by
  target: '[[2302.03693--concept-algebra-score-based-text-controlled-generative]]'
  target_id: paper:2302.03693
  confidence: high
- type: derived_from
  target: '[[classifier-free-guidance]]'
  target_id: method:classifier-free-guidance
---

The score representation for a text prompt y in a score-based generative model is the centered conditional score function Rep[y] = s(x,y) - s(x,Ø), where s(x,y) is the conditional score and s(x,Ø) is the unconditional (null-prompt) score. Centering removes the unconditional baseline shared by all prompts, isolating the prompt-specific direction in score space. The resulting representation is directly computable via [[classifier-free-guidance]] inference, and under this centering high-level semantic concepts correspond to linear subspaces, enabling [[concept-algebra]] operations.

**Why it matters here:** The centering operation mirrors analogous baseline-subtraction techniques used to expose concept-specific directions in language models (see [[contrastive-activation-addition]] and [[difference-in-means]]). Understanding that centering is what makes representations linear informs how epistemic axes such as [[known-unknown-direction]] or [[truth-direction]] should be extracted.

**Lineage:** derives from [[classifier-free-guidance]], which provides the unconditional score baseline; operationalized by [[concept-algebra]] as the substrate for subspace projection and replacement.
