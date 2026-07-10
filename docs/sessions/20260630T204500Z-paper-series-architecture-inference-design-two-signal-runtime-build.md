---
schema_version: research-session/v1
session_id: 20260630T204500Z-paper-series-architecture-inference-design-two-signal-runtime-build
title: Paper-series re-architecture + inference design + two-signal runtime build
status: active
created_at: '2026-06-30T20:45:00Z'
updated_at: '2026-06-30T20:45:00Z'
track: research
question: How do the findings break into a series of papers that build toward a flagship,
  what claims need shoring up, how would the two-signal readout be wired into live
  inference, and can we build a runnable reference pipeline (calibrated gate + dial
  + veto) the user can talk to?
tags:
- experiment-runner
run_ids: []
trajectory:
  anchor: docs/research-trajectory.md
  current_position: 'The deliverable (a surfaced, thresholdable trust number that
    tracks whether THIS answer is correct) is now both (a) re-architected into a 3-paper
    series leading to a flagship, with a confirmatory cross-family plan, and (b) realized
    as a runnable reference pipeline - calibrated gate + dial + veto on the raw Qwen3-4B
    base, talk-to-the-model CLI. Calibration (the flagship #1 do-item) landed - dial
    ECE 0.151 to 0.023, gate ECE 0.0156 to 0.0105 - turning the rank into a thresholdable
    probability. Amendment X cross-size sweep - 1.7B PASS all three gates, 8B extracting,
    14B pending.'
  changed_by_session: true
checkpoints:
- id: 001-decision
  at: '2026-06-30T19:00:00Z'
  kind: decision
  title: 3-paper series leading to a flagship
  summary: Re-architected the findings into a series (papers/series/plan.md). Paper
    1 The Abstention Tax (lit review + SFT/DPO/KTO/GRPO four-way + the tension); Paper
    2 It Knows It Won't Say (internal-vs-stated gap, training-resistant); Paper 3
    Confidence Is a Readout Not a Lesson (flagship, training-free two-signal readout).
    Papers state confirmed claims cleanly and never name amendments; the amendment
    trail is internal record only.
  signals:
    papers: 3
    flagship: 3
- id: 002-decision
  at: '2026-06-30T19:30:00Z'
  kind: decision
  title: Confirmatory backbone + claims audit
  summary: The flagship's confirmatory spine = a pre-registered cross-FAMILY replication
    (predict gate/dial/veto AUROCs, run once). Needs NO training (readout is training-free),
    so Papers 1-2 stay Qwen-only. Proposed set Qwen3-4B anchor + Llama 3.2 3B + Ministral
    3B + Gemma 4 E4B (post-cutoff; verify by compat smoke). Audit do-items - calibrate
    dial (done), fill-B natural-distribution dial, full baseline table; scope gate
    as category-answerability and training-free as no task-specific training.
  signals:
    confirmatory: cross-family
    new_families: 3
- id: 003-design
  at: '2026-06-30T20:00:00Z'
  kind: infrastructure
  title: Inference and serving architecture doc
  summary: Wrote docs/architecture/two-signal-readout-inference-serving.md. Base model
    never modified; a kilobyte linear tap reads two activations the model already
    computes; calibration map turns the dial into a probability; orchestration layer
    decides abstain/hedge/veto/surface. Covers tap points, capture paths, control
    flow, four injection patterns, the avoided activation-steering option, and a validated-vs-proposed
    honesty ledger.
  signals:
    doc: inference-serving
- id: 004-result
  at: '2026-06-30T20:20:00Z'
  kind: result
  title: Dial + gate calibration (flagship do-item 1)
  summary: fit_calibration.py (CPU, honest nested-CV) ships the lower-ECE map. Dial
    L20 AUROC 0.834, ECE 0.151 (G3 fail) to 0.023 (G3 pass), Platt. Gate L18 AUROC
    0.997, ECE 0.0156 to 0.0105, isotonic. ECE raw reproduces the prior S result exactly;
    AUROC unchanged (ranking preserved). The dial is now a thresholdable probability.
  evidence:
  - archive/experiment/phase1/probe/fit_calibration.py
  signals:
    dial_ece_before: 0.151
    dial_ece_after: 0.023
    gate_ece_after: 0.0105
- id: 005-result
  at: '2026-06-30T20:35:00Z'
  kind: result
  title: Runnable reference pipeline (library + CLI)
  summary: two_signal_runtime.py (TwoSignalReadout.generate_with_trust runs gate->abstain|generate->dial->veto,
    reusing the exact generation surface the dial was fit on) and two_signal_cli.py
    (talk-to-the-model REPL + one-shot). No-GPU self-check GREEN; compiles clean.
    Reference pipeline, not production serving; live GPU smoke pending the X sweep
    freeing the single GPU.
  evidence:
  - archive/experiment/phase1/probe/two_signal_runtime.py
  - archive/experiment/phase1/probe/two_signal_cli.py
  signals:
    self_check: green
    live_smoke: pending-gpu
- id: 006-result
  at: '2026-06-30T20:45:00Z'
  kind: result
  title: Amendment X 1.7B PASS; 8B running
  summary: "Qwen3-1.7B raw base passes all three locked gates - X-G1 gate 0.996, X-G2\
    \ dial 0.815, X-G3 veto 0.757 (CIs exclude 0.50); dial means ordered correct 0.558\
    \ > known 0.431 > halluc 0.219 > wrong 0.122. Within-SelfAware control 0.667 (weaker\
    \ than 4B). Verdict recorded in AMENDMENT-X \xA77. 8B extracting; 14B pending."
  evidence:
  - experiments/cross-model-size-sweep/AMENDMENT.md
  - archive/experiment/phase1/probe/amendment_x_qwen3-1.7b-bnb-4bit_result.json
  signals:
    x_gate: 0.996
    x_dial: 0.815
    x_veto: 0.757
legacy_session:
  id: paper-series-architecture-inference-design-two-signal-runtime-build-20260630
  path: docs/sessions/0031 - paper-series-architecture-inference-design-two-signal-runtime-build.md
---
# Session 0031 - Paper-series architecture, inference design, two-signal runtime build

Continues the two-signal arc from session 0030. Two halves: a research-strategy
pass (paper series + claims audit + a confirmatory plan) and an engineering build
(an inference design doc plus a runnable reference pipeline the user can talk to).

## 001 - decision: 3-paper series leading to a flagship

Re-architected the findings into a series that builds toward Paper 3 (flagship),
captured in `papers/series/plan.md`. Title format `[catchy]: [subtitle]`.

1. **The Abstention Tax** - lit review (the former standalone meta-analysis, folded
   in as motivation) + the SFT/DPO/KTO/**GRPO** four-way + the abstention-trades-
   calibration tension. GRPO added (was a post-lock exploratory arm; reported as an
   extension unless a confirmatory GRPO arm is registered).
2. **It Knows, It Won't Say** - internal-vs-stated gap (0.997 vs 0.52-0.56),
   training-resistant, steering-asymmetric. The diagnosis.
3. **Confidence Is a Readout, Not a Lesson** (flagship) - training-free two-signal
   readout (gate + dial + veto), calibrated, baselined, size- and family-general.

Convention locked: papers state confirmed claims cleanly and DO NOT name amendments;
the amendment trail is our internal record only. Headline claims rest on
pre-registered confirmatory runs, not on exploratory amendments.

## 002 - decision: confirmatory backbone + claims audit

**Confirmatory replication** explained and planned: an exploratory finding earns a
flat in-paper assertion only after a pre-registered run predicts it under untouched
conditions, then lands. The flagship's backbone = a **pre-registered cross-FAMILY**
replication: predict gate/dial/veto AUROCs before running, run once. Needs NO
training (the readout is training-free - one forward + a CPU probe per model), so
Papers 1-2 stay Qwen-only and only Paper 3 goes cross-family. Proposed set (size
held ~3-4B): Qwen3-4B anchor + Llama 3.2 3B + Ministral 3B + **Gemma 4 E4B**
(post-cutoff; architecture/modality verified empirically by a compat smoke, not
assumed). Multimodal is a non-issue: text-only input never fires the vision tower;
the work is per-family extraction plumbing.

**Claims audit do-items** (in the plan): (1) calibrate the dial [DONE this session];
(2) real natural-distribution dial evidence [fill option B, chosen]; (3) full
baseline table (verbalized / P(True) / max-softmax / semantic entropy). Scope-honestly
items: gate is category-answerability not competence; training-free = no task-specific
training; demote O's +95pt margin (partly circular) in favor of AUROC + selective
prediction.

## 003 - design: inference & serving architecture doc

Wrote `docs/architecture/two-signal-readout-inference-serving.md`. Core stance:
the base model is never modified; a kilobyte linear tap reads two activations the
model already computes; a calibration map turns the dial into a probability; the
orchestration layer (not the weights) decides abstain/hedge/veto/surface. Covers
the two tap points (pre-gen anchor = gate, post-gen content token = dial), inline
vs re-forward capture, the two-stage control flow, the four injection patterns, and
the one we deliberately avoid (activation steering - our own steering-asymmetry
result says it is unreliable). Includes a validated-vs-proposed honesty ledger.

## 004 - result: dial + gate calibration (the flagship #1 do-item)

`archive/experiment/phase1/probe/fit_calibration.py` (CPU, cached data). Honest nested-CV
calibration (calibrator never sees its own eval fold); ships the lower-ECE of
Platt/isotonic; saves a portable artifact (npz vectors + json manifest with metrics
and reliability bins). Results on Qwen3-4B Instruct base:

| signal | layer | AUROC | ECE raw | ECE calibrated | shipped |
|--------|-------|-------|---------|----------------|---------|
| dial (correctness, post) | L20 | 0.834 | 0.151 (G3 FAIL) | **0.023** (G3 PASS) | Platt |
| gate (answerability, pre) | L18 | 0.997 | 0.0156 | **0.0105** | isotonic |

ECE raw 0.151 reproduces the prior S result exactly (faithful). AUROC unchanged
(calibration preserves ranking). The G3 calibration miss flagged in the audit is now
a PASS. (Earlier this session I had mis-remembered Platt as already done; grep
confirmed it was not - the scorers only measured ECE + a risk-coverage curve.)

## 005 - result: runnable reference pipeline (library + CLI)

- `archive/experiment/phase1/probe/two_signal_runtime.py` - `TwoSignalReadout`: loads base
  model + gate/dial artifacts; `generate_with_trust(question)` runs gate (prompt-only
  forward at the anchor) -> abstain | generate -> dial (re-forward over [prompt+answer]
  at the content token) -> calibrated trust, with veto. Reuses the EXACT generation
  surface the dial was fit on (`SYSTEM_PROMPT`, `render_probe_prompt`,
  `_content_end_index`), so live reads match the validated offline surface (4.2 path).
  No-GPU self-check passes (artifacts load + apply).
- `archive/experiment/phase1/probe/two_signal_cli.py` - talk-to-the-model REPL (and `-q`
  one-shot): shows answerability, the answer, calibrated trust, and a LOW-TRUST flag
  on vetoed answers; `:set gate/veto` knobs. Compiles clean; live run pending GPU.

Reference pipeline, NOT production serving (vLLM/aux-head-in-graph deferred per the
design doc ledger). Live GPU smoke of the CLI waits for the Amendment X sweep to free
the single GPU.

## 006 - result: Amendment X 1.7B PASS; 8B running

Qwen3-1.7B (raw base) PASSES all three locked gates - X-G1 gate 0.996 [0.993,0.998],
X-G2 dial 0.815 [0.787,0.842], X-G3 veto 0.757 [0.729,0.786]; dial means ordered
correct 0.558 > known 0.431 > halluc 0.219 > wrong 0.122. Nearly identical to 4B.
Caveat: within-SelfAware control 0.667 (weaker than 4B's 0.93). Verdict recorded in
`AMENDMENT-X` section 7. 8B extraction running (`eh-amd-x-full-8b`); 14B pending.

## Open / next

- Live GPU smoke of `two_signal_cli.py` once the X sweep frees the GPU.
- Score 8B, launch 14B, assemble the cross-size roll-up in AMENDMENT-X section 7.
- Remaining flagship do-items: fill-B natural-distribution dial evidence; full
  baseline table; pre-register the cross-family confirmatory run (+ Gemma 4 compat smoke).
- Uncommitted on branch `amendment-j-grpo-v3-proper-scoring`: papers/series/plan.md,
  the design doc, fit_calibration.py + runtime + CLI + artifacts, AMENDMENT-X section 7, and
  this note. Commit pending user go.
