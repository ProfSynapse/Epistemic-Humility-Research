---
schema_version: research-session/v1
session_id: '0026'
title: caution-vs-doubt-knowledge-gate
status: active
created_at: '2026-06-27T09:37:23Z'
updated_at: '2026-06-27T10:32:31Z'
phase: phase3
question: Are caution (a late refuse/answer gate) and doubt (graded knowledge-axis
  position) separable signals, and is over-refusal a miscalibrated late gate over
  borderline-known items rather than suppression of fully-known answers?
tags:
- mech-interp
- caution-axis
- knowledge-axis
- doubt
- epistemic-humility
run_ids: []
trajectory:
  anchor: experiment/protocol/research-trajectory.md
  current_position: ''
  changed_by_session: ''
checkpoints:
- id: 001-result
  at: '2026-06-27T09:37:56Z'
  kind: result
  title: 'Branch founding: depth profile separates early knowledge from a late caution
    gate; over-refused items are intermediate-known'
  summary: 'GPU-free layer-resolved probe (h_lora, end-of-question residuals, 168
    rows/group balanced, 5-fold logistic AUROC). KNOWLEDGE contrast known_refused
    vs unknown_refused (BOTH refused -> behavior held fixed, isolates knowability):
    AUROC 0.969 at L2, 0.996 by L26 and flat to L36. CAUTION contrast known_refused
    vs known_correct_answered (BOTH known -> knowledge held fixed, isolates refuse/answer):
    AUROC 0.704 at L2 climbing monotonically to 0.907 at L35. Two opposite depth profiles:
    knowability is established early (likely question-surface familiarity, since extraction
    is at end-of-prompt pre-generation, so this is prospective answerability not verified
    retrieval); the refuse-vs-answer decision among KNOWN items is a LATE-forming
    gate peaking at L35 (second-to-last block; 37 hidden states L0..L36). Humility-tax
    projection: fit a CLEAN knowledge axis on known_correct_answered vs unknown_refused
    (never sees known_refused), project the over-refused group: known_answered=-180
    (known anchor), known_refused=-228, unknown_refused=-297 (unknown anchor) -> over-refused
    sit 58% of the way from UNKNOWN toward KNOWN. Over-refused items are NOT internally
    identical to confidently-answered ones; they are an intermediate, partially-known
    population. Reframes the claim: over-refusal is a late caution gate over-converting
    BORDERLINE doubt into refusal, not suppression of fully-known answers. Geometry
    caveat: raw mass-mean cos(caution, knowledge) approx -0.5 but inflated by shared
    anchor group; rigorous whitened-probe orthogonality (~0.02) from session 0025
    is the trusted separation number.'
  evidence:
  - scratchpad/depth_knowledge_caution.py over extraction__55254a04aa1f; caution_direction_L35.json
    (raw mass-mean, AUROC 0.9094)
  run_ids: []
  commands: []
  decisions:
  - Treat caution (late binary gate) and doubt (graded knowledge-axis position) as
    candidate-separable constructs; this is a distinct branch from the 0025 caution-monitor-timing
    line.
  next_steps:
  - 'GPU-free: correlate emitted response_confidence vs caution-axis and knowledge-axis
    projections on answered rows (does graded confidence ride the knowledge axis =
    doubt, while caution is the binary gate?). Then GPU: doubt-axis from hedged-answered
    vs confident-answered generations; layer-band caution ablation to locate where
    the gate becomes load-bearing. B1 single-site L35 ablation running now.'
  signals: {}
- id: 002-result
  at: '2026-06-27T09:42:09Z'
  kind: result
  title: 'Confidence-vs-axes: emitted confidence is flat/uninformative; caution and
    knowledge are LARGELY COLLINEAR in raw space (cos -0.83); refusal = low-known
    tail of a single graded doubt axis'
  summary: 'GPU-free, scratchpad/confidence_vs_axes.py over 556 B2 known rows (emitted
    response_confidence parsed from JSON) + L35 h_lora projections. (A) Within answered
    rows, emitted response_confidence has ~ZERO Spearman with BOTH axes (knowledge
    rho=-0.04, caution rho=+0.05) -- but this is because emitted confidence is NEAR-CONSTANT
    (~0.82 correct vs ~0.81 wrong), i.e. the model does NOT verbalize internal doubt;
    the channel is too flat to adjudicate doubt-location. (B) Refuse(1)-vs-answer(0)
    separability over known rows: caution axis AUROC 0.909 (definitional); KNOWLEDGE
    axis AUROC 0.127 = 0.873 flipped -> refused-knowns sit LOWER on the knowledge
    axis. So the knowledge/doubt axis ALSO separates refuse/answer strongly. (C) Knowledge-axis
    ordering is monotonic: correct-answered -184 > wrong-answered -202 (n=15, tentative)
    > refused-known -228 > unknown -297. The axis tracks REAL correctness even among
    answered items. GEOMETRY UPDATE: raw mass-mean cos(caution theta, clean knowledge
    axis ka-ur) = -0.83 (highly collinear, opposite sign), NOT the ~0.02 near-orthogonality
    reported in session 0025. The 0025 number was a whitened/logistic construction;
    raw and whitened can both hold (shared bulk variance, orthogonal residual). REVISION:
    my prior-turn ''two cleanly separable signals'' claim is too strong. The dominant
    raw geometry is ONE graded epistemic (knowledge/doubt) axis; refusal happens at
    its low-known tail; caution is largely doubt-thresholding, with only a small whitened-orthogonal
    caution-specific residual. CAVEAT FOR B1: ablating the raw caution theta at L35
    is ~83% ablating the knowledge/doubt axis too, so the known_answered specificity
    control becomes diagnostic -- if ablation also harms known_answered correctness,
    we removed doubt/knowledge, not a clean gate.'
  evidence:
  - scratchpad/confidence_vs_axes.py; caution_direction_L35.json; B2 rows.jsonl (556
    known); extraction__55254a04aa1f
  run_ids: []
  commands: []
  decisions:
  - Downgrade the strict two-stage separable-signals hypothesis; adopt a single-graded-doubt-axis-with-low-tail-thresholding
    model as the leading account, with a small caution-specific residual to be isolated
    by whitened/non-overlapping-anchor geometry. Emitted response_confidence is unusable
    as a doubt proxy (flat).
  next_steps:
  - 'Nail the geometry: whitened cos(caution, knowledge) + non-overlapping-anchor
    split-half cos, to size the caution-specific residual vs the shared doubt axis.
    Re-read B1 with the collinearity caveat (use known_answered control as the doubt-vs-gate
    discriminator). Doubt-axis-from-generations experiment still valuable to test
    if a generation-position doubt signal diverges from the prompt-position knowledge
    axis.'
  signals: {}
- id: 003-result
  at: '2026-06-27T09:48:06Z'
  kind: result
  title: 'Linchpin geometry: caution is NOT reducible to doubt-thresholding -- held-out
    refuse/answer survives at AUROC 0.825 after projecting out the doubt axis'
  summary: 'GPU-free, scratchpad/caution_residual_geometry.py, L35 h_lora, kr=168/ka=300/ur=300,
    shrinkage-whitened cov (lam=0.1), 5-fold held-out. GEOMETRY: raw cos(caution,knowledge)=-0.830
    BUT whitened/Mahalanobis cos=-0.565, and the caution direction''s residual fraction
    off the knowledge axis = 0.557 (55.7% of the caution direction length, ~31% of
    variance, is doubt-orthogonal). LINCHPIN held-out refuse(1)/answer(0) AUROC among
    KNOWNS: knowledge axis alone = 0.125 (=0.875 flipped; strong doubt-thresholding,
    refuse=less-known); caution orthogonalized to knowledge (caution_perp) = 0.825;
    full caution = 0.894. Removing the entire (rank-1) doubt direction barely dents
    refuse/answer separability (0.894 -> 0.825), so the refuse/answer decision is
    NOT confined to the doubt axis -- a genuine caution-specific gate exists. METHOD
    LESSON: raw cosine in high-dim activation space is dominated by a few shared high-variance
    dims and OVERSTATES collinearity (-0.83); the reliable instrument is held-out
    discriminability after orthogonalization, which says separate-gate. This RE-VALIDATES
    the session-0025 whitened near-orthogonality (~0.02): stronger whitening pushes
    -0.83 -> -0.56 -> toward 0. CAVEAT: only the rank-1 mass-mean doubt direction
    was projected out; a multi-dimensional knowledge-probe subspace removal is the
    stronger next test. Caution and doubt ARE correlated (both elevated on the low-known
    tail) but separable.'
  evidence:
  - scratchpad/caution_residual_geometry.py; extraction__55254a04aa1f; caution_direction_L35.json
  run_ids: []
  commands: []
  decisions:
  - 'Re-adopt a TWO-component model (revised): a graded doubt/knowledge axis (refuse=low-known
    tail) PLUS a partially-separate caution gate carrying refuse/answer structure
    orthogonal to doubt (>=55% of the caution direction, held-out AUROC 0.825). Reject
    last turn''s ''caution fully reducible to doubt-thresholding''. Trust held-out
    discriminability over raw cosine.'
  next_steps:
  - 'Stronger reducibility test: project out a full multi-dim knowledge-probe subspace
    (not just rank-1 mass-mean) and re-check caution_perp AUROC. Refine B1: a CLEANER
    causal arm ablates the doubt-orthogonalized caution_perp direction (isolates the
    gate) rather than raw theta (which is 83% doubt-aligned). Re-read the in-flight
    B1 single-site L35 raw-theta ablation with the known_answered control as the doubt-vs-gate
    discriminator.'
  signals: {}
- id: 004-result
  at: '2026-06-27T09:54:49Z'
  kind: result
  title: 'Calibration gap quantified: stated confidence flat+underconfident (ECE 0.14,
    AUROC 0.56); internal doubt-axis probe well-calibrated (ECE 0.004) and more discriminating
    -- the model KNOWS but doesn''t SAY'
  summary: 'GPU-free, scratchpad/calibration_gap.py, B2 answered known rows n=389
    (373 correct / 16 wrong; UNDERPOWERED on wrong -> discrimination numbers directional).
    Predict correct(1) vs wrong(0). Model accuracy among answered = 0.959. EMITTED
    response_confidence: mean 0.821, std 0.015 (essentially CONSTANT), AUROC 0.559
    (~chance at ranking its own right vs wrong answers), ECE 0.142. DOUBT-axis raw
    projection AUROC 0.667; 1-D logistic probe on the doubt projection (axis = ka
    vs ur, no correct/wrong leakage, 5-fold CV) mean p 0.959, AUROC 0.649, ECE 0.004
    (near-perfect aggregate calibration; matches base rate). Per-cell emitted confidence
    is flat (known_correct_answered 0.821, known_answered_wrong 0.813, known_refused
    0.811 -- all ~0.81) while doubt projection is monotone (correct -176 > wrong -194
    > refused -226). TWO failures of honesty, both robust to the 16-wrong caveat:
    (1) AGGREGATE miscalibration -- the model states ~0.82 but is right 96%, i.e.
    systematically UNDER-confident on answered items (even a constant 0.96 would beat
    it); (2) NO discrimination -- stated confidence cannot rank correct vs wrong (0.56)
    while the internal axis can (0.65-0.67, noisy at n=16). The discriminating signal
    exists internally; the verbalized number is a collapsed near-constant. Likely
    cause: training never graded the confidence field against realized correctness
    (proper-scoring pressure absent) -> collapse to a safe low prior.'
  evidence:
  - scratchpad/calibration_gap.py; B2 rows.jsonl (389 answered); extraction__55254a04aa1f
  run_ids: []
  commands: []
  decisions:
  - 'Adopt the ''knowing-vs-saying'' calibration gap as a headline result: internal
    epistemic state is calibratable (ECE 0.004 via linear readout) even though emitted
    confidence is flat+underconfident (ECE 0.14). Honesty-by-readout (a logistic probe
    on the doubt axis) is the cheapest honesty lever. Discrimination claim is directional
    pending more wrong-answered rows.'
  next_steps:
  - 'Power the discrimination test: harvest more known_answered_wrong rows (GPU generation
    or a higher-error dataset) and re-run AUROC. Optional: proper-scoring-rule (Brier/log-loss)
    retrain of the confidence field as the actual fix (links to session 0018 response-confidence
    training). Synthesis: BOTH action channels (refuse/answer + stated confidence)
    are timid readouts decoupled from one well-ordered internal doubt axis -- refusal
    is gradient-hypersensitive, confidence is flat+depressed.'
  signals: {}
