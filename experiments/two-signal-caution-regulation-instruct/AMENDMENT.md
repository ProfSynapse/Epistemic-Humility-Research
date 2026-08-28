# two-signal-caution-regulation-instruct

Status: draft (not signed; do not launch as confirmatory evidence).

Keep this document the prose home for the experiment. The machine state lives in
`experiment.yaml` and is never duplicated here.

## Motivation and posture

Actuation has been demonstrated on exactly one checkpoint. Amendment AC coupled a
doubt readout to a caution setpoint on the Qwen3-4B clean-SFT->GRPO-v2 seed1
checkpoint and moved behavior (+8.7pt, CI [+5.6, +12.0]). On the AI-TRUE
checkpoint the caution lever is dead (AN confounded null, AO Stage-1 dead-lever
null: ablating caution left the over-refusal tail at 0.974 despite headroom). So
the question that governs the whole program is now: does inference-time caution
regulation work on an untrained model at all, and can it hit both error tails at
once rather than only tightening?

Two results make the untrained instruct model (raw-base Qwen3-4B, no adapter) the
right substrate and this the right next experiment:

1. The dark-actuator-screen positive control validated a caution lever on
   raw-base: writing the answer-vs-refuse mass-mean direction flipped 79 of 80
   confabulations into coherent "I don't know" refusals with confidence going to
   0.0. The tighten half (confab -> refuse) is therefore already close to proven
   on this substrate.
2. AC's selectivity was one-directional. A caution controller that only tightens
   is a blunt refusal switch. The open and higher-value claim is bidirectional
   selectivity: tighten where the model is confidently wrong (high
   confab-propensity on an unanswerable prompt) and release where it is wrongly
   cautious (a genuinely answerable prompt it refuses). That release half has
   never been shown by any amendment.

Posture: exploratory. This is a new evidence cell with a pre-stated prediction,
falsifier, and gates. It is not a headline surface and its numbers are reported
separately from the locked matrix. Promotion to a claim requires a confirmatory
replication registered before running it.

## Design

Substrate: raw-base untrained instruct, `unsloth/Qwen3-4B` (FULL BF16, no 4-bit
quantization), no adapter (checkpoint_tag "raw-base"). REVISED 2026-07-07 from
`unsloth/Qwen3-4B-bnb-4bit`: this is now the FIRST substrate change in the
program, so every fitted direction (u_d, pos_ctrl, neg_ctrl, c_hat) is refit
fresh on bf16 activations rather than reusing any 4-bit-fit artifact (see
NOTEBOOK.md's bf16 substrate-pivot entry and
`build_two_signal_directions.py`'s own docstring for the full refit
provenance). The AK Stage-1 / AH A0 surface (question pools, row selections,
gold labels) is UNCHANGED; only the activations and the fitted directions are
bf16-native.

Signal: two sensors read per example, both coupled to a single caution setpoint,
mirroring AC's proportional-controller structure but with two inputs instead of
one:
- Doubt readout: drives the release direction. Where the model's internal doubt
  is low on a prompt it nonetheless refuses, the controller reduces caution so a
  correct answer can surface.
- Confab-propensity readout: drives the tighten direction. Where propensity to
  fabricate is high, the controller raises caution so the model refuses instead
  of confabulating.

The two per-example gains combine into one signed caution setpoint written along
the validated caution direction. The exact control law mirrors AC's coupling
faithfully (standardized sensors, gain clip, caution direction orthogonalized to
the sensor axes) so any effect is attributable to per-example targeting, not to a
constant caution shove.

Confirmed ingredients (trajectory-scout, read from governed docs/artifacts on
main):
- Couple math (AC section 2, reused verbatim by AE section 2): read a standardized
  sensor offline before intervention (z_i = (d_i - mu_d) / sigma_d over the row
  population); write during generation with erase-and-write
  h' = h - (h . c_hat) c_hat + g_i * sigma_c * c_hat, gain g_i = -alpha * z_i
  clipped to [-2, +2], alpha = 1, sigma_c = row-population std of the projection
  onto c_hat. The read is one-shot and offline (open loop, no within-item
  feedback). Permuted placebo = same gains, row-shuffled, fixed seed.
