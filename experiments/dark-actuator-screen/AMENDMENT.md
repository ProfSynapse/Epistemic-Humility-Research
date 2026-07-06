# dark-actuator-screen

Status: draft (not signed; do not launch as confirmatory evidence). Tier-2
exploratory lab-diagnostic (a knob-discovery SCREEN, not a single-hypothesis
confirmatory cell). Never pooled with the locked Phase 1 matrix. Its only
positive output is a ranked shortlist: any candidate that clears the graduation
bar earns its OWN signed amendment before any claim is made.

Machine state lives in `experiment.yaml`; it is not duplicated here.

## Motivation and posture

The dark-displacement census (PR #222, lab notebook) found that 96 to 99% of
generation-time hidden-state displacement lies outside the named epistemic axes,
with a structured low-rank remainder. It froze 12 raw-base candidate directions
that clear all three literature nuisance screens (consistency >= 0.6, pooled
outcome AUROC >= 0.60, all nuisance correlations < 0.15). The census verdict was
explicit: these are genuine, stable, non-bookkeeping off-axis directions, but
weak-prior (outcome AUROC 0.60 to 0.72, poor cross-checkpoint transfer), so they
are "worth a dose screen, not a claim." This is that dose screen.

The question is causal, not correlational: reading structure off an axis does not
mean pushing along it moves behavior. AL already showed the confab-propensity
direction reads the confab cloud but does not actuate it; the census candidates
are weaker on outcome than propensity. So the prior is that most or all are inert.
The screen exists to find the exception cheaply if one exists, and to rule the
set out cleanly if not.

## Design

Substrate: the RAW-BASE checkpoint. The 12 candidates were fit on raw-base and do
NOT transfer to GRPO-v2 (best |cosine| 0.15 to 0.52), so they can only be screened
where they live. Raw-base produces confabulations on the unanswerable pool (the AK
Stage-1 raw-base arm: confab and refuse rows both present), so there is a
fabricate-vs-refuse behavior to move. Same system prompt, greedy decoding, grader
as the AK Stage-1 raw-base cell. Local RTX 3090, single seed.

A causal actuation (dose) screen. For each screened direction, apply the tuner's
fixed-strength erase_write (or additive push) at matched norms across a small dose
ladder, at the pre-generation anchor onward, and score the behavioral flip rate
(confab -> refuse, and refuse -> answer) on the pool. This uses the EXISTING
tuner fixed-strength arm machinery (not AO's proportional-gain feature); a screen
is about whether a direction moves behavior at all, not about proportional
control.

Directions screened (the candidate set is exactly the 12; controls calibrate the
instrument):

- 12 dark-displacement candidates: the frozen raw-base JSONs
  `dark_cand_raw-base_<layer>_<family>_pc<idx>.json` (census output; currently
  untracked in the census worktree, to be staged or regenerated for the run).
- Positive control: the raw-base answer-vs-refuse mass-mean direction (a direct
  behavioral axis; must register as a hit or the screen instrument is broken).
  NOTE the honest limitation below: we have no AC-validated lever on raw-base.
- Negative controls: random unit directions at matched norm (seeded) and the
  raw-base confab-propensity direction (AL showed it does not actuate). Both must
  register at or near the random floor or the screen mislabels.

Each direction is pushed identically (matched norms, same dose ladder, same rows),
so the screen does not confound the direction with the write form.

## Prediction

(orchestrator) Most likely 0 candidates beat the random-direction control;
small chance the strongest by within-checkpoint consistency (`L34 succ pc0`)
registers a weak hit. The positive control (answer-vs-refuse) moves behavior; the
negative controls (random, propensity) sit at the floor.

(user, recorded 2026-07-06) SEVERAL candidates graduate: the dark subspace holds
real behavioral levers, worth a cluster of follow-up amendments. This is a sharp
disagreement with the orchestrator's mostly-null call and the census weak-prior
read; scored on the graduation count.

Positive-control decision (user, 2026-07-06): proceed with the raw-base
answer-vs-refuse mass-mean axis as the positive control (do not add a separate
lever-validation pre-step); the honest limitation below stands and the negative
controls bound the candidate verdicts.

## Falsifier / graduation criterion

This is a screen, so the operative bar is graduation, not a single falsifier: a
candidate GRADUATES iff its behavioral flip rate exceeds the random-direction
control with a bootstrap 95% CI excluding 0, at matched norm. Graduation earns a
separate signed amendment; it is not itself a claim. If no candidate graduates,
the 12 join the correlate pile cleanly (reads-structure-but-does-not-actuate) and
the dark subspace is ruled out as a near-term actuator source. If the positive
control fails to move behavior, the screen instrument is broken and the run is
void (no candidate verdicts drawn).

## Gates

- G-instrument (pass/fail, precondition): the positive control moves the flip
  rate with a CI excluding 0 AND both negative controls sit within the random
  floor. If this fails the screen is void.
- G-screen (descriptive, per candidate): flip rate vs the random-direction
  control, bootstrap 95% CI. Ranked table; graduation bar = CI excludes 0.
  Effect-size floor locks from a pilot before the full readout.

## Honest limitation (pre-stated)

We have no AC-validated caution lever on raw-base (AC validated GRPO-v2). The
positive control here is the answer-vs-refuse mass-mean axis, which is expected to
move behavior but has not been independently validated as a lever on raw-base the
way refined B1 validated caution_perp on GRPO-v2. So a weak positive-control
result would leave the screen underpowered rather than cleanly negative. This is
the same class of gap AN fell into; the difference is we name it up front and the
negative controls still bound the candidate verdicts.

## Predictions scoreboard

| Predictor | Call |
|-----------|------|
| orchestrator | 0 graduate (small chance L34 succ pc0); controls behave |
| user | Several graduate (dark subspace holds real levers) |

## Build notes (config staging, CPU-only, no GPU launch)

Recorded here for review before sign, not part of the locked prediction/
falsifier/gates prose above.

- **Authoritative candidate copy**: two non-identical `dark_cand_raw-base_*`
  copies existed on disk (main checkout vs the `lab-dark-displacement-census`
  worktree). The worktree copy (HEAD `787f4b6d`, merged as PR #222) is
  authoritative: its per-candidate provenance (`screen_input_linear_r2`,
  `screen_position_r2`, `screen_rogue_energy_frac`, `screen_verdict`) and its
  `census_report.json` headline (`n_survive_all_screens: 12`) reproduce the
  committed `analysis-committed/dark_displacement_census_summary.md` table
  exactly (spot-checked `L16 arel pc7`, `L34 succ pc0`). The main-checkout copy
  predates the three-screen commit and carries no screen fields at all.
- **Positive/negative controls are fit per capture layer** (L16/L20/L24/L28/
  L34), one pair per layer, using the exact pre-QR `refuse`/`propensity`
  formulas at `dark_displacement_census.py:206-215` (`build_span`) on the same
  raw-base pool -- not the QR-orthogonalized span basis `build_span` returns.
  Each candidate is screened against the positive/negative control fit at ITS
  OWN layer. The AMENDMENT text names these controls in the singular; per-layer
  fitting was chosen because `build_span` is inherently per-layer and this is
  the literal, lowest-risk-of-misinterpretation reading of "reusing the census
  `build_span()` logic."
- **Random-direction controls**: one seeded unit vector per candidate (not one
  global random direction), matched to the candidate's own layer/hidden_dim,
  seed derived from `sha256(f"20260706:{candidate_name}")`.
- **Layer/block adapter**: the census candidate JSON's `layer` field is the
  1-indexed AK Stage-1 capture label (e.g. `L16` -> 16); the tuner's
  `InterventionHook`/`get_decoder_layer` need the 0-indexed decoder-module
  index. Every direction JSON staged for this screen carries the tuner's
  `layer` field set to the census's `block` (`lnum - 1`), not its `layer`
  (`lnum`) -- see `build_directions.py` docstring "ADAPTER NOTE."
- **One steer cell per direction**: `synaptic-tuner` `SteerCellConfig` binds
  exactly one `law.readout` per run, so `cell.yaml` is the shared PATTERN for
  all 34 directions (12 candidates + 5 positive + 5 negative + 12 random
  controls), not 34 separate committed files. `law.readout` defaults to
  `L34_succ_pc0` (parseable on its own). Landing every direction's dose-ladder
  rows in the ONE `execution.output_path` `gates.yaml` reads requires a
  launch-time wrapper that overrides `law.readout` and prefixes each arm name
  with the direction name (`<direction>__baseline`, `<direction>__dose3`, ...)
  per sub-run. That wrapper is NOT built yet -- see NOTEBOOK.md.
- `gates.yaml` was validated end-to-end against that arm-naming convention
  with `evaluate_gates()` on synthetic rows (both pass and fail branches
  exercised); no real rows exist yet.

## Outcome

Filled at resolve.
