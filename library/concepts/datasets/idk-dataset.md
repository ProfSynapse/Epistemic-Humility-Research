---
aliases:
- I don't know dataset
- model-specific Idk dataset
- Say-I-Dont-Know dataset
tags:
- kg/dataset
- concept
- dataset
kg:
  id: dataset:idk-dataset
  type: dataset
  status: canonical
area: datasets
related:
- '[[2401.13275--can-ai-assistants-know-what-they-dont-know]]'
- '[[triviaqa]]'
relationships:
- type: proposed_by
  target: '[[2401.13275--can-ai-assistants-know-what-they-dont-know]]'
  target_id: paper:2401.13275
  confidence: high
- type: derived_from
  target: '[[triviaqa]]'
  target_id: dataset:triviaqa
---

The Idk dataset is a model-specific training corpus built from [[triviaqa]] by
sampling multiple model responses per question, computing per-question accuracy,
and labeling questions as "known" or "unknown" relative to a tunable
[[ik-threshold]]. For questions the model does not know, the target response is
a templated refusal; for known questions the target is the correct answer. The
dataset is used to align an assistant to refuse questions it cannot answer while
still answering those it can.

**Why it matters here:** The Idk dataset is the training signal for both
[[idk-sft]] and the DPO/RL variants in the Cheng et al. pipeline, making it
directly analogous to the abstention training sets used in our locked training-regimen
SFT-vs-DPO-vs-KTO comparison.

**Lineage:** derives from [[triviaqa]]; proposed by
[[2401.13275--can-ai-assistants-know-what-they-dont-know]].
