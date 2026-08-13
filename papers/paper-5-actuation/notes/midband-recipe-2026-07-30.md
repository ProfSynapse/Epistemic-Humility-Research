# The mid-band abstention recipe (working note)

Status: working note for the paper 5 rewrite, captured 2026-07-30 from the PI
discussion. Not a claims surface. Each step cites where it was validated; the
boxed version of this goes into the rewritten manuscript as a numbered
procedure. Vocabulary follows papers/common/terminology.md (known-unknown /
KU; no "doubt"; "caution" pending the naming battery, use "abstention write"
here).

## Goal

Given any open-weight model, make it say "I don't know" on questions it
internally cannot answer, at minimal cost to questions it answers correctly,
using only a fitted linear direction and (optionally) a per-row gate.

## The recipe

1. **Run the family read-atlas first.** Full-depth workspace profile plus the
   three-axis read panel; find the interior band where the KU readout reads at
   or above 0.80 held out. Layer choices are NEVER ported across families
   (family-atlas skill; four-family precedent: llama 15-23, mistral 7-27,
   gemma hs13-42 read-healthy, qwen 22-36).
2. **Pick the write site inside the actuating band, by relative depth.**
   rd = layer_idx / num_hidden_layers, actuating band rd approximately
   0.375-0.639 across validated families (paper 5 section 3 reporting
   convention). Everything at rd above ~0.71 failed everywhere it was tried.
3. **Check the architecture for traps before committing to a site.** No write
   sites inside KV-shared regions or other cache-reuse blocks: at the
   Gemma-4-E4B KV seam (first shared block), apparent actuation was
   reproduced by random-direction placebos (effect ratio 1.14 vs floor 3.0,
   Phase A 2026-07-30) and is instability, not steering. Below the seam the
   same model actuates with perfect direction-specificity (placebo 0/168 in
   all five draws).
4. **Fit on a FIT split, evaluate held out. Always.** Fit the KU readout
   (gate) and the abstention write direction (c_hat) from the model's own
   contrast on FIT rows; freeze tau and the direction before any held-out
   scoring (qwen35-4b-midband-doubt-snap -> -heldout promotion pattern).
5. **Calibrate dose per site on the registered ratio ladder.** Ladder ratios
   are registered before running; a site with zero usable rungs is a
   dose-viability NOT-RUN, not a tuning invitation. Readback verification:
   dosed rows read back within 5% + 0.5 absolute of the calibrated dose.
6. **Run the mandatory controls or the number is not real.**
   - Undosed floor on the same held-out rows (no-injection baseline).
   - K >= 3 (registered K = 5) magnitude-matched random-direction placebos at
     the same site, same dose, same fired rows; SC1-screened orthogonal to
     both c_hat and the readout. Effect ratio = lift(true) / max_k
     |lift(placebo_k)| must clear 3.0 (RG1 criterion; PASS-DEGENERATE label
     when the denominator is exactly zero).
   - Known-correct cost cap (G2, rate <= 0.05 and Wilson upper < 0.10), with
     the fired-only companion reported (NOT-ADJUDICABLE below n = 35 fired
     known rows is a third disposition, never a pass).
7. **Gate by dose regime.** At overdrive doses the gate is mandatory (ungated
   damages 60.1% of known-correct rows vs 3.1% gated;
   ungated-vs-gated-dose-matched). At calibrated mid-band doses the write
   self-sorts (permuted-gate control retains most of the confab abstention;
   gate-contribution-factorial) and the gate is an optional accuracy trim
   (+0.13-0.15 selectivity, sub-floor) plus cost governance. Ship the gate if
   the deployment cannot tolerate known-answer damage; skip it only at
   validated mid-band operating points.

## Open extensions (paper 6 candidates, not part of the recipe)

- Graded dosing by readout score (M2 showed margin is redundant with the
  readout, so grade by readout, not margin; untested as an actuator).
- Optimized write directions and low-rank subspaces (precedent caution: the
  M4c constructed direction lost specificity to covariance-shaped random
  directions; any optimization needs the full placebo battery and held-out
  discipline).
- Naming battery for the write direction (dose-response shape, negative dose
  on a refusing checkpoint, hard-known vs easy-known cost profile, output-form
  analysis) so the direction's name is earned, not vibed.
