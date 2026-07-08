---
schema_version: research-session/v1
session_id: 20260706T150244Z-an-purge-guardrails-ao-propensity-caution-redesign
title: an-purge-guardrails-ao-propensity-caution-redesign
status: active
created_at: '2026-07-06T15:02:44Z'
updated_at: '2026-07-06T15:03:45Z'
phase: mechinterp / actuation
question: How do we permanently stop the recurring stale-claim failure, correct the
  bungled AN, and design the propensity-regulated caution experiment the user actually
  wanted?
tags:
- guardrails
- ao
- actuation
run_ids: []
trajectory:
  anchor: experiment/protocol/research-trajectory.md
  current_position: ''
  changed_by_session: ''
checkpoints:
- id: 001-checkpoint
  at: '2026-07-06T15:03:45Z'
  kind: checkpoint
  title: Checkpoint
  summary: "Open state at checkpoint: 4 PRs held for user review (none merged) \u2014\
    \ #227 guardrails+hooks, #226 AN confounded-null correction, #228 KG null-atom\
    \ backfill, plus the AO draft branch (no PR until signed). harness-builder running:\
    \ generic tuner proportional-gain feature (Synaptic-Tuner PR) + AO cell.yaml/gates.yaml,\
    \ CPU-only. AK Stage 2 completed on Modal (DONE 14:32:59Z, app ap-jPgOtPQGaWu4yeC3YX7q7j);\
    \ doc updated to LAUNCHED+approved; AK-G1/G2/G3 verdict scoring + queued AM launch\
    \ still parked. NEXT: (1) review/merge the 4 PRs; (2) sign AO after harness returns\
    \ (exp sign, then user GPU approval, then Stage 1->Stage 2); (3) dark-matter actuator\
    \ exploration \u2014 screen the 12 frozen dark-displacement candidates (PR #222\
    \ lab notebook) as candidate actuators via the same knob-discovery screen AO Stage\
    \ 1 uses; (4) AK verdict + AM."
  evidence: []
  run_ids: []
  commands: []
  decisions: []
  next_steps: []
  signals: {}
legacy_session:
  id: 0039
  path: docs/sessions/0039 - an-purge-guardrails-ao-propensity-caution-redesign.md
---
# an-purge-guardrails-ao-propensity-caution-redesign

## Question

How do we permanently stop the recurring stale-claim failure, correct the bungled AN, and design the propensity-regulated caution experiment the user actually wanted?

## Trajectory Position

RQ4 control-system arc. AC (doubt-regulated caution) remains the standing
use-the-signal WIN (+8.7pt selectivity). This session corrected the record on
AN, then designed AO to test the user's actual hypothesis (confab-propensity
regulating caution, the AC mechanism applied to confabulation).

## Summary

Three threads, in order.

1. SYSTEMIC FIX (the recurring stale-claim failure). For the second or third
   time the lead had asserted a false actuation taxonomy: "input-side actuates,
   write-side activation edits null." It is false because AC is a WRITE-side
   erase-write on caution_perp that PASSED (+8.7pt, CI [+5.6, +12.0]). Fix
   shipped in PR #227: a READ BEFORE YOU CITE guardrail in AGENTS.md/CLAUDE.md
   (never state a fact about a prior experiment without reading its amendment
   doc; memory/notes/KG are navigation aids, not citable results), an Environment
   section (canonical checkout /home/profsynapse/code/Epistemic-Humility-Research
   on ext4; /mnt/f is a frozen backup where bin/search hangs), and three
   project-local hooks: block_memory_write.sh (bars writes to agent memory,
   nudges to a session note), session_note_tracker.sh (nudges every 15 turns),
   launch_guard.sh (blocks modal run / sbatch / hf jobs run until an
   EHR_LAUNCH_OK=<slug> token confirms the signed doc was updated first). All 60
   agent-memory files were deleted; durable knowledge is now in-repo only.
   taxonomy-scout (read-only sweep) confirmed the wrong taxonomy survived in
   exactly one repo file (docs/sessions/20260703T140000Z-amendment-ag-asymmetric-compliance-mi-fog-of-war.md), now corrected; everything else
   was already right.

