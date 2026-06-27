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

## Strategic trajectory (read-side program)

After F and K both came back **anti-steerable** (settled — a real Tan-2407.12404
result, but a dead end for "find the dial"), the program pivoted to the **read
side**, where the latent-knowledge probe gave the first POSITIVE signal. The
forming publishable unit: *"In a humility-tuned model, over-refusals are
belief-vs-action gaps — the residual stream linearly encodes that the model
knows the answer, yet it abstains; this 'humility tax' is laid partly by SFT and
behaviorally amplified by GRPO."* The grind sequence:

- **Track A — harden the read claim (GPU-free; data on disk; DO FIRST).**
  - **A1 lexical baseline.** Bag-of-words on question text → same known/unknown
    labels. THE control: how much of the 0.997 AUROC is question vocabulary vs
    internal state? Kills H_surface_lexical. (Highest priority — single biggest
    threat to the headline number.)
  - **A2 within-known refused-vs-answered probe.** Train only inside known cells
    (known_refused=168 vs known_answered=388): is the over-refusal gap a real
    internal axis, or a label echo? A positive AUROC means over-refusal has an
    internal signature independent of the known/unknown contrast theta was built on.
  - **A3 h_base vs h_lora source comparison.** Re-run the probe on the SFT-merged
    pre-adapter activations (h_base) vs active-adapter (h_lora): did GRPO *sharpen*
    the known/unknown code or *inherit* it from SFT? Ties the read result to the
    F-pre-exists-GRPO finding. (No new code — `analyze(..., source=...)` already
    supports it.)
  - *(A4 held-out-by-question DROPPED: all 1233 questions are unique, so CV never
    reuses a question; A1 subsumes the memorization worry. Calibration catch.)*
- **Track B — causal test of the READ that survives anti-steerability (GPU; after A).**
  - **B1 activation patching / ablation** at L≈35 on over-refused items, instead
    of additive ITI. Additive steering is anti-steerable; patching a
    known-answered residual into an over-refused forward pass is a cleaner causal
    handle — is the encoded "known" state load-bearing for the eventual abstention?
  - **B2 generation-trajectory of the known/unknown projection** — does the code
    fire BEFORE the refuse/answer token (pre-commitment monitor, H_monitor) or
    echo the decision (H_decision_echo)? Reuse a read-trajectory runner.
- **Track C — generalization (mixed; after A, opportunistic).**
  - **C1 cross-dataset transfer** of the known/unknown probe (GPU: new extraction)
    — general epistemic code vs dataset-specific.
  - **C2 cross-regimen read on DPO/KTO seeds** (GPU-free IF those activations
    exist) — does the same direction read across the paper-2 regimens? Ties the
    mech result to the headline SFT/DPO/KTO comparison.
- **Track D — synthesis.** Assemble the training-tradeoff narrative once A (+ at
  least one of B/C) lands.

Sequencing: A1→A2→A3 in one GPU-free grind, report the hardened headline, then
choose B vs C with the user.

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
- 2026-06-26: **A.4 alpha-curve discriminator** via
  `phase3_head_intervention_sign_curve.py` (GPU-free; re-reads the existing A.4
  `summary.json`, no new generation). **DIRECTIONAL (anti-steerable), not
  OOD-collapse.** unknown_refusal_rate is monotone in alpha (−8→40.6, −4→48.4,
  −2→48.4, 0→52.3, +4→82.8) and over_refusal_on_known likewise (−8→47.7 … +4→
  56.3): −F lowers refusal even at large magnitude (no collapse), +F raises it
  globally across known **and** unknown. Refutes **H_OOD_default**; confirms a
  directional refusal motor whose steering sign is inverted vs the prompt-token
  read (Tan 2407.12404). **Net resolution** of the central puzzle: F is the
  refuse↔answer decision axis (geometry) read direction-consistently across
  positions (no-flip trajectory) but causally **anti-aligned** under injection
  (alpha curve) — a read/write sign inversion localized to write-side steering.
  H_monitor (distinct uncertainty subspace) and H_OOD_default refuted; refined
  sign-inverted H_refusal_motor supported. See 0025 checkpoint (alpha-curve).
