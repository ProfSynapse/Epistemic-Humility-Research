---
aliases:
- cross-sentence reasoning
- multi-sentence inference
- multi-hop reading comprehension
tags:
- kg/term
- concept
- term
kg:
  id: term:multi-sentence-reasoning
  type: term
  status: canonical
area: terms
related:
- '[[1705.03551--triviaqa-dataset]]'
- '[[triviaqa]]'
- '[[squad]]'
- '[[hotpotqa]]'
- '[[musique]]'
- '[[knowledge-boundary]]'
relationships:
- type: proposed_by
  target: '[[1705.03551--triviaqa-dataset]]'
  target_id: paper:1705.03551
  confidence: high
- type: related_to
  target: '[[triviaqa]]'
  target_id: dataset:triviaqa
  confidence: medium
- type: related_to
  target: '[[squad]]'
  target_id: dataset:squad
  confidence: medium
- type: related_to
  target: '[[hotpotqa]]'
  target_id: dataset:hotpotqa
  confidence: medium
- type: related_to
  target: '[[musique]]'
  target_id: dataset:musique
  confidence: medium
- type: related_to
  target: '[[knowledge-boundary]]'
  target_id: term:knowledge-boundary
  confidence: medium
---

The requirement that a system combine or integrate information scattered across two or more sentences in an evidence document (or across documents) to derive a correct answer, as opposed to extracting an answer span from a single sentence.

**Why it matters here:** TriviaQA has 40% multi-sentence reasoning examples, more than three times the SQuAD rate, which contributes to the gap between state-of-the-art model performance (40% EM) and human performance (79.7%). Multi-sentence reasoning is also a proxy for knowledge integration difficulty relevant to epistemic humility: questions that require chaining facts are harder for models to know confidently.

**Lineage:** Characterized empirically in Joshi et al. (arXiv:1705.03551) Table 5 and Section 4; later formalized as a dataset property in HotpotQA and MuSiQue.
