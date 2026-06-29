---
aliases:
- Hidden states linearly encode unanswerability even when the model hallucinates an answer
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:hidden-state-linearly-encodes-unanswerability-despite-hallucination
  type: mechanism
  status: canonical
cause: "Probing an LLM's last-layer, first-generated-token hidden state with a linear classifier for whether the question is answerable from context."
effect: "Answerability is decoded with high accuracy even on examples where the model nonetheless hallucinates an answer to an unanswerable question, evidencing an internal/behavior dissociation."
polarity: enables
related:
- '[[2310.11877--curious-case-hallucinatory-un-answerability-finding-truths]]'
- '[[answerability-subspace]]'
- '[[linear-probe]]'
- '[[unanswerable-questions]]'
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
  target: '[[linear-probe]]'
  target_id: method:linear-probe
  confidence: high
---

Slobodkin et al. 2023 find that a linear probe reads answerability off the last
layer's first-token representation with high accuracy even on instances where the
model goes on to fabricate an answer to an unanswerable question - the model
"knows" internally that it cannot answer while its behavior says otherwise. This
is the closest prior art to the internal-axis vs emitted-behavior dissociation
the experiment studies.