- id: 005-result
  at: '2026-06-27T10:11:42Z'
  kind: result
  title: 'B1 caution-axis causal intervention: LOAD-BEARING'
  summary: 'B1 GPU intervention complete (2164 units, raw-theta L35, 4 arms). Verdict
    LOAD-BEARING. Ablating the caution axis on known_refused drops refusal 0.994->0.030
    (delta -0.96) and 57.1% of de-refused knowns answer correctly. Specificity holds:
    known_correct_answered refusal stays 0.00 (+0.00 collateral), correct 1.00->0.979.
    Monotone bidirectional dose-response: shift_plus2 induces 19.6% new refusals on
    previously-answered knowns + saturates known_refused at 100%; shift_minus2 partial
    (refusal 0.65, 28.6% correct). Under the 83%-doubt-aligned caveat the specificity
    control passing means this is not a global doubt wipe but behaviorally specific
    to over-refusal; the 57% (not ~98%) correct-on-de-refusal is the two-component
    fingerprint (part spurious caution recovered, part genuine residual doubt).'
  evidence:
  - experiment/phase1/probe/analysis/current_clean_grpo_v2_caution_residual_intervention/summary.json
  run_ids: []
  commands: []
  decisions:
  - Caution gate is causal for over-refusal, not merely correlational. Refined B1
    should ablate caution_perp (doubt-orthogonalized) to attribute the residual split.
  next_steps:
  - Commit B1 module/runner/config/tests + PR; draft new SFT-computed-confidence training
    regimen note; refined B1 on caution_perp.
  signals: {}
- id: 006-interpretation
  at: '2026-06-27T10:24:44Z'
  kind: interpretation
  title: 'Audit: emitted-confidence collapse is GRPO-driven, not SFT-driven'
  summary: 'Read-only audit of session 0018 corrects the computed-confidence regimen
    premise. (1) The clean SFT base is NOT a flat-0.8 prior: 2489 unique confidence
    values spread 0.35-0.9, mean 0.788 (0018 section 009). (2) Probe-scaled (computed
    per-question) SFT was ALREADY run and collapsed to a single value 0.8765 because
    the target distribution is imbalanced (modal target 0.8765 covered 81.79% of rows,
    low-band rows 0) -> SFT minimized loss by emitting the mode; explicitly paused,
    not taken downstream (section 004). (3) The emitted-confidence collapse is GRPO-driven:
    clean SFT emits a spread, GRPO v1 already banded it (known/unknown means 0.746/0.747
    nearly identical, top value 0.711 on 1521 rows, section 023) and v2 tightened
    to std 0.015 (session 0026), because the v1/v2 reward made a near-constant confidence
    reward-optimal. Brier-vs-appropriateness was already an eval metric (GRPO v1 0.3697);
    session 0026 added the ECE/AUROC/internal-coherence framing.'
  evidence:
  - docs/sessions/0018 - probe-scaled-response-confidence-retrain.md; experiment/phase1/eval/results_amendment_e_response_confidence_selfaware_clean_sft_grpo_seed1_corrected_base_full_4b/
  run_ids: []
  commands: []
  decisions:
  - 'Primary lever is the v3 GRPO proper-scoring reward (arm B0: clean SFT -> GRPO-v3),
    NOT redoing the SFT dataset. Redoing SFT with naive computed confidence is unnecessary
    for anti-collapse (clean SFT already spread) and insufficient alone (collapses
    from target imbalance). Secondary open arm: quantile-balanced per-question SFT
    target.'
  next_steps:
  - 'On sign-off: CPU preflight v3 re-scoring of v2 rollouts (confirm group targets
    spread), then B0 train+eval vs clean-sft-grpo-v2.'
  signals: {}
- id: 007-validation
  at: '2026-06-27T10:32:31Z'
  kind: validation
  title: "v3 reward CPU preflight GREEN \u2014 B0 de-risked"
  summary: 'Re-scored 19904 real GRPO rollouts (v1 full reward_debug, 4211 distinct
    prompts; refused/correct re-derived with base reward matchers, grouped by gold-answer
    set) with the v3 proper-scoring reward via experiment/phase1/grpo/v3_reward_preflight.py.
    Q1 group-target spread: mean 0.571, std 0.320, range 0-1, 65.6% in [0.2,0.8] ->
    the degenerate-target collapse-one-level-up risk is empirically ABSENT (v3 has
    real per-prompt signal). Q2 behavior ordering on real data: known_correct +3.04
    > unknown_abstain +2.20 > known_wrong -0.45 > known_over_refusal -1.78 (behavior
    dominance holds beyond unit tests). Q3 proper scoring beats flat 0.82 on 4211/4211
    prompts (mean Brier gain +0.394). PREFLIGHT GREEN: B0 well-posed.'
  evidence:
  - experiment/phase1/grpo/v3_reward_preflight.py; scratch/schema_response_confidence/reward_debug/schema_sft_grpo_seed1_full_b32_latest.jsonl
  run_ids: []
  commands: []
  decisions:
  - B0 (clean SFT -> GRPO-v3) is the de-risked primary arm. Spread is a property of
    the fixed question set's difficulty range so it survives the policy shift during
    training.
  next_steps:
  - B0 gated on user sign-off + governed PROTOCOL amendment before any GPU training
    run.
  signals: {}
---
# caution-vs-doubt-knowledge-gate

## Question

Are caution (a late refuse/answer gate) and doubt (graded knowledge-axis position) separable signals, and is over-refusal a miscalibrated late gate over borderline-known items rather than suppression of fully-known answers?

## Trajectory Position

_Not yet recorded._

## Summary

_No summary yet._

## Checkpoints
### 001-result - Branch founding: depth profile separates early knowledge from a late caution gate; over-refused items are intermediate-known

- at: `2026-06-27T09:37:56Z`
- kind: `result`
- summary: GPU-free layer-resolved probe (h_lora, end-of-question residuals, 168 rows/group balanced, 5-fold logistic AUROC). KNOWLEDGE contrast known_refused vs unknown_refused (BOTH refused -> behavior held fixed, isolates knowability): AUROC 0.969 at L2, 0.996 by L26 and flat to L36. CAUTION contrast known_refused vs known_correct_answered (BOTH known -> knowledge held fixed, isolates refuse/answer): AUROC 0.704 at L2 climbing monotonically to 0.907 at L35. Two opposite depth profiles: knowability is established early (likely question-surface familiarity, since extraction is at end-of-prompt pre-generation, so this is prospective answerability not verified retrieval); the refuse-vs-answer decision among KNOWN items is a LATE-forming gate peaking at L35 (second-to-last block; 37 hidden states L0..L36). Humility-tax projection: fit a CLEAN knowledge axis on known_correct_answered vs unknown_refused (never sees known_refused), project the over-refused group: known_answered=-180 (known anchor), known_refused=-228, unknown_refused=-297 (unknown anchor) -> over-refused sit 58% of the way from UNKNOWN toward KNOWN. Over-refused items are NOT internally identical to confidently-answered ones; they are an intermediate, partially-known population. Reframes the claim: over-refusal is a late caution gate over-converting BORDERLINE doubt into refusal, not suppression of fully-known answers. Geometry caveat: raw mass-mean cos(caution, knowledge) approx -0.5 but inflated by shared anchor group; rigorous whitened-probe orthogonality (~0.02) from session 0025 is the trusted separation number.
- evidence:
  - `scratchpad/depth_knowledge_caution.py over extraction__55254a04aa1f; caution_direction_L35.json (raw mass-mean, AUROC 0.9094)`
- decisions:
  - Treat caution (late binary gate) and doubt (graded knowledge-axis position) as candidate-separable constructs; this is a distinct branch from the 0025 caution-monitor-timing line.
- next steps:
  - GPU-free: correlate emitted response_confidence vs caution-axis and knowledge-axis projections on answered rows (does graded confidence ride the knowledge axis = doubt, while caution is the binary gate?). Then GPU: doubt-axis from hedged-answered vs confident-answered generations; layer-band caution ablation to locate where the gate becomes load-bearing. B1 single-site L35 ablation running now.
### 002-result - Confidence-vs-axes: emitted confidence is flat/uninformative; caution and knowledge are LARGELY COLLINEAR in raw space (cos -0.83); refusal = low-known tail of a single graded doubt axis

- at: `2026-06-27T09:42:09Z`
- kind: `result`
- summary: GPU-free, scratchpad/confidence_vs_axes.py over 556 B2 known rows (emitted response_confidence parsed from JSON) + L35 h_lora projections. (A) Within answered rows, emitted response_confidence has ~ZERO Spearman with BOTH axes (knowledge rho=-0.04, caution rho=+0.05) -- but this is because emitted confidence is NEAR-CONSTANT (~0.82 correct vs ~0.81 wrong), i.e. the model does NOT verbalize internal doubt; the channel is too flat to adjudicate doubt-location. (B) Refuse(1)-vs-answer(0) separability over known rows: caution axis AUROC 0.909 (definitional); KNOWLEDGE axis AUROC 0.127 = 0.873 flipped -> refused-knowns sit LOWER on the knowledge axis. So the knowledge/doubt axis ALSO separates refuse/answer strongly. (C) Knowledge-axis ordering is monotonic: correct-answered -184 > wrong-answered -202 (n=15, tentative) > refused-known -228 > unknown -297. The axis tracks REAL correctness even among answered items. GEOMETRY UPDATE: raw mass-mean cos(caution theta, clean knowledge axis ka-ur) = -0.83 (highly collinear, opposite sign), NOT the ~0.02 near-orthogonality reported in session 0025. The 0025 number was a whitened/logistic construction; raw and whitened can both hold (shared bulk variance, orthogonal residual). REVISION: my prior-turn 'two cleanly separable signals' claim is too strong. The dominant raw geometry is ONE graded epistemic (knowledge/doubt) axis; refusal happens at its low-known tail; caution is largely doubt-thresholding, with only a small whitened-orthogonal caution-specific residual. CAVEAT FOR B1: ablating the raw caution theta at L35 is ~83% ablating the knowledge/doubt axis too, so the known_answered specificity control becomes diagnostic -- if ablation also harms known_answered correctness, we removed doubt/knowledge, not a clean gate.
- evidence:
  - `scratchpad/confidence_vs_axes.py; caution_direction_L35.json; B2 rows.jsonl (556 known); extraction__55254a04aa1f`
