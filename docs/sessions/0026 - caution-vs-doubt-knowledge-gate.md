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
  - Smoke->full gate PASSED; launched the full B0 run (container phase3-grpo-v3-full, config grpo_schema_clean_sft_merged_seed1_v3_full.yaml, 1 epoch ~465 steps over 14888 examples, reward-debug to schema_clean_sft_grpo_v3_seed1_full.jsonl). v2 cell outputs untouched (distinct run dir).
- next steps:
  - On full completion: merge adapter, run the Amendment E/F SelfAware eval, then calibration_gap_report.py on B0 scored_rows for the apples-to-apples table vs v2 (target: emitted std up from 0.013, ECE-vs-appropriateness down from 0.403, AUROC->known/appropriateness up toward internal 0.97, Spearman(internal,emitted) up); re-probe L35 doubt-axis coherence.
