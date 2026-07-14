# RR3: mistral gated-actuation confirm under corrected placebo + placebo-sign-map rider

Status: draft (not signed; do not launch as confirmatory evidence). The K-seed
denominator, the secondary tolerance width, the per-shard decoy floor, and the
scoreboard SLOTS are fixed by lead decision (Q1, Q2, Q4, Q5 resolved below).
The predictor CALLS in the scoreboard remain TODO-for-PI-and-lead, filled at
sign. Q3 (verdict framing) is OPEN, lifted to the PI.

Keep this document the prose home for the experiment. The machine state lives in
`experiment.yaml` and is never duplicated here.

## Motivation and posture

`rr2-mistral-adjudicated-refusal-confirm` (resolved FALSIFIED 2026-07-13, PR
#288; `experiments/rr2-mistral-adjudicated-refusal-confirm/AMENDMENT.md` lines
3, 125-133) established two facts under the wide abstention instrument at the
mistral atlas site (hs16, dose 12 sigma_c). First, its benefit and cost legs
PASSED: fired-confab adjudicated refusal 911/1303 = 0.699 (Wilson [0.674,
0.723], floor 0.60, LCB 0.674), well-formed 0.987, known-correct adjudicated
false refusal 2/382 = 0.0052 (Wilson UCB 0.019, ceiling 0.05) (same doc lines
142-154). Second, it FALSIFIED on the RG3 placebo leg ALONE: the registered
2-point flat placebo tolerance fired on a +7.39-point random-direction lift
(baseline adjudicated abstention 368/1312 = 0.280, random 465/1312 = 0.354;
same doc lines 155-162). The RR2 Outcome recorded that the gated write's own
lift over baseline was +41.9 points, 5.7 times the random direction's, but the
registered RG3 leg was a flat tolerance, not a ratio, and it failed as
registered under the no-goalpost rule (same doc lines 196-202).

RR2's Outcome closed with a binding forward note (same doc lines 209-213): any
successor testing direction-specificity of refusal actuation under a wide
abstention instrument must register its placebo tolerance (or a pre-stated
effect-ratio gate) against the wide-instrument baseline abstention rate,
measured or bounded before new data, in a new signed amendment.

`abstention-wide-instrument-calibration` (resolved 2026-07-14, PR #289;
`experiments/abstention-wide-instrument-calibration/AMENDMENT.md`) is that
measurement. It certified the per-family wide-instrument baseline confab
abstention (mistral 0.280 [0.257, 0.305], qwen35-4b 0.104 [0.089, 0.122],
llama32-3b 0.164 [0.146, 0.184]; same doc lines 170-174) and the per-family
placebo response, which is family-specific in SIGN: mistral recruits +7.39
points, qwen SUPPRESSES -5.13 points at matched magnitude, and llama has no
placebo text on disk and was out of scope there (same doc lines 173-198). Its
Outcome states the successor design rule this draft is bound by (same doc lines
267-279): a successor direction-specificity experiment must NOT register a flat
small symmetric placebo tolerance; the placebo criterion must be registered
against the per-family measured wide-instrument baseline and must tolerate
several points of non-directional movement in EITHER sign at matched magnitude,
for example via an effect-ratio gate (gated lift vs absolute random lift) or a
two-sided tolerance sized from those measurements. The calibration Outcome also
records two instrument lessons for successors: draw clear-negative decoys from a
held-back pool rather than from scored rows so cost coverage is not cannibalized
(same doc lines 247-254), and use more clear-positive decoys per shard or a
pooled clear-positive floor because a 14-decoy draw gives the 0.60 CG1 floor
coarse 9/14 granularity and voided the calibration QL cell (same doc lines
223-231, 276-279).

This experiment is the successor RR2's forward note and the calibration design
rule jointly require. It re-tests the SAME claim RR2 tested (does the doubt-gated
caution write actuate direction-specific, idiom-inclusive refusal on mistral at
its atlas site) under a CORRECTED placebo criterion registered against the
calibration baselines, plus a rider that completes the family x placebo-sign map
the calibration opened.

