---
title: Margin Theory of Epistemic State
aliases:
- margin theory of epistemic state
- margin theory
- margin-theory framework
tags:
- kg/term
- concept
- term
kg:
  id: term:margin-theory-of-epistemic-state
  type: term
  status: canonical
area: terms
related:
- '[[commitment-margin]]'
- '[[boundary-anisotropy]]'
- '[[known-unknown-direction]]'
- '[[write-selectivity-is-operating-point-dependent]]'
- '[[gate-contribution-factorial]]'
- '[[ungated-vs-gated-dose-matched]]'
- '[[qwen35-4b-midband-doubt-snap]]'
- '[[margin-mapping]]'
- '[[qwen-midband-commitment-margins-miss-separation-floor]]'
relationships:
- type: related_to
  target: '[[commitment-margin]]'
  target_id: term:commitment-margin
  confidence: high
  evidence:
  - docs/research/margin-theory-framework.md (section 2, Claim 1)
- type: related_to
  target: '[[boundary-anisotropy]]'
  target_id: term:boundary-anisotropy
  confidence: high
  evidence:
  - docs/research/margin-theory-framework.md (section 2, Claim 4)
- type: related_to
  target: '[[known-unknown-direction]]'
  target_id: term:known-unknown-direction
  confidence: high
  evidence:
  - docs/research/margin-theory-framework.md (section 3)
- type: related_to
  target: '[[write-selectivity-is-operating-point-dependent]]'
  target_id: mechanism:write-selectivity-is-operating-point-dependent
  confidence: high
  evidence:
  - docs/research/margin-theory-framework.md (section 2, Claim 2)
- type: related_to
  target: '[[gate-contribution-factorial]]'
  target_id: experiment:gate-contribution-factorial
  confidence: high
  evidence:
  - docs/research/margin-theory-framework.md (section 1, anchor result 3)
- type: related_to
  target: '[[ungated-vs-gated-dose-matched]]'
  target_id: experiment:ungated-vs-gated-dose-matched
  confidence: high
  evidence:
  - docs/research/margin-theory-framework.md (section 1, anchor result 1)
- type: related_to
  target: '[[qwen35-4b-midband-doubt-snap]]'
  target_id: experiment:qwen35-4b-midband-doubt-snap
  confidence: high
  evidence:
  - docs/research/margin-theory-framework.md (section 1, anchor result 2)
- type: related_to
  target: '[[margin-mapping]]'
  target_id: experiment:margin-mapping
  confidence: high
  evidence:
  - experiments/margin-mapping/AMENDMENT.md (Outcome, resolved 2026-07-17)
- type: related_to
  target: '[[qwen-midband-commitment-margins-miss-separation-floor]]'
  target_id: mechanism:qwen-midband-commitment-margins-miss-separation-floor
  confidence: high
  evidence:
  - experiments/margin-mapping/AMENDMENT.md (Outcome, resolved 2026-07-17)
---

The margin theory of epistemic state is the program's working framework
(adopted 2026-07-16) for how a model's knowledge status is encoded and how
steering interventions interact with it. Four claims: (1) knowledge is
encoded as distance to an abstention boundary, the per-row
[[commitment-margin]]; (2) dose regime determines who supplies selectivity,
with a mid-band regime where the boundary push self-sorts rows and an
overdrive regime where the gate is the sole source of selectivity (see
[[write-selectivity-is-operating-point-dependent]]); (3) epistemic
information exists in two channels, a readout channel (probe or gate score
on the [[known-unknown-direction]]) and a susceptibility channel (the
margin), which may dissociate; (4) [[boundary-anisotropy]] is
substrate-dependent, direction-specific on the Qwen mid-band point and
generic on the Mistral point.

**Why it matters here:** the framework reconciles three anchor results that
initially point in opposite directions on gate-vs-write attribution
([[gate-contribution-factorial]], [[ungated-vs-gated-dose-matched]],
[[qwen35-4b-midband-doubt-snap]]) and generates the M1-M6 experiment
cascade (margin mapping, susceptibility-as-probe, anisotropy panel,
evidence-responsiveness naming test, training bridge, scale). It also
registers the vocabulary revision: doubt direction to known-unknown
direction, doubt gate to KU readout gate, caution write to boundary push,
confab propensity split into baseline confab rate vs commitment margin,
with a four-part earnability criterion for mentalistic names.

**Claim 1 status (first empirical test, 2026-07-17):** the
[[margin-mapping]] experiment (M1) measured per-row margins directly and
resolved FALSIFIED as registered at the qwen mid-band operating point: the
censoring-aware observable separation bound came out 2.0 against the
registered 2.5 floor, while setpoint placement (Claim 2's mid-band
geometry), retrodiction of the anchor rates, and construct integrity all
passed (see [[qwen-midband-commitment-margins-miss-separation-floor]]).
Margins are real and correctly placed; the registered quantitative
separation was not met at ladder resolution. Mistral was void by
instrument loss and Claims 1-2 remain untested there.

**Lineage:** working framework, not a governed claims surface; the prose
home is `docs/research/margin-theory-framework.md` and every experimental
fact in it cites a governed amendment Outcome. Claims become registered
only through the cascade's signed amendments (first: the margin-mapping
experiment). Supersedes the informal gate-supplies-selectivity account
falsified at mid-band by [[gate-contribution-factorial]].
