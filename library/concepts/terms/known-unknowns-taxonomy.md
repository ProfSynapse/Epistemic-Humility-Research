---
aliases:
- unknown question categories
- KUQ categories
- uncertainty categorization
- Known-Unknowns Taxonomy
tags:
- kg/term
- concept
- term
kg:
  id: term:known-unknowns-taxonomy
  type: term
  status: canonical
area: epistemic-humility
related:
- '[[2305.13712--kuq-knowledge-of-knowledge]]'
- '[[knowledge-boundary]]'
relationships:
- type: proposed_by
  target: '[[2305.13712--kuq-knowledge-of-knowledge]]'
  target_id: paper:2305.13712
  confidence: high
- type: derived_from
  target: '[[knowledge-boundary]]'
  target_id: term:knowledge-boundary
---

The Known-Unknowns Taxonomy is a 7-category framework classifying why a question lacks a definitive answer: Future Unknown (outcome not yet determined), Unsolved Problem or Mystery (open scientific or philosophical question), Controversial or Debatable (reasonable disagreement among experts), Question with False Assumption (the premise is wrong), Counterfactual Question (asks about an unrealized world), Underspecified Question (missing context prevents a unique answer), and Known Question (has a correct answer, used as the positive foil). The taxonomy was introduced with the KUQ dataset to ensure that unknowability is treated as a structured property rather than a monolithic label.

**Why it matters here:** The abstention study aims to teach models to abstain specifically on questions where abstention is warranted. The taxonomy clarifies that "warranted abstention" is not uniform: false-assumption and underspecified questions require a different communicative response than genuinely open scientific mysteries, informing how abstention training data should be categorized.

**Lineage:** extends [[knowledge-boundary]]; instantiated in [[known-unknown-questions]] as proposed by [[2305.13712--kuq-knowledge-of-knowledge]].