- decisions:
  - Downgrade the strict two-stage separable-signals hypothesis; adopt a single-graded-doubt-axis-with-low-tail-thresholding model as the leading account, with a small caution-specific residual to be isolated by whitened/non-overlapping-anchor geometry. Emitted response_confidence is unusable as a doubt proxy (flat).
- next steps:
  - Nail the geometry: whitened cos(caution, knowledge) + non-overlapping-anchor split-half cos, to size the caution-specific residual vs the shared doubt axis. Re-read B1 with the collinearity caveat (use known_answered control as the doubt-vs-gate discriminator). Doubt-axis-from-generations experiment still valuable to test if a generation-position doubt signal diverges from the prompt-position knowledge axis.
### 003-result - Linchpin geometry: caution is NOT reducible to doubt-thresholding -- held-out refuse/answer survives at AUROC 0.825 after projecting out the doubt axis

- at: `2026-06-27T09:48:06Z`
- kind: `result`
- summary: GPU-free, scratchpad/caution_residual_geometry.py, L35 h_lora, kr=168/ka=300/ur=300, shrinkage-whitened cov (lam=0.1), 5-fold held-out. GEOMETRY: raw cos(caution,knowledge)=-0.830 BUT whitened/Mahalanobis cos=-0.565, and the caution direction's residual fraction off the knowledge axis = 0.557 (55.7% of the caution direction length, ~31% of variance, is doubt-orthogonal). LINCHPIN held-out refuse(1)/answer(0) AUROC among KNOWNS: knowledge axis alone = 0.125 (=0.875 flipped; strong doubt-thresholding, refuse=less-known); caution orthogonalized to knowledge (caution_perp) = 0.825; full caution = 0.894. Removing the entire (rank-1) doubt direction barely dents refuse/answer separability (0.894 -> 0.825), so the refuse/answer decision is NOT confined to the doubt axis -- a genuine caution-specific gate exists. METHOD LESSON: raw cosine in high-dim activation space is dominated by a few shared high-variance dims and OVERSTATES collinearity (-0.83); the reliable instrument is held-out discriminability after orthogonalization, which says separate-gate. This RE-VALIDATES the session-0025 whitened near-orthogonality (~0.02): stronger whitening pushes -0.83 -> -0.56 -> toward 0. CAVEAT: only the rank-1 mass-mean doubt direction was projected out; a multi-dimensional knowledge-probe subspace removal is the stronger next test. Caution and doubt ARE correlated (both elevated on the low-known tail) but separable.
- evidence:
  - `scratchpad/caution_residual_geometry.py; extraction__55254a04aa1f; caution_direction_L35.json`
- decisions:
  - Re-adopt a TWO-component model (revised): a graded doubt/knowledge axis (refuse=low-known tail) PLUS a partially-separate caution gate carrying refuse/answer structure orthogonal to doubt (>=55% of the caution direction, held-out AUROC 0.825). Reject last turn's 'caution fully reducible to doubt-thresholding'. Trust held-out discriminability over raw cosine.
- next steps:
  - Stronger reducibility test: project out a full multi-dim knowledge-probe subspace (not just rank-1 mass-mean) and re-check caution_perp AUROC. Refine B1: a CLEANER causal arm ablates the doubt-orthogonalized caution_perp direction (isolates the gate) rather than raw theta (which is 83% doubt-aligned). Re-read the in-flight B1 single-site L35 raw-theta ablation with the known_answered control as the doubt-vs-gate discriminator.
### 004-result - Calibration gap quantified: stated confidence flat+underconfident (ECE 0.14, AUROC 0.56); internal doubt-axis probe well-calibrated (ECE 0.004) and more discriminating -- the model KNOWS but doesn't SAY

- at: `2026-06-27T09:54:49Z`
- kind: `result`
- summary: GPU-free, scratchpad/calibration_gap.py, B2 answered known rows n=389 (373 correct / 16 wrong; UNDERPOWERED on wrong -> discrimination numbers directional). Predict correct(1) vs wrong(0). Model accuracy among answered = 0.959. EMITTED response_confidence: mean 0.821, std 0.015 (essentially CONSTANT), AUROC 0.559 (~chance at ranking its own right vs wrong answers), ECE 0.142. DOUBT-axis raw projection AUROC 0.667; 1-D logistic probe on the doubt projection (axis = ka vs ur, no correct/wrong leakage, 5-fold CV) mean p 0.959, AUROC 0.649, ECE 0.004 (near-perfect aggregate calibration; matches base rate). Per-cell emitted confidence is flat (known_correct_answered 0.821, known_answered_wrong 0.813, known_refused 0.811 -- all ~0.81) while doubt projection is monotone (correct -176 > wrong -194 > refused -226). TWO failures of honesty, both robust to the 16-wrong caveat: (1) AGGREGATE miscalibration -- the model states ~0.82 but is right 96%, i.e. systematically UNDER-confident on answered items (even a constant 0.96 would beat it); (2) NO discrimination -- stated confidence cannot rank correct vs wrong (0.56) while the internal axis can (0.65-0.67, noisy at n=16). The discriminating signal exists internally; the verbalized number is a collapsed near-constant. Likely cause: training never graded the confidence field against realized correctness (proper-scoring pressure absent) -> collapse to a safe low prior.
- evidence:
  - `scratchpad/calibration_gap.py; B2 rows.jsonl (389 answered); extraction__55254a04aa1f`
- decisions:
  - Adopt the 'knowing-vs-saying' calibration gap as a headline result: internal epistemic state is calibratable (ECE 0.004 via linear readout) even though emitted confidence is flat+underconfident (ECE 0.14). Honesty-by-readout (a logistic probe on the doubt axis) is the cheapest honesty lever. Discrimination claim is directional pending more wrong-answered rows.
- next steps:
  - Power the discrimination test: harvest more known_answered_wrong rows (GPU generation or a higher-error dataset) and re-run AUROC. Optional: proper-scoring-rule (Brier/log-loss) retrain of the confidence field as the actual fix (links to session 0018 response-confidence training). Synthesis: BOTH action channels (refuse/answer + stated confidence) are timid readouts decoupled from one well-ordered internal doubt axis -- refusal is gradient-hypersensitive, confidence is flat+depressed.
### 005-result - B1 caution-axis causal intervention: LOAD-BEARING

- at: `2026-06-27T10:11:42Z`
- kind: `result`
- summary: B1 GPU intervention complete (2164 units, raw-theta L35, 4 arms). Verdict LOAD-BEARING. Ablating the caution axis on known_refused drops refusal 0.994->0.030 (delta -0.96) and 57.1% of de-refused knowns answer correctly. Specificity holds: known_correct_answered refusal stays 0.00 (+0.00 collateral), correct 1.00->0.979. Monotone bidirectional dose-response: shift_plus2 induces 19.6% new refusals on previously-answered knowns + saturates known_refused at 100%; shift_minus2 partial (refusal 0.65, 28.6% correct). Under the 83%-doubt-aligned caveat the specificity control passing means this is not a global doubt wipe but behaviorally specific to over-refusal; the 57% (not ~98%) correct-on-de-refusal is the two-component fingerprint (part spurious caution recovered, part genuine residual doubt).
- evidence:
  - `experiment/phase1/probe/analysis/current_clean_grpo_v2_caution_residual_intervention/summary.json`
- decisions:
  - Caution gate is causal for over-refusal, not merely correlational. Refined B1 should ablate caution_perp (doubt-orthogonalized) to attribute the residual split.
- next steps:
  - Commit B1 module/runner/config/tests + PR; draft new SFT-computed-confidence training regimen note; refined B1 on caution_perp.
### 006-interpretation - Audit: emitted-confidence collapse is GRPO-driven, not SFT-driven

- at: `2026-06-27T10:24:44Z`
- kind: `interpretation`
- summary: Read-only audit of session 0018 corrects the computed-confidence regimen premise. (1) The clean SFT base is NOT a flat-0.8 prior: 2489 unique confidence values spread 0.35-0.9, mean 0.788 (0018 section 009). (2) Probe-scaled (computed per-question) SFT was ALREADY run and collapsed to a single value 0.8765 because the target distribution is imbalanced (modal target 0.8765 covered 81.79% of rows, low-band rows 0) -> SFT minimized loss by emitting the mode; explicitly paused, not taken downstream (section 004). (3) The emitted-confidence collapse is GRPO-driven: clean SFT emits a spread, GRPO v1 already banded it (known/unknown means 0.746/0.747 nearly identical, top value 0.711 on 1521 rows, section 023) and v2 tightened to std 0.015 (session 0026), because the v1/v2 reward made a near-constant confidence reward-optimal. Brier-vs-appropriateness was already an eval metric (GRPO v1 0.3697); session 0026 added the ECE/AUROC/internal-coherence framing.
- evidence:
  - `docs/sessions/0018 - probe-scaled-response-confidence-retrain.md; experiment/phase1/eval/results_amendment_e_response_confidence_selfaware_clean_sft_grpo_seed1_corrected_base_full_4b/`
- decisions:
  - Primary lever is the v3 GRPO proper-scoring reward (arm B0: clean SFT -> GRPO-v3), NOT redoing the SFT dataset. Redoing SFT with naive computed confidence is unnecessary for anti-collapse (clean SFT already spread) and insufficient alone (collapses from target imbalance). Secondary open arm: quantile-balanced per-question SFT target.
- next steps:
  - On sign-off: CPU preflight v3 re-scoring of v2 rollouts (confirm group targets spread), then B0 train+eval vs clean-sft-grpo-v2.
### 007-validation - v3 reward CPU preflight GREEN — B0 de-risked

- at: `2026-06-27T10:32:31Z`
- kind: `validation`
- summary: Re-scored 19904 real GRPO rollouts (v1 full reward_debug, 4211 distinct prompts; refused/correct re-derived with base reward matchers, grouped by gold-answer set) with the v3 proper-scoring reward via experiment/phase1/grpo/v3_reward_preflight.py. Q1 group-target spread: mean 0.571, std 0.320, range 0-1, 65.6% in [0.2,0.8] -> the degenerate-target collapse-one-level-up risk is empirically ABSENT (v3 has real per-prompt signal). Q2 behavior ordering on real data: known_correct +3.04 > unknown_abstain +2.20 > known_wrong -0.45 > known_over_refusal -1.78 (behavior dominance holds beyond unit tests). Q3 proper scoring beats flat 0.82 on 4211/4211 prompts (mean Brier gain +0.394). PREFLIGHT GREEN: B0 well-posed.
- evidence:
  - `experiment/phase1/grpo/v3_reward_preflight.py; scratch/schema_response_confidence/reward_debug/schema_sft_grpo_seed1_full_b32_latest.jsonl`
- decisions:
  - B0 (clean SFT -> GRPO-v3) is the de-risked primary arm. Spread is a property of the fixed question set's difficulty range so it survives the policy shift during training.
- next steps:
  - B0 gated on user sign-off + governed PROTOCOL amendment before any GPU training run.
### 008-result - Full-eval calibration baseline + internal-vs-emitted head-to-head (B0 control)

