---
aliases:
- Zero-Shot Relation Extraction benchmark
- Zero-Shot Relation Extraction (zsRE)
- zsRE
- zero-shot relation extraction benchmark
tags:
- kg/dataset
- concept
- dataset
kg:
  id: dataset:zsre
  type: dataset
  status: canonical
area: mechanistic-interpretability
related:
- '[[counterfact]]'
relationships:
- type: related_to
  target: '[[counterfact]]'
  target_id: dataset:counterfact
---

zsRE (Zero-Shot Relation Extraction) is a benchmark originally designed for
zero-shot reading comprehension and repurposed as a standard evaluation set for
model-editing methods. It supplies subject-relation-object triples and
associated question prompts, but its records reflect facts the model already
assigns high probability to, which limits its ability to stress-test edit
difficulty or measure downstream effects on specificity.

**Why it matters here:** As the predecessor benchmark to [[counterfact]], zsRE
illustrates that measuring only efficacy on already-known facts understates the
challenge of bounded editing, a problem structurally similar to measuring
calibration only on high-confidence queries.

**Lineage:** extended by [[counterfact]], which adds counterfactual records and
a multi-criteria evaluation suite to address zsRE's coverage gaps.