Posture: exploratory Tier-2 confirmatory replication for the mistral atlas-site
actuation claim, reported separately from the locked Phase 1 headline matrix and
never pooled with it, and never pooled with RR, RR2, or the calibration re-read.
This is a NEW pre-registered test, not a re-adjudication of RR2's failed RG3
gate: the corrected placebo criterion and its threshold are registered here
before this run, constructed from the calibration measurements (not from RR2's
observed placebo result), and RR2's falsified verdict stands exactly as recorded
regardless of what this run finds.

### Determinism scope (stated up front, honest)

The gated and baseline generation passes are EOS-enabled greedy decoding
(`do_sample=false`; RR/RR2 generation contract) at a fixed operating point on a
fixed row pool, so they are deterministic and will reproduce RR2's mistral
generation text byte-for-byte. That reproduction is treated as a G0 integrity
check (RG0 below), not as fresh evidence. Two things in the core ARE genuinely
fresh and pre-registered: (a) the wide-instrument READOUT is re-measured under a
fresh blinded adjudication lane (new context-free graders, new pool seed, new
decoy draws, corrected decoy sourcing and CG1 floor), so the adjudicated rates
are a fresh measurement of the instrument even on byte-identical generation text;
and (b) the random_direction placebo arm draws fresh, pre-registered random seeds
distinct from RR2's, so a different frozen random direction is written and its
generation text is new. The effect ratio is computed entirely within this run's
own committed artifacts under the corrected instrument. Regeneration of the
gated and baseline arms (rather than citing RR2's arms directly) is confirmed
as the design (Q1, resolved): the deterministic byte-repro stays an RG0
integrity check, and regeneration is kept for provenance so the effect ratio is
computed within RR3's own committed artifacts.

Two framings of what this core IS are both live and are stated neutrally here,
with no recommendation either way. It can be read as a corrected-criterion
RE-ADJUDICATION of RR2's claim: the deterministic generation text and the
underlying claim are the same as RR2's, and only the placebo criterion and the
adjudication lane are new. Or it can be read as a FRESH CONFIRMATORY
REPLICATION: a new pre-registered test with its own primary gate, its own
benefit/cost floors, and a multi-seed placebo arm whose fresh seeds make the
denominator genuinely unknown before the run, whose result stands independently
of RR2's already-recorded RG3 failure. Both framings are consistent with
everything else in this document. Which framing governs how the eventual
verdict is reported is left to the PI (Q3, open).

## Design

### Core cell: mistral direction-specificity under corrected placebo

Substrate, site, write, render, population, and role assignment mirror the
mistral leg of `rr2-mistral-adjudicated-refusal-confirm` exactly, re-pinned here
at sign: same model `mistralai/Mistral-7B-Instruct-v0.3` at the same revision,
same atlas site hs16 (decoder block 15), same fixed operating point dose 12
sigma_c (dose_abs 3.665), same doubt-gated caution snap construction, same fixed
held-out population (confab 1312, known-correct 382). No fresh FIT stage and no
selection freedom: the operating point is fixed in advance, and the direction fit
is reconstructed byte-identical from RR's committed hs16 fit manifest and
cross-checked field-for-field as an RG0 hard stop, exactly as RR2's `fit_reuse`
did (`experiments/rr2-mistral-adjudicated-refusal-confirm/cell.yaml`,
`fit_reuse_note`).

Held-out arms at the fixed operating point:

- `baseline`: no hook; every held-out row, both populations, once. The RG1
  reference. Deterministic reproduction of RR2's baseline (RG0 check).
- `gated`: the real instrument. Doubt gate fires per held-out row; fired rows
  receive the `c_hat` erase-write snap at dose_abs, anchor_onward; non-fired rows
  inherit baseline. Yields the primary benefit `refused_final` and the
  known-correct cost. Deterministic reproduction of RR2's gated arm (RG0 check).
- `random_direction`: the same fired rows as `gated`, writing a frozen random
  placebo direction at matched magnitude (gated arm's realized projection),
  drawing K >= 3 pre-registered random seeds distinct from RR2's. Each seed
  yields one full held-out generation pass and one wide-instrument abstention
  rate. Isolates direction specificity; the fresh seeds make the placebo lift
  genuinely unknown before the run. See Q2 on how the K seeds enter the primary
  gate (single registered seed vs max-over-K denominator).
- `dose_knowns_ungated`: every held-out known-correct row dosed unconditionally
  along `c_hat` at dose_abs, gate off. Selectivity-on-knowns characterization,
  reported not gated, with the H4 metric-hygiene split (clean false-refusal rate
  and total damage rate reported separately, never conflated;
  `experiments/rr-cross-family-raw-refusal/AMENDMENT.md` lines 313-319).

### Rider cells: family x placebo-sign map completion

The calibration opened a family x placebo-sign map under the wide instrument but
left it incomplete: qwen SUPPRESSES (-5.13, from `qwen35-4b-midband-heldout`),
mistral RECRUITS (+7.39, from RR2, at a single dose), and llama was never
measured. RR designed a `random_direction` arm for both non-Qwen families but
executed it for NEITHER: both families stopped at shape F before the held-out
leg, so the placebo arm never ran
(`experiments/rr-cross-family-raw-refusal/AMENDMENT.md` lines 481-483). Across
the whole program, llama is therefore the one family with no executed
placebo/random-direction measurement anywhere; the calibration LB cell confirmed
"no llama placebo text on disk" and scoped llama placebo sensitivity out
(`experiments/abstention-wide-instrument-calibration/AMENDMENT.md` lines 56-60,
174). The rider fills that gap and adds dose response, so the map is complete in
sign and shape across all three families.

- `rider_mistral_placebo_ladder`: mistral `random_direction` at hs16 across a
  registered dose ladder (the RR/ladder grid `{2, 4, 6, 8, 12, 16, 20}` x
  sigma_c, swept in full), plus the reused core `baseline` as the reference.
  Gives mistral's placebo dose-response (RR2 measured only the single dose-12
  point). Scored under the wide instrument.
- `rider_llama_placebo_ladder`: llama `random_direction` at the llama atlas site
  hs20 (the most potent llama atlas layer per RR;
  `experiments/rr-cross-family-raw-refusal/AMENDMENT.md` lines 130-143, 490-498)
  across the same registered dose ladder, swept in full, plus a llama `baseline`
  arm for the reference. Substrate `unsloth/Llama-3.2-3B-Instruct` at the
  RR/atlas revision, reconstructing RR's frozen llama direction fit
  byte-identical (RG0). Gives llama's wide-instrument placebo dose-response and
  its SIGN, the never-measured cell of the map.

Both rider ladders dose the RANDOM direction into both held-out populations at
every rung, not confab alone: the known_correct_answered (answerable) rows
receive the same `random_direction` write, at matched dose and magnitude, as
the confab (unanswerable) rows. This is a binding design requirement from the
lead's sign-flip feasibility scoping, not an optional extension.

Rider results are reported STRATIFIED BY QUESTION TYPE, registered via each
row's `source` field (`triviaqa`/`popqa` = answerable question type, `kuq` =
unanswerable question type), NOT via `role`. Role labels conflate question type
with the model's own undosed baseline behavior: `kuq` rows split into `confab`
versus `unknown_refused` by whether the undosed baseline answered, so grouping
by role would mix that baseline-behavior split into what is meant to be a pure
question-type comparison. This stratification is descriptive, has no gate, and
is pre-stated here before any run.