2. AN CORRECTED, NOT ACCEPTED. The an-resolve agent had written PR #226 with the
   wrong taxonomy and called AN a clean write-side null. Corrected across the
   amendment doc, KG mechanism atom, internal note, and PR body: AN is a
   CONFOUNDED null. Its actuator was caution_perp REFIT on AI-TRUE (cosine -0.064
   with AC's validated GRPO-v2 direction, essentially orthogonal), never shown to
   be a lever there (the section 6 knob-validation screen was deferred). So AN
   cannot separate "caution cannot suppress confabulation" from "this refit
   direction is a dead actuator." PR #226 held for user re-adjudication, not
   merged. Separately, KG backfill PR #228 (librarian) added the missing
   resolved-null atoms for AA/AB/AI plus an AC-win atom, all cross-linked and
   scoped by entry-point x axis x write-form x population x outcome, so the
   correct picture is now structural in the graph. 0 validator errors.

3. AO DESIGNED (the experiment the user actually wanted). experiments/
   ao-propensity-regulated-caution scaffolded via bin/exp new (new experiments-
   first layout), branch amendment-ao-propensity-regulated-caution. Faithful AC
   analog for confabulation: sensor = confab-propensity readout standardized per
   row (prop_z), actuator = erase-write on a caution direction, gain
   g_i = +alpha*prop_z_i (continuous, proportional, clipped; mirror of AC's
   g_i = -alpha*z_i). Fixes AN's three confounds: (a) Stage 1 knob-validation
   validates a caution lever on AI-TRUE FIRST (wide net: AN refit + answer-vs-
   refuse + fresh fit); if none validates, that is the clean explanation AN could
   not give; (b) continuous proportional gain not a fixed shove; (c) permuted-
   signal placebo. Substrate AI-TRUE first (both calibration tails present: 116
   confabs that should refuse + 114 answerable-refused that should answer);
   GRPO-v2 is a pre-planned fast-follow (validated lever for free, needs
   propensity refit). GOAL IS BIDIRECTIONAL CALIBRATION, not one-way confab
   suppression: primary metric is a propensity-conditioned selectivity gap
   [delta_refusal(high-prop confabs) - delta_refusal(low-prop answerable-refused)]
   beating the placebo, exactly how AC won. Predictions recorded: user Stage 1
   PASS / Stage 2 PASS; orchestrator weak-lever Stage 1 PASS, small Stage 2
   positive (3-10pt), nontrivial chance Stage 1 fails.

   BLOCKER RESOLVED BY DECISION: the current tuner MechInterp cannot express
   AC-style continuous per-row gain (ArmConfig only does fixed strength + a
   threshold/flag selection, which IS AN's mechanism; AC's couple+gain-map lived
   in the now-frozen phase3 tree). User chose to EXTEND THE TUNER generically
   (not reuse frozen phase3). harness-builder is building a generic per-row
   proportional-gain arm mode (gain_field, permuted-gain control, ablate-writes-
   zero vs baseline-no-op) + tests as a Synaptic-Tuner submodule PR, then AO's
   cell.yaml/gates.yaml on it (CPU-only, nothing launched).

## Checkpoints
### 001-checkpoint - Checkpoint

- at: `2026-07-06T15:03:45Z`
- kind: `checkpoint`
- summary: Open state at checkpoint: 4 PRs held for user review (none merged) — #227 guardrails+hooks, #226 AN confounded-null correction, #228 KG null-atom backfill, plus the AO draft branch (no PR until signed). harness-builder running: generic tuner proportional-gain feature (Synaptic-Tuner PR) + AO cell.yaml/gates.yaml, CPU-only. AK Stage 2 completed on Modal (DONE 14:32:59Z, app ap-jPgOtPQGaWu4yeC3YX7q7j); doc updated to LAUNCHED+approved; AK-G1/G2/G3 verdict scoring + queued AM launch still parked. NEXT: (1) review/merge the 4 PRs; (2) sign AO after harness returns (exp sign, then user GPU approval, then Stage 1->Stage 2); (3) dark-matter actuator exploration — screen the 12 frozen dark-displacement candidates (PR #222 lab notebook) as candidate actuators via the same knob-discovery screen AO Stage 1 uses; (4) AK verdict + AM.
