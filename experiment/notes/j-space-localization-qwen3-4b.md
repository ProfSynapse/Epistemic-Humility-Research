---
title: 'J-space localization on Qwen3-4B'
kg:
  id: experiment:j-space-localization-qwen3-4b
  type: experiment
  status: canonical
tags:
  - kg/experiment
status: done
governance: exploratory
phase: phase1
lane: cloud
est_compute: 'Completed: 10760.2 seconds on Modal A10/A10G-class GPU for n_prompts=1000'
relationships:
  - type: tests
    target: '[[j-space-mediated-actuation-fragility]]'
    target_id: mechanism:j-space-mediated-actuation-fragility
    confidence: medium
  - type: builds_on
    target: '[[tc-2026-workspace--verbalizable-representations-global-workspace]]'
    target_id: paper:tc-2026-workspace
    confidence: high
  - type: builds_on
    target: '[[jacobian-lens]]'
    target_id: method:jacobian-lens
    confidence: high
  - type: related_to
    target: '[[global-workspace]]'
    target_id: term:global-workspace
    confidence: high
related:
  - '[[j-space-mediated-actuation-fragility]]'
  - '[[tc-2026-workspace--verbalizable-representations-global-workspace]]'
  - '[[jacobian-lens]]'
  - '[[global-workspace]]'
---

## Question & Hypothesis

Does a from-scratch Jacobian lens on Qwen3-4B localize a workspace-like band
relative to this project's existing L34 write layer, and do the fitted epistemic
directions verbalize as uncertainty, abstention, answer, or error tokens?

Hypothesis: the final-layer J-lens should match the direct unembed baseline;
the workspace-like band should be mid-to-late but short of the final layers; and
the caution-flavored directions should verbalize more clearly than the
confab-propensity direction.

Falsifier: this was a lab diagnostic rather than a confirmatory claim, so the
only hard go/no-go was the implementation smoke. If the final-layer J-lens had
failed to track the direct unembed baseline, the characterization would not have
been trusted.

## Design

The governed source of truth is
`experiments/j-space-localization-qwen3-4b/AMENDMENT.md`. The instrument is
`experiments/j-space-localization-qwen3-4b/jlens.py`, run on
`unsloth/Qwen3-4B` bf16 with 1000 prompts fetched at runtime from private HF
staging and represented in the public repo only by the committed row-key
manifest.

The H1 direction inputs were same-substrate bf16 refits copied into
`experiments/j-space-localization-qwen3-4b/analysis-committed/source_directions/`.
The run measured a final-layer smoke, H1 direction verbalizations around L34,
and a depth profile across hs indices 2, 5, 8, 11, 14, 17, 20, 23, 26, 29, 32,
35, and 36.

## Prerequisites & Gating

Before launch, the local smoke had to show strong agreement between the
final-layer J-lens and direct unembed. Paid Modal launch also required explicit
lead approval plus `EHR_LAUNCH_OK=j-space-localization-qwen3-4b` and a Modal cost
cap.

The result has already completed. Future causal follow-ups are not authorized by
this note; they require a fresh registered design because this note records a
read-only characterization.

## Runbook

1. Read `experiments/j-space-localization-qwen3-4b/AMENDMENT.md` and
   `experiments/j-space-localization-qwen3-4b/NOTEBOOK.md`.
2. Inspect result provenance under
   `experiments/j-space-localization-qwen3-4b/analysis-committed/results/jspace-jlens-r1/`.
3. For reruns, use the checked-in Modal harness
   `experiments/j-space-localization-qwen3-4b/cloud/modal_jlens.py` only after
   refreshing its pinned repo commit and repeating the launch gates.
4. For interpretation, cite the resolved Outcome rather than this KG note.

## Validation contract

Definition of done for the completed run: `smoke_full.json`, `h1_full.json`,
`profile_full.json`, `DONE`, and provenance are committed; the containment scan
finds no prompt/question text; `bin/exp validate` passes; and the experiment is
resolved.

The actual full-corpus smoke passed with mean cosine 0.9811106324195862, mean
top-10 overlap 0.82, and 3/5 top-1 matches.

## Outputs & provenance

Committed outputs live under
`experiments/j-space-localization-qwen3-4b/analysis-committed/results/jspace-jlens-r1/`.
The run tag was `jspace-jlens-r1`; Modal app `ap-vnvIl5WaUIDDwhEN2UWwFF`;
function call `fc-01KWZ03RBXAK7HQKV7SQ4AM9GX`; seed 20260707; n_prompts 1000.

Result summary: `u_d_L34` verbalized as answer/reply-like; `pos_ctrl_L34` and
`c_hat_L34` verbalized as self/absence/error/impossibility-like; `neg_ctrl_L34`
was a noisy local null. The effective-dimensionality profile peaked at hs=26
and formed a broader hs=23-29 workspace-like band. L34 maps to hs=34, just after
that band.

## Variations

- Local prelaunch smoke: passed.
- Local pre-swap H1/profile orientation: not the launch substrate; kept only as
  notebook context.
- Full Modal run `jspace-jlens-r1`: completed and resolved.
- Proposed next variant: a causal mid-band versus late-layer write sweep. That
  is a successor experiment, not a rerun of this characterization.

## Status log

- 2026-07-07: Modal full-corpus run completed, results committed, experiment
  resolved, and PR #250 merged to main.
- 2026-07-07: KG note added after merge to make the finding discoverable by the
  typed research graph.