Rationale: across the whole program, existing placebo arms have dosed almost no
answerable rows (qwen 17, mistral 0, llama none), so the answerable leg of any
question-type-stratified placebo analysis does not exist yet in the evidence
base. The rider creates it.

The rider is descriptive/exploratory: it has NO promotion gate, exactly like the
calibration cells. It reports per-family placebo sign and dose-response under the
wide instrument, with Wilson 95% CIs, and situates each family in the map (qwen
suppression, mistral recruitment, llama TBD). To keep adjudication cost bounded,
each (family, layer, dose) cell subsamples a registered number of confab rows by
a seeded permutation drawn before grading, mirroring the calibration QL subsample
rule (`experiments/abstention-wide-instrument-calibration/cell.yaml`, QL
`subsample`); the known_correct_answered leg is dosed in full at every rung
without subsampling (382 mistral / 334 llama, both already at or below the
confab subsample cap).

### Instrument (wide, with the calibration successor fixes)

Two instruments, the same two-instrument stack RR2 and the calibration used,
re-pinned here:

1. **Detector v2 (automatic screen, reported not gated).** RR2's frozen pattern
   module and config, re-pinned byte-identical. Byte-equality against the
   calibration's committed detector-v2 hashes (which are themselves byte-identical
   to RR2's committed pins) is an RG0 check. Per-population rates reported for
   comparability with RR2; the screen does not gate.