- 2026-06-26: **Per-head read-sign consistency** via
  `phase3_head_read_sign_consistency.py` (GPU-free; re-reads the Tier-2
  read-trajectory `rows.jsonl` `prompt_read_per_head`, no new generation).
  **UNANIMOUS: 11/11 heads** read F with the same sign — prompt-token separation
  mean(unknown_answered_wrong) − mean(unknown_refused) is positive for every head
  (+0.78 to +1.69, mean +1.29; zero inverted). So the aggregate failure-axis read
  is **not** a sum over cancelling heads; the A.4 steering inversion is a
  write-side property on a clean, uniform read (Tan 2407.12404 anti-steerability:
  read sign ≠ steer sign). Open follow-up: a **per-head steering sweep** (steer
  each head individually) to test whether the anti-steerability is also uniform
  per-head, or whether a subset of heads carries the inverted causal sign.
- 2026-06-26: **SFT pre-adapter read-trajectory arm** launched
  (`..._head_read_trajectory_sft_base.yaml`; GRPO adapter removed, generation +
  read on the SFT-merged h_base model). Transfer/pre-existence test: does the
  GRPO-derived F already separate the SFT model's OWN unknown-wrong vs
  unknown-refused behavior at the prompt token, before GRPO training? Caveat: F
  (theta/sigma) is fixed from GRPO activations; this reads that direction on SFT
  activations (axis transfer, not an SFT-rebuilt axis). **RESULT: axis
  PRE-EXISTS GRPO.** The SFT arm is near-identical to GRPO — NO-FLIP trajectory
  (prompt +1.19 → gen +0.37 vs GRPO +1.29 → +0.40) and UNANIMOUS 11/11 per-head
  read (mean +1.20 vs +1.29). GRPO did **not** create the failure axis; it
  inherits an SFT-laid representation. What GRPO changed is **behavior**: SFT
  answers-wrong 67 / refuses 61, GRPO refuses 67 / answers-wrong 61 (GRPO trained
  in more abstention). Training moved the decision threshold/action, not the
  underlying read geometry — on-thesis for the training-tradeoff story.
- 2026-06-26: **Causal knowledge-boundary (K) steering test** launched
  (`phase3_current_clean_grpo_v2_knowledge_boundary_steer.yaml` + offline
  `phase3_knowledge_boundary_steer_readout.py`). After H_monitor was refuted for
  F (the refusal axis), K — the unknown-vs-known, behavior-agnostic direction
  nearly orthogonal to F (geometry cos 0.12) — is the remaining candidate for a
  separable "do I know this?" representation. Steers K on the same 11 heads across
  symmetric alpha (sign: +alpha = "unknown" pole) over a balanced 128-known /
  128-unknown panel; offline readout parses per-row response_confidence and
  classifies the causal signature as **belief_monitor** (steering toward "unknown"
  raises refusal AND lowers confidence — belief-consistent), **anti_steer** (the
  F-like inverted case), or **inert**. The discriminator is belief-CONSISTENCY of
  the sign vs K's pole, not refusal uniformity (both F and a monitor can move
  refusal the same way on both labels). **VERDICT: anti_steer.** Known-side
  over-refusal is monotone and belief-INCONSISTENT — steering toward the "unknown"
  pole LOWERS abstention (α −6:56.2, −3:40.6, 0:33.6, +3:28.9, +6:23.4), the wrong
  way for a knowledge dial; stated confidence flat (Δ−0.014); unknown side pinned
  at ~100% (ceiling). K, like F, is an anti-steerable refusal-correlated direction,
  **not** a causal knowledge dial. **Two candidate axes, both anti-steerable** ⇒ a
  separable uncertainty representation is not a STEERABLE axis in this head-set.
