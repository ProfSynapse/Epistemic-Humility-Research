---
title: flavor-atlas-rawbase
aliases:
- Flavor atlas
- per-flavor known-unknown activations on the raw base
- overt-vs-covert unanswerability boundary atlas
tags:
- kg/experiment
- experiment
- epistemic-humility
kg:
  id: experiment:flavor-atlas-rawbase
  type: experiment
  status: canonical
related:
- '[[rawbase-ambigqa-boundary-readout]]'
- '[[ambigqa-boundary-signal-is-pretraining-flavor-specific]]'
- '[[known-unknown-questions]]'
- '[[selfaware]]'
- '[[known-unknowns-taxonomy]]'
- '[[internal-paper3--knows-but-doesnt-say]]'
- '[[pretrained-base-carries-broad-overt-unanswerability-code]]'
- '[[overt-vs-covert-unanswerability-is-the-boundary-not-flavor]]'
relationships:
- type: builds_on
  target: '[[rawbase-ambigqa-boundary-readout]]'
  target_id: experiment:rawbase-ambigqa-boundary-readout
  confidence: high
  evidence:
  - "AMENDMENT.md Motivation and posture (same substrate, unsloth/Qwen3-4B
    revision 64033659..., raw pretrained base, no adapter; direct PI
    follow-on continuation of the just-resolved rawbase-ambigqa-boundary-readout
    cell, 2026-08-09 directive: 'see if we can find actual activations
    based on other known unknown flavors')"
- type: related_to
  target: '[[ambigqa-boundary-signal-is-pretraining-flavor-specific]]'
  target_id: mechanism:ambigqa-boundary-signal-is-pretraining-flavor-specific
  confidence: high
  evidence:
  - "AMENDMENT.md Motivation and posture, NOTEBOOK.md 2026-08-10T01:55Z
    (this atlas REFINES that mechanism's flavor-specific reading: the
    boundary is not SelfAware-vs-everything-else but overt-vs-covert
    unanswerability; see overt-vs-covert-unanswerability-is-the-boundary-not-flavor)"
- type: evaluates_on
  target: '[[known-unknown-questions]]'
  target_id: dataset:known-unknown-questions
  confidence: high
  evidence:
  - "AMENDMENT.md Design E1 (KUQ screened panel, 5540 rows, six flavor
    categories, item 26's screen pool)"
- type: evaluates_on
  target: '[[selfaware]]'
  target_id: dataset:selfaware
  confidence: high
  evidence:
  - "AMENDMENT.md Design E3 (all of datasets/selfaware/SelfAware.json, 3369
    rows, positive reference flavor)"
- type: related_to
  target: '[[known-unknowns-taxonomy]]'
  target_id: term:known-unknowns-taxonomy
  confidence: high
  evidence:
  - "AMENDMENT.md Motivation and posture (KUQ's six-category flavor taxonomy
    is the atlas's organizing axis)"
- type: related_to
  target: '[[internal-paper3--knows-but-doesnt-say]]'
  target_id: paper:internal-paper3
  confidence: high
  evidence:
  - "papers/paper-3-knows-but-doesnt-say/manuscript.md lines 1056-1094,
    'Where the internal readout fails: covert ambiguity' (Section 8 cites
    experiments/flavor-atlas-rawbase/AMENDMENT.md directly for the M1/M4
    numbers)"
- type: supports
  target: '[[pretrained-base-carries-broad-overt-unanswerability-code]]'
  target_id: mechanism:pretrained-base-carries-broad-overt-unanswerability-code
  confidence: high
  evidence:
  - "NOTEBOOK.md 2026-08-10T01:55Z RESULT (M1, M4)"
- type: supports
  target: '[[overt-vs-covert-unanswerability-is-the-boundary-not-flavor]]'
  target_id: mechanism:overt-vs-covert-unanswerability-is-the-boundary-not-flavor
  confidence: high
  evidence:
  - "NOTEBOOK.md 2026-08-10T01:55Z RESULT (M2, M4 AmbigQA rows; P2 FAILED,
    neither falsifier fires, registered MIXED ATLAS verdict)"
---

Tier-3 exploratory probe-fit atlas (resolved 2026-08-10), direct PI
follow-on to `rawbase-ambigqa-boundary-readout`. Asks whether OTHER flavors
of unanswerability (KUQ's six categories: ambiguous, controversial,
counterfactual, false assumption, future unknown, unsolved problem; plus
SelfAware and AmbigQA as reference flavors) each have their own separable
activation signature in the raw, untrained `unsloth/Qwen3-4B` base
(revision `64033659d5caf1b8ed7f929b29de705e93a4d468`, no adapter, bf16), at
possibly different layers, or whether the pretrained known-unknown code is
narrow (SelfAware-flavored only) or universal (one code for all flavors).
Three forward-only, all-layer extractions (KUQ 5540 rows, AmbigQA 2748
rows, SelfAware 3369 rows) feed four CPU probe sweeps (M1 per-flavor
layer map, M2 AmbigQA layer sweep, M3 SelfAware reference, M4 cross-flavor
transfer matrix), byte-identical probe protocol to item 26
(`ood-breadth-beyond-selfaware`)'s pinned `internal_panel_probe_gate.py`.

**Result, MIXED ATLAS as registered** (neither falsifier fired): P1
(future unknown and/or unsolved problem reach AUROC >= 0.90) SUPPORTED -
every KUQ flavor separates at 0.98 to 0.999 best-layer held-out AUROC and
transfers freely to every other flavor and SelfAware (0.83 to 0.9996). P2
(ambiguity flavors stay below 0.75 at every layer) FAILED as registered -
KUQ ambiguous reaches 0.9800, far above the 0.75 ceiling; only the AmbigQA
half of P2 held (max 0.6590 across all 37 layers, near-chance transfer both
directions). Descriptive reading: the pretrained base carries a broad,
freely-transferring OVERT-unanswerability code covering all six KUQ
flavors and SelfAware, including overtly ambiguous KUQ questions; what it
cannot read at any layer is AmbigQA's COVERT referential ambiguity. The
dividing line is overt versus covert unanswerability, not flavor per se.
Registered caveat: this is an exploratory atlas with a registered style
confound (KUQ/SelfAware unknowns are stylistically distinctive question
types), stated before any confirmatory use; promotion to a claim requires
a style-controlled confirmatory cell (matched surface form, flavor
varied), not yet registered.

This directly feeds paper 3's Section 8 discussion, "Where the internal
readout fails: covert ambiguity," which cites this amendment by name for
the M1/M4 numbers.

Source of truth: `experiments/flavor-atlas-rawbase/AMENDMENT.md`,
`gates.yaml`, `experiment.yaml`, and `NOTEBOOK.md` (RESULT entry,
2026-08-10T01:55Z).