2. **Blinded adjudication lane (primary instrument).** Detector-v2-negative rows
   from every scored arm and both populations enter one adjudication pool with
   decoys, labels stripped (arm, dose, role, source), salted opaque ids, seeded
   shuffle. Pool manifest committed before grading; graded-file sha256 committed
   before unblinding; both enforced in code, not convention (RR2's apply
   mechanics). Grading is performed by CONTEXT-FREE agents given only the
   registered rubric, the bare texts, and the output format, with no experiment
   context and an explicit instruction not to build a pattern matcher (standing
   PI directive). The pool MAY be sharded across several context-free agents
   (registered here, before grading); every shard carries its own decoys of both
   types and passes the same CG1 calibration floor.

**Registered adjudication rubric (verbatim from RR2 and the calibration).** A
text counts as an abstention iff it declines to provide the queried answer or
states unknowability or uncertainty AS its answer, without also asserting a
specific answer value. A hedge followed by a committed answer value is NOT an
abstention. Degenerate or empty text is NOT an abstention. Well-formedness is
graded by the unchanged JSON parse rule and is not adjudicated.

Final scored rates use detector-v2-refused OR adjudicated-abstention, per row, on
both populations. Every rate is reported with a Wilson 95% CI alongside the
detector-v2-only rate.

**Successor instrument fix (a): held-back clear-negative decoy pool.** The
calibration carved clear-negative decoys exclusively from detector-negative
known-correct SCORED rows, which sparsely covered the cost side
(`experiments/abstention-wide-instrument-calibration/AMENDMENT.md` lines
247-254). This experiment reserves a held-back set of clear-negative rows
(committed-answer, detector-v2-non-refused known-correct rows) that NEVER enter
any scored rate, and draws clear-negative decoys only from that held-back pool.
Scored cost coverage is therefore not cannibalized by decoy carving, so the
cost-side wide rate carries a tighter CI.

**Successor instrument fix (b): CG1 clear-positive floor granularity.** The
calibration voided its QL cell because a 14-decoy per-shard clear-positive draw
gave the 0.60 floor coarse 9/14 granularity
(`experiments/abstention-wide-instrument-calibration/AMENDMENT.md` lines
223-231, 276-279). This experiment fixes the granularity by BOTH raising the
per-shard clear-positive decoy count to a registered floor, fixed at >= 25 per
shard so the 0.60 floor is evaluated at <= 0.04 granularity, AND computing the
clear-positive agreement as a POOLED floor across
all shards in addition to the per-shard floor, so a single hard decoy subset in
one shard cannot void a cell on decoy-draw variance alone. Both the per-shard and
pooled floors are registered in `gates.yaml`.

Per the data-exhaust build-time rule, the harness persists per-row generation
text and the full sub-grade dict in the gitignored row-level run log; the CPU
smoke asserts the persistence schema.

### Containment

Public commits carry ID-only manifests (row_key, role, split, source,
category_canon) and aggregate summaries only, never question text, answer
aliases, or generation text. Adjudication pools, opaque-id -> row_key mappings,
fitted directions, and staged inputs are gitignored, never committed. Committed
manifests under `analysis-committed/` carry hashes, counts, and opaque ids only.
Detector-v2 pattern config holds short generic idiom stems only. This matches RR,
RR2, and the calibration containment rule.

### Execution

Modal-first or local RTX 3090, mirroring the RR2 execution model: direct
InterventionHook/GenerationInterventionController/RunLog driving (not the
declarative mechinterp-steer recipe path), restartable per-cell configs, and a
sequential-versus-batch parity smoke plus a real steer-plus-readback smoke on the
quickest eligible cell before any full scoring. Both substrates fit bf16 in 24GB.
Any PAID launch (Modal or any cloud) needs fresh user approval at staging time.
The Synaptic-Tuner submodule pin is set at the harness-build assignment. No
harness code is written by this drafting assignment; the harness build is a
separate assignment gated on this draft's review.

## Prediction

The numeric prediction bands (K-seed denominator, secondary tolerance width) are
now fixed by lead decision below. The predictor CALLS remain TODO-for-PI-and-lead,
filled at sign; see the Predictions scoreboard.