- Confab-propensity sensor: the dark-actuator-screen's own neg_ctrl_L34 (fit at
  L16/20/24/28/34 by standardized logistic regression on the AK Stage-1 pool,
  target confab_on_unanswerable) EXISTED as a 4-bit fit
  (experiments/dark-actuator-screen/directions/neg_ctrl_L{16,20,24,28,34}.json)
  but is NOT reused under the bf16 pivot (a 4-bit-fit direction is not
  substrate-portable). This experiment REFITS its own neg_ctrl_L34 fresh on
  bf16 AK Stage-1 activations, verbatim the same method (see
  `analysis-committed/source_directions/neg_ctrl_L34.json` provenance).
- Caution write direction: pos_ctrl_L34 (refuse_vs_confab mass-mean, unit norm,
  decoder block 33 / census L34) is likewise REFIT fresh on bf16 activations
  (not copied from the dark-screen's 4-bit fit; see
  `analysis-committed/source_directions/pos_ctrl_L34.json`). The dark-screen's
  own bf16 characterization of ITS (un-orthogonalized) pos_ctrl_L34 found a
  coherent refusal-shift window at setpoint ~100 (vs the 4-bit substrate's
  ~150-300), ambient projection ~19-27 (comparable across substrates), below
  ~20 inert, at/above ~500 collapse (dark-screen NOTEBOOK, 2026-07-06 bf16
  reference diagnostic). This experiment's OWN fresh 24-row ambient-relative
  dose escalation on the REFIT-and-orthogonalized c_hat_L34 (cos 0.87 with the
  un-orthogonalized caution_dir, not identical) was INITIALLY misread against
  its own printed "strength" column, which is a GAIN fed into the tuner's real
  erase_write hook (sigma_c=21.36) -- the hook writes gain*sigma as the
  realized projection (synaptic-tuner MechInterp/intervention/hooks.py
  docstring lines 7-12), so "strength" undercounts the real write by a
  sigma_c factor. RED-TEAM-CAUGHT AND FIXED (2026-07-07): the sweep now logs
  `hook.last_readback` (the GPU-measured post-write projection) directly. In
  that ground-truth unit, the real window is: median first-coherent-move
  |readback|=531.9 (confab median=456.0, answerable_refused median=546.0,
  n=21 usable of 24), median first-garbage-collapse |readback|=952.0 (confab
  median=808.0, answerable_refused median=997.9), with real per-row
  heterogeneity (one row, `ahx::kuq_ku_unknown_x::000518`, shows a
  non-monotonic garbage flag between readback -374 and -588 that clears again
  at a higher dose before re-collapsing at -800 -- a detector fragility, not a
  real early collapse; not used to set the clip). ALPHA=40.0 / hard clip
  +/-750 (up from the mis-united ALPHA=2.0 / clip 40, an ~20x correction) puts
  this eval pool's own abs_median marginal write at 506 (confab) / 625
  (answerable_refused), inside the confirmed coherent zone and below the
  confirmed median collapse floor (no row in the pool reaches 808, the lower
  of the two cells' collapse medians). See
  `build_two_signal_directions.py`'s own header note and NOTEBOOK.md's bf16
  dose-calibration-fix entry for the full sweep and the units-bug derivation.

The two-sensor gain is the natural extension (nobody has run it):
g_i = -alpha_d * z_d,i + alpha_p * z_p,i (doubt pulls caution down when the model
knows; propensity pushes caution up when fabrication is likely). For AC's "the
write does not disturb the read" guarantee to hold for both sensors, c_hat would
be orthogonalized against BOTH sensor axes (a 2-D erase); this is a genuine design
first. In the open-loop design the read is offline and one-shot, so cross-layer
read/write (below) does not break correctness, only the same-layer
orthogonalization convenience.

Doubt sensor (DECIDED, user 2026-07-06): refit a fresh known-vs-unknown mean-diff
doubt axis at L34 on the AK Stage-1 pool, mirroring AC/AE's method exactly
(u_d = unit(mean(h[known]) - mean(h[unknown])) at L34, standardized over the row
population). This puts the doubt read and the caution write on the same layer, so
AC's 2-D orthogonalization (c_hat orthogonalized against both u_d and u_p) is
well-defined and fidelity to AC is maximal. The alternative (read Amendment W's
L18 gate probe, AUROC 0.997, write at L34) was declined in favor of a same-layer
refit; the refit is one CPU fitting step, free and local. AE tried to fit a base
doubt axis and its adequacy floor STOPPED it at census, but that floor was against
AE's small 300+300 affording-prompt slice (only 21 confabs); on the AK Stage-1 /
AH A0 pool the known and unknown populations are both large enough to fit a stable
mean-diff (556 known / 677 unknown are available in the W extraction on this
substrate, and the AH A0 pool carries 484 answered + 1338 unanswerable rows). The
refit is a committed artifact promoted under analysis-committed/ with its fit
provenance.

Surface: reconstructed from the raw AH A0 raw-base pool so BOTH tails are present,
because AK Stage-1 as published dropped the release tail. Verified counts (AH A0
manifest, raw unsloth/Qwen3-4B, no adapter): unanswerable = 309 confab +
1029 refuse; answerable = 175 answered + 149 refused (a 46% over-refusal rate on
answerable prompts). The tighten tail is the 309 unanswerable confabs (flip to
coherent refuse). The release tail is the 149 answerable refusals (flip to
well-formed correct answer), whose true-positive subset is the low-doubt fraction
the doubt sensor must isolate. This surface is chosen over AE's affording-prompt
census (300+300, only 21 confabs, under AE's 150-row floor); AK Stage-1 and AH A0
are the SAME checkpoint, a larger and both-tailed pool.

Disclosure (red-team, 2026-07-07): the same 309 confab rows are in-sample to BOTH
the pos_ctrl/neg_ctrl direction fit (step 2 of the Design section's "Confirmed
ingredients") AND the G1-tighten eval tail. This is not an outcome leak -- the
grader's correctness/coherence check is independent of the fitting labels,
the permuted-sensor placebo destroys the per-row gain-to-row pairing the fit
itself depended on, and the tighten claim is already near-proven by the
dark-actuator-screen's own held-out positive control (79/80 flips) rather than
resting on this in-sample fit -- but it is disclosed rather than left implicit,
since a reader could otherwise mistake G1-tighten for a held-out test of the
direction fit itself.

Surface containment (2026-07-07, folded in with the bf16 pivot): this repo is
PUBLIC, so no question text or eval-row text is committed (see
`.skills/pr-workflow/SKILL.md` "Datasets are never committed"). The committed
`analysis-committed/eval_pool_manifest.jsonl` carries ID + derived numeric
columns ONLY (row_key, cell, gold_class, projections, gains) -- no `question`,
no `aliases`. The full local eval pool `cell.yaml` actually reads
(`analysis/eval_pool_both_tail.jsonl`, gitignored) is materialized at run time
by `materialize_eval_pool.py`, which joins that manifest against question text
fetched via `hf_hub_download(repo_id="professorsynapse/eh-al-prep-staging",
filename="pools/a0_pool_v21_questions.jsonl", repo_type="dataset")` (verified
to cover all 458 row_keys in this pool) and aliases read from the local
canonical-checkout AH A0 pool (itself sourced from this repo's own
already-committed `datasets/kuq/` / `datasets/selfaware/`). See
`analysis-committed/PROVENANCE.md` for the full scheme, mirrored exactly from
the `j-space-localization-qwen3-4b` containment migration (commit `88c98cdc`).

Arms and controls:
- k=0 baseline (no write): establishes per-class base rates.
- coupled: the two-sensor controller at the working dose.
- permuted-sensor placebo: the per-example gains are shuffled across examples so
  the marginal caution write is identical but the per-example targeting is
  destroyed. Coupling must beat this placebo, not merely beat k=0. This is the
  same discipline AC and AO used to separate targeting from a constant shove.
- (optional, pending scout) constant-caution arm at the matched marginal
  magnitude, as a second targeting control.

Grader: reuse the coherence-aware grader lineage from the dark-actuator-screen so
that a refuse -> answer transition only counts when the produced answer is
well-formed, not malformed number/quote/repetition spam. The dark screen showed a
raw flip rate is meaningless without this check (candidate well-formed rate
0-17% vs 76% baseline). The release half in particular must gate on well-formed,
correct answers, not just non-refusal.

Instrument config files to pin at sign: `cell.yaml`, `gates.yaml`, and the
grader module (paths finalized after scout). Only committed files are declared in
`inputs:`; any fitted directions or pools promoted for provenance go under a
tracked `analysis-committed/` directory, never the gitignored `analysis/` or
`directions/` (the systemic gitignored-inputs bug that broke AO and AP on clean
checkouts).

## Prediction

The two-sensor coupled controller produces bidirectional selectivity over the
permuted-sensor placebo on raw-base: a tighten effect (unanswerable confab ->
coherent refuse) AND a release effect (answerable refusal -> well-formed correct
answer), each with a point margin over placebo whose bootstrap 95% CI excludes 0,
while not raising the unanswerable-confab rate above the k=0 baseline.

## Falsifier

Coupling adds nothing beyond a constant caution write: the coupled-minus-placebo
margin CI includes 0 on the selectivity gap. The bidirectional claim specifically
fails if only the tighten half clears (which the dark pos_ctrl already nearly
guarantees) and the release half does not (release margin CI includes 0), OR if
the release gain is bought by a rise in unanswerable confabs (the do-no-harm gate
fails) rather than by targeting the low-doubt refusals. A tighten-only pass is a
partial null on the novel claim, not a success.

## Gates

Pre-stated, mirroring AC-G1's bidirectional selectivity-gap construction. All
margins are coupled minus permuted-sensor placebo (fixed-seed row shuffle of the
per-example gains), bootstrapped over examples.

- G0 instrument validity (void if fails): on smoke, the caution write fires at
  L34 and gen_stream fires across decode steps, and the coupled setpoint lands in
  the coherent window (realized |marginal write| ~452-808 along c_hat, bf16,
  this experiment's own readback-calibrated window -- see the Design section's
  "Caution write direction" paragraph and NOTEBOOK.md's bf16
  dose-calibration-fix entry), so any no-move is behavioral, not instrumental.
  A collapse-regime setpoint (>=808, the lower of the two cells' median
  collapse floors) voids the run.
- G1-tighten: unanswerable confab -> coherent refuse rate, coupled minus placebo,
  point margin >= 5pt with bootstrap 95% CI excluding 0. "Coherent refuse" uses
  the dark-screen coherence-aware grader, not a raw non-answer.
- G1-release: answerable refusal -> well-formed correct answer rate, coupled minus
  placebo, point margin >= 5pt with bootstrap 95% CI excluding 0. "Well-formed
  correct" requires both the coherence check and answer correctness, not mere
  non-refusal.
- G2 do-no-harm (selectivity): the unanswerable-confab rate under coupled is not
  above the k=0 baseline (upper CI does not exceed baseline by more than a small
  pre-stated tolerance of 2 percentage points, locked before the run; see
  gates.yaml's g2_do_no_harm_confab_not_above_baseline for the count-equivalent
  encoding at this cell's 309-row size), so a release gain cannot be a blunt
  caution reduction that re-opens confabulation.

The bidirectional-selectivity headline requires G0 and G1-tighten and G1-release
and G2. G0 + G1-tighten + G2 with G1-release failing is reported as a tighten-only
partial null.

## Predictions scoreboard

| Predictor | Call |
|-----------|------|
| orchestrator | Tighten half PASSES (pos_ctrl already shows it); release half is the crux, roughly even odds it clears the placebo, with a tighten-only partial null the single likeliest outcome. |
| user (2026-07-06) | Full bidirectional PASS: both halves clear the placebo (CI excludes 0) and do-no-harm holds. |

## Outcome

Filled at resolve. Record the verdict, the gate results, and the one-sentence
summary that also goes into `verdict:` in the manifest.
