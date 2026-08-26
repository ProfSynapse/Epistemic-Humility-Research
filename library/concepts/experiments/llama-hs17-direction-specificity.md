---
title: llama-hs17-direction-specificity
aliases:
- Llama hs17 mid-band direction-specificity census
- llama's first verified direction-specific write
tags:
- kg/experiment
- experiment
- cross-family
- j-space
- doubt-snap
kg:
  id: experiment:llama-hs17-direction-specificity
  type: experiment
  status: canonical
related:
- '[[j-space-cross-family-layer-contrast]]'
- '[[caution-encoding-read-actuate-dissociation-across-families]]'
- '[[llama-hs17-write-is-direction-specific]]'
- '[[activation-steering]]'
- '[[known-unknown-direction]]'
- '[[abstention]]'
relationships:
- type: builds_on
  target: '[[j-space-cross-family-layer-contrast]]'
  target_id: experiment:j-space-cross-family-layer-contrast
  confidence: high
  evidence:
  - experiments/llama-hs17-direction-specificity/AMENDMENT.md (Design; reuses
    the frozen KU-gated c_hat write, gate, and dose verbatim from that
    experiment's resolved INCONCLUSIVE llama arm, at hs17)
- type: related_to
  target: '[[caution-encoding-read-actuate-dissociation-across-families]]'
  target_id: mechanism:caution-encoding-read-actuate-dissociation-across-families
  confidence: high
  evidence:
  - experiments/llama-hs17-direction-specificity/AMENDMENT.md (Motivation and
    posture; runs the missing random-direction verification at llama's one
    floor-clearing write, hs17, to adjudicate whether the "no verified
    selective write outside the Qwen lineage" reading still stands)
- type: related_to
  target: '[[activation-steering]]'
  target_id: method:activation-steering
  confidence: high
- type: related_to
  target: '[[known-unknown-direction]]'
  target_id: term:known-unknown-direction
  confidence: high
  evidence:
  - experiments/llama-hs17-direction-specificity/AMENDMENT.md (Design; reuses
    the frozen hs17 known-unknown read direction and c_hat caution write
    direction verbatim from the parent cell)
- type: supports
  target: '[[llama-hs17-write-is-direction-specific]]'
  target_id: mechanism:llama-hs17-write-is-direction-specific
  confidence: high
  evidence:
  - experiments/llama-hs17-direction-specificity/AMENDMENT.md#outcome (LG-G1,
    LG-G2)
- type: related_to
  target: '[[abstention]]'
  target_id: term:abstention
  confidence: medium
---

Exploratory cell on raw-base `unsloth/Llama-3.2-3B-Instruct` running the
missing verification step at llama's only write ever to clear a held-out
abstention floor: the cross-family layer-contrast program's mid-band site
hs17 (relative depth 0.607), where a frozen KU-gated `c_hat` write had
reached held-out confab `clean_tighten` 0.7420 with no random-direction
control and a non-diagnostic known-correct cost gate. This cell reruns the
gated write under a fresh decode seed (replication arm) alongside fifteen
fresh matched-dose random directions (seeds 910001-910015) on the same
frozen 872-row confab and 334-row known-correct held-out pools.

Resolved 2026-08-25, prediction confirmed. LG-G1 (replication): arm-1 held-out
`clean_tighten` 635/872 = 0.7282 (Wilson 95% [0.6977, 0.7567]) against the
0.50 floor, PASS, and consistent with the parent's 0.7420 under overlapping
Wilson intervals. LG-G2 (direction-specificity): effect ratio (gated lift
0.7190) / (max abs random lift 0.0872, seed 910010) = 8.25 against the 3.0
floor, PASS; per-seed signed lifts skew positive (9/15) around a median of
+0.0023, far below the gated effect. LG-G3 (known-correct cost): the KU gate
fired 0/334 held-out known-correct rows, below the pre-registered
adjudicability floor of 22 fired rows, so the gate is NOT-ADJUDICABLE as
pre-stated, not PASS or FAIL. Llama becomes the second family, alongside
Qwen, with a verified direction-specific selective write; the site is
mid-band (hs17), not the late site the cross-family read-actuate
dissociation was measured at (see
[[caution-encoding-read-actuate-dissociation-across-families]]), which the
result confirms as a wrong-site rather than absent-mechanism explanation for
llama specifically. Source of truth:
`experiments/llama-hs17-direction-specificity/AMENDMENT.md`.
