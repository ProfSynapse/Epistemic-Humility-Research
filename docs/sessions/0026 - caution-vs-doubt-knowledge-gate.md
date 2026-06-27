---
schema_version: research-session/v1
session_id: '0026'
title: caution-vs-doubt-knowledge-gate
status: active
created_at: '2026-06-27T09:37:23Z'
updated_at: '2026-06-27T10:11:42Z'
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
