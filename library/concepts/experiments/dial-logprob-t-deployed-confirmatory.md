---
title: dial-logprob-t-deployed-confirmatory
aliases:
- 'Dial vs token-logprob on the deployed checkpoint: gated confirmation at adequate
  power'
- LP-T, the T-arm gated confirmation cell
tags:
- kg/experiment
- experiment
- correctness-dial
kg:
  id: experiment:dial-logprob-t-deployed-confirmatory
  type: experiment
  status: canonical
related:
- '[[dial-logprob-baseline-v3]]'
- '[[dial-logprob-baseline]]'
- '[[dial-logprob-baseline-v2]]'
- '[[per-answer-correctness-linearly-readable-post-generation]]'
- '[[sequence-probability]]'
- '[[qwen3-4b-dial-margin-over-logprob-large-on-deployed-checkpoint]]'
- '[[dial-margin-over-logprob-is-checkpoint-dependent]]'
relationships:
- type: builds_on
  target: '[[dial-logprob-baseline-v3]]'
  target_id: experiment:dial-logprob-baseline-v3
  confidence: high
  evidence:
  - experiments/dial-logprob-t-deployed-confirmatory/AMENDMENT.md (Design;
    "Verbatim reuse of the v3 instrument, single arm" -- same single-pass
    vLLM 0.27.1 generation, teacher-forced HF extraction, source scorers,
    OOF dial refit, and paired bootstrap; v3's T arm stopped at a
    data-stage power-floor short-fall (710/1000 answered) that this cell
    resolves by raising the registered attempt cap)
- type: related_to
  target: '[[dial-logprob-baseline]]'
  target_id: experiment:dial-logprob-baseline
  confidence: medium
  evidence:
  - experiments/dial-logprob-t-deployed-confirmatory/AMENDMENT.md
    (Motivation; v1's descriptive T read, +0.158 with the round-trip
    caveat, is superseded by this cell's gated number)
- type: related_to
  target: '[[dial-logprob-baseline-v2]]'
  target_id: experiment:dial-logprob-baseline-v2
  confidence: medium
  evidence:
  - experiments/dial-logprob-t-deployed-confirmatory/AMENDMENT.md
    (Motivation; v2's unblinded stopped-cell T margin, +0.1747 CI [0.140,
    0.211], is superseded by this cell's gated number)
- type: related_to
  target: '[[per-answer-correctness-linearly-readable-post-generation]]'
  target_id: mechanism:per-answer-correctness-linearly-readable-post-generation
  confidence: high
  evidence:
  - experiments/dial-logprob-t-deployed-confirmatory/AMENDMENT.md (Design;
    dial is the T-cell's own out-of-fold post-generation correctness
    probe, layer L22, deployed abstention-trained checkpoint)
- type: related_to
  target: '[[sequence-probability]]'
  target_id: term:sequence-probability
  confidence: high
  evidence:
  - experiments/dial-logprob-t-deployed-confirmatory/AMENDMENT.md (Design;
    comparison is dial OOF AUROC vs primary length-normalized mean
    answer-span logprob AUROC)
- type: supports
  target: '[[qwen3-4b-dial-margin-over-logprob-large-on-deployed-checkpoint]]'
  target_id: mechanism:qwen3-4b-dial-margin-over-logprob-large-on-deployed-checkpoint
  confidence: high
  evidence:
  - experiments/dial-logprob-t-deployed-confirmatory/AMENDMENT.md#outcome
    (LT-G1 PASS; dial AUROC 0.7962 vs primary mean_answer_span logprob
    AUROC 0.6569, margin +0.1393, paired bootstrap 95% CI [0.1031,
    0.1755])
- type: supports
  target: '[[dial-margin-over-logprob-is-checkpoint-dependent]]'
  target_id: mechanism:dial-margin-over-logprob-is-checkpoint-dependent
  confidence: high
  evidence:
  - experiments/dial-logprob-t-deployed-confirmatory/AMENDMENT.md#outcome
    (paired with v3's S-arm result, raw base margin +0.0118 ambiguous
    band, the program-level shape is that the dial's margin over the
    model's own answer-span logprob is checkpoint dependent -- negligible
    on the raw base, large and now gated on the deployed abstention-trained
    checkpoint)
---

Fourth cell of the dial-token-logprob-baseline lineage, and the first to
gate the T-side (deployed-checkpoint) comparison at adequate power. v1 and
v2 never computed a gated T-arm number (integrity/reproduction stops); v3
reused v1/v2's populations under a fresh self-consistent single-pass
capture but its T arm itself data-stage-stopped at 710/1000 answered rows,
inherited from a 4,000-attempt cap sized for the S arm. This cell is a
verbatim reuse of the v3 instrument on a single arm (the deployed
abstention-trained checkpoint, T side), with the attempt cap raised to
12,000 (power arithmetic pre-stated from v3's observed 17.75% answer rate)
so the LT-G0 power floor is reachable.

Resolved 2026-08-13 (local RTX 3090, single launch, vLLM 0.27.1 pinned
stack).

**LT-G0 PASS on all four conditions.** Capture integrity: 0 divergences
across all extracted rows (the v3 single-capture posture held). Coverage:
8,621 attempted, 8,621 distinct dispositions (the registered
`select_attempted` stopping rule reached its correct/wrong balance targets
inside the 12,000 cap; cap not extended). Power floor: 1,501 answered rows
(>= the 1,000 floor; answer rate ~17.4%, consistent with v3's ~17.75% on
the same checkpoint/pool convention). Instrument sanity: fresh T dial OOF
AUROC 0.7962 (>= the 0.75 bound).

**LT-G1 PASS.** Dial AUROC 0.7962 vs primary (mean_answer_span) logprob
AUROC 0.6569: margin **+0.1393, paired bootstrap 95% CI [0.1031, 0.1755]**
(n_boot 2000, seed 20260813). The +0.05 floor is cleared and the CI
excludes zero; neither falsifier fires; the ambiguous band does not apply.
The registered prediction (clearly positive, near +0.15) landed as stated.
Descriptive-only secondary variants: sum_answer_span AUROC 0.7706,
min_answer_span AUROC 0.7536 (both n=1501, not gated) -- the sum variant
runs much closer to the dial than the mean variant does.

This cell supersedes the two non-citable descriptive T reads in the
lineage (v1's +0.158 with the round-trip caveat; v2's unblinded stopped-cell
+0.1747) as the sole citable deployed-checkpoint number. Paired with v3's
S-arm result (raw base margin +0.0118, ambiguous band), the program-level
shape is checkpoint-dependence: see
[[dial-margin-over-logprob-is-checkpoint-dependent]].

**One-sentence verdict:** on the deployed abstention-trained checkpoint,
the dial beats the model's own answer-span logprob by a gated margin of
+0.1393 (95% CI [0.1031, 0.1755], n=1,501), passing LT-G1 at adequate
power.

**Lineage:** builds on [[dial-logprob-baseline-v3]] (instrument reuse),
supersedes descriptive T reads from [[dial-logprob-baseline]] (v1) and
[[dial-logprob-baseline-v2]] (v2). Source of truth:
`experiments/dial-logprob-t-deployed-confirmatory/AMENDMENT.md`, Outcome
section, resolved 2026-08-13.
