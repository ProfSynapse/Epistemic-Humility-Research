# Write-direction naming battery: what is the mid-band c_hat write, behaviorally?

Status: DRAFT (not signed; do not launch as confirmatory evidence). Drafted
2026-07-30 under a lead design assignment. Signing is lead-only with explicit
PI approval. Two disclosures below (section "Prior reads that broke blinding")
must be adjudicated by the PI before this draft can be signed, because they
change what this cell is allowed to pre-register.

Keep this document the prose home for the experiment. The machine state lives in
`experiment.yaml` and is never duplicated here.

## Motivation and posture

The program has already retired one mentalistic name by experiment rather than
by taste. `docs/research/margin-theory-framework.md` section 3 records the
rename table (doubt direction to known-unknown direction; doubt gate to KU
readout gate; caution write to boundary push) and states the earnability
criterion: a mentalistic name is earned for an activation when it (a) tracks
actual ignorance, (b) drives abstention when amplified, (c) does so
direction-specifically, and (d) responds to evidence the way the named state
should. Criterion (d) was adjudicated by the M4 arc and is NOT earned:
`experiments/margin-evidence-responsiveness-worldknown/AMENDMENT.md` (Outcome,
verdict sentence) records that the named KUQ direction does not fire on the
world-known error class at all (baseline confab-vs-correct AUROC 0.3018,
bootstrap 95% CI [0.2647, 0.3396], against a 0.70 firing floor; primary test
VOID, out of domain), that the reversal is real and not a harness artifact, and
that the direction "reads as unanswerability recognition plus a separate weak
evidence-registration."

That adjudication was about the READ direction. This cell applies the same
discipline to the WRITE. The write is currently called the "caution" direction
or the "caution snap" in the older governed docs, and "boundary push (dosed
write)" in the new vocabulary. Neither name has been earned by a behavioral
characterization of what the write actually does. The PI's stated prior is that
"caution" is wrong and that the honest candidate is an abstention /
I-don't-know actuator. This cell is built to make that a decidable question,
and its deliverable is a pre-stated outcome-to-name mapping table that is
exhaustive over the outcome space, so the name is fixed by the result rather
than chosen after it.

Posture: exploratory instrument/mechanism tier, one substrate, reported
separately. It is never pooled with the locked Phase 1 headline matrix and it
cannot move any locked verdict. It adjudicates a NAME, not an effect.

### What is already governed, and what it constrains

Every fact in this subsection was read from the cited doc for this draft.

1. **The mid-band write converts confabulations to clean refusals, held out.**
   `experiments/qwen35-4b-midband-heldout/AMENDMENT.md` (Outcome, resolved
   2026-07-13, shape A): on the untouched Qwen3.5-4B held-out pool, the frozen
   hs20 operating point produced fired-confab refused 872/1286 = 0.678 (Wilson
   95% [0.652, 0.703]) with well-formed 1256/1286 = 0.977 and known-correct
   false refusal 14/360 = 0.039. Placebo legs held: random_direction was a
   no-op (confab refused delta +0.008 vs baseline) and permuted_gate known
   false refusal 0.056 was strictly worse than gated 0.039.
2. **The write self-sorts at mid-band; the gate is a deployment limiter.**
   `experiments/qwen35-4b-midband-doubt-snap/AMENDMENT.md` (Outcome, binding
   scope statement 3): in the permuted-gate control, randomly selected dosed
   confabs refuse at 0.669 versus the gated arm's 0.684, while directly dosed
   knowns refuse at only 0.056; "the gate's operational role is limiting how
   many knowns get dosed (13 vs 197 at hs20), not creating the refusal
   selectivity." The same Outcome's scope statement 4 records that the
   magnitude-matched random-direction placebo produces about 0 refusal (0.005
   at the G1 cell), so refusal is direction-specific.
3. **The gate axis is falsified in both families.**
   `experiments/gate-contribution-factorial/AMENDMENT.md` is cited by the
   framework (section 1, anchor 3) for held-out Gap_Sel(c_hat) 0.148 qwen (CI
   [0.119, 0.177]) against a registered 0.20 floor, with permuted-gate confab
   abstention 0.550 qwen versus baseline 0.083.
4. **The cost gate's low number is a targeting artifact, not write safety.**
   Same doubt-snap Outcome, binding scope statement 1: the 0.042 system-level
   false refusal on knowns is low because the gate fires on only 13/240 knowns
   AND the write spares most knowns; "of the 13 knowns the gate does fire on,
   77% (10/13) are falsely refused. The snap is not safe to apply to a known
   item."
