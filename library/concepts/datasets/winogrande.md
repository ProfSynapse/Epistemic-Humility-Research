---
aliases:
- WinoGrande
tags:
- kg/dataset
- concept
- dataset
kg:
  id: dataset:winogrande
  type: dataset
  status: canonical
area: datasets
related:
- '[[2407.09298--transformer-layers-as-painters]]'
- '[[hellaswag]]'
relationships:
- type: evaluation_set_for
  target: '[[2407.09298--transformer-layers-as-painters]]'
  target_id: paper:2407.09298
  confidence: high
- type: related_to
  target: '[[hellaswag]]'
  target_id: dataset:hellaswag
---

WinoGrande is a large-scale benchmark of Winograd-schema-style pronoun
resolution problems, requiring commonsense reasoning to disambiguate which of
two candidate entities a pronoun refers to. It was adversarially filtered
from a larger crowdsourced pool to remove examples solvable by simple
statistical shortcuts.

**Why it matters here:** Used as a semantic/commonsense benchmark in
arXiv:2407.09298's layer-order and layer-skipping experiments, where it is
contrasted with mathematical/reasoning benchmarks (ARC, GSM8K) to show
semantic tasks are more robust to layer reordering and parallel execution
than reasoning tasks.

**Lineage:** a widely adopted commonsense-reasoning benchmark; no direct
lineage to other atoms in this vault.
