---
title: pretrained-base-carries-broad-overt-unanswerability-code
aliases:
- broad overt-unanswerability code in the raw pretrained base
- one shared code for all six KUQ flavors plus SelfAware
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:pretrained-base-carries-broad-overt-unanswerability-code
  type: mechanism
  status: canonical
cause: "Fitting a linear known/unknown probe (5-fold, out-of-fold, StandardScaler + L2 LogisticRegression C=0.5) per KUQ unanswerability flavor (ambiguous, controversial, counterfactual, false assumption, future unknown, unsolved problem) against the shared 3071-row KUQ known pool, at every one of 37 layers, plus SelfAware as a seventh reference flavor, all on the raw pretrained unsloth/Qwen3-4B base (no adapter, no post-training, no task training), then evaluating a cross-flavor/SelfAware transfer matrix (M4) at each source's best layer."
effect: "Every KUQ flavor separates its own unknowns from the known pool at 0.98 to 0.999 best-layer held-out AUROC (ambiguous 0.9800, controversial 0.9960, counterfactual 0.9963, false assumption 0.9918, future unknown 0.9994, unsolved problem 0.9937), and SelfAware reads 0.9937. The M4 transfer matrix shows every pair among the six KUQ flavors and SelfAware transfers at 0.8331 to 0.9996 (minimum: the unsolved-problem probe reading ambiguous). The pretrained base carries one broad, freely-transferring overt-unanswerability code rather than six flavor-specific codes, already present before any post-training or task training of any kind."
polarity: enables
related:
- '[[flavor-atlas-rawbase]]'
- '[[unanswerability-detection-shares-one-axis-across-flavors]]'
- '[[answerability-axis-present-without-task-training]]'
- '[[overt-vs-covert-unanswerability-is-the-boundary-not-flavor]]'
- '[[known-unknowns-taxonomy]]'
relationships:
- type: supported_by
  target: '[[flavor-atlas-rawbase]]'
  target_id: experiment:flavor-atlas-rawbase
  confidence: high
  evidence:
  - "NOTEBOOK.md 2026-08-10T01:55Z RESULT, M1 and M4 tables"
- type: related_to
  target: '[[unanswerability-detection-shares-one-axis-across-flavors]]'
  target_id: mechanism:unanswerability-detection-shares-one-axis-across-flavors
  confidence: high
  evidence:
  - "NOTEBOOK.md 2026-08-10T01:55Z M4 (that mechanism found the same
    near-flat cross-flavor transfer, off-diagonal 0.988 vs diagonal 0.998,
    on the raw INSTRUCT base with generation and behavior arms; this
    mechanism finds the same one-shared-axis pattern one training stage
    earlier, on the raw PRETRAINED base with forward-only extraction and
    no generation, extending the 'one gate, not six' reading back to
    before any post-training)"
- type: related_to
  target: '[[answerability-axis-present-without-task-training]]'
  target_id: mechanism:answerability-axis-present-without-task-training
  confidence: medium
  evidence:
  - "NOTEBOOK.md 2026-08-10T01:55Z RESULT (both mechanisms show a
    pretraining-origin answerability signal; this one adds that the
    pretrained signal is broad across overt unanswerability flavors, not
    scoped to one dataset)"
- type: related_to
  target: '[[overt-vs-covert-unanswerability-is-the-boundary-not-flavor]]'
  target_id: mechanism:overt-vs-covert-unanswerability-is-the-boundary-not-flavor
  confidence: high
  evidence:
  - "NOTEBOOK.md 2026-08-10T01:55Z RESULT (the companion finding from the
    same sweep: this mechanism is the 'every overt flavor reads well' half,
    the companion mechanism is the 'AmbigQA/covert reads badly' half)"
- type: related_to
  target: '[[known-unknowns-taxonomy]]'
  target_id: term:known-unknowns-taxonomy
  confidence: high
  evidence:
  - "AMENDMENT.md Motivation and posture (KUQ's six-category taxonomy is
    the organizing axis of the atlas)"
---

`flavor-atlas-rawbase`'s P1-supported finding. Six labeled KUQ
unanswerability categories, read on the raw pretrained Qwen3-4B base with
no post-training and no task training of any kind, each separate their own
unknowns at 0.98-0.999 best-layer held-out AUROC, and a probe trained on
any one of them (or SelfAware) reads every other one at 0.83 or better.
This is a "one code, not six" result: the pretrained representation does
not maintain flavor-specific detectors, it maintains one broad detector
that generalizes freely across overtly-marked unanswerability surfaces.

**Why it matters here:** extends `unanswerability-detection-shares-one-axis-across-flavors`
(the same shared-axis finding, measured on the raw INSTRUCT base with
generation) one training stage earlier, to the raw PRETRAINED base with
forward-only extraction only. Combined with the companion finding
[[overt-vs-covert-unanswerability-is-the-boundary-not-flavor]], this
reframes what "flavor-specific" meant in the prior fork resolved by
[[ambigqa-boundary-signal-is-pretraining-flavor-specific]]: the pretrained
code is not narrowly SelfAware-shaped, it is broad across every flavor
whose unanswerability is marked on the question's surface.

**Registered caveat (travels with this claim):** this is an exploratory
atlas with a registered style confound. KUQ and SelfAware unknowns are
stylistically distinctive question types, so a within-dataset known-versus-
unknown probe may ride surface style in part. Free cross-dataset transfer
(KUQ probes reading SelfAware at 0.91-0.98 and vice versa) argues against a
pure dataset artifact but does not eliminate style as a shared carrier. A
style-controlled confirmatory cell (matched surface form, flavor varied) is
the natural follow-up and must be registered before any promotion of this
atlas reading to a claim.

**Lineage:** builds on [[flavor-atlas-rawbase]], the direct PI follow-on to
[[ambigqa-boundary-signal-is-pretraining-flavor-specific]] (which resolved
only the AmbigQA-specific pretraining-origin fork). Source of truth:
`experiments/flavor-atlas-rawbase/NOTEBOOK.md`, RESULT entry,
2026-08-10T01:55Z.