5. **Base checkpoints barely refuse, so a negative-dose arm on base has a floor
   trap.** Confirmed here: in the M1 ladder's own baseline pass over this
   substrate and render, known-correct refusal is 0.000/360 and confab refusal
   0.035/400
   (`experiments/margin-mapping/analysis/runlog/qwen35_4b__baseline_reused.jsonl`,
   recomputed 2026-07-30). Independently,
   `papers/paper-3-knows-but-doesnt-say/manuscript.md` (section 5, "Caution is a
   trained-checkpoint construct") states that on the 1,233-question
   known/unknown surface of the base-model readout the raw base "refused zero
   questions, so there is no base-model caution direction to fit." A negative
   dose on an undosed base population has nothing to relax. The design below
   solves this without a trained checkpoint.

### Substrate correction (a design fact the assignment had inverted)

The assignment proposed "qwen3-4b base for positive arms (the best-instrumented
substrate)". The docs do not support that. The mid-band self-sorting evidence
and the only held-out promotion both sit on **Qwen/Qwen3.5-4B at hs20**, not on
Qwen3-4B. The Qwen3-4B/L34 lineage
(`experiments/doubt-gated-caution-tighten/`, `experiments/ungated-vs-gated-dose-matched/`)
runs at dose 200 in what the framework (section 2, Claim 2) classifies as the
**overdrive regime**, where "everything crosses, or degrades" and the write is
non-selective: ungated dose-matched dosing there damages 60.1% of held-out
known-correct rows versus 3.1% gated. Characterizing the write at an operating
point where it is already known to be non-selective would answer a different
question. This cell therefore runs entirely on Qwen3.5-4B / hs20 / reference
dose_abs 12.608, the operating point that carries the held-out claim. No
Qwen3-4B arm is proposed.

### The ablation result the assignment asked us to replicate

The assignment cited the KG mechanism note
`library/concepts/mechanisms/caution-residual-ablation-relaxes-overrefusal-asymmetrically.md`
(over-refusal 0.994 to 0.030 on ablation). Tracing it to a governed source
found a provenance problem the PI should know about before this cell claims to
replicate anything.

- The note's `supported_by` edge points at `paper:internal-paper3`.
  `papers/paper-3-knows-but-doesnt-say/manuscript.md` section 6 states the
  number twice but explicitly **defers ownership**: "Testing that prediction by
  steering is actuation work, and it belongs to the companion actuation paper
  ... which establishes the result this paper's argument needs."
- `papers/paper-5-actuation/manuscript.md`, the named companion, does **not**
  currently restate the number; a scoped search for 0.994 / 0.030 / the
  ablation prose returns no hit there.
- `papers/series/plan.md` line 55 records this exact gap as a pending ownership
  move: the result is currently argued inline in paper 3 under "census flag A3"
  and is slated to move to paper 5.
- The underlying runs survive as **configuration only**:
  `archive/experiment/phase1/probe/config/current-clean-grpo-v2-known-overrefusal/phase3_current_clean_grpo_v2_known_overrefusal_native_l26_coeff_sweep.yaml`
  and the sibling `..._caution_perp_residual_intervention.yaml`. Their declared
  `output_root` and `probe_results` paths under
  `experiment/phase1/probe/analysis/` do not exist in this checkout, so the
  row-level evidence is not locally re-derivable. The checkpoint is
  `clean_sft_grpo_v2_seed1` with `caution_direction_L35.json`; that sweep config
  targets L26.

**Consequence for this design.** The 0.994-to-0.030 result is a different object
from this cell's write direction. It ablates a **caution direction fit on a
trained, over-refusing Qwen3-4B checkpoint** by a refuse-versus-answer contrast
among knowns, at L35/L26. This cell's c_hat is fit on a **raw Qwen3.5-4B base**
by a KUQ confab-versus-refused contrast at hs20. Different vector, different
model, different layer. Arm B below is therefore registered as an **analogue,
not a replication**, and this draft does not claim to reproduce that number.
Flagged for PI: the mechanism note reads as a program-wide fact, but its
source-of-record is currently paper 3 prose citing an un-re-derivable dataset.

## Prior reads that broke blinding (mandatory disclosure)

While probing instrument feasibility for this draft, the drafter computed
outcome-relevant quantities from the M1 ladder's on-disk row logs
(`experiments/margin-mapping/analysis/runlog/qwen35_4b__*.jsonl`, gitignored,
11 files x 760 rows, each carrying `answer_text`). These numbers are now known
to the drafter and to the lead, so **they cannot be pre-registered as blind
predictions in this cell.** They are recorded here as INPUTS. The recomputation
script and exact per-rung values go into `NOTEBOOK.md` at sign.