- at: `2026-06-27T11:12:00Z`
- kind: `result`
- summary: GPU-free, reusable `experiment/phase1/eval/analysis/calibration_gap_report.py` over the FULL clean_sft_grpo_v2 SelfAware eval (3369 rows) + a head-to-head against the L35 internal doubt axis on the 1233-row behavior subset. This is the locked Amendment J section-5 CONTROL the B0 (GRPO-v3) eval must beat. (A) Emitted response_confidence is collapsed: mean 0.813, std 0.0126, range [0.70,0.88], 50 unique values; per-cell means are flat to +/-0.01 -- known_correct_answered 0.822 vs known_answered_wrong 0.820 (delta 0.002, IDENTICAL when right vs wrong), unknown_refused 0.811 = known_refused 0.811. ECE-vs-appropriateness 0.403, Brier 0.403 (model claims ~0.81 appropriate, is 0.41 appropriate -> massively overconfident once over-refusals count). AUROC emitted->appropriateness 0.520; AUROC emitted->correct-vs-wrong among answered-known 0.521 (n=780, 360 wrong -> WELL-POWERED here, unlike 0026's n=16 subset, and still chance). (B) Head-to-head on identical 1233 rows: internal L35 doubt axis (doubt_u = unit(mean ka - mean ur)) AUROC->known/unknown = 0.972 vs emitted 0.637; internal vs emitted coupling Pearson 0.336 / Spearman 0.173. Internal cell means monotone known-side: ka -174 > kaw -193 > kr -224 >> ur -290 / uaw -286 (known_refused sits on the KNOWN side = over-refusal-gap signature). NOTE auroc_internal->appropriateness = 0.351 (below chance) is NOT a defect: the doubt axis tracks known/unknown, while appropriateness spans both ends (unknown_refused is appropriate AND low-proj; known_refused is inappropriate AND high-proj) -- the knowledge axis is a knowledge detector, not an appropriateness oracle; appropriateness additionally needs the answer/refuse ACTION, which is the broken channel.
- evidence:
  - `experiment/phase1/eval/analysis/calibration_gap_report.py; experiment/phase1/eval/analysis/calibration_gap_clean_sft_grpo_v2_seed1.json`
- decisions:
  - 'Model knows but doesn't say' now quantified head-to-head on identical rows: internal known/unknown AUROC 0.972 vs emitted 0.637, Spearman coupling 0.17. The internal knowledge is present and near-separable; the emitted scalar fails to express it and is decoupled from it. This is exactly the gap B0's proper-scoring reward targets (tie the emitted scalar to realized appropriateness) while the behavior term keeps repairing the action channel.
  - Numbers are consistent with 0026 (NOT contradictory): 0026 ECE 0.14 / AUROC 0.56 were scoped to answered-known rows vs CORRECTNESS (n=389, 16 wrong); this is full-eval emitted vs APPROPRIATENESS (the Amendment J section-5 target) + the head-to-head. The earlier internal fitted-probe ECE 0.004 is the calibrated analogue of the 0.972 threshold-free AUROC here.
- next steps:
  - Re-run calibration_gap_report.py on B0's scored_rows after the GRPO-v3 full run for an apples-to-apples table; success = emitted std up, ECE-vs-appropriateness down, emitted->known/appropriateness AUROC toward the internal 0.97, Spearman(internal,emitted) up.
### 009-interpretation - Stage trajectory refines 'GRPO-driven collapse': v2-specific std-crush + SFT-level discrimination failure

- at: `2026-06-27T11:30:00Z`
- kind: `interpretation`
- summary: Ran calibration_gap_report.py Analysis A across all three training stages (full SelfAware eval, 3369 rows each). emitted response_confidence std/mean/ECE-vs-appropriateness/AUROC->correct-vs-wrong: clean_SFT 0.047 / 0.748 / 0.343 / 0.489; GRPO_v1 0.047 / 0.747 / 0.350 / 0.460; GRPO_v2 0.013 / 0.813 / 0.403 / 0.521. Two refinements to checkpoint 006's 'collapse is GRPO-driven': (1) the STD-collapse is v2-SPECIFIC, not generic GRPO -- v1 PRESERVED SFT's spread (std 0.047 unchanged); only v2 crushed it to 0.013. 006's 'v1 already banded it' was about the known/unknown MEANS being equal (0.746/0.747 = no discrimination), which still holds; overall std is a separate axis and survived v1. (2) DISCRIMINATION was never present -- emitted AUROC->correct-vs-wrong is ~0.5 at EVERY stage including clean SFT (0.489), so GRPO did not destroy discrimination; SFT never created it. Separately, GRPO worsens overconfidence: mean drifts 0.748->0.813 while appropriateness stays ~0.40, so ECE rises 0.343->0.403. Also note clean SFT already COMPRESSES the training-target spread (targets std ~0.15 / 2489 unique -> SFT emits std 0.047 / 52 unique): SFT learns the format and a muted spread, not the full target distribution.
- evidence:
  - `experiment/phase1/eval/analysis/calibration_gap_report.py over clean_sft_seed1_merged_full / clean_sft_grpo_seed1_corrected_base_full / clean_sft_grpo_v2_seed1_corrected_base_full`
- decisions:
  - B0's v3 proper-scoring reward has TWO jobs the baseline proves are BOTH needed: (a) restore/expand spread (counter v2's std-crush), and (b) INDUCE discrimination the emitted scalar never had at any stage (tie it to realized appropriateness so it ranks correct vs wrong). The internal L35 axis (AUROC 0.972, checkpoint 008) shows the signal exists to be surfaced; the proper-scoring Brier term is the mechanism to surface it into the scalar.
- next steps:
  - After B0, compare its Analysis-A row in this trajectory table: success = std up from 0.013, ECE down from 0.403, AUROC->correct-vs-wrong up from ~0.5 toward the internal 0.97.
### 010-result - Refined B1 (caution_perp, doubt-orthogonalized): independently LOAD-BEARING, two-component attribution