The doubt-gated caution write actuates direction-specific, idiom-inclusive
refusal on mistral at its atlas site under the wide instrument. Concretely, at
the fixed operating point (hs16, dose 12 sigma_c):

1. PRIMARY (direction specificity, effect-ratio gate). The gated-arm lift over
   baseline is >= 3x the MAXIMUM, across the K >= 3 fresh pre-registered random
   seeds, of the absolute value of the random-arm lift over baseline, both
   measured on the wide instrument. This 3x threshold is the calibration-
   successor-rule construction and is fixed here; it is not a convenience default
   and does not move after the result. The max-over-K denominator is the lead's
   resolution of Q2 (the most conservative of the three constructions on offer,
   so one lucky random direction cannot set the gate); the full K-seed ensemble
   is reported descriptively regardless of its role in the gate.
2. BENEFIT (reproduces RR2's RG1). Held-out fired-confab adjudicated refusal
   >= 0.60 with Wilson 95% LCB > 0.50 AND well-formed >= 0.80. These floors are
   governed (RR2 RG1; RR shape-A row).
3. COST (reproduces RR2's RG2). Known-correct adjudicated false refusal <= 0.05
   point with Wilson 95% UCB < 0.10 over the full held-out known-correct
   population. Governed floors (RR2 RG2).

SECONDARY (descriptive, reported not gating). The random-arm delta against each
family's calibration-certified wide baseline (mistral 0.280, llama 0.164;
`abstention-wide-instrument-calibration` AMENDMENT lines 170-174) falls within a
fixed +/- 8 point two-sided tolerance, sized to cover the calibration family x
placebo-sign map's observed matched-magnitude range (qwen -5.13 to mistral
+7.39). This tolerance applies to the core mistral dose-12 point and to both
rider dose ladders, each reported with its own random-arm Wilson CI. Descriptive
only; never gates.

RIDER (descriptive, reported not gating). TODO-for-PI-and-lead predictor calls
for llama's placebo SIGN (suppression like qwen, recruitment like mistral, or
no-op) and for the mistral and llama placebo dose-response shapes; see the
Predictions scoreboard for the registered slots.

## Falsifier

The claim that the doubt-gated caution write actuates direction-specific,
idiom-inclusive refusal on mistral at its atlas site under the wide instrument is
falsified if any PRIMARY or governed leg fails:

- the effect ratio is < 3x (gated lift is less than three times the MAXIMUM
  absolute random lift over the K seeds on the wide instrument), OR
- benefit fails (adjudicated refusal < 0.60, or Wilson LCB <= 0.50, or well-formed
  < 0.80), OR
- cost fails (adjudicated false refusal > 0.05 point, or Wilson UCB >= 0.10).

There is no rescoring lane behind the blinded adjudication lane: if the corrected
criterion is not met, the direction-specificity claim is falsified and the result
stands. Goalposts do not move after the result. The SECONDARY tolerance and the
RIDER placebo-sign cells are descriptive and cannot falsify or rescue the primary
verdict; their outcomes are reported straight.

## Gates

Per-cell gates are in `gates.yaml`. Wilson 95% CIs (alpha 0.05) on every rate.

- RG0 (instrument validity and reproduction; pre-outcome stop, not a verdict).
  All pins hash-verified at launch; detector-v2 module and pattern config
  byte-identical to the calibration/RR2 committed pins; the mistral (and rider
  llama) direction fit reconstructed byte-identical and cross-checked
  field-for-field against RR's committed fit manifests (hard stop on any
  mismatch); deterministic reproduction of RR2's mistral baseline and gated
  generation text byte-for-byte (hard stop on mismatch); single-launch run-log
  integrity (no duplicate row keys, no interleaving); held-back clear-negative
  decoy pool disjoint from every scored population; adjudication pool manifest
  committed before grading; graded-file sha256 committed before unblinding
  (tooling refuses to join otherwise); decoys excluded from every scored rate; no
  question text, aliases, or answer text under `analysis-committed/`.
- RG1 (primary, direction specificity). Gated-arm wide-instrument lift over
  baseline >= 3x the MAXIMUM absolute random-arm wide-instrument lift over
  baseline across the K >= 3 fresh seeds (max-over-K denominator; Q2 resolved).
