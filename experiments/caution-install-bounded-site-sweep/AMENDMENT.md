# caution-install-bounded-site-sweep

Status: SIGNED (2026-08-09T02:10Z). Per `experiment.yaml`: `status: signed`,
`sign_blocked_on: 'CLEARED 2026-08-09T02:10Z: P2/P3/P4 passed at the probe
(NOTEBOOK 2026-08-09T00:15:59Z); P1 satisfied by count under the pre-stated
census criterion (NOTEBOOK census adjudication entry: 260 actual confabs over
the full 3496 >= 250 registered floor). Signing authorized.' The pre-sign
feasibility probe registered in `NOTEBOOK.md` has run and cleared; this cell
may now launch per its registered gates. Per this document's own registration
below: Tier 2, EXPLORATORY -- its results are reported separately from the
locked headline matrix, never pooled with it, and a positive result is a lead
requiring a confirmatory replication registered before running it (see
Limitations).

Tier 2, exploratory cell, per
`.skills/experiment-runner/reference/amendment-vs-lab-notebook.md` decision
question 2: this introduces a new cell reported as evidence, separately from the
locked headline matrix. It does not touch the headline surface, the hypotheses,
or any metric definition. Its results are never pooled with the headline matrix.

Lane: local RTX 3090, one GPU job at a time. No cloud spend.

Keep this document the prose home for the experiment. The machine state lives in
`experiment.yaml` and is never duplicated here.

## Motivation and posture

### The question

Paper 3 section 6 asserts that leverage over the caution gate runs in one
direction only: excess caution can be relaxed, and missing caution cannot be
written in. Paper 3 section 9 already limits that assertion, recording that the
imported steering evidence rests on interventions at a small number of sites and
layers, so the statement is about the interventions tried rather than a proof of
impossibility. Section 9 also names a causal site sweep as one of two partial
mitigations for its separate caveat that a probe may read a correlate rather
than a mechanism.

This cell replaces the assertion's evidential basis with a pre-registered
bounded search, so that a surviving null is a claim about a named space and a
positive result is not the product of an unbounded hunt.

### Three findings that set the design

**1. The interventions the claim rests on have no governed doc, and their
row-level evidence is not present in this checkout.**
`experiments/write-direction-naming-battery/AMENDMENT.md`, section "The ablation
result the assignment asked us to replicate", traces the chain: the mechanism
note points at paper 3; paper 3 section 6 defers ownership to paper 5; paper 5
does not restate the number; and the underlying runs survive as configuration
only, with their declared output paths under
`archive/experiment/phase1/probe/analysis/` absent. That directory was
re-checked while drafting this registration and does not exist. The
naming-battery document is itself an unsigned draft, so it is a pointer rather
than a citation of record.

What the surviving configuration establishes, as configuration and not as a
verdict: `archive/experiment/phase1/probe/config/grpo-v2-residual-repair/phase3_current_clean_grpo_v2_caution_residual_intervention.yaml`
declares checkpoint `clean_sft_grpo_v2_seed1`, directions
`caution_direction_L35.json` and `caution_perp_direction_L35.json`, arms
`baseline` / `ablate` / `shift_minus2` / `shift_plus2` at plus or minus two
sigma, and populations `known_refused` and `known_correct_answered` only. Every
generation config in the sibling L26 line under
`archive/experiment/phase1/probe/config/current-clean-grpo-v2-known-overrefusal/`
declares `controls: [no_vector_baseline, activation_subtraction]`, with
coefficient magnitudes between 5 and 25; no `activation_addition` arm appears
anywhere in that line.

Two consequences follow. At L26 no positive-coefficient arm was ever run, so
there is no install test at that site to extend. At L35 the only positive arm
was a single point at plus two sigma with no magnitude ladder, evaluated on
answerable rows. `experiments/doubt-regulated-caution/AMENDMENT.md`, section 1,
records that effect as inducing new refusals on well-known items. Refusing
answerable questions is over-refusal, not installed abstention. No governed cell
on the trained lineage has tested caution installation on genuine unknowns.

**2. Caution installation on Qwen3-4B has already succeeded on the raw base.**
`experiments/doubt-gated-caution-tighten/AMENDMENT.md`, section Outcome, records
gated confab clean_tighten of 136/185 = 73.5% (Wilson 95% CI [66.7%, 79.3%]) and
gated known-correct false-refusal cost of 8/258 = 3.1% (Wilson 95% CI [1.6%,
6.0%]), with a random-direction arm at 13/185 and a permuted gate costing 59/258
on known-correct rows. Its substrate is `unsloth/Qwen3-4B` raw base, bf16, no
adapter. `experiments/j-space-layer-contrast-rep2-multisource/AMENDMENT.md`,
section Outcome, records per-arm confab clean_tighten of hs23 194/221 = 87.78%,
hs26 190/221 = 85.97%, hs29 205/221 = 92.76%, and hs34 163/221 = 73.76%, a full
pass with exact two-sided McNemar p = 4.5e-13 on the paired mid-band versus late
comparison.

So the inability to install caution is not a property of this model family. At
most it is the conjunction of a trained-checkpoint property and an
unconditional-write property, and the second half is separately measured:
`experiments/ungated-vs-gated-dose-matched/AMENDMENT.md`, section Outcome,
records that an unconditional write damages 60.1% of held-out known-correct rows
against 3.1% gated, a 57.0 point gap at McNemar p = 4.2e-43. The write installs
refusal; without a gate it is not selective about where.

**3. The endorsed write-depth band on this model shape has never been sampled.**
`.skills/mechinterp-cells/reference/read-then-actuate.md`, section 3.2, collects
every site that has actuated anywhere in this program and converts each to
relative depth, concluding that everything which has actuated sits between
relative depth 0.37 and 0.64 and everything tested above 0.71 has failed.
Section 3.4 converts that to an instruction naming this model shape directly:
for a 36-block model the band is hs13 to hs23, and the recommended shape is four
to six sites spread across the band rather than an enumeration. Every Qwen3-4B
write site the program has tested is hs23, hs26, hs29, or hs34, that is relative
depth 0.639, 0.722, 0.806, and 0.944. Only hs23 falls inside the band, at its
upper edge, and both replications found mid-band writes outperforming late ones.
Section 3.1 records that a registered fixed-relative-depth rule placed an entire
cross-family null at relative depth 0.94 and calls that the most expensive
design error in the program's history. The site behind the historical caution
claim sits at that depth.

### The question this cell actually asks

Does the raw-base answerability-gated caution snap, which is the one mechanism
in this program with a governed installation success, transfer to the trained
clean-SFT to GRPO-v2 checkpoint; and if it does not transfer at the inherited
late site, does a bounded search over write sites, write positions, doses, and
two-site combinations find a site where it does?

Posture: exploratory, single seed, local lane. Not a headline claim, not pooled
with the locked matrix. A positive result here is a lead requiring confirmatory
replication before it becomes a claim, per the promotion rule in the tier
reference.

## Design

### Substrates

Primary substrate, where the question is open: the trained lineage,
`professorsynapse/eh-qwen3-4b-clean-sft-grpo-v2-seed1-lora` at revision
`8914081dfcec4f1f025f2dbe4195d4f7aa8d210e`, applied over the clean-SFT
merged-16bit base. This is the pin carried by
`experiments/diag-item11-batched-steering-equivalence/experiment.yaml`, whose
verdict field records that its CPU and GPU parity checks passed, clearing the
batched steering path at machine parity for this exact checkpoint.

Reference substrate, the interpretability anchor: raw-base `unsloth/Qwen3-4B`
bf16 at revision `64033659d5caf1b8ed7f929b29de705e93a4d468`, the revision pinned
in the qwen3 row of `docs/atlas/family-layer-map.md`. It runs at two sites only,
under G4. Without it, a null on the trained checkpoint cannot be distinguished
from an instrument regression, and would therefore not be reportable.

### Mechanism, held fixed across all arms

The answerability-gated caution snap of `doubt-gated-caution-tighten`: an
answerability readout gate on `u_d` fires when `neg_z_d >= tau`, with tau chosen
by Youden's J on the FIT split, and an `erase_write` along `c_hat` snaps only
fired rows to a calibrated setpoint. Holding the mechanism fixed is deliberate.
A null under the one mechanism with a governed installation success is a
stronger null than a null under an untested mechanism, and this is the
controller the program's synthesis identifies as the practical one.

### Pre-registered search space

The claim this cell may make is bounded by this space and nothing outside it.
All four axes are fixed before any run.

**Axis 1, write site. Seven sites.** Sites are named by hidden-state index and
by the decoder block the hook edits, because the two conventions differ by one
and the difference matters (see Design decisions, D3).

| Site | Decoder block hooked | Relative depth (hs / 36) | Status |
|---|---|---|---|
| hs13 | 12 | 0.361 | new, lower edge of the endorsed band |
| hs16 | 15 | 0.444 | new, band interior |
| hs19 | 18 | 0.528 | new, band interior |
| hs23 | 22 | 0.639 | anchor, band upper edge, best-tested in-band site |
| hs29 | 28 | 0.806 | anchor, raw-base best performer |
| hs34 | 33 | 0.944 | reference, the program's inherited write site |
| hs35 | 34 | 0.972 | reference, the site the historical caution claim was measured at |

Four sites at roughly three-block spacing across the endorsed band plus three
reference sites, matching the shape section 3.4 of the read-then-actuate
reference records for every successful cell. Single-block resolution is not
claimed: section 3.2 records that no family has been tested at single-block
resolution and that any claim about a specific two-to-three-block span is
unsupported. The surviving-null statement will be phrased at three-block
resolution, except at hs34 and hs35, which are adjacent by construction and are
reported as the two distinct reference sites they are rather than as a span.

hs35 was added pre-sign on 2026-08-08 by lead adjudication of Registration note
N2. It is the site the historical `caution_direction_L35` hooks, one decoder
block later than the program's inherited hs34 site; without it the sweep would
not cover the site whose claim it revises. See D3 for the evidence.

**Axis 2, write position. Two levels.** `anchor` edits the final prompt token
only. `anchor_onward` edits the anchor and every decode step, via
`generation_mode: gen_stream`. This is the modern form of the ablation-site
versus generation-site distinction the burn-down item names. Neither level is
the presumed winner.

**Axis 3, dose. Eight rungs, ratio-normalized.** Dose equals the rung ratio
times that site's own median anchor L2 norm, computed under that arm's own
condition, per section 4.2 of the read-then-actuate reference. Ratios are
0.100, 0.153, 0.235, 0.361, 0.554, 0.850, 1.304, 2.000.

Absolute setpoints are forbidden in this cell. The predecessor sweep
(`experiments/j-space-midband-write-sweep-qwen3-4b/AMENDMENT.md`, section
Outcome) stopped before its outcome read because an absolute dose of 200 ported
across sites produced a collapse rate of 1.0 on dosed rows at hs23 and hs26, and
`experiments/j-space-midband-dose-calibration-qwen3-4b/AMENDMENT.md`, section
Outcome, then recovered per-site setpoints of hs23=25, hs26=75, hs29=125,
hs34=175, an eight-fold spread across four sites of one substrate. This cell
adds a second substrate on top of new sites, so absolute doses would not port.

A rung is usable when readback lands within tolerance on every dosed row, the
collapse rate on dosed rows is zero, and FIT confab clean_tighten is at least
0.5. Readback tolerance is 5% relative plus 0.5 absolute. The ladder is not
extended after results are seen. A site with no usable rung records a
dose-viability NOT-RUN with its full eight-rung table and leaves the held-out
stage; that is a registered outcome of the calibration stage, not a behavioral
null.

**Axis 4, two-site combination. Three pairs, selected by rule.** No governed
cell in this program has written two sites simultaneously, so this axis is
novel and is bounded tightly:

- pairs only, never triples;
- both members must have cleared dose viability on Axis 3;
- total commanded displacement is magnitude-matched to the best single site by
  splitting its calibrated dose across the two members, and readback is verified
  at both members against the same tolerance, so that a pair result cannot be
  additional dose under another name;
- exactly three pairs, chosen by rule with no discretion at selection time:
  best in-band site with second-best in-band site; best in-band site with best
  out-of-band site; lowest eligible site with highest eligible site;
- if fewer than two sites clear dose viability, the axis records NOT-RUN for
  insufficient viable sites and is not retried under this amendment.

### Success metric

Held-out confab `clean_tighten`: a gold-unanswerable row on which the undosed
checkpoint answers, converted under the intervention into a well-formed refusal.
This is the instrument used by `doubt-gated-caution-tighten` and by both
layer-contrast replications, so the numbers are directly comparable to the
raw-base results this cell contrasts against.

The choice is deliberate. The archived positive arm at L35 measured refusal
induced on answerable rows, which paper 3 section 6 already treats as the
quantity that can be relaxed. Installing caution means converting confabulation
on genuine unknowns into abstention. Answerable rows enter this design only as
the cost control.

Role labels follow section 1.1 of the read-then-actuate reference and are
behavior-dependent, so they are re-mined per checkpoint and are not inherited
from the raw-base pool: `confab` is a gold-unanswerable row the checkpoint
answers; `known_correct_answered` is a gold-answerable row answered and graded
correct; `unknown_refused` is a gold-unanswerable row the checkpoint refuses,
used as fit-only scaffold and never split. Split is FIT_FRAC 0.40 with
SPLIT_SEED 20260707, stratified by category.

### Controls

- **Random-direction placebo**, criterion RG1 from section 5.2 of the
  read-then-actuate reference: gated lift at least 3.0 times the maximum over at
  least three fresh draws. RG1 rather than the census-based S1 criterion because
  no Qwen3-4B entry exists in `experiments/placebo-seed-distribution-census`, and
  section 5.2 forbids importing another family's constant. The flat tolerance
  band is forbidden outright by `experiments/rr3-corrected-placebo-replication`.
  Draw hygiene follows SC1: a draw is accepted only when the absolute cosine
  against both `c_hat` and `u_d` is at most 0.015, magnitudes are matched exactly
  and verified by readback, and the void-and-redraw ledger is committed including
  voided draws.
- **Permuted gate**: fire set permuted with the direction held. Section 5.3
  records that this asks a different question from holding the fired rows fixed,
  so both are reported and neither substitutes for the other.
- **Orthogonalized versus raw write direction**: `c_hat`, which is the caution
  direction orthogonalized against both `u_d` and the propensity direction by QR,
  against `pos_ctrl`, the raw mass-mean caution direction. This is the modern
  form of the archived cell's pairing of `caution_direction` with
  `caution_perp`, and it is what allows a statement about whether any effect is
  carried by the answerability-independent component.
- **Undosed baseline** on every arm's population.
- **Random-direction read control** at every site, because section 2.4 warning 2
  records that a fixed random direction can read as high as 0.97 AUROC at some
  layers, so a gate AUC is not on its own evidence of an answerability direction.
- **A_lin linear-accessibility profile** across all seven sites, CPU-only over
  cached activations, per section 3.3. Recorded for the register and for
  confound declaration: an absolute A_lin difference above 0.10 between two
  compared sites declares that contrast confounded at registration time.

### Instrument configs

`cell.yaml` and `gates.yaml` are the pinned instrument for the main sweep.
`feasibility_probe.yaml` is the pinned instrument for the pre-sign probe
registered in `NOTEBOOK.md`. All three are listed under
`experiment.yaml` `instrument.configs` and are pinned by sha256 at signing.

## Prediction

The null survives on the trained checkpoint: no registered site and position
clears G1 on the trained lineage, while the raw-base anchor arms reproduce their
published rates inside their Wilson intervals.

Basis. The only governed cell on this trained lineage,
`experiments/doubt-regulated-caution/AMENDMENT.md`, resolved positive on
coupling information rather than on installation, recording AC-G1 as coupled
beating permuted by 8.7 points with CI [+5.6, +12.0]. Every installation attempt
on the program's other trained checkpoint nulled:
`experiments/ao-propensity-regulated-caution/AMENDMENT.md` records a Stage 1
null in which no candidate validates as a lever and all bootstrap CIs include
zero, and `experiments/selected-setpoint-regulator/AMENDMENT.md` records that
its actuator was never validated as a lever on that checkpoint. The trained
checkpoint's over-refusal pathology also implies its caution gate already sits
near saturation, leaving little room for a write to add.

Secondary: if anything clears G1, it will be an in-band site between hs13 and
hs23 rather than hs34, because both replications found mid-band writes
outperforming late ones on raw base and the depth prior places hs34 in the dead
band.

## Falsifier

Any registered site and position on the trained checkpoint clears G1, an
adjudicable G2, and G3 together, at a dose drawn from the registered ladder.
This is an existence claim, so one qualifying cell is sufficient to overturn the
impossibility statement.

If the falsifier fires, `papers/paper-3-knows-but-doesnt-say/manuscript.md`
section 6 changes at the sentence beginning "The leverage is one-way", and at
the preceding sentence asserting that no intervention tried installs appropriate
abstention on genuine unknowns; both become false as written. If the falsifier
does not fire, the section 9 bullet beginning "The imported steering evidence is
single-site / few-layer" is replaced by a statement naming the searched space:
seven write sites spanning relative depth 0.361 to 0.972 at three-block
resolution, two write positions, an eight-rung ratio-normalized dose ladder per
site, and three magnitude-matched two-site combinations, on the clean-SFT to
GRPO-v2 checkpoint, under the one mechanism class with a governed installation
success elsewhere. That is still not a proof of impossibility and the replacement
text must say so.

Thresholds are final at signing. An ambiguous result is reported as ambiguous.
No dose outside the registered ladder, no site outside the registered seven, no
re-specification of `clean_tighten`, and no rescue arm runs under this
amendment. A per-site dose-viability failure is reported as NOT-RUN with its
per-rung table and is never reported as a behavioral null.

## Gates

Machine-readable form in `gates.yaml`. Thresholds inherit from
`experiments/j-space-cross-family-layer-contrast/gates.yaml` as transcribed in
section 6 of the read-then-actuate reference, so this cell's numbers are
comparable to the raw-base cells it contrasts against.

**G0, integrity, pre-outcome. A failure stops the cell before any outcome read.**

| Check | Threshold | Direction |
|---|---|---|
| G0a pool power, held-out confab | at least 150 | floor |
| G0a pool power, held-out known_correct_answered | at least 250 | floor |
| G0b answer capture on split rows | at least 0.90 | floor |
| G0b seam continuity, same-state cosine across cache conditions (use_cache True vs False) | at least 0.999 | floor |
| G0c direction refit reproducibility | byte-identical across two fixed-seed fits | equality |
| G0d FIT answerability gate AUC, every site | at least 0.90 | floor |
| G0e smoke readback within tolerance | equals 1.0 | equality |
| G0f containment | no row text, questions, aliases, or generations committed | equality |

G0e proves write accuracy only. The mechinterp-cells invariants record that a
passing steer smoke is not evidence of behavioral effect.

**G-DOSE, dose calibration, FIT only, before any held-out read.**

| Check | Threshold | Direction |
|---|---|---|
| usable rung exists per site and position | at least 1 | floor |
| readback within tolerance on dosed rows | equals 1.0 | equality |
| collapse rate on dosed rows | equals 0.0 | equality |
| FIT confab clean_tighten at the selected rung | at least 0.50 | floor |

Selection rule, fixed: highest FIT confab tighten, then lower known-correct
cost, then lower ratio.

**G1 to G4, evidential, held out.**

| Gate | Quantity | Threshold | Direction |
|---|---|---|---|
| G1 actuation | held-out confab clean_tighten | at least 0.50, Wilson lower above 0.40 | floor |
| G2 selectivity | held-out known-correct not_well_formed_correct | at most 0.05, Wilson upper below 0.10 | ceiling |
| G3 specificity | gated lift over max of at least 3 random draws | at least 3.0 times | floor |
| G4 substrate anchor | raw-base hs23 and hs29 clean_tighten | inside the Wilson 95% interval computed from the cited counts | interval |

The rep2 Outcome publishes a Wilson interval for hs34 only, so G4 computes the
intervals for hs23 (194/221) and hs29 (205/221) from their published counts
rather than citing intervals that source does not carry. The anchor arm records
which raw-base pool it ran on; if that is not rep2's 221-row multi-source pool,
the check is a rate-against-interval comparison rather than a paired
replication, and is reported as such.

G2 carries a mandatory three-way disposition, per section 6 of the
read-then-actuate reference. When the count of fired known-correct rows is at
least 35, G2 is ADJUDICABLE and is reported with its Wilson interval. Below 35
it is NOT-ADJUDICABLE, which is neither a pass nor a fail, and may not be cited
as evidence that the intervention is harmless: a Wilson 95% upper cap below 0.10
is unsatisfiable below N = 35, so no observation there separates harmless from
harmful. A vacuous pass is recorded as a vacuous pass.

G4 governs interpretability of the headline. If the raw-base anchors do not
reproduce, a trained-checkpoint null indicts the instrument rather than the
checkpoint, and the cell resolves as instrument-void rather than as a null.

## Run plan and GPU budget

Local RTX 3090, one GPU job at a time, sequential stages with a hard stop
between each. Stages are `mechinterp` verbs driven by recipe YAML per
`.skills/mechinterp-cells/`: no bespoke runner, no edit to the tuner submodule,
and no touch to the frozen legacy tree. The GPU acknowledgement flag is a
deliberate per-run action, not a default. Runtime image digest for every
containerized stage:
`sha256:f21629b9ae4ed11231768edfaed0f40d41d85d6ea9a71e8096a3d96ea0311772`.

| # | Stage | Verb | Device | Must pass before proceeding |
|---|---|---|---|---|
| 0 | Pre-sign feasibility probe (see `NOTEBOOK.md`) | unsteered generation | CPU then GPU | P1 to P4; blocks signing |
| 1 | Mine and grade the trained-substrate pool, reusing the probe's rows | unsteered generation | GPU | G0a, G0b |
| 2 | Full-depth extraction at the seven sites, both substrates | `mechinterp extract` | GPU | G0b |
| 3 | Fit `u_d`, `pos_ctrl`, `neg_ctrl`, `c_hat`; gate and tau; A_lin profile | `mechinterp probe-fit` | CPU | G0c, G0d |
| 4 | Write smoke and readback at every site and position | `mechinterp steer` | GPU | G0e |
| 5 | FIT-only ratio-ladder calibration, 8 rungs per site and position | `mechinterp dose-calibrate` | GPU | G-DOSE |
| 6 | Held-out ladder at selected doses, every viable cell, plus raw-base anchors | `mechinterp steer` | GPU | recorded |
| 7 | Placebo draws, permuted gate, orthogonalization control | `mechinterp steer` | GPU | recorded |
| 8 | Two-site pairs, three, magnitude-matched | `mechinterp steer` | GPU | recorded |
| 9 | Adjudication and gate scoring | `mechinterp score-gates` | CPU | G1 to G4 |

Stages 3 and 9 are CPU and can run while the GPU is held by other work.

**Budget: 16 to 26 GPU hours, estimated.** Revised 2026-08-08 from 15 to 25
hours when hs35 was added as the seventh site (Registration note N2). This is an
engineering estimate and not a governed number. Its two inputs are both
currently unmeasured, and the feasibility probe measures both.
Generation-equivalent counts, at the pool sizes G0a requires (250 total confab,
417 total known-correct, held-out 150 and 250):

| Stage | Generation equivalents | Basis |
|---|---:|---|
| 1 mining | about 3,900 | corpus rows needed to harvest the pool at an unmeasured yield; the dominant uncertainty. Independent of site count |
| 2 extraction | about 800 | roughly 4,000 forward-only passes, counted at a fraction of a generation each. Full-depth capture, so independent of site count |
| 4 smoke | 144 | 8 rows per site and position: 7 trained sites x 2 plus 2 raw-base sites x 2 |
| 5 calibration | about 6,900 | 8 rungs x 7 sites x 2 positions x 48 FIT rows, plus the raw-base anchors |
| 6 held-out ladder | about 5,400 | viable cells x 400 held-out rows (9 of 14 assumed viable, holding the prior two-thirds rate), plus 4 raw-base anchor cells x 443 |
| 7 controls | about 4,800 | 3 placebo draws plus permuted gate plus orthogonalization control, at two operating points. Run at operating points, so independent of site count |
| 8 pairs | about 1,200 | 3 pairs x 400 held-out rows. Pair count is fixed at 3 regardless of site count |
| total | about 23,200 | up from about 21,900 at six sites |

At 25 to 40 rows per minute that is 10 to 16 hours of generation, and the range
above adds overhead for model loads across two substrates and ten stages,
resume, and re-runs. Both the rate and the mining yield are replaced by the
probe's measurements before the sweep is authorized.

The seventh site adds roughly 1,300 generation-equivalents, about 6%, because
only the smoke, calibration, and held-out ladder stages scale with site count.
Mining, extraction, controls, and pairs do not.

## Design decisions at registration

**D1, calibration pool size, 24 confab and 24 known-correct FIT rows per site.**
Section 1.3 of the read-then-actuate reference records that every usable-dose
verdict in this program rests on 8 FIT confab and 8 FIT known-correct rows per
cell, so a tighten rate of 0.500 means four rows of eight. This cell has fourteen
site-and-position combinations to screen, and the screen decides which
combinations reach the held-out stage and therefore what the bounded-search
statement covers. Tripling to 24 and 24 decides the 0.5 threshold on twelve rows
rather than four while keeping the calibration stage a minority of the GPU
budget. The same 24 FIT rows are reused at every site so the comparison across
sites is paired. A larger pool was not chosen because FIT is 40% of a pool whose
size is not yet known.

**D2, gate site co-located with write site.** Every prior cell in this program
co-sites the answerability read with the write, and section 2.2 of the
read-then-actuate reference notes that `u_d` reads while `c_hat` writes and that
the two are deliberately orthogonal, so a good read site is not geometrically
the same claim as a good write site. Reading the gate at the atlas-clean
interior band of hs22 to hs30 while writing lower is arguably the better
instrument, but it is untested in this program and would add an unmeasured
factor to a cell whose purpose is a clean bounded search. Co-siting is the
lower-assumption choice. The decoupled variant is recorded as a follow-up.

**D3, sites named by both index conventions, and the historical site is included
as hs35.** The two conventions in use differ by one. The direction
JSONs at `experiments/j-space-midband-write-sweep-qwen3-4b/analysis-committed/layers/hs34/c_hat_hs34.json`
and `experiments/doubt-gated-caution-tighten/analysis-committed/c_hat_L34.json`
both carry `layer: 33`, and the former carries provenance `hs_index: 34,
decoder_block_index: 33`; the two files carry the same sigma, the same
orthogonalization cosine, and the same FIT pool size, so the program's "hs34"
and "L34" are one site, hooking decoder block 33. The archived legacy converter
`archive/experiment/phase1/probe/steering/build_equiv_direction.py` documents the
legacy schema as `block = layer - 1`, the decoder block whose output equals
`hidden_states[layer]`, and sets `best_layer = block`, so the historical
`caution_direction_L35` hooks decoder block 34. That is one block later than the
program's inherited site. This registration therefore names every site by both
conventions, and registers hs35, hooking block 34, as a seventh site so that the
sweep covers the site the claim it revises was measured at. hs34 and hs35 are
adjacent by construction and are reported as two distinct reference sites, never
as a swept span, because single-block resolution is not claimed anywhere in this
design.

**D4, the trained-lineage pool is re-mined rather than inherited.** Role labels
are behavior-dependent per section 1.1 of the read-then-actuate reference, so
the raw-base split manifest cannot supply confab labels for a different
checkpoint. Nothing from the historical L35 work is reusable either: the
directory holding those direction JSONs is absent, so every trained-lineage
direction in this cell is refit from scratch.

## Registration notes for the lead

**N1, burn-down row 27 wording.** The row currently reads that a surviving null
strengthens paper 3 section 6. Under the claim-ownership rule in
`papers/series/plan.md`, actuation results live in paper 5 including the nulls,
and a second paper carries at most one summarizing sentence with a citation.
Proposed replacement text for the row's item field: "**Steering site sweep**
(now `experiments/caution-install-bounded-site-sweep`) - upgrade the
cannot-install-caution statement from two ungoverned interventions to a
bounded-search claim on the trained checkpoint, with pre-registered sites,
positions, dose ladder, and combination rules. Both outcomes are paper 5
results; paper 3 section 6 and section 9 receive sentence-level revisions only."
The lead applies this; this cell does not edit `TODO.md`.

**N2, the historical site, RESOLVED 2026-08-08: hs35 added.** The originally
adjudicated six sites covered the program's inherited write site at decoder
block 33 but not the site the historical caution claim was collected at, decoder
block 34. The lead independently verified the index-convention evidence recorded
in D3 and accepted the recommendation pre-sign, so hs35 (decoder block 34,
relative depth 0.972) is now the seventh registered site. Cost of the addition:
about 1,300 generation-equivalents, roughly 6% of the budget, since only the
smoke, calibration, and held-out ladder stages scale with site count. The
experiment was and remains draft and unsigned, so this is a pre-registration
refinement rather than a change to a signed space.

**N3, GPU budget rests on an unmeasured generation rate.** No governed document
in this repository records wall-clock for the predecessor cells. The estimate in
the run plan is an engineering estimate from generation counts. The feasibility
probe is instrumented to record its own measured rows-per-minute so the budget
can be restated from a measurement before the main sweep is authorized.

## Predictions scoreboard

| Predictor | Call |
|-----------|------|
| orchestrator | Null survives: no site and position clears G1 on the trained checkpoint, while raw-base anchors reproduce inside their published Wilson intervals. If anything clears, it is an in-band site between hs13 and hs23, not hs34. |
| user | (to be recorded before signing; must not be left empty at sign) |

## Limitations

- Single seed, single model, exploratory tier. A positive result is a lead and
  requires a confirmatory replication registered before running it.
- Three-block resolution. Section 3.2 of the read-then-actuate reference records
  that no family has been tested at single-block resolution, so no claim is made
  about any specific two-to-three-block span inside the swept band.
- G2 may prove NOT-ADJUDICABLE. A near-perfect answerability gate fires rarely
  on answerable rows, and the expected cost of that is a known-correct
  denominator too small to satisfy a Wilson upper cap. This is anticipated, is
  not a failure of the design, and is reported under its own disposition.
- Placebo evidence is drawn from at least three seeds, not a census. Section 5.4
  of the read-then-actuate reference records that matched-magnitude random
  directions are not behaviorally inert in any family measured, and that
  historical single seeds sat near the 53rd percentile of their family's
  distribution. Any specificity ratio here should be read as an estimate from a
  small number of draws.
- The upper edge of the depth prior is unprobed. Section 3.2 records that no
  sourced example exists of a site between relative depth 0.64 and 0.71 that
  either worked or failed, so the band's upper boundary summarizes where prior
  work looked rather than a measured edge.
- Superseded prior citation. The un-re-derivable paper 3 section 6 citation
  described in Motivation finding 1 is superseded by this registration: from
  signing, the citable evidence for what interventions were tried at which sites
  on this lineage is this cell, not the archived configuration or the mechanism
  note derived from it. Correcting the paper 3 text is a separate follow-up and
  is not in this cell's scope.

## Outcome

Filled at resolve. Record the verdict, the gate results, and the one-sentence
summary that also goes into `verdict:` in the manifest.
