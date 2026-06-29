---
aliases:
- Answerability Subspace
- answerability axis
- linear answerability direction
tags:
- kg/term
- concept
- term
kg:
  id: term:answerability-subspace
  type: term
  status: canonical
area: terms
related:
- '[[2310.11877--curious-case-hallucinatory-un-answerability-finding-truths]]'
- '[[linear-concept-erasure]]'
- '[[linear-probe]]'
- '[[unanswerable-questions]]'
- '[[overconfidence]]'
relationships:
- type: proposed_by
  target: '[[2310.11877--curious-case-hallucinatory-un-answerability-finding-truths]]'
  target_id: paper:2310.11877
  confidence: high
- type: related_to
  target: '[[linear-probe]]'
  target_id: method:linear-probe
  confidence: high
- type: related_to
  target: '[[unanswerable-questions]]'
  target_id: term:unanswerable-questions
  confidence: high
- type: related_to
  target: '[[linear-concept-erasure]]'
  target_id: method:linear-concept-erasure
  confidence: medium
---

The answerability subspace is a low-dimensional, linearly-decodable direction in
an LLM's hidden states (found at the last layer, first generated token) that
encodes whether the model "knows" a question is answerable from the given
context. A linear probe reads answerability off this subspace with high accuracy
even on examples where the model nonetheless goes on to hallucinate an answer to
an unanswerable question.

**Why it matters here:** This is the direct prior art for the experiment's
internal answerability axis: it establishes that answerability is linearly
encoded in the representation and dissociable from behavior, exactly the
internal/behavior gap the confidence-head work targets. It is the external
precedent that an answerability readout is latent and recoverable.

**Lineage:** Slobodkin et al. 2023; read via a [[linear-probe]] and causally
tested by [[linear-concept-erasure]]; conceptually parallel to truthfulness-axis
probing but about answerability rather than factual truth.