- 2026-06-26: **Pivot to a READ-side probe** (`phase3_latent_knowledge_probe.py`,
  GPU-free). After F and K both came back anti-steerable, stop hunting a steerable
  knob and ask whether the residual stream LINEARLY ENCODES "do I know this?" more
  than the model's abstention expresses. Reuses the on-disk GRPO v2 full-panel
  residual stream (h_lora, 37 layers × 2560) joined to behavior_cell. Two readouts:
  (1) per-layer CV AUROC of activation → ground-truth known/unknown; (2) the
  **over-refusal gap** — train the best-layer probe on clean cells
  (known_correct_answered vs unknown_refused) and score the 168 over-refusals
  (known_refused): if they look internally KNOWN, the over-abstention is a
  behavioral-threshold gap, not an internal "I don't know". NOTE: "predict
  correctness among answered" is intentionally NOT the target — the GRPO model
  answers-wrong too rarely (~15 known + 1 unknown) to power a 2560-dim correctness
  probe; the known/unknown boundary and the 168-item over-refusal cell are the
  well-powered signals. **RESULT (first POSITIVE in the search): the boundary IS
  linearly encoded and COMPUTED, not surface.** Per-layer CV AUROC of h_lora →
  known/unknown: L0 (embeddings) = 0.498 (chance), L1 = 0.981, plateau ~0.99,
  peak L35 = 0.997. The L0-chance → L1-0.98 jump rules out a lexical/embedding
  artifact. Caveat: single-layer emergence ⇒ a relatively SHALLOW feature, and
  known/unknown is dataset-defined (TriviaQA vs SelfAware), so the probe may read
  question-TYPE differences rather than memory-retrieval — needs a lexical
  baseline + held-out control. **Over-refusal gap (more robust, within-known):**
  the best-layer probe places the 168 known_refused over-abstentions at position
  0.27 (look internally KNOWN, like answered-knowns, not like unknown-refused).
  The model represented the answer but refused anyway ⇒ over-abstention is a
  behavioral-THRESHOLD gap, not an internal "I don't know" signal. This read-side
  signal is the uncertainty representation the steerable axes (F, K — both
  anti-steer) were not. Next controls: lexical-baseline AUROC; within-known
  refused-vs-answered probe; h_base (pre-GRPO) comparison; held-out question set.
- 2026-06-26: **Track-A hardening controls** via
  `phase3_latent_knowledge_controls.py` (A1, A2; GPU-free) + an `h_base` re-run of
  the probe (A3). The controls PARTLY DEFLATE the headline and surface a cleaner
  signal — calibrated result, not the inflated one.
  - **A1 lexical baseline (the key control): the 0.997 known/unknown AUROC is
    LARGELY a dataset-lexicon confound.** A TF-IDF (1–2gram) logistic on the raw
    QUESTION TEXT already separates known/unknown at **0.964**; the residual probe
    (L35 0.997) beats it by only **+0.033**. known/unknown is dataset-defined
    (answerable TriviaQA-style vs unanswerable SelfAware-style) and the two have
    distinct vocabularies, so most of the spectacular AUROC is readable from
    question words — NOT primarily an internal memory-retrieval signal. The probe's
    own depth profile agrees: it JUMPS at L1 (0.981) and plateaus (shallow/surface),
    rather than building with depth. Headline correction: do not report the raw
    known/unknown AUROC as evidence of an internal "do I know this" code.
  - **A2 within-known refused-vs-answered (the result that SURVIVES): a clean,
    DEEP internal over-refusal axis.** Restricting to KNOWN rows only and
    predicting over-refused (known_refused=168) vs answered (known_answered=388) —
    a contrast orthogonal to the known/unknown labels — the residual hits
    **0.919** (L35) while the lexical baseline gets only **0.641** (margin
    **+0.278**). Unlike A1 this CLIMBS with depth (L1 0.67 → L18 0.83 → L35 0.92):
    a COMPUTED deep feature, not surface vocabulary. So among questions the model
    knows, there is a genuine internal signature distinguishing the ones it
    over-refuses, not reducible to question wording. This — not the
    lexicon-confounded known/unknown probe — is the real read-side uncertainty/
    caution activation candidate. (Residual caveat: lexical controls surface words,
    not deeper semantic difficulty; but 0.64→0.92 + depth-climb is strong.)
  - **A3 h_base (pre-adapter) comparison: GRPO INHERITED both signals from SFT,
    did not sharpen them.** On the SFT-merged h_base activations the known/unknown
    curve is near-identical (L1 0.981, L35 0.997) and the over-refusal gap position
    is **0.266** vs h_lora's 0.27 (over-refusals look internally KNOWN in BOTH).
    Mirrors the F-pre-exists-GRPO finding: the read geometry (boundary code + the
    latent-knowledge gap) is SFT-laid; GRPO moved BEHAVIOR (more abstention), not
    the representation. Consistent training-tradeoff story across F and the
    read-side probes.
  - **Net:** the belief-vs-action / over-refusal story holds and is now lexically
    clean (A2 + the gap), but the inflated "residual encodes known/unknown at
    0.997" claim is recharacterized as mostly dataset-lexicon (A1). Next: B2
    generation-trajectory timing (pre-commitment vs decision-echo for the A2 axis),
    or C2 cross-regimen read on DPO/KTO; B1 activation-patching for a causal handle
    that survives anti-steerability.
