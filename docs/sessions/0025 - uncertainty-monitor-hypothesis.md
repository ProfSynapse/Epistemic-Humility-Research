---
schema_version: research-session/v1
session_id: '0025'
title: uncertainty-monitor-hypothesis
status: complete
created_at: '2026-06-26T19:11:24Z'
updated_at: '2026-06-26T20:11:32Z'
phase: phase-3-mech-interp
question: "Is the sign-inverted per-head failure-axis direction a graded internal\
  \ UNCERTAINTY MONITOR (amplifying it raises abstention) rather than a be-wrong axis\
  \ \u2014 and the 'stimulant amplifies the brake, not the symptom' analogy?"
tags:
- mech-interp
- abstention
- uncertainty-monitor
- iti
- hypothesis
run_ids:
- a4_randctl
trajectory:
  anchor: experiment/protocol/research-trajectory.md
  current_position: ''
  changed_by_session: ''
checkpoints:
- id: 001-interpretation
  at: '2026-06-26T19:12:16Z'
  kind: interpretation
  title: 'H_monitor: the sign-inverted failure axis may be a graded UNCERTAINTY MONITOR,
    not a be-wrong axis'
  summary: 'ORIGIN: Session 0023 checkpoint 038-result (the A.4 ITI sweep). We BUILT
    the per-head direction as mean(unknown_answered_wrong) - mean(unknown_refused)
    and assumed a ''be-wrong'' axis, so ADDING it should hallucinate MORE. Causally
    it does the opposite: alpha=+4 (adding the wrong-answer direction to the 11 localized
    heads) RAISES refusal (unknown_answered_wrong 61->22 /128, unknown_refused 67->106),
    and alpha<0 makes the failure WORSE. H_monitor: the direction is not a wrongness
    axis but a GRADED INTERNAL UNCERTAINTY (''this-is-hard, I-might-not-know'') signal
    present DURING hard/unknown questions regardless of the eventual answer-vs-refuse
    outcome. Hallucinations are items where the alarm fired sub-threshold (model guessed);
    refusals are items where it crossed threshold (model bailed). Amplifying the alarm
    pushes more items over threshold -> more refusal. This is the ''stimulant calms
    ADHD'' shape: amplifying a regulatory/MONITOR signal, not the symptom, so a low-level
    ''more'' yields a behavioral ''less guessing''. It reframes the sign inversion
    from a measurement gotcha (ITI folklore: always sweep both signs) into a testable
    claim that humility-trained models carry a READABLE knowledge-uncertainty signal.
    Competing hypotheses to kill: H_wrongness (original ''be-wrong'' axis -- contradicted
    by data); H_refusal_motor (just the refuse-vs-answer MOTOR direction, not epistemic);
    H_OOD_default (no specific signal; any large perturbation -> fallback to safe
    default abstention under the JSON prompt). GROUNDING (KG already holds adjacent
    lit): paper:2306.03341 (ITI), paper:2310.01405 (RepE read+control), paper:2212.03827
    (CCS latent knowledge), paper:2304.13734 (internal state knows when lying), paper:2207.05221
    (P(IK)), paper:2510.09033 (CAUTION: probes may read recall not truth), term:truth-direction,
    term:universal-truthfulness-hyperplane, term:knowledge-boundary. A background
    research+ingestion agent is filling external gaps (candidates: Geometry of Truth
    2310.06824, Semantic Entropy Probes 2406.15927, selective-prediction-for-LLMs).'
  evidence:
  - docs/sessions/0023 - phase-3-model-variation-panel.md#038-result
  - experiment/notes/mech-interp-model-variation-panel.md
  run_ids: []
  commands: []
  decisions:
  - 'Test H_monitor with READ-OUT (correlational, GPU-cheap, less confounded than
    steering) BEFORE more interventions; key circularity guard: never score the monitor
    against the same wrong/refused labels theta was built from -- use INDEPENDENT
    difficulty (stated response_confidence, answer-token logprob, resample accuracy,
    or an external model).'
  - 'Frame the deployable version as the contribution if it survives: not ''we steered
    refusal'' but ''humility-trained models compute a graded knowledge-uncertainty
    signal you can READ to abstain (selective prediction) and AMPLIFY to abstain more''
    -- direct evidence on gap:4-probe-transfer.'
  next_steps:
  - Run the Tier 1-3 test battery (see next checkpoint); Test 1 (geometry vs refusal
    axis) can kill it cheaply on data in hand.
  signals: {}
- id: 002-planning
  at: '2026-06-26T19:12:32Z'
  kind: planning
  title: 'H_monitor test battery (Tier 1-3): kill cheap, separate monitor from refusal-motor
    / decision-echo / OOD-jolt, then test transfer'
  summary: 'Tiered battery to discriminate H_monitor from H_refusal_motor, H_OOD_default,
    and H_decision_echo. TIER 1 (offline, near-free, reuses data in hand): (1) Geometry
    vs refusal axis -- cosine(theta_failure, theta_refuse-vs-answer) per head; if
    ~1, H_monitor collapses into H_refusal_motor (cheap brutal falsifier); we have
    both axes'' inputs. (2) Flip-order vs difficulty -- per unknown item, the alpha
    at which it flips to refusal across the sweep, correlated with INDEPENDENT difficulty
    (baseline stated confidence / answer logprob); monitor predicts difficulty-ordered
    flips, OOD-default predicts difficulty-agnostic. (3) Read-don''t-steer wrongness
    prediction -- among ANSWERED items only (no refusal happening), does theta-projection
    predict the answer being WRONG? monitor predicts yes, refusal-motor predicts null;
    doubles as the selective-prediction/abstention-trigger test (compare AUC vs the
    model''s own stated confidence). TIER 2 (one modest GPU pass): (4) Ground-truth
    difficulty grading -- resample each item N times, empirical accuracy = difficulty;
    check theta-projection rises monotonically from always-right to always-wrong.
    (5) Pre-commitment timing -- read the projection trajectory across generated positions;
    is it high at the prompt-final/first token BEFORE the refusal tokens appear? separates
    monitor from decision-echo. (6) Random-DIRECTION control -- same 11 heads, random
    directions, matched norm; crosses head x direction with the random-HEAD control.
    TIER 3 (more GPU, the real novelty test): (7) Cross-dataset / cross-regimen transfer
    -- build theta here, read+steer on TriviaQA/bridge and on KTO/DPO regimens; transfer
    => general uncertainty monitor, no transfer => panel-surface artifact; speaks
    directly to gap:4-probe-transfer. LOGIC: Test 1 can kill it cheaply; 2-3 separate
    monitor from refusal-motor on data in hand; 5 separates monitor from decision-echo;
    6 separates specific-signal from generic-OOD-jolt; 4 upgrades difficulty to ground
    truth; 7 tests portability. Surviving 1+3+5+7 = a real, deployable result.'
  evidence:
  - experiment/notes/mech-interp-model-variation-panel.md
  run_ids: []
  commands: []
  decisions:
  - 'Sequence cheapest-falsifier-first: Tier 1 offline (no GPU) before any new GPU
    pass; only escalate to Tier 2/3 if Tier 1 does not kill H_monitor.'
  next_steps:
  - Implement Tier 1 Test 1 (per-head cosine theta_failure vs theta_refuse-vs-answer)
    -- GPU-free, reuses the extracted contrasts; a high cosine is the cheapest falsifier.
  signals: {}
