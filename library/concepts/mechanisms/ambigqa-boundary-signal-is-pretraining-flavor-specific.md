---
title: ambigqa-boundary-signal-is-pretraining-flavor-specific
aliases:
- raw base reads AmbigQA boundary at the same low level as trained checkpoints
- flavor-specific reading confirmed, training-warp falsifier does not fire
- pretraining-flavor vs training-warp fork resolved flavor-specific
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:ambigqa-boundary-signal-is-pretraining-flavor-specific
  type: mechanism
  status: canonical
cause: "In rawbase-ambigqa-boundary-readout, the identical 2748-row AmbigQA internal panel (1245 known / 1503 unknown, pool sha256 b0f93658...48bfd), the identical layer-35 anchor-position extraction, and the pinned internal_panel_probe_gate.py protocol (5-fold, unchanged) from ood-breadth-beyond-selfaware's G7 were run on the raw, untrained Qwen3-4B base (unsloth/Qwen3-4B, revision 64033659d5caf1b8ed7f929b29de705e93a4d468, no adapter, bf16), to separate two accounts of item 26's G7 FAIL: a pretrained activation flavored to SelfAware-style unanswerability from the start (flavor-specific, pre-stated heldout_probe_auroc <= 0.73), versus a broader pretrained answerability signal that post-training warped or narrowed (training-warp, pre-stated falsifier heldout_probe_auroc >= 0.85)."
effect: "The raw base reads heldout_probe_auroc = 0.6338 (5-fold std 0.0104, n=2748), within 0.006 of both trained comparators fixed at signing (A1 0.6279, A4 0.6349). The prediction is SUPPORTED and the falsifier DOES NOT FIRE: the raw pretrained base already sits at the same low level as the trained checkpoints on the AmbigQA answerability boundary at this locus. Item 26's G7 non-transfer is resolved as a property of the pretrained representation, not a training-induced warp: the near-0.997 SelfAware internal readout is flavored to SelfAware-style unanswerability from pretraining onward, and post-training neither installed nor destroyed AmbigQA boundary information at layer 35, anchor position."
polarity: explains
related:
- '[[rawbase-ambigqa-boundary-readout]]'
- '[[ood-breadth-beyond-selfaware]]'
- '[[ambigqa-internal-readout-does-not-transfer-from-selfaware]]'
- '[[internal-paper3--knows-but-doesnt-say]]'
- '[[known-unknown-direction]]'
relationships:
- type: supported_by
  target: '[[rawbase-ambigqa-boundary-readout]]'
  target_id: experiment:rawbase-ambigqa-boundary-readout
  confidence: high
  evidence:
  - "experiments/rawbase-ambigqa-boundary-readout/NOTEBOOK.md 2026-08-09T23:30Z
    RESULT and gate adjudication"
- type: related_to
  target: '[[ood-breadth-beyond-selfaware]]'
  target_id: experiment:ood-breadth-beyond-selfaware
  confidence: high
  evidence:
  - "experiments/rawbase-ambigqa-boundary-readout/AMENDMENT.md Question (the
    fork this cell resolves, opened by item 26's G7 FAIL)"
- type: related_to
  target: '[[ambigqa-internal-readout-does-not-transfer-from-selfaware]]'
  target_id: mechanism:ambigqa-internal-readout-does-not-transfer-from-selfaware
  confidence: high
  evidence:
  - "experiments/rawbase-ambigqa-boundary-readout/NOTEBOOK.md 2026-08-09T23:30Z
    RESULT (this finding resolves that mechanism's open origin question)"
- type: related_to
  target: '[[internal-paper3--knows-but-doesnt-say]]'
  target_id: paper:internal-paper3
  confidence: medium
  evidence:
  - "experiments/rawbase-ambigqa-boundary-readout/AMENDMENT.md Reporting
    (feeds the paper-3 revision as the scoping sentence for the
    pretraining-origin claim)"
- type: related_to
  target: '[[known-unknown-direction]]'
  target_id: term:known-unknown-direction
  confidence: high
  evidence:
  - "experiments/rawbase-ambigqa-boundary-readout/cell.yaml (layer 35, anchor
    position, the same direction locus item 26 read)"
---

The raw-base cell resolves the fork item 26's G7 FAIL opened. Reading the
identical AmbigQA internal panel and probe protocol on the raw, untrained
Qwen3-4B base gives heldout_probe_auroc 0.6338, statistically indistinguishable
from both trained comparators (0.6279 and 0.6349) and far below the 0.85
training-warp falsifier. Post-training did not narrow a once-broader
answerability signal at this locus; the signal was already narrow before any
training began.

**Why it matters here:** this closes the open question
[[ambigqa-internal-readout-does-not-transfer-from-selfaware]] left standing.
It reframes the internal known-unknown readout's near-perfect SelfAware
performance as a property of what pretraining installed, specific to
SelfAware-style unanswerability, rather than a general answerability axis
that training later degraded. For paper 3's Result 1 (the internal
answerability axis, AUROC 0.997 on SelfAware), this is direct evidence the
axis's high fidelity is itself a SelfAware-construct artifact of pretraining,
not a post-training achievement and not a post-training loss.

**Lineage:** resolves the fork opened by
[[ambigqa-internal-readout-does-not-transfer-from-selfaware]], the headline
finding of [[ood-breadth-beyond-selfaware]] (paper-3 limitations burn-down
item 26). Source of truth:
`experiments/rawbase-ambigqa-boundary-readout/NOTEBOOK.md`, RESULT entry,
2026-08-09T23:30Z.