**Disclosure D-1: the dose-response shape for refusal is already measured, and
it is graded, not a snap.** Over the M1 rungs (multipliers of dose_abs 12.608),
confab wide-detector refusal runs 0.035 (baseline), 0.150, 0.185, 0.268, 0.450,
0.580, 0.655 (1.0x), 0.710 (1.5x), then 0.000 at 2.0x with 1.000 degenerate.
The transition is smooth and monotone across a factor of 16 in dose. **Arm A
therefore cannot be registered as "graded versus binary snap" for refusal; that
question is answered.** Arm A is re-scoped to the unmeasured question of whether
the intermediate-dose behavior is *epistemically* graded (hedging,
qualification, explicit non-answerability) or merely *degraded* (unmarked wrong
answers).

**Disclosure D-2: the cost profile on knowns is dominated by silent wrongness,
not abstention.** Over the same rungs, known-correct rows dosed **ungated** show
correctness 0.983, 0.967, 0.964, 0.938, 0.875, 0.782, 0.673 (1.0x), 0.369
(1.5x), while their refusal rate only reaches 0.069 at 1.0x and 0.106 at 1.5x,
with well-formedness still 0.983 at 1.0x. At the registered setpoint the write
destroys roughly 31 points of known-correct accuracy while converting under 7
points to abstention. This is the opposite decomposition from the Qwen3-4B/L34
overdrive result, which `experiments/ungated-vs-gated-dose-matched/AMENDMENT.md`
(per framework section 2) decomposes as 55.8pp false refusal versus 3.9pp
answered-wrong. This is a substantive, previously unreported dissociation and it
is the single most name-relevant fact the drafter encountered.

**Disclosure D-3: the difficulty contrast was computed on the M1 known rows.**
Joining the 133 PopQA known rows to `datasets/popqa/test.jsonl` `s_pop`
(100% join coverage, id namespace verified) and splitting at the within-pool
median s_pop = 680 gives, at the 1.0x rung: rare half n=67, now-wrong 26/67 =
0.388, refused 13/67 = 0.194; popular half n=66, now-wrong 17/66 = 0.258,
refused 6/66 = 0.091. **Arm C cannot be pre-registered on the M1 rows.** It is
re-registered below on a fresh, larger, never-dosed PopQA known population, as a
confirmatory test of this disclosed exploratory read.

**Disclosure D-4: the abstention the write produces is narrow.** The gap between
the wide detector (`refused_v2`, detector_v2 diverse idioms) and the narrow
detector (`semantic_refuse`, literally `"i don't know" in answer_value.lower()`,
`experiments/doubt-snap-cross-family-confirmatory/gen_lib.py:117`) on dosed
confabs is at most +0.040 (at 0.25x) and is negative (-0.033) at 1.5x. The
write's abstention is essentially all literal "I don't know". **Arm D cannot be
registered as "narrow versus semantically varied abstention" on the existing
pattern instruments**; it is re-scoped to the unmeasured question of whether a
third form class exists that BOTH detectors miss.

**Feasibility probe (instrument characterization, disclosed).** A seeded sample
of 18 intermediate-dose rows was read to confirm the Arm A taxonomy has
referents. It does: dosed confabs that neither refuse nor degenerate include
forms like "cannot be answered with a single fact because it depends on specific
data" (a non-answerability assertion with no IDK token, scored
`refused_v2 = False` by both detectors), while knowns that lose correctness
produce bare unmarked substitutions ("Kazan", "1900", "York") and confident
false biographies. No aggregate form rate was computed. The taxonomy's class
boundaries were fixed after this read and are frozen in this draft.

**Governance ask.** The PI must decide whether these disclosures are acceptable
as declared inputs (drafter's recommendation: yes; they are recomputations of a
resolved cell's committed-lineage exhaust, and declaring them is strictly better
than pre-registering questions already answered), and whether the M1 exhaust may
be cited as evidence given that M1 itself resolved `falsified` on its own
separation criterion. Note that M1's construct-integrity gate C1 PASSED
(detector-versus-adjudication disagreement 20/700 = 0.029 against a 0.05
ceiling), so the ladder's grading is validated even though Claim 1 was falsified
(`experiments/margin-mapping/AMENDMENT.md`, Outcome, C1).

## Design

### Frozen operating point (nothing refit)

Every quantity is loaded byte-identically from the resolved doubt-snap ladder's
committed artifacts, exactly as `qwen35-4b-midband-heldout` did. This cell fits
no direction, fits no gate, and recomputes no standardization scalar.