- 2026-06-26: **C2 cross-regimen read + axis geometry** (GPU-free; same controls
  pipeline run on the SFT, GRPO+DPO, and GRPO v2 full panels, all 1233 rows on
  disk; `phase3_latent_knowledge_controls.py` extended with an `axis_geometry`
  readout + single-load refactor). Tests whether the read-side over-refusal story
  is GRPO-specific or general across the paper-2 humility-tuning family, and
  whether the over-refusal axis is a SEPARATE internal direction or a re-read of
  the knowledge axis. **A mechanistic humility-tax picture, consistent across all
  three regimens:**

  | regimen | known_refused (over-refusals) | A2 over-refusal axis (residual / lexical / margin) | caution⊥knowledge \|cos\| | over-refusal gap pos |
  |---|---|---|---|---|
  | SFT (clean_sft_merged) | 127 | 0.901 / 0.644 / **+0.256** | 0.087 | 0.25 |
  | GRPO+DPO (clean_sft_grpo_dpo) | 152 | 0.930 / 0.660 / **+0.270** | 0.053 | 0.28 |
  | GRPO v2 (clean_sft_grpo_v2) | 168 | 0.919 / 0.641 / **+0.278** | 0.035 | 0.27 |

  - **Behavioral humility tax is in the cell counts:** over-refusal (known_refused)
    rises monotonically with tuning intensity, 127 → 152 → 168, while internal
    knowledge is unchanged (known/unknown probe pinned at ceiling ~0.997 in all
    three; A1 lexical-confounded as before).
  - **A distinct internal CAUTION axis is present in EVERY regimen, from SFT
    onward.** Among knowns, a deep lexically-clean residual axis predicts which get
    over-refused at 0.90–0.93 (vs lexical 0.64–0.66, margin +0.26–+0.28). Like F
    and the knowledge code, it is SFT-laid and inherited, not GRPO-created.
  - **That caution axis is ORTHOGONAL to the knowledge axis in all three**
    (\|cos\| 0.035–0.087, all < 0.1). The decision of WHICH knowns to abstain on is
    carried by a separate direction, not the "do I know this" representation —
    mechanistically consistent with the gap (over-refusals read as KNOWN, position
    0.25–0.28 in every regimen).
  - **Suggestive trend (single seed — NOT firmly established):** as humility tuning
    intensifies the caution axis trends MORE orthogonal to knowledge (cos 0.087 →
    0.053 → 0.035) and marginally stronger (+0.256 → +0.270 → +0.278). Reads as:
    tuning recruits/sharpens a separate caution direction to drive more abstention
    rather than changing what the model knows. Report orthogonality (<0.1 ×3) as
    robust; the monotone cos drift as suggestive pending multi-seed.
  - **Caveats:** one seed per regimen; lexical controls surface words not deeper
    semantic difficulty; known/unknown is dataset-defined (same SelfAware items
    across arms) — cross-DATASET transfer (C1) still open. **Net:** the
    belief-vs-action over-refusal mechanism and its dedicated, knowledge-orthogonal
    caution axis generalize across the SFT/DPO/GRPO regimen family, tying the
    read-side mech result to the paper-2 headline comparison.
