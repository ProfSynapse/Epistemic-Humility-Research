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
- '[[panoptic-scene-graph]]'
- '[[false-option-rejection]]'
- '[[humility-score]]'
- '[[epistemic-humility]]'
- '[[multimodal-large-language-model]]'
- '[[hallucination]]'
- '[[abstention]]'
relationships:
- type: proposed_by
  target: '[[2509.09658--humblebench-epistemic-humility-multimodal]]'
  target_id: paper:2509.09658
  confidence: high
- type: derived_from
  target: '[[panoptic-scene-graph]]'
  target_id: dataset:panoptic-scene-graph
- type: related_to
  target: '[[false-option-rejection]]'
  target_id: term:false-option-rejection
- type: related_to
  target: '[[humility-score]]'
  target_id: metric:humility-score
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

HumbleBench is a large-scale multimodal hallucination benchmark of 22,831 five-way
multiple-choice questions in which one option is always "None of the above"
(NOTA), testing whether an MLLM can reject all plausible-but-wrong options and
abstain when no listed answer is supported by the image. Each item targets one of
three hallucination types: object, relation, or attribute. It is built from the
[[panoptic-scene-graph]] (PSG) dataset (4,500 sampled images): object and relation
labels come from PSG annotations, attribute cues from InstructBLIP (Vicuna-7B),
and GPT-4-Turbo generates the questions and plausible distractors, followed by
manual filtering (41,843 candidates down to 22,831 final). Introduced by Tong et
al. 2025 (arXiv:2509.09658, maifoundations/HumbleBench).

**Why it matters here:** HumbleBench operationalizes the rejection facet of
[[epistemic-humility]] as a forced-choice task in the visual domain. Its central
finding, that models clear random-guess accuracy on standard items but average
near random (26.61%) on the NOTA-only stress test while humans score 92%, makes
it the multimodal analog of the text-only abstention/NOTA framing in the Phase 1
SFT-vs-DPO-vs-KTO study, and a reference for over-commitment under uncertainty.

**Lineage:** introduced by
[[2509.09658--humblebench-epistemic-humility-multimodal]]; derived from
[[panoptic-scene-graph]]; reports [[humility-score]]; instantiates
[[false-option-rejection]].
