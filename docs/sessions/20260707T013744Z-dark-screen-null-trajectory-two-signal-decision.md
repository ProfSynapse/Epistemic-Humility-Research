---
schema_version: research-session/v1
session_id: 20260707T013744Z-dark-screen-null-trajectory-two-signal-decision
title: dark-screen-null-trajectory-two-signal-decision
status: active
created_at: '2026-07-07T01:37:44Z'
updated_at: '2026-07-07T01:37:57Z'
phase: mechinterp / actuation
question: With dark-actuator-screen and AO both resolving NULL and all four actuation-arc
  PRs merged, what does the trajectory look like now, and what is the highest-leverage
  next experiment?
tags:
- actuation
- dark-screen
- ao
- am
- ap
- two-signal
- retrospective
run_ids: []
trajectory:
  anchor: experiment/protocol/research-trajectory.md
  current_position: ''
  changed_by_session: ''
checkpoints:
- id: 001-decision
  at: '2026-07-07T01:37:57Z'
  kind: decision
  title: Actuation arc closed out, next front decided
  summary: 'All four actuation-arc PRs merged: AM (#238, gates PASS but length-confounded,
    honest content signal ~0.77), AO (#231, resolved NULL, no caution lever validates
    on AI-TRUE), AP (#242, confirmed with answerability caveat, ~0.74 answerability-controlled),
    dark-actuator-screen (#233, resolved NULL, screen valid via pos_ctrl, 9 graduations
    artifact via 3 failure modes). Two gitignored-inputs hotfixes landed on AO and
    AP (exp validate declares only committed files in inputs: now). Decision: next
    experiment is two-signal caution regulation on the untrained instruct (raw-base,
    no adapter), coupling both the doubt readout and the confab-propensity readout
    to the caution setpoint to catch both tails, targeting AC''s bidirectional selectivity
    gap. Confab-to-refuse half evidenced by the dark-screen pos_ctrl; refuse-to-answer
    half is the crux to prove. In scaffolding, not yet signed.'
  evidence:
  - experiments/dark-actuator-screen/experiment.yaml
  - experiments/ao-propensity-regulated-caution/experiment.yaml
  - experiments/ap-veto-length-balanced-confirmatory/experiment.yaml
  - experiments/residual-catch-veto-coverage/AMENDMENT.md
  run_ids: []
  commands: []
  decisions:
  - 'Next experiment: two-signal caution regulation on the untrained instruct (raw-base
    Qwen3-4B, no adapter), in scaffolding, needs prediction + exp sign before any
    run.'
  next_steps:
  - Record orchestrator + user predictions for the two-signal caution-regulation cell,
    then exp sign, then GPU approval.
  signals: {}
legacy_session:
  id: '0040'
  path: docs/sessions/0040 - dark-screen-null-trajectory-two-signal-decision.md
---
# dark-screen-null-trajectory-two-signal-decision

## Question

With dark-actuator-screen and AO both resolving NULL and all four actuation-arc PRs merged, what does the trajectory look like now, and what is the highest-leverage next experiment?

## Trajectory Position

RQ4 control-system arc, actuation branch. AC (doubt-regulated caution) remains
the one standing WIN: +8.7pt selectivity, CI [+5.6, +12.0], on the clean-SFT to
GRPO-v2 seed1 checkpoint. This session closed out the AK-AP actuation arc.
AO's attempt to find a fresh caution lever on the AI-TRUE checkpoint
(professorsynapse/eh-qwen3-4b-clean-sft-grpo-par-true-seed1-lora, the
clean-SFT to GRPO probe-as-reward-TRUE lineage) came back NULL, joining AL
(clean null) and AN (confounded null) as a triple null on that lineage: AI-TRUE
still has no validated caution actuator. The dark-actuator-screen resolved NULL
on the raw-base dark subspace, but its positive control confirmed a caution /
answer-vs-refuse lever DOES exist and works on raw-base, which becomes the
substrate for the next experiment. AM's post-generation veto claim came back
gate-PASS but length-confounded; AP's confirmatory follow-up recovered a
genuine, smaller content signal on the same raw-base surface. Net effect: real
actuation still works on exactly one checkpoint (AC), and the next front moves
the actuation question from AI-TRUE to the untrained instruct.