- id: 003-result
  at: '2026-06-26T19:12:53Z'
  kind: result
  title: 'Random-HEAD control (sigma-matched) discriminates specific-circuit from
    OOD-default: random heads do NOT reproduce the abstention shift'
  summary: 'Decisive control for H_OOD_default. Ran the SAME A.4 sweep (alphas [-8,-4,-2,0,+4],
    256-row matched panel 128 known/128 unknown, greedy, max_new_tokens=96) on 11
    RANDOM heads (numpy default_rng seed 20260626, disjoint from the localized 11),
    each given its own mass-mean failure-axis direction at its own per-head sigma
    (standard ITI scaling). RESULT at alpha=+4 vs the SAME baseline: unknown_refused
    67 (52.3%) -> 63 (49.2%) -- i.e. refusal moved essentially ZERO, slightly DOWN;
    unknown_answered_wrong 61 -> 65 (slightly UP, wrong direction); known_correct
    63 -> 61. Only 9/256 rows changed refusal status. Contrast with the LOCALIZED
    heads at the same +4: unknown_refused 67 -> 106 (+39 cells) and unknown_answered_wrong
    61 -> 22. Even at alpha=-8 (2x the localized magnitude, opposite sign) the random
    heads moved refusal only ~+11 cells (truthful 53.1%). CONCLUSION: the localization
    is REAL -- any-11-heads + a failure-axis direction does NOT produce the abstention
    dial; the effect is specific to the localization-scan-selected heads. CAVEAT (the
    remaining loophole): the sigma-matched random control sits at ~0.298x the localized
    perturbation NORM at matched alpha (random heads have a weaker failure axis ->
    smaller sigma -> smaller alpha*sigma push). So a skeptic can still say ''give
    random heads the same norm and they''d do it too.'' The NORM-MATCHED variant (grafts
    the localized sigma multiset onto the random heads, identical total perturbation
    energy) is running to close exactly that loophole -- 680/1280 rows at last check,
    container a4_randctl up.'
  evidence:
  - experiment/phase1/probe/analysis/current_clean_grpo_v2_unknown_failure_prompt_matched_head_intervention_sweep_randomctl/summary.json
  - experiment/phase1/probe/phase3_head_norm_match_control.py
  run_ids:
  - a4_randctl
  commands: []
  decisions:
  - 'DECISION RULE for the pair: localized >> both controls => localization real (head
    selection carries the effect); norm-matched ~ localized => magnitude story (any
    heads at that energy refuse); norm-matched ~ sigma-matched (both null) => the
    effect is head-position/direction-specific AND not mere energy. Sigma-matched
    leg already null; verdict gated on the norm-matched leg.'
  next_steps:
  - 'When norm-matched summary lands: compare its +4 cells to localized (+39) and
    sigma-matched (~0) refusal moves, check generation coherence (well-formed JSON
    refusals, not OOD collapse), write the control verdict, then commit notes + control
    configs/script and PR.'
  signals: {}
- id: 004-interpretation
  at: '2026-06-26T19:21:00Z'
  kind: interpretation
  title: 'Literature grounding: the core claim is largely Ferrando 2411.14257; the
    defensible novelty is the probe-sign/causal-sign inversion + per-head localization
    + graded asymmetry'
  summary: 'Background research+ingestion agent (107k tokens, 40 tool-uses) grounded
    H_monitor against the KG + arXiv. HEADLINE for calibration: the bare claim ''a
    linear knowledge-conditioned direction causally gates refuse-vs-hallucinate''
    is ESSENTIALLY PRIOR ART. Nearest precedent: Ferrando, Obeso, Rajamanoharan, Nanda,
    ''Do I Know This Entity? Knowledge Awareness and Hallucinations in LMs'' (paper:2411.14257,
    ingested this session) -- linear/SAE ''entity-recognition directions'' the authors
    call self-knowledge, which gate refuse-vs-hallucinate and TRANSFER base->chat-refusal.
    Gradedness+transfer of such directions is also established: Semantic Entropy Probes
    (paper:2406.15927, reads graded uncertainty off hidden states incl. the token-before-generating,
    beats accuracy probes OOD by 7.7-10.5 AUROC) and the universal-truthfulness-hyperplane
    (paper:2407.08582). Steering a direction as a monotonic abstention/refusal DIAL
    is also shown (paper:2604.03147 arousal axis; paper:2411.11296 SAE-refusal-steering).
    And the SIGN dissociation itself is a known failure mode: Tan et al. ''Analyzing
    the Generalization and Reliability of Steering Vectors'' (paper:2407.12404, ingested
    this session) -- with CAA, per-input steerability is high-variance and ~50% of
    inputs on several datasets are ANTI-STEERABLE (same direction moves behavior the
    opposite way; mechanism:steering-vector-steerability-is-high-variance-and-sign-unstable).
    H_monitor sits in the ''do-I-know''/self-knowledge family (Ferrando + P(IK) paper:2207.05221
    + SEP), NOT the truth-of-statement family (Geometry-of-Truth paper:2310.06824,
    CCS, universal hyperplane). DEFENSIBLE NOVELTY (must frame AGAINST Ferrando, must
    NOT claim ''a knowledge direction exists'' or ''steering changes refusal'' as
    new): (1) a PRINCIPLED probe-sign vs causal-sign INVERSION on an abstention monitor
    derived from a BEHAVIORAL wrong-vs-refuse mass-mean contrast in a POST-TRAINING
    humility-tuned model -- Ferrando steers an entity-known label (sign intuitive);
    Tan documents anti-steerability in aggregate but does not tie it to a probe whose
    decoded meaning is the inverse of its causal role; (2) per-ATTENTION-HEAD ITI
    localization (11 sparse heads) of an abstention/uncertainty monitor (vs Ferrando''s
    residual-stream SAE latents, vs ITI''s truthfulness heads); (3) the ~5.6x unknown/known
    quantification as evidence of a graded threshold-pusher, not a gate. NET calibration
    update on the earlier ''true novel finding?'' question: the headline is NOT a
    clean novel discovery -- it is a sharper, causally-validated instance of an established
    phenomenon; the publishable contribution is the inversion+localization+asymmetry
    triad framed explicitly against Ferrando. Two papers ingested (2411.14257, 2407.12404),
    validator 0 errors. KG was already richer than the brief assumed (Geometry-of-Truth,
    SEP, CAA, universal hyperplane all pre-existing nodes).'
  evidence:
  - library/notes/2411.14257--do-i-know-this-entity-knowledge-awareness.md
  - library/notes/2407.12404--analyzing-generalization-reliability-steering-vectors.md
  - experiment/notes/uncertainty-monitor-hypothesis.md
  run_ids: []
  commands: []
  decisions:
  - Frame any write-up AGAINST Ferrando 2411.14257 as the nearest precedent and lean
    the contribution on the sign-inversion + per-head localization + graded asymmetry
    triad -- NOT on 'a knowledge direction exists' or 'steering changes refusal',
    both prior art. Do NOT overclaim novelty.
  - 'Created the H_monitor KG node as experiment:uncertainty-monitor-hypothesis (experiment/notes/uncertainty-monitor-hypothesis.md):
    tests gap:4-probe-transfer; builds_on Ferrando 2411.14257 + entity-recognition-gates
    mechanism + ITI + known-unknown-direction + P(IK) + Tan 2407.12404 + steerability-sign-unstable
    mechanism; related_to SEP 2406.15927 + probes-read-recall 2510.09033. Experiment-note
    + KG validation pass, 0 errors.'
  next_steps:
  - 'Tier 1 T3 (read-don''t-steer) is now doubly motivated: it is both the cheapest
    H_monitor falsifier AND the selective-prediction comparison vs Ferrando/SEP; run
    it first among the GPU-free tests.'
  signals: {}
