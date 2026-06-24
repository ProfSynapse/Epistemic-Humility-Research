---
aliases:
- atomic fact extraction
- atomic decomposition
- fact atomization
- atomic claim extraction
tags:
- kg/method
- concept
- method
kg:
  id: method:atomic-fact-decomposition
  type: method
  status: canonical
area: methods
related:
- '[[2305.14251--factscore]]'
- '[[factscore]]'
- '[[hallucination]]'
- '[[factscore-biography-benchmark]]'
relationships:
- type: proposed_by
  target: '[[2305.14251--factscore]]'
  target_id: paper:2305.14251
  confidence: high
- type: related_to
  target: '[[factscore]]'
  target_id: metric:factscore
  confidence: medium
- type: related_to
  target: '[[hallucination]]'
  target_id: term:hallucination
  confidence: medium
- type: related_to
  target: '[[factscore-biography-benchmark]]'
  target_id: dataset:factscore-biography-benchmark
  confidence: medium
---

A preprocessing step that takes a long-form generated text and breaks it into a list of atomic facts: short, self-contained sentences each conveying exactly one piece of information. Each atomic fact can be independently verified against a knowledge source as supported, not-supported, or irrelevant. The decomposition is carried out either by human annotators (with InstructGPT-produced candidates as a starting point) or fully automatically using a prompted LM.

**Why it matters here:** Atomic fact decomposition is the foundational operation that makes FActScore possible: without decomposing a generation into independently verifiable claims, one is forced back to holistic binary judgments that obscure the mixture of true and false content in a typical long-form response. Any vault pipeline that uses FActScore as an evaluation signal depends on this decomposition step.

**Lineage:** Introduced as the first key idea in FActScore (arXiv:2305.14251, Section 3.1); draws on prior summarization content-unit work (Nenkova and Passonneau 2004) and concurrent fact-verification decomposition work (Fan et al. 2020, Chen et al. 2022).
