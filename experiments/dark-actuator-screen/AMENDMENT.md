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
erase_write at an AMBIENT-RELATIVE dose across a small ladder, at the
pre-generation anchor onward, and score the behavioral flip rate (confab ->
refuse, and refuse -> answer) on the pool. This uses the EXISTING tuner
fixed-strength arm machinery (not AO's proportional-gain feature): the strength is
fixed per direction, not per row; a screen is about whether a direction moves
behavior at all, not about proportional control.

Dose calibration (pre-flight, 2026-07-06; see NOTEBOOK.md). erase_write writes an
absolute coordinate (setpoint = strength * sigma), so behavior is
inert-then-coherent-then-collapse in the setpoint, and the coherent window scales
with the direction's own ambient projection, NOT with a fixed absolute strength.
On the positive control (answer-vs-refuse mass-mean, `pos_ctrl_L34`), a free-3090
sweep over 24 pool rows found the clean confab -> refuse flip at setpoint ~= k *
ambient with k in {5,7,9} (median 7), collapse only at k >= 13-15, and 12/12
confab rows flipping cleanly while already-refusing rows stay unchanged until
k >= 9 (the selectivity G-instrument needs). Therefore the dose ladder is set per
direction as strength = k * ambient_dir / sigma_dir for k in {5,7,9} (plus the
k=0 baseline), where `ambient_dir` is that direction's mean absolute projection
measured over the pool at the write positions during un-intervened decode. This
replaces the earlier absolute {1,2,4} placeholder ladder, which the pre-flight
showed is entirely in the inert regime (it would have failed the positive control
and voided the screen). A single absolute strength is NOT used because the 34
directions have different ambient scales: it would over-dose small-scale
directions into degenerate output (a false "moves behavior" hit) and under-dose
large-scale ones.

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
  [SUPERSEDED 2026-07-06: the wrapper was built and the screen executed; see
  Outcome.]
- `gates.yaml` was validated end-to-end against that arm-naming convention
  with `evaluate_gates()` on synthetic rows (both pass and fail branches
  exercised); no real rows exist yet. [SUPERSEDED 2026-07-06: the full 21760-row
  screen ran and was scored; see Outcome.]

## Outcome

RESOLVED 2026-07-06. NULL. Local RTX 3090, single seed 20260706, raw-base
bnb-4bit on the AK Stage-1 confab-rich surface. 34 directions (12 dark
candidates + 5 pos_ctrl + 5 neg_ctrl + 12 random controls) times 4 arms (k=0
baseline plus dose1/2/3 at k=5/7/9) times n=160 stratified subsample (80 confab
+ 80 refuse) = 21760 rows. rows_out.jsonl sha256
302fc7084672a7e8c1ab2a4fbbb9ffda6f07e08deb2aee176c0ee6b4fbe01ab5. Gate report
and lead verification banked under analysis-committed/ (score_gates_report.json,
verification_summary.json).

G-instrument PASSES, so the screen is VALID (not void). pos_ctrl_L34 at dose3
flips 79/80 confab rows to refuse (diff +77, CI [64, 90]); both negative controls
sit at the floor (neg_ctrl diff 0; randctrl diff 2, CI [0, 5]). The positive
control is independently verified as a genuine, coherent lever, not gobbledegook:
79/79 of its confab-origin abstentions are clean "I don't know the answer"
refusals with response_confidence driven to 0.0 from baseline confident answers,
against a baseline natural-refusal coherence of 78/78.

Verdict: NULL. The nine candidates that clear the raw graduation bar are an
artifact; none is promoted. score_gates_report.json records nine candidate
screen-gates passing (flip rate above the paired random control, CI excluding 0)
and three failing outright (degenerate). All nine apparent graduations fail on
verification, through three compounding failure modes. This is a lead
re-derivation corroborating the dark-redteam adversarial audit.

1. Grader coherence gap (decisive). Every graduating flip is refuse-to-answer,
   and the "answers" are malformed output the grader miscounts. The
   well-formed-answer rate (answer field is a real natural-language sentence, over
   60 percent alphabetic) on the dose3 refuse-origin "answered" rows is 0/79,
   0/66, 0/80, 3/72, 0/80, 1/80, 0/76, 10/80, 3/18 across the nine candidates,
   against a 61/80 (76 percent) baseline yardstick. The text is number-spam
   ("0.5,0.8}0.5,0.8}"), decimal loops (":0.85:0.85"), quote-spam, and
   mangled-refusal loops ("i don't don't don't"). The grader's is_degenerate
   (experiments/common/graders/dark_actuator_grader.py:76-154) only catches pure
   whole-string repetition, so a valid JSON prefix followed by collapse scores as
   not degenerate, the mangled wrapper defeats the refusal regex so the row scores
   as not abstained, and the row is therefore counted answered and flipped. The
   reported near-zero degenerate rate is this scoring gap, not clean output. The
   uniform refuse-to-answer polarity is itself a symptom: garbage can only score
   as "answered", which only refuse rows can flip into.

2. Under-dosed random control (matched-norm violated). The dose ladder is
   strength = k times ambient, so at dose3 the candidates write absolute setpoints
   of 34 to 219 while their paired random controls write only 4 to 42, roughly 5
   to 10 times weaker. The random control was never exercised at the candidate's
   own magnitude, so "beats its random control" is confounded by write magnitude
   rather than direction quality. Per-candidate setpoints are in
   verification_summary.json.

3. Off-manifold over-drive, not a graded lever. The refuse-to-answer rate is not
   dose-graded (it saturates at dose1 for several candidates and collapses for
   others; three candidates are 98 to 100 percent degenerate at dose3 and
   correctly fail their gates). The candidates are exactly off-axis (absolute
   cosine 0.000 to the pos_ctrl answer/refuse axis and to the propensity axis,
   orthogonal by census construction) and only weakly outcome-linked (census
   AUROC 0.60 to 0.72). A weak off-axis correlational signal cannot produce a real
   near-100-percent behavioral flip; over-writing an off-manifold direction pushes
   the hidden state off-manifold into grader-miscounted garbage. This matches the
   census read exactly: worth a screen, not a claim.

Scoreboard, scored straight: the orchestrator's call ("0 graduate; controls
behave") is correct; the user's call ("several graduate") missed. The user's
separate strategic read, that the dark subspace is not a source of taggable
features or actuators, is affirmed by this null.

Disposition: SHELVED. The dark subspace is ruled out as a near-term actuator or
feature source, and no candidate earns a follow-up amendment. The only
predictable, coherent lever surfaced by the screen is the on-manifold
answer/refuse axis (pos_ctrl), which was already known. Any future re-screen
requires two harness fixes as preconditions: (1) a magnitude-matched random
control written at the same absolute setpoint and the same layer as the
candidate, not merely the same k; (2) a coherence gate that catches
partial-repetition and malformed-JSON collapse, since the current is_degenerate
is defeated by any structured prefix.

Provenance: analysis/ and directions/ are gitignored for data containment; the
raw rows_out.jsonl is recorded by the sha256 above, and the gate report plus the
lead verification are committed under analysis-committed/. The expected_config_sha
in gates.yaml and experiment.yaml was left as a placeholder for this run, and the
config-sha drift guard was not enforced, consistent with a lab-notebook
diagnostic rather than signed confirmatory evidence. The run is therefore not
bit-reproducible from committed files alone (raw rows and direction JSONs are
gitignored); the banked reports and recorded SHA are the provenance record.

Attribution: dark-redteam adversarial audit (candidate cosine matrix,
dose-response curves, degeneracy detector) plus lead independent re-derivation of
the two decisive claims (the grader coherence gap and the magnitude mismatch).