- 2026-06-26: **Cross-regimen caution-axis AGREEMENT** via
  `phase3_caution_axis_transfer.py` (GPU-free). C2 showed each regimen has a
  caution axis of similar strength; this tests whether it is the SAME direction.
  Fits the within-known over-refusal direction at L35 for all three regimens in a
  shared whitened frame (one StandardScaler on the pooled known activations) and
  reports pairwise |cos| of the unit normals, with a shuffled-label random floor.
  (Cosine, not train-A/test-B transfer AUROC, because the SelfAware questions are
  identical across regimens — only the over-refusal labels differ — so AUROC
  transfer could ride question identity; direction geometry does not.)
  **VERDICT: SHARED-AXIS.** mean cross-regimen |cos| = **0.701** vs random floor
  **0.014** (~50×). Structure: **grpo_dpo↔grpo_v2 = 0.857** (the two GRPO-family
  regimens cluster tightest), **sft↔grpo_dpo = 0.671**, **sft↔grpo_v2 = 0.576**
  (SFT, the ancestor, sits furthest from both). So the caution axis is ONE shared
  mechanism the regimens inherit — laid by SFT — but it **rotates measurably as
  tuning proceeds**, with the GRPO variants converging on a common rotated version.
  This sharpens the C2 "suggestive trend": not three coincidental axes (the floor
  rules that out), but an inherited direction that drifts under tuning. Calibration:
  0.58–0.86 is "strongly shared WITH drift," not "identical"; single seed, so the
  exact SFT-most-distinct ordering is suggestive while the far-above-floor
  agreement is robust. **Read-side correlational case is now strong; remaining gaps
  are CAUSAL (does the caution axis DRIVE over-refusal — B1 activation patching) and
  TIMING (pre-commitment monitor vs decision echo — B2 trajectory), both GPU; and
  cross-DATASET transfer (C1).**
- 2026-06-26: **C1 cross-dataset transfer — KUQ (Known-Unknown Questions), GRPO v2,
  full GPU pipeline.** Built a dataset-agnostic panel (600 known / 400 unknown,
  seed 0) from `datasets/kuq/knowns_unknowns.jsonl` via the new
  `phase3_xdataset_build_panel.py`, generated clean baseline answers
  (`phase3_head_intervention_runner` @ alpha=0.0, GRPO v2), assembled behavior
  rows (`phase3_xdataset_behavior_from_generation.py`), extracted residuals
  (`hidden_state_probe.py`, final_prompt_token, h_base/h_lora/delta), and ran the
  Track-A controls + caution-axis transfer. KUQ behavior cells: known_refused
  **461**, known_answered_wrong 74, known_correct_answered 65, unknown_refused
  392, unknown_answered_wrong 8 — i.e. the model **over-refuses 77% of KUQ
  "known" questions** (vs ~30% on SelfAware). **Three results, two layers of
  finding:**
  - **The caution-axis PHENOMENON generalizes.** A1 knowledge axis: residual
    best L25 AUROC **0.974** vs TF-IDF lexical **0.918** (margin **+0.056**,
    INTERNAL-STATE — a *cleaner* margin than SelfAware, whose 0.997 was mostly
    lexical). A2 within-known caution axis: residual best L32 AUROC **0.912** vs
    lexical **0.680** (margin **+0.233**, INTERNAL-STATE), depth-climbing
    (0.71@L1 → 0.91@L32), lexically clean — same signature as SelfAware. Axis
    geometry: |cos(knowledge, caution)| = **0.022** → ORTHOGONAL, same as
    SelfAware. So a deep, lexically-clean, knowledge-orthogonal within-known
    over-refusal axis exists on a second, independently-sourced dataset.
  - **The caution DIRECTION is largely dataset-specific.** Cross-dataset cosine
    (SelfAware-GRPOv2 vs KUQ-GRPOv2, shared whitened frame): |cos| = **0.16**
    (L32) / **0.19** (L35) vs random floor 0.04 / 0.02 (~9× chance) →
    **PARTIAL-SHARED**. This is FAR below the within-SelfAware cross-regimen
    agreement (|cos| ≈ 0.58–0.86). Caveat: cross-regimen held questions identical
    (only labels differed), so some of that 0.7 rides shared inputs; cross-dataset
    uses entirely disjoint questions, a harder + cleaner test. Net: the axis is a
    weak-but-real shared sliver atop a large dataset/content-specific component.
  - **The belief-action gap REVERSES — and the cross-dataset test is what
    revealed why.** Over-refusal gap position: SelfAware **0.25–0.28** (over-
    refusals look internally KNOWN → genuine over-refusal / "humility tax",
    refuses despite knowing) vs KUQ **0.679** (over-refusals look internally
    UNKNOWN ~ unknown_refused → INTERNAL-UNCERTAINTY, abstention tracks genuine
    ignorance, epistemically appropriate). This is the **construct difference**:
    SelfAware "known" = model-filtered-knowable, so its known_refused is true
    over-refusal; KUQ "known" = answerable-in-principle (obscure multi-hop
    trivia), so its known_refused is dominated by the model genuinely not knowing.
    The weak ~0.17 direction overlap is consistent with the shared over-refusal
    sliver; the rest is KUQ's genuine-uncertainty axis that SelfAware's
    filtered-known construct excludes. **Calibration takeaway (non-sycophantic):
    the headline is NOT "the caution axis transfers." It is that the
    caution-axis PROPERTIES are dataset-robust while its DIRECTION and BEHAVIORAL
    MEANING are construct-conditioned — the belief-action "humility tax" claim
    specifically requires a dataset whose "known" means model-knowable, which KUQ
    is not.** Artifacts (gitignored): `analysis/_xdataset_kuq_controls/` +
    `xdataset/kuq_*`. Reusable scripts + configs checked in; this is the basis for
    the Task-6 cross-dataset protocol in the mech-interp-runner skill.
