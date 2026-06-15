---
aliases:
- PaLM 2-M
- PaLM 2 Medium
tags:
- kg/model
- concept
- model
kg:
  id: model:palm-2
  type: model
  status: canonical
area: models
---

PaLM 2 Medium is the medium-sized variant of Google's PaLM 2 base language
model family. It serves as the primary subject of fine-tuning experiments in the
unfamiliar-finetuning-examples study, where SFT data composition is manipulated
to isolate the effect of unfamiliar training examples on closed-book QA accuracy.

**Why it matters here:** Results from PaLM 2-M establish that the hallucination
mechanism driven by [[unfamiliar-finetuning-examples]] generalizes beyond
open-source model families, supporting the mechanistic claim rather than treating
it as an artifact of a particular architecture.

**Lineage:** no formal lineage edges to other atoms.
