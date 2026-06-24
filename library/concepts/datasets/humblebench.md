---
aliases:
- HumbleBench
- HumbleBench benchmark
tags:
- kg/dataset
- concept
- dataset
kg:
  id: dataset:humblebench
  type: dataset
  status: canonical
area: datasets
related:
- '[[2509.09658--humblebench-epistemic-humility-multimodal]]'
- '[[epistemic-humility]]'
- '[[multimodal-large-language-model]]'
- '[[hallucination]]'
- '[[abstention]]'
relationships:
- type: proposed_by
  target: '[[2509.09658--humblebench-epistemic-humility-multimodal]]'
  target_id: paper:2509.09658
  confidence: high
- type: related_to
  target: '[[epistemic-humility]]'
  target_id: term:epistemic-humility
- type: related_to
  target: '[[multimodal-large-language-model]]'
  target_id: term:multimodal-large-language-model
- type: related_to
  target: '[[hallucination]]'
  target_id: term:hallucination
- type: related_to
  target: '[[abstention]]'
  target_id: term:abstention
---

HumbleBench is a multimodal hallucination benchmark of 22,831 five-way
multiple-choice questions that tests an MLLM's ability to reject plausible but
incorrect answers and select "None of the above" (NOTA) when no listed option
matches the image. Each item probes one of three fine-grained hallucination
types: object, relation, or attribute. Questions are constructed from the
Panoptic Scene Graph (PSG) dataset's dense scene-graph annotations, with
GPT-4-Turbo (and InstructBLIP in the generation loop) producing the questions and
distractors, followed by a rigorous manual filtering pass. It was introduced by
Tong et al. 2025 (arXiv:2509.09658, maifoundations/HumbleBench).

**Why it matters here:** HumbleBench operationalizes [[epistemic-humility]] as a
forced-choice abstention task in the visual domain. Its central finding, that
state-of-the-art models clear random-guess accuracy on standard items but
collapse on NOTA-only and pure-noise-image cases, makes it the multimodal analog
of the text-only abstention/NOTA framing in the Phase 1 SFT-vs-DPO-vs-KTO study,
and a reference for over-commitment under uncertainty.

**Lineage:** introduced by
[[2509.09658--humblebench-epistemic-humility-multimodal]]; derived from the
Panoptic Scene Graph dataset; related to [[hallucination]] and [[abstention]].
