---
title: 'H_monitor: the sign-inverted per-head failure axis as a graded uncertainty monitor'
kg:
  id: experiment:uncertainty-monitor-hypothesis
  type: experiment
  status: canonical
tags:
- kg/experiment
status: proposed
governance: exploratory
phase: phase3
lane: local
est_compute: 'Tier 1 = GPU-free (reuses extracted contrasts + the A.4 sweep rows in hand); Tier 2 ~2-4 GPU-hours on one RTX 3090 (resample + trajectory read); Tier 3 ~6-10 GPU-hours (cross-dataset/cross-regimen build + read+steer)'
relationships:
- type: tests
  target: '[[gap-4-probe-transfer]]'
  target_id: gap:4-probe-transfer
  confidence: high
- type: builds_on
  target: '[[2411.14257--do-i-know-this-entity-knowledge-awareness]]'
  target_id: paper:2411.14257
  confidence: high
  evidence: ['nearest precedent: linear self-knowledge / entity-recognition directions that gate refuse-vs-hallucinate']
- type: builds_on
  target: '[[entity-recognition-direction-gates-refusal-vs-hallucination]]'
  target_id: mechanism:entity-recognition-direction-gates-refusal-vs-hallucination
  confidence: high
- type: builds_on
  target: '[[known-unknown-direction]]'
  target_id: term:known-unknown-direction
  confidence: high
- type: builds_on
  target: '[[inference-time-intervention]]'
  target_id: method:inference-time-intervention
  confidence: high
- type: builds_on
  target: '[[2306.03341--inference-time-intervention]]'
  target_id: paper:2306.03341
  confidence: high
- type: builds_on
  target: '[[2407.12404--analyzing-generalization-reliability-steering-vectors]]'
  target_id: paper:2407.12404
  confidence: high
  evidence: ['grounds the probe-sign vs causal-sign dissociation: ~50% of inputs anti-steerable in CAA']
- type: builds_on
  target: '[[steering-vector-steerability-is-high-variance-and-sign-unstable]]'
  target_id: mechanism:steering-vector-steerability-is-high-variance-and-sign-unstable
  confidence: high
- type: builds_on
  target: '[[2207.05221--lms-mostly-know-what-they-know]]'
  target_id: paper:2207.05221
  confidence: medium
- type: related_to
  target: '[[2406.15927--semantic-entropy-probes]]'
  target_id: paper:2406.15927
  confidence: high
  evidence: ['graded hidden-state uncertainty axis read for abstention; the read-out analogue']
- type: related_to
  target: '[[2510.09033--probes-read-recall-not-truth]]'
  target_id: paper:2510.09033
  confidence: medium
  evidence: ['the recall-not-truth caution H_monitor must rule out']
related:
- '[[gap-4-probe-transfer]]'
- '[[2411.14257--do-i-know-this-entity-knowledge-awareness]]'
- '[[entity-recognition-direction-gates-refusal-vs-hallucination]]'
- '[[known-unknown-direction]]'
- '[[inference-time-intervention]]'
- '[[2306.03341--inference-time-intervention]]'
- '[[2407.12404--analyzing-generalization-reliability-steering-vectors]]'
- '[[steering-vector-steerability-is-high-variance-and-sign-unstable]]'
- '[[2207.05221--lms-mostly-know-what-they-know]]'
- '[[2406.15927--semantic-entropy-probes]]'
- '[[2510.09033--probes-read-recall-not-truth]]'
---

## Question & Hypothesis

Spun off from the Step A.4 ITI sweep (session `docs/sessions/0023` checkpoint
038, continued in `docs/sessions/` (note 0025)). On a GRPO-humility-tuned Qwen3-4B, a
sparse 11-head during-generation intervention on a per-head failure axis — built
as `mean(unknown_answered_wrong) - mean(unknown_refused)` — is causally potent
but **sign-inverted vs the probe**: *adding* the direction we labelled
"wrong-answer" *raises* abstention (at alpha=+4, unknown_answered_wrong 61->22 of
128, unknown_refused 67->106), and it does so ~5.6x more on unknown than on known
questions.

