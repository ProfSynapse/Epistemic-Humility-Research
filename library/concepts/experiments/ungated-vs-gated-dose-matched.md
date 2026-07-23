---
title: ungated-vs-gated-dose-matched
aliases:
- Registered ungated-vs-gated dose-matched arm for the caution snap (H4)
- H4
tags:
- kg/experiment
- experiment
kg:
  id: experiment:ungated-vs-gated-dose-matched
  type: experiment
  status: canonical
related:
- '[[qwen3-4b-l34-dose200-write-non-selective-gate-supplies-selectivity]]'
- '[[caution-write-selectivity-is-content-dependent-not-gate-created]]'
- '[[known-unknown-direction]]'
- '[[activation-steering]]'
relationships:
- type: supports
  target: '[[qwen3-4b-l34-dose200-write-non-selective-gate-supplies-selectivity]]'
  target_id: mechanism:qwen3-4b-l34-dose200-write-non-selective-gate-supplies-selectivity
  confidence: high
  evidence:
  - experiments/ungated-vs-gated-dose-matched/AMENDMENT.md#outcome
- type: related_to
  target: '[[caution-write-selectivity-is-content-dependent-not-gate-created]]'
  target_id: mechanism:caution-write-selectivity-is-content-dependent-not-gate-created
  confidence: high
  evidence:
  - experiments/ungated-vs-gated-dose-matched/AMENDMENT.md#outcome (binding scope statement 2)
- type: related_to
  target: '[[known-unknown-direction]]'
  target_id: term:known-unknown-direction
  confidence: medium
- type: related_to
  target: '[[activation-steering]]'
  target_id: method:activation-steering
  confidence: medium
---

Registered, signed exploratory test (paper 5 review memo hardening item H4)
of whether the resolved doubt-gated caution snap's most-quoted mechanism
sentence, that the write is non-selective and the doubt gate supplies all of
the instrument's selectivity, holds as a registered dose-every-row contrast
rather than a citation of unregistered diagnostic scratch. It reuses the
resolved instrument verbatim (direction, gate threshold, standardization,
held-out split; no refit) on raw-base Qwen3-4B, and doses the SAME 443
held-out rows (185 confab, 258 known-correct) at the SAME setpoint
(dose_target 200.0 along c_hat, scope anchor_onward) in two arms: gate-on
(the resolved re-run) and gate-off (every row dosed unconditionally).

Resolved 2026-07-13. **All gates pass; the falsifier did not fire.**
Gate-on reproduces the resolved instrument exactly (confab clean_tighten
73.5%, known-correct cost 3.1%, instrument-validity anchor H4-G0 PASS).
Ungated known-correct damage is 60.1% (155/258) versus gated 3.1% (8/258), a
57.0pp gap far exceeding the registered 15pp margin (paired McNemar
p = 4.2e-43 over 258 rows; H4-G1 PASS); ungated confab conversion (77.8%)
exceeds gated (73.5%) by only 4.3pp, well inside the 15pp parity bound
(H4-G2 PASS). Two binding scope statements are recorded at resolve: the
60.1% figure is a not-well-formed-correct damage rate (144 clean
false-refusals, 10 answered-wrong, 1 degenerate), not a refusal rate, and it
supersedes rather than reproduces the earlier unregistered 36.2% diagnostic;
and the non-selectivity finding is scoped to the Qwen3-4B / L34 / dose-200
operating point, reconciled with, not contradicted by, the Qwen3.5-4B
mid-band ladder's opposite-looking permuted-gate result
([[qwen3-4b-l34-dose200-write-non-selective-gate-supplies-selectivity]]).
Source of truth: `experiments/ungated-vs-gated-dose-matched/AMENDMENT.md`.
