---
aliases:
- Erasing the answerability subspace degrades answerability behavior
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:answerability-subspace-erasure-degrades-answerability-behavior
  type: mechanism
  status: canonical
cause: "Applying linear concept erasure (LEACE) to remove the linearly-decodable answerability direction from the hidden state."
effect: "The model's ability to behave appropriately on (un)answerable questions degrades, showing the linear subspace is causally used rather than merely correlated."
polarity: decreases
related:
- '[[2310.11877--curious-case-hallucinatory-un-answerability-finding-truths]]'
- '[[answerability-subspace]]'
- '[[linear-concept-erasure]]'
relationships:
- type: supported_by
  target: '[[2310.11877--curious-case-hallucinatory-un-answerability-finding-truths]]'
  target_id: paper:2310.11877
  confidence: high
- type: related_to
  target: '[[answerability-subspace]]'
  target_id: term:answerability-subspace
  confidence: high
- type: related_to
  target: '[[linear-concept-erasure]]'
  target_id: method:linear-concept-erasure
  confidence: high
---

Slobodkin et al. 2023 causally test the answerability direction by erasing it with
LEACE: once the linearly-decodable subspace is removed, the model's appropriate
handling of (un)answerable questions degrades, indicating the subspace is
functionally implicated in the behavior, not an epiphenomenal correlate.
