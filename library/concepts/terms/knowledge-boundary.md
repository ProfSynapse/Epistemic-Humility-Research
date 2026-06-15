---
aliases:
- parametric knowledge boundary
- knowledge gap
- knowledge intersection
- model knowledge boundary
- known vs unknown questions
- model knowledge limits
- known unknowns
- unknown unknowns
- knowledge quadrant
- known-unknowns
- Rumsfeld quadrant
- knowledge scope
- out-of-knowledge
- pre-existing knowledge
- model knowledge
tags:
- kg/term
- concept
- term
kg:
  id: term:knowledge-boundary
  type: term
  status: canonical
area: terms
---

The knowledge boundary demarcates what a model does and does not know given its pretraining data. The concept is often framed as a two-by-two quadrant: known knowns (correct and confident), known unknowns (the model recognizes its ignorance), unknown unknowns (the model is ignorant and unaware of that ignorance), and unknown knowns (knowledge the model holds but fails to retrieve). Self-knowledge is the ability to accurately identify items that fall beyond this boundary.

**Why it matters here:** The knowledge boundary is the central construct for the abstention study: training methods (SFT via [[refusal-aware-instruction-tuning]], DPO, KTO) are evaluated on whether they teach models to abstain precisely at the boundary rather than over-abstaining on known items or hallucinating on unknown ones.

**Lineage:** operationalized by [[refusal-aware-instruction-tuning]]; studied in the context of [[hallucination]] and [[self-knowledge]].