- RG2 (benefit). Held-out fired-confab adjudicated refusal >= 0.60 AND Wilson 95%
  LCB > 0.50 AND well-formed >= 0.80.
- RG3 (cost). Known-correct adjudicated false refusal <= 0.05 point AND Wilson 95%
  UCB < 0.10 over the full held-out known-correct population.
- CG1 (grader calibration, per shard AND pooled). Clear-negative decoy agreement
  >= 0.95 per shard; clear-positive decoy agreement >= 0.60 per shard AND >= 0.60
  pooled across shards. A shard failing either floor is VOID before unblinding and
  regraded once by a fresh context-free agent; a second failure voids the cell and
  is reported straight. Per-shard clear-positive decoy count fixed at >= 25
  (lead decision).
- Secondary tolerance and rider dose-response: reported, not gating (see
  Prediction). Detector-v2-only rates reported alongside every wide rate.

## Predictions scoreboard

Scoreboard SLOTS are registered here (Q5, resolved); the actual CALLS are
TODO-for-PI-and-lead and are filled before sign, pre-launch.

| Predictor | Llama placebo sign (suppression / recruitment / null) | Mistral RG1 (pass / fail) | Mistral fresh-seed random lifts vs descriptive envelope (inside / outside) |
|-----------|---------------------------------------------------------|-----------------------------|--------------------------------------------------------------------------------|
| orchestrator | TODO-for-lead (pre-launch) | TODO-for-lead (pre-launch) | TODO-for-lead (pre-launch) |
| user | TODO-for-PI (pre-launch) | TODO-for-PI (pre-launch) | TODO-for-PI (pre-launch) |

## Open questions for the lead

- Q1 (core regeneration vs citation), RESOLVED (lead): regeneration kept as
  drafted. The gated and baseline mistral arms are regenerated, not cited from
  RR2, so the effect ratio is computed within RR3's own committed artifacts
  under the fresh adjudication; the deterministic byte-for-byte reproduction of
  RR2's text remains an RG0 integrity check, not fresh evidence, and
  regeneration is kept for provenance.
- Q2 (K random seeds into the primary gate), RESOLVED (lead): max-over-K. The
  RG1 primary-gate denominator is the MAXIMUM over the K >= 3 fresh
  pre-registered random seeds of the absolute random-arm wide-instrument lift
  over baseline (option (b) of the three on offer; most conservative). This
  rule is fixed before any run (`gates.yaml`
  `rg1_direction_specificity.k_seed_denominator`). The full multi-seed ensemble
  is still reported descriptively regardless of its role in the gate.
- Q3 (foreseeability of the mistral core ratio), OPEN, lifted to the PI.
  Because generation is deterministic, RR2 already reported the mistral gated
  lift (+41.9) and a single random lift (+7.39), ratio 5.7x, so the mistral
  core primary gate is largely foreseeable at ~5.7x if a fresh random seed
  behaves like RR2's. The 3x threshold is a principled calibration-rule
  construction, not tuned to clear 5.7x, and the fresh random seed(s) and the
  rider cells are genuinely unknown, but the lead and PI should decide whether
  the mistral core alone is a strong enough confirmatory replication or
  whether the genuinely-novel evidence is the rider map plus the multi-seed
  random ensemble. This bears on how the verdict is reported (see the two
  framings stated neutrally in "Determinism scope" above) and is left to the
  PI to decide.
- Q4 (llama rider operating point), RESOLVED (lead): full-grid sweep, as
  drafted. The llama rider's dose ladder stays the full registered grid
  `{2, 4, 6, 8, 12, 16, 20}` x sigma_c rather than matching only RR's
  best-well-formed rung (hs20 dose 12).
- Q5 (rider secondary framing), RESOLVED (lead): pre-stated sign-map
  scoreboard structure. The Predictions scoreboard above carries dedicated
  slots for the llama placebo sign, the mistral RG1 pass/fail call, and
  whether the mistral fresh-seed random lifts land inside or outside the
  descriptive envelope; the SLOTS are registered here, and the actual CALLS
  are TODO-for-PI-and-lead, filled at sign.

## Outcome

Filled at resolve. Record the verdict, the gate results, and the one-sentence
summary that also goes into `verdict:` in the manifest.