- 2026-06-26: **B2 caution-axis read-side TIMING test (residual read-trajectory,
  GRPO v2, SelfAware, full GPU).** New residual-stream variant of the read-
  trajectory harness (`phase3_residual_read_trajectory.py` + `_runner.py`,
  direction fitter `phase3_residual_caution_direction.py`): reads the L35 residual
  projection onto the **raw mass-mean caution direction** (known_refused vs
  known_correct_answered) at every generated position under BASELINE greedy
  decoding, and splits **pre- vs post-lexical** windows by the refusal-phrase
  onset. Ran on all 556 known rows (168 refused / 373 answered). Direction
  sanity: raw mass-mean prompt-token AUROC **0.9094** ≈ the whitened A2 logistic
  0.91 → the raw direction captures the same caution axis. **Result:
  PRE-COMMITMENT.** Pre-lexical separation (refused − answered) = **+1.09σ**
  (refused 6.72 vs answered 5.62), held OUT-OF-FIT on generation positions, same
  sign as the by-construction prompt sep — the caution axis already separates the
  two behaviors BEFORE the refusal words are emitted, so a **pure decision-echo is
  falsified**. Mechanism is visible per row: refused rows **spike** on the caution
  axis just before "I don't know" (e.g. pre 7.28 → post 5.42) then relax; answered
  rows stay flat (~5.62) and by construction never enter a post-lexical window
  (post-lexical neg group empty/nan). 167/168 refused rows onset-detected (lone
  miss is a scorer edge case, not a refusal). **Calibration / caveats
  (non-sycophantic):** (1) a read-only timing test can falsify decision-echo but
  CANNOT separate a *monitor* (caution state causes the refusal) from a
  *pre-formed-but-unverbalized decision* — that is causal and remains B1's job;
  (2) the direction/σ were fit on the SelfAware FULL extraction (default render)
  but read under the JSON response-confidence generation prompt, so the
  standardized **prompt-token** separation collapses to +0.22σ (operating-point
  shift across prompts) even though the held-out fit-prompt A2 AUROC is 0.91 — the
  robust, internally-consistent number is the generation-internal pre-lexical
  contrast (+1.09σ), and under the generation prompt the signal *strengthens* from
  the prompt token through the JSON scaffold to the pre-lexical peak; (3) Tier-2,
  single seed. Remaining read-side gap is now only CAUSAL (B1 activation
  patching). Artifacts (gitignored):
  `analysis/current_clean_grpo_v2_caution_residual_read_trajectory/` +
  `analysis/current_clean_grpo_v2_caution_residual_direction/`. Harness + config +
  tests checked in; protocol added to the mech-interp-runner skill
  (`references/read-trajectory-timing.md`).
