---
aliases:
- unwarranted hedging
- excessive epistemic caution
- Over-Hedging
tags:
- kg/term
- concept
- term
kg:
  id: term:over-hedging
  type: term
  status: canonical
area: terms
related:
- '[[alignment-tax]]'
- '[[over-conservativeness-score]]'
relationships:
- type: related_to
  target: '[[alignment-tax]]'
  target_id: term:alignment-tax
- type: related_to
  target: '[[over-conservativeness-score]]'
  target_id: metric:over-conservativeness-score
---

Over-hedging is a failure mode in which a model trained to reward epistemic humility adds excessive caveats or claims there is no clear answer to questions that have obvious, well-established answers. It is documented in InstructGPT (section 4.3) as a reward-induced artifact: labelers instructed to reward epistemic humility inadvertently penalize confident correct answers, teaching the policy to hedge even when certainty is warranted.

**Why it matters here:** Over-hedging is the mirror-image failure to hallucination and is a central risk in the Phase 1 abstention study; a training signal that pushes models toward abstention can overshoot and suppress legitimate confident responses, raising the [[over-conservativeness-score]] and depressing effective reliability.

**Lineage:** a specific symptom of [[alignment-tax]]; related to [[over-conservativeness-score]] as the metric used to measure it.