- id: 005-result
  at: '2026-06-26T19:30:31Z'
  kind: result
  title: 'Norm-matched random-head control: localization carries ~75% of the abstention
    effect; ~25% is generic perturbation energy'
  summary: 'The norm-matched leg (random heads given the localized sigma MULTISET,
    i.e. identical total perturbation energy) completed (fingerprint 1b9deed8c2615450,
    256-row panel). At alpha=+4 vs the SAME baseline (unknown_refusal 52.3%): NORM-MATCHED
    random unknown_refusal -> 60.2% (= 67->77 cells, +10), answer_on_unknown 47.7->39.8,
    known_correctness 49.2->45.3, refusal_changed=21. Three-way comparison of the
    unknown-abstention shift at +4: LOCALIZED +39 cells (67->106) >> NORM-MATCHED
    random +10 cells (67->77) >> SIGMA-MATCHED random ~0 (67->63). VERDICT: (1) localization
    is REAL and dominant -- the localization-scan-selected heads move abstention ~4x
    more than energy-matched random heads, so the effect is NOT merely magnitude.
    (2) There IS a non-zero generic-energy component -- norm-matched random (+10)
    beats sigma-matched random (~0), and at alpha=-8 norm-matched pushes unknown_refusal
    to 65.6% regardless of sign, consistent with a partial OOD-drift-toward-the-JSON-default
    at high energy. Net: head selection carries ~75% of the abstention effect, ~25%
    is non-specific perturbation energy. This is a PARTIAL-specificity result (matches
    the A.4 ''partially selective, not a clean gate'' finding), appropriately hedged
    -- localization real, purity not total. H_OOD_default is downgraded but not fully
    eliminated (the energy component is real).'
  evidence:
  - experiment/phase1/probe/analysis/current_clean_grpo_v2_unknown_failure_prompt_matched_head_intervention_sweep_randomctl_normmatched/summary.json
  - experiment/phase1/probe/analysis/current_clean_grpo_v2_unknown_failure_prompt_matched_head_intervention_sweep_randomctl/summary.json
  run_ids:
  - a4_randctl
  commands: []
  decisions:
  - 'Report the localization as REAL but PARTIAL: ~75% head-selection-specific, ~25%
    generic energy. Do not claim clean/pure localization; the norm-matched +10-cell
    shift and the sign-agnostic high-energy drift are evidence of a residual non-specific
    component. This tightens but does not fully close H_OOD_default -- Tier 2 random-DIRECTION
    control (same heads, scrambled directions, matched norm) is the remaining discriminator
    for direction-specificity.'
  next_steps:
  - Both control legs done -> commit the 0025/0023 notes, the H_monitor experiment
    node, and the control configs/script as one PR. Then proceed to Tier 1 offline
    tests (geometry, read-don't-steer) which are GPU-free.
  signals: {}
- id: 006-planning
  at: '2026-06-26T19:34:51Z'
  kind: planning
  title: 'Registered base-model entity-recall arm (T8): split the pretrained sensor
    from the tuning-installed abstain-wiring'
  summary: 'Added variation T8 to the H_monitor experiment node, prompted by the Ferrando
    methods read. Ferrando 2411.14257 labels known/unknown by querying Wikidata attributes
    and thresholding the model''s OWN recall accuracy (tau=1; ~35k entities across
    players/movies/cities/songs; final-entity-token directions; generalizes beyond
    the 4 types per their Appendix B; separate ''early'' uncertainty directions; Llama-3.1-8B
    replication). Crucially the recipe needs NO refusal behavior, so it ports to a
    base model. Two non-steering forms: (a) READ test -- project the tuned 11-head
    direction into base-model activations on the same items (is the geometry pretrained?);
    (b) entity-recall construction -- build a base-model known-vs-unknown ENTITY direction
    and test subspace overlap with our tuned wrong-vs-refuse axis. Conceptual frame:
    Ferrando''s evidence says the knowledge SENSOR is pretrained (base->chat transfer),
    while the sensor->abstain WIRING is what humility tuning installs; T8 tests that
    split on our stack. Caveat: our ''unknown'' is question-level UNANSWERABILITY
    (broader) vs Ferrando''s named-ENTITY recognition (narrower), so partial overlap
    is expected and is itself a result -- and is a seam where our framing is not fully
    subsumed by Ferrando.'
  evidence:
  - experiment/notes/uncertainty-monitor-hypothesis.md
  - library/notes/2411.14257--do-i-know-this-entity-knowledge-awareness.md
  run_ids: []
  commands: []
  decisions:
  - Base-model arm uses non-steering reads (project tuned direction into base activations)
    + Ferrando's accuracy-threshold entity labeling, NOT a base-model refusal contrast
    (base models do not refuse). Treat partial overlap as the expected, informative
    outcome given the unanswerability-vs-entity-recognition framing gap.
  next_steps:
  - Sequence T8(a) read test alongside the GPU-free Tier 1 tests (both are forward-pass
    reads, no training); it needs base-model activations on the same panel items.
  signals: {}
- id: 007-result
  at: '2026-06-26T19:48:55Z'
  kind: result
  title: 'Tier 1 geometry test: failure axis IS the refuse<->answer decision axis
    (anti-aligned), orthogonal to the static knowledge boundary -- refutes the clean
    H_monitor subspace reading'
  summary: 'Ran the first Tier 1 falsifier (phase3_head_axis_geometry.py, GPU-free,
    reuses build_directions for identical mass-mean machinery; parity self-check rebuilds
    the failure axis F and matches the stored theta exactly, min cos 1.0 across all
    11 heads -> cosines trustworthy). Compared F per-head against two reference axes
    on the SAME 11 localized heads: R = refuse-vs-answer pooled (positive refused,
    negative answered) and K = knowledge-boundary behavior-agnostic (positive label=unknown,
    negative label=known). RESULT: cos(F,R) is strongly NEGATIVE and consistent across
    all 11 heads (range -0.67..-0.89, mean |cos| 0.80); cos(F,K) is near zero (mean
    |cos| 0.12). Dominance ratio 6.4x. So F lives on the refuse<->answer DECISION
    axis (anti-aligned to the refusal direction by construction: F''s positive pole
    is unknown_answered_wrong, on the ANSWER side), and is roughly ORTHOGONAL to the
    static unknown-vs-known axis. IMPLICATIONS: (1) REFUTES the clean H_refusal_motor
    (naive): F is not +parallel to the refusal motor (it is ~antiparallel, |cos|=0.80<0.95).
    (2) REFUTES the clean H_monitor GEOMETRY: F is not a distinct knowledge-boundary/uncertainty
    subspace separate from the refusal decision -- it IS (anti-aligned with) the decision
    axis, and it does NOT encode the static known/unknown label. (3) RE-CENTERS the
    puzzle: read against the A.4 causal result (adding +F, which points geometrically
    toward ANSWER, RAISES refusal), the surviving phenomenon is a READ/WRITE SIGN
    INVERSION on the decision axis itself -- a probe direction whose causal valence
    is inverted relative to BOTH its label AND its geometric placement. This connects
    directly to Tan 2407.12404 anti-steerability and to a read-vs-write geometry mismatch
    (F is READ at the final prompt token but WRITTEN at generation positions). H_monitor
    is not dead but must be REFORMULATED: not ''a separate uncertainty monitor subspace''
    but possibly ''the decision axis read pre-generation whose injection at generation
    flips behavior''; the ''amplify the brake'' metaphor now needs the brake to BE
    the decision axis with inverted gain, a more mechanical story.'
  evidence:
  - experiment/phase1/probe/phase3_head_axis_geometry.py
  - experiment/phase1/probe/analysis/current_clean_grpo_v2_unknown_failure_prompt_matched_head_axis_geometry/axis_geometry.json
  - experiment/phase1/probe/tests/test_phase3_head_axis_geometry.py
  run_ids: []
  commands: []
  decisions:
  - Demote the 'distinct uncertainty subspace' reading of H_monitor; promote the READ/WRITE
    sign-inversion explanation (the prompt-token-read axis has inverted causal valence
    at generation positions). Reframe the contribution around the sign inversion on
    the decision axis, now the cleanest surviving novel phenomenon, explicitly linked
    to Tan 2407.12404 anti-steerability.
  next_steps:
  - 'Tier 2 PROMOTED: read the failure-axis projection trajectory ACROSS generated
    positions (not just the prompt token) -- does the read axis itself flip sign between
    the prompt token and generation positions? That directly tests the read/write-mismatch
    explanation. Also Tier 1 T3 read-don''t-steer (does prompt-token F-projection
    predict wrongness among answered items vs stated confidence) is still worth running
    as the selective-prediction comparison.'
  signals: {}