## Summary

Four threads, in order.

1. DARK-ACTUATOR-SCREEN RESOLVED NULL, screen itself valid
   (`experiments/dark-actuator-screen/experiment.yaml`, PR #233 merged). The
   G-instrument is not void: the positive control (raw-base answer-vs-refuse
   mass-mean at L34) killed 79 of 80 confabs into coherent "I dont know"
   refusals with confidence dropping to 0.0, and the negative controls sat at
   the floor. Of the 12 frozen dark-displacement candidates (census PR #222),
   9 cleared the raw graduation bar, but an adversarial read traced all 9 to
   artifact via three distinct failure modes: a grader coherence gap
   (refuse-to-answer flips were malformed spam scored as answers, well-formed
   answer rate 0 to 17 percent versus a 76 percent baseline), an under-dosed
   random control (candidate dose-3 setpoints of 34 to 219 against a paired
   random control of only 4 to 42), and off-manifold over-drive on directions
   that the census itself flagged as only weakly linked and mostly off-axis
   (AUROC 0.60 to 0.72). None promoted; the dark subspace is shelved as a
   near-term actuator. The orchestrator's "0 candidates graduate" call was
   correct; the user's "several graduate" call missed. The side benefit is the
   one that matters going forward: the positive control is itself a validated
   raw-base caution lever, resolving Amendment AE's long-open question of
   whether any actuator moves behavior on that checkpoint at all.

2. AO RESOLVED NULL, a dead lever rather than example-starvation
   (`experiments/ao-propensity-regulated-caution/experiment.yaml`, PR #231
   merged). AO's Stage 1 knob validation tried three ways to find a caution
   direction that behaves as a lever on AI-TRUE (AN's refit direction, a fresh
   answer-vs-refuse direction, and a fresh fit) before attempting the
   propensity-coupling stage AC's design calls for. None of them released the
   over-refusal tail: `answerable_refused` sat at 0.974 essentially unmoved
   despite real headroom, and point effects were near zero with bootstrap
   confidence intervals including 0 across both candidate directions and both
   arms. The smoke checks passed (the write fired, `gen_stream_fired` was
   true), so this is a genuine behavioral no-move on a working instrument, not
   an instrument failure. Stage 2 (the propensity-coupling test proper) never
   ran, per the pre-registered falsifier. This is the cleaner sibling of AN:
   where AN could not separate "caution cannot suppress confabulation" from
   "this particular refit direction is a dead actuator," AO tried multiple
   directions with a validated instrument and still found nothing, so AI-TRUE
   now reads as a checkpoint with no available caution lever at all, not
   merely an unlucky refit.

3. AM RESOLVED with a length caveat, AP CONFIRMED the residual content signal.
   AM (`experiments/residual-catch-veto-coverage/AMENDMENT.md`, PR
   #238 merged) passed both pre-registered gates exactly as worded (OOF veto
   AUROC 0.9168, CI [0.854, 0.963]; permutation p = 0.001), but an adversarial
   audit before recording found the residual-versus-good separation was
   dominated by an undisclosed answer-length confound: answer length alone
   separated the two classes at AUROC 0.943, higher than the veto's own 0.917.
   The mechanistic "content-trust veto catches the radial controller's blind
   spot" claim was therefore not established as such; the honest, non-length
   content-signal estimate was put at roughly 0.77 on the broader,
   length-matched hallucination population. AP
   (`experiments/ap-veto-length-balanced-confirmatory/experiment.yaml`, PR
   #242 merged) was the confirmatory follow-up built to settle exactly that
   question on a length-balanced, 192-token construction that removes the
   96-token truncation artifact. It confirmed a genuine content signal, with
   an answerability caveat: the veto adds signal over both length AND
   answerability, at an answerability-controlled AUROC of about 0.74 (margin
   +0.24, 95 percent CI [0.12, 0.37], excluding 0), which promotes AM's ~0.77
   length-matched estimate from plausible to confirmed. The larger 0.86 /
   +0.37 headline number in the raw AP data is answerability-inflated (37
   percent of the matched hallucinations are unanswerable confabs, where the
   veto reads almost perfectly at ~0.99) and must not be cited as the content
   characteristic; the honest number for the two-signal backstop claim is
   ~0.74.

4. Systemic hotfix and the decision on the next front. Both AO and AP hit the
   same `exp validate` gap during this arc: the tool checks that every
   declared `inputs:` path exists on disk, but the gitignored `analysis/`
   directory only exists on the worktree that produced it. A manifest that
   declares those paths passes validation on its own worktree and then breaks
   on every clean checkout, including CI. Both manifests were hotfixed to
   `inputs: []` with an explanatory comment; the durable rule going forward is
   to declare only committed files in `inputs:`. With the arc closed and the
   state of play reassessed (real actuation demonstrated on exactly one
   checkpoint, AC; AI-TRUE triple-null across AL/AN/AO; the training-free
   readout portable for gate and dial work, with 3 of 4 veto directions
   transferring and dataset transfer at 0.983; the veto itself model-dependent
   since it fails on Llama; the aux-head line split Q success versus R
   falsified; the temperature/top_p sweep and prompt panel still never run),
   the user decided the highest-leverage next experiment is a two-signal
   caution regulation cell on the untrained instruct: raw-base
   `unsloth/Qwen3-4B-bnb-4bit`, no adapter. The design couples BOTH the doubt
   readout and the confab-propensity readout to the caution setpoint, so it
   tightens refusal where confab-propensity is high and releases over-refusal
   where doubt is low, directly targeting the bidirectional selectivity gap
   that made AC the one clean win. It runs on the AK Stage-1 surface (309
   confab, 1,029 refuse). The confab-to-refuse (tighten) half is already
   evidenced by the dark-screen's positive control; the refuse-to-answer
   (release) half is the crux this experiment still has to prove. The
   substrate choice is deliberate: since actuation has only ever worked on the
   AC checkpoint and comes back null everywhere on AI-TRUE, moving to the
   untrained instruct tests the mechanism on the one raw-base surface where a
   caution lever has just been shown to exist. The cell is in scaffolding
   (worktree `exp/two-signal-caution-regulation-instruct`) and needs a
   recorded user prediction and an `exp sign` before any run.

## Checkpoints
### 001-decision - Actuation arc closed out, next front decided

- at: `2026-07-07T01:37:57Z`
- kind: `decision`
- summary: All four actuation-arc PRs merged: AM (#238, gates PASS but length-confounded, honest content signal ~0.77), AO (#231, resolved NULL, no caution lever validates on AI-TRUE), AP (#242, confirmed with answerability caveat, ~0.74 answerability-controlled), dark-actuator-screen (#233, resolved NULL, screen valid via pos_ctrl, 9 graduations artifact via 3 failure modes). Two gitignored-inputs hotfixes landed on AO and AP (exp validate declares only committed files in inputs: now). Decision: next experiment is two-signal caution regulation on the untrained instruct (raw-base, no adapter), coupling both the doubt readout and the confab-propensity readout to the caution setpoint to catch both tails, targeting AC's bidirectional selectivity gap. Confab-to-refuse half evidenced by the dark-screen pos_ctrl; refuse-to-answer half is the crux to prove. In scaffolding, not yet signed.
- evidence:
  - `experiments/dark-actuator-screen/experiment.yaml`
  - `experiments/ao-propensity-regulated-caution/experiment.yaml`
  - `experiments/ap-veto-length-balanced-confirmatory/experiment.yaml`
  - `experiments/residual-catch-veto-coverage/AMENDMENT.md`
- decisions:
  - Next experiment: two-signal caution regulation on the untrained instruct (raw-base Qwen3-4B, no adapter), in scaffolding, needs prediction + exp sign before any run.
- next steps:
  - Record orchestrator + user predictions for the two-signal caution-regulation cell, then exp sign, then GPU approval.