| Quantity | Value | Source |
|---|---|---|
| Substrate | `Qwen/Qwen3.5-4B`, bf16, rev `851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a`, no adapter, no quantization | doubt-snap / heldout Design |
| Write layer | hs20 (decoder block 19) | `qwen35-4b-midband-doubt-snap/analysis-committed/build_manifest.json` `layers.hs20.hs_index` |
| Write direction `c_hat` | frozen unit vector, dim 2560 | `.../directions/hs20/c_hat.json` |
| Placebo `random_direction` | frozen unit vector, dim 2560 | `.../directions/hs20/random_direction.json` |
| Snap standardization | mu_c -4.031343053353048, sigma_c 1.576023489724997 | same build_manifest hs20 block |
| Reference dose (1.0x) | dose_abs 12.608187917799976 = 8 x sigma_c | heldout Design; `margin-mapping/harness/config.py:81-83` |
| Snap law / position | `erase_write`, `anchor_onward` | doubt-snap `cell.yaml` `snap` |
| Render / anchor | `doubt-snap-cross-family-confirmatory` `render.py` BASELINE_SYSTEM_PROMPT + chat template, `enable_thinking=False`, anchor at `prompt_len - 1` | ladder Stage B convention |
| Generation | greedy, min_new_tokens 1, max_new_tokens 200, EOS incl. im_end | ladder `cell.yaml` `generation` |
| Grading | per-cell byte-for-byte port of `grader.py` + `gen_lib.py` + `detector_v2.py` + `detector_v2_patterns.yaml` | repo convention; each experiment owns its copy |

**No gate anywhere.** Every row in every arm is dosed. The gate's role is
deployment targeting (governed fact 2 above); gating here would censor exactly
the rows the naming question needs.

**Negative dose is well defined under this law.** `erase_write` erases the
component along the readout and writes a setpoint, so a negative dose is the
setpoint -12.608, a definite negative projection, not an unbounded subtraction.
Realized-projection readback is gated on the negative target the same way the
positive arms are gated on +12.608.

### Populations (three, all disjoint from each other and from prior dosing)

All three are drawn from artifacts already committed on main, with an ID-only
manifest committed before any generation and no question, alias, or answer text
under `analysis-committed/`.

