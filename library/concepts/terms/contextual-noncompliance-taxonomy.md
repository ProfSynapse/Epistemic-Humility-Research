---
aliases:
- noncompliance taxonomy
- contextual noncompliance
- CoCoNot taxonomy
tags:
- kg/term
- concept
- term
kg:
  id: term:contextual-noncompliance-taxonomy
  type: term
  status: canonical
area: terms
related:
- '[[2407.12043--coconot-art-of-saying-no]]'
- '[[safety-refusal]]'
- '[[over-abstention]]'
- '[[abstention]]'
- '[[unanswerable-questions]]'
- '[[false-premise-questions]]'
- '[[knowledge-boundary]]'
- '[[input-ambiguity]]'
relationships:
- type: proposed_by
  target: '[[2407.12043--coconot-art-of-saying-no]]'
  target_id: paper:2407.12043
  confidence: high
- type: related_to
  target: '[[safety-refusal]]'
  target_id: term:safety-refusal
  confidence: medium
- type: related_to
  target: '[[over-abstention]]'
  target_id: term:over-abstention
  confidence: medium
- type: related_to
  target: '[[abstention]]'
  target_id: term:abstention
  confidence: medium
- type: related_to
  target: '[[unanswerable-questions]]'
  target_id: term:unanswerable-questions
  confidence: medium
- type: related_to
  target: '[[false-premise-questions]]'
  target_id: term:false-premise-questions
  confidence: medium
- type: related_to
  target: '[[knowledge-boundary]]'
  target_id: term:knowledge-boundary
  confidence: medium
- type: related_to
  target: '[[input-ambiguity]]'
  target_id: term:input-ambiguity
  confidence: medium
---

A structured five-category taxonomy of situations where language models should not directly comply with user requests: (1) Incomplete requests (underspecified, false presupposition, incomprehensible); (2) Unsupported requests (modality, length, or temporal limitations); (3) Indeterminate requests (universal or model unknowns, subjective matters); (4) Humanizing requests (anthropomorphizing the model); and (5) Requests with safety concerns. The taxonomy distinguishes acceptable noncompliant responses (clarification, disclaimers, partial answers) from outright refusal and from direct compliance.

**Why it matters here:** Broadens the scope of appropriate model non-compliance beyond safety refusal to include epistemic humility cases (indeterminate, incomplete), capability limitations (unsupported), and identity/anthropomorphism issues. The taxonomy's indeterminate and incomplete categories directly correspond to knowledge-boundary and false-premise failures tracked in the Phase 1 experiment.

**Lineage:** Introduced by Brahman et al. (2407.12043), drawing on content moderation policies of Facebook, OpenAI, and Twitter, plus prior work on false presuppositions, underspecified queries, and AI safety.
