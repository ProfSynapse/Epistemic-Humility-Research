---
title: known-unknown-axis-does-not-carry-answer-correctness-at-deployment
aliases:
- The known-unknown axis does not carry answer correctness at deployment
- Paper-3 discrimination claim falsified at the axis level (wrong-answer-cell-power-fix)
- M7 comparator drop is power and render-surface confounded
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:known-unknown-axis-does-not-carry-answer-correctness-at-deployment
  type: mechanism
  status: canonical
cause: "In the wrong-answer-cell-power-fix experiment, the known-unknown axis (frozen L35 construction, refit fold-wise within each of 5 stratified folds to remove anchor overlap with the known_correct_answered cell) was used to rank the Qwen3-4B clean-SFT+GRPO-v2 checkpoint's own correct versus wrong answers on 360 deployment-rendered wrong / 420 correct answered-known SelfAware rows, a 24-fold increase in the wrong-row count over the paper's original n=16, against a registered floor of internal refit AUROC at least 0.60 with CI lower bound above 0.55 (E1) and a gap over the emitted response_confidence channel of at least +0.05 with paired CI excluding 0 (E2)."
effect: "The internal refit readout reaches AUROC 0.5597 (CI 0.5185-0.5993), below the 0.60 floor, and its gap over the emitted channel (AUROC 0.5207) is +0.0390 with CI (-0.0163, 0.0942), including 0 and below the +0.05 floor. Both primary falsifier conditions fire (E1 and E2 FAIL), overturning manuscript.md:336-337's discrimination claim at the axis level. A red-team pass independently reproduced every reported number from the safetensors and found the null is not instrument-induced: the paper's own in-sample axis construction reaches only 0.5680 on this population, the band maximum across L30-L36 (at L34) is 0.5718, alternative axis families reach 0.5636, and seven CV seeds span 0.5567-0.5632, so the anti-leakage refit itself costs about 0.008 AUROC, far short of the 0.09 needed to clear the floor. Critically, an unregistered, ungated full-dimension context probe fit on the same pre-generation vectors and rows reaches AUROC 0.6769 (grpov2 checkpoint) and 0.6995 (clean-SFT control checkpoint), so correct-versus-wrong answer correctness IS linearly decodable from the pre-generation residual stream at this position. The finding is scoped accordingly: the known-unknown axis specifically does not carry that signal at deployment rendering; it is never read as evidence that no internal correctness signal exists. The M7 comparator drop against the historical frozen-manifest reading (AUROC 0.649, measured under a different, neutral-prompt render on a 95.9-percent-correct population) is power- and render-surface-confounded and is never differenced against the deployment-render number without that caveat. Separately and by contrast, the raw internal-versus-emitted calibration gap (A7) survives decisively and widens under power (raw A7 +0.2373, CI 0.1853-0.2769) rather than eroding; the base-rate-reweighted accounting of the same gap is arithmetically degenerate (reweighting labels to the paper's 0.959 base rate without recalibrating collapses ECE to the distance of the mean prediction from 0.959, so its sign flip carries no calibration content and does not contest the raw result)."
polarity: decouples
related:
- '[[wrong-answer-cell-power-fix]]'
- '[[internal-paper3--knows-but-doesnt-say]]'
- '[[known-unknown-direction]]'
- '[[selfaware]]'
- '[[auroc]]'
- '[[expected-calibration-error]]'
- '[[verbalized-confidence-channel-bottleneck]]'
relationships:
- type: supported_by
  target: '[[wrong-answer-cell-power-fix]]'
  target_id: experiment:wrong-answer-cell-power-fix
  confidence: high
  evidence:
  - experiments/wrong-answer-cell-power-fix/experiment.yaml (verdict field)
  - experiments/wrong-answer-cell-power-fix/analysis-committed/real_run_results.md
    (grpov2 -- L35 primary gate table, E gate table)
  - experiments/wrong-answer-cell-power-fix/NOTEBOOK.md (2026-08-08 ~23:40Z entry,
    run-complete + red-team adjudication)
- type: related_to
  target: '[[internal-paper3--knows-but-doesnt-say]]'
  target_id: paper:internal-paper3
  confidence: high
  evidence:
  - papers/paper-3-knows-but-doesnt-say/manuscript.md:336-337 (the discrimination
    sentence this narrows at the axis level)
- type: related_to
  target: '[[known-unknown-direction]]'
  target_id: term:known-unknown-direction
  confidence: high
  evidence:
  - "experiments/wrong-answer-cell-power-fix/AMENDMENT.md (section 2.5, Internal
    readout: refit, not cold transport)"
- type: related_to
  target: '[[selfaware]]'
  target_id: dataset:selfaware
  confidence: high
  evidence:
  - "experiments/wrong-answer-cell-power-fix/AMENDMENT.md (section 2.3, Arm A
    population: all 3369 SelfAware rows)"
- type: related_to
  target: '[[auroc]]'
  target_id: metric:auroc
  confidence: high
- type: related_to
  target: '[[expected-calibration-error]]'
  target_id: metric:expected-calibration-error
  confidence: high
- type: related_to
  target: '[[verbalized-confidence-channel-bottleneck]]'
  target_id: mechanism:verbalized-confidence-channel-bottleneck
  confidence: medium
  evidence:
  - papers/paper-3-knows-but-doesnt-say/manuscript.md:314,330-331 (the M1-M5
    internal-vs-stated numbers this experiment re-estimates at power)
---

At paper-3's original power (n=16 wrong-answered rows), the known-unknown axis
appeared to discriminate the model's own correct from wrong answers better
than its emitted confidence did. Re-estimated on 360 wrong rows (24 times the
original count), that discrimination claim does not survive: the axis's
fold-wise refit AUROC lands at 0.5597, essentially chance, and its gap over
the emitted channel is statistically indistinguishable from zero. A red-team
pass ruled out instrument artifacts by reproducing every number independently
and by showing that no alternative axis construction, layer, or CV seed
within the registered band clears the floor either.

The finding is narrower than "no internal correctness signal exists." A
full-dimension probe on the identical pre-generation vectors reaches AUROC
0.68-0.70, so the residual stream does linearly encode which answers will
turn out correct; the known-unknown axis, built to separate known from
unknown questions, simply does not carry that separate correctness signal at
deployment. The two things paper 3 had been reading through one axis, whether
the model knows the answer and whether the answer it gives will be right,
come apart once the wrong-answer population is powered enough to tell them
apart.

**Why it matters here:** the calibration half of paper 3's contrast is not
touched by this. The raw gap between the axis's internal ECE and the model's
emitted ECE grows wider at power (raw A7 +0.2373, CI excluding 0), so the
stated-confidence channel is, if anything, more decoupled from reality than
the small-n estimate suggested; only the base-rate-reweighted accounting of
that same gap degenerates for arithmetic reasons unrelated to discrimination.

**Lineage:** re-estimates the internal-vs-stated numbers in
[[internal-paper3--knows-but-doesnt-say]] (manuscript.md:314, :315-316,
:330-331, :336-337, Figure 1) that previously rested on n=16 wrong rows.
Instrument is the fold-wise refit of [[known-unknown-direction]] over
[[selfaware]] SelfAware rows. Source of truth:
`experiments/wrong-answer-cell-power-fix/AMENDMENT.md`,
`experiments/wrong-answer-cell-power-fix/analysis-committed/real_run_results.md`,
resolved 2026-08-09 (falsified, PI approved).
