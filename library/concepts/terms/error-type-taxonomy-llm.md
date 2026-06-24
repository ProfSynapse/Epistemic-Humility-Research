---
aliases:
- error type taxonomy
- five-type error taxonomy
- behavioral error classification
tags:
- kg/term
- concept
- term
kg:
  id: term:error-type-taxonomy-llm
  type: term
  status: canonical
area: terms
related:
- '[[2410.02707--llms-know-more-than-they-show]]'
- '[[generation-discrimination-gap]]'
- '[[hallucination]]'
- '[[self-knowledge]]'
- '[[known-unknowns-taxonomy]]'
relationships:
- type: proposed_by
  target: '[[2410.02707--llms-know-more-than-they-show]]'
  target_id: paper:2410.02707
  confidence: high
- type: related_to
  target: '[[generation-discrimination-gap]]'
  target_id: term:generation-discrimination-gap
  confidence: medium
- type: related_to
  target: '[[hallucination]]'
  target_id: term:hallucination
  confidence: medium
- type: related_to
  target: '[[self-knowledge]]'
  target_id: term:self-knowledge
  confidence: medium
- type: related_to
  target: '[[known-unknowns-taxonomy]]'
  target_id: term:known-unknowns-taxonomy
  confidence: medium
---

A five-category behavioral taxonomy of LLM errors defined by the distribution of answers across K=30 resampled responses at temperature 1: (A) refuses to answer, (B) consistently correct, (C) consistently incorrect, (D) two competing answers at similar rates, (E) many distinct answers. Subtypes (B1/B2, C1/C2, E1/E2) capture whether the correct answer ever appears in the sample.

**Why it matters here:** The taxonomy decomposes a binary correct/incorrect label into behaviorally distinct failure modes, each with different implications for mitigation (retrieval augmentation, fine-tuning, inference-time selection). Internal probes can predict which type a given input will fall into at AUC 0.64-0.90, connecting behavioral patterns to internal representations.

**Lineage:** Introduced by Orgad et al. (2024) 2410.02707 for TriviaQA on Mistral-7B-instruct and Llama3-8B-instruct. Related to prior resampling-based knowledge analysis (Simhi et al. 2024; Gekhman et al. 2024).
