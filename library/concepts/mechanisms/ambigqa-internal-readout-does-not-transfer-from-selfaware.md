---
title: ambigqa-internal-readout-does-not-transfer-from-selfaware
aliases:
- G7 FAIL, internal known-unknown readout does not transfer to AmbigQA
- SelfAware internal readout collapses on the AmbigQA answerability boundary
- item 26 headline finding
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:ambigqa-internal-readout-does-not-transfer-from-selfaware
  type: mechanism
  status: canonical
cause: "In ood-breadth-beyond-selfaware (paper-3 limitations burn-down item 26), the pinned internal_panel_probe_gate.py protocol (5-fold cross-validation without correct/wrong leakage, layer 35, anchor position) fit a held-out known-unknown probe on the identical 2748-row AmbigQA internal panel (1245 known / 1503 unknown) for the two arms with a published SelfAware internal comparator, A1 (clean SFT) and A4 (SFT-to-GRPO-v2), against the registered G7 gate: held-out AUROC >= 0.90 and a margin of at least 0.15 over the same checkpoint's emitted AUROC on the 1832 shared rows."
effect: "Both arms fail G7: held-out probe AUROC 0.6279 (A1) and 0.6349 (A4), far below the 0.90 floor and far below paper 3's SelfAware values of 0.9968 and 0.9971 for the same two checkpoints. The margin-over-emitted leg also fails narrowly (0.1326 and 0.1379 vs the 0.15 floor). The internal known-unknown readout that separates SelfAware known from unknown near-perfectly collapses to near-chance-adjacent on the AmbigQA answerability boundary at the identical locus, protocol, and checkpoints. This does not falsify paper 3's registered falsifier for this cell (which reads emitted, not internal, AUROC), but it directly narrows manuscript lines 346-347 (\"the discriminating signal exists internally and the verbalized number is a collapsed near-constant\") to SelfAware rather than a general claim."
polarity: complicates
related:
- '[[ood-breadth-beyond-selfaware]]'
- '[[internal-paper3--knows-but-doesnt-say]]'
- '[[known-unknown-direction]]'
- '[[answerability-subspace]]'
- '[[rawbase-ambigqa-boundary-readout]]'
- '[[ambigqa-boundary-signal-is-pretraining-flavor-specific]]'
- '[[selfaware]]'
relationships:
- type: supported_by
  target: '[[ood-breadth-beyond-selfaware]]'
  target_id: experiment:ood-breadth-beyond-selfaware
  confidence: high
  evidence:
  - "experiments/ood-breadth-beyond-selfaware/NOTEBOOK.md 2026-08-09T16:45Z Stage 8
    (G7 verdict, lead-verified from g7_A1.json / g7_A4.json)"
- type: related_to
  target: '[[internal-paper3--knows-but-doesnt-say]]'
  target_id: paper:internal-paper3
  confidence: high
  evidence:
  - "papers/paper-3-knows-but-doesnt-say/manuscript.md lines 346-347, 387-390,
    1027-1029 (the internal-axis claim and the SelfAware-only limitation this
    finding narrows)"
- type: related_to
  target: '[[known-unknown-direction]]'
  target_id: term:known-unknown-direction
  confidence: high
  evidence:
  - "experiments/ood-breadth-beyond-selfaware/AMENDMENT.md Internal panel (layer
    35, anchor position, the frozen known-unknown-direction locus)"
- type: related_to
  target: '[[answerability-subspace]]'
  target_id: term:answerability-subspace
  confidence: medium
  evidence:
  - "experiments/ood-breadth-beyond-selfaware/AMENDMENT.md Internal panel (reads
    the AmbigQA answerability boundary at this locus)"
- type: related_to
  target: '[[rawbase-ambigqa-boundary-readout]]'
  target_id: experiment:rawbase-ambigqa-boundary-readout
  confidence: high
  evidence:
  - "experiments/rawbase-ambigqa-boundary-readout/AMENDMENT.md Question (the
    direct follow-on fork this finding opened: pretraining-flavor vs
    training-warp)"
- type: related_to
  target: '[[ambigqa-boundary-signal-is-pretraining-flavor-specific]]'
  target_id: mechanism:ambigqa-boundary-signal-is-pretraining-flavor-specific
  confidence: high
  evidence:
  - "experiments/rawbase-ambigqa-boundary-readout/NOTEBOOK.md 2026-08-09T23:30Z
    RESULT (resolves this finding's origin question)"
- type: related_to
  target: '[[selfaware]]'
  target_id: dataset:selfaware
  confidence: high
  evidence:
  - "experiments/ood-breadth-beyond-selfaware/AMENDMENT.md (the comparator
    values, 0.9968/0.9971, are paper 3's SelfAware internal readout for the
    same two checkpoints)"
---

Paper 3's internal known-unknown readout, near-perfect on SelfAware (AUROC
0.9968 for clean SFT, 0.9971 for SFT-to-GRPO-v2), does not transfer to the
AmbigQA answerability boundary at the identical L35 anchor-position locus and
probe protocol: held-out AUROC lands at 0.6279 and 0.6349 on the same two
checkpoints, against a registered 0.90 floor. This is the headline finding of
`ood-breadth-beyond-selfaware` (paper-3 limitations burn-down item 26): the
internal-vs-stated gap paper 3 reports is a real dissociation on SelfAware,
but the internal signal itself does not generalize to a construct as
different as AmbigQA's ambiguity-based unanswerability.

**Why it matters here:** this is the finding that directly forced paper 3's
SelfAware-only bullet (manuscript lines 1027-1029) to be narrowed rather than
deleted, and it opened the fork resolved by
[[ambigqa-boundary-signal-is-pretraining-flavor-specific]]: whether the
non-transfer reflects a pretrained representation that was always
SelfAware-flavored, or a training-induced warp of a once-broader signal. The
raw-base cell answered flavor-specific.

**Lineage:** headline finding of [[ood-breadth-beyond-selfaware]], resolved
2026-08-09. Read via the same [[known-unknown-direction]] locus paper 3
established. Source of truth:
`experiments/ood-breadth-beyond-selfaware/NOTEBOOK.md`, Stage 8 entry,
2026-08-09T16:45Z.