- id: 008-result
  at: '2026-06-26T20:11:32Z'
  kind: result
  title: 'Tier-1 T3 read-don''t-steer: INCONCLUSIVE on current extraction (label/correctness
    collinear)'
  summary: 'phase3_head_read_projection.py reads the prompt-token (final_prompt_token)
    projection onto the per-head failure axis F (sigma-standardized, mean over the
    11 localized heads) and asks whether that pre-generation read predicts WRONGNESS
    among ANSWERED items, head-to-head vs the model''s stated_confidence (the Ferrando/SEP
    selective-prediction frame). RESULT on the 256-row current_clean_grpo_v2_unknown_failure_prompt_matched
    extraction: the clean per-label test cannot run -- the extraction has perfect
    label<->correctness collinearity (known-answered: 64/64 correct, 0 wrong; unknown-answered:
    64/64 wrong, 0 correct), so ''wrongness among answered'' IS the known/unknown
    label and there is no within-label correctness variance to predict. Pooled across
    both labels, AUROC(read->wrong)=0.71 vs AUROC(1-stated_conf->wrong)=0.58 (read
    beats verbalized confidence by +0.13 on the confidence-bearing subset), but that
    pooled number only shows F re-reads the knowledge boundary at the prompt token
    and is partly circular (F''s positive pole IS the unknown-answered-wrong rows).
    NOT selective-prediction evidence either way.'
  evidence:
  - experiment/phase1/probe/analysis/current_clean_grpo_v2_unknown_failure_prompt_matched_head_read_projection/read_projection.json
    (gitignored); 2 unit tests in test_phase3_head_read_projection.py (non-degenerate
    known-population AUROC=1.0; degenerate-population->None) pass
  run_ids: []
  commands: []
  decisions: []
  next_steps:
  - 'To run T3 cleanly, need an extraction with WITHIN-label correctness variance:
    known-answered confident ERRORS and unknown-answered lucky-correct rows. The current
    prompt-matched panel is too ''pure'' by construction. Either widen the extraction
    row pool or accept that the read-vs-confidence selective-prediction comparison
    is deferred to a base-model / variance-bearing arm (T8).'
  signals: {}
