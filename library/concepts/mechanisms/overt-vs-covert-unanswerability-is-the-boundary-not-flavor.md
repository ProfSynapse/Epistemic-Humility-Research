---
title: overt-vs-covert-unanswerability-is-the-boundary-not-flavor
aliases:
- overt vs covert unanswerability is the operative boundary
- AmbigQA's covert ambiguity is unreadable in the pretrained base
- flavor-atlas-rawbase P2 failed / refines flavor-specific reading
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:overt-vs-covert-unanswerability-is-the-boundary-not-flavor
  type: mechanism
  status: canonical
cause: "Running the identical AmbigQA internal panel (2748 rows, 1245 known / 1503 unknown, pool sha256 b0f93658...48bfd) and probe protocol (M2) at every one of 37 layers on the raw pretrained unsloth/Qwen3-4B base, and evaluating the M4 cross-flavor transfer matrix between AmbigQA and the six KUQ flavors plus SelfAware, all on the same raw base and sweep as pretrained-base-carries-broad-overt-unanswerability-code."
effect: "AmbigQA never exceeds AUROC 0.6590 across all 37 layers (best L25; L35 reads 0.6338, matching the resolved rawbase-ambigqa-boundary-readout value exactly), while every KUQ flavor and SelfAware separate at 0.98-0.999 on the same base. Transfer is near-chance in both directions: every KUQ/SelfAware-trained probe evaluated on AmbigQA reads 0.4878 to 0.5746, and the AmbigQA-trained probe evaluated on every other flavor reads 0.4332 to 0.5853. P2 (both ambiguity surfaces stay below 0.75) FAILS as registered, since KUQ ambiguous itself reaches 0.9800; only the AmbigQA half of P2 held. Neither the universal-code falsifier (F1) nor the dataset-specific falsifier (F2) fires. The operative boundary in the pretrained base is therefore overt versus covert unanswerability, not flavor identity: KUQ's ambiguous category is marked overtly on the question surface and reads like every other overt flavor, while AmbigQA's referential ambiguity is covert and the pretrained base carries no usable linear signal for it at any layer."
polarity: decreases
related:
- '[[flavor-atlas-rawbase]]'
- '[[ambigqa-boundary-signal-is-pretraining-flavor-specific]]'
- '[[pretrained-base-carries-broad-overt-unanswerability-code]]'
- '[[answerability-probe-under-flags-ambiguous-questions]]'
- '[[rawbase-ambigqa-boundary-readout]]'
- '[[internal-paper3--knows-but-doesnt-say]]'
relationships:
- type: supported_by
  target: '[[flavor-atlas-rawbase]]'
  target_id: experiment:flavor-atlas-rawbase
  confidence: high
  evidence:
  - "NOTEBOOK.md 2026-08-10T01:55Z RESULT, M2 and M4 tables; P2/F1/F2
    adjudication"
- type: related_to
  target: '[[ambigqa-boundary-signal-is-pretraining-flavor-specific]]'
  target_id: mechanism:ambigqa-boundary-signal-is-pretraining-flavor-specific
  confidence: high
  evidence:
  - "NOTEBOOK.md 2026-08-10T01:55Z RESULT (this mechanism REFINES that
    mechanism's reading: the earlier cell resolved only that the
    AmbigQA-specific gap is flavor-specific, i.e. present pre-training and
    not training-installed, framed as SelfAware-vs-AmbigQA; this mechanism
    replaces the SelfAware-vs-everything framing with an overt-vs-covert
    framing that explains why the broad KUQ code transfers so freely while
    AmbigQA alone remains an outlier)"
- type: related_to
  target: '[[pretrained-base-carries-broad-overt-unanswerability-code]]'
  target_id: mechanism:pretrained-base-carries-broad-overt-unanswerability-code
  confidence: high
  evidence:
  - "NOTEBOOK.md 2026-08-10T01:55Z RESULT (companion finding from the same
    sweep: that mechanism is the 'every overt flavor reads well' half,
    this is the 'AmbigQA/covert reads badly' half)"
