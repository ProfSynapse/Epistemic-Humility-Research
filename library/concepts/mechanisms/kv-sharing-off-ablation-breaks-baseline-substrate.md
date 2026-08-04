---
aliases:
- disabling Gemma-4's KV-sharing destroys baseline behavior before any injection
- C1 precondition control forecloses the sharing ON/OFF primary contrast
- sharing-OFF ablation is too blunt to isolate the KV-sharing variable
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:kv-sharing-off-ablation-breaks-baseline-substrate
  type: mechanism
  status: canonical
cause: "Gemma-4-E4B-it's cross-layer KV-sharing (blocks 24-41 reading frozen K/V from donor blocks 22 and 23 through the cache object) is disabled with a registered, preflight-verified patch (kv_seam_patch.kv_sharing) that makes every formerly-shared block recompute its own K/V from its own retained trained projections, with no dosed injection applied -- an undosed C1 vs undosed C0 baseline comparison on the FIT split."
effect: "Baseline known-correct behavior collapses even without any write: the not_well_formed_correct cost rises from 0/180 rows (C0, sharing ON) to 180/180 rows (C1, sharing OFF), a delta whose Newcombe 95% CI [0.9704, 1.0] sits far outside the registered 0.05 cap / 0.10 CI bound, and mean per-token NLL nearly quadruples (3.5342 to 12.3303, relative delta 2.4889). The registered g0_c1_precondition_control therefore FAILS, and the sharing-OFF arms (A2, A4) resolve NOT-RUN and INCONCLUSIVE as pre-registered: the primary sharing-ON-vs-OFF contrast cannot fire. The ablation as built is too blunt an instrument to isolate the KV-sharing variable without also breaking the substrate it is meant to probe; any successor quarantine test needs a gentler ablation."
polarity: prevents
related:
- '[[gemma4-e4b-kv-seam-quarantine]]'
- '[[gemma-4]]'
relationships:
- type: supported_by
  target: '[[gemma4-e4b-kv-seam-quarantine]]'
  target_id: experiment:gemma4-e4b-kv-seam-quarantine
  confidence: high
  evidence:
  - experiments/gemma4-e4b-kv-seam-quarantine/AMENDMENT.md#outcome (Phase B
    and C1 section)
  - experiments/gemma4-e4b-kv-seam-quarantine/NOTEBOOK.md (2026-07-31 C1
    real-run raw verdict block and the same-day adjudication entry lifting
    the C0 positive-control hold)
- type: related_to
  target: '[[gemma-4]]'
  target_id: model:gemma-4
  confidence: high
---

C1 is a precondition control, not an outcome measurement: it asks whether
turning Gemma-4-E4B's KV-sharing off breaks the model on its own, before any
steering write is applied. It failed decisively on its known-correct
criterion (criterion 1), which the design had pre-registered as the
criterion that would be attributed if C1 failed, and that is exactly what
happened -- the delta survives the entire disputed range of the C0
comparator (even at the most favorable historical C0 estimate the gap would
still be an order of magnitude over the cap). The likelihood criterion
(criterion 3, mean NLL) is reported only as "C1 assigns lower likelihood to
C0's output" per its registered interpretive constraint, since it is
confounded with text divergence and cannot stand alone as forward-pass
evidence; the hedge criterion (criterion 2) passes vacuously on a substrate
that cannot emit well-formed output at all, and is not read as evidence the
OFF model behaves normally.

Because C1 gates the sharing-OFF arms, this instrument finding directly
forecloses the experiment's registered primary contrast (A1 sharing-ON vs
A2 sharing-OFF at the same site) without resolving the KV-quarantine
hypothesis either way on that axis. The hypothesis is left to rest entirely
on the sharing-ON depth ladder instead -- see
[[gemma-actuation-localizes-shallow-of-kv-seam]] -- which supports but does
not establish it. Source: [[gemma4-e4b-kv-seam-quarantine]].