- **P-CONFAB (Arm A).** 400 rows drawn by seeded permutation from the 932
  held-out KUQ confabs that `qwen35-4b-midband-heldout` scored at 1.0x but that
  M1 did **not** subsample (1,332 held-out confabs per that cell's Outcome,
  minus M1's 400-row subsample). Fresh at every fractional dose.
- **P-REFUSE (Arm B).** The 421 rows with `role == refused_on_answerable` in
  `experiments/margin-evidence-responsiveness-worldknown/analysis-committed/census/qwen35_4b_worldknown_census.jsonl`
  (committed, 14,267 rows, text-free). These are natural refusals on answerable
  PopQA questions produced by this exact substrate under this exact render, so
  Arm B needs no trained checkpoint, no prompt change, and no direction refit.
  Gold answers exist for every row, so refusal release can be scored for
  specificity.
- **P-KNOWN (Arm C).** 600 rows drawn by seeded permutation from the 2,744
  `correct_on_answerable` rows of the same census, stratified 300/300 by a
  median split on PopQA `s_pop` computed over that 2,744-row pool and **frozen
  before any generation**. Never dosed by any cell. Disjoint from the 133 PopQA
  rows used in disclosure D-3.

### Arms and generation budget

Local RTX 3090, batch_size 8, base conda `/home/profsynapse/miniconda3/bin/python3`
(the `qwen3_5` loader needs transformers >= 5.x; the pinned `unsloth_env` at
4.57.1 does not recognize the architecture; this is the documented
deviation-with-cause carried from the ladder and the held-out cell, not a silent
substitution). Throughput 21.0 generations/min measured on this substrate at
this batch size (`qwen35-4b-midband-heldout/AMENDMENT.md`, Lane and cost).

| Arm | Population | Doses (x reference) | Generations | Est. |
|---|---|---|---|---|
| A: form ladder | P-CONFAB 400 | 0 (baseline), 0.25, 0.5, 0.75, 1.0 | 2,000 | 1.6 h |
| A-placebo | P-CONFAB 400 | random_direction at 0.5, 1.0 | 800 | 0.6 h |
| B: negative dose | P-REFUSE 421 | 0, -0.5, -1.0, -2.0 | 1,684 | 1.3 h |
| B-placebo | P-REFUSE 421 | random_direction at -1.0 | 421 | 0.3 h |
| C: difficulty | P-KNOWN 600 | 0, 1.0 | 1,200 | 1.0 h |
| **Total** | | | **6,105** | **4.8 h** |

Budget **6 to 8 GPU-hours end to end** on the local 3090 including anchor
capture, model load, and the mandatory dosed smoke. Arm D consumes Arm A's
generations and costs no additional GPU time.

Positive dose rungs stop at 1.0x because the M1 ladder measured total
well-formedness collapse at 2.0x in both roles
(`experiments/margin-mapping/AMENDMENT.md`, Outcome: "total well-formedness
collapse at the 2.0x rung (25.216) in both roles"), and 1.5x already carries
0.111 degenerate on knowns. Rungs above 1.0x would buy only collapse. The
negative side extends to -2.0x because no collapse boundary has been measured
there and the arm needs headroom to find one.

### New instrument: the output-form taxonomy (the one real cost line)

Everything else is reuse. The taxonomy is new and is the only module this cell
must build. Confirmed absent from the existing stack: `grader.py`, `gen_lib.py`,
and `detector_v2.py` carry only binary refused/answered/correct/degenerate plus
`matched_pattern_ids`; there is no hedging, qualification, or partial-answer
predicate anywhere in the program.

Five mutually exclusive, jointly exhaustive classes, assigned in priority order
so every generation lands in exactly one:

| Class | Definition | Instrument |
|---|---|---|
| **F5 degenerate** | `is_degenerate` fires (empty, no alnum, repeated n-gram) | existing |
| **F4 explicit IDK** | `semantic_refuse` or `refused_v2` fires | existing |
| **F3 non-answerability assertion** | answers neither, but asserts the question cannot be answered, has no determinate answer, or depends on unavailable specifics, without an IDK idiom | **NEW** |
| **F2 hedged assertion** | supplies a candidate answer carrying an explicit epistemic qualifier or scope limitation | **NEW** |
| **F1 committed assertion** | supplies a candidate answer with no epistemic marking | remainder |

Build: one `form_taxonomy.py` plus a versioned `form_patterns.yaml`, both pinned
at sign. Validation is not optional: a **blinded adjudication slice** following
the M1 / M4-WK CG1 pattern (n = 200 stratified across arms and doses, pool hash
committed before grading, graded hash committed before unblind, isolated
adjudicator sees only opaque_id and generation text). Registered acceptance:
detector-versus-adjudication disagreement <= 0.05 on the F1/F2/F3 boundary, and
clear-positive decoy agreement >= 0.60 with a minimum of 25 decoys, mirroring
M1's C1 floors. **If the taxonomy fails its calibration slice, Arms A and D are
instrument-void and no name is earned from them**; Arms B and C are unaffected
because they read only existing validated fields.

Estimated build cost: one CPU-only harness assignment plus about 200 rows of
isolated-adjudicator labeling. No GPU.

### Reused instruments (no new build)

Frozen directions and standardization scalars, the render module, `grader.py` /
`gen_lib.py` / `detector_v2.py` / `detector_v2_patterns.yaml`, and the
random-direction placebo construction (`unit(rng.normal(size=hidden_dim))`, the
same construction `direction_fit.fit_directions` uses, per
`experiments/placebo-seed-distribution-census/direction_draw.py`). Placebo is
reimplemented per cell by repo convention rather than imported. `s_pop` is
joined from `datasets/popqa/test.jsonl` by numeric id; note for the record that
`experiments/margin-evidence-responsiveness-worldknown/harness/census.py` line
17 promises `s_pop` in its gitignored sidecar and the sidecar does not carry it,
so the join must target the dataset file, not the census.

## The naming table (the deliverable)

Three axes, each resolved by one arm against a numeric gate. The table is
exhaustive over the 2 x 2 x 2 outcome space; two override rules and an
instrument-void row close the remainder, so no result can land outside it. The
name is fixed here, before the run, and does not move.

**Axis G (Arm A, form gradedness).** GRADED if the combined F2+F3 share among
non-degenerate P-CONFAB generations exceeds 0.15 at one or more intermediate
doses (0.25x, 0.5x, 0.75x) AND exceeds its own baseline share by at least 0.10.
Otherwise BINARY: the write moves rows from F1 to F4 without passing through a
marked intermediate form.

**Axis B (Arm B, directionality).** BIDIRECTIONAL if negative dosing reduces
P-REFUSE refusal by at least 0.20 absolute at some negative rung with Wilson 95%
CI excluding zero, AND the release is specific (among released rows, the share
scored `correct_v2 == True` is at least 0.30), AND the random_direction placebo
at -1.0x moves refusal by less than 0.05. Otherwise POSITIVE-ONLY.

**Axis K (Arm C, what the write tracks on knowns).** DIFFICULTY-TRACKING if the
rare half's loss-of-correctness rate exceeds the popular half's by at least 0.10
absolute with a bootstrap 95% CI excluding zero. Otherwise KNOWLEDGE-STATE
(difficulty-blind: the write moves known rows at a rate independent of how hard
they are).

| # | G | B | K | Name earned |
|---|---|---|---|---|
| 1 | graded | bidirectional | knowledge-state | **abstention-disposition write** - a genuine, reversible, knowledge-indexed I-don't-know actuator; the PI's candidate name is earned in full |
| 2 | graded | bidirectional | difficulty | **commitment-strength axis** - a reversible, graded dial on how strongly the model commits to an answer, indexed to retrieval difficulty rather than to a knowledge boundary |
| 3 | graded | positive-only | knowledge-state | **one-way abstention ramp** - a graded, knowledge-indexed push into abstention that cannot be run backwards; matches the asymmetry paper 3 reports for the trained-checkpoint caution direction |
| 4 | graded | positive-only | difficulty | **retrieval-suppression gradient** - abstention is the visible endpoint of progressive retrieval failure, not a disposition being installed |
| 5 | binary | bidirectional | knowledge-state | **abstention-mode toggle** - a two-state, reversible switch between answer-mode and IDK-mode, indexed to knowledge |
| 6 | binary | bidirectional | difficulty | **answer-fragility switch** - a reversible mode switch keyed to how fragile the answer is, not to what is known |
| 7 | binary | positive-only | knowledge-state | **refusal-mode latch** - a one-way switch into IDK-mode; the write installs a refusal mode, it does not modulate an epistemic state |
| 8 | binary | positive-only | difficulty | **fragility-keyed refusal switch** - the weakest reading; a one-way mode switch that fires wherever the answer was already weakest |

**Override rule O-1 (silent-wrongness prefix).** If, in Arm C at 1.0x, the
known-row loss-of-correctness rate exceeds the known-row abstention rate by more
than a factor of 3, the earned name from rows 1-8 is prefixed
**"answer-corrupting"** (for example, "answer-corrupting one-way abstention
ramp"). Rationale: disclosure D-2 indicates that at the setpoint the write's
dominant effect on knowns is producing wrong answers rather than abstentions,
and no name containing "abstention" may be reported without that qualifier
attached. The rule is stated numerically here so it cannot be argued after the
result.

**Override rule O-2 (non-specific release).** If Arm B's refusal reduction
clears 0.20 but the specificity leg fails (released rows correct at under 0.30,
or the placebo also moves refusal by 0.05 or more), the BIDIRECTIONAL leg is NOT
earned. The table is read at POSITIVE-ONLY, and a separate finding is recorded:
**"output-gate suppression, not abstention control"** - the negative dose
suppresses the refusal output without restoring the answer.

**Instrument-void row.** If the Arm A taxonomy fails its blinded calibration
slice, axis G is unresolved and the cell reports **"unnamed write direction
(form instrument void)"** with axes B and K reported separately. If a dosed
readback gate fails on any arm, that arm is void and its axis is unresolved; no
name is assembled from a partial table.

**Naming discipline.** None of the eight names is mentalistic. Per the framework
section 3 rename table and the completed (d) adjudication, a mentalistic name
for this write is not available from this cell regardless of outcome; row 1's
"abstention-disposition" describes a behavioral disposition of the write, not an
attributed mental state. Nothing in this table renames a KG node id; aliases are
additive only.

## Prediction

Registered before any generation, and constrained by the disclosures above (no
prediction is offered on any quantity already computed in D-1 through D-4).

The write is a **graded, positive-only, difficulty-tracking, answer-corrupting**
actuator: Arm A finds a real intermediate marked-form band (F2+F3 clearing 0.15
at 0.5x or 0.75x); Arm B fails its specificity leg, so the bidirectional leg is
not earned; Arm C confirms the disclosed difficulty gradient on the fresh pool;
and override O-1 fires. Table row 4 with the O-1 prefix:
**"answer-corrupting retrieval-suppression gradient"**. The PI's candidate name
(abstention actuator) is NOT earned, and neither is "caution".

## Falsifier

The prediction is falsified if the assembled table row is any row other than 4,
or if override O-1 does not fire. Concretely, any one of these outcomes
falsifies it, and each is a named row rather than an open-ended miss:

- Arm A finds no intermediate marked-form band (F2+F3 below 0.15 at every
  intermediate dose, or failing the +0.10-over-baseline leg): axis G is BINARY
  and the table is read at rows 5-8.
- Arm B clears the 0.20 reduction leg and the 0.30 specificity leg with the
  placebo quiet: axis B is BIDIRECTIONAL and the table is read at rows 1, 2, 5,
  or 6. This is the outcome that would earn the PI's candidate name, and it is
  the single most consequential way this draft's prediction can be wrong.
- Arm C finds no difficulty gradient on the fresh pool (rare-minus-popular below
  0.10, or its bootstrap CI including zero): axis K is KNOWLEDGE-STATE and the
  table is read at rows 1, 3, 5, or 7. That would also mean the disclosed D-3
  read did not replicate on a never-dosed population, which is itself
  reportable.
- Override O-1 does not fire (known loss-of-correctness within a factor of 3 of
  known abstention at the setpoint): the D-2 dissociation does not generalize
  beyond the M1 rows and no prefix attaches.

Because the eight rows plus O-1, O-2, and the instrument-void row are exhaustive
over the outcome space, no result can land between the prediction and the
falsifier. This is the falsifier-coverage discipline the held-out cell adopted
after `doubt-snap-cross-family-confirmatory` resolved with a falsifier that could
not fire.

## Gates

Locked at sign; machine-readable form in `gates.yaml`. Wilson 95% CIs on every
rate; bootstrap 95% CIs on every difference, seed pinned at sign.

- **G0 (instrument validity; stop, not outcome).** Loader resolves
  `Qwen/Qwen3.5-4B@851bf6e8...` under a transformers version recognizing
  `qwen3_5`; the frozen `c_hat` and `random_direction` load byte-identical to
  the doubt-snap committed `directions/hs20/*.json` by sha256, and the
  standardization scalars load byte-for-byte from that `build_manifest.json`;
  the three population ID manifests are committed before any generation and are
  pairwise disjoint and disjoint from M1's 400-row confab subsample; dosed-smoke
  realized-projection readback within tolerance of +12.608 on positive arms and
  -12.608 on the -1.0x arm; RunLog grows during the run under a namespaced smoke
  path (the held-out cell's fingerprint-guard lesson); no question, alias, or
  answer text anywhere under `analysis-committed/`.
- **G1 (baseline reproduction; halt-and-lift on failure).** P-CONFAB baseline
  refusal within 0.05 of the held-out cell's baseline on this pool, and P-KNOWN
  baseline correctness at or above 0.90. If baselines do not reproduce, the
  render or the pool staging is wrong and the cell halts rather than scoring.
- **G2 (axis G; Arm A).** As stated in the naming table, plus the taxonomy
  calibration slice: disagreement <= 0.05 on the F1/F2/F3 boundary,
  clear-positive decoy agreement >= 0.60 with a minimum of 25 decoys. Failing
  calibration voids axis G.
- **G3 (axis B; Arm B).** Refusal reduction >= 0.20 absolute with Wilson 95% CI
  excluding zero; released-row correctness >= 0.30; random_direction at -1.0x
  moves refusal by < 0.05. All three are required for BIDIRECTIONAL.
- **G4 (axis K; Arm C).** Rare-minus-popular loss-of-correctness >= 0.10 with
  bootstrap 95% CI excluding zero for DIFFICULTY-TRACKING. Reported alongside:
  the same contrast on abstention rate, and the secondary internal-ordering read
  using per-row `z_d` from
  `experiments/qwen35-4b-midband-doubt-snap/analysis/from_modal/heldout_rows_for_steer.jsonl`
  (360/360 coverage on the M1 knowns), which adjudicates a third, distinct
  question (does the write track the KU readout's own ordering) and is **never
  rounded into** the axis-K verdict.
- **G5 (override O-1).** Known loss-of-correctness rate over known abstention
  rate at 1.0x, computed on P-KNOWN, against the factor-3 threshold.
- **C1 (construct).** Placebo arms behave as direction-specificity controls at
  matched realized projection; degenerate rate reported per arm and per dose; any
  arm whose degenerate rate exceeds 0.20 is reported as regime-invalid and its
  rows are excluded from form scoring, with the exclusion count committed.

## Predictions scoreboard

Registered at sign, before any generation, after the disclosures above are shown
to both predictors. Slot 1 is the table row; Slot 2 is the differentiating value.

| Predictor | Slot 1: table row earned | Slot 2: does Arm B earn BIDIRECTIONAL |
|-----------|--------------------------|----------------------------------------|
| orchestrator | Row 4 with O-1 prefix | NO, via O-2 specifically: the reduction leg fires (refusal drops >= 0.20 at some negative rung) but the specificity leg fails (released rows correct < 0.30), recording the "output-gate suppression, not abstention control" finding |
| user | Row 4 with O-1 prefix | NO (registered 2026-07-30 via decision prompt; user selected the row-4 + O-1 outcome, which entails the bidirectional leg is not earned) |

All three predictors (drafter, orchestrator, user) converge on row 4 + O-1.
The scoreboard differentiation is therefore in Slot 2's failure mechanism:
the drafter and user register only that BIDIRECTIONAL is not earned; the
orchestrator additionally commits to the O-2 shape (reduction fires,
specificity fails). If Arm B moves refusal by less than 0.20 at every
negative rung, the orchestrator's Slot 2 is wrong in mechanism even though
all Slot 1 calls may still be right.

The drafter's own call is recorded in the Prediction section (row 4 with the O-1
prefix) and is not a scoreboard slot.

## Outcome

**Resolved 2026-07-30 (lead adjudication, user-approved close-out). Cell
outcome: unnamed write direction (form instrument void).** The registered
instrument-void row governs: the Arm A form taxonomy failed its blinded
calibration slice (core disagreement 86/200 = 0.43 against the 0.05 floor;
clear-positive decoy agreement 19/19 = 1.00 against the 0.60 floor, over 19
decoys under a user-approved governed deviation from the registered 25-decoy
minimum, the placebo arms having produced only 19 such rows). Arms A and D are
instrument-void; no name is assembled and no Arm A form distribution is
citable. The mismatch is one-sided (79 of 86 disagreements are automated F1
read as F2 or F3 by the blinded judge): the pattern battery under-detects
epistemic marking, and any wider-recall taxonomy is a new instrument for a
future registration.

Axes B and K are reported separately per the registered rule.

**Axis B: POSITIVE-ONLY via O-2.** Negative dosing clears the release floor
decisively (refusal 0.969 at baseline falls by 0.760 at -0.5x and 0.948 at
-1.0x, bootstrap CIs excluding zero) but fails specificity both registered
ways: released-row correctness 0.094 and 0.105 against the 0.30 floor, and the
random-direction placebo at -1.0x moves refusal 0.107 against the 0.05
ceiling. The registered separate finding is recorded: **output-gate
suppression, not abstention control**. Per-arm C1 degenerate rates: b_baseline
0.000, b_neg_0p5 0.005, b_neg_1 0.102, b_neg_2 0.898 (regime-invalid over the
0.20 ceiling; the axis-B read rests on the two valid rungs), b_placebo_neg_1
0.007.

**Axis K: KNOWLEDGE-STATE.** Rare-minus-popular loss of correctness at 1.0x is
-0.06 (CI -0.137 to +0.017) against the +0.10-with-CI-excluding-zero
requirement; the disclosed D-3 difficulty gradient did not replicate on the
never-dosed pool, itself a registered reportable. Baseline P-KNOWN correctness
0.992 (G1 pass); C1 degenerate rates c_baseline 0.000, c_dose_1 0.012.
Reported alongside, never rounded in: the same contrast on abstention rate is
+0.06 (CI 0.020-0.100); the z_d internal-ordering read is
NOT-COMPUTABLE-AS-REGISTERED (the registered text names no outcome variable,
dose rung, or statistic; no post-hoc specification made; see NOTEBOOK
2026-07-30).

**O-1's numeric condition fires** (known-row loss of correctness 0.403 vs
known-row abstention 0.063, ratio 6.37 against the fires-above-3 line): the
D-2 dissociation generalizes to the fresh pool, with no earned name to prefix.
**O-2 fires** as stated under axis B. No assembled table row exists; rows 1-8
are all unearned.

**The registered prediction (row 4 with the O-1 prefix) is falsified** by two
independent routes: the assembled outcome is the instrument-void row, and axis
K resolved KNOWLEDGE-STATE, which excludes row 4 regardless of the void.
Scoreboard: orchestrator Slot 1 (row 4 + O-1) incorrect; user Slot 1 (row 4 +
O-1) incorrect; orchestrator Slot 2 correct in full including the committed
O-2 mechanism (reduction fires, released-row correctness fails the 0.30
floor); user Slot 2 (bidirectional not earned) correct.

One-sentence verdict for the manifest: **unnamed write direction (form
instrument void): the taxonomy failed blinded calibration (0.43 vs 0.05) so
axis G is void; axis B is positive-only via O-2 (output-gate suppression, not
abstention control); axis K is knowledge-state (no difficulty gradient); O-1's
dissociation confirmed (6.37:1 wrongness over abstention on knowns).**

Full arithmetic and provenance: NOTEBOOK.md entries of 2026-07-30,
analysis/axis_bk_arithmetic.json,
analysis-committed/form_adjudication_applied_manifest.json,
analysis-committed/form_adjudication_pool_manifest.json,
analysis-committed/form_adjudication_graded_manifest.json.
