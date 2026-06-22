---
aliases:
- BiB
- Bias in Bios dataset
- Bias in Bios (BiB)
tags:
- kg/dataset
- concept
- dataset
kg:
  id: dataset:bias-in-bios
  type: dataset
  status: canonical
area: mechanistic-interpretability
related:
- '[[sparse-feature-circuits]]'
- '[[shift-feature-trimming]]'
- '[[sparse-autoencoder]]'
relationships:
- type: related_to
  target: '[[sparse-feature-circuits]]'
  target_id: method:sparse-feature-circuits
- type: related_to
  target: '[[shift-feature-trimming]]'
  target_id: method:shift-feature-trimming
---

Bias in Bios is a dataset of professional biographies with labels for both
profession (the intended classification signal) and gender (a spurious
correlate). It was constructed to benchmark model robustness to spurious
correlations: in the ambiguous split, gender perfectly predicts the profession
label, while in the balanced split gender is equalized across professions,
isolating whether a model relies on the spurious cue.

**Why it matters here:** The dataset provides a controlled testbed for studying
whether sparse feature circuits encode and transmit spurious gender signal, and
whether targeted ablation methods such as [[shift-feature-trimming]] can remove
that signal without degrading profession accuracy.

**Lineage:** used as a classification benchmark in mechanistic-interpretability
work on [[sparse-feature-circuits]] and [[shift-feature-trimming]].
