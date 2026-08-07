---
aliases:
- filtered-denominator accuracy artifact
- correct_on_known_pct instrument caveat
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:filtered-denominator-accuracy-metric-reverses-sign-under-selective-refusal
  type: mechanism
  status: canonical
cause: "computing an accuracy-style rate metric over only the subset of rows a model chose to answer (a filtered denominator, e.g. correct_on_known_pct = correct_known / answered_known) rather than over the full row population, then comparing arms with different refusal rates"
effect: "the rate can rise even though the absolute count of correct answers falls, because the denominator shrinks faster than the numerator; in this lineage GRPO answers 226 fewer known questions and gets 52 fewer of them right in absolute terms at seed 3, yet correct_on_known_pct rises +7.56 pp, a sign reversal against the same numerator computed over the full known population (-2.23 pp)"
polarity: mediates
related:
- '[[grpo-three-seed-confirmatory]]'
- '[[grpo-abstention-shift-replicates-across-seeds]]'
relationships:
- type: supported_by
  target: '[[grpo-three-seed-confirmatory]]'
  target_id: experiment:grpo-three-seed-confirmatory
  confidence: high
  evidence:
  - "experiments/grpo-three-seed-confirmatory/NOTEBOOK.md INSTRUMENT FINDING entry (scorers.py:281-289 denominator audit; correct_on_known_pct is the sole FILTERED-denominator metric among the five reported, all others use the full unknown- or known-labeled class as denominator)"
- type: related_to
  target: '[[grpo-abstention-shift-replicates-across-seeds]]'
  target_id: mechanism:grpo-abstention-shift-replicates-across-seeds
  confidence: medium
  evidence:
  - "experiments/grpo-three-seed-confirmatory/NOTEBOOK.md G1 ADJUDICATED PASS entry (flags the +7 pp correct_on_known_pct rise accompanying the G1 pass and blocks citing it until the denominator was resolved)"
---

Instrument finding from `grpo-three-seed-confirmatory`, confirmed against the
scorer source (`archive/experiment/phase1/eval/scorers.py`) and independently
re-derived by hand from row-level artifacts. `refusal_recall_pct`,
`answer_on_unknown_pct`, and `over_refusal_pct` all use a full-class
denominator (all unknown- or known-labeled rows) and are directly comparable
across arms with different refusal rates; `correct_on_known_pct` alone uses a
filtered denominator (answered knowns only) and is not. Standing rule adopted
from this finding: `correct_on_known_pct` must never be quoted across arms
with different refusal rates without stating its denominator, preferably
alongside the raw `correct_known` count. The mechanism is general to any
refusal-conditioned accuracy metric, not specific to GRPO or this lineage.
