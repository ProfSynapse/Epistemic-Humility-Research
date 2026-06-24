---
aliases:
- CounterFact dataset
- CF benchmark
- CounterFact
tags:
- kg/dataset
- concept
- dataset
kg:
  id: dataset:counterfact
  type: dataset
  status: canonical
area: mechanistic-interpretability
related:
- '[[2202.05262--rome-locating-editing-factual-associations]]'
- '[[zsre]]'
relationships:
- type: proposed_by
  target: '[[2202.05262--rome-locating-editing-factual-associations]]'
  target_id: paper:2202.05262
  confidence: high
- type: derived_from
  target: '[[zsre]]'
  target_id: dataset:zsre
---

CounterFact is a 21,919-record evaluation benchmark for model editing whose
records are counterfactual (false) Wikidata triples, designed so that a correct
edit requires the model to output a belief it was never trained to hold. Each
record includes paraphrase prompts for generalization, neighborhood subjects for
specificity testing, and generation probes for consistency and fluency, covering
criteria that earlier benchmarks such as [[zsre]] leave unmeasured.

**Why it matters here:** The benchmark's emphasis on specificity (not bleeding
edits into adjacent facts) mirrors the calibration concern in epistemic humility
research: a model that over-generalizes an edit is analogous to a model that
over-extends a confidence update.

**Lineage:** extends [[zsre]] by adding counterfactual records and a richer
multi-criteria evaluation suite.