- **Hypothesis (H_monitor).** The direction is not a "be-wrong" axis but a
  GRADED internal uncertainty / "this-is-hard, I-might-not-know" monitor present
  during hard questions regardless of the eventual answer-vs-refuse outcome.
  Hallucinations are items whose alarm fired sub-threshold (the model guessed);
  refusals are items whose alarm crossed threshold (the model bailed); amplifying
  the alarm pushes more items over it — the "stimulant amplifies the brake, not
  the symptom" shape.
- **Competing hypotheses to kill.** H_wrongness (original "be-wrong" axis;
  already contradicted by the sign). H_refusal_motor (it is just the
  refuse-vs-answer motor direction, not an epistemic monitor). H_OOD_default (no
  specific signal; any large perturbation collapses to the model's default JSON
  abstention). H_decision_echo (the projection merely echoes a decision already
  taken, not a pre-commitment monitor).
- **Falsifier.** theta-projection does NOT track independent difficulty among
  answered items, OR theta is ~parallel to the refuse-vs-answer axis
  (cosine ~1), OR the effect reproduces under norm-matched random heads/directions
  (then it is energy, not this circuit), OR it does not transfer across
  dataset/regimen.

**Novelty boundary (skeptical, grounded by the lit sweep).** The bare claim "a
linear knowledge-conditioned direction causally gates refuse-vs-hallucinate" is
**essentially prior art** — Ferrando et al. `[[2411.14257--do-i-know-this-entity-knowledge-awareness]]`
(entity-recognition / self-knowledge directions), with gradedness/transfer
established by semantic-entropy probes
`[[2406.15927--semantic-entropy-probes]]` and steering-as-abstention-dial shown
elsewhere. Anti-steerability (per-input sign flips) is documented by Tan et al.
`[[2407.12404--analyzing-generalization-reliability-steering-vectors]]`. The
genuinely novel slice this experiment must defend is narrower and must be framed
*against Ferrando as the nearest precedent*: (1) a **principled probe-sign vs
causal-sign inversion** on an abstention monitor that was derived from a
*behavioral* wrong-vs-refuse contrast in a *post-training humility-tuned* model
(not an entity-known label); (2) **per-attention-head** ITI localization (11
sparse heads) of that monitor; (3) the **~5.6x unknown/known** asymmetry as
evidence it is a graded threshold-pusher, not a binary gate. Leaning on "a
knowledge direction exists" or "steering changes refusal" alone would be
rediscovery.

## Design

- **Model.** The same pinned GRPO v2 stack as A.4: SFT-merged Qwen3-4B base +
  active GRPO v2 adapter, greedy, `enable_thinking: false`, the JSON
  response-confidence prompt.
- **Direction.** The 11-head per-head failure axis already extracted for A.4
  (mass-mean `unknown_answered_wrong` vs `unknown_refused`), plus a
  refuse-vs-answer axis built on the same heads for the geometry test.
- **Independent difficulty signals (circularity guard).** NEVER score the monitor
  against the same wrong/refused labels theta was built from. Use: baseline
  stated `response_confidence`, answer-token logprob, resample empirical accuracy,
  or an external grader.
- **Controls.** Random-HEAD (sigma-matched AND norm-matched — already run under
  A.4) and random-DIRECTION (same 11 heads, scrambled directions, matched norm).
- **Metric panel.** Per-head cosine(theta_failure, theta_refuse-vs-answer);
  AUROC of theta-projection for wrong-vs-right among answered items, vs the
  model's stated confidence; flip-alpha vs difficulty correlation; projection
  trajectory across generated positions; transfer AUROC/cell-deltas across
  dataset and regimen.

This is an `exploratory` note: it is not part of PROTOCOL v0.3 and produces no
headline results. If any arm graduates to a signed experiment it goes through the
`amendment-governance.md` 7-point rule first.

## Prerequisites & Gating

- Tier 1 needs NO GPU and NO new model load: it reuses the extracted A.4
  contrasts and the A.4 sweep `rows.jsonl` already on disk.
- Tier 2/3 need a single RTX 3090 (Docker GPU via `docker.exe`, F: mount) and the
  same pinned checkpoints; Tier 3 additionally needs TriviaQA/bridge panels and
  the KTO/DPO regimen adapters staged.
