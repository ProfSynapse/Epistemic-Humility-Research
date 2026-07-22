---
title: Known/Unknown Direction
aliases:
  - epistemic abstention direction
  - known-unknown activation direction
  - knowledge-boundary direction
  - doubt direction (retired mentalistic name, see margin-theory-framework.md)
tags:
  - kg/term
  - concept
  - term
kg:
  id: term:known-unknown-direction
  type: term
  status: canonical
area: terms
related:
  - '[[knowledge-boundary]]'
  - '[[truth-direction]]'
  - '[[refusal-direction]]'
  - '[[correlational-probe]]'
relationships:
  - type: related_to
    target: '[[knowledge-boundary]]'
    target_id: term:knowledge-boundary
    confidence: high
  - type: different_from
    target: '[[truth-direction]]'
    target_id: term:truth-direction
    confidence: medium
  - type: different_from
    target: '[[refusal-direction]]'
    target_id: term:refusal-direction
    confidence: medium
  - type: related_to
    target: '[[correlational-probe]]'
    target_id: method:correlational-probe
    confidence: high
---

A known/unknown direction is this project's operational name for an activation
direction estimated from known-vs-unknown question contrasts. It must not be
treated as a truth direction, safety-refusal direction, or causal abstention
mechanism until controlled interventions show that it moves the relevant
behavior.

**Naming caveat (2026-07-16 vocabulary revision):** this node's name and
symbol (c_hat) are unchanged, but prior working prose in this project called
the same direction the "doubt direction," a mentalistic name the
gate-contribution factorial showed was carrying argumentative weight the
evidence had not earned. See `docs/research/margin-theory-framework.md`
section 3 for the full old-to-new mapping and section 3's earnability
criterion for mentalistic names: a name like "doubt" is earned only when the
activation (a) tracks actual ignorance, (b) drives abstention when amplified,
(c) does so direction-specifically, and (d) responds to evidence the way
doubt should (supplying the true answer in-context should collapse the
projection and lengthen the row's [[commitment-margin]]). Qwen currently
satisfies (a) through (c); (d) is untested. Mistral fails (c)
([[boundary-anisotropy]]), so mentalistic naming is retired for mistral
regardless of (d).