---
# uncertainty-monitor-hypothesis

## Question

Is the sign-inverted per-head failure-axis direction a graded internal UNCERTAINTY MONITOR (amplifying it raises abstention) rather than a be-wrong axis — and the 'stimulant amplifies the brake, not the symptom' analogy?

## Trajectory Position

Branches off Session 0023 (Phase 3 model-variation panel) at its Step A.4 ITI
sweep result (0023 checkpoint `038-result`). This note carries the *mechanistic
reinterpretation* of that result — whether the steered direction is a graded
uncertainty monitor — which is an evolution of, but conceptually separate from,
the model-variation panel that produced it. The A.4 sweep itself, its
resume/checkpoint infrastructure, and the broader panel stay in 0023.

## Summary

Session 0023's Step A.4 sweep found that a sparse 11-head inference-time
intervention on the failure axis is causally potent but **sign-inverted** vs the
probe: *adding* the `mean(unknown_answered_wrong) − mean(unknown_refused)`
direction (which we built as a "be-wrong" axis) **raises** abstention rather than
hallucination, and does so ~5:1 selectively for unknown vs known questions.

**H_monitor** reinterprets that inversion: the direction is not a wrongness axis
but a **graded internal uncertainty signal** ("this is hard, I might not know")
that is present during hard/unknown questions regardless of whether the model
eventually guesses or refuses. Hallucinations are items where the alarm fired
sub-threshold; refusals are items where it crossed threshold; amplifying the
alarm pushes more items over. The "stimulant calms ADHD" analogy: you amplify a
regulatory *monitor*, not the symptom, so a low-level "more" yields a behavioral
"less guessing." If it survives, the contribution is not "we steered refusal" but
"humility-trained models compute a readable, amplifiable knowledge-uncertainty
signal" — direct evidence on `gap:4-probe-transfer`.

Competing hypotheses to kill: **H_wrongness** (original be-wrong axis — already
contradicted), **H_refusal_motor** (just the refuse-vs-answer motor direction),
**H_OOD_default** (any large perturbation → fallback to the safe default
abstention), **H_decision_echo** (the projection merely echoes a decision already
made). A tiered test battery (checkpoint `002-planning`) discriminates these,
cheapest-falsifier-first. The **random-head control** (checkpoint `003-result`)
already kills H_OOD_default on the sigma-matched leg — random heads given the same
failure-axis direction move abstention ~0 (67→63 cells) vs the localized heads'
+39 — with the norm-matched leg in flight to close the magnitude loophole.

## Checkpoints
### 001-interpretation - H_monitor: the sign-inverted failure axis may be a graded UNCERTAINTY MONITOR, not a be-wrong axis

- at: `2026-06-26T19:12:16Z`
- kind: `interpretation`
- summary: ORIGIN: Session 0023 checkpoint 038-result (the A.4 ITI sweep). We BUILT the per-head direction as mean(unknown_answered_wrong) - mean(unknown_refused) and assumed a 'be-wrong' axis, so ADDING it should hallucinate MORE. Causally it does the opposite: alpha=+4 (adding the wrong-answer direction to the 11 localized heads) RAISES refusal (unknown_answered_wrong 61->22 /128, unknown_refused 67->106), and alpha<0 makes the failure WORSE. H_monitor: the direction is not a wrongness axis but a GRADED INTERNAL UNCERTAINTY ('this-is-hard, I-might-not-know') signal present DURING hard/unknown questions regardless of the eventual answer-vs-refuse outcome. Hallucinations are items where the alarm fired sub-threshold (model guessed); refusals are items where it crossed threshold (model bailed). Amplifying the alarm pushes more items over threshold -> more refusal. This is the 'stimulant calms ADHD' shape: amplifying a regulatory/MONITOR signal, not the symptom, so a low-level 'more' yields a behavioral 'less guessing'. It reframes the sign inversion from a measurement gotcha (ITI folklore: always sweep both signs) into a testable claim that humility-trained models carry a READABLE knowledge-uncertainty signal. Competing hypotheses to kill: H_wrongness (original 'be-wrong' axis -- contradicted by data); H_refusal_motor (just the refuse-vs-answer MOTOR direction, not epistemic); H_OOD_default (no specific signal; any large perturbation -> fallback to safe default abstention under the JSON prompt). GROUNDING (KG already holds adjacent lit): paper:2306.03341 (ITI), paper:2310.01405 (RepE read+control), paper:2212.03827 (CCS latent knowledge), paper:2304.13734 (internal state knows when lying), paper:2207.05221 (P(IK)), paper:2510.09033 (CAUTION: probes may read recall not truth), term:truth-direction, term:universal-truthfulness-hyperplane, term:knowledge-boundary. A background research+ingestion agent is filling external gaps (candidates: Geometry of Truth 2310.06824, Semantic Entropy Probes 2406.15927, selective-prediction-for-LLMs).
- evidence:
  - `docs/sessions/0023 - phase-3-model-variation-panel.md#038-result`
  - `experiment/notes/mech-interp-model-variation-panel.md`
- decisions:
  - Test H_monitor with READ-OUT (correlational, GPU-cheap, less confounded than steering) BEFORE more interventions; key circularity guard: never score the monitor against the same wrong/refused labels theta was built from -- use INDEPENDENT difficulty (stated response_confidence, answer-token logprob, resample accuracy, or an external model).
  - Frame the deployable version as the contribution if it survives: not 'we steered refusal' but 'humility-trained models compute a graded knowledge-uncertainty signal you can READ to abstain (selective prediction) and AMPLIFY to abstain more' -- direct evidence on gap:4-probe-transfer.
- next steps:
  - Run the Tier 1-3 test battery (see next checkpoint); Test 1 (geometry vs refusal axis) can kill it cheaply on data in hand.
### 002-planning - H_monitor test battery (Tier 1-3): kill cheap, separate monitor from refusal-motor / decision-echo / OOD-jolt, then test transfer