- Steering directions stay held-out; no probe enters a reward loop.
- Read `experiment/protocol/PHASE3-control-system-protocol.md` before any GPU run;
  GPU runs are gated on explicit user approval.

## Runbook

1. Tier 1 (offline, cheapest falsifiers; reuses data in hand):
   - **T1 geometry** — per-head cosine of the failure axis vs the
     refuse-vs-answer axis from the extracted contrasts under
     `experiment/phase1/probe/analysis/`. cosine ~1 collapses H_monitor into
     H_refusal_motor.
   - **T2 flip-order vs difficulty** — from the A.4 sweep rows, the alpha at which
     each unknown item flips to refusal, correlated with independent difficulty.
   - **T3 read-don't-steer** — among answered items only, AUROC of theta-projection
     for the answer being wrong, vs stated confidence (selective-prediction read).
2. Tier 2 (one modest GPU pass via `experiment/phase1/probe/phase3_head_intervention_runner.py`):
   resample difficulty grading; projection-trajectory (pre-commitment) read;
   random-DIRECTION control (sibling of `experiment/phase1/probe/phase3_head_norm_match_control.py`).
3. Tier 3 (the portability/novelty test): rebuild theta on TriviaQA/bridge and on
   KTO/DPO regimens, then read + steer; report transfer.
4. Document: write run records and `docs/sessions/` (note 0025) checkpoints; update the
   Status log below.

Bake in approval gates for any cost-incurring or destructive action. Do not add
experiment-specific code to the `synaptic-tuner` submodule.

## Validation contract

- **Pre-run.** The A.4 extracted contrasts and sweep rows resolve; for Tier 2/3
  the pinned checkpoints load and the extra panels/adapters exist.
- **Post-run.** Each tier emits its metric rows (cosines / AUROCs / correlations /
  trajectories / transfer deltas) with the independent-difficulty provenance
  recorded; a run record and a 0025 checkpoint are written.
- **Definition of done.** Tier 1 reports cosine + read-out AUROC + flip-vs-
  difficulty; H_monitor survives iff cosine is well below 1 AND projection
  predicts wrongness among answered items above the stated-confidence baseline.
  Surviving Tier 1 + T5(timing) + T7(transfer) = a real, deployable result framed
  against Ferrando.

## Outputs & provenance

- Run records: `experiment/phase1/probe/analysis/` siblings of the A.4 outputs.
- Episodic log: `docs/sessions/` (note 0025) checkpoints via the experiment-runner helper.
- Meta-analysis: results are mechanism/detection findings, not training-effect
  sizes, so they do NOT enter `meta-analysis/evidence/effects.csv`; they inform
  Gap 4 / Phase 3 discussion.

## Variations

- **T1 (offline).** Geometry vs refusal axis; flip-order vs difficulty;
  read-don't-steer wrongness prediction. Any one can falsify cheaply.
- **T2 (one GPU pass).** Ground-truth difficulty grading (resample); pre-commitment
  timing (projection trajectory before refusal tokens); random-DIRECTION control.
- **T3 (more GPU).** Cross-dataset / cross-regimen transfer — the portability test
  that separates a general uncertainty monitor from a panel-surface artifact.
- **T8 base-model split (the "is the sensor pretrained?" arm).** Ferrando
  `[[2411.14257--do-i-know-this-entity-knowledge-awareness]]` finds the
  knowledge-recognition signal *in the base model* and shows it drives the chat
  model's refusals — so the sensor may be pretrained while only the
  sensor→abstain *wiring* is tuning-installed. We cannot rebuild our exact
  wrong-vs-refuse contrast in the base model (base models barely refuse, so the
  "refused" group collapses), so this arm takes two non-steering forms: (a)
  **read test** — project the tuned model's 11-head direction into the *base*
  model's activations on the same items; is the geometry already present? (b)
  **Ferrando-style entity-recall construction** — label base-model known/unknown
  by querying Wikidata attributes and thresholding recall accuracy (τ=1, their
  Appendix A recipe; needs no refusal behavior), build a known-vs-unknown entity
  direction in the base model, and test whether our tuned wrong-vs-refuse axis
  lands in the same subspace. Splits "pretraining sensor" from "tuning-installed
  wiring"; note our "unknown" is question-level *unanswerability*, broader than
  Ferrando's *entity-recognition*, so partial (not full) overlap is the expected
  result.