- at: `2026-06-27T11:55:00Z`
- kind: `result`
- summary: Refined-B1 GPU intervention complete (2164 units, L35 caution_perp = caution with the rank-1 doubt axis removed, perp_fraction 0.558, 4 arms). Verdict LOAD-BEARING. Ablating ONLY the caution-specific (doubt-orthogonal) component drops known_refused refusal 0.994->0.524 (delta -0.47) with specificity intact (known_correct_answered refusal +0.00, correct 1.0->0.973). correct_rate is over the FULL cell (n=168), so de-refused-correct = 0.327/0.476 = 68.7%. Bidirectional monotone dose-response: shift_minus2 refusal 0.869 (corr 0.113), ablate 0.524 (corr 0.327), baseline 0.994, shift_plus2 1.0 AND induces new known_correct refusals 0.070 (corr 1.0->0.928). ATTRIBUTION vs raw-theta B1 (#110, same model/rows/layer): raw-theta ablate de-refused 97% (refusal 0.99->0.03, correct 0.571 of 168 = 58.9% per de-refused); caution_perp ablate de-refuses ~48% (correct 68.7% per de-refused). So ~half the over-refusal de-refusal (-0.47 of raw-theta's -0.96) is carried by the caution-SPECIFIC gate and ~half by the doubt-aligned component that caution_perp removed -> over-refusal is a TWO-component phenomenon (caution-specific gate + doubt-axis thresholding), neither alone reproducing the full effect. The caution-specific de-refusals are MORE accurate per row (68.7% vs 58.9%): removing the spurious gate recovers genuinely-known answers, while the extra rows raw-theta de-refuses via the doubt-aligned component are lower-accuracy (genuine residual doubt). raw-theta is uniformly stronger across all arms (shift magnitudes too), consistent with caution_perp being a 0.558-mass sub-component.
- evidence:
  - `experiment/phase1/probe/analysis/current_clean_grpo_v2_caution_perp_residual_intervention/summary.json (untracked per convention); experiment/phase1/probe/build_caution_perp_direction.py; experiment/phase1/probe/config/phase3_current_clean_grpo_v2_caution_perp_residual_intervention.yaml`
- decisions:
  - The doubt-orthogonalized caution gate is INDEPENDENTLY causal for over-refusal (not merely the doubt axis in disguise): with the rank-1 doubt direction removed it still de-refuses half the over-refusals at high specificity. Caution is not reducible to doubt-thresholding; the two are separable causal contributors. This closes the raw-theta caveat (raw theta was 83% doubt-aligned) -- the caution-specific residual is load-bearing on its own.
- next steps:
  - Commit build script + config + PR (analysis outputs stay untracked). The training half (Amendment J / B0 GRPO-v3) proceeds in parallel (smoke launched).
### 011-validation - B0 GRPO-v3 smoke GREEN; full run launched

- at: `2026-06-27T12:05:00Z`
- kind: `validation`
- summary: Amendment J B0 cell (clean schema-SFT seed1 -> GRPO-v3 proper-scoring reward). 12-step smoke completed clean (exit 0). Gate GREEN on every axis: per-completion reward std 1.82 over 384 rows (range [-3.6,3.2], 321 unique); per-STEP within-group reward std 1.17-2.11 at all 12 steps and frac_reward_zero_std=0.0 throughout (no degenerate groups -> the proper-scoring term gives GRPO a live learning signal a constant-confidence policy could not earn). Group confidence_targets spread mean 0.591 std 0.334 over {0,0.125,0.25,0.5,0.75,1.0} (matches the CPU preflight std 0.320 -> real per-group appropriateness, not collapsed-one-level-up). Behavior ordering correct: known +1.52 > unknown +1.16 > ambiguous +0.21. valid_json 97.1% (373/384). Emitted response_confidence already spans [0.311,0.899] std 0.105 under temp-1.35 sampling (not greedy eval, so not directly vs v2's 0.013, but the policy demonstrably CAN emit a range and the reward differentiates it). Reward path resolves via base_dir=Trainers/grpo (../../../experiment -> repo root), trainer self-bootstraps sys.path. Triton gpt_oss MoE kernel import warning is benign (Qwen3 is dense; same as v2).
- evidence:
  - `scratch/schema_response_confidence/runs/schema_clean_sft_grpo_v3_seed1_smoke/20260627_113404/; scratch/schema_response_confidence/reward_debug/schema_clean_sft_grpo_v3_seed1_smoke.jsonl`
- decisions:
  - Smoke->full gate PASSED; launched the full B0 run (container phase3-grpo-v3-full, config grpo_schema_clean_sft_merged_seed1_v3_full.yaml, 1 epoch = 1861 optimizer steps over 14888 prompts at 8 unique prompts/step [batch 32 / num_generations 4], reward-debug to schema_clean_sft_grpo_v3_seed1_full.jsonl). First launch died on a run-dir PermissionError (container uid 1001 could not mkdir inside my uid-1000 755 dir); fixed by chmod 777 on the full output dir (same treatment the smoke dir already had) and relaunched -- training started clean (run dir 20260627_114253). v2 cell outputs untouched (distinct run dir).
- next steps:
  - On full completion: merge adapter, run the Amendment E/F SelfAware eval, then calibration_gap_report.py on B0 scored_rows for the apples-to-apples table vs v2 (target: emitted std up from 0.013, ECE-vs-appropriateness down from 0.403, AUROC->known/appropriateness up toward internal 0.97, Spearman(internal,emitted) up); re-probe L35 doubt-axis coherence.
### 012-result - B0 GRPO-v3 full run COMPLETE (clean); SelfAware eval launched

- at: `2026-06-27T18:50:00Z`
- kind: `result`
- summary: Full B0 (clean schema-SFT seed1 -> GRPO-v3 proper-scoring Brier reward) finished clean, exit 0, "GRPO TRAINING COMPLETED". Final: 1861/1861 steps (full epoch 1.0), train_runtime 24514s (~6.8h), final train_loss 0.1485. Reward stayed varied to the end -- final logged step rewards/combined_reward mean 1.348 std 1.773, frac_reward_zero_std 0.0 (no group collapse at any point; proper-scoring term kept a live signal through the whole run). Completions mean length ~26 tokens, clipped_ratio 0.0085, kl 1.39. Adapter at runs/schema_clean_sft_grpo_v3_seed1_full/20260627_115816/final_model (adapter_model.safetensors 252MB) + checkpoints 1000/1500/1861; training_lineage.json + capacity_features.json written. No reboot interruptions on the run that completed (run dir 20260627_115816; the earlier 114253 attempt was lost to the reboot, this is the relaunch). Reward never collapsed = the exact contrast to v2, whose EMITTED scalar collapsed to std 0.013 post-hoc.
- evidence:
  - `scratch/schema_response_confidence/runs/schema_clean_sft_grpo_v3_seed1_full/20260627_115816/final_model/; .../training_lineage.json; .../capacity_features.json`
- decisions:
  - No separate adapter-merge step needed for eval: the v2 corrected-base eval pattern applies the GRPO LoRA directly on the merged-SFT base via vLLM (enable_lora, max_lora_rank 32). Mirrored that exactly in a new eval config so scored_rows are apples-to-apples vs grpo_v2. `method: clean_schema_sft_grpo_v3` is free-text provenance (run_eval passes it through, not registry-validated -- the method-registration gotcha was trainer-side).
  - Created `experiment/phase1/eval/config/eval_amendment_j_response_confidence_selfaware_clean_sft_grpo_v3_seed1_full_local_4b.yaml` (verbatim copy of the v2 corrected-base config; only results_dir + arm name/method/adapter changed). Launched eval container phase3-eval-grpo-v3 (run_eval.py --live-vllm); vLLM loaded clean (Qwen3, LoRA enabled). 3369 SelfAware rows, temp 0, n_samples 1.
- next steps:
  - On eval completion: run calibration_gap_report.py on B0 scored_rows (Analysis A) for the apples-to-apples table vs v2 (targets: emitted std up from 0.013, ECE-vs-appropriateness down from 0.403, AUROC->correct-vs-wrong up from ~0.5 toward internal 0.97). Then re-probe L35 doubt-axis coherence (Analysis B needs an overlay+extraction on the v3 model -- separate extraction run). Then open the PR (refined B1 + Amendment J + B0 configs + eval results).
### 013-result - B0 GRPO-v3 calibration eval: proper-scoring reward LARGELY FAILED (calibrated negative result)

- at: `2026-06-27T19:10:00Z`
- kind: `result`
- summary: B0 SelfAware eval complete (3369 rows, exit 0). Apples-to-apples vs v2 (same merged-SFT base, prompt, gold, generation/vLLM; ONLY the reward changed). BEHAVIOR preserved as designed: over_refusal 66.62->65.13%, truthful 41.08->40.99%, correct_on_known 53.85->52.52%, refusal_rate 74.83->73.46% (magnitudes held, so the comparison isolates calibration). CALIBRATION = mostly NEGATIVE. Emitted response_confidence (greedy, temp 0): std 0.0126->0.0273 (doubled but STILL collapsed -- all in [0.711,0.889], 49 unique, mean 0.813->0.849 i.e. MORE overconfident). AUROC emitted->appropriateness 0.5197->0.5221 (NO movement, still chance). ECE vs appropriateness 0.4026->0.4395 (WORSE). Brier vs appropriateness 0.4034->0.4345 (WORSE). The ONE real gain: AUROC correct-vs-wrong among answered-known rows 0.5207->0.5999 (+0.08, real but narrow/modest; n=815, 387 wrong). Per-cell emitted means barely separate (known_correct_answered 0.852 vs known_answered_wrong 0.842 = 0.010 gap; unknown_answered_wrong lowest at 0.835). The internal L35 doubt axis is AUROC 0.972 on known/unknown (checkpoint 008); the emitted scalar after v3 is still ~0.52 on appropriateness -> "model knows but doesn't say" is essentially UNCHANGED.
- evidence:
  - `experiment/phase1/eval/results_amendment_j_response_confidence_selfaware_clean_sft_grpo_v3_seed1_full_4b/clean_schema_sft_grpo_v3_seed1__selfaware/{scored_rows.jsonl,metrics.json} (untracked outputs); experiment/phase1/eval/analysis/calibration_gap_clean_sft_grpo_v3_seed1.json (committed report)`
- decisions:
  - VERDICT (calibrated, no spin): the proper-scoring Brier reward did NOT fix the calibration gap. It failed its primary job (surface internal knowledge into the emitted scalar): appropriateness AUROC unmoved at chance, emitted confidence still collapsed, ECE/Brier actually worse (mean confidence rose without appropriateness rising). Only the narrow correct-vs-wrong-among-answered-known sub-question improved (0.52->0.60).
  - LIKELY MECHANISM: confidence_weight 1.2 was too weak against preserved behavior magnitudes (+/-2.0) -> weak confidence gradient, behavior term dominates. The smoke proved the policy CAN spread confidence under temp-1.35 sampling (std 0.105), but proper-scoring never sharpened the GREEDY/modal confidence to track per-item appropriateness; at temp-0 eval it reverts to a near-constant high value. The per-group target (4 generations/prompt) gives limited within-prompt confidence variance for the reward to exploit.
- next steps:
  - This is a publishable negative result for the calibration-gap thread as-is. If a v4 is pursued (would need a NEW governed amendment): raise confidence_weight substantially relative to behavior magnitudes, and/or move the proper-scoring target to per-completion realized appropriateness rather than per-group, and/or add an eval-time check on modal (not just sampled) confidence spread. Do NOT relaunch without a signed amendment -- v0.3/Amendment-E/v2 cells remain locked and untouched.
  - Open the PR (refined B1 caution_perp + Amendment J + B0 configs + this calibration eval result). Analysis-B (internal-vs-emitted on the v3 model) would need a fresh L35 extraction on v3 generations -- optional follow-up, not required for the PR.
### 014-planning - Amendment K (contrastive-SFT calibration base) DRAFTED, preflight GREEN, pending sign-off

- at: `2026-06-27T19:45:00Z`
- kind: `planning`
- summary: After the v3 negative result, did a grounded theory pass on "align via RL for internal coherence" and decomposed the v3 full-run reward trace: the proper-score (calibration) term owns only 3.18% of within-group reward variance (behavior ~89%) -> inline GRPO is structurally signal-starved for a 3-token readout in a ~26-token completion, and behavior reinforcement (smeared onto the confidence tokens via shared advantage) drags confidence UP (explains mean 0.81->0.85). Framed three objectives (external-marginal / external-per-item / internal-coherence) and ranked fixes by credit-assignment isolation. User chose direction (C) fix-upstream-at-SFT, then (within C) "full contrastive, behavior-gated". Root cause confirmed in the builder: build_clean_sft_rows supervises ONLY appropriate completions (all high band [0.70,0.90], spread = hash noise) -> the model is never shown a low-confidence-warranting example -> collapse is inevitable. The half-trained contrastive-SFT (0018 ckpt-1500) already produced behavior-conditional confidence (known_correct 0.444 > known_wrong 0.280; unknown_refusal 0.668 > unknown_answer 0.246) -- abandoned only for poor (half-trained) behavior, not failed calibration.
- evidence:
  - `experiment/protocol/AMENDMENT-K-contrastive-sft-behavior-conditional-confidence.md (DRAFT)`
  - `experiment/phase1/grpo/configs/sft_schema_contrastive_seed1_{smoke,full}.yaml`
  - `scratch/schema_response_confidence/qwen3-4b-instruct/sft_response_confidence_train_contrastive.jsonl (29338 rows, bimodal)`
- decisions:
  - Amendment K authorizes ONE new local SFT cell schema_contrastive_sft_seed1 trained to completion, mirroring the clean-SFT recipe EXACTLY (r32/a64, batch10, LR2e-4, 1 epoch, completion_only+assistant_only, seed1) -- ONLY the dataset differs (contrastive bimodal vs clean band-noise), so any delta is attributable to the data. v0.3/E/J + clean-SFT base untouched.
  - PRIMARY RISK documented: completion_only/assistant_only masks the prompt, NOT the answer sub-span; the schema is one JSON object, so inappropriate rows train the wrong-ANSWER text (the likely cause of the half-trained run's poor behavior). Cannot mask the sub-span without editing synaptic-tuner (out of bounds). Mitigation = hard BEHAVIOR GATE (truthful >=35.6, correct_on_known >=42.2, over_refusal <=67.5, refusal_recall >=82.0 vs clean-SFT base); fallback on gate failure = probe-scaled appropriate + ~15% contrastive low tail.
  - CALIBRATION GATE (objective): emitted AUROC->appropriateness >=0.62 (vs ~0.52), behavior-conditional cell means, emitted std >=0.10, ECE <0.30.
  - CPU preflight GREEN: configs parse + mirror recipe; 29338 rows all valid schema payloads; bimodal appropriate(0.80)/inappropriate(0.23)/ambiguous(0.47); full ~2934 steps.
- next steps:
  - HOLD for user sign-off on Amendment K (protocol locked -- no training without signature). On sign-off: chmod 777 output dirs -> smoke (max_steps 32) -> verify lineage assistant_only + contrastive data -> full -> merge -> SelfAware eval + calibration_gap + behavior gate vs clean-SFT base and v3.
### 015-result - Amendment K contrastive-SFT: CALIBRATION GATE PASSES, BEHAVIOR GATE FAILS 3/4 -> cell REJECTED, fallback justified

- at: `2026-06-27T20:30:00Z`
- kind: `result`
- summary: Full contrastive schema-SFT (seed1, 4B) trained to completion (resumed from checkpoint-2000 after a transient external CUDA OOM at step 2205; recipe identical to clean-SFT), merged 16-bit, evaluated on SelfAware (3369 rows, exit 0). Apples-to-apples vs clean-SFT base + GRPO-v3 (same base family, prompt, gold, generation). The §4.1 CALIBRATION GATE PASSES ALL FOUR -- the FIRST time in the entire calibration-gap thread that behavior-conditional response confidence was actually installed: emitted AUROC->appropriateness 0.684 (gate >=0.62; clean-SFT/v3 ~0.52); emitted std 0.309 (gate >=0.10; clean-SFT 0.047, v3 0.027); ECE-vs-appropriateness 0.183 (gate <0.30; clean-SFT/v3 0.40-0.44); behavior-conditional cell means both hold: known_correct_answered 0.670 > known_answered_wrong 0.306, AND unknown_refused 0.581 > unknown_answered_wrong 0.156. Bonus: AUROC correct-vs-wrong among answered-known 0.789 (v3 reached only 0.600). The fully-trained run BEAT the 0018 half-trained ckpt-1500 existence proof. BUT the §4.2 BEHAVIOR GATE FAILS 3 of 4: truthful 30.93 (gate >=35.6 X), correct_on_known 36.63 (gate >=42.2 X), over_refusal 79.2 (gate <=67.5 X), refusal_recall 83.72 (gate >=82.0 OK). This is precisely the §3.2 PRIMARY RISK materializing: completion_only_loss masks the prompt but not the answer sub-span, so the 14,395 inappropriate rows trained wrong-ANSWER text -> degraded correctness + inflated over-refusal.
- evidence:
  - `experiment/phase1/eval/results_amendment_k_response_confidence_selfaware_contrastive_sft_seed1_merged_full_4b/contrastive_schema_sft_merged_seed1__selfaware/{scored_rows.jsonl,metrics.json,calibration_gap_report.json} (untracked container-owned outputs; report written via in-container run)`
  - `scratch/schema_response_confidence/runs/sft_schema_contrastive_seed1_full/20260627_203232/ (adapter + lineage) ; .../Qwen3-4B-bnb-4bit/merged-16bit (eval base)`
  - configs: `experiment/phase1/grpo/configs/sft_schema_contrastive_response_confidence_seed1_{smoke,full}.yaml ; experiment/phase1/eval/config/eval_amendment_k_response_confidence_selfaware_contrastive_sft_seed1_merged_full_local_4b.yaml`
- decisions:
  - VERDICT (calibrated, no spin): per Amendment K §4.2 the cell `schema_contrastive_sft_seed1` is REJECTED -- behavior gate fails regardless of calibration. RECORD HONESTLY: the cell is not usable as a base.
  - BUT the decision-relevant scientific result stands: the calibration MECHANISM works at the SFT stage. Supervised high/low confidence contrast installs behavior-conditional, appropriateness-tracking confidence that shapes the greedy mode eval reads -- the exact thing five downstream objectives (DPO/KTO/GRPO v1/v2/v3) all failed to do. This validates pursuing the §3.2 documented fallback: probe-scaled appropriate rows + a small (~15%) contrastive low-confidence tail (keep the contrast signal, remove the wrong-answer supervision that broke behavior). The fallback would require a NEW signed amendment (protocol locked).
- next steps:
  - PRESENT to user before pursuing the fallback (governance: fallback = revised amendment + sign-off). Decide: (a) draft Amendment L (probe-scaled + ~15% low tail) for sign-off, or (b) the cleaner mechanistic fix -- answer-sub-span masking in synaptic-tuner (now in-bounds as a generic engine feature) so inappropriate rows supervise ONLY the confidence token, not the wrong answer. Option (b) attacks the §3.2 root cause directly and would generalize the engine.
  - Fold Amendment K result into the PR (branch amendment-j-grpo-v3-proper-scoring / PR #114): Amendment K doc, the 2 SFT YAMLs + eval config, merge helper, calibration_gap_report None-row robustness fix, and this checkpoint. Analysis outputs stay untracked.
### 016-build - Amendment L (answer-sub-span-masked contrastive SFT) DRAFTED + infra implemented & verified, HOLD for sign-off

- at: `2026-06-27T22:00:00Z`
- kind: `build`
- summary: User chose path (b) ("B it is") after the Amendment K result -- fix the §3.2 root cause at the engine instead of diluting via probe-scaling. Traced the masking mechanism: shared/sft_preprocessing.py::materialize_sft_example builds labels=copy(input_ids) and assistant_only masks only the prompt PREFIX, so the entire assistant JSON (incl. the wrong-answer value) is supervised -- the exact §3.2 cause. Implemented a GENERIC, backward-compatible engine feature: per-row sub-span loss masking (loss_mask_spans / row column loss_mask_text). When present, encodes with return_offsets_mapping=True, maps each literal span's char range to overlapping tokens, sets them -100 AFTER prompt/assistant_only masking (only masks MORE); searches only within the supervised region so a refusal phrase echoed in the system prompt cannot shadow the real answer occurrence; loss_mask_mode gains "+subspan_masked"; absent -> byte-identical to before. Builder (build_contrastive_sft_rows) emits loss_mask_text=[answer value] on inappropriate rows ONLY (appropriate/ambiguous fully supervised); new masked dataset file written, K file left pristine.
- evidence:
  - submodule synaptic-tuner @ branch feature/sft-subspan-loss-mask commit 278ddba (shared/sft_preprocessing.py + Trainers/sft/src/preprocessing.py + tests; 13 passed incl. 5 new: answer masked/confidence supervised, no-spans byte-identical, not-found raises, prompt-collision, dataset-column consumed)
  - builder test: experiment/phase1/grpo/tests/test_build_schema_response_confidence_datasets.py (11 passed incl. new loss_mask_text emission test)
  - masked dataset: scratch/schema_response_confidence/qwen3-4b-instruct/sft_response_confidence_train_contrastive_masked.jsonl (29338 rows; 14395 inappropriate ALL carry a well-formed span, appropriate/ambiguous none; masked-minus-column == K content EXACTLY; K file unchanged, content md5 ca1f49 modulo CRLF)
  - real-tokenizer DRY validation (docker, Qwen3-4B fast tokenizer): inappropriate supervised tail = `{"answer": "","response_confidence": <low>}` (answer fully masked, envelope+confidence supervised); appropriate unchanged. All 5 sampled rows correct (one false-FAIL was an escaped-quote artifact in the check string, not the masking).
  - configs: experiment/phase1/grpo/configs/sft_schema_contrastive_masked_response_confidence_seed1_{smoke,full}.yaml; experiment/phase1/eval/config/eval_amendment_l_..._merged_full_local_4b.yaml (RUN_TIMESTAMP placeholder)
  - amendment: experiment/protocol/AMENDMENT-L-answer-subspan-masked-contrastive-sft.md (DRAFT, pending sign-off)
- decisions:
  - Amendment L reuses K's §4.1 calibration gate (expect calibration RETAINED ~K levels; masking removes answer-text gradient, not the confidence contrast) and makes K's §4.2 behavior gate the OBJECTIVE (must PASS). The ONLY differences from K are (a) dataset carries loss_mask_text, (b) engine honors it -> any behavior recovery is attributable to removing wrong-answer supervision.
  - Engine feature kept GENERIC (any project can supervise a sub-span of an assistant turn); not epistemic-specific. Authorized as a generic synaptic-tuner improvement.
- next steps:
  - HOLD for user sign-off on Amendment L (protocol locked -- no training without signature). On sign-off: smoke (max_steps 32) -> verify lineage loss_mask_mode assistant_only+subspan_masked + masked dataset -> full (~2934 steps, --run-timestamp pin) -> merge 16bit -> fill eval RUN_TIMESTAMP -> SelfAware eval + calibration_gap + both gates vs clean-SFT base / v3 / K.
### 017-result - Amendment L RESULT: behavior RECOVERED, calibration LOST -- a clean K<->L dissociation (REJECTED as joint solution)

- at: `2026-06-27T21:00:00Z`
- kind: `result`
- summary: Amendment L full run completed (max_steps 2934, exit 0; OOM-recovered via checkpoint-2000 resume + --run-timestamp 20260627_amendmentL_full), merged 16bit, evaluated on SelfAware (n=3369, live vLLM). RESULT IS THE INVERSE OF K. BEHAVIOR GATE (§4.2, the objective) PASSES ALL 4: truthful 41.59 (>=35.6; K 30.93, base 40.58), correct_on_known 50.06 (>=42.2; K 36.63, base 47.23), over_refusal 62.73 (<=67.5; K 79.2, base 57.51), refusal_recall 93.51 (>=82.0; K 83.72, base 87.02) -- truthful & correct_on_known EXCEED the clean-SFT base. CALIBRATION GATE (§4.1, expected RETAINED) FAILS the discrimination criteria: emitted AUROC->appropriateness 0.552 (<0.62; K 0.684, base ~0.52 -- back to ~chance), unknown_refused mean 0.666 < unknown_answered_wrong 0.696 (INVERTED: more confident answering an unknown wrong than correctly refusing it). Passes the weak criteria only: emitted std 0.180 (>=0.10; has variance, NOT collapsed) and ECE 0.277 (<0.30). known_correct 0.756 > known_wrong 0.742 holds but barely (+0.014 vs K's +0.364). So L emits SPREAD confidence without DISCRIMINATION; K had both.
- evidence:
  - behavior: experiment/phase1/eval/results_amendment_l_response_confidence_selfaware_contrastive_masked_sft_seed1_merged_full_4b/{comparisons/summary_table.csv, contrastive_masked_schema_sft_merged_seed1__selfaware/metrics.json}
  - calibration: experiment/phase1/eval/analysis/calibration_gap_contrastive_masked_sft_seed1.json (governed copy of Analysis A on L scored_rows)
  - model: scratch/schema_response_confidence/runs/sft_schema_contrastive_masked_seed1_full/20260627_amendmentL_full/{final_model (adapter), Qwen3-4B-bnb-4bit/merged-16bit (eval base), training_lineage.json}
  - config_sha 0dd9c8d57e4bed41
- decisions:
  - VERDICT (calibrated, no spin): cell `schema_contrastive_masked_sft_seed1` REJECTED as a JOINT calibration+behavior solution. K = calibration without behavior; L = behavior without calibration. Under this single SFT lever (mask wrong-answer text on inappropriate rows) the two are in TENSION -- you buy one or the other, not both.
  - MECHANISTIC PAYLOAD (decision-relevant): the wrong-answer supervision K used was LOAD-BEARING for the calibration signal, not merely a behavior-breaking side effect. Binding the low-confidence token to the (supervised) wrong-answer act is what made stated confidence track appropriateness; mask the answer and behavior recovers but the confidence token loses its conditioning -> discrimination collapses to baseline. The stated/emitted-confidence layer is now the proven-stubborn one: resisted DPO, KTO, GRPO v1/v2/v3, K, and L.
  - K<->L is a tight controlled dissociation (single-variable: only difference is answer-span masking) -> strong material for Paper 3 (calibration gap). Negatives folded in as robustness/mechanism evidence per user (2026-06-27).
- next steps:
  - OPEN PROBLEM reframed: install stated-confidence DISCRIMINATION without binding it to wrong-answer supervision. Candidate directions (would need a NEW signed amendment): (i) separate confidence head / decoupled confidence channel; (ii) a loss that supervises confidence-vs-appropriateness DIRECTLY rather than confidence-alongside-answer; (iii) probe-distillation (supervise emitted confidence toward the calibrated internal doubt-axis readout, ECE 0.004).
  - DEFER per user north-star focus: more pref-opt variants, GRPO tuning, dose-response, 8B, generalization.
  - Bookkeeping: fold Amendment L (doc + 2 SFT YAMLs + eval config + merge + this result + governed calibration copy) into PR #114 when user asks; submodule feature/sft-subspan-loss-mask @ 278ddba still local/unpushed.
### 018-build - Paper 3 drafted ("Knows but Doesn't Say") + Amendment M drafted (quantile-balanced probe distillation), HOLD for sign-off

- at: `2026-06-27T22:30:00Z`
- kind: `build`
- summary: User directive "outline then write the paper then probe distill". (1) Wrote Paper 3 draft-v0 = experiment/paper/paper3-knows-but-doesnt-say-draft-v0.md: the calibration-gap paper. Four results: R1 the gap (internal probe ~0.997 / ECE 0.004 vs stated AUROC ~0.52 / ECE 0.142; over-refused-known are internally known ~0.25-0.28; survives training); R2 doubt-vs-caution geometry (raw cos -0.83 artifact -> whitened -0.565 -> held-out caution_perp refuse/answer AUROC 0.825 = separable gate; method lesson on raw cosine); R3 asymmetric steerability (caution ablation 0.994->0.030 clean specificity, caution_perp independently load-bearing, L26 generation repair signed+layer-specific, knowledge-axis steer FAILS, cannot induce abstention on unknown); R4 seven training interventions fail + K<->L dissociation localizes mechanism (answer-bound supervision is the calibration carrier). Positioned as empirical realization of Paper 1's coherence axis (possessed vs performed humility). (2) Corrected two paper passages after reading experiment/notes/computed-confidence-alignment-regimen.md: GRPO v3 failure is NOT signal-starvation-only -- preflight verified per-prompt target dynamic range (group std 0.320, calibrated beats flat 4211/4211) yet emitted still collapsed (std 0.027, AUROC 0.522) = cleanest negative; and naive probe-scaled SFT (0.1+0.8p) was ALREADY run and collapsed to single value 0.8765 from 81.79% target imbalance (§004), so the implied next experiment is QUANTILE-BALANCED probe distillation, not naive. (3) Drafted Amendment M = experiment/protocol/AMENDMENT-M-quantile-balanced-probe-distilled-sft.md: cell schema_probe_distilled_sft_seed1, clean-SFT behavior completions with response_confidence = monotone quantile transform of appropriateness_p onto band [0.10,0.90] (per-question grounded AND distribution-balanced -> defeats §004 mode-collapse while preserving discrimination ordering). SFT-only, no masking (no wrong-answer rows), no engine change. Gates: §4.1 calibration WITH discrimination (AUROC>=0.62, cell-means ordered incl. unknown_refused>unknown_wrong which L inverted) + §4.2 behavior (clean-SFT bar). Falsifier: if balanced discriminating target still fails -> bottleneck is channel/loss not target -> motivates confidence-head engine change.
- evidence:
  - paper: experiment/paper/paper3-knows-but-doesnt-say-draft-v0.md (frontmatter numbers-discipline; every claim traced)
  - amendment: experiment/protocol/AMENDMENT-M-quantile-balanced-probe-distilled-sft.md (DRAFT, pending sign-off)
  - corrected-by source: experiment/notes/computed-confidence-alignment-regimen.md (audit §004, §009, §023; preflight GREEN)
- decisions:
  - Paper 3 negatives folded in as robustness/mechanism evidence (user 2026-06-27); single-seed/single-model scope stated up front + Limitations §9.
  - Probe distillation = quantile-balanced (B1-style), NOT naive probe-scaled (A1 already collapsed). Open sign-off decisions: global vs per-stratum quantile (rec: global), band [0.10,0.90] (rec), SFT-only clean completions first (rec) vs add masked-answer inappropriate rows.
- next steps:
  - HOLD for user sign-off on Amendment M (protocol locked). On sign-off: builder quantile target + tests -> CPU preflight (histogram balance + Spearman~1 vs appropriateness_p) -> smoke -> full -> merge -> eval -> both gates. Then re-probe winning arm for internal->stated coherence.
  - Paper 3 draft-v0 ready for user read; bibliography to be compiled (shares Paper 1 refs).
  - Bookkeeping: Paper 3 + Amendment M + L result fold into PR #114 when user asks.
### 019-build - Amendment N: GRPO v3 reward on the Amendment K base (RL on the calibrated base) -- SIGNED + smoke launched

- at: `2026-06-28T00:00:00Z`
- kind: `build`
- summary: Strategic pivot after the K<->L dissociation, driven by user questions ("is this where we bring back dpo/kto/grpo? are we trying too hard for sft" -> "was the underlying SFT trained wrong / have we trained it right enough now where another method might help" -> "why K instead of L"). DIAGNOSIS VERIFIED FROM CONFIGS (not memory): every failed RL run trained on a base whose confidence was already collapsed. grpo_schema_clean_sft_merged_seed1_v3_full.yaml pins model_name -> clean-SFT merged (emitted std 0.047, AUROC 0.52) with beta 0.1 -> GRPO v3 was asked to MANUFACTURE confidence spread against a KL anchor pinned to a flat reference, and (per cp B0 eval line 428) behavior was preserved but calibration stayed collapsed (std 0.027, AUROC 0.522, ECE 0.44). So the v3 negative was a BASE artifact, not a method limit. THE UNTRIED CELL: run the SAME v3 reward on the K base (std 0.309, AUROC 0.684, cells correctly ordered) -- there the KL anchor PRESERVES calibration and the proper-score reward REINFORCES it (both point the same way), while v3's already-dominant behavior term (known_correct +2.0, over_refusal -2.0, ...) repairs K's broken behavior. K not L: K holds the RL-impossible half (calibration), L holds the RL-easy half (behavior) and its unknown cells are INVERTED -- anchoring RL to L would defend the wrong ordering and ask RL for the thing it has failed at 5x. NO NEW CODE: humility_reward_v3.py reused unchanged; the two GRPO configs are byte-identical to Amendment J except model_name (-> K merged base) + output_dir -> cleanest possible single-variable test of the diagnosis. Wrote + SIGNED Amendment N (user "get this running I think it's worth a shot"), wrote smoke/full configs + eval config, launched the smoke.
- evidence:
  - amendment: experiment/protocol/AMENDMENT-N-grpo-v3-on-contrastive-sft-base.md (SIGNED 2026-06-28)
  - configs: experiment/phase1/grpo/configs/grpo_schema_contrastive_sft_merged_seed1_v3_{smoke,full}.yaml (clones of J; only model_name + output_dir changed)
  - eval: experiment/phase1/eval/config/eval_amendment_n_response_confidence_selfaware_grpo_on_contrastive_sft_seed1_full_local_4b.yaml (corrected-base pattern: GRPO LoRA on K merged base; adapter RUN_TIMESTAMP to fill post-run)
  - K base (read-only GRPO start): scratch/schema_response_confidence/runs/sft_schema_contrastive_seed1_full/20260627_203232/Qwen3-4B-bnb-4bit/merged-16bit
  - smoke container: eh-grpo-on-k-smoke (max_steps 12, GRPO_REWARD_DEBUG_PATH -> scratch/schema_response_confidence/runs/grpo_on_k_smoke_debug.jsonl); runs/ is 777 so the container creates+owns the output dir (no pre-create/chmod -- pre-creating as host uid 1000 is what caused the v3 PermissionError)
- decisions:
  - GRPO chosen over DPO/KTO for the FIRST shot (not all three): K's behavior is badly broken (heavy lift -> online RL pushes harder than offline preference pairs); v3's reward shaping lets the proper-score term explicitly protect calibration (DPO/KTO only get implicit pair signal + KL); and re-basing the exact v3 run is the cleanest test of the base-was-the-cause diagnosis. DPO/KTO held in reserve if smoke shows calibration holds but behavior won't move.
  - beta is the key knob with a real tension: KL-to-K protects calibration (wanted) AND resists moving off K's broken behavior (unwanted). First shot beta 0.1 (J value): soft enough for behavior reward magnitude 2.0 to move behavior, still anchors confidence to K's discriminating reference. beta + v3 reward magnitudes are authorized tuning knobs WITHIN Amendment N (no new signature), each logged here.
  - Amendment M moved to ON HOLD / fallback (not withdrawn): M tried one SFT for both halves; K already did the calibration half, so GRPO-on-K is the more direct route to coherence. M revives only if N's falsifier triggers.
- next steps:
  - SMOKE GATE (cheap go/no-go): from grpo_on_k_smoke_debug.jsonl over 12 steps -- emitted response_confidence std does NOT collapse off K's ~0.31 (heuristic > ~0.10, not trending to a constant) AND behavior reward live. If std collapses on K too -> that's the FALSIFIER arriving cheaply (channel collapse is intrinsic, not base) -> stop, redirect to confidence-head engine change.
  - On smoke PASS: launch full (1 epoch ~1861 steps, --run-timestamp pin, OOM-resume contingency) -> eval GRPO adapter on K base via vLLM -> calibration_gap_report -> §4.2 gates (calibration RETAIN: AUROC>=0.62/std>=0.10/ECE<0.30/cells ordered; behavior REPAIR: truthful>=35.6/correct_on_known>=42.2/over_refusal<=67.5/refusal_recall>=82.0). SUCCESS = first coherent-humility cell -> re-probe L35 for internal->stated coherence -> Paper 3 headline.
  - Bookkeeping: Amendment N (doc + 2 GRPO configs + eval config + this result) on branch amendment-n-grpo-on-k-base; fold into PR #114 when user asks.
### 020-result - Amendment N GRPO-on-K eval: calibration RETAINED, behavior NOT repaired (sampled-vs-greedy gap) -> beta 0.05 re-run

- at: `2026-06-28T15:00:00Z`
- kind: `result`
- summary: Full GRPO-v3-on-K run (1861 steps, ~8h55m, adapter 20260628_093753/final_model) evaluated on SelfAware OOD (greedy, temp 0) and gated against Amendment N §4.2. VERDICT = PARTIAL (§4.3): Calibration RETAIN PASS 4/4, Behavior REPAIR FAIL 2/4, falsifier NOT triggered. Calibration: AUROC emitted->appropriateness 0.646 (>=0.62), std 0.311 (>=0.10), ECE 0.214 (<0.30), cell-means cleanly monotone incl. unknown_refused 0.542 > unknown_wrong 0.138 (the exact ordering L INVERTED is now strongly correct), known_correct 0.724 highest. Calibration survived the policy moving well off K (training KL ~0.97) -> the base-was-the-cause diagnosis CONFIRMED for the calibration half: K is the correct calibration substrate and GRPO retains+sharpens it. Behavior: truthful 31.91 (<35.6 FAIL), correct_on_known 50.46 (>=42.2 PASS, +14 over K), over_refusal 90.76 (>67.5 FAIL, WORSE than K's 79.2), refusal_recall 93.6 (PASS). 
- root-cause (GROUNDED in reward debug, not inferred): analyzed scratch/.../grpo_on_k_full_debug.jsonl (1861 events, 59552 rows). Ruled OUT the invalid-JSON hypothesis (valid_json 94-97% for BOTH answer and refuse at temp 1.35). The driver is a SAMPLED-vs-GREEDY gap: during training the reward worked as designed -- known->answer mean reward +0.46 vs known->refuse -1.28; unknown->refuse +2.10 vs unknown->answer +0.42 -- and rollouts ANSWERED knowns ~75% (24016 answer / 7908 refuse). But greedy eval refuses knowns 91% (answered 216/2337). The reward lifted answer-probability MASS but the KL anchor to K (beta 0.1) held the ARGMAX at K's over-refusing mode. Behavior reward is not too weak; the greedy decode hasn't followed it.
- evidence:
  - metrics: experiment/phase1/eval/results_amendment_n_response_confidence_selfaware_grpo_on_contrastive_sft_seed1_full_4b/grpo_v3_on_contrastive_sft_seed1__selfaware/metrics.json
  - calibration_gap_report: per-cell emitted means (run on the scored_rows.jsonl, 3369 rows)
  - reward debug analysis: scratch/schema_response_confidence/runs/grpo_on_k_full_debug.jsonl (action x label valid_json% + mean_reward, full + last-15%)
  - amendment RESULT: experiment/protocol/AMENDMENT-N-grpo-v3-on-contrastive-sft-base.md §7
- decisions:
  - Disposition = §4.3 PARTIAL exactly as pre-stated ("calibration retained, behavior misses one gate -> tune beta within §3.3 and re-run"). NO goalpost move: re-run uses the SAME §4.2 dual gate.
  - Re-run knob = beta 0.1 -> 0.05, SINGLE variable, reward UNCHANGED. Rationale: the debug shows reward magnitudes are ALREADY correctly shaped (rollouts answer knowns 75%), so the bottleneck is the KL anchor pinning the greedy argmax to K's refusal mode, not reward weights. Lowering beta is the grounded lever for the sampled-vs-greedy gap AND least risks the calibration we must RETAIN (touching confidence_weight/behavior magnitudes would jeopardize the PASS). This is tier-3 authorized-knob tuning under Amendment N §3.3 (beta explicitly authorized) -- NOT a new amendment (same mechanism, same cell).
  - Did NOT need humility_reward_v3.py edits: beta is a YAML knob, so "reward UNCHANGED" stays literally true. (Considered + rejected an env-var override of RewardConfigV3 -- unnecessary for a beta-only change.)
- next steps:
  - Launch config experiment/phase1/grpo/configs/grpo_schema_contrastive_sft_merged_seed1_v3_beta005_full.yaml (clone of full; ONLY beta 0.05 + output_dir schema_contrastive_sft_grpo_v3_beta005_seed1_full). Full run ~9h, --run-timestamp pin, GRPO_REWARD_DEBUG_PATH -> grpo_on_k_beta005_full_debug.jsonl, runs/ 777 so container owns output dir (no pre-create).
  - On completion: clone the N eval config (adapter -> new timestamp, results_dir _beta005), eval greedy on K base, calibration_gap_report + behavior gate. SUCCESS = first coherent-humility cell -> re-probe L35 internal->stated coherence -> Paper 3 headline. If beta 0.05 still leaves greedy anchored -> gap is intrinsic to argmax-vs-expectation decode (a real finding) -> decode/objective change, not more beta steps.
  - Bookkeeping: Amendment N result + beta005 config fold into PR #114 when user asks (branch amendment-n-grpo-on-k-base / current amendment-j-grpo-v3-proper-scoring).
### 021-result - Temp-1.35 diagnostic eval (user-requested): behavior does NOT repair at training temp -> falsifies decode-artifact hypothesis, reveals knowledge-INDEPENDENT action

- at: `2026-06-28T20:30:00Z`
- kind: `result`
- summary: User insight "we should try the eval at temp 1.35 that we trained it at" -> tier-3 DIAGNOSTIC (reported separately; does NOT relabel the locked greedy §4.2 gate). Config eval_amendment_n_diag_temp135_... (clone of N eval; ONLY temperature 0.0->1.35 + results_dir). Same adapter (20260628_093753/final_model) on K base, SelfAware OOD, n=1. RESULT = behavior does NOT repair; it flips to the OPPOSITE failure. over_refusal 90.76->6.25 (answers knowns now), BUT refusal_recall 93.6->12.79 (answers 87% of UNKNOWNS), correct_on_known 50.46->12.09 (accuracy collapses at high temp), truthful 31.91->11.78. Calibration ALSO degrades: AUROC 0.646->0.559, ECE 0.214->0.322 (now FAILS <0.30), cell ordering BROKEN (known_refused 0.691 highest, should be low).
- interpretation: temperature slides a SINGLE knowledge-INDEPENDENT refuse-propensity knob: greedy=refuse-all (over_refusal 91%), temp1.35=answer-all (refusal 8%). At NEITHER point does the action discriminate known/unknown -- the conditioning margin is tiny at both ends (knowns answered only ~3-6pt more than unknowns: greedy 9.2% vs 6.4%; temp1.35 93.75% vs 87.21%), swamped by global bias. THE FINDING: GRPO-on-K produced calibrated CONFIDENCE without calibrated ACTION -- internal knowledge reached the emitted confidence scalar (calibration retained, cells ordered) but NOT the answer/abstain decision. "Knows but doesn't say" extended one layer: says (confidence tracks knowledge) but doesn't act (refuse decision doesn't).
- decisions:
  - H_decode (conditioning exists, greedy decode hides it) = FALSIFIED: freeing decode via temperature gives answer-all, not discrimination. Temperature is eval-time re-sampling of a FIXED policy; it cannot INSTALL conditioning.
  - H_train_KL (KL-to-K pinned the ACTION during training; softer beta gives the gradient room to install knowledge-conditioned action) = STILL LIVE. Only a re-train tests it; temp eval cannot. So the temp-1.35 diagnostic does NOT kill the beta=0.05 re-run -- it sharpens its rationale (training-time KL room, not decode) and gives it an explicit falsifier.
  - PRE-STATED FALSIFIER for the beta=0.05 re-run: if it STILL shows no answer-rate margin between knowns and unknowns (action stays a global propensity knob), the action-conditioning failure is STRUCTURAL, not a KL artifact -> that is the publishable finding ("calibrated confidence, uncalibrated action") -> STOP tuning beta, write it up. No further beta steps.
- evidence:
  - metrics: experiment/phase1/eval/results_amendment_n_diag_temp135_selfaware_grpo_on_contrastive_sft_seed1_full_4b/grpo_v3_on_contrastive_sft_seed1__selfaware/metrics.json
  - calibration_gap_report on that scored_rows.jsonl (AUROC 0.559, std 0.269, ECE 0.322, cells broken)
  - reconciliation with reward debug: rollout "answers knowns 75%" was MISLEADING -- it also answered unknowns ~67% (unknown_answer net reward +0.42, positive despite -1.2 penalty, offset by proper-score+JSON terms), and high-temp answers are low quality -> answer-all, not discrimination.
- next steps:
  - AWAIT user go (9h compute) on beta=0.05 re-run (config grpo_schema_contrastive_sft_merged_seed1_v3_beta005_full.yaml, staged, NOT launched). On launch: --run-timestamp pin, GRPO_REWARD_DEBUG_PATH grpo_on_k_beta005_full_debug.jsonl. On completion: GREEDY §4.2 gate (locked comparison) + check the pre-stated falsifier (known vs unknown answer-rate margin from both eval and reward debug).
  - If beta=0.05 falsifier triggers -> pivot to writing up "calibrated confidence, uncalibrated action" as a Paper 3 result (extends knows-but-doesnt-say to the action layer); revisit confidence-head / action-supervision routes under a NEW amendment.
### 022-build - Action-conditioning analysis (CPU, while beta005 trains): quantifies "calibrated confidence, uncalibrated action" + pre-registers the re-run falsifier metric

- at: `2026-06-28T21:30:00Z`
- kind: `build`
- summary: Built reusable experiment/phase1/eval/analysis/action_conditioning_report.py (stdlib-only: manual Mann-Whitney AUROC + two-proportion z-test + training-trajectory binning) to quantify whether the answer/abstain ACTION tracks knowledge, and to compute the Amendment N re-run FALSIFIER deterministically. Ran on greedy N, temp-1.35 N, and the beta-0.1 reward-debug trajectory (existing artifacts; no GPU). Also pre-filled the beta005 greedy eval config (adapter pinned to run ts 20260628_204936/final_model) for instant post-run turnaround.
- findings (the quantitative backbone of the cp021 finding):
  - GREEDY (temp 0): ACTION margin P(ans|known) 9.24% vs P(ans|unknown) 6.40% = +2.85pt (z=2.75, p=0.006 -- statistically real but PRACTICALLY NEGLIGIBLE). CONFIDENCE channel DISCRIMINATES: refusal-appropriateness AUROC 0.620 (separates mistaken known-refused conf-mean 0.412 from correct unknown-refused 0.542), answer-correctness AUROC 0.837 (correct 0.724 vs wrong 0.315). => confidence channel AUROC 0.62-0.84 vs action margin 2.85pt: the model HAS the knowledge and routes it to the SCALAR but not to the DECISION. The action is ~97% global propensity, ~3% knowledge.
  - TEMP 1.35: ACTION margin +6.54pt (93.75% vs 87.21%, z=6.36) -- still tiny vs the ~90% global answer rate. CONFIDENCE channel BREAKS at high temp: refusal-appropriateness AUROC 0.335 (INVERTED -- more confident on mistaken refusals), answer-correctness AUROC 0.586 (near chance). So high temp destroys the one channel that worked.
  - TRAINING TRAJECTORY (beta 0.1, 1861 steps, 6 bins): action margin started +2.5pt and plateaued at ~+7pt -- NEVER opened. The policy answered BOTH knowns (~74-77%) and unknowns (~66-74%) throughout; the strong reward differential (known-refuse -1.28 vs unknown-refuse +2.10) moved the GLOBAL answer rate, not the conditioning. Across the whole run the action never learned to gate on knowledge.
- decisions:
  - PRE-REGISTERED quantitative falsifier for beta005 (derived from the locked §4.2 behavior gate, NOT post-hoc): a behavior PASS requires answer_rate_known >= ~32.5% (over_refusal <=67.5) AND answer_rate_unknown <= ~18% (refusal_recall >=82) => action margin >= ~14.5pt with absolute rates inside the gate box. FALSIFIER: if beta005 greedy action margin stays < ~10pt OR the absolute rates miss the box, the action-conditioning failure is STRUCTURAL (not a KL artifact) -> STOP tuning beta -> write up "calibrated confidence, uncalibrated action" as a Paper 3 result.
  - Prior on beta005 LOWERED by the trajectory evidence (margin plateaued at beta 0.1 across all 1861 steps), but the run is still warranted: beta is the one untested training-time lever and lower KL is the only thing that could let the gradient open the margin. Run it, apply the pre-registered falsifier, do not add further beta steps if it triggers.
  - action_conditioning_report.py is a reusable eval-analysis tool (belongs in experiment/phase1/eval/analysis/, alongside calibration_gap_report.py); it is experiment analysis, not skill orchestration, so it stays in the experiment tree.
- evidence:
  - script: experiment/phase1/eval/analysis/action_conditioning_report.py
  - greedy + temp1.35 scored_rows (Amendment N results dirs); trajectory from scratch/schema_response_confidence/runs/grpo_on_k_full_debug.jsonl
  - pre-filled eval: experiment/phase1/eval/config/eval_amendment_n_beta005_selfaware_grpo_on_contrastive_sft_seed1_full_local_4b.yaml (greedy, adapter ts 20260628_204936)
- next steps:
  - On beta005 completion (~06:50): run the pre-filled greedy eval -> calibration_gap_report + action_conditioning_report -> §4.2 gate + the pre-registered margin falsifier. Report verdict.
  - If falsifier triggers -> Paper 3 result section "calibrated confidence, uncalibrated action" (greedy + temp1.35 + trajectory already support it); revisit action-supervision / confidence-head under a NEW amendment.
  - Bookkeeping (await user go): commit Amendment N (doc+§7), beta005 + temp135 + beta005-eval configs, action_conditioning_report.py, cps 020/021/022, and the earlier skill-governance update; fold into PR #114.
