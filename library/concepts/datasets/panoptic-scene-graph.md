---
aliases:
- Panoptic Scene Graph
- PSG
- PSG dataset
tags:
- kg/dataset
- concept
- dataset
kg:
  id: dataset:panoptic-scene-graph
  type: dataset
  status: canonical
area: datasets
related:
- '[[humblebench]]'
relationships:
- type: related_to
  target: '[[humblebench]]'
  target_id: dataset:humblebench
---

The Panoptic Scene Graph (PSG) dataset (Yang et al. 2022, ECCV) provides
pixel-level panoptic segmentation masks for objects together with their pairwise
relations, offering finer granularity than bounding-box scene-graph datasets. It
contains over 40,000 images with, on average, 11.04 objects and 5.65 relations
per image plus multiple captions.

**Why it matters here:** PSG is the ground-truth source for
[[humblebench]]: its dense, verifiable object and relation annotations let the
benchmark construct multiple-choice hallucination questions with known-correct
answers, while attribute cues are added separately and manually verified. The
quality of PSG annotations is what makes the "None of the above" option
trustworthy.

**Lineage:** source dataset that [[humblebench]] is derived from.