## Status log

- 2026-06-26: created (proposed). Spun off from session 0023's Step A.4 sweep into
  a dedicated session note (0025) and this experiment node. Grounded by a
  literature sweep that surfaced Ferrando 2411.14257 as the nearest precedent and
  Tan 2407.12404 as the sign-instability grounding (both ingested same day). The
  random-HEAD control sigma-matched leg is complete (random heads do NOT reproduce
  the abstention shift); the norm-matched leg was in flight at creation.
- 2026-06-26: random-HEAD control complete (both legs). Localization is real and
  dominant (~75% head-selection-specific) with a ~25% generic-energy component;
  see session 0025 checkpoint 005.
- 2026-06-26: **Tier 1 T1 (geometry) run** via `phase3_head_axis_geometry.py`
  (GPU-free; parity self-check passes). Failure axis F vs refuse-vs-answer axis R:
  mean cos −0.80 across all 11 heads; vs knowledge-boundary axis K: mean |cos| 0.12
  (6.4× dominance). F **is** the refuse↔answer decision axis (anti-aligned by
  construction), **orthogonal** to the static known/unknown axis. This **refutes**
  both the naive refusal-motor reading and the clean "distinct uncertainty
  subspace" reading of H_monitor, and re-centers the puzzle on a **read/write sign
  inversion** on the decision axis (see 0025 checkpoint 006). Design update:
  promote the Tier-2 projection-trajectory test (does the read axis flip sign
  between the prompt token and generation positions?) and the read/write-mismatch
  explanation; demote the separate-subspace framing.
- 2026-06-26: **Tier 1 T3 (read-don't-steer) run** via
  `phase3_head_read_projection.py` (GPU-free). Reads the prompt-token projection
  onto F (σ-standardized, mean over the 11 heads) and tests whether that
  pre-generation read predicts WRONGNESS among answered items vs the model's
  stated confidence (Ferrando/SEP selective-prediction frame). **INCONCLUSIVE**
  on the current extraction: it has perfect label↔correctness collinearity
  (known-answered 64/64 correct, unknown-answered 64/64 wrong), so within-label
  wrongness has no variance to predict and the clean per-label test is undefined.
  Pooled, AUROC(read)=0.71 vs AUROC(1−stated_conf)=0.58 (+0.13), but that only
  re-reads the knowledge boundary and is partly circular (F's positive pole IS
  the unknown-wrong rows). To run T3 cleanly needs an extraction carrying
  within-label correctness variance (known confident-errors, unknown
  lucky-correct); deferred to a variance-bearing / base-model arm (T8). See 0025
  checkpoint (T3).
- 2026-06-26: **Tier 2 read-trajectory run** via
  `phase3_head_read_trajectory_runner.py` (GPU, Docker/unsloth, 256 rows,
  baseline greedy decode, read pre-hooks on the 11 o_proj blocks; NO steering).
  Reads F's natural projection at the final prompt token and every generated
  position to test the read/write-mismatch hypothesis (does F's read flip sign
  between prompt and generation, explaining A.4's inverted causal sign?).
  **VERDICT: NO FLIP.** unknown-wrong vs unknown-refused separation along F keeps
  its sign: **+1.29 at the prompt token → +0.40 during generation** (attenuates
  to ~31%, never inverts). Per-position, unknown-wrong stays positive across
  generation (2.21 → ~0.9 → 0.24) and unknown-refused decays to ~0 (0.91 → 0.15
  → −0.01). F's read is direction-consistent at every position and strongest
  pre-generation (Ferrando-style decision-time read). This **refutes** the
  read/write coordinate-mismatch explanation: the inverted causal sign is a
  **write-side** effect, not a read-axis flip. Two live write-side explanations
  remain — Tan 2407.12404 anti-steerability vs H_OOD_default (all-position
  all-head injection → safe-default collapse). Cheap offline discriminator:
  re-read the A.4 sweep alpha→refusal curve (symmetric in sign ⇒ OOD-collapse;
  monotone ⇒ directional). See 0025 checkpoint (Tier-2 read-trajectory).
