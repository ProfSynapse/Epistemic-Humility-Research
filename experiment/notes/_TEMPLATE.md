---
title: '<human title>'
kg:
  id: experiment:<slug>
  type: experiment
  status: canonical
status: proposed
governance: exploratory
phase: phase3
lane: local
est_compute: '<one line, e.g. ~6 GPU-hours on one RTX 3090>'
relationships:
  - type: tests
    target: '[[<gap-or-mechanism-slug>]]'
    target_id: gap:<slug>
    confidence: high
  - type: builds_on
    target: '[[<arxiv>--<slug>]]'
    target_id: paper:<arxiv>
related:
  - '[[<gap-or-mechanism-slug>]]'
  - '[[<arxiv>--<slug>]]'
---

## Question & Hypothesis

<RQ, hypothesis, falsifier. For locked/amendment notes, cite the PROTOCOL.md
section instead of restating pre-registered claims.>

## Design

<Arms/conditions, pinned models, datasets, metric panel, seeds / sample size /
power. Exploratory notes carry this inline.>

## Prerequisites & Gating

<What must exist or pass before a run, and the gating commands.>

## Runbook

<Ordered steps: setup -> run -> eval -> document. Point each at a checked-in
script/recipe by path, e.g. `experiment/phase1/probe/hidden_state_linear_probe.py`.
Bake in approval gates for cost-incurring or destructive actions.>

## Validation contract

<Pre-run assertions (counts), post-run checks (artifacts exist + schema-valid),
and the definition of done.>

## Outputs & provenance

<Where run records / eval / session notes land; how results feed (or do not feed)
the meta-analysis.>

## Variations

<The sweep and how each variant differs.>

## Status log

- YYYY-MM-DD: created (proposed).
