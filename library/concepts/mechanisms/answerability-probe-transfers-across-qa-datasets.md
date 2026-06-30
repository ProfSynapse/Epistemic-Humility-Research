---
aliases:
- A linear answerability probe transfers across QA datasets
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:answerability-probe-transfers-across-qa-datasets
  type: mechanism
  status: canonical
cause: "Fitting a linear answerability probe on one QA dataset and applying it to held-out QA datasets."
effect: "The probe retains high answerability-decoding accuracy on the other datasets, indicating a dataset-general rather than dataset-specific answerability representation."
polarity: enables
related:
- '[[2310.11877--curious-case-hallucinatory-un-answerability-finding-truths]]'
- '[[answerability-subspace]]'
- '[[linear-probe]]'
- '[[squad]]'
- '[[natural-questions]]'
- '[[musique]]'
relationships:
- type: supported_by
  target: '[[2310.11877--curious-case-hallucinatory-un-answerability-finding-truths]]'
  target_id: paper:2310.11877
  confidence: high
- type: related_to
  target: '[[answerability-subspace]]'
  target_id: term:answerability-subspace
  confidence: high
- type: related_to
  target: '[[linear-probe]]'
  target_id: method:linear-probe
  confidence: high
---

Slobodkin et al. 2023 report that the linear answerability probe transfers across
SQuAD, Natural Questions, and MuSiQue, decoding answerability on datasets it was
not fit on. This cross-dataset transfer is the external precedent for the
Amendment P finding that an answerability readout transfers across datasets.