- type: related_to
  target: '[[answerability-probe-under-flags-ambiguous-questions]]'
  target_id: mechanism:answerability-probe-under-flags-ambiguous-questions
  confidence: medium
  evidence:
  - "NOTEBOOK.md 2026-08-10T01:55Z M1 ambiguous row (0.9800) (that
    mechanism found KUQ-labeled ambiguous questions under-flagged, AUROC
    0.92, on the raw INSTRUCT base with generation; this mechanism finds
    KUQ ambiguous reads at 0.9800 on the raw PRETRAINED base with
    forward-only extraction - a substrate/measurement difference worth
    flagging, not a direct contradiction, since one measures behavioral
    under-flagging post-generation and the other measures linear
    separability pre-generation)"
- type: related_to
  target: '[[rawbase-ambigqa-boundary-readout]]'
  target_id: experiment:rawbase-ambigqa-boundary-readout
  confidence: high
  evidence:
  - "NOTEBOOK.md 2026-08-10T01:55Z M2 (0.6338 at L35 reproduces that cell's
    committed heldout_probe_auroc exactly to 4dp)"
- type: related_to
  target: '[[internal-paper3--knows-but-doesnt-say]]'
  target_id: paper:internal-paper3
  confidence: high
  evidence:
  - "papers/paper-3-knows-but-doesnt-say/manuscript.md lines 1070-1075,
    Section 8 'Where the internal readout fails: covert ambiguity' ('The
    dividing line is therefore not flavor but overt versus covert')"
---

`flavor-atlas-rawbase`'s P2-failed, refining finding. AmbigQA is the one
exception, in both directions, to the broad overt-unanswerability code
described in [[pretrained-base-carries-broad-overt-unanswerability-code]]:
it never clears AUROC 0.6590 at any of 37 layers, and probes trained
elsewhere fail to transfer into it (and vice versa) at rates indistinguishable
from chance. Because KUQ's own ambiguous category reads at 0.9800 on the
same raw base, the failure cannot be explained by "ambiguity" as a flavor -
it is explained by whether the unanswerability is marked overtly on the
question's surface (KUQ ambiguous, and every other KUQ flavor, plus
SelfAware) or covertly, as AmbigQA's referential underspecification is.

**Why it matters here:** this REFINES
[[ambigqa-boundary-signal-is-pretraining-flavor-specific]], the mechanism
that resolved the prior pretraining-flavor-vs-training-warp fork. That
cell established only that the AmbigQA-specific gap predates training; it
could not distinguish "SelfAware-flavored" from "overt-flavored" because it
tested a single comparator (AmbigQA vs SelfAware). This atlas adds six more
overt flavors and shows they all pattern with SelfAware, not with AmbigQA,
which relocates the boundary from a dataset-pair distinction to a
overt-vs-covert distinction. For paper 3 (Section 8, "Where the internal
readout fails: covert ambiguity"), this is the evidence behind the
paper's own framing: what pretraining supplies is an overt-unanswerability
signal, not a general answerability signal, and covert referential
ambiguity is a distinct, harder hallucination surface because judging it
requires retrieving the competing answers a question admits, not merely
reading the prompt.

**Registered caveat (travels with this claim):** exploratory atlas with a
registered style confound (see
[[pretrained-base-carries-broad-overt-unanswerability-code]] for the full
statement); promotion to a claim requires a style-controlled confirmatory
cell, not yet registered.

**Lineage:** companion to
[[pretrained-base-carries-broad-overt-unanswerability-code]] from the same
sweep; refines [[ambigqa-boundary-signal-is-pretraining-flavor-specific]];
reproduces [[rawbase-ambigqa-boundary-readout]]'s L35 reading exactly.
Source of truth: `experiments/flavor-atlas-rawbase/NOTEBOOK.md`, RESULT
entry, 2026-08-10T01:55Z.