- at: `2026-06-26T19:12:32Z`
- kind: `planning`
- summary: Tiered battery to discriminate H_monitor from H_refusal_motor, H_OOD_default, and H_decision_echo. TIER 1 (offline, near-free, reuses data in hand): (1) Geometry vs refusal axis -- cosine(theta_failure, theta_refuse-vs-answer) per head; if ~1, H_monitor collapses into H_refusal_motor (cheap brutal falsifier); we have both axes' inputs. (2) Flip-order vs difficulty -- per unknown item, the alpha at which it flips to refusal across the sweep, correlated with INDEPENDENT difficulty (baseline stated confidence / answer logprob); monitor predicts difficulty-ordered flips, OOD-default predicts difficulty-agnostic. (3) Read-don't-steer wrongness prediction -- among ANSWERED items only (no refusal happening), does theta-projection predict the answer being WRONG? monitor predicts yes, refusal-motor predicts null; doubles as the selective-prediction/abstention-trigger test (compare AUC vs the model's own stated confidence). TIER 2 (one modest GPU pass): (4) Ground-truth difficulty grading -- resample each item N times, empirical accuracy = difficulty; check theta-projection rises monotonically from always-right to always-wrong. (5) Pre-commitment timing -- read the projection trajectory across generated positions; is it high at the prompt-final/first token BEFORE the refusal tokens appear? separates monitor from decision-echo. (6) Random-DIRECTION control -- same 11 heads, random directions, matched norm; crosses head x direction with the random-HEAD control. TIER 3 (more GPU, the real novelty test): (7) Cross-dataset / cross-regimen transfer -- build theta here, read+steer on TriviaQA/bridge and on KTO/DPO regimens; transfer => general uncertainty monitor, no transfer => panel-surface artifact; speaks directly to gap:4-probe-transfer. LOGIC: Test 1 can kill it cheaply; 2-3 separate monitor from refusal-motor on data in hand; 5 separates monitor from decision-echo; 6 separates specific-signal from generic-OOD-jolt; 4 upgrades difficulty to ground truth; 7 tests portability. Surviving 1+3+5+7 = a real, deployable result.
- evidence:
  - `experiment/notes/mech-interp-model-variation-panel.md`
- decisions:
  - Sequence cheapest-falsifier-first: Tier 1 offline (no GPU) before any new GPU pass; only escalate to Tier 2/3 if Tier 1 does not kill H_monitor.
- next steps:
  - Implement Tier 1 Test 1 (per-head cosine theta_failure vs theta_refuse-vs-answer) -- GPU-free, reuses the extracted contrasts; a high cosine is the cheapest falsifier.
### 003-result - Random-HEAD control (sigma-matched) discriminates specific-circuit from OOD-default: random heads do NOT reproduce the abstention shift

- at: `2026-06-26T19:12:53Z`
- kind: `result`
- summary: Decisive control for H_OOD_default. Ran the SAME A.4 sweep (alphas [-8,-4,-2,0,+4], 256-row matched panel 128 known/128 unknown, greedy, max_new_tokens=96) on 11 RANDOM heads (numpy default_rng seed 20260626, disjoint from the localized 11), each given its own mass-mean failure-axis direction at its own per-head sigma (standard ITI scaling). RESULT at alpha=+4 vs the SAME baseline: unknown_refused 67 (52.3%) -> 63 (49.2%) -- i.e. refusal moved essentially ZERO, slightly DOWN; unknown_answered_wrong 61 -> 65 (slightly UP, wrong direction); known_correct 63 -> 61. Only 9/256 rows changed refusal status. Contrast with the LOCALIZED heads at the same +4: unknown_refused 67 -> 106 (+39 cells) and unknown_answered_wrong 61 -> 22. Even at alpha=-8 (2x the localized magnitude, opposite sign) the random heads moved refusal only ~+11 cells (truthful 53.1%). CONCLUSION: the localization is REAL -- any-11-heads + a failure-axis direction does NOT produce the abstention dial; the effect is specific to the localization-scan-selected heads. CAVEAT (the remaining loophole): the sigma-matched random control sits at ~0.298x the localized perturbation NORM at matched alpha (random heads have a weaker failure axis -> smaller sigma -> smaller alpha*sigma push). So a skeptic can still say 'give random heads the same norm and they'd do it too.' The NORM-MATCHED variant (grafts the localized sigma multiset onto the random heads, identical total perturbation energy) is running to close exactly that loophole -- 680/1280 rows at last check, container a4_randctl up.
- run ids:
  - `a4_randctl`
- evidence:
  - `experiment/phase1/probe/analysis/current_clean_grpo_v2_unknown_failure_prompt_matched_head_intervention_sweep_randomctl/summary.json`
  - `experiment/phase1/probe/phase3_head_norm_match_control.py`
- decisions:
  - DECISION RULE for the pair: localized >> both controls => localization real (head selection carries the effect); norm-matched ~ localized => magnitude story (any heads at that energy refuse); norm-matched ~ sigma-matched (both null) => the effect is head-position/direction-specific AND not mere energy. Sigma-matched leg already null; verdict gated on the norm-matched leg.
- next steps:
  - When norm-matched summary lands: compare its +4 cells to localized (+39) and sigma-matched (~0) refusal moves, check generation coherence (well-formed JSON refusals, not OOD collapse), write the control verdict, then commit notes + control configs/script and PR.
### 004-interpretation - Literature grounding: the core claim is largely Ferrando 2411.14257; the defensible novelty is the probe-sign/causal-sign inversion + per-head localization + graded asymmetry

- at: `2026-06-26T19:21:00Z`
- kind: `interpretation`
- summary: Background research+ingestion agent (107k tokens, 40 tool-uses) grounded H_monitor against the KG + arXiv. HEADLINE for calibration: the bare claim 'a linear knowledge-conditioned direction causally gates refuse-vs-hallucinate' is ESSENTIALLY PRIOR ART. Nearest precedent: Ferrando, Obeso, Rajamanoharan, Nanda, 'Do I Know This Entity? Knowledge Awareness and Hallucinations in LMs' (paper:2411.14257, ingested this session) -- linear/SAE 'entity-recognition directions' the authors call self-knowledge, which gate refuse-vs-hallucinate and TRANSFER base->chat-refusal. Gradedness+transfer of such directions is also established: Semantic Entropy Probes (paper:2406.15927, reads graded uncertainty off hidden states incl. the token-before-generating, beats accuracy probes OOD by 7.7-10.5 AUROC) and the universal-truthfulness-hyperplane (paper:2407.08582). Steering a direction as a monotonic abstention/refusal DIAL is also shown (paper:2604.03147 arousal axis; paper:2411.11296 SAE-refusal-steering). And the SIGN dissociation itself is a known failure mode: Tan et al. 'Analyzing the Generalization and Reliability of Steering Vectors' (paper:2407.12404, ingested this session) -- with CAA, per-input steerability is high-variance and ~50% of inputs on several datasets are ANTI-STEERABLE (same direction moves behavior the opposite way; mechanism:steering-vector-steerability-is-high-variance-and-sign-unstable). H_monitor sits in the 'do-I-know'/self-knowledge family (Ferrando + P(IK) paper:2207.05221 + SEP), NOT the truth-of-statement family (Geometry-of-Truth paper:2310.06824, CCS, universal hyperplane). DEFENSIBLE NOVELTY (must frame AGAINST Ferrando, must NOT claim 'a knowledge direction exists' or 'steering changes refusal' as new): (1) a PRINCIPLED probe-sign vs causal-sign INVERSION on an abstention monitor derived from a BEHAVIORAL wrong-vs-refuse mass-mean contrast in a POST-TRAINING humility-tuned model -- Ferrando steers an entity-known label (sign intuitive); Tan documents anti-steerability in aggregate but does not tie it to a probe whose decoded meaning is the inverse of its causal role; (2) per-ATTENTION-HEAD ITI localization (11 sparse heads) of an abstention/uncertainty monitor (vs Ferrando's residual-stream SAE latents, vs ITI's truthfulness heads); (3) the ~5.6x unknown/known quantification as evidence of a graded threshold-pusher, not a gate. NET calibration update on the earlier 'true novel finding?' question: the headline is NOT a clean novel discovery -- it is a sharper, causally-validated instance of an established phenomenon; the publishable contribution is the inversion+localization+asymmetry triad framed explicitly against Ferrando. Two papers ingested (2411.14257, 2407.12404), validator 0 errors. KG was already richer than the brief assumed (Geometry-of-Truth, SEP, CAA, universal hyperplane all pre-existing nodes).
- evidence:
  - `library/notes/2411.14257--do-i-know-this-entity-knowledge-awareness.md`
  - `library/notes/2407.12404--analyzing-generalization-reliability-steering-vectors.md`
  - `experiment/notes/uncertainty-monitor-hypothesis.md`
- decisions:
  - Frame any write-up AGAINST Ferrando 2411.14257 as the nearest precedent and lean the contribution on the sign-inversion + per-head localization + graded asymmetry triad -- NOT on 'a knowledge direction exists' or 'steering changes refusal', both prior art. Do NOT overclaim novelty.
  - Created the H_monitor KG node as experiment:uncertainty-monitor-hypothesis (experiment/notes/uncertainty-monitor-hypothesis.md): tests gap:4-probe-transfer; builds_on Ferrando 2411.14257 + entity-recognition-gates mechanism + ITI + known-unknown-direction + P(IK) + Tan 2407.12404 + steerability-sign-unstable mechanism; related_to SEP 2406.15927 + probes-read-recall 2510.09033. Experiment-note + KG validation pass, 0 errors.
- next steps:
  - Tier 1 T3 (read-don't-steer) is now doubly motivated: it is both the cheapest H_monitor falsifier AND the selective-prediction comparison vs Ferrando/SEP; run it first among the GPU-free tests.
### 005-result - Norm-matched random-head control: localization carries ~75% of the abstention effect; ~25% is generic perturbation energy

- at: `2026-06-26T19:30:31Z`
- kind: `result`
- summary: The norm-matched leg (random heads given the localized sigma MULTISET, i.e. identical total perturbation energy) completed (fingerprint 1b9deed8c2615450, 256-row panel). At alpha=+4 vs the SAME baseline (unknown_refusal 52.3%): NORM-MATCHED random unknown_refusal -> 60.2% (= 67->77 cells, +10), answer_on_unknown 47.7->39.8, known_correctness 49.2->45.3, refusal_changed=21. Three-way comparison of the unknown-abstention shift at +4: LOCALIZED +39 cells (67->106) >> NORM-MATCHED random +10 cells (67->77) >> SIGMA-MATCHED random ~0 (67->63). VERDICT: (1) localization is REAL and dominant -- the localization-scan-selected heads move abstention ~4x more than energy-matched random heads, so the effect is NOT merely magnitude. (2) There IS a non-zero generic-energy component -- norm-matched random (+10) beats sigma-matched random (~0), and at alpha=-8 norm-matched pushes unknown_refusal to 65.6% regardless of sign, consistent with a partial OOD-drift-toward-the-JSON-default at high energy. Net: head selection carries ~75% of the abstention effect, ~25% is non-specific perturbation energy. This is a PARTIAL-specificity result (matches the A.4 'partially selective, not a clean gate' finding), appropriately hedged -- localization real, purity not total. H_OOD_default is downgraded but not fully eliminated (the energy component is real).
- run ids:
  - `a4_randctl`
- evidence:
  - `experiment/phase1/probe/analysis/current_clean_grpo_v2_unknown_failure_prompt_matched_head_intervention_sweep_randomctl_normmatched/summary.json`
  - `experiment/phase1/probe/analysis/current_clean_grpo_v2_unknown_failure_prompt_matched_head_intervention_sweep_randomctl/summary.json`
- decisions:
  - Report the localization as REAL but PARTIAL: ~75% head-selection-specific, ~25% generic energy. Do not claim clean/pure localization; the norm-matched +10-cell shift and the sign-agnostic high-energy drift are evidence of a residual non-specific component. This tightens but does not fully close H_OOD_default -- Tier 2 random-DIRECTION control (same heads, scrambled directions, matched norm) is the remaining discriminator for direction-specificity.
- next steps:
  - Both control legs done -> commit the 0025/0023 notes, the H_monitor experiment node, and the control configs/script as one PR. Then proceed to Tier 1 offline tests (geometry, read-don't-steer) which are GPU-free.
### 006-planning - Registered base-model entity-recall arm (T8): split the pretrained sensor from the tuning-installed abstain-wiring

- at: `2026-06-26T19:34:51Z`
- kind: `planning`
- summary: Added variation T8 to the H_monitor experiment node, prompted by the Ferrando methods read. Ferrando 2411.14257 labels known/unknown by querying Wikidata attributes and thresholding the model's OWN recall accuracy (tau=1; ~35k entities across players/movies/cities/songs; final-entity-token directions; generalizes beyond the 4 types per their Appendix B; separate 'early' uncertainty directions; Llama-3.1-8B replication). Crucially the recipe needs NO refusal behavior, so it ports to a base model. Two non-steering forms: (a) READ test -- project the tuned 11-head direction into base-model activations on the same items (is the geometry pretrained?); (b) entity-recall construction -- build a base-model known-vs-unknown ENTITY direction and test subspace overlap with our tuned wrong-vs-refuse axis. Conceptual frame: Ferrando's evidence says the knowledge SENSOR is pretrained (base->chat transfer), while the sensor->abstain WIRING is what humility tuning installs; T8 tests that split on our stack. Caveat: our 'unknown' is question-level UNANSWERABILITY (broader) vs Ferrando's named-ENTITY recognition (narrower), so partial overlap is expected and is itself a result -- and is a seam where our framing is not fully subsumed by Ferrando.
- evidence:
  - `experiment/notes/uncertainty-monitor-hypothesis.md`
  - `library/notes/2411.14257--do-i-know-this-entity-knowledge-awareness.md`
- decisions:
  - Base-model arm uses non-steering reads (project tuned direction into base activations) + Ferrando's accuracy-threshold entity labeling, NOT a base-model refusal contrast (base models do not refuse). Treat partial overlap as the expected, informative outcome given the unanswerability-vs-entity-recognition framing gap.
- next steps:
  - Sequence T8(a) read test alongside the GPU-free Tier 1 tests (both are forward-pass reads, no training); it needs base-model activations on the same panel items.
### 007-result - Tier 1 geometry test: failure axis IS the refuse<->answer decision axis (anti-aligned), orthogonal to the static knowledge boundary -- refutes the clean H_monitor subspace reading

- at: `2026-06-26T19:48:55Z`
- kind: `result`
- summary: Ran the first Tier 1 falsifier (phase3_head_axis_geometry.py, GPU-free, reuses build_directions for identical mass-mean machinery; parity self-check rebuilds the failure axis F and matches the stored theta exactly, min cos 1.0 across all 11 heads -> cosines trustworthy). Compared F per-head against two reference axes on the SAME 11 localized heads: R = refuse-vs-answer pooled (positive refused, negative answered) and K = knowledge-boundary behavior-agnostic (positive label=unknown, negative label=known). RESULT: cos(F,R) is strongly NEGATIVE and consistent across all 11 heads (range -0.67..-0.89, mean |cos| 0.80); cos(F,K) is near zero (mean |cos| 0.12). Dominance ratio 6.4x. So F lives on the refuse<->answer DECISION axis (anti-aligned to the refusal direction by construction: F's positive pole is unknown_answered_wrong, on the ANSWER side), and is roughly ORTHOGONAL to the static unknown-vs-known axis. IMPLICATIONS: (1) REFUTES the clean H_refusal_motor (naive): F is not +parallel to the refusal motor (it is ~antiparallel, |cos|=0.80<0.95). (2) REFUTES the clean H_monitor GEOMETRY: F is not a distinct knowledge-boundary/uncertainty subspace separate from the refusal decision -- it IS (anti-aligned with) the decision axis, and it does NOT encode the static known/unknown label. (3) RE-CENTERS the puzzle: read against the A.4 causal result (adding +F, which points geometrically toward ANSWER, RAISES refusal), the surviving phenomenon is a READ/WRITE SIGN INVERSION on the decision axis itself -- a probe direction whose causal valence is inverted relative to BOTH its label AND its geometric placement. This connects directly to Tan 2407.12404 anti-steerability and to a read-vs-write geometry mismatch (F is READ at the final prompt token but WRITTEN at generation positions). H_monitor is not dead but must be REFORMULATED: not 'a separate uncertainty monitor subspace' but possibly 'the decision axis read pre-generation whose injection at generation flips behavior'; the 'amplify the brake' metaphor now needs the brake to BE the decision axis with inverted gain, a more mechanical story.
- evidence:
  - `experiment/phase1/probe/phase3_head_axis_geometry.py`
  - `experiment/phase1/probe/analysis/current_clean_grpo_v2_unknown_failure_prompt_matched_head_axis_geometry/axis_geometry.json`
  - `experiment/phase1/probe/tests/test_phase3_head_axis_geometry.py`
- decisions:
  - Demote the 'distinct uncertainty subspace' reading of H_monitor; promote the READ/WRITE sign-inversion explanation (the prompt-token-read axis has inverted causal valence at generation positions). Reframe the contribution around the sign inversion on the decision axis, now the cleanest surviving novel phenomenon, explicitly linked to Tan 2407.12404 anti-steerability.
- next steps:
  - Tier 2 PROMOTED: read the failure-axis projection trajectory ACROSS generated positions (not just the prompt token) -- does the read axis itself flip sign between the prompt token and generation positions? That directly tests the read/write-mismatch explanation. Also Tier 1 T3 read-don't-steer (does prompt-token F-projection predict wrongness among answered items vs stated confidence) is still worth running as the selective-prediction comparison.
### 008-result - Tier-1 T3 read-don't-steer: INCONCLUSIVE on current extraction (label/correctness collinear)

- at: `2026-06-26T20:11:32Z`
- kind: `result`
- summary: phase3_head_read_projection.py reads the prompt-token (final_prompt_token) projection onto the per-head failure axis F (sigma-standardized, mean over the 11 localized heads) and asks whether that pre-generation read predicts WRONGNESS among ANSWERED items, head-to-head vs the model's stated_confidence (the Ferrando/SEP selective-prediction frame). RESULT on the 256-row current_clean_grpo_v2_unknown_failure_prompt_matched extraction: the clean per-label test cannot run -- the extraction has perfect label<->correctness collinearity (known-answered: 64/64 correct, 0 wrong; unknown-answered: 64/64 wrong, 0 correct), so 'wrongness among answered' IS the known/unknown label and there is no within-label correctness variance to predict. Pooled across both labels, AUROC(read->wrong)=0.71 vs AUROC(1-stated_conf->wrong)=0.58 (read beats verbalized confidence by +0.13 on the confidence-bearing subset), but that pooled number only shows F re-reads the knowledge boundary at the prompt token and is partly circular (F's positive pole IS the unknown-answered-wrong rows). NOT selective-prediction evidence either way.
- evidence:
  - `experiment/phase1/probe/analysis/current_clean_grpo_v2_unknown_failure_prompt_matched_head_read_projection/read_projection.json (gitignored); 2 unit tests in test_phase3_head_read_projection.py (non-degenerate known-population AUROC=1.0; degenerate-population->None) pass`
- next steps:
  - To run T3 cleanly, need an extraction with WITHIN-label correctness variance: known-answered confident ERRORS and unknown-answered lucky-correct rows. The current prompt-matched panel is too 'pure' by construction. Either widen the extraction row pool or accept that the read-vs-confidence selective-prediction comparison is deferred to a base-model / variance-bearing arm (T8).
